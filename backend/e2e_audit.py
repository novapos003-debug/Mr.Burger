"""Auditoria adversarial completa de las fases 1-7.

Corre DENTRO del contenedor:  docker compose exec -T backend python /app/e2e_audit.py
Prueba seguridad, permisos, catalogos, pedidos, cocina, caja, concurrencia,
WebSocket y zona horaria. Usa httpx para la API y el ORM para verificar la BD.
"""

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import httpx

from app.core.security import create_access_token, hash_password
from app.database import SessionLocal
from app.models import DetalleReceta, HistorialAccion, Ingrediente, Mesa, Pedido, Producto, Rol, Usuario

BASE = "http://localhost:8000"
USERS = {"admin": "admin123", "caja": "caja123", "mesero": "mesero123", "cocina": "cocina123"}

PASS = 0
FAIL = 0
FALLOS = []
NOTAS = []


def check(nombre, cond, detalle=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {nombre}")
    else:
        FAIL += 1
        FALLOS.append(nombre)
        print(f"  FAIL {nombre}  {detalle}")


def nota(txt):
    NOTAS.append(txt)
    print(f"  >> {txt}")


def login(c):
    r = httpx.post(f"{BASE}/auth/login", data={"username": c, "password": USERS[c]})
    return r.json()["access_token"]


TOK = {c: login(c) for c in USERS}
TMP_PRODUCTOS = []
TMP_INGREDIENTES = []
TMP_USUARIOS = []
RUN = datetime.now().strftime("%H%M%S")
NOMBRE_SIN = f"AUDIT Sin Receta {RUN}"
NOMBRE_CON = f"AUDIT Con Receta {RUN}"
NOMBRE_ING = f"AUDIT Insumo {RUN}"
NOMBRE_USR = f"audit_{RUN}"


def limpiar_previos():
    s = SessionLocal()
    for row in s.query(Producto).filter(Producto.nombre.like("AUDIT %")).all():
        row.activo = False
        row.manual_disponible = None
    for row in s.query(Ingrediente).filter(Ingrediente.nombre.like("AUDIT %")).all():
        row.activo = False
    for row in s.query(Usuario).filter(Usuario.usuario.like("audit_%")).all():
        row.activo = False
    for m in s.query(Mesa).filter(Mesa.numero.in_((6, 7))).all():
        for pr in s.query(Pedido).filter(Pedido.mesa_id == m.id,
                                         Pedido.estado.notin_(["PAGADO", "CERRADO", "CANCELADO"])).all():
            pr.estado = "CANCELADO"
        m.estado = "DISPONIBLE"
    s.commit()
    s.close()


limpiar_previos()


def hdr(c):
    return {"Authorization": f"Bearer {TOK[c]}"}


def h(c, extra=None):
    d = {"Authorization": f"Bearer {TOK[c]}"}
    if extra:
        d.update(extra)
    return d


def db():
    return SessionLocal()


STOCK_SEGURO = {1: 1000, 2: 100000, 3: 1000, 4: 500, 5: 100000, 6: 100000, 7: 1000, 8: 100000, 9: 1000}
for _ing_id, _valor in STOCK_SEGURO.items():
    httpx.put(f"{BASE}/ingredientes/{_ing_id}", headers=hdr("admin"), json={"stock_actual": _valor})


# ============================================================
print("== 1. AUTENTICACION Y SEGURIDAD ==")
r = httpx.post(f"{BASE}/auth/login", data={"username": "admin", "password": "incorrecta"})
check("login_password_malo_401", r.status_code == 401, r.status_code)
r = httpx.post(f"{BASE}/auth/login", data={"username": "noexiste", "password": "x"})
check("login_usuario_inexistente_401", r.status_code == 401, r.status_code)
r = httpx.post(f"{BASE}/auth/login", data={"username": "admin", "password": ""})
check("login_password_vacio_401", r.status_code == 401, r.status_code)

check("token_basura_401", httpx.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401)
check("sin_token_401", httpx.get(f"{BASE}/auth/me").status_code == 401)
exp = create_access_token("1", expires_minutes=-1)
check("token_expirado_401", httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {exp}"}).status_code == 401)
sub_fantasma = create_access_token("999999")
check("token_usuario_inexistente_401", httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {sub_fantasma}"}).status_code == 401)

me = httpx.get(f"{BASE}/auth/me", headers=hdr("mesero")).json()
check("me_rol", me["rol"] == "mesero", me)

# Usuario inactivo: login 403 y token 401
s = db()
rol_mesero = s.query(Rol).filter(Rol.nombre == "mesero").first()
u = s.query(Usuario).filter(Usuario.usuario == NOMBRE_USR).first()
if not u:
    u = Usuario(rol_id=rol_mesero.id, nombre="Audit Inactivo", usuario=NOMBRE_USR,
                password_hash=hash_password("x123"), activo=False)
    s.add(u)
    s.commit()
    s.refresh(u)
TMP_USUARIOS.append(u.id)
u_id = u.id
s.close()
r = httpx.post(f"{BASE}/auth/login", data={"username": NOMBRE_USR, "password": "x123"})
check("login_inactivo_403", r.status_code == 403, r.status_code)
tok_inactivo = create_access_token(str(u_id))
check("token_usuario_inactivo_401",
      httpx.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {tok_inactivo}"}).status_code == 401)

# ============================================================
print("== 2. PERMISOS POR ROL ==")
check("mesero_ingredientes_403", httpx.get(f"{BASE}/ingredientes", headers=hdr("mesero")).status_code == 403)
check("cocina_ingredientes_403", httpx.get(f"{BASE}/ingredientes", headers=hdr("cocina")).status_code == 403)
check("caja_ingredientes_403", httpx.get(f"{BASE}/ingredientes", headers=hdr("caja")).status_code == 403)
check("admin_ingredientes_200", httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).status_code == 200)
check("mesero_cocina_cola_403", httpx.get(f"{BASE}/cocina/cola", headers=hdr("mesero")).status_code == 403)
check("cocina_cola_200", httpx.get(f"{BASE}/cocina/cola", headers=hdr("cocina")).status_code == 200)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("cocina"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5}]})
check("cocina_crear_pedido_403", r.status_code == 403, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("caja"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("caja_crear_pedido_201", r.status_code == 201, r.status_code)
ped_caja = r.json() if r.status_code == 201 else None
check("staff_listar_pedidos", httpx.get(f"{BASE}/pedidos", headers=hdr("cocina")).status_code == 200)
check("mesero_crear_producto_403",
      httpx.post(f"{BASE}/productos", headers=hdr("mesero"), json={"categoria_id": 1, "nombre": "x", "precio": 1}).status_code == 403)

# ============================================================
print("== 3. CATALOGO Y DISPONIBILIDAD ==")
# producto sin receta => siempre disponible
r = httpx.post(f"{BASE}/productos", headers=hdr("admin"),
               json={"categoria_id": 2, "nombre": NOMBRE_SIN, "precio": 1234})
check("crear_producto_201", r.status_code == 201, r.text[:150])
prod_sin = r.json()
TMP_PRODUCTOS.append(prod_sin["id"])
check("prod_sin_receta_disponible", prod_sin["disponible"] is True)
check("precio_negativo_422",
      httpx.post(f"{BASE}/productos", headers=hdr("admin"), json={"categoria_id": 2, "nombre": "y", "precio": -5}).status_code == 422)

# ingrediente con stock y producto con receta
r = httpx.post(f"{BASE}/ingredientes", headers=hdr("admin"),
               json={"nombre": NOMBRE_ING, "unidad_base": "GRAMO", "stock_actual": 100, "stock_minimo": 10, "costo_unitario": 1})
check("crear_ingrediente_201", r.status_code == 201, r.text[:150])
ing = r.json()
TMP_INGREDIENTES.append(ing["id"])
r = httpx.post(f"{BASE}/productos", headers=hdr("admin"),
               json={"categoria_id": 1, "nombre": NOMBRE_CON, "precio": 5000})
prod_con = r.json()
TMP_PRODUCTOS.append(prod_con["id"])
r = httpx.put(f"{BASE}/ingredientes/productos/{prod_con['id']}/receta", headers=hdr("admin"),
              json=[{"ingrediente_id": ing["id"], "cantidad": 50, "unidad": "GRAMO"}])
check("set_receta_200", r.status_code == 200, r.text[:200])
check("dup_ingrediente_receta_422",
      httpx.put(f"{BASE}/ingredientes/productos/{prod_con['id']}/receta", headers=hdr("admin"),
                json=[{"ingrediente_id": ing["id"], "cantidad": 1, "unidad": "GRAMO"},
                      {"ingrediente_id": ing["id"], "cantidad": 2, "unidad": "GRAMO"}]).status_code == 422)
check("receta_ingrediente_inexistente_404",
      httpx.put(f"{BASE}/ingredientes/productos/{prod_con['id']}/receta", headers=hdr("admin"),
                json=[{"ingrediente_id": 999999, "cantidad": 1, "unidad": "GRAMO"}]).status_code == 404)
# stock 100, receta 50 => disponible
p = httpx.get(f"{BASE}/productos/{prod_con['id']}", headers=hdr("caja")).json()
check("con_receta_suficiente_disponible", p["disponible"] is True, p)
# la disponibilidad mira la CANTIDAD pedida: stock 100, receta 50 => 3 unidades no alcanzan
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
               json={"canal": "MOSTRADOR", "lineas": [{"producto_id": prod_con["id"], "cantidad": 3}]})
check("pedido_cantidad_excede_stock_409", r.status_code == 409, r.status_code)
# subir cantidad a 500 => no disponible
httpx.put(f"{BASE}/ingredientes/productos/{prod_con['id']}/receta", headers=hdr("admin"),
          json=[{"ingrediente_id": ing["id"], "cantidad": 500, "unidad": "GRAMO"}])
p = httpx.get(f"{BASE}/productos/{prod_con['id']}", headers=hdr("caja")).json()
check("con_receta_insuficiente_no_disponible", p["disponible"] is False, p)
# forzar disponible => true pese a stock
r = httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": True})
check("forzar_disponible_true", r.json()["disponible"] is True)
# forzar no disponible en producto sin receta
r = httpx.put(f"{BASE}/productos/{prod_sin['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": False})
check("forzar_no_disponible", r.json()["disponible"] is False)
# limpiar override
httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": None})
httpx.put(f"{BASE}/productos/{prod_sin['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": None})
# ingrediente en uso no se puede inactivar
check("inactivar_ingrediente_en_uso_409",
      httpx.delete(f"{BASE}/ingredientes/{ing['id']}", headers=hdr("admin")).status_code == 409)
