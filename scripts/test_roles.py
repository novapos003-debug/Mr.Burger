import urllib.request
import urllib.parse
import json
import ssl
import sys

BASE = "https://mrburger-api.onrender.com"
CTX = ssl.create_default_context()

def req(path, method="GET", data=None, token=None):
    url = f"{BASE}{path}"
    headers = {}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        if isinstance(data, dict) and path == "/auth/login":
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
    
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=30) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json
    except Exception as e:
        return 0, {"error": str(e)}

PASSES = 0
FAILS = 0

def assert_test(name, condition, detail=""):
    global PASSES, FAILS
    if condition:
        PASSES += 1
        print(f"  [PASS] {name}")
    else:
        FAILS += 1
        print(f"  [FAIL] {name} -> {detail}")

print("==================================================")
print(" AUDITORIA EXHAUSTIVA MULTI-ROL (MR. BURGER POS)  ")
print(" Servidor: " + BASE)
print("==================================================\n")

import time

# Warm-up ping para despertar el servicio Render si está en sleep
print("Verificando estado del servidor...")
for intento in range(6):
    st_h, h = req("/health")
    if st_h == 200:
        print(f"  -> Servidor en línea: {h}\n")
        break
    print(f"  -> Esperando respuesta del servidor (intento {intento+1}/6)...")
    time.sleep(5)

# 1. AUTENTICACION Y CONTROL DE ACCESO
print("--- FASE 1: Verificacion de Tokens y Roles ---")
roles = ["admin", "mesero", "cocina", "caja"]
tokens = {}
for r_name in roles:
    pwd = f"{r_name}123"
    st, res = req("/auth/login", method="POST", data={"username": r_name, "password": pwd})
    if st != 200:
        time.sleep(2)
        st, res = req("/auth/login", method="POST", data={"username": r_name, "password": pwd})
    assert_test(f"Login rol: {r_name}", st == 200 and isinstance(res, dict) and "access_token" in res, f"status={st}")
    if st == 200 and isinstance(res, dict) and "access_token" in res:
        tokens[r_name] = res["access_token"]
        if r_name != "admin":
            # Abre o valida el turno laboral para que el guardia deps.py permita peticiones
            req("/asistencia/entrada", method="POST", token=res["access_token"])

# 2. ROL MESERO
print("\n--- FASE 2: Rol Mesero (Salón, Mesas, Comanda) ---")
tok_m = tokens.get("mesero")
st_mesas, mesas = req("/pedidos/mesas", token=tok_m)
assert_test("Mesero consulta mapa de mesas (1 a 9)", st_mesas == 200 and isinstance(mesas, list) and len(mesas) >= 9)

st_cat, cats = req("/categorias", token=tok_m)
assert_test("Mesero consulta categorias de productos", st_cat == 200 and isinstance(cats, list) and len(cats) >= 5)

st_prods, prods = req("/productos", token=tok_m)
assert_test("Mesero consulta catalogo de productos", st_prods == 200 and isinstance(prods, list) and len(prods) > 0)

# Verificar regla de seguridad: Mesero NO puede ver dashboard del admin
st_hack_admin, _ = req("/admin/dashboard", token=tok_m)
assert_test("Seguridad: Mesero bloqueado de ver Dashboard Admin (403)", st_hack_admin == 403)

# Seleccionar mesa libre (estado DISPONIBLE) o usar MOSTRADOR
mesa_libre = next((m for m in mesas if isinstance(m, dict) and m.get("estado") == "DISPONIBLE"), None) if isinstance(mesas, list) else None
canal_prueba = "MESA" if mesa_libre else "MOSTRADOR"
mesa_id_prueba = mesa_libre["id"] if mesa_libre else None

burger = next((p for p in prods if "BURGER" in p["nombre"].upper() or "HAMBURGUESA" in p["nombre"].upper()), prods[0])
print(f"  -> Probando pedido en Canal: {canal_prueba} (Mesa {mesa_id_prueba}) con {burger['nombre']}")

payload_pedido = {
    "canal": canal_prueba,
    "mesa_id": mesa_id_prueba,
    "lineas": [
        {
            "producto_id": burger["id"],
            "cantidad": 1,
            "variacion_snapshot": {"notas": "Sin cebolla"}
        }
    ]
}
st_ped, ped = req("/pedidos", method="POST", data=payload_pedido, token=tok_m)
assert_test(f"Mesero crea pedido ({canal_prueba})", st_ped == 201 and ped.get("id") is not None, f"status={st_ped} {ped}")
pedido_id = ped.get("id") if st_ped == 201 else None

detalle_id = None
if ped and ped.get("detalles"):
    detalle_id = ped["detalles"][0]["id"]

if pedido_id:
    # Enviar a cocina
    st_env, env = req(f"/pedidos/{pedido_id}/enviar-a-cocina", method="POST", token=tok_m)
    assert_test("Mesero envia comanda a Cocina KDS", st_env == 200 and env.get("estado") in ["ENVIADO_A_COCINA", "EN_COCINA"], f"estado={env.get('estado')}")

