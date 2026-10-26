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
12. Para el árbol de popularidad, cada compra suma las unidades vendidas de cada
    producto. Deshacer resta esas mismas unidades.

## Implementación

Las compras se preparan y se confirman en SQLite junto con sus detalles y el
descuento de stock. Tras confirmar se actualizan lista, pila y ambos árboles.
La reversión de la cima devuelve unidades al stock actual y atiende al primer
cliente de cada cola cuyo producto pasa de cero a positivo, guardando también
un aviso persistente. Se reconstruyen las estructuras al iniciar el servidor.

El árbol de popularidad suma las unidades vendidas por producto. Un segundo BST
ordena claves (stock, id_producto) para consultar las menores existencias.

## Ingreso y carrito

El cliente ingresa por DNI. Si es nuevo, completa nombre y apellido. Los DNI se
normalizan quitando puntos y espacios; se exige un documento de siete u ocho
dígitos y se garantiza su unicidad. No se almacena email.

El navegador guarda la identificación y el carrito en sessionStorage durante
esa pestaña. Al iniciar una pestaña nueva se pide DNI otra vez. Las reservas,
compras y avisos se conservan en SQLite, independientemente del carrito.
El servidor asocia las compras y reservas al cliente de la sesión; el portal
no permite elegir manualmente a otro cliente.

Los registros anteriores a la migración se conservan con sus IDs y sin DNI,
pendientes de completarlo con un dato real. Esta es la única excepción al DNI
obligatorio en el registro. No se vinculan automáticamente por nombre para
evitar confundir personas con nombres repetidos.

Vaciar el carrito no cancela reservas. Una reserva no descuenta unidades ni
crea una compra. La notificación de reposición se simula y se muestra en el
carrito del cliente, sin envío de correo.

## Cambio de comportamiento solicitado

Las compras confirmadas no pueden editarse ni deshacerse desde el sistema.
Se retiraron el historial administrativo del inventario y la ruta HTTP de
reversión. El historial personal del cliente es solo de consulta.
La función interna de reversión con TDA Pila se conserva para referencia
académica, pero no está expuesta por la API ni por la interfaz. Esta decisión
se aparta de la opción de deshacer que pide la consigna del punto 3.
