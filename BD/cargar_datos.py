"""Carga de datos de ejemplo para pruebas del sistema."""

from BD.cargar_tablas import cargar_tablas


# SOLO PARA PRUEBAS: estos registros son ejemplos, no datos reales de la tienda.
def cargar_datos():
    """Carga los ejemplos únicamente en las tablas que estén vacías."""
    return cargar_tablas()


if __name__ == "__main__":
    cantidades = cargar_datos()
    print(f"Productos de prueba insertados: {cantidades['productos']}")
    print(f"Clientes de prueba insertados: {cantidades['clientes']}")
