"""Harness E2E Fase 8 (Cierre de caja): apertura/cierre de turno, fotograma,
entradas-egresos manuales admin. Corre dentro del contenedor contra httpx."""

import sys
from decimal import Decimal

import httpx

from app.database import SessionLocal
from app.models import Cierre, MovimientoCaja, Pago

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


STOCK_SEGURO = {1: 1000, 2: 100000, 3: 1000, 4: 500, 5: 100000, 6: 100000, 7: 1000, 8: 100000, 9: 1000}


def asegurar_stock():
    for ing_id, valor in STOCK_SEGURO.items():
        httpx.put(f"{BASE}/ingredientes/{ing_id}", headers=hdr("admin"), json={"stock_actual": valor})


asegurar_stock()


def d(x):
    return Decimal(str(x))


def crear(canal, lineas, **extra):
    body = {"canal": canal, "lineas": lineas}
    body.update(extra)
    return httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json=body).json()


def cobrar(pid, pagos, user="caja"):
    return httpx.post(f"{BASE}/caja/pedidos/{pid}/cobrar", headers=hdr(user), json={"pagos": pagos})


def turno():
    return httpx.get(f"{BASE}/caja/turno", headers=hdr("caja")).json()


# ---------- limpieza: cerrar turno abierto y barrer históricos ----------
t = turno()
if t:
    httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "baseline"})
httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 0})
httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "barrido historico"})

print("== 1. Permisos ==")
check("mesero_abrir_403", httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("mesero"), json={"monto_inicial": 0}).status_code == 403)
check("cocina_abrir_403", httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("cocina"), json={"monto_inicial": 0}).status_code == 403)
check("mesero_turno_403", httpx.get(f"{BASE}/caja/turno", headers=hdr("mesero")).status_code == 403)
check("cocina_cierres_403", httpx.get(f"{BASE}/caja/cierres", headers=hdr("cocina")).status_code == 403)
check("caja_movimiento_403", httpx.post(f"{BASE}/caja/movimientos", headers=hdr("caja"),
      json={"tipo": "SALIDA", "categoria": "PROVEEDOR", "valor": 1000, "descripcion": "prueba"}).status_code == 403)

print("== 2. Apertura de turno ==")
r = httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 50000})
check("abrir_201", r.status_code == 201, r.text[:200])
turno_id = r.json()["id"]
check("turno_abierto_sin_cerrar", r.json()["cerrado_en"] is None, r.json()["cerrado_en"])
check("abrir_dos_veces_409", httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 0}).status_code == 409)
movs = httpx.get(f"{BASE}/caja/movimientos?categoria=CAMBIO_INICIAL", headers=hdr("caja")).json()
check("fondo_inicial_registrado", any(d(m["valor"]) == 50000 and m["tipo"] == "ENTRADA" for m in movs))

print("== 3. Operaciones del turno ==")
# a) comida en efectivo con cambio
pa = crear("MOSTRADOR", [{"producto_id": 1, "cantidad": 1}])
r = cobrar(pa["id"], [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 15000}])
check("efectivo_200", r.status_code == 200 and r.json()["pagos"][0]["cambio"] == "3000.00", r.text[:150])
# b) bebida con tarjeta
pb = crear("MOSTRADOR", [{"producto_id": 5, "cantidad": 1}])
check("tarjeta_200", cobrar(pb["id"], [{"metodo": "TARJETA", "monto": 3000}]).status_code == 200)
# c) movimientos manuales admin
r = httpx.post(f"{BASE}/caja/movimientos", headers=hdr("admin"),
               json={"tipo": "SALIDA", "categoria": "PROVEEDOR", "valor": 10000, "descripcion": "Compra de pan"})
check("egreso_admin_201", r.status_code == 201, r.text[:150])
check("egreso_entra_al_turno", r.json().get("valor") == "10000.00")
r = httpx.post(f"{BASE}/caja/movimientos", headers=hdr("admin"),
               json={"tipo": "ENTRADA", "categoria": "PRESTAMO", "valor": 5000, "descripcion": "Prestamo interno"})
check("ingreso_admin_201", r.status_code == 201, r.text[:150])
check("mov_descripcion_corta_422", httpx.post(f"{BASE}/caja/movimientos", headers=hdr("admin"),
      json={"tipo": "SALIDA", "categoria": "OTRO", "valor": 100, "descripcion": "x"}).status_code == 422)
check("mov_valor_cero_422", httpx.post(f"{BASE}/caja/movimientos", headers=hdr("admin"),
      json={"tipo": "SALIDA", "categoria": "OTRO", "valor": 0, "descripcion": "algo"}).status_code == 422)
check("mov_categoria_invalida_422", httpx.post(f"{BASE}/caja/movimientos", headers=hdr("admin"),
      json={"tipo": "SALIDA", "categoria": "NOEXISTE", "valor": 100, "descripcion": "algo"}).status_code == 422)
