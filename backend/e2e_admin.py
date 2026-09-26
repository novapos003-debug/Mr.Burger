"""Harness E2E Fase 15: Panel de Administración, Dashboard, Reportes, Compras y Auditoría.

Verifica:
1. Permisos estrictos: solo rol admin puede acceder a /admin/*.
2. Dashboard gerencial: KPIs en vivo, ticket promedio, canales, tipos, métodos, top productos, stock.
3. Reporte de ventas histórico por rango de fechas y desglose diario.
4. Stock crítico con cálculo de déficit y presupuesto estimado de reabastecimiento.
5. Módulo de compras a proveedores: ingreso de stock, actualización de costos y movimientos COMPRA.
6. Bitácora inmutable de auditoría con filtros y paginación.
"""

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

import httpx

from app.database import SessionLocal
from app.models import Ingrediente, MovimientoInventario

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


def d(x):
    return Decimal(str(x))


# ============================================================
print("== 1. Permisos del Panel de Administración ==")
# ============================================================
check("mesero_dashboard_403", httpx.get(f"{BASE}/admin/dashboard", headers=hdr("mesero")).status_code == 403)
check("caja_dashboard_403", httpx.get(f"{BASE}/admin/dashboard", headers=hdr("caja")).status_code == 403)
check("cocina_dashboard_403", httpx.get(f"{BASE}/admin/dashboard", headers=hdr("cocina")).status_code == 403)
check("anonimo_dashboard_401", httpx.get(f"{BASE}/admin/dashboard").status_code == 401)
check("admin_dashboard_200", httpx.get(f"{BASE}/admin/dashboard", headers=hdr("admin")).status_code == 200)

check("mesero_reportes_403", httpx.get(f"{BASE}/admin/reportes/ventas?desde=2026-01-01&hasta=2026-01-02", headers=hdr("mesero")).status_code == 403)
check("mesero_stock_critico_403", httpx.get(f"{BASE}/admin/stock-critico", headers=hdr("mesero")).status_code == 403)
check("mesero_compras_403", httpx.get(f"{BASE}/admin/compras", headers=hdr("mesero")).status_code == 403)
check("mesero_auditoria_403", httpx.get(f"{BASE}/admin/auditoria", headers=hdr("mesero")).status_code == 403)


# ============================================================
print("== 2. Dashboard Gerencial (KPIs en Vivo) ==")
# ============================================================
r_dash = httpx.get(f"{BASE}/admin/dashboard", headers=hdr("admin"))
check("dash_status_200", r_dash.status_code == 200)
dash = r_dash.json()

check("dash_fecha_presente", "fecha" in dash)
check("dash_total_ventas", d(dash["total_ventas"]) >= 0)
check("dash_total_pedidos", dash["total_pedidos"] >= 0)
check("dash_ticket_promedio", d(dash["ticket_promedio"]) >= 0)
check("dash_canales_incluidos", all(c in dash["ventas_por_canal"] for c in ["MESA", "MOSTRADOR", "DIDI", "DOMICILIO"]))
check("dash_tipos_incluidos", "COMIDA" in dash["ventas_por_tipo"] and "BEBIDA" in dash["ventas_por_tipo"])
check("dash_metodos_incluidos", all(m in dash["pagos_por_metodo"] for m in ["EFECTIVO", "TARJETA", "TRANSFERENCIA", "VALE"]))
check("dash_top_productos_lista", isinstance(dash["top_productos"], list))
check("dash_alertas_stock_lista", isinstance(dash["alertas_stock"], list))
check("dash_preparados_count", dash["preparados_disponibles_count"] >= 0)
check("dash_vales_monto", d(dash["vales_pendientes_monto"]) >= 0)


# ============================================================
print("== 3. Reportes Históricos de Ventas ==")
# ============================================================
hoy = date.today().isoformat()
ayer = (date.today() - timedelta(days=1)).isoformat()
manana = (date.today() + timedelta(days=1)).isoformat()

# Validación: desde > hasta
r_invalido = httpx.get(f"{BASE}/admin/reportes/ventas?desde={manana}&hasta={ayer}", headers=hdr("admin"))
check("reporte_fecha_invalida_422", r_invalido.status_code == 422)

