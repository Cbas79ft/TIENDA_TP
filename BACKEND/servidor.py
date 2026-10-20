"""Servidor HTTP nativo para la interfaz de la tienda."""

"""Servidor HTTP de la tienda y rutas de su API."""

# Permite conexion a la base de datos.
import sqlite3
# controlar el acceso a recursos compartidos.
from threading import Lock
# Permite trabajar con formato JSON.
import json
# permite crear una nueva función a partir de otra.
from functools import partial
# simpleHTTP: Se encarga de atender solicitudes HTTP | Permite ejecutar un servidor HTTP capaz de atender múltiples solicitudes.
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
# permite trabajar con rutas de archivos y directorios de manera más sencilla.
from pathlib import Path
# permite separar una URL en sus diferentes componentes.
from urllib.parse import urlsplit

from BD import persistencia
from BACKEND.inventario import cargar_inventario, consultar_producto, consultar_productos, agregar_producto, modificar_producto, eliminar_producto
from BACKEND.esperas import cargar_colas, consultar_esperas, registrar_espera


class ManejadorTienda(SimpleHTTPRequestHandler):
    """Atiende consultas de la API y entrega archivos del frontend."""

    def __init__(self, *args, inventario, colas, bloqueo, **kwargs):
        """Recibe inventario, colas y bloqueo compartidos entre solicitudes."""
        self.inventario = inventario
        self.colas = colas
        self.bloqueo = bloqueo
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Consulta productos, clientes o esperas, o entrega el frontend."""
        ruta = urlsplit(self.path).path

        # Solo esta dirección devuelve el inventario en JSON.
        if ruta == "/api/productos":
            with self.bloqueo:
                productos = consultar_productos(self.inventario)

            self.responder_json(200, productos)
            return

        if ruta == "/api/clientes":
            try:
                with self.bloqueo:
                    clientes = persistencia.leer_clientes()
            except sqlite3.Error:
                self.log_error("No se pudieron consultar los clientes en SQLite.")
                self.responder_json(
                    500, {"error": "No se pudieron consultar los clientes."}
                )
                return

            self.responder_json(200, clientes)
            return

        partes = ruta.strip("/").split("/")
        if (
            len(partes) == 4
            and partes[:2] == ["api", "productos"]
            and partes[3] == "esperas"
        ):
            try:
                id_producto = int(partes[2])
                if not 0 < id_producto <= 9223372036854775807:
                    raise ValueError
            except ValueError:
                self.responder_json(
                    400, {"error": "El ID debe ser un entero positivo válido."}
                )
                return

            # El barrido rota la cola temporalmente: comparte el bloqueo
            # con el registro de esperas y la reposición del inventario.
            with self.bloqueo:
                producto = consultar_producto(self.inventario, id_producto)
                esperas = (
                    consultar_esperas(self.colas, id_producto)
                    if producto is not None else None
                )

            if esperas is None:
                self.responder_json(404, {"error": "El producto no existe."})
                return

            self.responder_json(200, esperas)
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
        """Registra un producto o una espera recibidos desde el frontend."""
        ruta = urlsplit(self.path).path

        if ruta not in ("/api/productos", "/api/esperas"):
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

        if ruta == "/api/esperas":
            self.registrar_espera_api(datos)
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

    def registrar_espera_api(self, datos):
        """Valida los IDs y registra una espera bajo el bloqueo compartido."""
        campos = {"id_cliente", "id_producto"}
        if not isinstance(datos, dict) or set(datos) != campos:
            self.responder_json(
                400,
                {"error": "Enviá únicamente id_cliente e id_producto."},
            )
            return

        # bool no es un ID. El límite evita desbordar los enteros de SQLite.
        for campo in campos:
            if (
                type(datos[campo]) is not int
                or not 0 < datos[campo] <= 9223372036854775807
            ):
                self.responder_json(
                    400,
                    {"error": f"{campo} debe ser un entero positivo válido."},
                )
                return

        try:
            with self.bloqueo:
                espera = registrar_espera(
                    self.colas, datos["id_cliente"], datos["id_producto"]
                )
        except ValueError as error:
            self.responder_json(400, {"error": str(error)})
            return
        except sqlite3.Error:
            self.log_error("No se pudo registrar la espera en SQLite.")
            self.responder_json(
                500, {"error": "No se pudo registrar la espera."}
            )
            return

        self.responder_json(201, espera)

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
                    colas=self.colas,
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

    def do_DELETE(self):
        """Elimina un producto identificado por la ruta /api/productos/ID."""
        ruta =  urlsplit(self.path).path
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

        try:
            #Usamos el mismo bloqueo que GET y POST.
            with self.bloqueo:
                producto = eliminar_producto(self.inventario, id_producto)
        except sqlite3.IntegrityError:
            """
            Las claves foráneas impiden borrar un producto que ya figura
            en compras o en la lista de espera. El inventario conserva el producto
            porque SQLite falla antes de tocar la lista.
            """
            self.responder_json(
                409,
                {
                    "error": (
                        "No se puede eliminar: el producto tiene compras"
                        "o clientes en espera asociados."
                    )
                }
            
            )
            return
        except sqlite3.Error:
            self.log_error("No se pudo eliminar el producto en SQLite.")
            self.responder_json(
                500, {"error": "No se pudo eliminar el producto"}
            )
            return
        if producto is None:
            self.responder_json(
                404, {"error": "El producto no existe."}
            )
            return

        #Devolvemos el producto eliminado para que la interfaz  lo informe.
        self.responder_json(200, producto)

def iniciar_servidor(host="127.0.0.1", puerto=8000):
    """Carga el inventario y sirve la API y los archivos del frontend."""
    carpeta_frontend = Path(__file__).resolve().parent.parent / "FRONTEND"

    # Se carga una sola vez al iniciar, no en cada solicitud.
    inventario = cargar_inventario()
    colas = cargar_colas()
    bloqueo = Lock()

    # Cada solicitud recibe el mismo inventario y carpeta del frontend.
    manejador = partial(
        ManejadorTienda,
        inventario=inventario,
        colas=colas,
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
