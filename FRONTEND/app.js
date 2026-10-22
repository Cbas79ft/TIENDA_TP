"use strict";

/*
 * app.js: interacción de las pantallas del frontend (JavaScript nativo, sin librerías).
 * Se carga desde index.html y desde compra.html; cada página declara su tipo en
 * <body data-pagina="..."> y solo se ejecuta el código de esa pantalla.
 *
 * Pantalla de inventario (index.html), funcion iniciarInventario:
 * Consulta GET /api/productos mediante fetch, valida la respuesta JSON,
 * construye la tabla y calcula el resumen de productos y existencias.
 * Permite buscar por nombre o ID y volver a consultar con Actualizar.
 * Gestiona los estados de carga, error, inventario vacío y búsqueda sin
 * resultados. Envía altas con POST, modificaciones con PUT y bajas con DELETE.
 * El backend se encarga de escribir en SQLite y actualizar el TDA.
 * Registra clientes en espera, consulta su orden FIFO y muestra avisos
 * de notificación simulada cuando se repone un producto.
 *
 * Pantalla de compra (compra.html), funcion iniciarCompra:
 * Muestra el catálogo con la popularidad de cada producto (GET /api/recomendados)
 * y arma un carrito local en el navegador.
 */

// Cada pantalla vive en su función para que sus variables no se mezclen.
const pagina = document.body.dataset.pagina;
if (pagina === "compra") {
    iniciarCompra();
} else {
    iniciarInventario();
}

