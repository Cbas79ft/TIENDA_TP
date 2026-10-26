"use strict";

// Identificación y carrito duran la pestaña; reservas y compras viven en SQLite.
const CLAVE = 'tienda.portal.v1';
const $ = selector => document.querySelector(selector);
const moneda = new Intl.NumberFormat('es-AR', {style:'currency', currency:'ARS'});
const esCarrito = document.body.dataset.vista === 'carrito';
let sesion = null;
let productos = [];
let reservas = [];
let avisos = [];
let compras = [];
let ocupado = false;
let cargando = false;
let catalogoDisponible = false;
try {
    const guardada = JSON.parse(sessionStorage.getItem(CLAVE) || 'null');
    if (guardada && typeof guardada.token === 'string' && guardada.cliente && Array.isArray(guardada.carrito)) {
        guardada.carrito = guardada.carrito.filter(d => Number.isSafeInteger(d.id_producto) && d.id_producto > 0 && Number.isSafeInteger(d.cantidad) && d.cantidad > 0);
        sesion = guardada;
    }
} catch (_) { /* Un almacenamiento inválido vuelve al formulario de ingreso. */ }

function guardarSesion() {
    sessionStorage.setItem(CLAVE, JSON.stringify(sesion));
}
function mensaje(texto, error = false) {
    $('#mensaje-portal').textContent = texto;
    $('#mensaje-portal').classList.toggle('error', error);
}
async function pedir(ruta, datos) {
    const controlador = new AbortController();
    const temporizador = setTimeout(() => controlador.abort(), 15000);
    try {
        const respuesta = await fetch(ruta, {
            method: datos === undefined ? 'GET' : 'POST',
            headers: {'Accept':'application/json', ...(datos === undefined ? {} : {'Content-Type':'application/json'}), ...(sesion ? {'X-Sesion':sesion.token} : {})},
            body: datos === undefined ? undefined : JSON.stringify(datos),
            cache:'no-store', signal:controlador.signal,
        });
        const resultado = await respuesta.json();
        if (!respuesta.ok) {
            const error = new Error(resultado.error || 'No se pudo completar la operación.');
            error.codigo = respuesta.status; error.registrar = resultado.registrar;
            throw error;
        }
        return resultado;
    } catch(error) {
        if (error.name === 'AbortError') throw new Error('El servidor tardó demasiado. Actualizá antes de volver a enviar la operación.');
        throw error;
    } finally { clearTimeout(temporizador); }
}
function mostrarIngreso() {
    $('#ingreso').hidden = false; $('#portal-contenido').hidden = true; $('#identidad-cliente').hidden = true;
}
function abrirPortal() {
    $('#ingreso').hidden = true; $('#portal-contenido').hidden = false; $('#identidad-cliente').hidden = false;
    $('#nombre-cliente').textContent = `Hola, ${sesion.cliente.nombre} ${sesion.cliente.apellido}`;
}
function cerrarIngreso() {
    sesion = null; sessionStorage.removeItem(CLAVE); mostrarIngreso();
    $('#formulario-ingreso').reset(); $('#datos-nuevo-cliente').hidden = true;
    $('#nombre-ingreso').required = false; $('#apellido-ingreso').required = false;
    $('#dni-ingreso').focus();
}
$('#dni-ingreso').addEventListener('input', () => {
    $('#datos-nuevo-cliente').hidden = true;
    $('#nombre-ingreso').required = false; $('#apellido-ingreso').required = false;
    $('#estado-ingreso').textContent = '';
});
$('#formulario-ingreso').addEventListener('submit', async evento => {
    evento.preventDefault();
    if ($('#continuar-ingreso').disabled) return;
    $('#continuar-ingreso').disabled = true; $('#estado-ingreso').textContent = 'Consultando DNI…';
    const datos = {dni:$('#dni-ingreso').value};
    if (!$('#datos-nuevo-cliente').hidden) {
        datos.nombre = $('#nombre-ingreso').value.trim(); datos.apellido = $('#apellido-ingreso').value.trim();
    }
    try {
        const resultado = await pedir('/api/ingreso', datos);
        sesion = {token:resultado.token, cliente:resultado.cliente, carrito:[]};
        guardarSesion(); abrirPortal(); $('#estado-ingreso').textContent = '';
        await cargarPortal();
    } catch(error) {
        if (error.registrar) {
            $('#datos-nuevo-cliente').hidden = false;
            $('#nombre-ingreso').required = true; $('#apellido-ingreso').required = true;
            $('#estado-ingreso').textContent = 'Es tu primera visita. Completá nombre y apellido para registrarte.';
            $('#nombre-ingreso').focus();
        } else { $('#estado-ingreso').textContent = error.message; }
    } finally { $('#continuar-ingreso').disabled = false; }
});
$('#salir-cliente').addEventListener('click', async () => {
    if (ocupado) return;
    try { await pedir('/api/salir', {}); } catch (_) { /* La identificación local se cierra de todas formas. */ }
    cerrarIngreso(); mensaje('');
});