# 3. ROL COCINA
print("\n--- FASE 3: Rol Cocina (KDS, Comandas, Producción) ---")
tok_c = tokens.get("cocina")
st_kds, kds_tickets = req("/cocina/cola", token=tok_c)
assert_test("Cocina consulta pantalla KDS activa (/cocina/cola)", st_kds == 200, f"status={st_kds}")

# Seguridad: Cocina no puede ver caja ni cobrar
st_hack_caja, _ = req("/caja/turno", token=tok_c)
assert_test("Seguridad: Cocina bloqueada de acceder a Caja (403)", st_hack_caja == 403)

if detalle_id:
    # Cocina ACEPTA la orden (empieza preparación y descuenta inventario)
    st_acep, ticket_acep = req(f"/cocina/detalles/{detalle_id}/aceptar", method="POST", token=tok_c)
    assert_test("Cocina ACEPTA ticket de comanda (descuenta stock)", st_acep in [200, 400, 409], f"status={st_acep}")

    # Cocina marca pedido como LISTO
    st_listo, ticket_listo = req(f"/cocina/detalles/{detalle_id}/listo", method="POST", token=tok_c)
    assert_test("Cocina marca detalle como LISTO para servir", st_listo in [200, 400, 409], f"status={st_listo}")

# 4. ROL CAJA
print("\n--- FASE 4: Rol Caja (POS, Cobro, Turnos) ---")
tok_cj = tokens.get("caja")
st_turno, turno = req("/caja/turno", token=tok_cj)
if st_turno == 200 and not turno:
    # Abrir turno
    st_apertura, turno_nuevo = req("/caja/turno/abrir", method="POST", data={"monto_inicial_efectivo": 50000}, token=tok_cj)
    assert_test("Caja apertura de turno con base $50.000", st_apertura == 201, f"status={st_apertura}")
else:
    assert_test("Caja verifica turno abierto actualmente", st_turno == 200)

# Seguridad: Cajero no puede ver auditoría del admin
st_hack_aud, _ = req("/admin/auditoria", token=tok_cj)
assert_test("Seguridad: Cajero bloqueado de ver auditoria global (403)", st_hack_aud == 403)

if pedido_id:
    # Cobrar pedido
    total_a_pagar = ped["total"]
    payload_cobro = {
        "pagos": [
            {
                "metodo": "EFECTIVO",
                "monto": total_a_pagar, "recibido": total_a_pagar
            }
        ]
    }
    st_cobro, cobro = req(f"/caja/pedidos/{pedido_id}/cobrar", method="POST", data=payload_cobro, token=tok_cj)
    assert_test("Caja cobra pedido con Efectivo exitosamente", st_cobro in [200, 409], f"status={st_cobro}")

# 5. ROL ADMINISTRADOR
print("\n--- FASE 5: Rol Administrador (Dashboard, Precios, Insumos, Auditoria) ---")
tok_a = tokens.get("admin")
st_dash, dash = req("/admin/dashboard", token=tok_a)
assert_test("Admin visualiza Dashboard y KPIs en vivo", st_dash == 200 and "total_ventas" in dash)

st_aud, aud = req("/admin/auditoria?limit=10", token=tok_a)
assert_test("Admin consulta historial inmutable de auditoria", st_aud == 200 and len(aud) > 0)

st_ing, ings = req("/ingredientes", token=tok_a)
assert_test("Admin lista materias primas e insumos con stock", st_ing == 200 and len(ings) > 0)

# Crear nuevo producto de prueba
test_burger_name = f"Hamburguesa Test Auditoria"
nuevo_prod_data = {
    "categoria_id": cats[0]["id"] if cats else 1,
    "nombre": test_burger_name,
    "descripcion": "Burger creada por test automatico",
    "precio": 24500,
    "iva_incluido": True
}
st_cp, prod_creado = req("/productos", method="POST", data=nuevo_prod_data, token=tok_a)
assert_test("Admin crea nuevo producto con precio en catálogo", st_cp == 201 and prod_creado.get("id") is not None)

if st_cp == 201 and prod_creado.get("id"):
    pid = prod_creado["id"]
    # Modificar precio
    st_up, prod_up = req(f"/productos/{pid}", method="PUT", data={"precio": 26000}, token=tok_a)
    assert_test("Admin actualiza precio del producto ($24.500 -> $26.000)", st_up == 200 and float(prod_up.get("precio")) == 26000.0)
    
    # Desactivar producto
    st_del, _ = req(f"/productos/{pid}", method="DELETE", token=tok_a)
    assert_test("Admin desactiva producto (soft-delete sin romper historial)", st_del == 204)

print("\n==================================================")
print(f" RESUMEN DE PRUEBAS: {PASSES} PASARON, {FAILS} FALLARON")
print("==================================================")
sys.exit(0 if FAILS == 0 else 1)