/** Pantalla de inventario y clientes en espera. */
function iniciarInventario() {
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
            const botonEspera = document.createElement("button");
            botonEspera.type = "button";
            botonEspera.className = "boton-espera";
            botonEspera.textContent = disponible ? "Ver espera" : "Anotar cliente";
            botonEspera.setAttribute("aria-label", `Consultar espera de ${producto.nombre}`);
            botonEspera.addEventListener("click", () => abrirEspera(producto.id_producto));
            celdaAcciones.append(botonEspera);
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
            sincronizarProductosEspera();
            await cargarEsperaSeleccionada();
        } catch (error) {
            productos = [];
            cuerpoTabla.replaceChildren();
            cantidadResultados.textContent = "Inventario no disponible";
            document.querySelector("#ultima-actualizacion").textContent = "Actualización pendiente";
            mostrarEstado("No pudimos cargar el inventario. Verificá que el servidor esté funcionando y presioná Actualizar.", true);
            sincronizarProductosEspera();
            await cargarEsperaSeleccionada();
            console.error("Error al consultar productos:", error);
        } finally {
            clearTimeout(temporizador);
            actualizar.disabled = false;
            document.querySelector(".catalogo").setAttribute("aria-busy", "false");
        }
    }

    buscar.addEventListener("input", mostrarProductos);
    actualizar.addEventListener("click", cargarProductos);

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

            if (resultado.notificacion) {
                document.querySelector("#aviso-reposicion").textContent = resultado.notificacion.mensaje;
                document.querySelector("#notificacion-reposicion").hidden = false;
            }

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

    // La API conserva el orden de la cola; esta sección solo presenta sus datos.
    const productoEspera = document.querySelector("#producto-espera");
    const clienteEspera = document.querySelector("#cliente-espera");
    const formularioEspera = document.querySelector("#formulario-espera");
    const camposEspera = document.querySelector("#campos-espera");
    const registrarEspera = document.querySelector("#registrar-espera");
    const actualizarEsperas = document.querySelector("#actualizar-esperas");
    const estadoClientes = document.querySelector("#estado-clientes");
    const reglaEspera = document.querySelector("#regla-espera");
    const mensajeEspera = document.querySelector("#mensaje-espera");
    const estadoCola = document.querySelector("#estado-cola");
    const listaEsperas = document.querySelector("#lista-esperas");
    const fechaEspera = new Intl.DateTimeFormat("es-AR", {
        dateStyle: "short", timeStyle: "short",
    });
    let clientesEspera = [];
    let esperasVisibles = [];
    let clientesDisponibles = false;
    let colaDisponible = false;
    let cargandoClientes = false;
    let cargandoCola = false;
    let guardandoEspera = false;
    let versionConsultaCola = 0;

    /** Consulta JSON con un tiempo límite; nunca reintenta una escritura. */
    async function solicitarDatosEspera(url, opciones = {}) {
        const controlador = new AbortController();
        const temporizador = setTimeout(() => controlador.abort(), 10000);
        try {
            const respuesta = await fetch(url, {
                ...opciones,
                headers: { "Accept": "application/json", ...opciones.headers },
                cache: "no-store",
                signal: controlador.signal,
            });
            const datos = await respuesta.json();
            if (!respuesta.ok) {
                throw new Error(datos.error || "No se pudo completar la solicitud.");
            }
            return datos;
        } catch (error) {
            if (error.name === "AbortError") {
                throw new Error("El servidor tardó demasiado en responder.");
            }
            throw error;
        } finally {
            clearTimeout(temporizador);
        }
    }

    /** Habilita el registro solo con un producto agotado y datos disponibles. */
    function actualizarControlesEspera() {
        const producto = productos.find(p => p.id_producto === Number(productoEspera.value));
        const puedeAnotar = Boolean(producto && producto.cantidad_disponible === 0 &&
            clientesDisponibles && colaDisponible && !cargandoClientes && !cargandoCola);
        camposEspera.disabled = guardandoEspera;
        productoEspera.disabled = guardandoEspera || productos.length === 0;
        clienteEspera.disabled = guardandoEspera || !puedeAnotar || clientesEspera.length === 0;
        registrarEspera.disabled = guardandoEspera || !puedeAnotar || clienteEspera.value === "";
        registrarEspera.textContent = guardandoEspera ? "Registrando…" : "Anotar cliente en espera";
        actualizarEsperas.disabled = guardandoEspera || cargandoClientes || cargandoCola;
        reglaEspera.textContent = !producto
            ? "Seleccioná un producto para consultar su espera."
            : producto.cantidad_disponible > 0
                ? "Este producto tiene stock. Podés consultar su cola, pero no agregar nuevas esperas."
                : "Producto sin stock: los clientes se atienden en orden de llegada al reponer.";
    }

    /** Reconstruye el selector sin perder el producto elegido si todavía existe. */
    function sincronizarProductosEspera() {
        const seleccionado = productoEspera.value;
        productoEspera.replaceChildren(new Option("Seleccioná un producto", ""));
        for (const producto of productos) {
            productoEspera.append(new Option(
                `#${producto.id_producto} · ${producto.nombre} (${producto.cantidad_disponible === 0 ? "sin stock" : "con stock"})`,
                String(producto.id_producto)
            ));
        }
        if (productos.some(p => String(p.id_producto) === seleccionado)) {
            productoEspera.value = seleccionado;
        }
        actualizarControlesEspera();
    }

    /** Presenta clientes y marca a quienes ya esperan el producto elegido. */
    function mostrarClientesEspera() {
        const seleccionado = clienteEspera.value;
        clienteEspera.replaceChildren(new Option("Seleccioná un cliente", ""));
        const anotados = new Set(esperasVisibles.map(espera => espera.id_cliente));
        for (const cliente of clientesEspera) {
            const anotado = anotados.has(cliente.id_cliente);
            const opcion = new Option(
                `#${cliente.id_cliente} · ${cliente.nombre} ${cliente.apellido}${anotado ? " (ya está en espera)" : ""}`,
                String(cliente.id_cliente)
            );
            opcion.disabled = anotado;
            clienteEspera.append(opcion);
            if (!anotado && opcion.value === seleccionado) clienteEspera.value = seleccionado;
        }
        actualizarControlesEspera();
    }

    /** Carga los clientes registrados; el catálogo puede funcionar si falla. */
    async function cargarClientesEspera() {
        cargandoClientes = true;
        clientesDisponibles = false;
        estadoClientes.textContent = "Cargando clientes…";
        estadoClientes.classList.remove("error");
        actualizarControlesEspera();
        try {
            const datos = await solicitarDatosEspera("/api/clientes");
            if (!Array.isArray(datos) || !datos.every(cliente => cliente &&
                Number.isSafeInteger(cliente.id_cliente) && cliente.id_cliente > 0 &&
                typeof cliente.nombre === "string" && typeof cliente.apellido === "string")) {
                throw new Error("El formato de los clientes no es válido.");
            }
            clientesEspera = datos;
            clientesDisponibles = true;
            estadoClientes.textContent = datos.length === 0
                ? "No hay clientes registrados. Se necesita un cliente existente para anotarlo."
                : "Los clientes que ya esperan este producto aparecen deshabilitados.";
        } catch (error) {
            clientesEspera = [];
            estadoClientes.textContent = `${error.message} Usá Actualizar espera para reintentar.`;
            estadoClientes.classList.add("error");
        } finally {
            cargandoClientes = false;
            mostrarClientesEspera();
            dibujarColaEspera();
        }
    }

    /** Muestra el orden recibido del TDA sin interpretar nombres como HTML. */
    function dibujarColaEspera() {
        listaEsperas.replaceChildren();
        listaEsperas.hidden = !colaDisponible || esperasVisibles.length === 0;
        if (!colaDisponible) return;
        estadoCola.textContent = esperasVisibles.length === 0
            ? "Este producto no tiene clientes en espera."
            : `${entero.format(esperasVisibles.length)} ${esperasVisibles.length === 1 ? "cliente en espera" : "clientes en espera"}. Se atiende primero a quien figura al inicio.`;
        const clientesPorId = new Map(clientesEspera.map(cliente => [cliente.id_cliente, cliente]));
        esperasVisibles.forEach((espera, indice) => {
            const cliente = clientesPorId.get(espera.id_cliente);
            const elemento = document.createElement("li");
            const nombre = document.createElement("strong");
            nombre.textContent = cliente
                ? `${cliente.nombre} ${cliente.apellido}` : `Cliente #${espera.id_cliente}`;
            elemento.append(nombre);
            if (indice === 0) {
                const primero = document.createElement("span");
                primero.className = "primero-espera";
                primero.textContent = "Primero en espera";
                elemento.append(primero);
            }
            const detalle = document.createElement("span");
            detalle.className = "detalle-espera";
            detalle.textContent = `Espera #${espera.id_espera} · Ingreso: ${fechaEspera.format(new Date(espera.fecha_espera))}`;
            elemento.append(detalle);
            listaEsperas.append(elemento);
        });
    }

    /** Descarta respuestas viejas si el usuario cambia de producto mientras carga. */
    async function cargarEsperaSeleccionada() {
        const version = ++versionConsultaCola;
        const idProducto = Number(productoEspera.value);
        esperasVisibles = [];
        colaDisponible = false;
        cargandoCola = false;
        estadoCola.classList.remove("error");
        listaEsperas.replaceChildren();
        listaEsperas.hidden = true;
        mostrarClientesEspera();
        document.querySelector("#titulo-cola").textContent = "Orden de atención";
        if (!idProducto) {
            estadoCola.textContent = "Seleccioná un producto para ver sus clientes en espera.";
            document.querySelector("#cola-espera").setAttribute("aria-busy", "false");
            return;
        }
        const producto = productos.find(p => p.id_producto === idProducto);
        document.querySelector("#titulo-cola").textContent = `Espera de ${producto.nombre}`;
        cargandoCola = true;
        estadoCola.textContent = "Consultando clientes en espera…";
        document.querySelector("#cola-espera").setAttribute("aria-busy", "true");
        actualizarControlesEspera();
        try {
            const datos = await solicitarDatosEspera(`/api/productos/${idProducto}/esperas`);
            if (version !== versionConsultaCola) return;
            if (!Array.isArray(datos) || !datos.every(espera => espera &&
                Number.isSafeInteger(espera.id_espera) && espera.id_espera > 0 &&
                Number.isSafeInteger(espera.id_cliente) && espera.id_cliente > 0 &&
                espera.id_producto === idProducto && typeof espera.fecha_espera === "string" &&
                Number.isFinite(Date.parse(espera.fecha_espera)))) {
                throw new Error("El formato de las esperas no es válido.");
            }
            esperasVisibles = datos;
            colaDisponible = true;
            dibujarColaEspera();
        } catch (error) {
            if (version !== versionConsultaCola) return;
            estadoCola.textContent = `${error.message} Usá Actualizar espera para reintentar.`;
            estadoCola.classList.add("error");
        } finally {
            if (version === versionConsultaCola) {
                cargandoCola = false;
                document.querySelector("#cola-espera").setAttribute("aria-busy", "false");
                mostrarClientesEspera();
            }
        }
    }

    /** Abre la consulta desde la fila del catálogo, incluso si tiene stock. */
    function abrirEspera(idProducto) {
        if (guardandoEspera) return;
        productoEspera.value = String(idProducto);
        mensajeEspera.textContent = "";
        mensajeEspera.classList.remove("error");
        cargarEsperaSeleccionada();
        document.querySelector("#seccion-esperas").scrollIntoView({ block: "start" });
        productoEspera.focus({ preventScroll: true });
    }

    /** Guarda una espera y vuelve a consultar su posición confirmada por el servidor. */
    async function guardarEspera(evento) {
        evento.preventDefault();
        if (guardandoEspera || registrarEspera.disabled || !formularioEspera.reportValidity()) return;
        const idProducto = Number(productoEspera.value);
        const idCliente = Number(clienteEspera.value);
        guardandoEspera = true;
        mensajeEspera.textContent = "";
        mensajeEspera.classList.remove("error");
        actualizarControlesEspera();
        try {
            await solicitarDatosEspera("/api/esperas", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_cliente: idCliente, id_producto: idProducto }),
            });
            clienteEspera.value = "";
            mensajeEspera.textContent = "Cliente registrado en espera correctamente.";
            await cargarEsperaSeleccionada();
        } catch (error) {
            mensajeEspera.textContent = `${error.message} Consultá la cola antes de volver a enviarlo.`;
            mensajeEspera.classList.add("error");
            // Si el stock cambió o se perdió la respuesta, consulta lo que quedó guardado.
            await cargarProductos();
        } finally {
            guardandoEspera = false;
            actualizarControlesEspera();
        }
    }

    productoEspera.addEventListener("change", () => {
        mensajeEspera.textContent = "";
        mensajeEspera.classList.remove("error");
        cargarEsperaSeleccionada();
    });
    clienteEspera.addEventListener("change", actualizarControlesEspera);
    formularioEspera.addEventListener("submit", guardarEspera);
    actualizarEsperas.addEventListener("click", () => {
        cargarClientesEspera();
        cargarProductos();
    });

    // Se inicia después de declarar todos los controles de ambas secciones.
    cargarProductos();
    cargarClientesEspera();
}

