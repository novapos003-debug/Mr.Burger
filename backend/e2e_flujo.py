"""Harness E2E de FLUJO OPERATIVO COMPLETO (fases 1-8).

No prueba endpoints aislados: recorre el dia real del restaurante siguiendo la
idea establecida y verifica que el comportamiento respeta las reglas del dueno:

  mesero crea -> envia a cocina -> cocina acepta (descuenta inventario,
  mesa EN_CURSO) -> rondas -> listo -> caja cobra -> cierre de turno.

Cubre los 4 canales, cobro adelantado, DiDi, vales, devolucion, ocultamiento de
dinero y consistencia del cierre contra lo realmente operado.
"""

import sys
from decimal import Decimal

import httpx
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Cierre, DetalleReceta, Ingrediente, Mesa, MovimientoInventario, Pago, Pedido

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


def crear(canal, lineas, user="mesero", **extra):
    body = {"canal": canal, "lineas": lineas}
    body.update(extra)
    return httpx.post(f"{BASE}/pedidos", headers=hdr(user), json=body)


def enviar(pid):
    return httpx.post(f"{BASE}/pedidos/{pid}/enviar-a-cocina", headers=hdr("mesero"))


def get_pedido(pid, user="mesero"):
    return httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr(user)).json()


def aceptar(det_id):
    return httpx.post(f"{BASE}/cocina/detalles/{det_id}/aceptar", headers=hdr("cocina"))


def listo(det_id):
    return httpx.post(f"{BASE}/cocina/detalles/{det_id}/listo", headers=hdr("cocina"))


def cola():
    return httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()


def cobrar(pid, pagos, user="caja"):
    return httpx.post(f"{BASE}/caja/pedidos/{pid}/cobrar", headers=hdr(user), json={"pagos": pagos})


def mesa_estado(numero):
    for m in httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("mesero")).json():
        if m["numero"] == numero:
            return m["estado"]
    return None


def stock(nombre):
    s = SessionLocal()
    ing = s.query(Ingrediente).filter(Ingrediente.nombre == nombre).first()
    v = d(ing.stock_actual)
    s.close()
    return v


def detalle_ids(pid):
    p = get_pedido(pid)
    return {dd["producto_id"]: dd["id"] for dd in p["detalles"]}


# ============================================================
# PRECONDICIONES: mesas 1-3 libres, sin turno abierto, historico barrido
# ============================================================
s = SessionLocal()
for p in s.query(Pedido).filter(Pedido.mesa_id.in_([1, 2, 3]), Pedido.estado.notin_(("PAGADO", "CERRADO", "CANCELADO"))).all():
    p.estado = "CANCELADO"
    p.cancelado_en = func.now()
for m in s.query(Mesa).filter(Mesa.id.in_([1, 2, 3])).all():
    m.estado = "DISPONIBLE"
s.commit()
s.close()

t = httpx.get(f"{BASE}/caja/turno", headers=hdr("caja")).json()
if t:
    httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "baseline-flujo"})
httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 0})
httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "barrido-flujo"})

print("== [Turno] Apertura con fondo de caja ==")
r = httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 10000})
check("turno_abierto_201", r.status_code == 201, r.text[:150])
turno_id = r.json()["id"]

# ============================================================
print("\n== [A] MESA: ciclo completo con ronda, inventario y dinero oculto ==")
MESA_A = 1
stock_antes_envio = {n: stock(n) for n in ("Pan", "Carne", "Queso Cheddar", "Lechuga", "Salsa")}
r = crear("MESA", [{"producto_id": 1, "cantidad": 1}, {"producto_id": 5, "cantidad": 1}], mesa_id=MESA_A)
check("crear_mesa_201", r.status_code == 201, r.text[:200])
pa = r.json()
check("mesa_ocupada_al_crear", mesa_estado(MESA_A) == "OCUPADA", mesa_estado(MESA_A))
pa_cocina = httpx.get(f"{BASE}/pedidos/{pa['id']}", headers=hdr("cocina")).json()
check("cocina_no_ve_dinero", pa_cocina["subtotal"] is None and pa_cocina["iva"] is None and pa_cocina["total"] is None)
check("precio_linea_oculto_cocina", all(x["precio_unitario"] is None for x in pa_cocina["detalles"]))
check("mesero_si_ve_dinero", pa["total"] is not None)
check("no_doble_pedido_mesa", crear("MESA", [{"producto_id": 5, "cantidad": 1}], mesa_id=MESA_A).status_code == 409)