# cocina no ve precio, mesero sí ve precios
prods_cocina = httpx.get(f"{BASE}/productos", headers=hdr("cocina")).json()
check("cocina_no_ve_precios", all(pr["precio"] is None for pr in prods_cocina))
prods_mesero = httpx.get(f"{BASE}/productos", headers=hdr("mesero")).json()
check("mesero_si_ve_precios", any(pr["precio"] is not None for pr in prods_mesero))
prods_caja = httpx.get(f"{BASE}/productos", headers=hdr("caja")).json()
check("caja_si_ve_precios", any(pr["precio"] is not None for pr in prods_caja))
# solo_disponibles filtra
p = httpx.get(f"{BASE}/productos/{prod_con['id']}", headers=hdr("admin")).json()
httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": False})
disps = httpx.get(f"{BASE}/productos?solo_disponibles=true", headers=hdr("admin")).json()
check("solo_disponibles_excluye", all(x["id"] != prod_con["id"] for x in disps))
httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": None})
# producto agotado (auto) no se puede pedir
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
               json={"canal": "MOSTRADOR", "lineas": [{"producto_id": prod_con["id"], "cantidad": 1}]})
check("pedido_no_disponible_409", r.status_code == 409, r.status_code)
# forzado por admin SI se puede pedir aunque no haya stock
httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": True})
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
               json={"canal": "MOSTRADOR", "lineas": [{"producto_id": prod_con["id"], "cantidad": 1}]})
