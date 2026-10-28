@echo off
setlocal
title Tienda TP - Servidor local

rem Usa la carpeta del BAT aunque se inicie desde un acceso directo.
pushd "%~dp0"
if errorlevel 1 (
    echo No se pudo abrir la carpeta del proyecto.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo No se encontro main.py. Deja este BAT en la carpeta TIENDA_TP.
    goto error
)

rem Busca Python 3; admite tambien el lanzador py de Windows.
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "TIENDA_PYTHON=python"
    goto iniciar
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "TIENDA_PYTHON=py -3"
    goto iniciar
)

echo No se encontro Python 3.8 o posterior.
echo Instala Python y habilita la opcion de agregarlo al PATH.
goto error

:iniciar
echo Iniciando Tienda TP...
echo.
echo Comprar:    http://127.0.0.1:8000/compra.html
echo Inventario: http://127.0.0.1:8000/
echo.
echo Espera el mensaje "Tienda disponible" antes de abrir el sitio.
echo Manten esta ventana abierta mientras uses la tienda.
echo Para detener el servidor, presiona Ctrl+C.
echo.
%TIENDA_PYTHON% -B main.py
set "TIENDA_RESULTADO=%ERRORLEVEL%"
if not "%TIENDA_RESULTADO%"=="0" (
    echo.
    echo El servidor no pudo iniciar o se detuvo por un error.
    echo Revisa el mensaje anterior. Si el puerto 8000 esta ocupado,
    echo detene la otra instancia antes de volver a iniciar.
    pause
)
popd
exit /b %TIENDA_RESULTADO%

:error
popd
pause
exit /b 1
