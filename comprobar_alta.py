"""Comprueba el alta de productos sin modificar la base real."""

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from BD import persistencia
from BACKEND.inventario import (
    agregar_producto,
    cargar_inventario,
    consultar_producto,
    consultar_productos,
)


def comprobar_alta():
    """Verifica guardado, carga en el TDA y rechazo de datos inválidos."""
    with TemporaryDirectory() as carpeta:
        ruta_temporal = Path(carpeta) / "prueba.db"

        # Creamos solamente la tabla necesaria para esta comprobación.
        conexion = sqlite3.connect(ruta_temporal)
        try:
            conexion.execute("""
                CREATE TABLE productos (
                    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cantidad_disponible INTEGER NOT NULL DEFAULT 0,
                    precio REAL NOT NULL,
                    CHECK (cantidad_disponible >= 0),
                    CHECK (precio >= 0)
                )
            """)
            conexion.commit()
        finally:
            conexion.close()

        # Durante este bloque, persistencia usa la base temporal.
        # Al salir, se restaura automáticamente la ruta original.
        with patch.object(persistencia, "RUTA_BD", ruta_temporal):
            inventario = cargar_inventario()

            producto = agregar_producto(
                inventario,
                "Teclado de prueba",
                10,
                35000,
            )
            identificador = producto["id_producto"]

            # El producto debe existir en memoria y en SQLite.
            assert consultar_producto(inventario, identificador) == producto
            assert persistencia.consultar_producto(identificador) == producto
            print("OK: producto guardado en SQLite y en la lista.")

            # Recargar simula la recuperación después de un reinicio.
            inventario_recargado = cargar_inventario()
            assert consultar_producto(
                inventario_recargado, identificador
            ) == producto
            print("OK: el producto se recupera al recargar.")

            # Las entradas inválidas no deben agregar registros.
            casos_invalidos = [
                ("", 10, 100),
                ("Producto", -1, 100),
                ("Producto", 1.5, 100),
                ("Producto", 10, -100),
            ]

            productos_anteriores = consultar_productos(inventario)
            registros_anteriores = persistencia.leer_productos()

            for nombre, cantidad, precio in casos_invalidos:
                try:
                    agregar_producto(
                        inventario, nombre, cantidad, precio
                    )
                except ValueError:
                    pass
                else:
                    raise AssertionError(
                        "Se aceptó un producto con datos inválidos."
                    )

            assert consultar_productos(inventario) == productos_anteriores
            assert persistencia.leer_productos() == registros_anteriores
            print("OK: datos inválidos rechazados sin modificar registros.")

    print("Comprobación terminada. La base temporal fue eliminada.")


if __name__ == "__main__":
    comprobar_alta()
