"""
Popularidad de productos y recomendaciones con el TAD árbol Binario de búsqueda.
La popularidad de un producto es la cantidad de compras en las que figura (cada compra cuenta
una vez por producto, sin importar las unidades).
El árbol guarda claves (popularidad, id_producto). Incluir el id hace que la clave sea única
aunque varios producto tengan la misma popularidad, y el recorrido inorden inverso entrega primero los
más populares.
"""

from BD import persistencia
from BACKEND.tad_arbol import eliminar_nodo, insertar_nodo, mayores
from BACKEND.inventario import consultar_producto

MAXIMO_RECOMENDADOS = 50

class Popularidad(object):
    """
    Estado de popularidad: raíz del BST y conteo actual de cada producto.
    El árbol solo contiene productos con al menos una compra. El diccionario permite
    conocer la clave actual de un producto para poder retirarla del árbol antes de insertar la nueva
    (El BST se ordena por esa clave).
    """
    def __init__(self):
        self.raiz = None
        self.conteo = {}

def cargar_popularidad():
    """ Reconstruye el árbol desde las compras guardadas en SQLite."""
    estado = Popularidad()
    for registro in persistencia.leer_popularidad():
        id_producto = registro["id_producto"]
        popularidad = registro["popularidad"]
        #La clave (popularidad, id) es unica: No hay claves repetidas
        estado.raiz = insertar_nodo(estado.raiz, (popularidad, id_producto))
        estado.conteo[id_producto] = popularidad
    return estado

def _cambiar_popularidad(estado, id_producto, variacion):
    """
    Suma o resta a la popularidad de un producto y reubica su nodo.
    Un BST ordena por la clave, así que no se puede modificar el
    nodo en el lugar: se elimina la clave vieja y se inserta la nueva.
    """
    actual = estado.conteo.get(id_producto, 0)
    nueva = actual + variacion
    if nueva < 0:
        raise ValueError(f"El producto #{id_producto} no tiene compras para revertir.")
    if actual > 0:
        estado.raiz, _ = eliminar_nodo(estado.raiz, (actual, id_producto))
    if nueva > 0:
        estado.raiz = insertar_nodo(estado.raiz, (nueva, id_producto))
        estado.conteos[id_producto] = nueva
    else:
        #Sin compras, el producto sale del árbol de popularidad
        del estado.conteos[id_producto]

def registrar_compra(estado, ids_productos):
    """
    Suma una compra a cada producto distinto de la lista recibida.
    Debe llamarse DESPUÉS de confirmar la compra en SQLite, bajo el bloqueo del servidor, para 
    que el árbol no cambie si el guardado falla.
    """
    for id_producto in set(ids_productos):
        _cambiar_popularidad(estado, id_producto, 1)

def revertir_compra(estado, ids_productos):
    """
    Resta una compra a cada producto distinto de la lista recibida.
    Se valida todo antes de modificar, para no dejar el árbol a medias.
    """
    distintos = set(ids_productos)
    for id_producto in distintos:
        if estado.conteos.get(id_producto, 0) < 1:
            raise ValueError(f"El producto #{id_producto} no tiene compras para revertir.")
    for id_producto in distintos:
        _cambiar_popularidad(estado, id_producto, -1)

def consultar_recomendados(estado, inventario, cantidad=5):
    """
    Devuelve hasta 'cantidad' productos, de más al menos popular.
    Cada elemento es una copia del producto del inventario más su popularidad. Con un árbol
    de altura h cuesta O(h + cantidad), porque el recorrido se detiene al reunir los
    productos pedidos.
    """
    if type(cantidad) is not int or not 0 < cantidad <= MAXIMO_RECOMENDADOS:
        raise ValueError(f"Cantidad de recomendados debe ser un entero entre 1 y {MAXIMO_RECOMENDADOS}.")
    recomendados = []
    for popularidad, id_producto in mayores(estado.raiz, cantidad):
        producto = consultar_producto(inventario, id_producto)
        if producto is None:
            continue
        producto["popularidad"] = popularidad
        recomendados.append(producto)
    return recomendados
