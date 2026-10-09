
import sqlite3

def clientes():
    conexion = sqlite3.connect("BD/tablas.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_cliente, nombre, apellido, email
        FROM clientes
    """)

    clientes = cursor.fetchall()

    conexion.close()

    return clientes

clientes = clientes()

for cliente in clientes:
    id_cliente = cliente[0]
    nombre = cliente[1]
    apellido = cliente[2]
    email = cliente[3]

    print("ID:", id_cliente)
    print("Nombre:", nombre)
    print("Apellido:", apellido)
    print("Email:", email)



def productos():
    conexion = sqlite3.connect("BD/tablas.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_producto, nombre, cantidad, precio
        FROM productos
    """)

    clientes = cursor.fetchall()

    productos.close()

    return productos

productos = productos()
for producto in productos:
    id_producto = cliente[0]
    nombre = cliente[1]
    cantidad_disponible = cliente[2]
    email = cliente[3]

    print("ID:", id_cliente)
    print("Nombre:", nombre)
    print("Apellido:", apellido)
    print("Email:", email)