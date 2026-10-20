"""Gestiona las colas de espera por producto mediante el TDA Cola."""

from BD import persistencia
from BACKEND.tad_cola import (
    Cola,
    arribo,
    cola_vacia,
    en_frente,
    mover_al_final,
    tamanio,
)


def cargar_colas():
    """Reconstruye una cola por producto desde las esperas guardadas.

    Devuelve un diccionario cuya clave es el ID del producto
    y cuyo valor es una instancia del TDA Cola.
    """
    colas = {}

    # Persistencia entrega los registros ordenados por id_espera.
    for espera in persistencia.leer_esperas():
        id_producto = espera["id_producto"]

        if id_producto not in colas:
            colas[id_producto] = Cola()

        # Cada registro ingresa al final, respetando el orden de llegada.
        arribo(colas[id_producto], espera.copy())

    return colas


def consultar_esperas(colas, id_producto):
    """Devuelve copias de las esperas del producto en orden FIFO.

    Si el producto no tiene una cola, devuelve una lista vacía.
    Al terminar, la cola conserva su orden original.
    """
    cola = colas.get(id_producto)

    if cola is None or cola_vacia(cola):
        return []

    esperas = []
    cantidad = tamanio(cola)

    # Una vuelta completa permite consultar mediante las primitivas
    # del TDA y deja los elementos en su orden original.
    for _ in range(cantidad):
        espera = mover_al_final(cola)
        esperas.append(espera.copy())

    return esperas


def consultar_primera_espera(colas, id_producto):
    """Devuelve una copia de la primera espera sin retirarla.

    Devuelve None si el producto no tiene clientes en espera.
    """
    cola = colas.get(id_producto)

    if cola is None or cola_vacia(cola):
        return None

    return en_frente(cola).copy()
