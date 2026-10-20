"""Reglas y preparación de compras para la gestión con TDA Pila.

Este primer paso valida y prepara los datos. El guardado, el descuento
de stock, el apilado y la reversión se incorporarán en los pasos siguientes.
Las operaciones compartidas deberán usar el bloqueo del servidor.
"""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite

from BD import persistencia
from BACKEND.inventario import consultar_producto
from BACKEND.tad_pila import en_cima, pila_vacia


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
