#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# SCRIPT DE ACTUALIZACIÓN RÁPIDA - MR. BURGER POS (TERMUX)
# ============================================================
set -e

echo ""
echo "🍔 =========================================="
echo "   ACTUALIZANDO MR. BURGER A LA ÚLTIMA VERSIÓN"
echo "=============================================="
echo ""

cd ~/mrburger

# 1. Descargar cambios de GitHub
echo "📥 1/3 Descargando cambios de GitHub..."
git pull origin main

# 2. Reconstruir Frontend
echo "⚡ 2/3 Recompilando Frontend..."
cd ~/mrburger/frontend
npm run build

# 3. Reiniciar el servidor Frontend para servir los nuevos archivos
echo "🔄 3/3 Reiniciando servicios..."
pkill -f "serve -s dist" || true
nohup serve -s dist -l 5173 --cors > ~/frontend.log 2>&1 &

# Reiniciar Backend por si hubo cambios en Python
pkill -f "uvicorn app.main:app" || true
cd ~/mrburger/backend
export DATABASE_URL="postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
export SECRET_KEY="ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/backend.log 2>&1 &

echo ""
echo "✅ ¡MR. BURGER ACTUALIZADO CON ÉXITO!"
echo "   Todos los celulares y pantallas conectadas"
echo "   recibirán la nueva versión automáticamente."
echo "=============================================="
echo ""
