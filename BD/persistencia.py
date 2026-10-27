"""
Conexión a SQLite y persistencia de productos, clientes y esperas.
La persistencia guarda los productos en la base de datos SQLite para que
no se pierda información al cerrar el programa. La lista enlazada del inventario
se reconstruye a partir de la base de datos al iniciar el programa.
El módulo persistencia.py no depende de inventario.py ni de servidor.py.
"""

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite
from pathlib import Path

# Siempre apunta a tablas.db dentro de la carpeta BD,
# sin importar desde dónde se ejecute el programa.
RUTA_BD = Path(__file__).resolve().parent / "tablas.db"
RUTA_DDL = Path(__file__).resolve().parent / "ddl.sql"


def migrar_clientes_dni():
    """Retira email preservando IDs, relaciones y clientes sin DNI conocido.

    Conserva una copia de la base anterior. Los clientes heredados quedan
    pendientes de completar DNI; nunca se les asigna un documento ficticio.
    """
    conexion = conectar()
    try:
        columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(clientes)")}
        if not columnas or "email" not in columnas:
            return
        respaldo = RUTA_BD.with_name(
            "respaldo_antes_dni_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f") + ".db"
        )
        copia = sqlite3.connect(respaldo)
        try:
            conexion.backup(copia)
        finally:
            copia.close()
        conexion.execute("PRAGMA foreign_keys = OFF")
        with conexion:
            conexion.execute("BEGIN IMMEDIATE")
            conexion.execute("""
                CREATE TABLE clientes_nuevos (
                    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    dni TEXT UNIQUE CHECK (dni IS NULL OR
                        (length(dni) BETWEEN 7 AND 8 AND dni NOT GLOB '*[^0-9]*'))
                )
            """)
            conexion.execute("""
                INSERT INTO clientes_nuevos(id_cliente, nombre, apellido)
                SELECT id_cliente, nombre, apellido FROM clientes
            """)
            conexion.execute("DROP TABLE clientes")
            conexion.execute("ALTER TABLE clientes_nuevos RENAME TO clientes")
            if conexion.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("La migración produciría referencias inválidas.")
        conexion.execute("PRAGMA foreign_keys = ON")
    finally:
        conexion.close()