r = enviar(pa["id"])
check("enviar_200", r.status_code == 200)
check("estado_enviado", resp_estado := get_pedido(pa["id"])["estado"] == "ENVIADO_A_COCINA", resp_estado)
check("enviar_no_descuenta_inventario",
      all(stock(n) == stock_antes_envio[n] for n in stock_antes_envio),
      "el stock cambio al enviar")

ticket = next((x for x in cola() if x["pedido_id"] == pa["id"]), None)
check("ticket_en_cola", ticket is not None)
check("ticket_sin_dinero", ticket is not None and not any(k in str(ticket).lower() for k in ("precio", "total", "subtotal", "iva")))
check("ticket_con_productos", ticket and ticket["rondas"][0]["detalles"][0]["producto_nombre"] == "Hamburguesa Clásica")

ids_a = detalle_ids(pa["id"])
det_hamb = ids_a[1]
det_gase = ids_a[5]
r = aceptar(det_hamb)
check("aceptar_200", r.status_code == 200, r.text[:150])
check("mesa_en_curso_al_aceptar", mesa_estado(MESA_A) == "EN_CURSO", mesa_estado(MESA_A))
check("pedido_en_preparacion", get_pedido(pa["id"])["estado"] == "EN_PREPARACION")
check("inventario_baja_harina", stock("Pan") == stock_antes_envio["Pan"] - 2, f"pan={stock('Pan')}")
check("inventario_baja_carne", stock("Carne") == stock_antes_envio["Carne"] - 125, f"carne={stock('Carne')}")
check("inventario_baja_queso", stock("Queso Cheddar") == stock_antes_envio["Queso Cheddar"] - 1)
check("inventario_baja_lechuga", stock("Lechuga") == stock_antes_envio["Lechuga"] - 20)
check("inventario_baja_salsa", stock("Salsa") == stock_antes_envio["Salsa"] - 15)
s = SessionLocal()
mov = s.query(MovimientoInventario).filter(MovimientoInventario.pedido_id == pa["id"]).all()
check("movimientos_venta_negativos", len(mov) == 5 and all(m.tipo == "VENTA" and d(m.cantidad) < 0 for m in mov), f"n={len(mov)}")
s.close()

aceptar(det_gase)
s = SessionLocal()
mov_gaseosa = s.query(MovimientoInventario).filter(
    MovimientoInventario.pedido_id == pa["id"],
    MovimientoInventario.referencia.like("%Gaseosa%"),
).count()
s.close()
check("sin_movimiento_bebida", mov_gaseosa == 0, f"movs={mov_gaseosa}")

r = httpx.put(f"{BASE}/pedidos/mesas/{MESA_A}/estado", headers=hdr("mesero"), json={"estado": "DISPONIBLE"})
check("mesero_no_cambia_mesa_403", r.status_code == 403, r.status_code)
r = httpx.put(f"{BASE}/pedidos/mesas/{MESA_A}/estado", headers=hdr("caja"), json={"estado": "DISPONIBLE"})
check("caja_no_libera_mesa_con_pedido_409", r.status_code == 409, r.status_code)

r = httpx.post(f"{BASE}/pedidos/{pa['id']}/rondas", headers=hdr("mesero"),
               json={"ronda": 2, "lineas": [{"producto_id": 4, "cantidad": 1}]})
