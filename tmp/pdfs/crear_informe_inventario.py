"""Genera un informe explicativo del inventario implementado."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import pypdfium2 as pdfium

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / 'output/pdf/Funcionamiento_gestion_inventario.pdf'
SALIDA.parent.mkdir(parents=True, exist_ok=True)
azul = colors.HexColor('#173b3c')
verde = colors.HexColor('#e9f4ef')
estilos = getSampleStyleSheet()
estilos['BodyText'].fontSize = 10.5
estilos['BodyText'].leading = 15
estilos['BodyText'].spaceAfter = 9
estilos['Heading1'].fontSize = 20
estilos['Heading1'].leading = 24
estilos['Heading1'].textColor = azul
estilos['Heading2'].fontSize = 12.5
estilos['Heading2'].leading = 17
estilos['Heading2'].textColor = azul
estilos['Heading2'].spaceBefore = 12
estilos.add(ParagraphStyle(name='Portada', fontName='Helvetica-Bold', fontSize=28, leading=33, textColor=azul, spaceAfter=18))
estilos.add(ParagraphStyle(name='CodigoInventario', fontName='Courier', fontSize=9, leading=13, backColor=verde, borderPadding=9, spaceBefore=8, spaceAfter=16))
estilos.add(ParagraphStyle(name='Flujo', fontName='Helvetica-Bold', fontSize=11, leading=17, alignment=TA_CENTER, textColor=azul, backColor=verde, borderPadding=13, spaceBefore=12, spaceAfter=16))
elementos = []
def par(texto): elementos.append(Paragraph(texto, estilos['BodyText']))
def titulo(texto): elementos.append(Paragraph(texto, estilos['Heading1']))
def subtitulo(texto): elementos.append(Paragraph(texto, estilos['Heading2']))
def codigo(texto): elementos.append(Paragraph(texto, estilos['CodigoInventario']))
def pagina(): elementos.append(PageBreak())
def tabla(filas, anchos):
    datos = [[Paragraph(str(celda), estilos['BodyText']) for celda in fila] for fila in filas]
    objeto = Table(datos, colWidths=anchos, hAlign='LEFT')
    objeto.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), verde),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), .4, colors.HexColor('#dae4e1')),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elementos.append(objeto)

elementos.append(Paragraph('Gestión de inventario', estilos['Portada']))
par('<b>TIENDA TP | Informe de funcionamiento</b><br/>Algoritmos y Estructura de Datos III<br/>15 de octubre de 2026')
subtitulo('1. Objetivo del módulo')
par('Administrar productos con identificador, nombre, cantidad disponible y precio. El sistema combina una lista enlazada para operar en memoria, SQLite para conservar los registros y una interfaz web para consultar, agregar y editar productos.')
par('<b>Estado actual:</b> consulta, alta y edición están conectadas a la web. La eliminación está implementada en la lógica de inventario y persistencia, pero todavía no tiene ruta DELETE ni botón en pantalla.')
elementos.append(Paragraph('Navegador: HTML + CSS + JavaScript<br/>↓ fetch / JSON<br/>Servidor HTTP: rutas de la API<br/>↓<br/>Inventario: reglas y coordinación<br/>↓<br/>TDA Lista en memoria + persistencia SQLite', estilos['Flujo']))
subtitulo('2. Responsabilidades de cada archivo')
tabla([
    ['<b>Archivo</b>', '<b>Responsabilidad</b>'],
    ['main.py', 'Inicia el servidor al ejecutar el programa.'],
    ['BACKEND/servidor.py', 'Sirve el frontend, recibe HTTP y devuelve JSON.'],
    ['BACKEND/inventario.py', 'Coordina validaciones, TDA y persistencia.'],
    ['BACKEND/producto.py', 'Construye y valida el diccionario del producto.'],
    ['BACKEND/tad_listas.py', 'Encapsula los nodos, enlaces y primitivas de la lista.'],
    ['BD/persistencia.py', 'Abre conexiones y ejecuta el CRUD sobre SQLite.'],
    ['FRONTEND/', 'HTML: estructura; CSS: presentación; app.js: interacción y API.'],
], [175, 336])

pagina()
titulo('El producto y la lista enlazada')
subtitulo('3. Representación y validación')
codigo('{"id_producto": 3, "nombre": "Teclado",<br/> "cantidad_disponible": 10, "precio": 35000.0}')
par('crear_producto() exige un ID entero positivo, un nombre de texto no vacío, stock entero mayor o igual a cero y precio numérico finito no negativo. Elimina espacios de los extremos del nombre y devuelve el precio como float. Los booleanos no se aceptan como ID, cantidad o precio.')
par('SQLite asigna el ID definitivo. En el alta, la lógica usa temporalmente el valor 1 para validar los otros campos; ese ID provisional no se guarda ni se inserta en el TDA.')
subtitulo('4. Cómo se organiza el inventario')
codigo('inicio → [ID 1 | siguiente] → [ID 3 | siguiente]<br/>       → [ID 8 | None]')
par('Cada nodo almacena el diccionario en info y el enlace al siguiente nodo en sig. La lista es lineal y termina en None. Se mantiene ordenada por id_producto: por eso las altas con IDs crecientes aparecen al final. El orden no depende del nombre ni del precio.')
tabla([
    ['<b>Primitiva utilizada</b>', '<b>Aplicación</b>'],
    ['Lista()', 'Crea el inventario vacío.'],
    ['inserta1(..., "id_producto")', 'Inserta un diccionario en orden de ID.'],
    ['buscar1(..., "id_producto")', 'Localiza el nodo del ID solicitado.'],
    ['eliminar1(..., "id_producto")', 'Retira el producto y reconecta los nodos.'],
    ['barrido(inventario)', 'Recorre la lista y devuelve sus elementos.'],
], [210, 301])
subtitulo('5. Encapsulamiento y copias')
par('inventario.py llama a las primitivas y no recorre ni modifica los enlaces sig. Para una consulta individual lee info del nodo devuelto por buscar1(). El barrido fue adaptado para devolver datos en lugar de imprimirlos. En el archivo actual hay dos definiciones de barrido; Python utiliza la última.')
par('Las consultas devuelven copias de los diccionarios. Así, modificar un resultado no altera el inventario sin validación ni guardado. La copia superficial es suficiente porque los campos contienen solo texto y números.')
par('<b>Costo:</b> buscar, insertar ordenado, eliminar y recorrer pueden requerir O(n). La carga mediante inserciones ordenadas repetidas puede llegar a O(n²). La lista se utiliza para aplicar el TDA requerido por la consigna.')

pagina()
titulo('Inicio, consulta y alta')
subtitulo('6. Qué ocurre al iniciar')
par('1. main.py llama a iniciar_servidor().<br/>2. cargar_inventario() crea una Lista y pide los registros a persistencia.leer_productos().<br/>3. Cada registro se valida con crear_producto() y se inserta mediante inserta1().<br/>4. El servidor conserva esa misma lista para atender las solicitudes. No vuelve a leer toda la base en cada GET.')
par('Si no hay registros, se crea un inventario vacío. Si un registro persistido no cumple las reglas, la carga propaga el error en lugar de omitirlo silenciosamente.')
subtitulo('7. Consultar productos desde la pantalla')
par('1. app.js ejecuta fetch("/api/productos").<br/>2. do_GET() reconoce la ruta y llama a consultar_productos().<br/>3. barrido() obtiene los elementos y la lógica devuelve copias.<br/>4. responder_json() serializa los datos y devuelve HTTP 200.<br/>5. JavaScript construye las filas y calcula los indicadores de stock.')
par('La búsqueda por nombre o ID se realiza sobre la copia de productos recibida en JavaScript. No consulta SQLite por cada tecla ni modifica el orden del TDA. Los nombres se insertan con textContent para mostrarlos como texto.')
subtitulo('8. Agregar un producto')
par('1. El usuario completa el formulario; el navegador y JavaScript verifican los datos.<br/>2. Se envía POST /api/productos con nombre, cantidad_disponible y precio.<br/>3. El servidor comprueba el formato del pedido y llama a agregar_producto().<br/>4. La lógica vuelve a validar los datos, independientemente del frontend.<br/>5. insertar_producto() guarda el registro y devuelve el ID generado por SQLite.<br/>6. El producto recibe ese ID y se incorpora a la lista con inserta1().<br/>7. El servidor responde HTTP 201 con el diccionario creado.<br/>8. La pantalla limpia el formulario, quita el filtro y vuelve a consultar la API.')
subtitulo('Ejemplo de alta')
par('Si el último ID es 20, un alta podría recibir el ID 21. Un producto con nombre "Mouse USB", cantidad 5 y precio 12000 se guarda en SQLite y queda al final de la lista. El ID no se escribe en el formulario y los huecos de IDs no se rellenan necesariamente.')
par('Si SQLite falla, la función no llega a insertar en memoria. Si la respuesta se pierde después de guardar, el usuario debe actualizar el catálogo antes de reenviar, porque el alta podría haberse realizado.')

pagina()
titulo('Edición y eliminación')
subtitulo('9. Editar desde el catálogo')
par('Cada fila tiene un botón Editar. iniciarEdicion() copia sus valores al formulario, guarda el ID en idProductoEnEdicion, muestra Cancelar edición y cambia el botón principal a Guardar cambios.')
par('Al enviar, guardarNuevoProducto() distingue el modo: si el ID es null usa POST; si hay un ID usa PUT /api/productos/ID. El cuerpo contiene los tres campos editables; el identificador viaja en la dirección.')
par('En el backend, modificar_producto() busca el producto en el TDA, valida los datos y actualiza SQLite. Si se modificó el registro, elimina la versión anterior con eliminar1() e inserta la nueva con inserta1(). El ID se conserva y el producto mantiene su posición por ese criterio.')
par('Ante un ID inexistente la ruta devuelve HTTP 404. Ante datos inválidos devuelve 400. Si el guardado se confirma, devuelve 200, la interfaz vuelve al modo alta y recarga el catálogo. Cancelar edición limpia el formulario sin enviar cambios al servidor.')
subtitulo('Ejemplo de modificación')
par('El producto #3 tiene 10 unidades y precio 35000. Al cambiarlo a 15 unidades y precio 40000, el mismo ID #3 conserva su identidad. Los datos actualizados quedan en SQLite y en la lista; no se crea otro producto.')
subtitulo('10. Eliminación implementada en la lógica')
par('eliminar_producto() consulta primero el TDA. Si el ID existe, intenta borrar en SQLite y solo después retira el producto con eliminar1(). Devuelve una copia de lo eliminado o None cuando no se encuentra.')
par('Si una clave foránea impide borrar un producto asociado a compras o esperas, SQLite lanza IntegrityError. Como el error ocurre antes de retirar el nodo, el inventario permanece sin cambios.')
par('<b>Pendiente:</b> exponer esta operación mediante DELETE /api/productos/ID y agregar la acción correspondiente al frontend. La existencia de eliminar_producto() no significa que ya se pueda eliminar desde el navegador.')
subtitulo('11. Operaciones disponibles por HTTP')
tabla([
    ['<b>Método y ruta</b>', '<b>Función</b>', '<b>Éxito</b>'],
    ['GET /api/productos', 'Consultar el inventario completo.', '200'],
    ['POST /api/productos', 'Registrar un nuevo producto.', '201'],
    ['PUT /api/productos/ID', 'Actualizar los tres campos editables.', '200'],
    ['DELETE /api/productos/ID', 'Todavía no implementado en la API.', 'Pendiente'],
], [205, 231, 75])

pagina()
titulo('Persistencia, control y comprobación')
subtitulo('12. Cómo se conservan los registros')
par('persistencia.py resuelve BD/tablas.db desde la ubicación del propio archivo, abre una conexión para cada operación, activa foreign_keys y usa consultas parametrizadas. Las escrituras usan with conexion para confirmar o revertir la operación SQL; finally cierra la conexión.')
par('Al detener el programa, la lista desaparece de memoria, pero SQLite conserva los registros. En el siguiente inicio cargar_inventario() reconstruye la lista a partir de la base. Una modificación externa de tablas.db mientras el servidor está abierto no actualiza automáticamente la lista: el botón Actualizar consulta la memoria del servidor.')
subtitulo('13. Concurrencia y errores')
par('ThreadingHTTPServer puede atender varios pedidos en hilos diferentes. Un Lock compartido protege las consultas y las escrituras del inventario desde GET, POST y PUT para que no se intercalen esas operaciones dentro del mismo servidor.')
par('POST y PUT exigen application/json, un cuerpo declarado de hasta 65536 bytes y exactamente los campos nombre, cantidad_disponible y precio. Los errores de datos reciben 400, los tipos de contenido incorrectos 415, las rutas o productos ausentes 404 y los errores de SQLite 500.')
par('<b>Límite de consistencia:</b> el bloqueo no convierte a SQLite y al TDA en una única transacción. Si el proceso falla después de confirmar SQL y antes de actualizar la lista, puede existir una diferencia temporal; reiniciar reconstruye el inventario desde SQLite. Actualmente no hay recuperación automática de ese caso ni sincronización entre varios procesos.')
subtitulo('14. Qué se comprobó')
par('El usuario confirmó las pruebas temporales de alta, modificación y eliminación: persistencia, recuperación al recargar, datos inválidos, IDs inexistentes y eliminación bloqueada por claves foráneas. También confirmó la consulta web y el alta desde la pantalla.')
par('Para la interfaz de edición se verificaron sintaxis y lógica con DOM y API simulados: botón Editar, envío PUT, cancelación, conservación del modo ante error y alta POST. Esa verificación no sustituye una comprobación manual de edición contra SQLite desde el navegador.')
subtitulo('15. Guía breve de uso y prueba manual')
codigo('Desde la raíz TIENDA_TP: python -B main.py<br/>Pantalla: http://127.0.0.1:8000/<br/>Consulta JSON: http://127.0.0.1:8000/api/productos')
par('Agregar: completar y guardar; comprobar tabla y resumen. Editar: seleccionar una fila, cambiar datos y guardar; comprobar que el ID y la cantidad de productos no cambien. Reiniciar el servidor y verificar que los valores persistan. Las operaciones desde la pantalla escriben en la base real.')
par('<b>Alcance del informe:</b> describe el código actual del módulo de inventario. No implementa nuevas funciones ni cambia los registros de la tienda. La carpeta .git no se utiliza para generar este documento.')

def pie(lienzo, documento):
    lienzo.setStrokeColor(colors.HexColor('#d5e2dc'))
    lienzo.line(42, 38, A4[0]-42, 38)
    lienzo.setFont('Helvetica', 8)
    lienzo.setFillColor(azul)
    lienzo.drawString(42, 25, 'TIENDA TP | Gestión de inventario | 15/10/2026')
    lienzo.drawRightString(A4[0]-42, 25, str(documento.page))

SimpleDocTemplate(str(SALIDA), pagesize=A4, leftMargin=42, rightMargin=42, topMargin=40, bottomMargin=52, title='Funcionamiento de la gestión de inventario - TIENDA TP', author='TIENDA TP').build(elementos, onFirstPage=pie, onLaterPages=pie)
documento = pdfium.PdfDocument(str(SALIDA))
for numero in range(len(documento)):
    documento[numero].render(scale=1.1).to_pil().save(RAIZ / f'tmp/pdfs/inventario_informe_{numero+1}.png')
print(f'PDF: {SALIDA} | Páginas: {len(documento)}')
