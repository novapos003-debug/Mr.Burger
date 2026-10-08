@echo off
title Optimizador de Rendimiento para PC Caja - Mr. Burger
echo ============================================================
echo   OPTIMIZANDO RENDIMIENTO DE WINDOWS PARA LA CAJA MR. BURGER
echo ============================================================
echo.
echo Ejecutando ajustes de rendimiento maximo...
echo.

:: 1. Activar Plan de Energia de Alto Rendimiento (Evita que el procesador se aletargue)
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>nul
echo [OK] Plan de energia puesto en Alto Rendimiento.

:: 2. Desactivar inicio de OneDrive y bloatware común del usuario
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OneDrive" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Spotify" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Discord" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Teams" /f 2>nul
echo [OK] Aplicaciones pesadas removidas del inicio del usuario.

:: 3. Desactivar animaciones innecesarias que ralentizan PCs viejas
reg add "HKCU\Control Panel\Desktop" /v "UserPreferencesMask" /t REG_BINARY /d 9012038010000000 /f 2>nul
echo [OK] Animaciones graficas optimizadas para velocidad.

:: 4. Evitar que Edge y Chrome se queden consumiendo memoria en segundo plano al cerrar
reg add "HKLM\SOFTWARE\Policies\Microsoft\Edge" /v "BackgroundModeEnabled" /t REG_DWORD /d 0 /f 2>nul
reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v "BackgroundModeEnabled" /t REG_DWORD /d 0 /f 2>nul
echo [OK] Navegadores en segundo plano deshabilitados.

echo.
echo ============================================================
echo   ¡OPTIMIZACION COMPLETADA!
echo   La PC respondera mucho mas rapido.
echo ============================================================
echo.
pause
