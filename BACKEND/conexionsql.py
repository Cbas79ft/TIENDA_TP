'''Consultas de clientes y productos usando la persistencia compartida.

import sqlite3
import os

RUTA_BD = os.path.join(os.path.dirname(__file__), "tablas.db")

def clientes():
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_cliente, nombre, apellido, email
        FROM clientes
    """)

    clientes = cursor.fetchall()

    conexion.close()

    return clientes

cliente = clientes()

for cliente in clientes:
    id_cliente = cliente[0]
    nombre = cliente[1]
    apellido = cliente[2]
    email = cliente[3]

    print("ID:", id_cliente)
    print("Nombre:", nombre)
    print("Apellido:", apellido)
    print("Email:", email)




Para mostrar los registros desde la raíz: python -m BACKEND.conexionsql.
Importar este módulo no consulta ni modifica la base de datos.
'''

from BD import persistencia

def clientes():
    """Devuelve los clientes como una lista de diccionarios ordenada por ID."""
    conexion = persistencia.conectar()
    try:
        filas = conexion.execute(
            "SELECT id_cliente, nombre, apellido, email FROM clientes ORDER BY id_cliente"
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()
def productos():
    """Devuelve los productos mediante la consulta del módulo de persistencia."""
    return persistencia.leer_productos()


if __name__ == "__main__":
    for cliente in clientes():
        print("ID:", cliente["id_cliente"])
        print("Nombre:", cliente["nombre"])
        print("Apellido:", cliente["apellido"])
        print("Email:", cliente["email"])
        print()

    for producto in productos():
        print("ID:", producto["id_producto"])
        print("Nombre:", producto["nombre"])
        print("Cantidad disponible:", producto["cantidad_disponible"])
        print("Precio:", producto["precio"])
        print()
