# 🛠️ Guía de Instalación Físico en Local (Modo Servidor Caja)

> 📱 **¿La caja es una Pantalla Android All-in-One sin PC?**
> Sigue la guía especializada: [GUIA_SERVIDOR_ANDROID_TERMUX.md](file:///C:/Users/jhona/Documents/default%20project/GUIA_SERVIDOR_ANDROID_TERMUX.md) para instalar el servidor autónomo dentro de Android usando Termux sin necesidad de computadores externos ni nube.

Este documento contiene los pasos si se utiliza un computador físico con Windows en la caja:

## 1. Configuración de Energía (Evitar que el servidor "muera")
El computador de la caja actuará como el servidor maestro. Si se suspende, todo el restaurante se detiene.
- Ir a **Configuración > Sistema > Inicio/Apagado y suspensión**.
- Pantalla: Puede apagarse si lo desean.
- **Suspender equipo: NUNCA**.
- *Pro Tip:* En "Configuración avanzada de energía", buscar "Disco duro" y poner "Apagar disco duro tras: 0 minutos (Nunca)".

## 2. Fijar la Dirección IP (IP Estática)
Para que los meseros no pierdan la conexión si el router se reinicia.
1. Abrir **CMD** en Windows y escribir `ipconfig`.
2. Anotar la Puerta de enlace predeterminada (Ej. `192.168.1.1`), la Máscara de subred (Ej. `255.255.255.0`) y la IP actual (Ej. `192.168.1.14`).
3. Ir a **Panel de Control > Redes e Internet > Centro de redes y recursos compartidos > Cambiar configuración del adaptador**.
4. Clic derecho en el Wi-Fi o Ethernet > Propiedades > Protocolo de Internet versión 4 (TCP/IPv4) > Propiedades.
5. Seleccionar "Usar la siguiente dirección IP" y fijar una IP alta para que no choque con otros dispositivos (Ej. `192.168.1.50`). Llenar la máscara y puerta de enlace anotadas. (DNS: `8.8.8.8` y `8.8.4.4`).

## 3. Configurar la Red como "Privada" y abrir Firewall
Windows bloquea conexiones entrantes por defecto si la red está configurada como Pública.
- En la configuración de Wi-Fi/Ethernet, asegurar que el perfil de red esté en **Privado**.
- **Regla de Firewall:** Se deben abrir los puertos **8000** (Backend) y **5173** (Frontend) en el Firewall de Windows Defender, o desactivar temporalmente el firewall para la red privada si es un entorno cerrado seguro.

## 4. Ejecución del Sistema para Red Local (¡Importante!)
Para levantar el sistema de manera que sea visible para los celulares, los comandos cambian ligeramente:

**Backend (En una terminal):**
```powershell
docker compose up -d
```
*(Docker ya expone el puerto al localhost y a la red LAN automáticamente).*

**Frontend (En otra terminal):**
```powershell
cd frontend
npm run dev -- --host
```
*(⚠️ CRÍTICO: Si no se pone `--host`, Vite solo dejará entrar al computador local y bloqueará a los celulares de los meseros).*

## 5. Conexión de los Dispositivos (Meseros y Cocina)
1. Conectar los celulares/tablets a la **red Wi-Fi del restaurante**. (Desactivar datos móviles para evitar problemas).
2. Abrir Chrome/Safari y escribir la IP configurada en el Paso 2:
   `http://192.168.1.50:5173`
3. Usar la opción "Añadir a la pantalla de inicio" del navegador para instalar la PWA como una app nativa.
