"""Carga y consulta del inventario usando las primitivas del TDA Lista."""

from BD import persistencia
from BACKEND.producto import crear_producto
from BACKEND.tad_listas import Lista, barrido, buscar1, inserta1, eliminar1


def cargar_inventario():
    """Carga los productos persistidos en una lista enlazada ordenada por ID.

    Devuelve una lista vacía si no hay registros. Si un producto guardado
    tiene datos inválidos, propaga ValueError en lugar de omitirlo.
    """
    inventario = Lista()
    for registro in persistencia.leer_productos():
        # Se valida el formato sin escribir en SQLite.
        producto = crear_producto(
            registro["id_producto"],
            registro["nombre"],
            registro["cantidad_disponible"],
            registro["precio"],
        )
        inserta1(inventario, producto, "id_producto")
    return inventario


def consultar_productos(inventario):
    """Devuelve copias de los productos, ordenadas por ID y listas para JSON."""
    # El recorrido de nodos queda encapsulado dentro del barrido del TDA.
    return [producto.copy() for producto in barrido(inventario)]


def consultar_producto(inventario, id_producto):
    """Devuelve una copia del producto buscado, o None si no existe."""
    if type(id_producto) is not int or id_producto <= 0:
        raise ValueError("El identificador debe ser un entero positivo.")

    # buscar1 compara el campo indicado y devuelve el nodo encontrado.
    nodo = buscar1(inventario, {"id_producto": id_producto}, "id_producto")
    if nodo is None:
        return None
    # Se lee el dato devuelto por la primitiva, sin recorrer sus enlaces.
    return nodo.info.copy()

def agregar_producto(inventario, nombre, cantidad_disponible, precio):
    """Valida, guarda e incorpora un producto al inventario.

    Devuelve una copia del producto con el ID generado por SQLite.
    Si los datos son inválidos, lanza ValueError antes de guardar.
    """
    # Usamos un ID provisional únicamente para validar los demás campos.
    # No se guarda este identificador en la base ni en la lista.
    producto = crear_producto(
        id_producto=1,
        nombre=nombre,
        cantidad_disponible=cantidad_disponible,
        precio=precio,
    )

    # SQLite genera el identificador definitivo.
    # Si esta operación falla, no se modifica la lista enlazada.
    id_producto = persistencia.insertar_producto(
        producto["nombre"],
        producto["cantidad_disponible"],
        producto["precio"],
    )

    producto["id_producto"] = id_producto

    # Incorporamos el producto usando la primitiva existente del TDA.
    inserta1(inventario, producto, "id_producto")

    # La copia evita que el código que recibe el resultado cambie
    # accidentalmente el diccionario almacenado en el inventario.
    return producto.copy()

def modificar_producto(
    inventario, id_producto, nombre, cantidad_disponible, precio
):
    """Modifica un producto conservando su identificador.

    Devuelve una copia del producto actualizado, o None si no existe.
    Lanza ValueError si los datos son inválidos.
    """
    # Buscamos el producto usando la consulta del inventario.
    if consultar_producto(inventario, id_producto) is None:
        return None

    # Validamos los nuevos datos antes de modificar la base o la lista.
    producto = crear_producto(
        id_producto,
        nombre,
        cantidad_disponible,
        precio,
    )

    # Primero guardamos los cambios en SQLite.
    actualizado = persistencia.modificar_producto(
        producto["id_producto"],
        producto["nombre"],
        producto["cantidad_disponible"],
        producto["precio"],
    )

    # Si el registro ya no existe en la base, no cambiamos la lista.
    if not actualizado:
        return None

    # Reemplazamos el producto mediante las primitivas existentes del TDA,
    # sin manipular los enlaces de sus nodos desde este módulo.
    eliminar1(inventario, {"id_producto": id_producto}, "id_producto")
    inserta1(inventario, producto, "id_producto")

    return producto.copy()

def eliminar_producto(inventario, id_producto):
    """Elimina un producto de SQLite y de la lista enlazada.

    Devuelve una copia del producto eliminado, o None si no existe.
    Si SQLite impide la eliminación, propaga el error y conserva la lista.
    """
    # Buscamos el producto antes de intentar eliminarlo.
    producto = consultar_producto(inventario, id_producto)

    if producto is None:
        return None

    # Primero eliminamos el registro persistido.
    # Las claves foráneas pueden impedir esta operación si el producto
    # está relacionado con compras o clientes en espera.
    eliminado = persistencia.eliminar_producto(id_producto)

    if not eliminado:
        return None

    # Solo después de confirmar la eliminación en SQLite,
    # retiramos el producto mediante la primitiva del TDA.
    eliminar1(
        inventario,
        {"id_producto": id_producto},
        "id_producto",
    )

    return producto.copy()