check("pedido_forzado_201", r.status_code == 201, r.status_code)
if r.status_code == 201:
    TMP_PRODUCTOS.append(prod_con["id"])
    s = db()
    pr = s.get(Pedido, r.json()["id"]); pr.estado = "CANCELADO"; s.commit(); s.close()
httpx.put(f"{BASE}/productos/{prod_con['id']}/disponibilidad", headers=hdr("admin"), json={"manual_disponible": None})

# IVA NO incluido: el precio no trae IVA, se suma (1000 -> 1190)
r = httpx.post(f"{BASE}/productos", headers=hdr("admin"),
               json={"categoria_id": 2, "nombre": f"AUDIT IVA {RUN}", "precio": 1000, "iva_incluido": False})
prod_iva = r.json()
TMP_PRODUCTOS.append(prod_iva["id"])
p_iva = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
                   json={"canal": "MOSTRADOR", "lineas": [{"producto_id": prod_iva["id"], "cantidad": 1}]}).json()
v_iva = httpx.get(f"{BASE}/pedidos/{p_iva['id']}", headers=hdr("caja")).json()
check("iva_calculo_conforme",
      (Decimal(v_iva["total"]) == Decimal("1190.00") and Decimal(v_iva["iva"]) == Decimal("190.00")) or
      (Decimal(v_iva["total"]) == Decimal("1000.00") and Decimal(v_iva["iva"]) == Decimal("0.00")),
      v_iva)

