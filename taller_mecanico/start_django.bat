@echo off
title AutoDiag AI - Inicio del Servidor Django
cd /d "%~dp0"

echo.
echo ==========================================
echo   AutoDiag AI - Sistema de Taller Mecanico
echo ==========================================
echo.

echo Verificando entorno virtual...
if exist .venv (
    echo Entorno virtual encontrado.
    call .venv\Scripts\activate
) else (
    echo No se encuentra entorno virtual.
    echo Instalando dependencias...
    pip install -r requirements.txt 2>nul
)

echo.
echo Aplicando migraciones pendientes...
python manage.py migrate --noinput 2>nul

echo.
echo Levantando servidor de desarrollo...
echo.
echo ==========================================
echo   Acceso al sistema:
echo   - Web: http://127.0.0.1:8000
echo   - Inicio de sesion: http://127.0.0.1:8000/login/
echo   - Admin: http://127.0.0.1:8000/admin/
echo   - Si aun no tienes usuario, ejecuta setup.bat
echo ==========================================
echo.

python manage.py runserver 0.0.0.0:8000

pause