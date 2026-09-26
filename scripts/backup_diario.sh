#!/bin/bash
# ============================================================
# SCRIPT DE RESPALDO AUTOMÁTICO DE BASE DE DATOS (Linux/Docker)
# Restaurante Mr. Burger
# ============================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$DIR/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="backup_pos_${TIMESTAMP}.dump"
LOCAL_PATH="$BACKUP_DIR/$FILENAME"

echo "================================================="
echo "INICIANDO RESPALDO DE BASE DE DATOS: $TIMESTAMP"
echo "================================================="

if ! docker ps | grep -q "restaurante_db"; then
    echo "ERROR: El contenedor 'restaurante_db' no está activo."
    exit 1
fi

echo "[1/3] Volcando base de datos con compresión..."
docker exec restaurante_db pg_dump -U restaurante -d restaurante -F c -b -v -f /tmp/backup_temp.dump

echo "[2/3] Extrayendo a $LOCAL_PATH..."
docker cp restaurante_db:/tmp/backup_temp.dump "$LOCAL_PATH"
docker exec restaurante_db rm -f /tmp/backup_temp.dump

echo "[3/3] Depurando respaldos con más de 30 días de antigüedad..."
find "$BACKUP_DIR" -name "backup_pos_*.dump" -type f -mtime +30 -delete

echo "✓ Respaldo completado exitosamente: $LOCAL_PATH"