check("ronda_201", r.status_code == 201, r.text[:150])
ticket_a = next((y for y in cola() if y["pedido_id"] == pa["id"]), None)
check("ronda_en_ticket", ticket_a is not None and any(r["ronda"] == 2 for r in ticket_a["rondas"]))
ids_a = detalle_ids(pa["id"])
aceptar(ids_a[4])  # la ronda nueva debe pasar por cocina (papas, sin receta)
listo(ids_a[4])
listo(ids_a[1])
listo(ids_a[5])
check("pedido_finalizado", get_pedido(pa["id"])["estado"] == "FINALIZADO", get_pedido(pa["id"])["estado"])
r = httpx.put(f"{BASE}/pedidos/mesas/{MESA_A}/estado", headers=hdr("caja"), json={"estado": "DISPONIBLE"})
check("no_libera_mesa_finalizada_409", r.status_code == 409, r.status_code)

r = cobrar(pa["id"], [{"metodo": "EFECTIVO", "monto": 21000, "recibido": 25000}])
check("cobro_efectivo_200", r.status_code == 200, r.text[:200])
check("cambio_4000", r.json()["pagos"][0]["cambio"] == "4000.00", r.json()["pagos"][0]["cambio"])
check("pedido_pagado", get_pedido(pa["id"])["estado"] == "PAGADO")
check("mesa_liberada_al_pagar", mesa_estado(MESA_A) == "DISPONIBLE", mesa_estado(MESA_A))
check("ronda_tras_pago_409", httpx.post(f"{BASE}/pedidos/{pa['id']}/rondas", headers=hdr("mesero"),
      json={"ronda": 3, "lineas": [{"producto_id": 5, "cantidad": 1}]}).status_code == 409)

# ============================================================
print("\n== [B] MESA: cobro ADELANTADO mientras la cocina produce ==")
MESA_B = 2
pb = crear("MESA", [{"producto_id": 3, "cantidad": 1}, {"producto_id": 5, "cantidad": 1}], mesa_id=MESA_B).json()
enviar(pb["id"])
ids_b = detalle_ids(pb["id"])
aceptar(ids_b[3])
aceptar(ids_b[5])
check("mesa_b_en_curso", mesa_estado(MESA_B) == "EN_CURSO")
r = cobrar(pb["id"], [{"metodo": "TARJETA", "monto": 11000}])
check("cobro_adelantado_200", r.status_code == 200, r.text[:200])
check("pagado_en_sin_cambiar_estado", get_pedido(pb["id"])["estado"] == "EN_PREPARACION", get_pedido(pb["id"])["estado"])
check("mesa_no_liberada_adelantado", mesa_estado(MESA_B) == "EN_CURSO", mesa_estado(MESA_B))
listo(ids_b[3])
listo(ids_b[5])
check("pagado_al_terminar_cocina", get_pedido(pb["id"])["estado"] == "PAGADO", get_pedido(pb["id"])["estado"])
check("mesa_liberada_al_terminar", mesa_estado(MESA_B) == "DISPONIBLE", mesa_estado(MESA_B))

# ============================================================
print("\n== [C] MOSTRADOR: del mostrador a caja ==")
pc = crear("MOSTRADOR", [{"producto_id": 4, "cantidad": 2}]).json()
enviar(pc["id"])
aceptar(detalle_ids(pc["id"])[4])
listo(detalle_ids(pc["id"])[4])
check("mostrador_finalizado", get_pedido(pc["id"])["estado"] == "FINALIZADO")
r = cobrar(pc["id"], [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 12000}])
check("mostrador_pagado", r.status_code == 200 and get_pedido(pc["id"])["estado"] == "PAGADO", r.text[:150])
check("cambio_cero", r.json()["pagos"][0]["cambio"] == "0.00")

