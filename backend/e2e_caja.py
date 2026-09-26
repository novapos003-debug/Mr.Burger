"""Harness E2E Fase 7 (Caja): cobros, vales, DiDi, devoluciones y su integración
con cocina (cobro adelantado). Corre dentro del contenedor contra httpx."""

import sys

import httpx

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
    r = httpx.post(f"{BASE}/auth/login", data={"username": c, "password": USERS[c]})
    return r.json()["access_token"]


TOK = {c: login(c) for c in USERS}


def hdr(c):
    return {"Authorization": f"Bearer {TOK[c]}"}


STOCK_SEGURO = {1: 1000, 2: 100000, 3: 1000, 4: 500, 5: 100000, 6: 100000, 7: 1000, 8: 100000, 9: 1000}


def asegurar_stock():
    for ing_id, valor in STOCK_SEGURO.items():
        httpx.put(f"{BASE}/ingredientes/{ing_id}", headers=hdr("admin"), json={"stock_actual": valor})


asegurar_stock()


def crear_pedido(canal, lineas, **extra):
    body = {"canal": canal, "lineas": lineas}
    body.update(extra)
    return httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json=body)


def cobrar(pedido_id, pagos, user="caja"):
    return httpx.post(f"{BASE}/caja/pedidos/{pedido_id}/cobrar", headers=hdr(user), json={"pagos": pagos})


def detalle_id(pedido, producto_id, ronda=1):
    for d in pedido["detalles"]:
        if d["producto_id"] == producto_id and d["ronda"] == ronda:
            return d["id"]
    return None


print("== 1. Permisos: solo caja/admin cobran ==")
p = crear_pedido("MOSTRADOR", [{"producto_id": 5, "cantidad": 1}]).json()
check("mesero_cobrar_403", cobrar(p["id"], [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}], "mesero").status_code == 403)
check("cocina_cobrar_403", cobrar(p["id"], [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}], "cocina").status_code == 403)
check("mesero_vales_403", httpx.get(f"{BASE}/caja/vales", headers=hdr("mesero")).status_code == 403)

print("== 2. Mostrador: cobro adelantado NO saca el pedido de cocina ==")
p = crear_pedido("MOSTRADOR", [{"producto_id": 1, "cantidad": 1}]).json()
pid = p["id"]
p_coc = httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("cocina")).json()
check("cocina_no_ve_total", p_coc["total"] is None)
check("mesero_si_ve_total", p["total"] is not None)
pa = httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("caja")).json()
check("total_caja_12000", pa["total"] == "12000.00", pa["total"])
r = cobrar(pid, [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 20000}])
check("cobro_200", r.status_code == 200, r.text[:200])
body = r.json()
check("cambio_8000", body["pagos"][0]["cambio"] == "8000.00", body["pagos"][0]["cambio"])
check("pagado_true", body["pagado"] is True)
check("estado_sigue_NUEVO", httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("mesero")).json()["estado"] == "NUEVO")
check("enviar_cocina_200", httpx.post(f"{BASE}/pedidos/{pid}/enviar-a-cocina", headers=hdr("mesero")).status_code == 200)
d = detalle_id(httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("caja")).json(), 1)
check("aceptar_200", httpx.post(f"{BASE}/cocina/detalles/{d}/aceptar", headers=hdr("cocina")).status_code == 200)
cola = httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()
check("pagado_adelantado_sigue_en_cola", any(t["pedido_id"] == pid for t in cola))
check("listo_200", httpx.post(f"{BASE}/cocina/detalles/{d}/listo", headers=hdr("cocina")).status_code == 200)
check("estado_PAGADO_al_terminar", httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("mesero")).json()["estado"] == "PAGADO")
cola2 = httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()
check("sale_de_cola", not any(t["pedido_id"] == pid for t in cola2))
check("re_cobro_409", cobrar(pid, [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 12000}]).status_code == 409)

print("== 3. Validaciones de cobro ==")
p = crear_pedido("DOMICILIO", [{"producto_id": 5, "cantidad": 1}]).json()
check("suma_no_cuadra_422", cobrar(p["id"], [{"metodo": "TARJETA", "monto": 2000}]).status_code == 422)
check("efectivo_sin_recibido_422", cobrar(p["id"], [{"metodo": "EFECTIVO", "monto": 3000}]).status_code == 422)
check("efectivo_insuficiente_422", cobrar(p["id"], [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 1000}]).status_code == 422)
check("monto_cero_422", cobrar(p["id"], [{"metodo": "TARJETA", "monto": 0}]).status_code == 422)

print("== 4. Pago mixto tarjeta + efectivo ==")
p = crear_pedido("DOMICILIO", [{"producto_id": 3, "cantidad": 2}]).json()
pid = p["id"]
r = cobrar(pid, [
    {"metodo": "TARJETA", "monto": 10000},
    {"metodo": "EFECTIVO", "monto": 6000, "recibido": 6000},
])
check("mixto_200", r.status_code == 200, r.text[:200])
check("dos_pagos", len(r.json()["pagos"]) == 2)
check("cambio_cero", r.json()["pagos"][1]["cambio"] == "0.00")
check("mixto_pagado", r.json()["pagado"] is True)