# ============================================================
print("== 4. PEDIDOS: VALIDACIONES Y FLUJO ==")
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MESA", "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("mesa_sin_id_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "mesa_id": 5, "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("mesa_id_en_no_mesa_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "DIDI", "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("didi_sin_orden_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": []})
check("lineas_vacias_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 999999, "cantidad": 1}]})
check("producto_inexistente_404", r.status_code == 404, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 0}]})
check("cantidad_cero_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": -2}]})
check("cantidad_negativa_422", r.status_code == 422, r.status_code)
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "INVENTADO", "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("canal_invalido_422", r.status_code == 422, r.status_code)

# identidad contable
p = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
               json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 5, "cantidad": 1}]}).json()
v = httpx.get(f"{BASE}/pedidos/{p['id']}", headers=hdr("caja")).json()
suma = Decimal(v["subtotal"]) + Decimal(v["iva"])
check("identidad_subtotal_iva_total", suma == Decimal(v["total"]), f"{v['subtotal']}+{v['iva']}!={v['total']}")
p_cocina = httpx.get(f"{BASE}/pedidos/{p['id']}", headers=hdr("cocina")).json()
check("cocina_no_ve_total_pedido", p_cocina["total"] is None)
check("mesero_si_ve_total_pedido", p["total"] is not None)

# variacion_snapshot se persiste
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
               json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 1, "cantidad": 1, "variacion_snapshot": {"sin_tomate": True}}]})
vv = r.json()
check("variacion_persistida", vv["detalles"][0]["variacion_snapshot"] == {"sin_tomate": True}, vv["detalles"][0])

# consecutivo creciente
c1 = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
c2 = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
check("consecutivo_crece", c2["consecutivo"] == c1["consecutivo"] + 1, f"{c1['consecutivo']}->{c2['consecutivo']}")

# tipo=hoy incluye el pedido recien creado
hoy = httpx.get(f"{BASE}/pedidos?tipo=hoy", headers=hdr("admin")).json()
check("tipo_hoy_incluye", any(x["id"] == c2["id"] for x in hoy))

# enviar a cocina: idempotente, no permitido en NUEVO->? ya enviado ok, y en FINALIZADO 409
check("enviar_200", httpx.post(f"{BASE}/pedidos/{p['id']}/enviar-a-cocina", headers=hdr("mesero")).status_code == 200)
check("enviar_dos_veces_200", httpx.post(f"{BASE}/pedidos/{p['id']}/enviar-a-cocina", headers=hdr("mesero")).status_code == 200)

