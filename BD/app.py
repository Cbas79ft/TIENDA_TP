import sqlite3

# 1. Conectar a la base de datos (si no existe, se crea automáticamente)
conexion = sqlite3.connect("tablas.db")

# 2. Crear un cursor para ejecutar comandos SQL
cursor = conexion.cursor()

# 3. Crear las tablas y activar las claves foráneas
cursor.executescript(
    """
PRAGMA foreign_keys = ON;


-- TABLA: CLIENTES

CREATE TABLE clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);


-- TABLA: PRODUCTOS

CREATE TABLE productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cantidad_disponible INTEGER NOT NULL DEFAULT 0,
    precio REAL NOT NULL,

    CHECK (cantidad_disponible >= 0),
    CHECK (precio >= 0)
);



-- TABLA: ESPERA
-- Clientes que esperan la reposición de un producto

CREATE TABLE esperas (
    id_espera INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    fecha_espera TEXT NOT NULL,

    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
);


-- TABLA: TRANSACCIONES
-- Una transacción representa una compra

CREATE TABLE transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    total REAL NOT NULL,

    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),

    CHECK (total >= 0)
);



-- TABLA: DETALLE_TRANSACCION
-- Productos incluidos en cada compra

CREATE TABLE detalle_transaccion (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,

    FOREIGN KEY (id_transaccion)
        REFERENCES transacciones(id_transaccion),

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto),

    CHECK (cantidad > 0),
    CHECK (precio_unitario >= 0)
);
    """
)

# Lista ordenada de tus 20 productos
productos_nuevos = [
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


# 4. Inserción masiva y segura
cursor.executemany(
    "INSERT INTO productos (nombre, cantidad_disponible, precio) VALUES (?, ?, ?)",
    productos_nuevos,
)



ingreso_clientes = [
    ('Sebastian', 'Trujillo', 'strujillo@gmail.com'),
    ('Agustin', 'Sanoguera', 'aesanoguera@gmail.com'),
    ('Carlos', 'Rodríguez', 'carlos.rodriguez@example.com'),
    ('Lucía', 'Fernández', 'lucia.fernandez@example.com'),
    ('Martín', 'López', 'martin.lopez@example.com'),
    
]

cursor.executemany(
    "INSERT INTO clientes (nombre, apellido, email) VALUES (?, ?, ?)",
    ingreso_clientes,
)

# 5. Guardar los datos y cerrar la conexión
conexion.commit()
conexion.close()
