import sqlite3
import os

RUTA_BD = os.path.join(os.path.dirname(__file__), "tablas.db")

def conectar():
    """
    Abre la conexión a la base de datos con las claves foráneas.
    """
    conexion = sqlite3.connect(RUTA_BD)
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
    """
    inserta un producto y devuelve su id.
    """
    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO productos (nombre, cantidad_disponible, precio) VALUES (?, ?, ?)",
        (nombre, cantidad, precio),
    )
    conexion.commit()
    conexion.close()
    return cursor.lastrowid