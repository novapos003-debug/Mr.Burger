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
echo "📥 1/2 Descargando cambios de GitHub..."
git pull origin main

# Si no existe dist precompilado, compilar como respaldo
if [ ! -d ~/mrburger/frontend/dist ]; then
    echo "⚡ Compilando Frontend..."
    cd ~/mrburger/frontend
    npm run build
fi

# 2. Reiniciar servicios
echo "🔄 2/2 Refrescando servicios..."
pkill -f "serve -s dist" || true
cd ~/mrburger/frontend
nohup serve -s dist -l 5173 --cors > ~/frontend.log 2>&1 &

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
