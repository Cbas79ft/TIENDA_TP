from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader
import pypdfium2 as pdfium

OUT=Path('output/pdf/Informe_Punto_2_Clientes_en_Espera.pdf')
INK=HexColor('#173B3C'); GREEN=HexColor('#2C7563'); MUTED=HexColor('#54696C'); LIGHT=HexColor('#EDF5F1'); LINE=HexColor('#D6E3DF')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8,textColor=INK))
styles.add(ParagraphStyle(name='SmallReport',parent=styles['BodyReport'],fontSize=8.5,leading=11.5,spaceAfter=5,textColor=MUTED))
styles.add(ParagraphStyle(name='TitleReport',fontName='Helvetica-Bold',fontSize=27,leading=32,spaceAfter=12,textColor=INK))
styles.add(ParagraphStyle(name='HeadingReport',fontName='Helvetica-Bold',fontSize=19,leading=24,spaceAfter=13,textColor=INK))
styles.add(ParagraphStyle(name='SubReport',fontName='Helvetica-Bold',fontSize=11.5,leading=15,spaceBefore=10,spaceAfter=7,textColor=GREEN))
styles.add(ParagraphStyle(name='CellReport',parent=styles['BodyReport'],fontSize=9,leading=12,spaceAfter=0))
styles.add(ParagraphStyle(name='CellHeadReport',parent=styles['CellReport'],fontName='Helvetica-Bold',textColor=white))
styles.add(ParagraphStyle(name='CodeReport',fontName='Courier',fontSize=8.3,leading=12,textColor=INK,spaceAfter=8))
story=[]
def p(text,style='BodyReport'):
 return Paragraph(text,styles[style])
def add(text,style='BodyReport'):
 story.append(p(text,style))
def sub(text): add(text,'SubReport')
def table(head,rows,widths):
 data=[[p(escape(x),'CellHeadReport') for x in head]]+[[p(x,'CellReport') for x in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.6,INK),('LINEBELOW',(0,1),(-1,-1),.35,LINE)]))
 story.append(t); story.append(Spacer(1,9))
def numbered(items):
 for n,item in enumerate(items,1):add(f'<b>{n}.</b> {item}')
class QueueDiagram(Flowable):
 def __init__(self): Flowable.__init__(self);self.width=511;self.height=102
 def draw(self):
  c=self.canv;c.setFont('Helvetica-Bold',9);c.setFillColor(MUTED)
  c.drawString(0,89,'Producto de ejemplo: teclado sin stock')
  for x,label,order in [(0,'Ana','Primera'),(175,'Luis','Segunda'),(350,'Eva','Tercera')]:
   c.setFillColor(LIGHT);c.setStrokeColor(LINE);c.roundRect(x,28,155,45,6,fill=1,stroke=1)
   c.setFillColor(INK);c.setFont('Helvetica-Bold',11);c.drawString(x+12,54,label)
   c.setFillColor(MUTED);c.setFont('Helvetica',9);c.drawString(x+12,39,order+' en ingresar')
  for x in [157,332]:
   c.setStrokeColor(GREEN);c.line(x,50,x+15,50);c.line(x+15,50,x+11,54);c.line(x+15,50,x+11,46)
  c.setFillColor(GREEN);c.setFont('Helvetica-Bold',9);c.drawString(0,10,'Sale por el frente')
  c.drawRightString(505,10,'Los nuevos registros ingresan al final')

def frame(c,doc):
 w,h=A4;c.saveState();c.setFillColor(INK);c.rect(0,h-53,w,53,fill=1,stroke=0)
 c.setFont('Helvetica-Bold',12);c.setFillColor(white);c.drawString(42,h-32,'TIENDA TP')
 c.setFont('Helvetica',9);c.drawRightString(w-42,h-32,'INFORME DE IMPLEMENTACIÓN | PUNTO 2')
 c.setStrokeColor(LINE);c.line(42,38,w-42,38)
 c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(42,24,'Algoritmos y Estructura de Datos III | 20 de octubre de 2026')
 c.drawRightString(w-42,24,f'{doc.page} / 4');c.restoreState()

