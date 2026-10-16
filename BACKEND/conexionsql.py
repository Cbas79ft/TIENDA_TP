"""Consultas de clientes y productos usando la persistencia compartida.

Para mostrar los registros desde la raíz: python -m BACKEND.conexionsql.
Importar este módulo no consulta ni modifica la base de datos.
"""

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