/** Pantalla de compra: catálogo, popularidad y carrito. */
function iniciarCompra() {
    const listaProductos = document.querySelector("#productos");
    const estado = document.querySelector("#estado");
    const buscar = document.querySelector("#buscar");
    const orden = document.querySelector("#orden");
    const cantidadResultados = document.querySelector("#cantidad-resultados");
    const resumenCarrito = document.querySelector("#resumen-carrito");
    const totalCarrito = document.querySelector("#total-carrito");
    const vaciarCarrito = document.querySelector("#vaciar-carrito");
    const moneda = new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" });
    const entero = new Intl.NumberFormat("es-AR");

    let productos = [];
    const carrito = new Map();

    function normalizar(texto) {
        return String(texto).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    }

    async function pedirJSON(ruta) {
        const respuesta = await fetch(ruta, {
            headers: { Accept: "application/json" },
            cache: "no-store"
        });
        if (!respuesta.ok) throw new Error(`Error HTTP ${respuesta.status}`);
        return respuesta.json();
    }

    function mostrarCarrito() {
        let unidades = 0;
        let total = 0;
        for (const [id, cantidad] of carrito) {
            const producto = productos.find(item => item.id_producto === id);
            if (!producto) continue;
            unidades += cantidad;
            total += producto.precio * cantidad;
        }
        resumenCarrito.textContent = unidades
            ? `${entero.format(unidades)} ${unidades === 1 ? "unidad" : "unidades"} en el carrito`
            : "Todavía no agregaste productos.";
        totalCarrito.textContent = moneda.format(total);
        vaciarCarrito.disabled = unidades === 0;
    }

    function agregarAlCarrito(idProducto) {
        const producto = productos.find(item => item.id_producto === idProducto);
        if (!producto || producto.cantidad_disponible <= 0) return;
        const cantidadActual = carrito.get(idProducto) || 0;
        if (cantidadActual >= producto.cantidad_disponible) {
            window.alert("No podés agregar más unidades que las disponibles en stock.");
            return;
        }
        carrito.set(idProducto, cantidadActual + 1);
        mostrarCarrito();
        mostrarProductos();
    }

    function mostrarProductos() {
        const consulta = normalizar(buscar.value.trim());
        let visibles = productos.filter(producto =>
            normalizar(producto.nombre).includes(consulta) ||
            String(producto.id_producto).includes(consulta)
        );

        if (orden.value === "nombre") {
            visibles.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
        } else if (orden.value === "precio") {
            visibles.sort((a, b) => a.precio - b.precio || a.id_producto - b.id_producto);
        } else {
            visibles.sort((a, b) => b.popularidad - a.popularidad || a.id_producto - b.id_producto);
        }

        listaProductos.replaceChildren();
        cantidadResultados.textContent = `${entero.format(visibles.length)} de ${entero.format(productos.length)} productos`;
        if (!visibles.length) {
            estado.hidden = false;
            estado.classList.remove("error");
            estado.textContent = productos.length
                ? "No encontramos productos con esa búsqueda."
                : "Todavía no hay productos registrados.";
            return;
        }

        estado.hidden = true;
        const fragmento = document.createDocumentFragment();
        for (const producto of visibles) {
            const tarjeta = document.createElement("article");
            tarjeta.className = "producto";
            const superior = document.createElement("div");
            superior.className = "producto-superior";
            const id = document.createElement("span");
            id.className = "id-producto";
            id.textContent = `Producto #${producto.id_producto}`;
            const popular = document.createElement("span");
            popular.className = "etiqueta-popular";
            popular.textContent = producto.popularidad
                ? `★ ${entero.format(producto.popularidad)} ${producto.popularidad === 1 ? "compra" : "compras"}`
                : "Sin compras";
            superior.append(id, popular);

            const nombre = document.createElement("h3");
            nombre.textContent = producto.nombre;
            const precio = document.createElement("p");
            precio.className = "precio";
            precio.textContent = moneda.format(producto.precio);
            const stock = document.createElement("p");
            stock.className = producto.cantidad_disponible > 0 ? "stock" : "stock agotado";
            stock.textContent = producto.cantidad_disponible > 0
                ? `${entero.format(producto.cantidad_disponible)} disponibles`
                : "Sin stock";
            const boton = document.createElement("button");
            boton.type = "button";
            boton.className = "agregar";
            boton.textContent = producto.cantidad_disponible > 0
                ? `Agregar al carrito${carrito.has(producto.id_producto) ? ` · ${carrito.get(producto.id_producto)}` : ""}`
                : "Sin stock";
            boton.disabled = producto.cantidad_disponible <= 0;
            boton.addEventListener("click", () => agregarAlCarrito(producto.id_producto));
            tarjeta.append(superior, nombre, precio, stock, boton);
            fragmento.append(tarjeta);
        }
        listaProductos.append(fragmento);
    }

    async function cargarCatalogo() {
        estado.hidden = false;
        estado.classList.remove("error");
        estado.textContent = "Cargando productos y popularidad…";
        buscar.disabled = true;
        orden.disabled = true;
        try {
            const [inventario, recomendados] = await Promise.all([
                pedirJSON("/api/productos"),
                pedirJSON("/api/recomendados?cantidad=50")
            ]);
            if (!Array.isArray(inventario) || !Array.isArray(recomendados)) {
                throw new Error("El servidor devolvió datos con un formato inesperado.");
            }
            const popularidadPorId = new Map(
                recomendados.map(producto => [producto.id_producto, producto.popularidad])
            );
            productos = inventario.map(producto => ({
                ...producto,
                popularidad: popularidadPorId.get(producto.id_producto) || 0
            }));
            buscar.disabled = false;
            orden.disabled = false;
            mostrarProductos();
            mostrarCarrito();
        } catch (error) {
            estado.hidden = false;
            estado.classList.add("error");
            estado.textContent = "No se pudo cargar el catálogo y la popularidad. Verificá que el servidor esté funcionando y actualizá la página.";
            console.error("Error al cargar la compra:", error);
        }
    }

    buscar.addEventListener("input", mostrarProductos);
    orden.addEventListener("change", mostrarProductos);
    vaciarCarrito.addEventListener("click", () => {
        carrito.clear();
        mostrarCarrito();
        mostrarProductos();
    });

    cargarCatalogo();
}