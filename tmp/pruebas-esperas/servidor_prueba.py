import os
import sqlite3
import subprocess
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock, Thread
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from BD import persistencia as p
from BACKEND.inventario import cargar_inventario
from BACKEND.esperas import cargar_colas
from BACKEND.servidor import ManejadorTienda

class ManejadorPrueba(ManejadorTienda):
    def log_message(self, formato, *argumentos):
        pass

origen=sqlite3.connect(p.RUTA_BD.resolve().as_uri()+'?mode=ro',uri=True)
esquema=origen.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('clientes','productos','esperas')").fetchall()
origen.close()
with TemporaryDirectory(prefix='tienda_interfaz_') as carpeta:
    ruta=Path(carpeta)/'prueba.db'
    c=sqlite3.connect(ruta)
    for (sql,) in esquema: c.execute(sql)
    c.executemany('INSERT INTO clientes(nombre,apellido,email) VALUES(?,?,?)', [('Ana','Perez','a@test'),('Luis','Lopez','l@test')])
    c.executemany('INSERT INTO productos(nombre,cantidad_disponible,precio) VALUES(?,?,?)', [('Teclado sin stock',0,100),('Mouse disponible',5,200),('Producto <b>especial</b>',0,300)])
    c.commit();c.close()
    with patch.object(p,'RUTA_BD',ruta):
        manejador=partial(ManejadorPrueba,inventario=cargar_inventario(),colas=cargar_colas(),bloqueo=Lock(),directory=str(Path('FRONTEND').resolve()))
        servidor=ThreadingHTTPServer(('127.0.0.1',0),manejador)
        hilo=Thread(target=servidor.serve_forever,daemon=True);hilo.start()
        entorno=os.environ.copy()
        entorno['TIENDA_TEST_URL']=f'http://127.0.0.1:{servidor.server_port}'
        try:
            resultado=subprocess.run([r'C:/Users/aesan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe','tmp/pruebas-esperas/interfaz.cjs'],env=entorno)
            if resultado.returncode: raise SystemExit(resultado.returncode)
            c=p.conectar()
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert c.execute('SELECT cantidad_disponible FROM productos WHERE id_producto=1').fetchone()[0]==4
            assert c.execute('SELECT id_cliente FROM esperas WHERE id_producto=1').fetchone()[0]==2
            c.close()
            print('OK: base temporal consistente después de las pruebas de interfaz.',flush=True)
        finally:
            servidor.shutdown();servidor.server_close();hilo.join(timeout=5)
