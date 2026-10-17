"use strict";

/*
 * app.js: controla la interacción de la pantalla de inventario.
 * Consulta GET /api/productos mediante fetch, valida la respuesta JSON,
 * construye la tabla y calcula el resumen de productos y existencias.
 * Permite buscar por nombre o ID y volver a consultar con Actualizar.
 * Gestiona los estados de carga, error, inventario vacío y búsqueda sin
 * resultados. Envía altas con POST y modificaciones con PUT a la API.
 * El backend se encarga de escribir en SQLite y actualizar el TDA.
 * Utiliza JavaScript nativo, sin librerías externas.
 */

// El frontend consulta la API; los datos del inventario se gestionan en Python.
const cuerpoTabla = document.querySelector("#productos");
const tablaContenedor = document.querySelector("#tabla-contenedor");
const estado = document.querySelector("#estado");
const buscar = document.querySelector("#buscar");
const actualizar = document.querySelector("#actualizar");
const cantidadResultados = document.querySelector("#cantidad-resultados");
const moneda = new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" });
const entero = new Intl.NumberFormat("es-AR");

let productos = [];

const cancelarEdicion = document.querySelector("#cancelar-edicion");
// null significa alta; un ID indica que estamos editando ese producto.
let idProductoEnEdicion = null;

/** Completa el formulario con los datos del producto seleccionado. */
function iniciarEdicion(producto) {
    if (camposProducto.disabled) return;

    idProductoEnEdicion = producto.id_producto;

    document.querySelector("#titulo-alta").textContent =
        `Editar producto #${producto.id_producto}`;

    document.querySelector("#nombre-producto").value = producto.nombre;
    document.querySelector("#cantidad-producto").value =
        producto.cantidad_disponible;
    document.querySelector("#precio-producto").value = producto.precio;

    guardarProducto.textContent = "Guardar cambios";
    cancelarEdicion.hidden = false;
    mensajeProducto.textContent = "";
    mensajeProducto.classList.remove("error");

    document.querySelector("#nombre-producto").focus();
}

/** Limpia el formulario y lo devuelve al modo de alta. */
function volverAlAlta() {
    idProductoEnEdicion = null;
    formularioProducto.reset();
    document.querySelector("#titulo-alta").textContent = "Agregar producto";
    guardarProducto.textContent = "Guardar producto";
    cancelarEdicion.hidden = true;
}

cancelarEdicion.addEventListener("click", () => {
    volverAlAlta();
    mensajeProducto.textContent = "";
    mensajeProducto.classList.remove("error");
});


/** Muestra un estado de carga, error o ausencia de resultados. */
function mostrarEstado(mensaje, esError = false) {
    estado.textContent = mensaje;
    estado.classList.toggle("error", esError);
    estado.hidden = false;
    tablaContenedor.hidden = true;
}

