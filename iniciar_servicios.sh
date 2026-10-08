#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# MR. BURGER POS - ARRANQUE Y MANTENIMIENTO AUTÓNOMO 100% INVISIBLE
# ==============================================================================
termux-wake-lock

# 0. Sincronización Remota Segura con GitHub (Máx. 2 segundos si hay internet)
if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    cd ~/mrburger
    rm -f .git/index.lock
    git fetch origin main --quiet 2>/dev/null || true
    git reset --hard origin/main --quiet 2>/dev/null || true
fi

# 1. PostgreSQL - Motor de Base de Datos Local
if ! pg_isready -q; then
    pg_ctl -D $PREFIX/var/lib/postgresql start
fi

# 2. Backend - FastAPI (Puerto 8000)
if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
    cd ~/mrburger/backend
    export DATABASE_URL="postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
    export SECRET_KEY="ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj"
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/backend.log 2>&1 &
fi

# 3. Frontend - Servidor Web Estático PWA (Puerto 5173)
if ! pgrep -f "serve -s dist" > /dev/null; then
    cd ~/mrburger/frontend
    nohup serve -s dist -l 5173 --cors > ~/frontend.log 2>&1 &
fi

# 4. Demonio de Auto-Actualización en Segundo Plano (Cada 15 min mientras está abierto)
if ! pgrep -f "mrburger_auto_updater" > /dev/null; then
    nohup bash -c '
    while true; do
        sleep 900
        if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
            cd ~/mrburger
            BEFORE=$(git rev-parse HEAD 2>/dev/null)
            rm -f .git/index.lock
            git fetch origin main --quiet 2>/dev/null || true
            git reset --hard origin/main --quiet 2>/dev/null || true
            AFTER=$(git rev-parse HEAD 2>/dev/null)
            if [ "$BEFORE" != "$AFTER" ]; then
                echo "[$(date)] ¡Actualización remota aplicada con éxito desde GitHub!" >> ~/update.log
                pkill -f "uvicorn app.main:app" || true
                cd ~/mrburger/backend
                export DATABASE_URL="postgresql://restaurante:restaurante_dev@localhost:5432/restaurante"
                export SECRET_KEY="ymKGPH7kaMDwp4CJZluFvgU3BRcAnbrj"
                nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> ~/backend.log 2>&1 &
            fi
        fi
    done
    ' > /dev/null 2>&1 &
fi