# ============================================================
print("\n== [D] DIDI: orden obligatoria, tarjeta por cobrar, efectivo local ==")
check("didi_sin_orden_422", crear("DIDI", [{"producto_id": 2, "cantidad": 1}]).status_code == 422)
pd1 = crear("DIDI", [{"producto_id": 2, "cantidad": 1}], didi_orden_id="DD-FLUJO-1").json()
check("didi_con_orden_201", pd1["id"] is not None and pd1["didi_orden_id"] == "DD-FLUJO-1")
enviar(pd1["id"])
aceptar(detalle_ids(pd1["id"])[2])
r = cobrar(pd1["id"], [{"metodo": "DIDI_TARJETA", "monto": 15000}])
check("didi_tarjeta_adelantado_200", r.status_code == 200, r.text[:150])
listo(detalle_ids(pd1["id"])[2])
check("didi_tarjeta_pagado", get_pedido(pd1["id"])["estado"] == "PAGADO")
p_sin_orden = crear("MOSTRADOR", [{"producto_id": 6, "cantidad": 1}]).json()
check("pago_didi_sin_orden_422",
      cobrar(p_sin_orden["id"], [{"metodo": "DIDI_EFECTIVO", "monto": 2000}]).status_code == 422)
pd2 = crear("DIDI", [{"producto_id": 6, "cantidad": 1}], didi_orden_id="DD-FLUJO-2").json()
enviar(pd2["id"])
aceptar(detalle_ids(pd2["id"])[6])
listo(detalle_ids(pd2["id"])[6])
r = cobrar(pd2["id"], [{"metodo": "DIDI_EFECTIVO", "monto": 2000}])
check("didi_efectivo_pagado", r.status_code == 200 and get_pedido(pd2["id"])["estado"] == "PAGADO", r.text[:150])

# ============================================================
print("\n== [E] VALE: pagare pendiente y su cobro ==")
pe = crear("MOSTRADOR", [{"producto_id": 5, "cantidad": 1}]).json()
rv = cobrar(pe["id"], [{"metodo": "VALE", "monto": 3000, "vale_cliente_nombre": "Cliente Flujo", "vale_cliente_cedula": "123"}])
check("vale_creado", rv.status_code == 200 and len(rv.json()["vales"]) == 1, rv.text[:150])
check("vale_pendiente", rv.json()["vales"][0]["estado"] == "PENDIENTE")
vale_id = rv.json()["vales"][0]["id"]
check("vale_cobro_200", httpx.post(f"{BASE}/caja/vales/{vale_id}/cobrar", headers=hdr("caja"), json={}).status_code == 200)
cobrados = httpx.get(f"{BASE}/caja/vales?estado=COBRADO", headers=hdr("caja")).json()
check("vale_cobrado", any(v["id"] == vale_id for v in cobrados))
check("vale_doble_cobro_409", httpx.post(f"{BASE}/caja/vales/{vale_id}/cobrar", headers=hdr("caja"), json={}).status_code == 409)

# ============================================================
print("\n== [F] DEVOLUCION: un pago invalida el cobro ==")
pf = crear("MOSTRADOR", [{"producto_id": 6, "cantidad": 1}]).json()
enviar(pf["id"])
aceptar(detalle_ids(pf["id"])[6])
listo(detalle_ids(pf["id"])[6])
rp = cobrar(pf["id"], [{"metodo": "TARJETA", "monto": 2000}]).json()
check("f_pagado", get_pedido(pf["id"])["estado"] == "PAGADO")
r = httpx.post(f"{BASE}/caja/pagos/{rp['pagos'][0]['id']}/devolver", headers=hdr("caja"), json={"motivo": "Cliente desistio"})
check("devolucion_200", r.status_code == 200, r.text[:150])
check("vuelve_a_finalizado", get_pedido(pf["id"])["estado"] == "FINALIZADO", get_pedido(pf["id"])["estado"])
check("queda_por_pagar", get_pedido(pf["id"])["pagado"] is False)