def conectar():
    """Abre una conexión con claves foráneas activadas."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion

def inicializar_bd():
    """
    Crea las tablas ejecutando el ddl.sql.
    Si las tablas ya existen no hace nada (el DDL usa IF NOT EXISTS), así
    que se puede llamar siempre antes de cargar o usar la base.
    """
    migrar_clientes_dni()
    script = RUTA_DDL.read_text(encoding="utf-8")
    conexion = conectar()
    try:
        conexion.executescript(script)
    finally:
        conexion.close()

def leer_productos():
    """Devuelve todos los productos como una lista de diccionarios."""
    conexion = conectar()
    try:
        filas = conexion.execute(
            "SELECT * FROM productos ORDER BY id_producto"
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def consultar_producto(id_producto):
    """Devuelve un producto por su identificador, o None si no existe."""
    conexion = conectar()
    try:
        fila = conexion.execute(
            "SELECT * FROM productos WHERE id_producto = ?",
            (id_producto,),
        ).fetchone()
        return dict(fila) if fila is not None else None
    finally:
        conexion.close()


def insertar_producto(nombre, cantidad_disponible, precio):
    """Inserta un producto y devuelve su identificador."""
    conexion = conectar()
    try:
        with conexion:
            cursor = conexion.execute(
                """
                INSERT INTO productos (nombre, cantidad_disponible, precio)
                VALUES (?, ?, ?)
                """,
                (nombre, cantidad_disponible, precio),
            )
        return cursor.lastrowid
    finally:
        conexion.close()


def modificar_producto(
    id_producto, nombre, cantidad_disponible, precio,
    id_espera=None,
):
    """Actualiza un producto y, si corresponde, elimina su primera espera.

    Ambas operaciones se confirman juntas o se revierten juntas.
    Devuelve False si el producto no existe.
    """
    conexion = conectar()
    try:
        with conexion:
            conexion.execute("BEGIN IMMEDIATE")

            if id_espera is not None:
                producto = conexion.execute(
                    """
                    SELECT cantidad_disponible FROM productos
                    WHERE id_producto = ?
                    """,
                    (id_producto,),
                ).fetchone()

                if producto is None:
                    return False

                if (
                    producto["cantidad_disponible"] != 0
                    or cantidad_disponible <= 0
                ):
                    raise ValueError(
                        "La atención requiere una reposición de cero a positivo."
                    )

                primera = conexion.execute(
                    """
                    SELECT id_espera FROM esperas
                    WHERE id_producto = ?
                    ORDER BY id_espera
                    LIMIT 1
                    """,
                    (id_producto,),
                ).fetchone()

                if primera is None or primera["id_espera"] != id_espera:
                    raise ValueError(
                        "La cola no coincide con la primera espera guardada."
                    )

            cursor = conexion.execute(
                """
                UPDATE productos
                SET nombre = ?, cantidad_disponible = ?, precio = ?
                WHERE id_producto = ?
                """,
                (nombre, cantidad_disponible, precio, id_producto),
            )
            if cursor.rowcount == 0:
                return False

            if id_espera is not None:
                guardar_aviso(conexion, id_espera, nombre)
                conexion.execute(
                    "DELETE FROM esperas WHERE id_espera = ?",
                    (id_espera,),
                )

        return True
    finally:
        conexion.close()


def eliminar_producto(id_producto):
    """Elimina un producto y devuelve si se encontró el registro."""
    conexion = conectar()
    try:
        with conexion:
            cursor = conexion.execute(
                "DELETE FROM productos WHERE id_producto = ?",
                (id_producto,),
            )
        return cursor.rowcount > 0
    finally:
        conexion.close()


def leer_clientes():
    """Devuelve los clientes registrados, ordenados por ID."""
    conexion = conectar()
    try:
        filas = conexion.execute(
            """
            SELECT id_cliente, nombre, apellido, dni
            FROM clientes
            ORDER BY id_cliente
            """
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def consultar_cliente(id_cliente):
    """Devuelve un cliente por ID, o None si no existe."""
    conexion = conectar()
    try:
        fila = conexion.execute(
            "SELECT * FROM clientes WHERE id_cliente = ?",
            (id_cliente,),
        ).fetchone()
        return dict(fila) if fila is not None else None
    finally:
        conexion.close()


def existe_espera(id_cliente, id_producto):
    """Indica si el cliente ya está esperando ese producto."""
    conexion = conectar()
    try:
        fila = conexion.execute(
            """
            SELECT 1 FROM esperas
            WHERE id_cliente = ? AND id_producto = ?
            LIMIT 1
            """,
            (id_cliente, id_producto),
        ).fetchone()
        return fila is not None
    finally:
        conexion.close()


def insertar_espera(id_cliente, id_producto, fecha_espera):
    """Guarda una espera y devuelve su ID.

    Rechaza clientes o productos inexistentes, productos con stock
    y esperas duplicadas.
    """
    conexion = conectar()
    try:
        with conexion:
            # Mantiene las comprobaciones y la inserción juntas,
            # evitando que otra conexión escriba entre ambas.
            conexion.execute("BEGIN IMMEDIATE")

            cliente = conexion.execute(
                "SELECT 1 FROM clientes WHERE id_cliente = ?",
                (id_cliente,),
            ).fetchone()
            if cliente is None:
                raise ValueError("El cliente no existe.")

            producto = conexion.execute(
                """
                SELECT cantidad_disponible FROM productos
                WHERE id_producto = ?
                """,
                (id_producto,),
            ).fetchone()
            if producto is None:
                raise ValueError("El producto no existe.")

            if producto["cantidad_disponible"] != 0:
                raise ValueError("El producto tiene stock disponible.")

            duplicada = conexion.execute(
                """
                SELECT 1 FROM esperas
                WHERE id_cliente = ? AND id_producto = ?
                LIMIT 1
                """,
                (id_cliente, id_producto),
            ).fetchone()
            if duplicada is not None:
                raise ValueError(
                    "El cliente ya está esperando este producto."
                )

            cursor = conexion.execute(
                """
                INSERT INTO esperas (
                    id_cliente, id_producto, fecha_espera
                )
                VALUES (?, ?, ?)
                """,
                (id_cliente, id_producto, fecha_espera),
            )

        return cursor.lastrowid
    finally:
        conexion.close()


def leer_esperas(id_producto=None):
    """Devuelve las esperas en orden de llegada.

    Sin producto devuelve todas, para reconstruir las colas al iniciar.
    Con producto devuelve únicamente sus esperas.
    """
    conexion = conectar()
    try:
        if id_producto is None:
            filas = conexion.execute(
                "SELECT * FROM esperas ORDER BY id_espera"
            ).fetchall()
        else:
            filas = conexion.execute(
                """
                SELECT * FROM esperas
                WHERE id_producto = ?
                ORDER BY id_espera
                """,
                (id_producto,),
            ).fetchall()

        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def eliminar_espera(id_espera):
    """Elimina una espera y devuelve si existía."""
    conexion = conectar()
    try:
        with conexion:
            cursor = conexion.execute(
                "DELETE FROM esperas WHERE id_espera = ?",
                (id_espera,),
            )
        return cursor.rowcount > 0
    finally:
        conexion.close()

def leer_popularidad():
    """
    Suma las unidades vendidas de cada producto en todas las compras guardadas.
    La popularidad no se guarda en la tabla productos: se calcula desde
    detalle_transaccion, así siempre coincide con el historial (y con deshacer).
    """
    conexion = conectar()
    try:
        filas = conexion.execute(
            "SELECT id_producto, SUM(cantidad) AS popularidad "   # <-- antes: COUNT(DISTINCT id_transaccion)
            "FROM detalle_transaccion "
            "GROUP BY id_producto "
            "ORDER BY id_producto"
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def normalizar_dni(dni):
    """Normaliza el documento y exige siete u ocho dígitos ASCII."""
    if not isinstance(dni, str):
        raise ValueError("Ingresá el DNI como texto.")
    dni = dni.replace('.', '').replace(' ', '').strip()
    if not 7 <= len(dni) <= 8 or any(c < '0' or c > '9' for c in dni):
        raise ValueError("El DNI debe contener siete u ocho dígitos.")
    return dni

def normalizar_nombre(valor, campo):
    """Valida un nombre o apellido: solo letras, espacios, guiones y apóstrofes."""
    if not isinstance(valor, str):
        raise ValueError(f"Ingresá el {campo} como texto.")
    valor = ' '.join(valor.split())  # saca espacios de más al principio, al final y entre palabras
    if not 2 <= len(valor) <= 50:
        raise ValueError(f"El {campo} debe tener entre 2 y 50 caracteres.")
    for caracter in valor:
        if not (caracter.isalpha() or caracter == ' '):
            raise ValueError(f"El {campo} solo puede tener letras y espacios.")
    return valor

def ingresar_cliente(dni, nombre=None, apellido=None):
    """Recupera un cliente por DNI o registra uno nuevo con nombre y apellido."""
    dni = normalizar_dni(dni)
    conexion = conectar()
    try:
        with conexion:
            conexion.execute('BEGIN IMMEDIATE')
            fila = conexion.execute('SELECT * FROM clientes WHERE dni = ?', (dni,)).fetchone()
            if fila is not None:
                return dict(fila)
            if nombre is None and apellido is None:
                return None
            nombre = normalizar_nombre(nombre, 'nombre')
            apellido = normalizar_nombre(apellido, 'apellido')
            cursor = conexion.execute('INSERT INTO clientes(dni,nombre,apellido) VALUES(?,?,?)', (dni, nombre, apellido))
            return dict(conexion.execute('SELECT * FROM clientes WHERE id_cliente=?',(cursor.lastrowid,)).fetchone())
    finally:
        conexion.close()


def guardar_aviso(conexion, id_espera, nombre_producto):
    """Guarda un aviso dentro de la misma transacción que atiende la espera."""
    espera = conexion.execute('SELECT * FROM esperas WHERE id_espera=?', (id_espera,)).fetchone()
    if espera is None:
        raise ValueError('La espera ya no existe.')
    mensaje = f'El producto {nombre_producto} tiene stock disponible. Tu espera fue atendida.'
    conexion.execute('INSERT INTO notificaciones(id_cliente,id_producto,fecha,mensaje) VALUES(?,?,?,?)',
                     (espera['id_cliente'], espera['id_producto'], datetime.now(timezone.utc).isoformat(timespec='seconds'), mensaje))
    return mensaje


def leer_notificaciones(id_cliente):
    """Consulta los últimos avisos persistentes del cliente."""
    conexion = conectar()
    try:
        return [dict(f) for f in conexion.execute('SELECT * FROM notificaciones WHERE id_cliente=? ORDER BY id_notificacion DESC LIMIT 20', (id_cliente,))]
    finally:
        conexion.close()


def leer_transacciones():
    """Recupera las compras y sus detalles, de la más antigua a la más nueva."""
    conexion = conectar()
    try:
        with conexion:
            conexion.execute('BEGIN')
            compras = [dict(f) for f in conexion.execute('SELECT * FROM transacciones ORDER BY id_transaccion')]
            for compra in compras:
                compra['productos'] = [dict(f) for f in conexion.execute('''
                    SELECT d.id_producto,p.nombre,d.cantidad,d.precio_unitario
                    FROM detalle_transaccion d JOIN productos p USING(id_producto)
                    WHERE d.id_transaccion=? ORDER BY d.id_detalle
                ''', (compra['id_transaccion'],))]
        return compras
    finally:
        conexion.close()


def guardar_compra(compra):
    """Confirma compra, detalles y descuento de stock de forma indivisible."""
    conexion = conectar()
    try:
        with conexion:
            conexion.execute('BEGIN IMMEDIATE')
            if conexion.execute('SELECT 1 FROM clientes WHERE id_cliente=?', (compra['id_cliente'],)).fetchone() is None:
                raise ValueError('El cliente no existe.')
            total = Decimal('0')
            ids = set()
            for detalle in compra['productos']:
                if detalle['id_producto'] in ids:
                    raise ValueError('Los productos repetidos deben agruparse.')
                ids.add(detalle['id_producto'])
                actual = conexion.execute('SELECT * FROM productos WHERE id_producto=?', (detalle['id_producto'],)).fetchone()
                if actual is None or actual['cantidad_disponible'] < detalle['cantidad']:
                    raise ValueError('El stock cambió. Actualizá el carrito antes de comprar.')
                if actual['precio'] != detalle['precio_unitario']:
                    raise ValueError('El precio cambió. Actualizá el carrito antes de comprar.')
                total += Decimal(str(actual['precio'])) * detalle['cantidad']
            total = float(total)
            if not isfinite(total):
                raise ValueError('El total está fuera del rango admitido.')
            cursor = conexion.execute('INSERT INTO transacciones(id_cliente,fecha,total) VALUES(?,?,?)',
                                      (compra['id_cliente'], compra['fecha'], total))
            id_transaccion = cursor.lastrowid
            for detalle in compra['productos']:
                conexion.execute('INSERT INTO detalle_transaccion(id_transaccion,id_producto,cantidad,precio_unitario) VALUES(?,?,?,?)',
                                 (id_transaccion, detalle['id_producto'], detalle['cantidad'], detalle['precio_unitario']))
                conexion.execute('UPDATE productos SET cantidad_disponible=cantidad_disponible-? WHERE id_producto=?',
                                 (detalle['cantidad'], detalle['id_producto']))
        return id_transaccion
    finally:
        conexion.close()


def revertir_ultima_compra(id_transaccion):
    """Revierte solo la última compra y atiende las esperas por stock restituido."""
    conexion = conectar()
    atendidas = []
    try:
        with conexion:
            conexion.execute('BEGIN IMMEDIATE')
            ultima = conexion.execute('SELECT MAX(id_transaccion) FROM transacciones').fetchone()[0]
            if ultima != id_transaccion:
                raise ValueError('Solo se puede deshacer la última compra. Actualizá el historial.')
            detalles = conexion.execute('''
                SELECT d.id_producto,d.cantidad,p.nombre,p.cantidad_disponible
                FROM detalle_transaccion d JOIN productos p USING(id_producto)
                WHERE d.id_transaccion=?
            ''', (id_transaccion,)).fetchall()
            for detalle in detalles:
                stock = detalle['cantidad_disponible'] + detalle['cantidad']
                if stock > 9223372036854775807:
                    raise ValueError('La restitución excede el stock admitido.')
                conexion.execute('UPDATE productos SET cantidad_disponible=? WHERE id_producto=?',
                                 (stock, detalle['id_producto']))
                if detalle['cantidad_disponible'] == 0:
                    espera = conexion.execute('SELECT * FROM esperas WHERE id_producto=? ORDER BY id_espera LIMIT 1',
                                              (detalle['id_producto'],)).fetchone()
                    if espera:
                        aviso = guardar_aviso(conexion, espera['id_espera'], detalle['nombre'])
                        conexion.execute('DELETE FROM esperas WHERE id_espera=?', (espera['id_espera'],))
                        atendidas.append({**dict(espera), 'mensaje': aviso})
            conexion.execute('DELETE FROM detalle_transaccion WHERE id_transaccion=?', (id_transaccion,))
            conexion.execute('DELETE FROM transacciones WHERE id_transaccion=?', (id_transaccion,))
        return atendidas
    finally:
        conexion.close()
