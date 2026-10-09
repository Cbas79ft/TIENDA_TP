class nodoLista(object):
    info, sig = None, None
class Lista(object):
    def __init__(self):
        self.inicio = None
        self.tamanio = 0

def primero(lista):
    return lista.inicio.info
def agregar_final(lista, dato):
    nodo = nodoLista()
    nodo.info = dato
    nodo.sig = None
    if lista.inicio is None:
        lista.inicio = nodo
    else:
        aux = lista.inicio
        while aux.sig is not None:
            aux = aux.sig
        aux.sig = nodo
    lista.tamanio += 1
def insertar_sublista(lista_principal, sublista):
    nodo = nodoLista()
    nodo.info = sublista
    nodo.sig = None
    if lista_principal.inicio is None:
        lista_principal.inicio = nodo
    else:
        aux = lista_principal.inicio
        while aux.sig is not None:
            aux = aux.sig
        aux.sig = nodo
    lista_principal.tamanio += 1
def barrido_lista_de_listas(lista_principal):
    aux = lista_principal.inicio
    nro_alumno = 1
    while aux is not None:
        lista_alumno = aux.info
        aux2 = lista_alumno.inicio
        print(f"\n--- Alumno {nro_alumno} ---")
        campos = ["Nombre", "Apellido", "Legajo"]
        i = 0
        while aux2 is not None:
            if i < 3:
                print(f"{campos[i]}: {aux2.info}")
            else:
                lista_parciales = aux2.info
                aux3 = lista_parciales.inicio
                nro_parcial = 1
                while aux3 is not None:
                    lista_parcial = aux3.info
                    aux4 = lista_parcial.inicio
                    materia = aux4.info
                    aux4 = aux4.sig
                    nota = aux4.info
                    aux4 = aux4.sig
                    fecha = aux4.info
                    print(f"Parcial {nro_parcial}: Materia={materia}, Nota={nota}, Fecha={fecha}")
                    nro_parcial += 1
                    aux3 = aux3.sig
            i += 1
            aux2 = aux2.sig
        nro_alumno += 1
        aux = aux.sig

def insertar(lista, dato):
    nodo = nodoLista()
    nodo.info = dato
    if (lista.inicio is None) or (lista.inicio.info > dato):
        nodo.sig = lista.inicio
        lista.inicio = nodo
    else:
        ant = lista.inicio
        act = lista.inicio.sig
        while(act is not None and act.info < dato):
            ant = ant.sig
            act = act.sig
        nodo.sig = act
        ant.sig = nodo
    lista.tamanio += 1
def lista_vacia(lista):
    return lista.inicio is None
def eliminar(lista, clave):
    dato = None
    if lista.inicio is None:
        return dato
    if(lista.inicio.info == clave):
        dato = lista.inicio.info
        lista.inicio = lista.inicio.sig
        lista.tamanio -= 1
    else:
        anterior = lista.inicio
        actual = lista.inicio.sig
        while(actual is not None and actual.info != clave):
            anterior = anterior.sig
            actual = actual.sig
        if (actual is not None):
            dato = actual.info
            anterior.sig = actual.sig
            lista.tamanio -= 1
    return dato
def tamanio(lista):
    return lista.tamanio
def buscar(lista, buscado):
    aux = lista.inicio
    while(aux is not None and aux.info != buscado):
        aux = aux.sig
    return aux
def barrido(lista):
    aux = lista.inicio
    while(aux is not None):
        print(aux.info)
        aux = aux.sig

def criterio(dato, campo=None):
    if campo is None:
        return dato
    if isinstance(dato, dict):
        return dato[campo]
    if hasattr(dato, '__dict__'):
        return dato.__dict__[campo]
    return dato

def inserta1(lista, dato, campo=None):
    nodo = nodoLista()
    nodo.info = dato
    if(lista.inicio is None) or (criterio(lista.inicio.info, campo) > criterio(dato, campo)):
        nodo.sig = lista.inicio
        lista.inicio = nodo
    else:
        ant = lista.inicio
        act = lista.inicio.sig
        while(act is not None and criterio(act.info, campo) < criterio(dato, campo)):
            ant = ant.sig
            act = act.sig
        nodo.sig = act
        ant.sig = nodo
    lista.tamanio += 1
def buscar1(lista, buscado, campo=None):
    aux = lista.inicio
    while (aux is not None and criterio(aux.info, campo) != criterio(buscado, campo)):
        aux = aux.sig
    return aux
def eliminar1(lista, clave, campo=None):
    dato = None
    if lista.inicio is None:
        return dato
    if (criterio(lista.inicio.info, campo) == criterio(clave, campo)):
        dato = lista.inicio.info
        lista.inicio = lista.inicio.sig
        lista.tamanio -= 1
    else:
        anterior = lista.inicio
        actual = lista.inicio.sig
        while(actual is not None and criterio(actual.info, campo) != criterio(clave, campo)):
            anterior = anterior.sig
            actual = actual.sig
        if (actual is not None):
            dato = actual.info
            anterior.sig = actual.sig
            lista.tamanio -= 1
    return dato

def agregar_final2(lista, dato):
    nodo = nodoLista()
    nodo.info = dato
    if lista.inicio is None:
        lista.inicio = nodo
        nodo.sig = nodo
    else:
        aux = lista.inicio
        while aux.sig != lista.inicio:
            aux = aux.sig
        aux.sig = nodo
        nodo.sig = lista.inicio
    lista.tamanio += 1
def eliminar2(lista, clave):
    dato = None
    if lista.inicio is None:
        return dato

    if lista.inicio.info == clave:
        dato = lista.inicio.info
        if lista.inicio.sig == lista.inicio:
            lista.inicio = None
        else:
            ultimo = lista.inicio
            while ultimo.sig != lista.inicio:
                ultimo = ultimo.sig
            lista.inicio = lista.inicio.sig
            ultimo.sig = lista.inicio
        lista.tamanio -= 1
    else:
        anterior = lista.inicio
        actual = lista.inicio.sig
        while actual != lista.inicio and actual.info != clave:
            anterior = anterior.sig
            actual = actual.sig
        if actual != lista.inicio:
            dato = actual.info
            anterior.sig = actual.sig
            lista.tamanio -= 1
    return dato
def barrido2(lista):
    if lista_vacia(lista):
        return
    aux = lista.inicio
    while True:
        print(aux.info)
        aux = aux.sig
        if aux == lista.inicio:
            break