/** Normaliza texto para buscar sin distinguir mayúsculas ni tildes. */
function normalizar(texto) {
    return String(texto).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

/** Construye la tabla con texto, sin interpretar nombres como HTML. */
function mostrarProductos() {
    const consulta = normalizar(buscar.value.trim());
    const visibles = productos.filter(producto =>
        normalizar(producto.nombre).includes(consulta) ||
        String(producto.id_producto).includes(consulta)
    );

    cuerpoTabla.replaceChildren();
    cantidadResultados.textContent = `${entero.format(visibles.length)} de ${entero.format(productos.length)} productos`;

    if (productos.length === 0) {
        mostrarEstado("Todavía no hay productos registrados en el inventario.");
        return;
    }
    if (visibles.length === 0) {
        mostrarEstado("No encontramos productos con esa búsqueda. Probá con otro nombre o ID.");
        return;
    }

    const fragmento = document.createDocumentFragment();
    for (const producto of visibles) {
        const fila = document.createElement("tr");
        const valores = [
            `#${producto.id_producto}`,
            producto.nombre,
            entero.format(producto.cantidad_disponible),
            moneda.format(producto.precio),
        ];
        valores.forEach((valor, indice) => {
            const celda = document.createElement("td");
            celda.textContent = valor;
            if (indice >= 2) celda.className = "numero";
            fila.append(celda);
        });
        const celdaEstado = document.createElement("td");
        const etiqueta = document.createElement("span");
        const disponible = producto.cantidad_disponible > 0;
        etiqueta.className = disponible ? "disponibilidad" : "disponibilidad agotado";
        etiqueta.textContent = disponible ? "Disponible" : "Sin stock";
        celdaEstado.append(etiqueta);
        fila.append(celdaEstado);

        // Cada botón conserva el producto correspondiente a su fila.
        const celdaAcciones = document.createElement("td");
        const botonEditar = document.createElement("button");
        botonEditar.type = "button";
        botonEditar.className = "boton-editar";
        botonEditar.textContent = "Editar";
        botonEditar.setAttribute("aria-label", `Editar ${producto.nombre}`);
        botonEditar.addEventListener("click", () => iniciarEdicion(producto));
        celdaAcciones.append(botonEditar);

        // El botón Eliminar pide confirmación antes de llamar a la API.
        const botonEliminar = document.createElement("button");
        botonEliminar.type = "button";
        botonEliminar.className = "boton-eliminar";
        botonEliminar.textContent = "Eliminar";
        botonEliminar.setAttribute("aria-label", `Eliminar ${producto.nombre}`);
        botonEliminar.addEventListener("click", () => eliminarProducto(producto));
        celdaAcciones.append(botonEliminar);
        fila.append(celdaAcciones);
        fragmento.append(fila);
    }
    cuerpoTabla.append(fragmento);
    estado.hidden = true;
    tablaContenedor.hidden = false;
}

/** Comprueba que la respuesta tenga el formato acordado con el backend. */
function esProductoValido(producto) {
    return producto !== null && typeof producto === "object" &&
        Number.isInteger(producto.id_producto) && producto.id_producto > 0 &&
        typeof producto.nombre === "string" && producto.nombre.trim() !== "" &&
        Number.isInteger(producto.cantidad_disponible) && producto.cantidad_disponible >= 0 &&
        typeof producto.precio === "number" && Number.isFinite(producto.precio) && producto.precio >= 0;
}

/** Actualiza el catálogo desde la API y permite reintentar si falla. */
async function cargarProductos() {
    actualizar.disabled = true;
    buscar.disabled = true;
    document.querySelector(".catalogo").setAttribute("aria-busy", "true");
    mostrarEstado("Cargando productos…");
    cantidadResultados.textContent = "Consultando inventario…";
    for (const selector of ["#total-productos", "#total-unidades", "#sin-stock"]) {
        document.querySelector(selector).textContent = "—";
    }
    const controlador = new AbortController();
    const temporizador = setTimeout(() => controlador.abort(), 10000);
    try {
        const respuesta = await fetch("/api/productos", {
            headers: { "Accept": "application/json" },
            cache: "no-store",
            signal: controlador.signal,
        });
        if (!respuesta.ok) throw new Error(`Respuesta HTTP ${respuesta.status}`);
        const datos = await respuesta.json();
        if (!Array.isArray(datos) || !datos.every(esProductoValido)) {
            throw new Error("El formato de los productos no es válido.");
        }
        productos = datos;
        document.querySelector("#total-productos").textContent = entero.format(productos.length);
        document.querySelector("#total-unidades").textContent = entero.format(
            productos.reduce((total, producto) => total + producto.cantidad_disponible, 0)
        );
        document.querySelector("#sin-stock").textContent = entero.format(
            productos.filter(producto => producto.cantidad_disponible === 0).length
        );
        document.querySelector("#ultima-actualizacion").textContent = `Actualizado a las ${new Intl.DateTimeFormat("es-AR", { hour: "2-digit", minute: "2-digit" }).format(new Date())}`;
        buscar.disabled = false;
        mostrarProductos();
    } catch (error) {
        productos = [];
        cuerpoTabla.replaceChildren();
        cantidadResultados.textContent = "Inventario no disponible";
        document.querySelector("#ultima-actualizacion").textContent = "Actualización pendiente";
        mostrarEstado("No pudimos cargar el inventario. Verificá que el servidor esté funcionando y presioná Actualizar.", true);
        console.error("Error al consultar productos:", error);
    } finally {
        clearTimeout(temporizador);
        actualizar.disabled = false;
        document.querySelector(".catalogo").setAttribute("aria-busy", "false");
    }
}

buscar.addEventListener("input", mostrarProductos);
actualizar.addEventListener("click", cargarProductos);
cargarProductos();

// Formulario para enviar nuevos productos al backend.
const formularioProducto = document.querySelector("#formulario-producto");
const camposProducto = document.querySelector("#campos-producto");
const guardarProducto = document.querySelector("#guardar-producto");
const mensajeProducto = document.querySelector("#mensaje-producto");

/** Envía un alta o una modificación según el modo del formulario. */
async function guardarNuevoProducto(evento) {
    evento.preventDefault();

    if (camposProducto.disabled || !formularioProducto.reportValidity()) {
        return;
    }

    const nombre = document.querySelector("#nombre-producto").value.trim();
    const cantidad = document.querySelector("#cantidad-producto").valueAsNumber;
    const precio = document.querySelector("#precio-producto").valueAsNumber;

    mensajeProducto.textContent = "";
    mensajeProducto.classList.remove("error");

    if (
        nombre === "" ||
        !Number.isInteger(cantidad) ||
        cantidad < 0 ||
        !Number.isFinite(precio) ||
        precio < 0
    ) {
        mensajeProducto.textContent =
            "Completá un nombre, una cantidad entera no negativa y un precio válido.";
        mensajeProducto.classList.add("error");
        return;
    }

    // Capturamos el modo antes de enviar y evitamos envíos repetidos.
    const esEdicion = idProductoEnEdicion !== null;
    const url = esEdicion
        ? `/api/productos/${idProductoEnEdicion}`
        : "/api/productos";
    camposProducto.disabled = true;
    guardarProducto.textContent = "Guardando…";

    try {
        const respuesta = await fetch(url, {
            method: esEdicion ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            body: JSON.stringify({
                nombre: nombre,
                cantidad_disponible: cantidad,
                precio: precio,
            }),
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo guardar el producto.");
        }

        volverAlAlta();
        buscar.value = "";

        mensajeProducto.textContent = esEdicion
            ? `Producto #${resultado.id_producto} actualizado correctamente.`
            : `Producto "${resultado.nombre}" guardado con ID ${resultado.id_producto}.`;

        await cargarProductos();
    } catch (error) {
        mensajeProducto.textContent =
            `${error.message} Actualizá el catálogo para comprobar los datos ` +
            "antes de volver a enviarlos.";
        mensajeProducto.classList.add("error");
    } finally {
        camposProducto.disabled = false;
        guardarProducto.textContent = idProductoEnEdicion === null
            ? "Guardar producto"
            : "Guardar cambios";
    }
}

formularioProducto.addEventListener("submit", guardarNuevoProducto);

/** Elimina un producto después de pedir confirmación al usuario. */
async function eliminarProducto(producto) {
    const confirmado = window.confirm(
        `¿Eliminar "${producto.nombre}" (ID ${producto.id_producto})? ` +
        "Esta acción no se puede deshacer."
    );
    if (!confirmado) {
        return;
    }

    mensajeProducto.textContent = "";
    mensajeProducto.classList.remove("error");

    try {
        const respuesta = await fetch(`/api/productos/${producto.id_producto}`, {
            method: "DELETE",
            headers: { "Accept": "application/json" },
        });
        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo eliminar el producto.");
        }

        // Si justo se estaba editando ese producto, se vuelve al modo alta.
        if (idProductoEnEdicion === producto.id_producto) {
            volverAlAlta();
        }

        await cargarProductos();
        mensajeProducto.textContent = `Producto "${resultado.nombre}" eliminado correctamente.`;
    } catch (error) {
        mensajeProducto.textContent = error.message;
        mensajeProducto.classList.add("error");
    }
}