"""Índice de existencias con un BST independiente del árbol de popularidad."""
from BACKEND.tad_arbol import insertar_nodo, minimo
from BACKEND.inventario import consultar_productos, consultar_producto


class IndiceStock:
    """Ordena claves (stock, ID); un empate se resuelve por el menor ID."""
    def __init__(self, inventario):
        self.raiz = None
        self.actualizar(inventario)

    def actualizar(self, inventario):
        """Reconstruye el índice usando las primitivas del TDA árbol."""
        claves = sorted((p['cantidad_disponible'], p['id_producto']) for p in consultar_productos(inventario))
        self.raiz = None
        def insertar_mitad(inicio, fin):
            if inicio >= fin:
                return
            medio = (inicio + fin) // 2
            self.raiz = insertar_nodo(self.raiz, claves[medio])
            insertar_mitad(inicio, medio)
            insertar_mitad(medio + 1, fin)
        insertar_mitad(0, len(claves))

    def consultar_minimo(self, inventario):
        """Devuelve una copia del producto con menos stock, incluyendo agotados."""
        clave = minimo(self.raiz)
        return consultar_producto(inventario, clave[1]) if clave else None