# d) VALE -> crear pagaré y luego cobrarlo
pd = crear("MOSTRADOR", [{"producto_id": 6, "cantidad": 1}])
rv = cobrar(pd["id"], [{"metodo": "VALE", "monto": 2000, "vale_cliente_nombre": "Jorge Cierre"}])
check("vale_creado", rv.status_code == 200 and len(rv.json()["vales"]) == 1, rv.text[:150])
vale_id = rv.json()["vales"][0]["id"]
check("vale_cobrado", httpx.post(f"{BASE}/caja/vales/{vale_id}/cobrar", headers=hdr("caja"), json={}).status_code == 200)
# e) DiDi tarjeta (por cobrar)
pe = crear("DIDI", [{"producto_id": 3, "cantidad": 1}], didi_orden_id="DD-CIERRE")
check("didi_tarjeta_200", cobrar(pe["id"], [{"metodo": "DIDI_TARJETA", "monto": 8000}]).status_code == 200)
# f) cobro + devolución
pf = crear("MOSTRADOR", [{"producto_id": 6, "cantidad": 1}])
rp = cobrar(pf["id"], [{"metodo": "TARJETA", "monto": 2000}]).json()
check("devolucion_200", httpx.post(f"{BASE}/caja/pagos/{rp['pagos'][0]['id']}/devolver", headers=hdr("caja"),
      json={"motivo": "Cliente cancelo"}).status_code == 200)

print("== 4. Cierre de turno (fotograma) ==")
r = httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "Cierre de prueba"})
check("cerrar_200", r.status_code == 200, r.text[:200])
c = r.json()
check("cerrado_en_seteado", c["cerrado_en"] is not None)
check("total_pedidos_4", c["total_pedidos"] == 4, c["total_pedidos"])
check("venta_comida_20000", d(c["total_venta_comida"]) == 20000, c["total_venta_comida"])
check("venta_bebida_5000", d(c["total_venta_bebida"]) == 5000, c["total_venta_bebida"])
check("total_ventas_25000", d(c["total_ventas"]) == 25000, c["total_ventas"])
check("total_efectivo_12000", d(c["total_efectivo"]) == 12000, c["total_efectivo"])
check("total_tarjeta_3000", d(c["total_tarjeta"]) == 3000, c["total_tarjeta"])
check("total_vale_2000", d(c["total_vale"]) == 2000, c["total_vale"])
check("total_didi_tarjeta_8000", d(c["total_didi_tarjeta"]) == 8000, c["total_didi_tarjeta"])
check("total_entradas_57000", d(c["total_entradas_caja"]) == 57000, c["total_entradas_caja"])
check("total_salidas_12000", d(c["total_salidas_caja"]) == 12000, c["total_salidas_caja"])
check("cantidad_egresos_1", c["cantidad_egresos"] == 1, c["cantidad_egresos"])
check("total_devoluciones_2000", d(c["total_devoluciones"]) == 2000, c["total_devoluciones"])
check("efectivo_final_57000", d(c["total_efectivo_final"]) == 57000, c["total_efectivo_final"])
check("por_cobrar_incluye_didi", d(c["total_por_cobrar"]) >= 8000, c["total_por_cobrar"])
check("notas_guardadas", c["notas"] == "Cierre de prueba")

print("== 5. Estado posterior e inmutabilidad ==")
check("sin_turno_abierto", turno() is None)
check("cerrar_sin_turno_409", httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={}).status_code == 409)
lista = httpx.get(f"{BASE}/caja/cierres", headers=hdr("caja")).json()
check("cierre_en_lista", any(x["id"] == turno_id for x in lista))
o = httpx.get(f"{BASE}/caja/cierres/{turno_id}", headers=hdr("caja"))
check("obtener_cierre_200", o.status_code == 200 and d(o.json()["total_ventas"]) == 25000)
check("cierre_inexistente_404", httpx.get(f"{BASE}/caja/cierres/999999", headers=hdr("caja")).status_code == 404)

s = SessionLocal()
check("pagos_barridos_sin_cierre", s.query(Pago).filter(Pago.cierre_id.is_(None)).count() == 0)
check("movs_barridos_sin_cierre", s.query(MovimientoCaja).filter(MovimientoCaja.cierre_id.is_(None)).count() == 0)
check("cierre_unico", s.query(Cierre).filter(Cierre.cerrado_en.is_(None)).count() == 0)
s.close()

print()
print("=" * 50)
print(f"RESULTADO FASE 8: {PASS} PASS / {FAIL} FAIL")
if FALLOS:
    print("Fallos:", ", ".join(FALLOS))
print("=" * 50)
sys.exit(1 if FAIL else 0)