# ============================================================
print("\n== [C2] DOMICILIO: cuarto canal, con direccion ==")
pd = crear("DOMICILIO", [{"producto_id": 3, "cantidad": 1}], cliente="Ana", telefono="3001234567", direccion="Calle 1 #2-3").json()
check("domicilio_201", pd["id"] is not None and pd["canal"] == "DOMICILIO")
check("domicilio_guarda_direccion", get_pedido(pd["id"], "caja")["direccion"] == "Calle 1 #2-3")
enviar(pd["id"])
aceptar(detalle_ids(pd["id"])[3])
listo(detalle_ids(pd["id"])[3])
check("domicilio_finalizado", get_pedido(pd["id"])["estado"] == "FINALIZADO")
r = cobrar(pd["id"], [{"metodo": "EFECTIVO", "monto": 8000, "recibido": 10000}])
check("domicilio_pagado", r.status_code == 200 and get_pedido(pd["id"])["estado"] == "PAGADO", r.text[:150])
check("domicilio_cambio_2000", r.json()["pagos"][0]["cambio"] == "2000.00")

# ============================================================
print("\n== [G] IVA y consecutivo por dia ==")
pg = get_pedido(pa["id"], "caja")
check("identidad_iva", d(pg["subtotal"]) + d(pg["iva"]) == d(pg["total"]), pg)
check("iva_conforme_regimen", d(pg["iva"]) in (d("0.00"), d("3352.94")), pg["iva"])
consecutivos = [get_pedido(x, "caja")["consecutivo"] for x in (pa["id"], pb["id"], pc["id"], pd1["id"])]
check("consecutivos_correlativos", consecutivos == list(range(consecutivos[0], consecutivos[0] + 4)), consecutivos)
check("fecha_dia_local", get_pedido(pa["id"], "caja")["fecha_dia"] is not None)

# ============================================================
print("\n== [H] CIERRE: el fotograma coincide con lo operado ==")
r = httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "Fin del dia (flujo)"})
check("cierre_200", r.status_code == 200, r.text[:200])
c = r.json()
check("cierre_pedidos_7", c["total_pedidos"] == 7, c["total_pedidos"])
check("cierre_ventas_72000", d(c["total_ventas"]) == 72000, c["total_ventas"])
check("cierre_efectivo_41000", d(c["total_efectivo"]) == 41000, c["total_efectivo"])
check("cierre_tarjeta_11000", d(c["total_tarjeta"]) == 11000, c["total_tarjeta"])
check("cierre_vale_3000", d(c["total_vale"]) == 3000, c["total_vale"])
check("cierre_didi_tarjeta_15000", d(c["total_didi_tarjeta"]) == 15000, c["total_didi_tarjeta"])
check("cierre_didi_efectivo_2000", d(c["total_didi_efectivo"]) == 2000, c["total_didi_efectivo"])
check("cierre_comida_61000", d(c["total_venta_comida"]) == 61000, c["total_venta_comida"])
check("cierre_bebida_11000", d(c["total_venta_bebida"]) == 11000, c["total_venta_bebida"])
check("cierre_entradas_13000", d(c["total_entradas_caja"]) == 13000, c["total_entradas_caja"])
check("cierre_salidas_2000", d(c["total_salidas_caja"]) == 2000, c["total_salidas_caja"])
check("cierre_devoluciones_2000", d(c["total_devoluciones"]) == 2000, c["total_devoluciones"])
check("cierre_egresos_0", c["cantidad_egresos"] == 0, c["cantidad_egresos"])
check("cierre_efectivo_final_54000", d(c["total_efectivo_final"]) == 54000, c["total_efectivo_final"])
check("cierre_por_cobrar_didi", d(c["total_por_cobrar"]) >= 15000, c["total_por_cobrar"])

s = SessionLocal()
check("sin_pagos_sueltos", s.query(Pago).filter(Pago.cierre_id.is_(None)).count() == 0)
check("sin_turno_abierto", s.query(Cierre).filter(Cierre.cerrado_en.is_(None)).count() == 0)
s.close()

print()
print("=" * 56)
print(f"RESULTADO FLUJO OPERATIVO: {PASS} PASS / {FAIL} FAIL")
if FALLOS:
    print("Fallos:", ", ".join(FALLOS))
print("=" * 56)
sys.exit(1 if FAIL else 0)