print("== 5. VALE (pagaré) ==")
p = crear_pedido("DOMICILIO", [{"producto_id": 2, "cantidad": 1}]).json()
pid = p["id"]
r = cobrar(pid, [{"metodo": "VALE", "monto": 15000, "vale_cliente_nombre": "Juan Perez", "vale_cliente_cedula": "123456", "vale_cliente_telefono": "3000000000"}])
check("vale_200", r.status_code == 200, r.text[:200])
evales = r.json()["vales"]
check("vale_creado_pendiente", len(evales) == 1 and evales[0]["estado"] == "PENDIENTE")
val_id = evales[0]["id"]
check("vale_sin_nombre_422", cobrar(crear_pedido("DOMICILIO", [{"producto_id": 5, "cantidad": 1}]).json()["id"], [{"metodo": "VALE", "monto": 3000}]).status_code == 422)
lista = httpx.get(f"{BASE}/caja/vales?estado=PENDIENTE", headers=hdr("caja")).json()
check("vale_en_lista", any(v["id"] == val_id for v in lista))
r = httpx.post(f"{BASE}/caja/vales/{val_id}/cobrar", headers=hdr("caja"), json={"descripcion": "Pago en efectivo"})
check("cobrar_vale_200", r.status_code == 200, r.text[:200])
check("vale_cobrado", r.json()["estado"] == "COBRADO")
check("vale_re_cobro_409", httpx.post(f"{BASE}/caja/vales/{val_id}/cobrar", headers=hdr("caja"), json={}).status_code == 409)
movs = httpx.get(f"{BASE}/caja/movimientos?categoria=COBRO_VALE", headers=hdr("caja")).json()
check("mov_cobro_vale", any(m["vale_id"] == val_id and m["tipo"] == "ENTRADA" for m in movs))

print("== 6. DiDi ==")
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "DIDI", "lineas": [{"producto_id": 4, "cantidad": 1}]})
check("didi_sin_orden_422", r.status_code == 422)
p = crear_pedido("DIDI", [{"producto_id": 4, "cantidad": 1}], didi_orden_id="DD-777").json()
pid = p["id"]
r = cobrar(pid, [{"metodo": "DIDI_TARJETA", "monto": 6000}])
check("didi_tarjeta_200", r.status_code == 200, r.text[:200])
check("didi_orden_heredada", r.json()["pagos"][0]["didi_orden_id"] == "DD-777")
p2 = crear_pedido("DIDI", [{"producto_id": 5, "cantidad": 1}], didi_orden_id="DD-888").json()
r = cobrar(p2["id"], [{"metodo": "DIDI_EFECTIVO", "monto": 3000}])
check("didi_efectivo_200", r.status_code == 200, r.text[:200])
p3 = crear_pedido("DOMICILIO", [{"producto_id": 5, "cantidad": 1}]).json()
check("didi_sin_orden_422_2", cobrar(p3["id"], [{"metodo": "DIDI_TARJETA", "monto": 3000}]).status_code == 422)

print("== 7. Devolución de pago ==")
# creamos un pedido cobrado con tarjeta y devolvemos ese pago
mixto = cobrar(crear_pedido("DOMICILIO", [{"producto_id": 3, "cantidad": 1}]).json()["id"], [{"metodo": "TARJETA", "monto": 8000}])
mid = mixto.json()["pedido_id"]
pago_id = mixto.json()["pagos"][0]["id"]
r = httpx.post(f"{BASE}/caja/pagos/{pago_id}/devolver", headers=hdr("caja"), json={"motivo": "cliente cancela"})
check("devolucion_200", r.status_code == 200, r.text[:200])
check("pago_devuelto", r.json()["estado"] == "DEVUELTO")
check("motivo_guardado", r.json()["motivo_devolucion"] == "cliente cancela")
check("pedido_desmarcado", httpx.get(f"{BASE}/pedidos/{mid}", headers=hdr("caja")).json()["pagado"] is False)
check("devolucion_sin_motivo_422", httpx.post(f"{BASE}/caja/pagos/{pago_id}/devolver", headers=hdr("caja"), json={"motivo": "x"}).status_code == 422)
movs = httpx.get(f"{BASE}/caja/movimientos?categoria=DEVOLUCION", headers=hdr("caja")).json()
check("mov_devolucion", any(m["tipo"] == "SALIDA" and m["valor"] == "8000.00" for m in movs))

print("== 8. Mesa: pago al final libera la mesa ==")
p = crear_pedido("MESA", [{"producto_id": 6, "cantidad": 1}], mesa_id=5).json()
pid = p["id"]
m5 = httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("caja")).json()
check("mesa5_ocupada", next(m["estado"] for m in m5 if m["numero"] == 5) == "OCUPADA")
httpx.post(f"{BASE}/pedidos/{pid}/enviar-a-cocina", headers=hdr("mesero"))
d = detalle_id(httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("caja")).json(), 6)
httpx.post(f"{BASE}/cocina/detalles/{d}/aceptar", headers=hdr("cocina"))
httpx.post(f"{BASE}/cocina/detalles/{d}/listo", headers=hdr("cocina"))
check("mesa_finalizado", httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("caja")).json()["estado"] == "FINALIZADO")
r = cobrar(pid, [{"metodo": "EFECTIVO", "monto": 2000, "recibido": 2000}])
check("mesa_cobro_200", r.status_code == 200, r.text[:200])
check("mesa_pagado", r.json()["pagado"] is True)
check("mesa_PAGADO", httpx.get(f"{BASE}/pedidos/{pid}", headers=hdr("caja")).json()["estado"] == "PAGADO")
m5b = httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("caja")).json()
check("mesa5_liberada", next(m["estado"] for m in m5b if m["numero"] == 5) == "DISPONIBLE")
check("ronda_post_cobro_409", httpx.post(f"{BASE}/pedidos/{pid}/rondas", headers=hdr("mesero"), json={"ronda": 2, "lineas": [{"producto_id": 5, "cantidad": 1}]}).status_code == 409)

print()
print(f"RESULTADO: {PASS} PASS / {FAIL} FAIL")
if FALLOS:
    print("FALLOS:")
    for f in FALLOS:
        print("  -", f)
    sys.exit(1)
