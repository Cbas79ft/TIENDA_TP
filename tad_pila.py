class nodoPila(object):
    info, sig = None, None
class Pila(object):
    def __init__(self):
        self.cima = None
        self.tamanio = 0
    def apilar(pila, dato):
        nodo = nodoPila()
        nodo.info = dato
        nodo.sig = pila.cima
        pila.cima = nodo
        pila.tamanio += 1
    def desapilar(pila):
        x = pila.cima.info
        pila.cima = pila.cima.sig
        pila.tamanio -= 1
        return x
    def pila_vacia(pila):
        return pila.cima is None
    def en_cima(pila):
        if pila.cima is not None:
            return pila.cima.info
        else:
            return None
    def tamanio(pila):
        return pila.tamanio

def barrido(pila):
    paux = Pila()
    while (not Pila.pila_vacia(pila)):
        dato = Pila.desapilar(pila)
        print(dato)
        Pila.apilar(paux, dato)
    while (not Pila.pila_vacia(paux)):
        dato = Pila.desapilar(paux)
        Pila.apilar(pila, dato)