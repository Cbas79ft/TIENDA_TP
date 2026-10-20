"""
Conexión a SQLite y persistencia de productos, clientes y esperas.
La persistencia guarda los productos en la base de datos SQLite para que
no se pierda información al cerrar el programa. La lista enlazada del inventario
se reconstruye a partir de la base de datos al iniciar el programa.
El módulo persistencia.py no depende de inventario.py ni de servidor.py.
"""

import sqlite3
from pathlib import Path

# Siempre apunta a tablas.db dentro de la carpeta BD,
# sin importar desde dónde se ejecute el programa.
RUTA_BD = Path(__file__).resolve().parent / "tablas.db"


def conectar():
    """Abre una conexión con claves foráneas activadas."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


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


def modificar_producto(id_producto, nombre, cantidad_disponible, precio):
    """Actualiza un producto y devuelve si se encontró el registro."""
    conexion = conectar()
    try:
        with conexion:
            cursor = conexion.execute(
                """
                UPDATE productos
                SET nombre = ?, cantidad_disponible = ?, precio = ?
                WHERE id_producto = ?
                """,
                (nombre, cantidad_disponible, precio, id_producto),
            )
        return cursor.rowcount > 0
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
            SELECT id_cliente, nombre, apellido, email
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
