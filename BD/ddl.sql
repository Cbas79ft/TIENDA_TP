-- =====================================================================
-- DDL (Data Definition Language) - Sistema de Gestión de Tienda Online
--
-- Define la ESTRUCTURA de la base de datos: qué tablas existen, qué
-- columnas tiene cada una y qué reglas deben cumplir los datos.
-- No contiene datos (los de ejemplo están en BD/cargar_datos.py).
--
-- Se ejecuta con BD.persistencia.inicializar_bd() y es seguro correrlo
-- más de una vez: IF NOT EXISTS evita errores si las tablas ya existen.
-- =====================================================================

-- SQLite no aplica las claves foráneas salvo que se active por conexión.
PRAGMA foreign_keys = ON;

-- Clientes de la tienda.
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    apellido   TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE
);

-- Inventario. Al iniciar el servidor se carga en el TDA Lista.
CREATE TABLE IF NOT EXISTS productos (
    id_producto         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT    NOT NULL,
    cantidad_disponible INTEGER NOT NULL DEFAULT 0,
    precio              REAL    NOT NULL,

    CHECK (cantidad_disponible >= 0),
    CHECK (precio >= 0)
);

-- Clientes en espera por un producto sin stock (TDA Cola).
-- El id autoincremental conserva el orden de llegada (primero en entrar,
-- primero en salir).
CREATE TABLE IF NOT EXISTS esperas (
    id_espera    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente   INTEGER NOT NULL,
    id_producto  INTEGER NOT NULL,
    fecha_espera TEXT    NOT NULL,

    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
);

-- Historial de compras (TDA Pila: la última transacción es la cima).
CREATE TABLE IF NOT EXISTS transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente     INTEGER NOT NULL,
    fecha          TEXT    NOT NULL,
    total          REAL    NOT NULL,

    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),

    CHECK (total >= 0)
);

-- Productos de cada compra. Una fila por producto y por compra, por eso
-- COUNT(*) de esta tabla da la popularidad usada por el árbol (BST).
CREATE TABLE IF NOT EXISTS detalle_transaccion (
    id_detalle      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion  INTEGER NOT NULL,
    id_producto     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,

    FOREIGN KEY (id_transaccion)
        REFERENCES transacciones(id_transaccion),

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto),

    CHECK (cantidad > 0),
    CHECK (precio_unitario >= 0)
);