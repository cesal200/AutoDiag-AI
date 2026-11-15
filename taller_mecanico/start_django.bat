@echo off
title AutoDiag AI - Inicio del Servidor Django
cd /d "%~dp0"

echo.
echo ==========================================
echo   AutoDiag AI - Sistema de Taller Mecanico
echo ==========================================
echo.

echo Verificando entorno virtual...
if exist "%~dp0..\.venv\Scripts\activate.bat" (
    echo Entorno virtual de la raiz encontrado.
    call "%~dp0..\.venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    echo Entorno virtual local encontrado.
    call "%~dp0.venv\Scripts\activate.bat"
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
echo   - Admin: http://127.0.0.1:8000/admin/
echo   - Usuario demo (si se cargo seed_demo): admin / demo12345
echo ==========================================
echo.

python manage.py runserver 0.0.0.0:8000

pause