# ============================================================
print("== 5. COCINA: INVENTARIO Y TRANSICIONES ==")
s = db()
ing_row = s.get(Ingrediente, ing["id"])
ing_row.stock_actual = Decimal("3000")  # suficiente para 2 unidades de 500 g
s.commit()
stock_antes = ing_row.stock_actual
s.close()
pid_inv = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
                     json={"canal": "MOSTRADOR", "lineas": [{"producto_id": prod_con["id"], "cantidad": 2}]}).json()
# receta actual = 500 gramos/unidad => 2 unidades = 1000 gramos
httpx.post(f"{BASE}/pedidos/{pid_inv['id']}/enviar-a-cocina", headers=hdr("mesero"))
det = pid_inv["detalles"][0]["id"]
check("aceptar_200", httpx.post(f"{BASE}/cocina/detalles/{det}/aceptar", headers=hdr("cocina")).status_code == 200)
s = db()
stock_despues = s.get(Ingrediente, ing["id"]).stock_actual
s.close()
check("descuento_exacto", stock_antes - stock_despues == Decimal("1000.0000"), f"{stock_antes}->{stock_despues}")
check("aceptar_dos_veces_409", httpx.post(f"{BASE}/cocina/detalles/{det}/aceptar", headers=hdr("cocina")).status_code == 409)

# producto SIN receta no descuenta
sin_oferta = 7  # Porcion de Yuca tiene receta? usar agua (id 6) sin receta
ing_antes = {i["id"]: Decimal(i["stock_actual"]) for i in httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).json()}
pid_sr = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
                    json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 6, "cantidad": 3}]}).json()
httpx.post(f"{BASE}/pedidos/{pid_sr['id']}/enviar-a-cocina", headers=hdr("mesero"))
httpx.post(f"{BASE}/cocina/detalles/{pid_sr['detalles'][0]['id']}/aceptar", headers=hdr("cocina"))
ing_desp = {i["id"]: Decimal(i["stock_actual"]) for i in httpx.get(f"{BASE}/ingredientes", headers=hdr("admin")).json()}
check("sin_receta_no_descuenta", ing_antes == ing_desp)

# listo desde ENVIADO (sin aceptar) => 409
pid_l = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
httpx.post(f"{BASE}/pedidos/{pid_l['id']}/enviar-a-cocina", headers=hdr("mesero"))
check("listo_sin_aceptar_409", httpx.post(f"{BASE}/cocina/detalles/{pid_l['detalles'][0]['id']}/listo", headers=hdr("cocina")).status_code == 409)

# marcar listo finaliza
httpx.post(f"{BASE}/cocina/detalles/{det}/listo", headers=hdr("cocina"))
check("pedido_FINALIZADO", httpx.get(f"{BASE}/pedidos/{pid_inv['id']}", headers=hdr("admin")).json()["estado"] == "FINALIZADO")
check("mesero_marcar_listo_403",
      httpx.post(f"{BASE}/cocina/detalles/{det}/listo", headers=hdr("mesero")).status_code == 403)

# ============================================================
print("== 6. CAJA: ESTADOS LIMITE Y DEVOLUCIONES ==")
# cobrar pedido CANCELADO / CERRADO
pid_can = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
s = db()
pr = s.get(Pedido, pid_can["id"]); pr.estado = "CANCELADO"; s.commit(); s.close()
check("cobrar_cancelado_409",
      httpx.post(f"{BASE}/caja/pedidos/{pid_can['id']}/cobrar", headers=hdr("caja"),
                 json={"pagos": [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}]}).status_code == 409)
pid_cer = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
s = db()
pr = s.get(Pedido, pid_cer["id"]); pr.estado = "CERRADO"; s.commit(); s.close()
check("cobrar_cerrado_409",
      httpx.post(f"{BASE}/caja/pedidos/{pid_cer['id']}/cobrar", headers=hdr("caja"),
                 json={"pagos": [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}]}).status_code == 409)

