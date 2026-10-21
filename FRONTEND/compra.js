"use strict";

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
