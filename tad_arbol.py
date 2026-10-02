from tad_cola import Cola, arribo, cola_vacia, atencion

class nodoArbol(object):
    def __init__(self, info):
        self.izq = None
        self.der = None
        self.info = info
def eliminar_nodo(raiz, clave):
    x = None
    if raiz is not None:
        if clave < raiz.info:
            raiz.izq, x = eliminar_nodo(raiz.izq, clave)
        elif clave > raiz.info:
            raiz.der, x = eliminar_nodo(raiz.der, clave)
        else:
            x = raiz.info
            if raiz.izq is None:
                raiz = raiz.der
            elif raiz.der is None:
                raiz = raiz.izq
            else:
                raiz.izq, aux = remplazar(raiz.izq)
                raiz.info = aux.info
    return raiz, x
def insertar_nodo(raiz, dato):
    if raiz is None:
        raiz = nodoArbol(dato)
    elif dato < raiz.info:
        raiz.izq = insertar_nodo(raiz.izq, dato)
    else:
        raiz.der = insertar_nodo(raiz.der, dato)
    return raiz
def arbolvacio(raiz):
    return raiz is None
def remplazar(raiz):
    aux = None
    if raiz.der is None:
        aux = raiz
        raiz = raiz.izq
    else:
        raiz.der, aux = remplazar(raiz.der)
    return raiz, aux
def por_nivel(raiz):
    if raiz is None:
        return
    pendientes = Cola()
    arribo(pendientes, raiz)
    while not cola_vacia(pendientes):
        nodo = atencion(pendientes)
        print(nodo.info)
        if nodo.izq is not None:
            arribo(pendientes, nodo.izq)
        if nodo.der is not None:
            arribo(pendientes, nodo.der)
def buscar(raiz, clave):
    pos = None
    if raiz is not None:
        if raiz.info == clave:
            pos = raiz
        elif clave < raiz.info:
            pos = buscar(raiz.izq, clave)
        else:
            pos = buscar(raiz.der, clave)
    return pos
def inorden(raiz):
    if raiz is not None:
        inorden(raiz.izq)
        print(raiz.info)
        inorden(raiz.der)
def preorden(raiz):
    if raiz is not None:
        print(raiz.info)
        preorden(raiz.izq)
        preorden(raiz.der)
def postorden(raiz):
    if raiz is not None:
        postorden(raiz.izq)
        postorden(raiz.der)
        print(raiz.info)

def altura(raiz):
    if raiz is None:
        return -1
    return 1 + max(altura(raiz.izq), altura(raiz.der))