# Consulta válida
r_rep = httpx.get(f"{BASE}/admin/reportes/ventas?desde={ayer}&hasta={manana}", headers=hdr("admin"))
check("reporte_200", r_rep.status_code == 200)
rep = r_rep.json()
check("reporte_total_ventas", d(rep["total_ventas"]) >= 0)
check("reporte_desglose_diario", isinstance(rep["desglose_diario"], list))
check("reporte_ventas_canal", isinstance(rep["ventas_por_canal"], dict))

# Con filtro de canal
r_rep_canal = httpx.get(f"{BASE}/admin/reportes/ventas?desde={ayer}&hasta={manana}&canal=MOSTRADOR", headers=hdr("admin"))
check("reporte_filtro_canal_200", r_rep_canal.status_code == 200)


# ============================================================
print("== 4. Stock Crítico y Alertas ==")
# ============================================================
r_crit = httpx.get(f"{BASE}/admin/stock-critico", headers=hdr("admin"))
check("stock_critico_200", r_crit.status_code == 200)
criticos = r_crit.json()
check("stock_critico_lista", isinstance(criticos, list))
if criticos:
    item = criticos[0]
    check("critico_campos", all(k in item for k in ["ingrediente_id", "nombre", "stock_actual", "stock_minimo", "deficit", "costo_reabastecer"]))


# ============================================================
print("== 5. Compras a Proveedores (Reabastecimiento) ==")
# ============================================================
# Consultar stock actual de tomate (ingrediente 4)
ings = httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).json()
ing4_antes = d(next(i for i in ings if i["id"] == 4)["stock_actual"])

# Registrar orden de compra de 100 unidades de tomate a $2200 cada uno
compra_data = {
    "proveedor_id": 1,
    "descripcion": "Reabastecimiento semanal verduras",
    "detalles": [
        {"ingrediente_id": 4, "cantidad": 100, "costo_unitario": 2200},
    ],
}
r_compra = httpx.post(f"{BASE}/admin/compras", headers=hdr("admin"), json=compra_data)
check("crear_compra_201", r_compra.status_code == 201, r_compra.text)
compra = r_compra.json()
check("compra_total_calculado", d(compra["costo_total"]) == d(100 * 2200))
check("compra_detalles_count", len(compra["detalles"]) == 1)

# Verificar incremento real de stock
ings_desp = httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).json()
ing4_desp = d(next(i for i in ings_desp if i["id"] == 4)["stock_actual"])
check("stock_ingrediente_incrementado", ing4_desp == ing4_antes + Decimal("100"))

# Verificar actualización del costo_unitario del ingrediente
ing4_costo = d(next(i for i in ings_desp if i["id"] == 4)["costo_unitario"])
check("costo_unitario_actualizado", ing4_costo == Decimal("2200"))

# Verificar movimiento de inventario tipo COMPRA en BD
db = SessionLocal()
mov = (
    db.query(MovimientoInventario)
    .filter(MovimientoInventario.compra_id == compra["id"], MovimientoInventario.ingrediente_id == 4)
    .first()
)
check("movimiento_inventario_compra_creado", mov is not None and mov.tipo == "COMPRA" and d(mov.cantidad) == Decimal("100"))
db.close()

# Listar compras
r_list_comp = httpx.get(f"{BASE}/admin/compras", headers=hdr("admin"))
check("listar_compras_200", r_list_comp.status_code == 200)
check("compra_en_lista", any(c["id"] == compra["id"] for c in r_list_comp.json()))


# ============================================================
print("== 6. Auditoría e Historial de Acciones ==")
# ============================================================
r_aud = httpx.get(f"{BASE}/admin/auditoria?limit=20", headers=hdr("admin"))
check("auditoria_200", r_aud.status_code == 200)
aud_lista = r_aud.json()
check("auditoria_elementos", len(aud_lista) > 0)
check("auditoria_campos", all(k in aud_lista[0] for k in ["id", "accion", "entidad", "detalle", "creado_en"]))

# Filtro por acción
r_aud_filtro = httpx.get(f"{BASE}/admin/auditoria?accion=REGISTRAR_COMPRA", headers=hdr("admin"))
check("auditoria_filtro_accion", all(a["accion"] == "REGISTRAR_COMPRA" for a in r_aud_filtro.json()))

print("\n" + "=" * 50)
print(f"RESULTADO FASE 15 (PANEL ADMIN): {PASS} PASS / {FAIL} FAIL")
print("=" * 50)

if FALLOS:
    print(f"FALLOS ({len(FALLOS)}):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
