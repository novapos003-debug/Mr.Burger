"""
Auditoria Extrema - Pruebas de estrés y casos límite (Edge Cases)
Ejecuta solicitudes directamente contra la app FastAPI usando TestClient.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Usuario, Rol, Categoria, TipoCategoria, Producto, Mesa
from app.core.security import hash_password
import json

# Setup DB for tests
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Asegurar datos minimos para las pruebas si no existen
def setup_db():
    if not db.query(Rol).first():
        db.add_all([
            Rol(nombre="admin"), Rol(nombre="cajero"), Rol(nombre="mesero"), Rol(nombre="cocina")
        ])
        db.commit()
    
    # Crear usuarios de prueba
    if not db.query(Usuario).filter_by(usuario="test_hacker").first():
        db.add(Usuario(
            usuario="test_hacker", nombre="Hacker", password_hash=hash_password("hack123"),
            rol_id=db.query(Rol).filter_by(nombre="mesero").first().id, activo=True
        ))
    if not db.query(Usuario).filter_by(usuario="test_admin").first():
        db.add(Usuario(
            usuario="test_admin", nombre="Admin Test", password_hash=hash_password("admin123"),
            rol_id=db.query(Rol).filter_by(nombre="admin").first().id, activo=True
        ))
    if not db.query(Usuario).filter_by(usuario="test_caja").first():
        db.add(Usuario(
            usuario="test_caja", nombre="Caja Test", password_hash=hash_password("caja123"),
            rol_id=db.query(Rol).filter_by(nombre="cajero").first().id, activo=True
        ))
    db.commit()

    # Tipos, Categorias, Productos y Mesas
    if not db.query(TipoCategoria).first():
        tc = TipoCategoria(nombre="COMIDA")
        db.add(tc)
        db.commit()
        c = Categoria(nombre="Hamburguesas", tipo_id=tc.id)
        db.add(c)
        db.commit()
        p = Producto(nombre="Burguer Test", precio=15000, categoria_id=c.id)
        db.add(p)
        db.commit()
    if not db.query(Mesa).filter_by(numero="1").first():
        db.add(Mesa(numero="1", estado="DISPONIBLE"))
        db.commit()

setup_db()
db.close()

client = TestClient(app)

print("INICIANDO AUDITORIA EXTREMA (STRESS & EDGE CASES)...\n")

def get_token(username, password):
    res = client.post("/api/auth/login", data={"username": username, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

token_admin = get_token("test_admin", "admin123")
token_hacker = get_token("test_hacker", "hack123")
token_caja = get_token("test_caja", "caja123")

headers_admin = {"Authorization": f"Bearer {token_admin}"}
headers_hacker = {"Authorization": f"Bearer {token_hacker}"}
headers_caja = {"Authorization": f"Bearer {token_caja}"}

resultados = {"PASS": 0, "FAIL": 0, "detalles": []}

def asertar(nombre, condicion, detalle=""):
    if condicion:
        resultados["PASS"] += 1
        print(f" [PASS] {nombre}")
    else:
        resultados["FAIL"] += 1
        resultados["detalles"].append(f"{nombre} - {detalle}")
        print(f" [FAIL] {nombre} | {detalle}")

# 1. Seguridad y Autenticacion
print("--- 1. SEGURIDAD Y AUTENTICACION ---")
res = client.post("/api/auth/login", data={"username": "test_admin", "password": "wrongpassword"})
asertar("Login con credenciales invalidas debe fallar", res.status_code == 401)

# Rate limiting (10 intentos fallidos)
for _ in range(7):
    client.post("/api/auth/login", data={"username": "test_admin", "password": "wrong"})
res = client.post("/api/auth/login", data={"username": "test_admin", "password": "wrong"})
asertar("Rate Limit activo tras multiples intentos", res.status_code == 429)

res = client.get("/api/admin/dashboard", headers=headers_hacker)
asertar("RBAC: Mesero no puede acceder a dashboard Admin", res.status_code in [401, 403], f"Status: {res.status_code}")

# 2. Modulo de Asistencia
print("--- 2. MODULO DE ASISTENCIA ---")
res = client.post("/api/asistencia/entrada", headers=headers_hacker)
asertar("Registrar entrada por primera vez", res.status_code == 200)

res2 = client.post("/api/asistencia/entrada", headers=headers_hacker)
asertar("Doble entrada devuelve el mismo turno activo sin error", res2.status_code == 200 and res.json()["id"] == res2.json()["id"])

res = client.post("/api/asistencia/salida", headers=headers_hacker)
asertar("Registrar salida exitosa", res.status_code == 200)

res = client.post("/api/asistencia/salida", headers=headers_hacker)
asertar("Registrar salida de turno ya cerrado da error", res.status_code == 400)

# 3. Pedidos Limite
print("--- 3. CREACION DE PEDIDOS AL LIMITE ---")

# 3.0 Probar que sin turno activo NO se pueden hacer pedidos
res_sin_turno = client.post("/api/pedidos", json={"canal": "MESA", "mesa_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]}, headers=headers_hacker)
asertar("Empleado sin turno activo NO puede crear pedidos (Seguridad)", res_sin_turno.status_code == 401)

# Abrir turno para las pruebas que siguen
client.post("/api/asistencia/entrada", headers=headers_hacker)
client.post("/api/asistencia/entrada", headers=headers_caja)

# 3.1 Pedido sin productos
payload = {"canal": "MESA", "mesa_id": 1, "lineas": []}
res = client.post("/api/pedidos", json=payload, headers=headers_hacker)
asertar("No se puede crear pedido vacío", res.status_code in [400, 422])

# 3.2 Cantidad negativa
payload = {"canal": "MESA", "mesa_id": 1, "lineas": [{"producto_id": 1, "cantidad": -5}]}
res = client.post("/api/pedidos", json=payload, headers=headers_hacker)
asertar("Validacion: No permite cantidades negativas", res.status_code in [400, 422])

# 3.3 Mesa invalida
payload = {"canal": "MESA", "mesa_id": 9999, "lineas": [{"producto_id": 1, "cantidad": 1}]}
res = client.post("/api/pedidos", json=payload, headers=headers_hacker)
asertar("No se puede asignar a mesa inexistente", res.status_code in [400, 404, 422], f"Status real: {res.status_code} - {res.json()}")

# 3.4 Inyección SQL o Tipos inválidos en JSON
payload = {"canal": "MESA", "mesa_id": "1 OR 1=1", "lineas": [{"producto_id": 1, "cantidad": 1}]}
res = client.post("/api/pedidos", json=payload, headers=headers_hacker)
asertar("Proteccion contra SQLi/Tipos en mesa_id", res.status_code == 422)

# Crear un pedido valido
payload = {"canal": "MESA", "mesa_id": 1, "lineas": [{"producto_id": 1, "cantidad": 2}]}
res = client.post("/api/pedidos", json=payload, headers=headers_hacker)
asertar("Creacion de pedido válido exitosa", res.status_code in [200, 201], f"Status: {res.status_code} Error: {res.text}")
pedido_id = res.json().get("id", 0)

# 4. Pagos y Caja (Condiciones de carrera o reglas de negocio)
print("--- 4. CAJA Y PAGOS ---")
# Primero debe haber turno de caja
res = client.post("/api/caja/turno/abrir", json={"monto_inicial": 50000}, headers=headers_caja)
asertar("Abrir turno de caja", res.status_code in [200, 201, 409], f"Status: {res.status_code} Error: {res.text}") # 409 if already open

if pedido_id != 0:
    # Cobrar pedido valido
    res = client.post(f"/api/caja/pedidos/{pedido_id}/cobrar", json={
        "monto_total_calculado": 30000, 
        "pagos": [{"metodo": "EFECTIVO", "monto": 30000, "recibido": 50000}]
    }, headers=headers_caja)
    asertar("Cobrar pedido con vuelto correcto", res.status_code in [200, 201], f"Status: {res.status_code} Error: {res.text}")

    # Intentar cobrar de nuevo el mismo
    res = client.post(f"/api/caja/pedidos/{pedido_id}/cobrar", json={
        "monto_total_calculado": 30000, 
        "pagos": [{"metodo": "EFECTIVO", "monto": 30000, "recibido": 50000}]
    }, headers=headers_caja)
    asertar("Doble cobro del mismo pedido bloqueado (Seguridad)", res.status_code == 409, f"Status: {res.status_code} Error: {res.text}")

    # Devolver pago
    res_pago = client.get(f"/api/caja/pedidos/{pedido_id}/pagos", headers=headers_caja)
    if res_pago.status_code == 200 and len(res_pago.json()) > 0:
        pago_id = res_pago.json()[0]["id"]
        res = client.post(f"/api/caja/pagos/{pago_id}/devolver", json={"motivo": "Auditoria test"}, headers=headers_admin)
        asertar("Admin puede devolver pago", res.status_code in [200, 201], f"Status: {res.status_code} Error: {res.text}")

        res = client.post(f"/api/caja/pagos/{pago_id}/devolver", json={"motivo": "Doble test"}, headers=headers_admin)
        asertar("Pago no se puede devolver dos veces", res.status_code == 409, f"Status: {res.status_code} Error: {res.text}")

# 5. Cierre de Caja con cierre de asistencia
print("--- 5. INTEGRACION CAJA - ASISTENCIA ---")
client.post("/api/asistencia/entrada", headers=headers_hacker) # Abrimos un turno de hacker que olvida cerrar
res_cierre = client.post("/api/caja/turno/cerrar", json={"notas": "Cierre test extremo", "retiros": []}, headers=headers_caja)
asertar("Cierre de caja exitoso", res_cierre.status_code in [200, 201], f"Status: {res.status_code} Error: {res.text}")

# Verificar que el turno de asistencia se cerró
res_turno_hacker = client.get("/api/asistencia/mi-turno", headers=headers_hacker)
asertar("Turno de empleado cerrado automáticamente por Cierre de Caja", res_turno_hacker.json() is None, f"Status: {res.status_code}")

print("\n=== RESUMEN AUDITORIA EXTREMA ===")
print(f"PASSED: {resultados['PASS']}")
print(f"FAILED: {resultados['FAIL']}")
if resultados["detalles"]:
    for f in resultados["detalles"]:
        print(f"  -> {f}")
