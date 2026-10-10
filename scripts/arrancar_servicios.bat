@echo off
:: ============================================================
:: Arranca los servicios de Mr. Burger en este computador.
:: Lo llama iniciar_windows.bat DESPUES de descargar la ultima version,
:: asi que este archivo siempre se ejecuta ya actualizado.
:: ============================================================
cd /d "%~dp0.."
set "RAIZ=%CD%"

:: Asegurar que el servicio de PostgreSQL este iniciado (si ya lo esta, no hace nada)
for %%S in (postgresql-x64-18 postgresql-x64-17 postgresql-x64-16 postgresql-x64-15 postgresql-18 postgresql-17 postgresql-16 postgresql-15) do net start %%S >nul 2>nul

:: Detectar comando de Python disponible
set PY_CMD=python
where python >nul 2>nul
if errorlevel 1 set PY_CMD=py

:: Cerrar procesos previos y liberar estrictamente los puertos 8000 y 5173
taskkill /F /FI "WINDOWTITLE eq MrBurger-Backend*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MrBurger-Frontend*" >nul 2>nul
%PY_CMD% liberar_puertos.py >nul 2>nul

:: 1. Backend. La base es siempre la local de este computador; la clave de sesiones la
::    genera el propio backend (backend\.secret_key) y el token de la nube sale de .env
echo [1/3] Iniciando Cerebro Backend (Puerto 8000)...
start "MrBurger-Backend" /min cmd /c "cd /d "%RAIZ%\backend" && set PYTHONUTF8=1&& set PYTHONIOENCODING=utf-8&& set DATABASE_URL=postgresql://restaurante:restaurante_dev@127.0.0.1:5432/restaurante&& %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "%RAIZ%\backend.log" 2>&1"

:: 2. Frontend
echo [2/3] Iniciando Servidor Web PWA (Puerto 5173)...
start "MrBurger-Frontend" /min cmd /c "cd /d "%RAIZ%" && %PY_CMD% serve_frontend.py"

:: 3. Esperar a que el backend responda (maximo ~40 s) antes de abrir la caja
echo [3/3] Esperando a que el sistema este listo...
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 40;$i++){ try { Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if(-not $ok){ Write-Host '  [AVISO] El backend aun no responde. Revisa backend.log o ejecuta estado_sistema.bat' -ForegroundColor Yellow }"

:: Abrir la Caja. Con Chrome se usa un perfil propio del POS e impresion directa:
:: al cobrar, la tirilla sale por la impresora PREDETERMINADA de Windows sin mostrar el dialogo.
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if defined CHROME (
    start "" "%CHROME%" --user-data-dir="%LOCALAPPDATA%\MrBurgerPOS\Chrome" --kiosk-printing --no-first-run --no-default-browser-check --start-maximized http://localhost:5173
) else (
    start http://localhost:5173
)

echo.
echo ============================================================
echo   SISTEMA MR. BURGER EN MARCHA
echo ============================================================
echo   - Pantalla de Caja:  http://localhost:5173
echo   - Celulares y tablet (misma red Wi-Fi):
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.InterfaceAlias -notmatch 'Loopback|vEthernet' } | ForEach-Object { Write-Host ('       http://' + $_.IPAddress + ':5173') }"
echo ============================================================
echo.
timeout /t 6 >nul