# Página 1
add('Registro de clientes<br/>en espera','TitleReport')
add('Informe técnico y funcional del punto 2 del trabajo práctico final.','SmallReport')
sub('1. Objetivo y alcance')
add('Gestionar a los clientes que solicitan un producto sin disponibilidad mediante el <b>TDA Cola de la cátedra</b>. Al reponer stock se simula la notificación al primer cliente y se lo retira de la espera, respetando el orden de llegada.')
add('El módulo está conectado con el inventario implementado mediante lista enlazada, una base SQLite, el servidor HTTP nativo y la interfaz web. El registro utiliza clientes existentes; el alta de nuevos clientes no forma parte de esta funcionalidad.')
sub('2. Reglas adoptadas')
table(['Regla','Comportamiento definido'],[
 ('Existencia','El cliente y el producto deben estar registrados.'),
 ('Disponibilidad','Solo se admiten nuevas esperas cuando el stock es cero.'),
 ('Duplicados','Una sola espera activa por cliente y producto. Un cliente puede esperar varios productos.'),
 ('Orden FIFO','Cada producto tiene una cola independiente: el primero que ingresa es el primero que se atiende.'),
 ('Reposición','El cambio de stock de cero a positivo atiende a un solo cliente, si hay alguien en espera.'),
 ('Notificación','Se genera un aviso simulado en pantalla. No se envía un correo, no se reserva ni se descuenta stock y no se registra una compra.'),
 ('Persistencia','Las esperas se guardan en SQLite y las colas se reconstruyen al iniciar el servidor.'),
 ('Errores','Si SQLite rechaza una operación, no se modifica la cola. La reposición y la eliminación de la espera se confirman juntas.'),
],[108,403])
sub('Referencia de la consigna')
add('Fuente: 02.TP-Final.TIENDA-III.2026.pdf, página 1, apartado "Registro de clientes en espera (TDA Cola)". Las reglas de duplicados, stock cero y una cola por producto concretan el funcionamiento acordado para el proyecto.','SmallReport')
story.append(PageBreak())

# Página 2
add('TDA Cola y organización','HeadingReport')
sub('3. Representación de las esperas')
add('Un diccionario relaciona cada <b>id_producto</b> con una instancia de <b>Cola</b>. El diccionario localiza la estructura; los registros se almacenan dentro del TDA. Cada registro contiene id_espera, id_cliente, id_producto y fecha_espera.')
story.append(QueueDiagram())
add('Ejemplo ilustrativo: aunque se repongan varias unidades, se atiende a Ana y la cola restante queda Luis, Eva. Una nueva llegada se incorpora después de Eva.','SmallReport')
sub('4. Primitivas utilizadas')
table(['Primitiva','Uso en el módulo'],[
 ('Cola / arribo','Crear la cola e incorporar una espera al final.'),
 ('cola_vacia / en_frente','Comprobar si hay registros y consultar al primero sin retirarlo.'),
 ('atencion','Retirar al primer registro después de confirmar la operación en SQLite.'),
 ('tamanio / mover_al_final','Consultar todos los registros mediante una vuelta completa, conservando el orden final.'),
],[155,356])
add('Las operaciones básicas arribo, atencion y en_frente son O(1). Consultar una cola con n registros es O(n) y genera una lista de copias para responder a la interfaz. El recorrido rota temporalmente la cola; por eso también se ejecuta bajo el bloqueo compartido. La lógica no manipula directamente frente, final ni sig.','SmallReport')
sub('5. Responsabilidades por archivo')
table(['Archivo del proyecto','Responsabilidad'],[
 ('BACKEND/tad_cola.py','Implementación de la estructura y sus primitivas.'),
 ('BACKEND/esperas.py','Carga, consulta, registro, preparación del aviso y retiro de la primera espera.'),
 ('BD/persistencia.py','Consultas SQL, validaciones del registro y guardado transaccional.'),
 ('BACKEND/inventario.py','Detección de la reposición y coordinación entre lista y cola.'),
 ('BACKEND/servidor.py','Rutas HTTP y bloqueo compartido entre solicitudes.'),
 ('FRONTEND/index.html, app.js y estilos.css','Controles, comunicación con la API, mensajes y presentación adaptable.'),
],[206,305])
story.append(PageBreak())

# Página 3
add('Persistencia y flujo de datos','HeadingReport')
sub('6. Almacenamiento en SQLite')
add('La tabla <b>esperas</b> pertenece a BD/tablas.db. Sus claves foráneas relacionan clientes y productos; la conexión activa PRAGMA foreign_keys = ON.')
table(['Campo','Tipo y restricción','Finalidad'],[
 ('id_espera','INTEGER, PK, AUTOINCREMENT','Identificar el registro y establecer el orden de llegada.'),
 ('id_cliente','INTEGER, NOT NULL, FK','Referenciar al cliente registrado.'),
 ('id_producto','INTEGER, NOT NULL, FK','Determinar la cola correspondiente.'),
 ('fecha_espera','TEXT, NOT NULL','Guardar el ingreso en formato ISO 8601 con zona UTC.'),
],[105,181,225])
add('El orden de reconstrucción es ORDER BY id_espera. La fecha permite mostrar el ingreso, pero no determina la prioridad. La prohibición de duplicados se comprueba dentro de una transacción BEGIN IMMEDIATE; el esquema actual no tiene una restricción UNIQUE para el par cliente-producto.','SmallReport')
sub('7. Registro de una nueva espera')
numbered([
 'La pantalla envía los identificadores del cliente y del producto. El servidor valida el JSON y los IDs.',
 'Bajo el bloqueo compartido, registrar_espera genera la fecha UTC y solicita el guardado.',
 'SQLite comprueba existencia, stock cero y ausencia de duplicados dentro de la misma transacción.',
 'Confirmado el guardado, arribo incorpora el registro a la cola. La API devuelve el registro creado.',
])
sub('8. Reposición y atención')
numbered([
 'El inventario compara el stock anterior con el nuevo. Solo el paso de cero a positivo activa la atención.',
 'Se consulta al primero y se prepara el mensaje sin retirar todavía la espera.',
 'SQLite verifica que sea la primera espera del producto y guarda el nuevo stock junto con la eliminación del registro. Si falla, revierte ambos cambios.',
 'Después de confirmar SQLite, se actualiza la lista y atencion retira al primero. La respuesta incluye el aviso simulado.',
])
add('Un único Lock del servidor coordina las solicitudes de inventario y colas. Al iniciar se reconstruyen las colas desde SQLite, sin depender de la memoria de la ejecución anterior. Las consultas de espera devuelven copias de los registros.','SmallReport')
story.append(PageBreak())

