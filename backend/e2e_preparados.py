"""Harness E2E Fase 14: Cancelación de pedidos y bolsa de preparados reusables.

Prueba exhaustiva de todas las reglas del Documento Maestro (Sección 6.1 y 8):
1. Permisos por rol (cancelar y descartar solo admin; mesero/caja ven y asignan).
2. Cancelación No Pagado + No Producido (libera mesa, sin tocar inventario, sin preparados).
3. Cancelación No Pagado + Producido (insumos quedan gastados, producto pasa a PREPARADO DISPONIBLE).
4. Cancelación Pagado + No Producido (devolución SALIDA en caja, sin tocar inventario).
5. Cancelación Pagado + Producido (devolución SALIDA en caja + pasa a PREPARADO).
6. Reventa de preparado por mesero (ticket con nota, cocina NO descuenta inventario por 2da vez).
7. Choque de meseros (concurrencia: lock atómico, segundo mesero recibe 409).
8. Cancelación en cascada de preparado reutilizado (Regla 5: vuelve a DISPONIBLE).
9. Descarte de preparado por el admin (control de desperdicio/merma).
10. Fotograma de cierre de turno con preparados_reutilizados y preparados_descartados.
11. Historial inmutable de auditoría (nada se cancela ni descarta sin registro).
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import httpx

from app.database import SessionLocal
from app.models import (
    Cierre,
    DetallePedido,
    HistorialAccion,
    Ingrediente,
    Mesa,
    MovimientoCaja,
    MovimientoInventario,
    Pago,
    Pedido,
    Preparado,
    Producto,
)

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


STOCK_SEGURO = {1: 1000, 2: 100000, 3: 1000, 4: 500, 5: 100000, 6: 100000, 7: 1000, 8: 100000, 9: 1000}


def asegurar_stock():
    for ing_id, valor in STOCK_SEGURO.items():
        httpx.put(f"{BASE}/ingredientes/{ing_id}", headers=hdr("admin"), json={"stock_actual": valor})


asegurar_stock()

# Idempotencia: liberar mesas para pruebas limpias
db_init = SessionLocal()
for m in db_init.query(Mesa).all():
    for p in db_init.query(Pedido).filter(Pedido.mesa_id == m.id, Pedido.estado.notin_(("PAGADO", "CERRADO", "CANCELADO"))).all():
        p.estado = "CANCELADO"
    m.estado = "DISPONIBLE"
db_init.commit()
db_init.close()

# Asegurar turno de caja abierto
r_t = httpx.get(f"{BASE}/caja/turno", headers=hdr("caja"))
if r_t.status_code != 200 or r_t.json() is None:
    httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 200000})

# ============================================================
print("== 1. Permisos por rol (Seguridad) ==")
# ============================================================
# Crear pedido de prueba para permisos
p_perm = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("mesero"),
    json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 1, "cantidad": 1}]},
).json()
pid_perm = p_perm["id"]

# Mesero, caja y cocina no pueden cancelar pedidos
check("mesero_cancelar_403", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("mesero"), json={"motivo": "prueba mesero"}).status_code == 403)
check("caja_cancelar_403", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("caja"), json={"motivo": "prueba caja"}).status_code == 403)
check("cocina_cancelar_403", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("cocina"), json={"motivo": "prueba cocina"}).status_code == 403)
check("anonimo_cancelar_401", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", json={"motivo": "anonimo"}).status_code == 401)

# Validaciones de cancelación
check("motivo_corto_422", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("admin"), json={"motivo": "no"}).status_code == 422)
check("pedido_inexistente_404", httpx.post(f"{BASE}/pedidos/999999/cancelar", headers=hdr("admin"), json={"motivo": "pedido no existe"}).status_code == 404)

# Admin sí puede cancelar
r_canc = httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("admin"), json={"motivo": "Cancelación de prueba de permisos"})
check("admin_cancelar_200", r_canc.status_code == 200, r_canc.text)
check("doble_cancelar_409", httpx.post(f"{BASE}/pedidos/{pid_perm}/cancelar", headers=hdr("admin"), json={"motivo": "otra vez"}).status_code == 409)


def get_stock(ing_id):
    ings = httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).json()
    return d(next(i for i in ings if i["id"] == ing_id)["stock_actual"])


# ============================================================
print("== 2. Escenario A: No Pagado + No Producido ==")
# ============================================================
# Pedido en Mesa 7 (sin pagar, no enviado a cocina)
p_a = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("mesero"),
    json={"canal": "MESA", "mesa_id": 7, "lineas": [{"producto_id": 1, "cantidad": 1}]},
).json()
pid_a = p_a["id"]

# Mesa 7 debe estar OCUPADA
m7 = httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("mesero")).json()
mesa7 = next(m for m in m7 if m["id"] == 7)
check("mesa7_ocupada", mesa7["estado"] == "OCUPADA")

# Consultar stock de carne (ingrediente 2) antes
ing2_antes = get_stock(2)

# Cancelar por admin
r_canc_a = httpx.post(f"{BASE}/pedidos/{pid_a}/cancelar", headers=hdr("admin"), json={"motivo": "Cliente se retira de la mesa antes de ordenar a cocina"})
check("canc_a_200", r_canc_a.status_code == 200, r_canc_a.text)
check("canc_a_estado", r_canc_a.json()["estado"] == "CANCELADO")
check("canc_a_motivo", r_canc_a.json()["motivo_cancelacion"] == "Cliente se retira de la mesa antes de ordenar a cocina")

# Mesa 7 debe quedar LIBERADA (DISPONIBLE)
m7_post = httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("mesero")).json()
mesa7_post = next(m for m in m7_post if m["id"] == 7)
check("mesa7_liberada", mesa7_post["estado"] == "DISPONIBLE")

# Stock no debe haber cambiado en absoluto
ing2_desp = get_stock(2)
check("stock_intacto_no_producido", d(ing2_antes) == d(ing2_desp))

# No debe haber generado ningún preparado
db = SessionLocal()
preps_a = db.query(Preparado).filter(Preparado.pedido_origen_id == pid_a).all()
check("sin_preparados_no_producido", len(preps_a) == 0)
db.close()


# ============================================================
print("== 3. Escenario B: No Pagado + Producido (Bolsa de Preparados) ==")
# ============================================================
# Pedido en Mesa 8, enviado a cocina y aceptado por cocina (producido)
p_b = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("mesero"),
    json={
        "canal": "MESA",
        "mesa_id": 8,
        "lineas": [{"producto_id": 1, "cantidad": 1, "variacion_snapshot": {"sin_tomate": True}}],
    },
).json()
pid_b = p_b["id"]
httpx.post(f"{BASE}/pedidos/{pid_b}/enviar-a-cocina", headers=hdr("mesero"))

cola = httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()
ticket_b = next(t for t in cola if t["pedido_id"] == pid_b)
det_id_b = ticket_b["rondas"][0]["detalles"][0]["detalle_id"]

ing2_antes_prod = get_stock(2)

# Cocina ACEPTA => descuenta inventario real
r_acep = httpx.post(f"{BASE}/cocina/detalles/{det_id_b}/aceptar", headers=hdr("cocina"))
check("cocina_acepta_b", r_acep.status_code == 200)

ing2_desp_prod = get_stock(2)
check("stock_descontado_al_producir", ing2_desp_prod < ing2_antes_prod)

# Cliente cancela antes de pagar (ej. se fue)
r_canc_b = httpx.post(f"{BASE}/pedidos/{pid_b}/cancelar", headers=hdr("admin"), json={"motivo": "Cliente se fue sin esperar la comida"})
check("canc_b_200", r_canc_b.status_code == 200)

# Mesa 8 liberada
m8_post = httpx.get(f"{BASE}/pedidos/mesas", headers=hdr("mesero")).json()
mesa8_post = next(m for m in m8_post if m["id"] == 8)
check("mesa8_liberada", mesa8_post["estado"] == "DISPONIBLE")

# Insumos SE MANTIENEN DESCONTADOS (no se reponen mágicamente porque ya se cocinaron)
ing2_post_canc = get_stock(2)
check("stock_mantiene_descontado", ing2_post_canc == ing2_desp_prod)

# Debe haber entrado 1 registro a PREPARADOS con estado DISPONIBLE
r_preps = httpx.get(f"{BASE}/preparados?estado=DISPONIBLE", headers=hdr("mesero")).json()
prep_b = next((p for p in r_preps if p["pedido_origen_id"] == pid_b), None)
check("preparado_creado_en_bolsa", prep_b is not None)
check("preparado_variacion_guardada", prep_b["variacion_snapshot"] == {"sin_tomate": True} if prep_b else False)
check("preparado_estado_disponible", prep_b["estado"] == "DISPONIBLE" if prep_b else False)
prep_b_id = prep_b["id"] if prep_b else None


# ============================================================
print("== 4. Escenario C: Pagado + No Producido (Devolución de dinero) ==")
# ============================================================
# Pedido Mostrador cobrado por adelantado
p_c = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("caja"),
    json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 1, "cantidad": 1}]},
).json()
pid_c = p_c["id"]

# Cobro adelantado
r_cob = httpx.post(
    f"{BASE}/caja/pedidos/{pid_c}/cobrar",
    headers=hdr("caja"),
    json={"pagos": [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 12000}]},
)
check("cobro_c_adelantado_200", r_cob.status_code == 200)

# Cancelar por admin antes de cocinar
r_canc_c = httpx.post(
    f"{BASE}/pedidos/{pid_c}/cancelar",
    headers=hdr("admin"),
    json={"motivo": "Cliente en mostrador desiste antes de que empiece la cocina"},
)
check("canc_c_200", r_canc_c.status_code == 200)

# Verificar devolución de pago y movimiento de caja SALIDA
pagos_c = httpx.get(f"{BASE}/caja/pedidos/{pid_c}/pagos", headers=hdr("caja")).json()
check("pago_c_marcado_devuelto", pagos_c[0]["estado"] == "DEVUELTO")

movs_c = httpx.get(f"{BASE}/caja/movimientos?categoria=DEVOLUCION", headers=hdr("caja")).json()
mov_c = next((m for m in movs_c if m["pedido_id"] == pid_c), None)
check("movimiento_caja_salida_devolucion", mov_c is not None and mov_c["tipo"] == "SALIDA" and d(mov_c["valor"]) == 12000)

# No debe generar preparado
db = SessionLocal()
check("c_sin_preparado", db.query(Preparado).filter(Preparado.pedido_origen_id == pid_c).first() is None)
db.close()


# ============================================================
print("== 5. Escenario D: Pagado + Producido ==")
# ============================================================
# Pedido Mostrador cobrado adelantado y producido
p_d = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("caja"),
    json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 1, "cantidad": 1}]},
).json()
pid_d = p_d["id"]

httpx.post(f"{BASE}/caja/pedidos/{pid_d}/cobrar", headers=hdr("caja"), json={"pagos": [{"metodo": "EFECTIVO", "monto": 12000, "recibido": 12000}]})
httpx.post(f"{BASE}/pedidos/{pid_d}/enviar-a-cocina", headers=hdr("caja"))

cola = httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()
tk_d = next(t for t in cola if t["pedido_id"] == pid_d)
det_d = tk_d["rondas"][0]["detalles"][0]["detalle_id"]
httpx.post(f"{BASE}/cocina/detalles/{det_d}/aceptar", headers=hdr("cocina"))

# Cancelar por admin
r_canc_d = httpx.post(f"{BASE}/pedidos/{pid_d}/cancelar", headers=hdr("admin"), json={"motivo": "Devolución mostrador con producto ya cocinado"})
check("canc_d_200", r_canc_d.status_code == 200)

# Dinero devuelto
pagos_d = httpx.get(f"{BASE}/caja/pedidos/{pid_d}/pagos", headers=hdr("caja")).json()
check("pago_d_devuelto", pagos_d[0]["estado"] == "DEVUELTO")

# Preparado generado
db = SessionLocal()
prep_d = db.query(Preparado).filter(Preparado.pedido_origen_id == pid_d, Preparado.estado == "DISPONIBLE").first()
check("prep_d_generado", prep_d is not None)
prep_d_id = prep_d.id if prep_d else None
db.close()


# ============================================================
print("== 6. Escenario E: Reventa de Preparado (Mesero reutiliza producto) ==")
# ============================================================
# El mesero ve sugerencias y reutiliza el preparado creado en el escenario B
check("prep_b_valido", prep_b_id is not None)
sug = httpx.get(f"{BASE}/preparados/sugerir?producto_id=1", headers=hdr("mesero")).json()
check("sugerencia_coincidencia", sug["coincidencia"] is True)

# Mesero crea pedido nuevo en Mesa 3
p_e = httpx.post(
    f"{BASE}/pedidos",
    headers=hdr("mesero"),
    json={"canal": "MESA", "mesa_id": 3, "lineas": [{"producto_id": 5, "cantidad": 1}]},  # Bebida (Gaseosa $3000)
).json()
pid_e = p_e["id"]

# Mesero asigna el preparado existente al pedido
r_asig = httpx.post(f"{BASE}/preparados/{prep_b_id}/asignar", headers=hdr("mesero"), json={"pedido_id": pid_e})
check("asignar_preparado_200", r_asig.status_code == 200, r_asig.text)
check("preparado_marcado_asignado", r_asig.json()["estado"] == "ASIGNADO")

# El pedido refleja la línea con precio normal
p_e_updated = httpx.get(f"{BASE}/pedidos/{pid_e}", headers=hdr("caja")).json()
check("pedido_e_total_actualizado", d(p_e_updated["total"]) == d(12000 + 3000))
check("nota_interna_usar_preparado", "USAR PREPARADO" in p_e_updated["nota_interna"])

# Enviar a cocina
httpx.post(f"{BASE}/pedidos/{pid_e}/enviar-a-cocina", headers=hdr("mesero"))

# Cocina acepta la línea de la hamburguesa reutilizada
cola_e = httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).json()
tk_e = next(t for t in cola_e if t["pedido_id"] == pid_e)
det_prep_line = next(d for r in tk_e["rondas"] for d in r["detalles"] if d["producto_id"] == 1)

ing2_antes_prep = get_stock(2)

# Cocina ACEPTA el preparado
r_acep_prep = httpx.post(f"{BASE}/cocina/detalles/{det_prep_line['detalle_id']}/aceptar", headers=hdr("cocina"))
check("cocina_acepta_preparado_200", r_acep_prep.status_code == 200)

# REGLA DE ORO: NO SE DESCUENTA INVENTARIO POR SEGUNDA VEZ
ing2_desp_prep = get_stock(2)
check("inventario_no_descuenta_preparado", ing2_desp_prep == ing2_antes_prep)

# Cocina marca listo y caja cobra normalmente
httpx.post(f"{BASE}/cocina/detalles/{det_prep_line['detalle_id']}/listo", headers=hdr("cocina"))
r_cob_e = httpx.post(
    f"{BASE}/caja/pedidos/{pid_e}/cobrar",
    headers=hdr("caja"),
    json={"pagos": [{"metodo": "EFECTIVO", "monto": 15000, "recibido": 15000}]},
)
check("cobro_reventa_exitoso_200", r_cob_e.status_code == 200)


# ============================================================
print("== 7. Escenario F: Choque de meseros (Concurrencia) ==")
# ============================================================
# Usamos prep_d_id que está DISPONIBLE
check("prep_d_disponible", prep_d_id is not None)

# Crear dos pedidos para competir
p_f1 = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 4, "cantidad": 1}]}).json()
p_f2 = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 4, "cantidad": 1}]}).json()

def asignar_prep(pid):
    return httpx.post(f"{BASE}/preparados/{prep_d_id}/asignar", headers=hdr("mesero"), json={"pedido_id": pid})

with ThreadPoolExecutor(max_workers=2) as pool:
    fut1 = pool.submit(asignar_prep, p_f1["id"])
    fut2 = pool.submit(asignar_prep, p_f2["id"])
    res1 = fut1.result()
    res2 = fut2.result()

codigos = {res1.status_code, res2.status_code}
check("concurrencia_un_200_un_409", codigos == {200, 409}, f"codigos={codigos}")


# ============================================================
print("== 8. Escenario G: Cancelación en cascada (Regla 5) ==")
# ============================================================
# El pedido que ganó la asignación en el paso anterior se cancela
pid_ganador = p_f1["id"] if res1.status_code == 200 else p_f2["id"]

# Admin cancela el pedido que tenía el preparado asignado
r_canc_g = httpx.post(f"{BASE}/pedidos/{pid_ganador}/cancelar", headers=hdr("admin"), json={"motivo": "Cancelación de pedido con preparado"})
check("canc_ganador_200", r_canc_g.status_code == 200)

# REGLA 5: El preparado vuelve a estar DISPONIBLE en la bolsa
db = SessionLocal()
prep_d_reloaded = db.get(Preparado, prep_d_id)
check("regla5_vuelve_a_disponible", prep_d_reloaded.estado == "DISPONIBLE" and prep_d_reloaded.pedido_nuevo_id is None)
db.close()


# ============================================================
print("== 9. Escenario H: Descarte de preparado por el Admin (Merma) ==")
# ============================================================
# Mesero intenta descartar -> 403
check("mesero_descartar_403", httpx.post(f"{BASE}/preparados/{prep_d_id}/descartar", headers=hdr("mesero"), json={"motivo": "frio"}).status_code == 403)

# Admin descarta
r_desc = httpx.post(
    f"{BASE}/preparados/{prep_d_id}/descartar",
    headers=hdr("admin"),
    json={"motivo": "Producto frío tras superar 45 minutos en espera"},
)
check("admin_descartar_200", r_desc.status_code == 200, r_desc.text)
check("estado_descartado", r_desc.json()["estado"] == "DESCARTADO")

# Intentar re-asignar un descartado -> 409
check("asignar_descartado_409", httpx.post(f"{BASE}/preparados/{prep_d_id}/asignar", headers=hdr("mesero"), json={"pedido_id": p_f1["id"]}).status_code == 409)

# Intentar re-descartar -> 409
check("doble_descartar_409", httpx.post(f"{BASE}/preparados/{prep_d_id}/descartar", headers=hdr("admin"), json={"motivo": "otra vez"}).status_code == 409)


# ============================================================
print("== 10. Escenario I: Cierre de turno con Preparados ==")
# ============================================================
# Al cerrar el turno de caja, el fotograma debe haber registrado los preparados
# reutilizados y descartados durante el turno
r_cierre = httpx.post(f"{BASE}/caja/turno/cerrar", headers=hdr("caja"), json={"notas": "Cierre con auditoría de preparados"})
check("cerrar_turno_200", r_cierre.status_code == 200, r_cierre.text)

cierre_data = r_cierre.json()
check("cierre_preparados_reutilizados", cierre_data["preparados_reutilizados"] >= 1, f"reutilizados={cierre_data['preparados_reutilizados']}")
check("cierre_preparados_descartados", cierre_data["preparados_descartados"] >= 1, f"descartados={cierre_data['preparados_descartados']}")


# ============================================================
print("== 11. Escenario J: Inmutabilidad e Historial ==")
# ============================================================
db = SessionLocal()
hist_canc = db.query(HistorialAccion).filter(HistorialAccion.accion == "CANCELAR_PEDIDO").all()
check("historial_cancelar_registrado", len(hist_canc) >= 4)

hist_asig = db.query(HistorialAccion).filter(HistorialAccion.accion == "ASIGNAR_PREPARADO").all()
check("historial_asignar_registrado", len(hist_asig) >= 1)

hist_desc = db.query(HistorialAccion).filter(HistorialAccion.accion == "DESCARTAR_PREPARADO").all()
check("historial_descartar_registrado", len(hist_desc) >= 1)
db.close()


# Abrir nuevo turno limpio para dejar el sistema listo
httpx.post(f"{BASE}/caja/turno/abrir", headers=hdr("caja"), json={"monto_inicial": 50000})

print("\n" + "=" * 50)
print(f"RESULTADO FASE 14 (PREPARADOS): {PASS} PASS / {FAIL} FAIL")
print("=" * 50)

if FALLOS:
    print(f"FALLOS ({len(FALLOS)}):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
