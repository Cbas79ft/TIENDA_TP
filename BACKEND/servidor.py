"""Servidor HTTP nativo para la interfaz de la tienda."""

"""Servidor HTTP de la tienda y rutas de su API."""

import sqlite3
from threading import Lock
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from BACKEND.inventario import cargar_inventario, consultar_productos, agregar_producto, modificar_producto


class ManejadorTienda(SimpleHTTPRequestHandler):
    """Atiende consultas de la API y entrega archivos del frontend."""

    def __init__(self, *args, inventario, bloqueo, **kwargs):
        """Recibe el inventario compartido antes de atender la solicitud y el bloqueo compartido."""
        self.inventario = inventario
        self.bloqueo = bloqueo
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Consulta productos o entrega archivos del frontend."""
        ruta = urlsplit(self.path).path

        # Solo esta dirección devuelve el inventario en JSON.
        if ruta == "/api/productos":
            with self.bloqueo:
                productos = consultar_productos(self.inventario)

            self.responder_json(200, productos)
            return

        # Las rutas de API desconocidas devuelven un error.
        if ruta == "/api" or ruta.startswith("/api/"):
            self.responder_json(
                404, {"error": "Ruta de API inexistente."}
            )
            return

        # Las demás solicitudes reciben los archivos del frontend.
        super().do_GET()

    def responder_json(self, codigo, datos):
        """Envía una respuesta HTTP con contenido JSON."""
        contenido = json.dumps(
            datos,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

        self.send_response(codigo)
        self.send_header(
            "Content-Type", "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenido)

    def do_POST(self):
        """Registra un producto recibido desde el frontend."""
        ruta = urlsplit(self.path).path

        if ruta != "/api/productos":
            self.responder_json(404, {"error": "Ruta inexistente."})
            return

        if self.headers.get_content_type() != "application/json":
            self.responder_json(
                415, {"error": "El contenido debe ser JSON."}
            )
            return

        # Comprobamos cuánto contenido envió el navegador.
        try:
            longitud = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.responder_json(
                400, {"error": "Longitud del contenido inválida."}
            )
            return

        if longitud <= 0 or longitud > 65536:
            self.responder_json(
                400,
                {"error": "El contenido está vacío o es demasiado grande."},
            )
            return

        # Convertimos el JSON recibido en datos de Python.
        try:
            contenido = self.rfile.read(longitud)
            datos = json.loads(contenido.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            self.responder_json(
                400, {"error": "El contenido no es un JSON válido."}
            )
            return

        campos = {"nombre", "cantidad_disponible", "precio"}

        if not isinstance(datos, dict) or set(datos) != campos:
            self.responder_json(
                400,
                {
                    "error": (
                        "Enviá únicamente nombre, cantidad_disponible "
                        "y precio. El ID lo genera SQLite."
                    )
                },
            )
            return

        try:
            # La lógica del inventario valida, guarda en SQLite
            # e incorpora el producto al TDA.
            with self.bloqueo:
                producto = agregar_producto(
                    self.inventario,
                    datos["nombre"],
                    datos["cantidad_disponible"],
                    datos["precio"],
                )
        except ValueError as error:
            self.responder_json(400, {"error": str(error)})
            return
        except sqlite3.Error:
            self.log_error("No se pudo guardar el producto en SQLite.")
            self.responder_json(
                500, {"error": "No se pudo guardar el producto."}
            )
            return

        # 201 significa que el producto fue creado.
        self.responder_json(201, producto)
        
    def do_PUT(self):
        """Modifica un producto identificado por la ruta /api/productos/ID."""
        ruta = urlsplit(self.path).path
        partes = ruta.strip("/").split("/")

        # Esperamos una dirección como /api/productos/3.
        if len(partes) != 3 or partes[:2] != ["api", "productos"]:
            self.responder_json(404, {"error": "Ruta inexistente."})
            return

        try:
            id_producto = int(partes[2])
            if id_producto <= 0:
                raise ValueError
        except ValueError:
            self.responder_json(
                400, {"error": "El ID debe ser un entero positivo."}
            )
            return

        if self.headers.get_content_type() != "application/json":
            self.responder_json(
                415, {"error": "El contenido debe ser JSON."}
            )
            return

        try:
            longitud = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.responder_json(
                400, {"error": "Longitud del contenido inválida."}
            )
            return

        if longitud <= 0 or longitud > 65536:
            self.responder_json(
                400, {"error": "Contenido vacío o demasiado grande."}
            )
            return

        try:
            datos = json.loads(
                self.rfile.read(longitud).decode("utf-8")
            )
        except (UnicodeDecodeError, ValueError, RecursionError):
            self.responder_json(
                400, {"error": "El contenido no es un JSON válido."}
            )
            return

        campos = {"nombre", "cantidad_disponible", "precio"}

        if not isinstance(datos, dict) or set(datos) != campos:
            self.responder_json(
                400,
                {
                    "error": (
                        "Enviá únicamente nombre, cantidad_disponible y precio."
                    )
                },
            )
            return

        try:
            # Usamos el mismo bloqueo que GET y POST.
            with self.bloqueo:
                producto = modificar_producto(
                    self.inventario,
                    id_producto,
                    datos["nombre"],
                    datos["cantidad_disponible"],
                    datos["precio"],
                )
        except ValueError as error:
            self.responder_json(400, {"error": str(error)})
            return
        except sqlite3.Error:
            self.log_error("No se pudo modificar el producto en SQLite.")
            self.responder_json(
                500, {"error": "No se pudo modificar el producto."}
            )
            return

        if producto is None:
            self.responder_json(
                404, {"error": "El producto no existe."}
            )
            return

        self.responder_json(200, producto) 


def iniciar_servidor(host="127.0.0.1", puerto=8000):
    """Carga el inventario y sirve la API y los archivos del frontend."""
    carpeta_frontend = Path(__file__).resolve().parent.parent / "FRONTEND"

    # Se carga una sola vez al iniciar, no en cada solicitud.
    inventario = cargar_inventario()
    bloqueo = Lock()

    # Cada solicitud recibe el mismo inventario y carpeta del frontend.
    manejador = partial(
        ManejadorTienda,
        inventario=inventario,
        bloqueo=bloqueo,
        directory=str(carpeta_frontend),
    )

    with ThreadingHTTPServer((host, puerto), manejador) as servidor:
        print(f"Tienda disponible en http://{host}:{servidor.server_port}")
        print("Presioná Ctrl+C para detener el servidor.")

        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    iniciar_servidor()
