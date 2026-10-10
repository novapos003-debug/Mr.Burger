@echo off
chcp 65001 >nul
:: ============================================================
:: Deja este computador listo para operar. Lo llama actualizar_windows.bat
:: DESPUES de descargar la ultima version. Se puede ejecutar las veces
:: que haga falta: solo hace lo que falte.
:: ============================================================
cd /d "%~dp0.."

set PY_CMD=python
where python >nul 2>nul
if errorlevel 1 set PY_CMD=py
where %PY_CMD% >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python. Instala Python 3.11 y marca "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo [A] Verificando componentes de Python...
%PY_CMD% -c "import fastapi, sqlalchemy, psycopg2, httpx, jose, passlib, uvicorn, websockets, multipart" >nul 2>nul
if errorlevel 1 (
    echo     Instalando componentes que faltan (requiere internet^)...
    %PY_CMD% -m pip install --disable-pip-version-check -q -r backend\requirements.txt
    if errorlevel 1 echo     [AVISO] No se pudieron instalar. Revisa la conexion a internet.
) else (
    echo     [OK] Componentes completos.
)

echo.
echo [B] Verificando la base de datos local...
for %%S in (postgresql-x64-18 postgresql-x64-17 postgresql-x64-16 postgresql-x64-15 postgresql-18 postgresql-17 postgresql-16 postgresql-15) do net start %%S >nul 2>nul
%PY_CMD% -c "import psycopg2,sys; c=psycopg2.connect(host='127.0.0.1',port=5432,dbname='restaurante',user='restaurante',password='restaurante_dev',connect_timeout=5); cur=c.cursor(); cur.execute('select count(*) from producto'); print('    [OK] Base de datos lista:', cur.fetchone()[0], 'productos')" 2>nul
if errorlevel 1 (
    echo     [FALTA] No hay base de datos "restaurante" o PostgreSQL esta apagado.
    echo             Si es la primera vez en este computador, se va a crear ahora.
    echo.
    call configurar_bd_windows.bat
)

echo.
echo [C] Verificando la sincronizacion con la nube...
set "TIENE_TOKEN="
if exist ".env" for /f "usebackq tokens=1,* delims==" %%A in (".env") do if /i "%%A"=="CLOUD_SYNC_TOKEN" if not "%%B"=="" set "TIENE_TOKEN=1"
if defined TIENE_TOKEN (
    echo     [OK] Token de sincronizacion configurado.
) else (
    echo     [FALTA] Este computador aun no tiene el token de la nube.
    call configurar_sincronizacion_windows.bat
)

echo.
echo [D] Verificando el respaldo diario automatico...
schtasks /Query /TN "MrBurger - Respaldo diario" >nul 2>nul
if errorlevel 1 (
    call programar_respaldo_diario.bat /silencioso
) else (
    echo     [OK] Respaldo diario programado.
)

echo.
echo [E] Verificando el firewall para celulares y tablet...
netsh advfirewall firewall show rule name="MrBurger Backend (8000)" >nul 2>nul
if errorlevel 1 (
    echo     [FALTA] Los puertos no estan abiertos. Haz clic derecho sobre
    echo             configurar_firewall_windows.bat y elige "Ejecutar como administrador".
) else (
    echo     [OK] Puertos 5173 y 8000 abiertos.
)

echo.
echo [F] Impresora de tirillas...
powershell -NoProfile -Command "$p = Get-CimInstance Win32_Printer | Where-Object Default; if ($p) { Write-Host ('    Predeterminada de Windows: ' + $p.Name); if ($p.Name -match 'PDF|XPS|OneNote|Fax') { Write-Host '    [AVISO] La predeterminada NO es la termica. Cambiala en Configuracion > Impresoras.' -ForegroundColor Yellow } } else { Write-Host '    [AVISO] No hay impresora predeterminada. Instala la termica y marcala como predeterminada.' -ForegroundColor Yellow }"

echo.
exit /b 0
