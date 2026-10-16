"""Carga inicial de productos y clientes en las tablas existentes."""

# Solo para pruebas: carga datos de ejemplo, no datos reales de la tienda.

from BD.persistencia import conectar


PRODUCTOS_INICIALES = [
    ("Mouse Óptico Inalámbrico", 45, 12500.00),
    ("Teclado Mecánico RGB", 20, 35000.00),
    ("Monitor LED 24 Pulgadas", 12, 145000.00),
    ("Auriculares Bluetooth Pro", 30, 28000.00),
    ("Disco Sólido SSD 480GB", 18, 31000.00),
    ("Cargador Rápido Tipo C", 60, 8500.00),
    ("Cable HDMI 2 Metros", 80, 4200.00),
    ("Pendrive 64GB USB 3.0", 55, 6800.00),
    ("Arroz Integral 1kg", 150, 2400.00),
    ("Fideos Tallarín 500g", 200, 1300.00),
    ("Aceite de Girasol 1.5L", 85, 3800.00),
    ("Yerba Mate Premium 1kg", 95, 4800.00),
    ("Café Molido Tostado 250g", 60, 6500.00),
    ("Gaseosa Cola Original 2.25L", 250, 2700.00),
    ("Detergente Sintético Limón", 140, 1850.00),
    ("Jabón Líquido para Ropa 3L", 75, 8900.00),
    ("Remera Algodón Básica Negra", 40, 14500.00),
    ("Pantalón Jean Clásico Recto", 20, 38000.00),
    ("Termo de Acero Inoxidable 1L", 25, 28000.00),
    ("Foco LED 9W Luz Fría", 200, 1400.00),
]

CLIENTES_INICIALES = [
    ("Sebastian", "Trujillo", "strujillo@gmail.com"),
    ("Agustin", "Sanoguera", "aesanoguera@gmail.com"),
    ("Carlos", "Rodríguez", "carlos.rodriguez@example.com"),
    ("Lucía", "Fernández", "lucia.fernandez@example.com"),
    ("Martín", "López", "martin.lopez@example.com"),
]


def cargar_tablas():
    """Carga cada tabla solo si está vacía y devuelve las cantidades insertadas.

    Requiere que las tablas ya existan. No completa cargas parciales ni
    modifica los registros existentes. Ambas cargas se confirman juntas.
    """
    cantidades = {"productos": 0, "clientes": 0}
    conexion = conectar()
    try:
        with conexion:
            # Evita que otra carga escriba entre la consulta y la inserción.
            conexion.execute("BEGIN IMMEDIATE")
            if conexion.execute("SELECT 1 FROM productos LIMIT 1").fetchone() is None:
                conexion.executemany(
                    """
                    INSERT INTO productos (nombre, cantidad_disponible, precio)
                    VALUES (?, ?, ?)
                    """,
                    PRODUCTOS_INICIALES,
                )
                cantidades["productos"] = len(PRODUCTOS_INICIALES)

            if conexion.execute("SELECT 1 FROM clientes LIMIT 1").fetchone() is None:
                conexion.executemany(
                    "INSERT INTO clientes (nombre, apellido, email) VALUES (?, ?, ?)",
                    CLIENTES_INICIALES,
                )
                cantidades["clientes"] = len(CLIENTES_INICIALES)
        return cantidades
    finally:
        conexion.close()


if __name__ == "__main__":
    cantidades = cargar_tablas()
    print(f"Productos insertados: {cantidades['productos']}")
    print(f"Clientes insertados: {cantidades['clientes']}")