# Página 4
add('API, interfaz y verificación','HeadingReport')
sub('9. Rutas disponibles')
table(['Método y ruta','Resultado'],[
 ('GET /api/clientes','Clientes registrados para el selector.'),
 ('GET /api/productos/ID/esperas','Cola FIFO del producto; [] si está vacía; 404 si no existe el producto.'),
 ('POST /api/esperas','Recibe id_cliente e id_producto. Devuelve 201 y la espera creada.'),
 ('PUT /api/productos/ID','Modifica el inventario y devuelve notificacion cuando atiende una espera por reposición.'),
],[220,291])
add('Ejemplo de cuerpo para POST /api/esperas: <font name="Courier">{"id_cliente": 1, "id_producto": 3}</font>. La fecha y el ID de espera se generan en el backend. Las solicitudes inválidas o que incumplen las reglas reciben 400; un formato distinto de JSON, 415; los errores SQLite controlados, 500.','SmallReport')
sub('10. Uso desde la pantalla')
add('Desde el catálogo se puede elegir "Anotar cliente" si no hay stock o "Ver espera" si hay disponibilidad. La sección "Clientes en espera" permite seleccionar el producto y el cliente, consultar el orden y actualizar los datos. El primer cliente aparece destacado; quienes ya esperan el producto están deshabilitados en el selector.')
add('Al reponer desde la edición del producto, se muestra el aviso "Cliente notificado" y se actualiza la cola. Los estados de carga, ausencia de clientes, cola vacía y errores tienen mensajes específicos. Las respuestas tardías de otro producto se descartan y los nombres se insertan como texto. La interfaz usa HTML, CSS y JavaScript nativos.')
sub('11. Pruebas realizadas durante la implementación')
table(['Comprobación','Resultado observado'],[
 ('Registro y validaciones','Guardado correcto; rechazo de duplicados, IDs inválidos, registros inexistentes y productos con stock.'),
 ('FIFO e independencia','Orden conservado al consultar; colas separadas por producto; un cliente atendido por reposición.'),
 ('Concurrencia y fallos','Dos registros simultáneos del mismo par producen una sola espera. Un fallo al eliminar revierte la reposición.'),
 ('Persistencia y HTTP','Recarga de colas correcta y respuestas verificadas mediante solicitudes HTTP reales.'),
 ('Interfaz en navegador','Registro, aviso, actualización, errores y reintentos comprobados en escritorio y móvil, sin errores JavaScript.'),
],[153,358])
add('Las comprobaciones usaron bases temporales; no alteraron los registros reales. La prueba de interfaz está en tmp/pruebas-esperas/servidor_prueba.py y su automatización en interfaz.cjs. Este informe documenta las verificaciones previas, no una nueva ejecución de esas pruebas.','SmallReport')
add('<b>Estado:</b> punto 2 implementado e integrado. La pila de transacciones y el árbol de popularidad corresponden a los puntos siguientes; actualmente la espera no genera compras automáticas.','SmallReport')

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=76,bottomMargin=48,title='Informe del punto 2 - Registro de clientes en espera',author='Tienda TP',subject='TDA Cola, persistencia SQLite, API e interfaz')
doc.build(story,onFirstPage=frame,onLaterPages=frame)
r=PdfReader(str(OUT))
print('Páginas:',len(r.pages))
assert len(r.pages)==4, 'Revisar paginación'
for n,page in enumerate(r.pages,1):
 text=page.extract_text()
 assert len(text)>500
 print(n,len(text),'caracteres')
pdf=pdfium.PdfDocument(str(OUT))
for n in range(len(pdf)):
 pdf[n].render(scale=1.35).to_pil().save(f'tmp/pdfs/informe-esperas/pagina_{n+1}.png')
print(OUT.resolve())
