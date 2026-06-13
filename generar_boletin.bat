@echo off
title Generador de Boletin Highlights Diario
color 0B

echo ============================================================
echo   ✨ BIENVENIDO AL GENERADOR DE BOLETiN HIGHLIGHTS DIARIO ✨
echo ============================================================
echo.

:: 1. Detección robusta del Escritorio usando PowerShell (compatible con OneDrive y escritorio tradicional)
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "ESCRITORIO=%%D"

:: Fallback si PowerShell falla por alguna razón
if not defined ESCRITORIO (
    if exist "%USERPROFILE%\OneDrive\Desktop" (
        set "ESCRITORIO=%USERPROFILE%\OneDrive\Desktop"
    ) else (
        set "ESCRITORIO=%USERPROFILE%\Desktop"
    )
)

set "ESCRITORIO_BAT=%ESCRITORIO%\generar_boletin.bat"

if not exist "%ESCRITORIO_BAT%" (
    echo [INFO] Creando acceso directo del ejecutable en el Escritorio...
    copy "%~f0" "%ESCRITORIO_BAT%" >nul
    if errorlevel 1 (
        echo [ADVERTENCIA] No se pudo copiar el archivo al Escritorio de forma automatica.
        echo             Ruta intentada: "%ESCRITORIO%"
    ) else (
        echo [OK] Ahora puedes iniciar el boletin directamente desde tu Escritorio.
    )
    echo.
)

:: 2. Navegar a la carpeta del proyecto
echo [PASO 1] Entrando a la carpeta del proyecto...
cd /d "C:\Users\Lucidio\Proyectos\highlights"
if errorlevel 1 (
    echo [ERROR] No se pudo encontrar el directorio del proyecto en C:\Users\Lucidio\Proyectos\highlights.
    goto final
)

:: 3. Forzar Python 3.12 (Versión estable confirmada en el sistema)
set "PYTHON_CMD=py -3.12"

:: 4. Verificar e instalar requerimientos
echo [PASO 2] Verificando dependencias en Python 3.12...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ADVERTENCIA] Hubo un problema al verificar dependencias. Intentando ejecucion directamente...
)

:: 5. Ejecutar el orquestador principal
echo [PASO 3] Ejecutando generador de boletin con Python 3.12...
echo.
%PYTHON_CMD% main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un error al ejecutar el script de Python.
)

:final
echo.
echo ============================================================
echo   Proceso finalizado. Presiona cualquier tecla para salir...
echo ============================================================
pause >nul