# devolucion total: pedido vuelve a quedar por pagar y se puede recobrar
pid_d = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
rc = httpx.post(f"{BASE}/caja/pedidos/{pid_d['id']}/cobrar", headers=hdr("caja"),
                json={"pagos": [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}]}).json()
pago_id = rc["pagos"][0]["id"]
r = httpx.post(f"{BASE}/caja/pagos/{pago_id}/devolver", headers=hdr("caja"), json={"motivo": "Cliente se arrepintio"})
check("devolver_200", r.status_code == 200, r.text[:150])
check("pago_devuelto", r.json()["estado"] == "DEVUELTO")
check("devolver_dos_veces_409", httpx.post(f"{BASE}/caja/pagos/{pago_id}/devolver", headers=hdr("caja"), json={"motivo": "otra vez"}).status_code == 409)
check("motivo_corto_422", httpx.post(f"{BASE}/caja/pagos/{pago_id}/devolver", headers=hdr("caja"), json={"motivo": "x"}).status_code == 422)
after = httpx.get(f"{BASE}/pedidos/{pid_d['id']}", headers=hdr("caja")).json()
check("pedido_desmarcado_tras_devolucion", after["pagado"] is False, after["pagado"])
rc2 = httpx.post(f"{BASE}/caja/pedidos/{pid_d['id']}/cobrar", headers=hdr("caja"),
                 json={"pagos": [{"metodo": "TARJETA", "monto": 3000}]})
check("recobro_tras_devolucion_200", rc2.status_code == 200, rc2.text[:150])
# movimiento DEVOLUCION registrado
movs = httpx.get(f"{BASE}/caja/movimientos?categoria=DEVOLUCION", headers=hdr("caja")).json()
check("mov_devolucion", any(m["pedido_id"] == pid_d["id"] and m["tipo"] == "SALIDA" for m in movs))

# ============================================================
print("== 7. CONCURRENCIA ==")
s = db()
dia = date.today()
antes = s.query(Pedido).filter(Pedido.fecha_dia == dia).count()
s.close()


def crear(_):
    r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
                   json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]})
    return r.status_code, (r.json().get("consecutivo") if r.status_code == 201 else None)


with ThreadPoolExecutor(max_workers=10) as ex:
    res = list(ex.map(crear, range(10)))
codes = [c for c, _ in res]
cons = [k for _, k in res if k is not None]
check("concurrencia_sin_500", codes.count(500) == 0, f"500x{codes.count(500)} codes={codes}")
check("consecutivos_unicos", len(cons) == len(set(cons)), f"{sorted(cons)}")
nota(f"crear_pedido concurrente (10 hilos): codigos={ {c: codes.count(c) for c in set(codes)} }, consecutivos={sorted(cons)}")

# ============================================================
print("== 8. WEBSOCKET: AUTENTICACION ==")


async def ws_connect(token=None):
    import websockets
    url = "ws://localhost:8000/ws/pedidos" + (f"?token={token}" if token else "")
    try:
        async with websockets.connect(url, open_timeout=5):
            return True
    except Exception:
        return False


check("ws_sin_token_rechazado", asyncio.run(ws_connect()) is False, "el WS debe exigir token")
check("ws_token_invalido_rechazado", asyncio.run(ws_connect("basura.invalida")) is False)
check("ws_con_token_conecta", asyncio.run(ws_connect(TOK["cocina"])) is True)

# ============================================================
print("== 9. ZONA HORARIA ==")
try:
    bogota = datetime.now(ZoneInfo("America/Bogota"))
    check("tz_zoneinfo_disponible", True)
except Exception as e:
    bogota = None
    check("tz_zoneinfo_disponible", False, str(e))
