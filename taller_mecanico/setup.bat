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
echo Creando superusuario administrador...
python manage.py createsuperuser --username admin --email admin@taller.mecanico 2>nul

if %errorLevel% equ 0 (
    echo.
    echo Superusuario creado exitosamente.
    echo Usuario: admin
    echo Contraseña: Se asignó una contraseña segura
    echo Para cambiarla, use: python manage.py changepassword admin
) else (
    echo.
    echo El superusuario ya existe o hubo un error.
    echo Para crear uno nuevo: python manage.py createsuperuser --username admin --email admin@taller.mecanico
)

echo.
echo Leyendo bases de datos...
python manage.py migrate

echo.
echo Cargando datos iniciales...
python manage.py loaddata taller_mecanico/fixtures/initial_data.json 2>nul

echo.
echo ==========================================
echo   Configuración completada
echo ==========================================
echo.
echo Para iniciar el servidor ejecute:
echo   start_django.bat
echo.
pause