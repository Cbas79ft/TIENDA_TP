"""Gestiona las colas de espera por producto mediante el TDA Cola."""

from datetime import datetime, timezone

from BD import persistencia
from BACKEND.tad_cola import (
    Cola,
    arribo,
    atencion,
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


def registrar_espera(colas, id_cliente, id_producto):
    """Guarda una nueva espera y la incorpora a la cola del producto.

    Devuelve una copia del registro creado.
    Si la persistencia falla, la cola no se modifica.
    """
    if type(id_cliente) is not int or id_cliente <= 0:
        raise ValueError(
            "El identificador del cliente debe ser un entero positivo."
        )

    if type(id_producto) is not int or id_producto <= 0:
        raise ValueError(
            "El identificador del producto debe ser un entero positivo."
        )

    # Se guarda una fecha con zona horaria en un formato uniforme.
    fecha_espera = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    # Persistencia comprueba que existan el cliente y el producto,
    # que el stock sea cero y que no haya una espera duplicada.
    id_espera = persistencia.insertar_espera(
        id_cliente,
        id_producto,
        fecha_espera,
    )

    espera = {
        "id_espera": id_espera,
        "id_cliente": id_cliente,
        "id_producto": id_producto,
        "fecha_espera": fecha_espera,
    }

    # La cola solo cambia después de confirmar el guardado.
    if id_producto not in colas:
        colas[id_producto] = Cola()

    arribo(colas[id_producto], espera)

    return espera.copy()


def preparar_notificacion(colas, id_producto, nombre_producto):
    """Prepara el aviso del primer cliente sin modificar la cola."""
    espera = consultar_primera_espera(colas, id_producto)

    if espera is None:
        return None

    cliente = persistencia.consultar_cliente(espera["id_cliente"])

    if cliente is None:
        raise ValueError("El cliente de la primera espera no existe.")

    return {
        "id_espera": espera["id_espera"],
        "id_cliente": cliente["id_cliente"],
        "id_producto": id_producto,
        "mensaje": (
            f"Notificación simulada para "
            f"{cliente['nombre']} {cliente['apellido']}: "
            f"el producto {nombre_producto} tiene stock disponible."
        ),
    }


def confirmar_atencion(colas, id_producto):
    """Retira al primero después de confirmar los cambios en SQLite.

    Debe ejecutarse bajo el mismo bloqueo que la reposición.
    """
    return atencion(colas[id_producto]).copy()
