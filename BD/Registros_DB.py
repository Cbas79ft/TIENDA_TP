
import sqlite3

conexion = sqlite3.connect("BD/tablas.db")
cursor = conexion.cursor()

ingreso_clientes = [
    ('Sebastian', 'Trujillo', 'strujillo@gmail.com'),
    ('Agustin', 'Sanoguera', 'aesanoguera@gmail.com'),
    ('Carlos', 'Rodríguez', 'carlos.rodriguez@example.com'),
    ('Lucía', 'Fernández', 'lucia.fernandez@example.com'),
    ('Martín', 'López', 'martin.lopez@example.com')
]

cursor.executemany(
    "INSERT INTO clientes (nombre, apellido, email) VALUES (?, ?, ?)",
    ingreso_clientes
)

conexion.commit()
conexion.close()