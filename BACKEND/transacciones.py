"""Reglas y preparación de compras para la gestión con TDA Pila.

Valida, guarda, apila y revierte compras coordinando inventario y esperas.
Las operaciones compartidas deberán usar el bloqueo del servidor.
"""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite

from BD import persistencia
from BACKEND.inventario import consultar_producto
from BACKEND.tad_pila import Pila, apilar, desapilar, en_cima, pila_vacia
from BACKEND.inventario import sincronizar_productos
from BACKEND.esperas import confirmar_atencion
from BACKEND import recomendaciones


MAX_ENTERO_SQLITE = 9223372036854775807


def validar_entero_positivo(valor, campo):
    """Rechaza booleanos y valores fuera del rango entero de SQLite."""
    if type(valor) is not int or not 0 < valor <= MAX_ENTERO_SQLITE:
        raise ValueError(f"{campo} debe ser un entero positivo válido.")


def preparar_compra(inventario, id_cliente, productos_solicitados):
    """Valida una compra completa y devuelve sus datos sin modificar estado.

    Recibe una lista de diccionarios con id_producto y cantidad. Agrupa
    productos repetidos, exige stock suficiente y toma los precios del
    inventario. No acepta precios ni totales proporcionados por la pantalla.
    """
    validar_entero_positivo(id_cliente, "El identificador del cliente")
    if persistencia.consultar_cliente(id_cliente) is None:
        raise ValueError("El cliente no existe.")

    if not isinstance(productos_solicitados, list) or not productos_solicitados:
        raise ValueError("La compra debe incluir al menos un producto.")

    cantidades = {}
    for solicitado in productos_solicitados:
        if (
            not isinstance(solicitado, dict)
            or set(solicitado) != {"id_producto", "cantidad"}
        ):
            raise ValueError(
                "Cada producto debe incluir únicamente id_producto y cantidad."
            )

        id_producto = solicitado["id_producto"]
        cantidad = solicitado["cantidad"]
        validar_entero_positivo(id_producto, "El identificador del producto")
        validar_entero_positivo(cantidad, "La cantidad")

        # La disponibilidad se comprueba contra la cantidad total solicitada,
        # evitando que varias líneas del mismo producto excedan el stock.
        acumulada = cantidades.get(id_producto, 0) + cantidad
        validar_entero_positivo(acumulada, "La cantidad acumulada")
        cantidades[id_producto] = acumulada

    detalles = []
    total = Decimal("0")
    for id_producto, cantidad in cantidades.items():
        producto = consultar_producto(inventario, id_producto)
        if producto is None:
            raise ValueError(f"El producto #{id_producto} no existe.")
        if cantidad > producto["cantidad_disponible"]:
            raise ValueError(
                f"Stock insuficiente para el producto #{id_producto}."
            )

        precio_unitario = producto["precio"]
        # Calculamos con decimales antes de convertir al tipo REAL de SQLite.
        total += Decimal(str(precio_unitario)) * cantidad
        detalles.append({
            "id_producto": id_producto,
            "nombre": producto["nombre"],
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
        })

    total = float(total)
    if not isfinite(total):
        raise ValueError("El total de la compra está fuera del rango admitido.")

    return {
        "id_cliente": id_cliente,
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "productos": detalles,
        "total": total,
    }


def consultar_ultima_transaccion(pila):
    """Devuelve una copia independiente de la última compra sin desapilar.

    Una pila vacía no permite deshacer. La copia incluye los detalles para
    impedir cambios accidentales en los productos de la compra almacenada.
    """
    if pila_vacia(pila):
        raise ValueError("No hay transacciones para deshacer.")
    return deepcopy(en_cima(pila))



def cargar_pila():
    """Reconstruye la pila global dejando arriba la compra más reciente."""
    pila = Pila()
    for compra in persistencia.leer_transacciones():
        apilar(pila, compra)
    return pila


def registrar_transaccion(inventario, pila, popularidad, indice_stock, id_cliente, productos):
    """Registra una compra completa bajo el bloqueo compartido del servidor."""
    compra = preparar_compra(inventario, id_cliente, productos)
    compra['id_transaccion'] = persistencia.guardar_compra(compra)
    ids = [d['id_producto'] for d in compra['productos']]
    sincronizar_productos(inventario, ids)
    apilar(pila, compra)
    recomendaciones.registrar_compra(popularidad, ids)
    indice_stock.actualizar(inventario)
    return deepcopy(compra)


def deshacer_transaccion(inventario, colas, pila, popularidad, indice_stock, id_transaccion):
    """Deshace la cima y restaura inventario, colas y árboles tras confirmar SQLite."""
    ultima = consultar_ultima_transaccion(pila)
    if ultima['id_transaccion'] != id_transaccion:
        raise ValueError('La última compra cambió. Actualizá el historial.')
    ids = [d['id_producto'] for d in ultima['productos']]
    if any(popularidad.conteo.get(id_producto, 0) < 1 for id_producto in ids):
        raise ValueError('El árbol de popularidad no coincide con las compras.')
    atendidas = persistencia.revertir_ultima_compra(id_transaccion)
    sincronizar_productos(inventario, ids)
    for espera in atendidas:
        confirmar_atencion(colas, espera['id_producto'])
    desapilar(pila)
    recomendaciones.revertir_compra(popularidad, ids)
    indice_stock.actualizar(inventario)
    return {'transaccion': ultima, 'notificaciones': atendidas}


def consultar_historial(pila):
    """Recorre la pila con una auxiliar y restituye su orden original."""
    auxiliar = Pila()
    historial = []
    try:
        while not pila_vacia(pila):
            compra = desapilar(pila)
            apilar(auxiliar, compra)
            historial.append(deepcopy(compra))
    finally:
        while not pila_vacia(auxiliar):
            apilar(pila, desapilar(auxiliar))
    return historial
