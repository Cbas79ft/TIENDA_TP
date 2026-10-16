"""Formato y reglas de los productos del inventario.

Cada producto es un diccionario compatible con BD.persistencia. El TDA Lista
guardará ese diccionario en el campo info de un nodo y lo ordenará por
id_producto. SQLite genera el identificador antes de crear el producto.
"""

from math import isfinite


def crear_producto(id_producto, nombre, cantidad_disponible, precio):
    """Devuelve un producto validado sin escribir en la base de datos.

    Requiere un ID entero positivo, nombre no vacío, stock entero no negativo
    y precio numérico finito no negativo. Devuelve el precio como float.
    Lanza ValueError si alguno de los datos no cumple estas reglas.
    """
    if type(id_producto) is not int or id_producto <= 0:
        raise ValueError("El identificador debe ser un entero positivo.")

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre del producto no puede estar vacío.")

    # bool también es un subtipo de int en Python: no se acepta como stock.
    if type(cantidad_disponible) is not int or cantidad_disponible < 0:
        raise ValueError("La cantidad disponible debe ser un entero no negativo.")

    if type(precio) not in (int, float):
        raise ValueError("El precio debe ser un número finito no negativo.")
    try:
        precio = float(precio)
    except OverflowError:
        raise ValueError("El precio está fuera del rango admitido.") from None
    if not isfinite(precio) or precio < 0:
        raise ValueError("El precio debe ser un número finito no negativo.")

    return {
        "id_producto": id_producto,
        "nombre": nombre.strip(),
        "cantidad_disponible": cantidad_disponible,
        "precio": precio,
    }
