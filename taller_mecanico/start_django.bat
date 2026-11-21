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
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

echo.
echo Aplicando migraciones pendientes...
python manage.py migrate --noinput
if errorlevel 1 (
    echo No se pudieron aplicar las migraciones. Revisa el error anterior.
    pause
    exit /b 1
)

echo.
echo Levantando servidor de desarrollo...
echo.
set "LAN_IP="
for /f "delims=" %%I in ('powershell -NoProfile -Command "$ip = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | Where-Object { $_.OperationalStatus -eq 'Up' -and $_.NetworkInterfaceType -in @('Ethernet','Wireless80211') } | ForEach-Object { $_.GetIPProperties().UnicastAddresses | Where-Object { $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $_.Address.ToString() -notmatch '^(127\.|169\.254\.)' } | Select-Object -First 1 -ExpandProperty Address } | Select-Object -First 1; if (-not $ip) { $ip = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | Where-Object { $_.OperationalStatus -eq 'Up' -and $_.NetworkInterfaceType -notin @('Loopback','Tunnel') } | ForEach-Object { $_.GetIPProperties().UnicastAddresses | Where-Object { $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $_.Address.ToString() -notmatch '^(127\.|169\.254\.)' } | Select-Object -First 1 -ExpandProperty Address } | Select-Object -First 1 }; if ($ip) { $ip.ToString() }" 2^>nul') do set "LAN_IP=%%I"

if defined LAN_IP (
    if defined DJANGO_ALLOWED_HOSTS (
        set "DJANGO_ALLOWED_HOSTS=%DJANGO_ALLOWED_HOSTS%,%LAN_IP%,127.0.0.1,localhost"
    ) else (
        set "DJANGO_ALLOWED_HOSTS=%LAN_IP%,127.0.0.1,localhost"
    )
    echo   - Red local: http://%LAN_IP%:8000
    echo   - Inicio de sesion en red: http://%LAN_IP%:8000/login/
) else (
    echo No se detecto una direccion IPv4 de red. Usa la direccion local del equipo.
)
echo.
echo ==========================================
echo   Acceso al sistema:
echo   - Web: http://127.0.0.1:8000
echo   - Inicio de sesion: http://127.0.0.1:8000/login/
echo   - Usuario demo (si se cargo seed_demo): admin / demo12345
echo ==========================================
echo.
echo El equipo cliente debe estar en la misma red. Si no conecta, revisa el firewall de Windows.
echo.

python manage.py runserver 0.0.0.0:8000

pause