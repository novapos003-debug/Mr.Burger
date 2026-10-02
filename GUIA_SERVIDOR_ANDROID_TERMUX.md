# 📱 Guía Definitiva: Servidor Autónomo en Pantalla Android (Termux)

Esta guía detalla cómo convertir la pantalla táctil Android fija de la caja en el **servidor central del restaurante (Cerebro Local)** sin requerir computadores externos ni conexión a la nube.

---

## 1. Descarga e Instalación de Termux en la Pantalla

> ⚠️ **IMPORTANTE:** NO instales Termux desde Google Play Store (está desactualizada y falla al instalar paquetes).

1. Abre el navegador de la pantalla Android y descarga el APK oficial desde F-Droid:
   👉 **URL de descarga:** `https://f-droid.org/repo/com.termux_118.apk`
2. Instala el APK en la pantalla Android y ábrelo.

---

## 2. Preparación del Sistema Android

Dentro de la pantalla negra de Termux, corre estos comandos iniciales:

```bash
# 1. Dar permisos de almacenamiento interno (aparecerá ventana en Android, dale "Permitir")
termux-setup-storage

# 2. Impedir que Android duerma el servidor o corte los procesos
termux-wake-lock
```

---

## 3. Instalación de Motor Linux (Python, PostgreSQL y Node.js)

Copia y pega este comando en Termux para instalar todo el entorno:

```bash
pkg update -y && pkg install -y python python-pip postgresql git nodejs clang make libjpeg-turbo libffi
```

---

## 4. Configurar e Inicializar PostgreSQL en Android

Ejecuta estos comandos para crear la base de datos interna:

```bash
# 1. Crear el clúster de datos
initdb -D $PREFIX/var/lib/postgresql

# 2. Encender el motor de PostgreSQL
pg_ctl -D $PREFIX/var/lib/postgresql -l $PREFIX/var/log/postgres.log start

# 3. Crear el usuario y la base de datos de Mr. Burger
createuser -s restaurante
createdb -O restaurante restaurante
psql -U restaurante -d restaurante -c "ALTER USER restaurante WITH PASSWORD 'restaurante_dev';"
```

---

## 5. Descargar / Copiar el Código de Mr. Burger

Puedes clonar el repositorio directamente desde GitHub:

```bash
cd ~
git clone https://github.com/novapos003-debug/Mr.Burger.git mrburger
cd mrburger
```

*(O si lo pasas por memoria USB, lo copias desde `/sdcard/Download`)*.

---

## 6. Cargar los Datos y Recetas en PostgreSQL

Ejecuta las migraciones y catálogo real:

```bash
psql -U restaurante -d restaurante -f database/init/01_schema.sql
psql -U restaurante -d restaurante -f database/init/02_seeds.sql
psql -U restaurante -d restaurante -f database/init/03_migracion_arquitectura_e_insumos.sql
```

---

## 7. Instalar Librerías de Python

```bash
pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings python-multipart python-jose[cryptography] passlib[bcrypt] psycopg2-binary httpx websockets
```

---

## 8. Script de Arranque Automático en 1 Solo Toque

Crea un script llamado `iniciar.sh` para que no tengas que escribir comandos cada día:

```bash
cat << 'EOF' > ~/iniciar.sh
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
pg_ctl -D $PREFIX/var/lib/postgresql start

cd ~/mrburger/backend
export DATABASE_URL="postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
export SECRET_KEY="ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

cd ~/mrburger/frontend
npx serve -s dist -l 5173 --cors &

echo "================================================="
echo "🍔 MR. BURGER SERVIDOR ANDROID ACTIVO"
echo "IP Local en Pantalla: http://$(ifconfig wlan0 | grep 'inet ' | awk '{print $2}'):5173"
echo "================================================="
EOF

chmod +x ~/iniciar.sh
```

---

## 9. ¿Cómo se opera día a día?

1. Al encender la pantalla Android, abres la app **Termux**.
2. Escribes: `./iniciar.sh` y das Enter.
3. Termux te mostrará en verde la IP local (Ej: `http://192.168.1.50:5173`).
4. **En la misma pantalla Android:** Abres Chrome y entras a `http://localhost:5173` (o la IP). Le das a "Instalar aplicación" y abres la caja registradora.
5. **En la cocina y celulares de meseros:** Abren en Chrome la IP que mostró Termux (`http://192.168.1.50:5173`).

Todo queda 100% autónomo dentro de la pantalla Android fija, sin depender de computadores externos ni de la nube.
