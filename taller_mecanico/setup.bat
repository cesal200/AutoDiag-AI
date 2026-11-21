@echo off
title AutoDiag AI - Configuración Inicial
cd /d "%~dp0"

echo.
echo ==========================================
echo   AutoDiag AI - Configuración Inicial
echo ==========================================
echo.

echo Verificando Python y Django...
python --version
python -c "import django; print(f'Django {django.VERSION}')"

echo.
echo Aplicando migraciones...
python manage.py migrate --noinput
if errorlevel 1 (
    echo No se pudieron aplicar las migraciones.
    pause
    exit /b 1
)

echo.
echo Crea el usuario administrador para iniciar sesion.
python manage.py createsuperuser
if errorlevel 1 (
    echo No se pudo crear el usuario. Revisa el error anterior y vuelve a ejecutar setup.bat.
    pause
    exit /b 1
)

echo.
echo Cargando datos iniciales...
python manage.py loaddata taller_mecanico/fixtures/initial_data.json 2>nul

echo.
echo ==========================================
echo   Configuración completada
echo ==========================================
echo.
echo Inicia sesion en http://127.0.0.1:8000/login/
echo Para iniciar el servidor ejecuta:
echo   start_django.bat
echo.
pause