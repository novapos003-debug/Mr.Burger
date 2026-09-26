"""Harness E2E Fase 16: Motor de Sincronización Offline-Online con Idempotencia UUID.

Verifica:
1. Permisos: staff autorizado (mesero, caja, admin) para sincronizar terminales; anónimo 401.
2. Idempotencia absoluta por UUID: reenvío de operaciones no genera duplicados.
3. Regla de autoridad (Documento Maestro, Sección 3):
   - Ventas locales mandan sobre espejo de nube.
   - Configuración de nube manda sobre catálogo local.
4. Pull incremental: descarga de operaciones producidas 'since' timestamp.
5. Métricas de estado de sincronización.
"""

import sys
import uuid
from datetime import datetime, timezone

import httpx

from app.database import SessionLocal
from app.models import RegistroSync

BASE = "http://localhost:8000"
USERS = {"admin": "admin123", "caja": "caja123", "mesero": "mesero123", "cocina": "cocina123"}

PASS = 0
FAIL = 0
FALLOS = []


def check(nombre, cond, detalle=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {nombre}")
    else:
        FAIL += 1
        FALLOS.append(nombre)
        print(f"  FAIL {nombre}  {detalle}")


def login(c):
    return httpx.post(f"{BASE}/auth/login", data={"username": c, "password": USERS[c]}).json()["access_token"]


TOK = {c: login(c) for c in USERS}


def hdr(c):
    return {"Authorization": f"Bearer {TOK[c]}"}


# ============================================================
print("== 1. Permisos y Autenticación ==")
# ============================================================
check("anonimo_push_401", httpx.post(f"{BASE}/sync/push", json={"dispositivo_id": "test", "operaciones": []}).status_code == 401)
check("anonimo_pull_401", httpx.get(f"{BASE}/sync/pull").status_code == 401)
check("mesero_pull_200", httpx.get(f"{BASE}/sync/pull", headers=hdr("mesero")).status_code == 200)
check("caja_estado_200", httpx.get(f"{BASE}/sync/estado", headers=hdr("caja")).status_code == 200)


# ============================================================
print("== 2. Push Offline con UUIDs (Idempotencia) ==")
# ============================================================
uid1 = str(uuid.uuid4())
uid2 = str(uuid.uuid4())
uid3 = str(uuid.uuid4())

lote = {
    "dispositivo_id": "tablet_mesero_1",
    "operaciones": [
        {
            "op_id": uid1,
            "dispositivo_id": "tablet_mesero_1",
            "tipo": "CREAR_PEDIDO",
            "entidad": "pedido",
            "entidad_id": 101,
            "payload": {"canal": "MESA", "mesa_id": 1, "total": 15000},
            "origen": "LOCAL",
        },
        {
            "op_id": uid2,
            "dispositivo_id": "tablet_mesero_1",
            "tipo": "AGREGAR_RONDA",
            "entidad": "detalle_pedido",
            "entidad_id": 202,
            "payload": {"ronda": 2, "producto_id": 5, "cantidad": 2},
            "origen": "LOCAL",
        },
        {
            "op_id": uid3,
            "dispositivo_id": "tablet_mesero_1",
            "tipo": "COBRO_PEDIDO",
            "entidad": "pago",
            "entidad_id": 303,
            "payload": {"metodo": "EFECTIVO", "monto": 21000},
            "origen": "LOCAL",
        },
    ],
}

# Primer envío: debe procesar las 3 operaciones
r_push1 = httpx.post(f"{BASE}/sync/push", headers=hdr("mesero"), json=lote)
check("push1_200", r_push1.status_code == 200, r_push1.text)
p1 = r_push1.json()
check("push1_procesadas_3", p1["procesadas"] == 3, f"procesadas={p1['procesadas']}")
check("push1_duplicadas_0", p1["duplicadas"] == 0)
check("push1_conflictos_0", p1["conflictos"] == 0)

# Reenvío exacto (simulando desconexión durante respuesta del servidor):
# DEBE ser 100% idempotente: 0 procesadas nuevas, 3 duplicadas
r_push2 = httpx.post(f"{BASE}/sync/push", headers=hdr("mesero"), json=lote)
check("push2_200", r_push2.status_code == 200)
p2 = r_push2.json()
check("push2_idempotencia_duplicadas_3", p2["duplicadas"] == 3, f"duplicadas={p2['duplicadas']}")
check("push2_procesadas_0", p2["procesadas"] == 0)


# ============================================================
print("== 3. Regla de Autoridad (Local vs Nube) ==")
# ============================================================
# Caso A: La nube intenta enviar una transacción de ventas => CONFLICTO (el local manda)
uid_conflicto = str(uuid.uuid4())
lote_conflicto = {
    "dispositivo_id": "servidor_nube",
    "operaciones": [
        {
            "op_id": uid_conflicto,
            "dispositivo_id": "servidor_nube",
            "tipo": "MODIFICAR_VENTA",
            "entidad": "pedido",
            "entidad_id": 101,
            "payload": {"total": 5000},
            "origen": "NUBE",
        }
    ],
}
r_conf = httpx.post(f"{BASE}/sync/push", headers=hdr("admin"), json=lote_conflicto)
check("conflicto_push_200", r_conf.status_code == 200)
p_conf = r_conf.json()
check("conflicto_detectado_1", p_conf["conflictos"] == 1, f"conflictos={p_conf['conflictos']}")
check("conflicto_estado_operacion", p_conf["operaciones"][0]["estado"] == "CONFLICTO")

# Caso B: La nube envía un cambio de catálogo/precios => APLICADO (la nube manda en configuración)
uid_catalogo = str(uuid.uuid4())
lote_catalogo = {
    "dispositivo_id": "servidor_nube",
    "operaciones": [
        {
            "op_id": uid_catalogo,
            "dispositivo_id": "servidor_nube",
            "tipo": "ACTUALIZAR_PRECIO",
            "entidad": "producto",
            "entidad_id": 1,
            "payload": {"precio": 13000},
            "origen": "NUBE",
        }
    ],
}
r_cat = httpx.post(f"{BASE}/sync/push", headers=hdr("admin"), json=lote_catalogo)
check("catalogo_push_200", r_cat.status_code == 200)
p_cat = r_cat.json()
check("catalogo_nube_aplicado", p_cat["procesadas"] == 1 and p_cat["operaciones"][0]["estado"] == "APLICADO")


# ============================================================
print("== 4. Pull de Operaciones (Puesta al Día) ==")
# ============================================================
r_pull = httpx.get(f"{BASE}/sync/pull?limit=50", headers=hdr("mesero"))
check("pull_200", r_pull.status_code == 200)
ops = r_pull.json()
check("pull_contiene_operaciones", len(ops) >= 5)

# Filtro por origen
r_pull_local = httpx.get(f"{BASE}/sync/pull?origen=LOCAL", headers=hdr("mesero"))
check("pull_filtro_local", all(o["origen"] == "LOCAL" for o in r_pull_local.json()))

r_pull_nube = httpx.get(f"{BASE}/sync/pull?origen=NUBE", headers=hdr("mesero"))
check("pull_filtro_nube", all(o["origen"] == "NUBE" for o in r_pull_nube.json()))


# ============================================================
print("== 5. Estado y Métricas de Sincronización ==")
# ============================================================
r_est = httpx.get(f"{BASE}/sync/estado", headers=hdr("admin"))
check("estado_200", r_est.status_code == 200)
estado = r_est.json()
check("estado_cerebro_modo", estado["cerebro_modo"] == "LOCAL")
check("estado_total_ops", estado["total_operaciones"] >= 5)
check("estado_aplicadas", estado["aplicadas"] >= 4)
check("estado_conflictos", estado["conflictos"] >= 1)
check("estado_ultima_sync_not_null", estado["ultima_sincronizacion"] is not None)

print("\n" + "=" * 50)
print(f"RESULTADO FASE 16 (OFFLINE + SYNC): {PASS} PASS / {FAIL} FAIL")
print("=" * 50)

if FALLOS:
    print(f"FALLOS ({len(FALLOS)}):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
