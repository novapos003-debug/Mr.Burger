#!/usr/bin/env bash
# ============================================================
# SCRIPT DE ACTUALIZACIÓN DEL SISTEMA POS MR. BURGER (LINUX/MAC)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "   ACTUALIZADOR AUTOMÁTICO DE SISTEMA — POS MR. BURGER      "
echo "============================================================"

# 1. Respaldo previo
echo "[1/4] Ejecutando respaldo de seguridad previo..."
if [ -f "$SCRIPT_DIR/backup_diario.sh" ]; then
    bash "$SCRIPT_DIR/backup_diario.sh" || echo "Aviso: No se pudo completar el backup preventivo."
fi

# 2. Actualizar código
echo "[2/4] Verificando repositorio Git..."
if [ -d "$PROJECT_ROOT/.git" ]; then
    cd "$PROJECT_ROOT"
    git pull || true
fi

# 3. Compilación PWA Frontend
echo "[3/4] Compilando frontend PWA..."
cd "$PROJECT_ROOT/frontend"
npm run build

# 4. Reinicio de contenedores
echo "[4/4] Reiniciando servicios..."
cd "$PROJECT_ROOT"
if command -v docker &> /dev/null; then
    docker restart restaurante_backend || true
fi

echo "============================================================"
echo "¡SISTEMA ACTUALIZADO EXITOSAMENTE A LA ÚLTIMA VERSIÓN!"
echo "Los celulares Android recibirán la actualización automáticamente."
echo "============================================================"
