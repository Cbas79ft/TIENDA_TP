const { chromium } = require('C:/Users/aesan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const base = process.env.TIENDA_TEST_URL;
(async () => {
    const browser = await chromium.launch({channel:'msedge', headless:true});
    try {
        const page = await browser.newPage({viewport:{width:1366,height:1000}});
        const errores = [];
        page.on('pageerror', error => errores.push(error.message));
        await page.goto(base);
        await page.waitForFunction(() => document.querySelector('#total-productos').textContent === '3' && !document.querySelector('#actualizar-esperas').disabled);
        assert.equal(await page.locator('#registrar-espera').isDisabled(), true);
        await page.getByRole('button', {name:'Consultar espera de Teclado sin stock',exact:true}).click();
        await page.getByText('Este producto no tiene clientes en espera.',{exact:true}).waitFor();
        await page.selectOption('#cliente-espera','1');
        await page.locator('#registrar-espera').click();
        await page.waitForFunction(() => document.querySelectorAll('#lista-esperas li').length === 1 && !document.querySelector('#actualizar-esperas').disabled);
        assert.match(await page.locator('#lista-esperas').innerText(),/Ana Perez/);
        assert.equal(await page.locator('#cliente-espera option[value="1"]').isDisabled(),true);
        await page.selectOption('#cliente-espera','2');
        await page.locator('#registrar-espera').click();
        await page.waitForFunction(() => document.querySelectorAll('#lista-esperas li').length === 2 && !document.querySelector('#actualizar-esperas').disabled);
        assert.match(await page.locator('#lista-esperas li').nth(0).innerText(),/Ana Perez/);
        assert.match(await page.locator('#lista-esperas li').nth(1).innerText(),/Luis Lopez/);
        await page.screenshot({path:'tmp/pruebas-esperas/esperas-escritorio.png',fullPage:true});
        // El cambio de selección no puede mostrar respuestas tardías de otro producto.
        await page.route('**/api/productos/3/esperas',async route => {
            await new Promise(resolve => setTimeout(resolve,300));
            await route.fulfill({json:[]});
        });
        await page.selectOption('#producto-espera','3');
        await page.selectOption('#producto-espera','1');
        await page.waitForFunction(() => document.querySelector('#cola-espera').getAttribute('aria-busy') === 'false');
        await page.waitForTimeout(400);
        assert.equal(await page.locator('#lista-esperas li').count(),2);
        await page.unroute('**/api/productos/3/esperas');
        // La reposición desde el formulario real muestra el aviso y retira solo al primero.
        await page.getByRole('button',{name:'Editar Teclado sin stock',exact:true}).click();
        await page.fill('#cantidad-producto','4');
        await page.locator('#guardar-producto').click();
        await page.locator('#notificacion-reposicion').waitFor({state:'visible'});
        await page.waitForFunction(() => document.querySelectorAll('#lista-esperas li').length === 1 && !document.querySelector('#actualizar-esperas').disabled);
        assert.match(await page.locator('#aviso-reposicion').innerText(),/Ana Perez/);
        assert.match(await page.locator('#lista-esperas').innerText(),/Luis Lopez/);
        assert.equal(await page.locator('#registrar-espera').isDisabled(),true);
        assert.match(await page.locator('#regla-espera').innerText(),/tiene stock/);
        await page.screenshot({path:'tmp/pruebas-esperas/reposicion-escritorio.png',fullPage:true});
        // Al recargar se reconstruye la cola confirmada por SQLite.
        await page.reload();
        await page.waitForFunction(() => !document.querySelector('#actualizar-esperas').disabled);
        await page.selectOption('#producto-espera','1');
        await page.waitForFunction(() => document.querySelectorAll('#lista-esperas li').length === 1);
        assert.match(await page.locator('#lista-esperas').innerText(),/Luis Lopez/);
        // Nombre con etiquetas: se presenta como texto, nunca como HTML.
        await page.selectOption('#producto-espera','3');
        await page.getByText('Este producto no tiene clientes en espera.',{exact:true}).waitFor();
        assert.equal(await page.locator('#titulo-cola b').count(),0);
        assert.match(await page.locator('#titulo-cola').innerText(),/<b>especial<\/b>/);
        // Error al registrar: no se pierde el mensaje ni se agrega una espera ficticia.
        await page.route('**/api/esperas',route => route.fulfill({status:400,json:{error:'El cliente ya está esperando este producto.'}}));
        await page.selectOption('#cliente-espera','1');
        await page.locator('#registrar-espera').click();
        await page.waitForFunction(() => document.querySelector('#mensaje-espera').classList.contains('error') && !document.querySelector('#actualizar-esperas').disabled);
        assert.match(await page.locator('#mensaje-espera').innerText(),/ya está esperando/);
        assert.equal(await page.locator('#lista-esperas li').count(),0);
        await page.unroute('**/api/esperas');
        // Error de consulta y recuperación manual.
        await page.route('**/api/productos/3/esperas',route => route.fulfill({status:500,json:{error:'Error de prueba al consultar.'}}));
        await page.locator('#actualizar-esperas').click();
        await page.waitForFunction(() => document.querySelector('#estado-cola').classList.contains('error') && !document.querySelector('#actualizar-esperas').disabled);
        assert.equal(await page.locator('#registrar-espera').isDisabled(),true);
        await page.unroute('**/api/productos/3/esperas');
        await page.locator('#actualizar-esperas').click();
        await page.waitForFunction(() => !document.querySelector('#actualizar-esperas').disabled && !document.querySelector('#estado-cola').classList.contains('error'));
        // Clientes no disponibles y reintento.
        await page.route('**/api/clientes',route => route.fulfill({status:500,json:{error:'Clientes no disponibles.'}}));
        await page.locator('#actualizar-esperas').click();
        await page.waitForFunction(() => document.querySelector('#estado-clientes').classList.contains('error') && !document.querySelector('#actualizar-esperas').disabled);
        assert.equal(await page.locator('#cliente-espera').isDisabled(),true);
        await page.unroute('**/api/clientes');
        await page.locator('#actualizar-esperas').click();
        await page.waitForFunction(() => !document.querySelector('#actualizar-esperas').disabled && !document.querySelector('#estado-clientes').classList.contains('error'));
        // Diseño móvil y consulta aun cuando el producto ya tiene stock.
        await page.setViewportSize({width:390,height:844});
        await page.selectOption('#producto-espera','1');
        await page.waitForFunction(() => document.querySelectorAll('#lista-esperas li').length === 1);
        await page.locator('#seccion-esperas').scrollIntoViewIfNeeded();
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),true);
        await page.screenshot({path:'tmp/pruebas-esperas/esperas-movil.png',fullPage:true});
        assert.deepEqual(errores,[]);
        console.log('OK: alta desde la pantalla, FIFO, duplicados, reposición, recarga, respuestas tardías, errores y reintentos, nombres seguros y pantalla móvil; sin errores JavaScript.');
    } finally {
        await browser.close();
    }
})().catch(error => {console.error(error);process.exitCode=1;});
