@echo off
title Configurar Firewall de Windows - Mr. Burger
echo ============================================================
echo   ABRIENDO PUERTOS EN EL FIREWALL DE WINDOWS PARA CELULARES
echo ============================================================
echo.
echo Este script debe ejecutarse como Administrador (clic derecho > Ejecutar como administrador).
echo.

netsh advfirewall firewall add rule name="MrBurger Frontend (5173)" dir=in action=allow protocol=TCP localport=5173
netsh advfirewall firewall add rule name="MrBurger Backend (8000)" dir=in action=allow protocol=TCP localport=8000

echo.
echo ============================================================
echo   ¡PUERTOS 5173 Y 8000 HABILITADOS EN EL FIREWALL!
echo   Los celulares de meseros y la tablet ya pueden conectarse.
echo ============================================================
echo.
pause
