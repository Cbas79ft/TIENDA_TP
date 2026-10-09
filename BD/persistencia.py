import sqlite3

def conectar():
    """
    Abre la conexión a la base de datos con las claves foráneas.
    """
    conexion = sqlite3.connect("tablas.db")
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion

def leer_productos():
    """
    Lee todos los productos de la base de datos como lista de diccionarios.
    """
    conexion = conectar()
    filas = conexion.execute("SELECT * FROM productos").fetchall()
    conexion.close()
    return [dict(fila) for fila in filas]

def insertar_producto(nombre, cantidad, precio):
    """"
    inserta un producto y devuelve su id.
    """
    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
        (nombre, cantidad, precio),
    )
    conexion.commit()
    conexion.close()
    return cursor.lastrowid