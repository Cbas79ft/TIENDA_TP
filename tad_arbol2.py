class nodoArbol(object):
    def __init__(self, info):
        self.izq = None
        self.der = None
        self.info = info
        self.altura = 0
def remplazar(raiz):
    aux = None
    if raiz.der is None:
        aux = raiz
        raiz = raiz.izq
    else:
        raiz.der, aux = remplazar(raiz.der)
    return raiz, aux
def altura(raiz):
    if raiz is None:
        return -1
    else:
        return raiz.altura
def actualizaraltura(raiz):
    if raiz is not None:
        alt_izq = altura(raiz.izq)
        alt_der = altura(raiz.der)
        raiz.altura = (alt_izq if alt_izq > alt_der else alt_der) + 1
def rotar_simple(raiz, control):
    if control:
        aux = raiz.izq
        raiz.izq = aux.der
        aux.der = raiz
    else:
        aux = raiz.der
        raiz.der = aux.izq
        aux.izq = raiz
    actualizaraltura(raiz)
    actualizaraltura(aux)
    raiz = aux
    return raiz
def rotar_doble(raiz, control):
    if control:
        raiz.izq = rotar_simple(raiz.izq, False)
        raiz = rotar_simple(raiz, True)
    else:
        raiz.der = rotar_simple(raiz.der, True)
        raiz = rotar_simple(raiz, False)
    return raiz
def balancear(raiz):
    if raiz is not None:
        if altura(raiz.izq) - altura(raiz.der) == 2:
            if altura(raiz.izq.izq) >= altura(raiz.izq.der):
                raiz = rotar_simple(raiz, True)
            else:
                raiz = rotar_doble(raiz, True)
        elif altura(raiz.der)-altura(raiz.izq) == 2:
            if altura(raiz.der.der) >= altura(raiz.der.izq):
                raiz = rotar_simple(raiz, False)
            else:
                raiz = rotar_doble(raiz, False)
    return raiz
def insertart_nodo(raiz, dato, pos):
    if raiz is not None:
        raiz = nodoArbol(dato, pos)
    elif dato < raiz.info:
        raiz.izq = insertart_nodo(raiz.izq, dato, pos)
    else:
        raiz.der = insertart_nodo(raiz.der, dato, pos)
    raiz = balancear(raiz)
    actualizaraltura(raiz)
    return raiz
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
                raiz.info, raiz.nrr = aux.info, aux.nrr
    raiz = balancear(raiz)
    actualizaraltura(raiz)
    return raiz, x