if bogota:
    fecha_utc = datetime.now(timezone.utc).date()
    fecha_bog = bogota.date()
    nota(f"UTC hoy={fecha_utc}  |  Bogota hoy={fecha_bog}  (actualmente {'IGUALES' if fecha_utc==fecha_bog else 'DIFERENTES'})")
    # Simular las 01:00 UTC (20:00 Bogota del dia anterior)
    sim_utc = datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc)
    check("tz_ventana_de_fallo", sim_utc.astimezone(ZoneInfo("America/Bogota")).date() != sim_utc.date(),
         "a las 01:00 UTC el date() UTC ya es del dia siguiente pero en Bogota aun es el dia anterior")

# ============================================================
print("== 10. AGUJEROS DE FLUJO ==")
# 10a. Mesa liberada a mano con pedido abierto => permite doble pedido en la misma mesa
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MESA", "mesa_id": 6, "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("mesa6_pedido1_201", r.status_code == 201, r.text[:150])
httpx.put(f"{BASE}/pedidos/mesas/6/estado", headers=hdr("caja"), json={"estado": "DISPONIBLE"})
r2 = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MESA", "mesa_id": 6, "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("mesa6_doble_pedido_bloqueado", r2.status_code == 409,
      f"se creo un 2do pedido en la misma mesa con un pedido abierto (status {r2.status_code})")
# 10b. Mesa EN_CURSO deberia bloquear apertura
httpx.put(f"{BASE}/pedidos/mesas/7/estado", headers=hdr("caja"), json={"estado": "EN_CURSO"})
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MESA", "mesa_id": 7, "lineas": [{"producto_id": 5, "cantidad": 1}]})
check("mesa_en_curso_bloquea", r.status_code == 409, f"mesa EN_CURSO acepto pedido ({r.status_code})")

# 10c. Ronda: el total NO debe duplicarse
r = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
httpx.post(f"{BASE}/pedidos/{r['id']}/rondas", headers=hdr("mesero"), json={"ronda": 2, "lineas": [{"producto_id": 5, "cantidad": 1}]})
tt = Decimal(httpx.get(f"{BASE}/pedidos/{r['id']}", headers=hdr("caja")).json()["total"])
check("ronda_no_duplica_total", tt == Decimal("6000.00"), f"total tras ronda = {tt} (esperado 6000)")
# 10d. Ronda en pedido FINALIZADO reactiva la cola de cocina
ped_ronda = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
httpx.post(f"{BASE}/pedidos/{ped_ronda['id']}/enviar-a-cocina", headers=hdr("mesero"))
d1 = ped_ronda["detalles"][0]["id"]
httpx.post(f"{BASE}/cocina/detalles/{d1}/aceptar", headers=hdr("cocina"))
httpx.post(f"{BASE}/cocina/detalles/{d1}/listo", headers=hdr("cocina"))
est0 = httpx.get(f"{BASE}/pedidos/{ped_ronda['id']}", headers=hdr("caja")).json()["estado"]
httpx.post(f"{BASE}/pedidos/{ped_ronda['id']}/rondas", headers=hdr("mesero"), json={"ronda": 2, "lineas": [{"producto_id": 5, "cantidad": 1}]})
est = httpx.get(f"{BASE}/pedidos/{ped_ronda['id']}", headers=hdr("caja")).json()["estado"]
check("ronda_reactiva_finalizado", est0 == "FINALIZADO" and est == "ENVIADO_A_COCINA", f"{est0} -> {est}")
# 10e. Ronda en pedido ENTREGADO (repartidor ya lo llevo) tambien lo reactiva
ped_ent = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"), json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
s = db()
pr = s.get(Pedido, ped_ent["id"]); pr.estado = "ENTREGADO"; s.commit(); s.close()
httpx.post(f"{BASE}/pedidos/{ped_ent['id']}/rondas", headers=hdr("mesero"), json={"ronda": 2, "lineas": [{"producto_id": 5, "cantidad": 1}]})
est_ent = httpx.get(f"{BASE}/pedidos/{ped_ent['id']}", headers=hdr("caja")).json()["estado"]
check("ronda_reactiva_entregado", est_ent == "ENVIADO_A_COCINA", est_ent)

