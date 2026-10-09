from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from pathlib import Path
import pypdfium2 as pdfium
OUT=Path('output/pdf/DER_MER_Tienda.pdf')
c=canvas.Canvas(str(OUT),pagesize=landscape(A4))
W,H=landscape(A4)
navy=HexColor('#15334C'); blue=HexColor('#246B8E'); light=HexColor('#EDF4F8'); gray=HexColor('#475569')
def txt(x,y,s,size=10,bold=False,color=gray):
 c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,s)
def base(num,title,sub):
 c.setFillColor(navy);c.rect(0,H-88,W,88,fill=1,stroke=0)
 txt(36,H-35,title,22,True,white);txt(36,H-60,sub,10,False,white)
 txt(36,20,'TIENDA TP | Esquema actual de BD/tablas.db | 07/10/2026',9)
 txt(W-70,20,f'{num} / 2',9)
def box(x,y,w,h,title,rows):
 c.setStrokeColor(blue);c.setFillColor(light);c.roundRect(x,y,w,h,7,fill=1,stroke=1)
 c.setFillColor(blue);c.rect(x,y+h-28,w,28,fill=1,stroke=0)
 txt(x+10,y+h-19,title,11,True,white)
 for i,row in enumerate(rows):txt(x+10,y+h-45-i*17,row,9)
def line(points):
 c.setStrokeColor(blue);c.setLineWidth(1.3)
 p=c.beginPath();p.moveTo(*points[0])
 for xy in points[1:]:p.lineTo(*xy)
 c.drawPath(p)
def diamond(x,y,label,w=52,h=22):
 c.setFillColor(white);c.setStrokeColor(blue)
 p=c.beginPath();p.moveTo(x-w,y);p.lineTo(x,y+h);p.lineTo(x+w,y);p.lineTo(x,y-h);p.close();c.drawPath(p,fill=1,stroke=1)
 c.setFont('Helvetica-Bold',9);c.setFillColor(navy);c.drawCentredString(x,y-3,label)
base(1,'MER | Modelo entidad-relación','Vista conceptual: entidades, atributos y relaciones del sistema de tienda.')
box(40,365,170,95,'CLIENTE',['Identificador de cliente','Nombre, apellido, email'])
box(335,365,170,95,'COMPRA',['Identificador de compra','Fecha, total pagado'])
box(630,365,170,95,'PRODUCTO',['Identificador de producto','Nombre, stock, precio'])
line([(210,415),(335,415)]);diamond(272,415,'Realiza',43)
txt(213,443,'1',10,True);txt(304,443,'0..N',10,True)
line([(505,415),(630,415)]);diamond(567,415,'Incluye',43)
txt(507,443,'0..N',10,True);txt(602,443,'0..N',10,True)
line([(125,365),(125,245),(368,245)])
line([(472,245),(715,245),(715,365)])
diamond(420,245,'Espera')
txt(135,320,'0..N',10,True);txt(677,320,'0..N',10,True)
txt(305,205,'Atributos de espera: identificador y fecha.',10)
txt(36,155,'Relaciones y su implementación',12,True,navy)
for i,s in enumerate([
 'Realiza: cada compra corresponde a un cliente; un cliente puede realizar muchas compras.',
 'Incluye: relación N:M resuelta mediante detalle_transaccion; registra cantidad y precio unitario.',
 'Espera: relación N:M resuelta mediante esperas; registra cada entrada de un cliente por un producto.',
 '0..N indica participación opcional y múltiple. El esquema actual permite compras sin detalles.',
 'El orden FIFO de espera, el historial LIFO y la popularidad se gestionan en la lógica del programa.'
]):txt(36,133-i*18,s,10)
c.showPage()
base(2,'DER | Diagrama de tablas y relaciones','Vista lógica: campos, tipos SQLite, claves y cardinalidades reales del esquema.')
box(35,325,220,155,'clientes',['PK id_cliente : INTEGER','nombre : TEXT','apellido : TEXT','UQ email : TEXT'])
box(310,325,220,155,'transacciones',['PK id_transaccion : INTEGER','FK id_cliente : INTEGER','fecha : TEXT','total : REAL'])
box(585,325,220,155,'detalle_transaccion',['PK id_detalle : INTEGER','FK id_transaccion : INTEGER','FK id_producto : INTEGER','cantidad : INTEGER','precio_unitario : REAL'])
box(35,105,220,130,'esperas',['PK id_espera : INTEGER','FK id_cliente : INTEGER','FK id_producto : INTEGER','fecha_espera : TEXT'])
box(585,105,220,130,'productos',['PK id_producto : INTEGER','nombre : TEXT','cantidad_disponible : INTEGER','precio : REAL'])
line([(255,405),(310,405)]);txt(261,416,'1',9,True);txt(279,389,'0..N',9,True)
line([(530,405),(585,405)]);txt(534,416,'1',9,True);txt(552,389,'0..N',9,True)
line([(145,325),(145,235)]);txt(154,307,'1',9,True);txt(154,250,'0..N',9,True)
line([(695,235),(695,325)]);txt(704,250,'1',9,True);txt(704,307,'0..N',9,True)
line([(255,172),(585,172)]);txt(270,183,'0..N',9,True);txt(561,183,'1',9,True)
txt(292,147,'esperas.id_producto -> productos.id_producto',8)
txt(290,281,'Cada registro hijo referencia exactamente',9)
txt(290,266,'un registro padre (FK NOT NULL).',9)
txt(35,82,'PK: clave primaria | FK: clave foránea | UQ: único. Todos los campos son obligatorios (NOT NULL o PK).',9)
txt(35,65,'CHECK: stock, precio, total y precio_unitario >= 0; cantidad del detalle > 0. Stock por defecto: 0.',9)
txt(35,48,'PK INTEGER con AUTOINCREMENT. No hay borrado en cascada ni restricción contra esperas o detalles repetidos.',9)
c.save()
pdf=pdfium.PdfDocument(str(OUT))
for i in range(len(pdf)):
 pdf[i].render(scale=1.4).to_pil().save(f'tmp/pdfs/DER_MER_pagina_{i+1}.png')
print(OUT.resolve())
