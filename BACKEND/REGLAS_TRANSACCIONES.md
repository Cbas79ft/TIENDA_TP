# Gestión de transacciones: reglas del punto 3

## Reglas acordadas

1. Cada compra corresponde a un cliente registrado.
2. La compra contiene al menos un producto existente. Las cantidades son
   enteros positivos. Se agrupan las líneas repetidas antes de validar stock.
3. Todos los productos deben tener stock suficiente. Si uno falla, se rechaza
   la compra completa. Anotarse en una cola sigue siendo una acción independiente.
4. El backend toma los precios del inventario y calcula el total. Los precios
   unitarios de la compra se conservan aunque cambien después en el inventario.
5. Cada transacción guarda identificador, cliente, fecha, productos, cantidades,
   precios unitarios y total. SQLite genera el identificador al guardar.
6. La compra, sus detalles y el descuento de stock se confirman en una misma
   transacción SQLite. Después se actualiza la lista de inventario y se apila.
7. Se usa una pila global de compras con orden LIFO. Solo se puede deshacer
   la última compra, independientemente del cliente. Una pila vacía no permite
   deshacer.
8. Deshacer suma las cantidades compradas al stock actual; no restaura una
   versión antigua del producto ni modifica su nombre o precio actuales.
9. La reversión elimina los detalles y la transacción de SQLite. Después de
   confirmar, se actualiza el inventario y se desapila. Si falla el guardado,
   se conserva el estado anterior de las estructuras.
10. Si al deshacer un producto pasa de stock cero a positivo, se notifica y
    retira al primero de su cola. La atención se confirma junto con la reversión.
11. Al iniciar se reconstruye la pila leyendo las compras por id_transaccion
    ascendente. Compras, reversiones, inventario y colas comparten el bloqueo
    del servidor. Las estructuras se manipulan mediante sus primitivas.
12. Para el futuro árbol de popularidad, cada compra cuenta una vez por producto,
    independientemente de las unidades. Deshacer revierte ese incremento.

## Estado del paso 1

`transacciones.py` implementa la preparación y validación de una compra, genera
su fecha UTC y permite consultar una copia de la cima mediante el TDA Pila.
Los identificadores y cantidades se limitan al rango entero de SQLite; no se
aceptan booleanos, precios externos ni totales externos en las líneas de compra.

La preparación no guarda ni descuenta stock, no registra esperas y no apila.
La persistencia deberá volver a comprobar cliente, productos y disponibilidad
dentro de su transacción al confirmar una compra.

El guardado, el registro en la pila, la reversión, la conexión con las colas,
la recuperación al iniciar, las rutas HTTP y la interfaz se implementarán en
los pasos siguientes. El árbol corresponde al punto 4 de la consigna.
