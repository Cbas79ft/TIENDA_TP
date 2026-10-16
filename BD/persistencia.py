"""Conexión a SQLite y operaciones de persistencia de productos."""

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