/** Crea nodos de texto: los nombres nunca se interpretan como HTML. */
function nodo(etiqueta, texto, clase) {
    const elemento = document.createElement(etiqueta);
    if (texto !== undefined) elemento.textContent = texto;
    if (clase) elemento.className = clase;
    return elemento;
}
function boton(texto, accion, deshabilitado = false, clase = 'boton-secundario') {
    const elemento = nodo('button', texto, clase); elemento.type = 'button';
    elemento.disabled = deshabilitado; elemento.addEventListener('click', accion); return elemento;
}
function normalizar(texto) { return String(texto).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }
function mostrarResumen() {
    let cantidad = 0, total = 0;
    for (const detalle of sesion.carrito) {
        cantidad += detalle.cantidad;
        const producto = productos.find(p => p.id_producto === detalle.id_producto);
        if (producto) total += producto.precio * detalle.cantidad;
    }
    $('#resumen-carrito').textContent = cantidad ? `${cantidad} ${cantidad === 1 ? 'unidad agregada' : 'unidades agregadas'}` : 'Todavía no agregaste productos.';
    $('#total-carrito').textContent = moneda.format(total);
}
function mostrarCatalogo() {
    const consulta = normalizar($('#buscar').value.trim());
    const visibles = productos.filter(p => normalizar(p.nombre).includes(consulta) || String(p.id_producto).includes(consulta));
    const orden = $('#orden').value;
    visibles.sort(orden === 'nombre' ? (a,b) => a.nombre.localeCompare(b.nombre,'es') : orden === 'precio' ? (a,b) => a.precio-b.precio : (a,b) => b.popularidad-a.popularidad || a.id_producto-b.id_producto);
    $('#cantidad-resultados').textContent = `${visibles.length} de ${productos.length} productos`;
    $('#estado-catalogo').textContent = visibles.length ? '' : 'No hay productos para mostrar.';
    $('#productos').replaceChildren();
    for (const producto of visibles) {
        const tarjeta = nodo('article', undefined, 'producto');
        const cabecera = nodo('div', undefined, 'producto-superior');
        cabecera.append(nodo('span', `Producto #${producto.id_producto}`, 'id-producto'), nodo('span', `${producto.popularidad} ${producto.popularidad === 1 ? 'vendido' : 'vendidos'}`, 'etiqueta-popular'));
        const enEspera = reservas.some(r => r.id_producto === producto.id_producto);
        const cantidad = sesion.carrito.find(d => d.id_producto === producto.id_producto)?.cantidad || 0;
        const disponible = producto.cantidad_disponible > 0;
        tarjeta.append(cabecera, nodo('h3', producto.nombre), nodo('p', moneda.format(producto.precio), 'precio'), nodo('p', disponible ? `${producto.cantidad_disponible} disponibles` : 'Sin stock', 'stock'));
        tarjeta.append(boton(disponible ? `Agregar al carrito${cantidad ? ` · ${cantidad}` : ''}` : enEspera ? 'En espera de stock' : 'Reservar',
            () => disponible ? agregar(producto) : reservar(producto),
            ocupado || cargando || !catalogoDisponible || (!disponible && enEspera) || (disponible && cantidad >= producto.cantidad_disponible), 'agregar'));
        $('#productos').append(tarjeta);
    }
}
function agregar(producto) {
    if (ocupado || !catalogoDisponible) return;
    const detalle = sesion.carrito.find(d => d.id_producto === producto.id_producto);
    if ((detalle?.cantidad || 0) >= producto.cantidad_disponible) return;
    if (detalle) detalle.cantidad += 1; else sesion.carrito.push({id_producto:producto.id_producto,cantidad:1});
    guardarSesion(); dibujar(); mensaje(`${producto.nombre} agregado al carrito.`);
}
async function reservar(producto) {
    if (ocupado) return;
    ocupado = true; dibujar();
    try {
        await pedir('/api/esperas', {id_producto:producto.id_producto});
        mensaje(`Reservaste ${producto.nombre}. Podés ver tu lugar en “Ver carrito”, en “En espera de stock”.`);
    } catch(error) { mensaje(`${error.message} Actualizá tus reservas antes de reintentar.`, true); }
    finally { ocupado = false; await cargarPortal(); }
}
function llenarLista(selector, elementos, vacio, dibujarElemento) {
    const lista = $(selector); lista.replaceChildren();
    if (!elementos.length) { lista.append(nodo('li', vacio, 'vacio-carrito')); return; }
    for (const elemento of elementos) lista.append(dibujarElemento(elemento));
}
function mostrarDetalle() {
    let valida = sesion.carrito.length > 0 && catalogoDisponible;
    llenarLista('#detalle-carrito', sesion.carrito, 'Tu carrito está vacío. Agregá productos desde Comprar.', detalle => {
        const producto = productos.find(p => p.id_producto === detalle.id_producto);
        const fila = nodo('li', undefined, 'fila-carrito');
        const info = nodo('div'); info.append(nodo('h3', producto?.nombre || `Producto #${detalle.id_producto} no disponible`));
        const suficiente = producto && detalle.cantidad <= producto.cantidad_disponible;
        if (!suficiente) valida = false;
        info.append(nodo('p', producto ? `${moneda.format(producto.precio)} por unidad · Stock: ${producto.cantidad_disponible}` : 'Quitá este producto para continuar.', 'nota'));
        if (!suficiente) info.append(nodo('p', 'Stock insuficiente. Ajustá la cantidad o quitá el producto.', 'error'));
        const controles = nodo('div', undefined, 'controles-carrito');
        const etiqueta = nodo('label', 'Cantidad'); const entrada = nodo('input');
        entrada.type='number'; entrada.min='1'; entrada.step='1'; entrada.value=detalle.cantidad; entrada.disabled=ocupado || cargando;
        entrada.setAttribute('aria-label',`Cantidad de ${producto?.nombre || detalle.id_producto}`);
        entrada.addEventListener('change', () => {
            const valor = entrada.valueAsNumber;
            if (!Number.isSafeInteger(valor) || valor < 1) { entrada.value=detalle.cantidad; return; }
            detalle.cantidad=valor; guardarSesion(); dibujar();
        });
        etiqueta.append(entrada); controles.append(etiqueta, nodo('strong', producto ? moneda.format(producto.precio*detalle.cantidad) : '—'));
        controles.append(boton('Quitar', () => { sesion.carrito=sesion.carrito.filter(d=>d!==detalle);guardarSesion();dibujar(); }, ocupado || cargando));
        fila.append(info,controles); return fila;
    });
    $('#comprar-carrito').disabled = ocupado || cargando || !valida;
    $('#vaciar-carrito').disabled = ocupado || cargando || sesion.carrito.length === 0;
    llenarLista('#reservas-carrito',reservas,'No tenés productos en espera de stock.', reserva => {
        const fila=nodo('li'); fila.append(nodo('h3',reserva.nombre),nodo('p',`En espera de stock · Turno ${reserva.turno} · Reserva #${reserva.id_espera}`)); return fila;
    });
    llenarLista('#avisos-carrito',avisos,'Todavía no hay avisos de reposición.', aviso => {
        const fila=nodo('li');fila.append(nodo('p',aviso.mensaje),nodo('small',new Date(aviso.fecha).toLocaleString('es-AR')));return fila;
    });
    llenarLista('#compras-cliente',compras,'Todavía no realizaste compras.', compra => {
        const fila=nodo('li');fila.append(nodo('h3',`Compra #${compra.id_transaccion} · ${moneda.format(compra.total)}`),nodo('p',compra.productos.map(p=>`${p.nombre} × ${p.cantidad}`).join(', ')));return fila;
    });
}
function dibujar() {
    if (!sesion) return;
    mostrarResumen(); if (esCarrito) mostrarDetalle(); else mostrarCatalogo();
    $('#actualizar-portal').disabled=ocupado || cargando;
    $('#salir-cliente').disabled=ocupado;
}
async function cargarPortal() {
    if (!sesion || cargando) return;
    cargando=true; catalogoDisponible=false; dibujar();
    try {
        const [inventario, populares, misReservas, notificaciones, misCompras] = await Promise.all([
            pedir('/api/productos'),pedir('/api/recomendados?cantidad=50'),pedir('/api/mis-reservas'),pedir('/api/mis-notificaciones'),pedir('/api/mis-compras')
        ]);
        if (![inventario,populares,misReservas,notificaciones,misCompras].every(Array.isArray)) throw new Error('Los datos recibidos no son válidos.');
        const conteos=new Map(populares.map(p=>[p.id_producto,p.popularidad]));
        productos=inventario.map(p=>({...p,popularidad:p.popularidad ?? conteos.get(p.id_producto) ?? 0}));
        reservas=misReservas;avisos=notificaciones;compras=misCompras;catalogoDisponible=true;
    } catch(error) {
        if (error.codigo===401) {cerrarIngreso();$('#estado-ingreso').textContent='Ingresá nuevamente tu DNI.';}
        else mensaje(`${error.message} Presioná Actualizar para reintentar.`,true);
    } finally { cargando=false;dibujar(); }
}
$('#actualizar-portal').addEventListener('click', cargarPortal);
if (esCarrito) {
    $('#vaciar-carrito').addEventListener('click',()=>{if(ocupado)return;sesion.carrito=[];guardarSesion();dibujar();mensaje('Carrito vacío. Tus reservas se conservan.');});
    $('#comprar-carrito').addEventListener('click',async()=>{
        if(ocupado || $('#comprar-carrito').disabled)return;
        ocupado=true;dibujar();
        try {
            const resultado=await pedir('/api/compras',{productos:sesion.carrito});
            sesion.carrito=[];guardarSesion();
            mensaje(`Compra #${resultado.id_transaccion} confirmada por ${moneda.format(resultado.total)}. El stock fue actualizado.`);
        } catch(error) {mensaje(`${error.message} Consultá Tus compras antes de volver a confirmar.`,true);}
        finally {ocupado=false;await cargarPortal();}
    });
} else {
    $('#buscar').addEventListener('input', mostrarCatalogo);$('#orden').addEventListener('change', mostrarCatalogo);
}
(async()=>{
    if (!sesion) {mostrarIngreso();return;}
    try {sesion.cliente=await pedir('/api/sesion');abrirPortal();await cargarPortal();}
    catch (_) {cerrarIngreso();$('#estado-ingreso').textContent='Ingresá nuevamente tu DNI.';}
})();