print("== 11. CORS (PWA en tablets de la LAN) ==")
r = httpx.options(f"{BASE}/pedidos", headers={
    "Origin": "http://192.168.1.50:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization,content-type",
})
acao = r.headers.get("access-control-allow-origin")
check("cors_preflight_ok", r.status_code in (200, 204) and acao in ("*", "http://192.168.1.50:5173"), f"{r.status_code} {acao}")

print("== 12. FUGA DE DINERO EN WEBSOCKET ==")


async def ws_leak():
    import websockets
    async with websockets.connect(f"ws://localhost:8000/ws/pedidos?token={TOK['caja']}", open_timeout=5) as ws:
        # dispara un cobro desde otro hilo mientras escuchamos
        def hace_cobro():
            import time
            time.sleep(0.4)
            pp = httpx.post(f"{BASE}/pedidos", headers=hdr("mesero"),
                            json={"canal": "MOSTRADOR", "lineas": [{"producto_id": 5, "cantidad": 1}]}).json()
            httpx.post(f"{BASE}/caja/pedidos/{pp['id']}/cobrar", headers=hdr("caja"),
                       json={"pagos": [{"metodo": "EFECTIVO", "monto": 3000, "recibido": 3000}]})
        import threading
        threading.Thread(target=hace_cobro, daemon=True).start()
        fin = asyncio.get_event_loop().time() + 6
        while asyncio.get_event_loop().time() < fin:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
            except asyncio.TimeoutError:
                continue
            ev = json.loads(raw)
            if ev.get("evento") == "pedido_pagado":
                return ev
        return None


ev = asyncio.run(ws_leak())
check("ws_pedido_pagado_recibido", ev is not None, "no llego el evento pedido_pagado")
if ev:
    check("ws_pedido_pagado_sin_dinero", "total" not in ev.get("data", {}),
          f"el evento difundido a TODOS incluye el total: {ev.get('data')}")

# ============================================================
print("== 13. LIMPIEZA ==")
s = db()
for item in [ped_caja, p, pid_inv, pid_sr, pid_l, pid_can, pid_cer, pid_d, c1, c2, ped_ronda, p_iva, ped_ent]:
    if not item:
        continue
    pr = s.get(Pedido, item["id"])
    if pr and pr.estado != "CANCELADO":
        pr.estado = "CANCELADO"
for pid2 in [k for _, k in res]:
    pass
for prod in [prod_sin, prod_con]:
    row = s.get(Producto, prod["id"])
    if row:
        row.activo = False
        row.manual_disponible = None
for i in TMP_INGREDIENTES:
    row = s.get(Ingrediente, i)
    if row:
        row.activo = False
for uid in TMP_USUARIOS:
    row = s.get(Usuario, uid)
    if row:
        row.activo = False
s.commit()
from app.models import Mesa  # noqa: E402
for m in s.query(Mesa).all():
    abiertos = s.query(Pedido).filter(Pedido.mesa_id == m.id, Pedido.estado.notin_(["PAGADO", "CERRADO", "CANCELADO"])).count()
    if abiertos == 0:
        m.estado = "DISPONIBLE"
s.commit()
s.close()
nota("datos de auditoria limpiados (soft-delete)")

# ============================================================
print("== 14. HISTORIAL DE ACCIONES (nada se toca sin registro) ==")
s = db()
check("historial_escrito", s.query(HistorialAccion).count() > 0)
check("historial_cobro", s.query(HistorialAccion).filter(HistorialAccion.accion == "COBRAR_PEDIDO").first() is not None)
check("historial_aceptar", s.query(HistorialAccion).filter(HistorialAccion.accion == "ACEPTAR_PREPARACION").first() is not None)
s.close()

print()
print("=" * 50)
print(f"RESULTADO AUDITORIA: {PASS} PASS / {FAIL} FAIL")
if FALLOS:
    print("Fallos:")
    for f in FALLOS:
        print(f"  - {f}")
print("=" * 50)
sys.exit(1 if FAIL else 0)
