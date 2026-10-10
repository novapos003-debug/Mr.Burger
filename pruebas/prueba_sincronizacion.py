"""Prueba de punta a punta de la sincronización: dos backends reales (caja y nube) con dos bases
desechables. NUNCA toca la nube real: ambos procesos apuntan a 127.0.0.1."""
import os
import subprocess
import sys
import time
from decimal import Decimal

import httpx
import psycopg2
from passlib.context import CryptContext

BACKEND = sys.argv[1]
PY = sys.executable
PG = dict(host="127.0.0.1", port=55432, user="restaurante", password="restaurante_dev")
URL_L, URL_N = "http://127.0.0.1:8900", "http://127.0.0.1:8901"
TOKEN = "token-solo-de-pruebas-0123456789"
CLAVE = "Prueba#2026"
HAMB, PAPAS, GASEOSA = 7, 55, 63
resultados = []
procesos = {}


def ok(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(("  PASA  " if cond else "  FALLA ") + nombre + (f"  -> {detalle}" if detalle else ""), flush=True)


def q(db, sql, *p):
    c = psycopg2.connect(dbname=db, **PG)
    try:
        c.autocommit = True
        cur = c.cursor()
        cur.execute(sql, p) if p else cur.execute(sql)
        return cur.fetchall() if cur.description else None
    finally:
        c.close()


def lanzar(nombre, puerto, db, modo, extra=None):
    env = {k: v for k, v in os.environ.items()}
    env.update({
        "DATABASE_URL": f"postgresql://restaurante:restaurante_dev@127.0.0.1:55432/{db}",
        "SECRET_KEY": f"clave-de-pruebas-{nombre}-0123456789abcdef",
        "MODO_CEREBRO": modo,
        "CLOUD_SYNC_TOKEN": TOKEN,
        "CLOUD_SYNC_URL": URL_N if modo == "LOCAL" else "",
        "CLOUD_SYNC_ENABLED": "true",
        "SYNC_INTERVAL_SECONDS": "3",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    env.update(extra or {})
    assert "onrender" not in env["CLOUD_SYNC_URL"]
    log = open(os.path.join(os.path.dirname(__file__), f"log_{nombre}.txt"), "w", encoding="utf-8")
    procesos[nombre] = subprocess.Popen(
        [PY, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(puerto), "--log-level", "warning"],
        cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{puerto}"
    for _ in range(120):
        try:
            if httpx.get(url + "/api/health", timeout=2).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"{nombre} no arrancó; ver log_{nombre}.txt")


def detener(nombre):
    p = procesos.pop(nombre, None)
    if p:
        p.terminate()
        try:
            p.wait(timeout=15)
        except Exception:
            p.kill()


def login(url, usuario, clave=CLAVE):
    r = httpx.post(url + "/auth/login", data={"username": usuario, "password": clave}, timeout=20)
    return r.json().get("access_token") if r.status_code == 200 else None


class Cliente:
    def __init__(self, url):
        self.url = url
        self.tokens = {}

    def h(self, usuario):
        if usuario not in self.tokens:
            self.tokens[usuario] = login(self.url, usuario)
        return {"Authorization": f"Bearer {self.tokens[usuario]}"}

    def req(self, metodo, ruta, usuario, **kw):
        return httpx.request(metodo, self.url + ruta, headers=self.h(usuario), timeout=30, **kw)


L, N = Cliente(URL_L), Cliente(URL_N)

TABLAS = [
    "rol", "usuario", "tipo_categoria", "categoria", "categoria_insumo", "proveedor", "producto", "ingrediente",
    "detalle_receta", "componente_combo", "mesa", "pedido", "detalle_pedido", "pago", "vale", "cierre",
    "movimiento_caja", "movimiento_inventario", "preparado", "compra", "detalle_compra", "turno_laboral",
    "historial_accion",
]


def huella(db, tabla):
    return q(db, f"select count(*), coalesce(md5(string_agg(md5(to_jsonb(t)::text), '' order by t.id)), '') from \"{tabla}\" t")[0]


def huella_config(db):
    return q(db, "select count(*), coalesce(md5(string_agg(md5(to_jsonb(t)::text), '' order by t.clave)), '') "
                 "from configuracion t where clave not like 'sync_%' and clave not like 'migracion_%'")[0]


def diferencias():
    dif = [t for t in TABLAS if huella("prueba", t) != huella("nube", t)]
    if huella_config("prueba") != huella_config("nube"):
        dif.append("configuracion")
    return dif


def detalle_diferencias(limite=6):
    """Para diagnosticar un fallo: qué filas y columnas difieren entre la caja y la nube."""
    partes = []
    for tabla in diferencias():
        if tabla == "configuracion":
            continue
        a = dict(q("prueba", f'select t.id, to_jsonb(t) from "{tabla}" t'))
        b = dict(q("nube", f'select t.id, to_jsonb(t) from "{tabla}" t'))
        for i in sorted(set(a) | set(b)):
            if a.get(i) != b.get(i) and len(partes) < limite:
                if i not in a or i not in b:
                    partes.append(f"{tabla}#{i} solo en {'caja' if i in a else 'nube'}")
                else:
                    partes.append(f"{tabla}#{i} " + str({k: (a[i][k], b[i].get(k)) for k in a[i] if a[i][k] != b[i].get(k)}))
    return "; ".join(partes)


def pendientes_local():
    return q("prueba", "select count(*) from registro_sync where estado='PENDIENTE' and origen='LOCAL'")[0][0]


def esperar(cond, segundos=40, paso=0.25):
    """Espera hasta que `cond()` sea verdadera. Devuelve (ok, segundos transcurridos)."""
    t0 = time.time()
    while time.time() - t0 < segundos:
        try:
            if cond():
                return True, time.time() - t0
        except Exception:
            pass
        time.sleep(paso)
    return False, time.time() - t0


def esperar_iguales(segundos=60):
    listo, t = esperar(lambda: pendientes_local() == 0 and not diferencias(), segundos, 0.5)
    return listo, t


def vender(cliente, usuario_caja="caja", **extra):
    body = {"canal": "MOSTRADOR", "lineas": [{"producto_id": HAMB, "cantidad": 1}], **extra}
    p = cliente.req("POST", "/pedidos", usuario_caja, json=body).json()
    cliente.req("POST", f"/pedidos/{p['id']}/enviar-a-cocina", usuario_caja)
    for d in p["detalles"]:
        cliente.req("POST", f"/cocina/detalles/{d['id']}/aceptar", "cocina")
        cliente.req("POST", f"/cocina/detalles/{d['id']}/listo", "cocina")
    total = cliente.req("GET", f"/pedidos/{p['id']}", "admin").json()["total"]
    r = cliente.req("POST", f"/caja/pedidos/{p['id']}/cobrar", usuario_caja,
                    json={"pagos": [{"metodo": "EFECTIVO", "monto": total, "recibido": total}]})
    assert r.status_code == 200, r.text
    return p["id"], r.json()["pagos"][0]["id"]


def main():
    # --- bases desechables: caja = copia del respaldo; nube = vacía (la crea el propio backend)
    for db in ("prueba", "nube"):
        q("postgres", f"drop database if exists {db} with (force)")
    q("postgres", "create database prueba template restaurante")
    origen_nube = os.environ.get("NUBE_ORIGEN", "")
    q("postgres", "create database nube" + (f" template {origen_nube}" if origen_nube else ""))
    q("prueba", "update usuario set password_hash = %s", CryptContext(schemes=["bcrypt"]).hash(CLAVE))
    q("prueba", "update cierre set cerrado_en = now() where cerrado_en is null")

    lanzar("nube", 8901, "nube", "NUBE")
    lanzar("caja", 8900, "prueba", "LOCAL")

    print("\n[A] Copia inicial completa al espejo")
    listo, t = esperar_iguales(120)
    ok("A1. tras el primer arranque la nube queda idéntica a la caja", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")
    ok("A2. no quedan operaciones con error", q("prueba", "select count(*) from registro_sync where estado like 'ERROR%'")[0][0] == 0)
    ok("A3. el dueño puede entrar al panel web con su usuario", login(URL_N, "admin") is not None)

    print("\n[B] Una venta completa llega a la nube con todos sus datos")
    r = L.req("POST", "/caja/turno/abrir", "caja", json={"monto_inicial": 100000})
    ok("B0. abrir turno", r.status_code == 201, r.text[:100])
    t0 = time.time()
    body = {"canal": "DOMICILIO", "tipo_consumo": "LLEVAR", "cliente": "Ana Prueba", "telefono": "3001234567",
            "direccion": "Calle 5 # 10-20", "nota_interna": "sin cebolla",
            "lineas": [{"producto_id": HAMB, "cantidad": 2, "variacion_snapshot": {"adiciones": [{"id": "ad-tocineta", "nombre": "Tocineta", "precio": 3000}]}}]}
    p = L.req("POST", "/pedidos", "caja", json=body).json()
    visto, lat = esperar(lambda: q("nube", "select 1 from pedido where id=%s", p["id"]), 20, 0.1)
    ok("B1. el pedido aparece en la nube en segundos", visto, f"{lat:.1f}s")
    fila = q("nube", "select tipo_consumo, telefono, direccion, nota_interna, recargo_empaque, total, creado_en from pedido where id=%s", p["id"])
    local = q("prueba", "select tipo_consumo, telefono, direccion, nota_interna, recargo_empaque, total, creado_en from pedido where id=%s", p["id"])
    ok("B2. llega con tipo de consumo, teléfono, dirección, nota, empaque, total y hora exactos", fila == local and fila[0][0] == "LLEVAR", str(fila[0][:6]) if fila else "sin fila")
    snap = q("nube", "select variacion_snapshot from detalle_pedido where pedido_id=%s", p["id"])
    ok("B3. las adiciones del pedido llegan", bool(snap and snap[0][0] and snap[0][0].get("adiciones")))
    L.req("POST", f"/pedidos/{p['id']}/enviar-a-cocina", "caja")
    for d in p["detalles"]:
        L.req("POST", f"/cocina/detalles/{d['id']}/aceptar", "cocina")
    visto, lat = esperar(lambda: q("nube", "select estado from pedido where id=%s", p["id"])[0][0] == "EN_PREPARACION", 20, 0.1)
    ok("B4. el estado de cocina se refleja en la nube", visto, f"{lat:.1f}s")
    for d in p["detalles"]:
        L.req("POST", f"/cocina/detalles/{d['id']}/listo", "cocina")
    total = L.req("GET", f"/pedidos/{p['id']}", "admin").json()["total"]
    L.req("POST", f"/caja/pedidos/{p['id']}/cobrar", "caja", json={"pagos": [{"metodo": "EFECTIVO", "monto": total, "recibido": total}]})
    listo, t = esperar_iguales()
    ok("B5. cobro, inventario, auditoría y base de caja: todo idéntico en la nube", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")
    ok("B6. la base inicial de caja está en la nube", q("nube", "select count(*) from movimiento_caja where categoria='CAMBIO_INICIAL'")[0][0] >= 1)
    dash_l = L.req("GET", "/admin/dashboard", "admin").json()
    dash_n = N.req("GET", "/admin/dashboard", "admin").json()
    ok("B7. el panel del dueño muestra las mismas ventas que la caja",
       dash_l["total_ventas"] == dash_n["total_ventas"] and Decimal(dash_n["total_ventas"]) > 0, f"caja={dash_l['total_ventas']} nube={dash_n['total_ventas']}")

    print("\n[C] Cancelaciones, devoluciones y vales")
    pid, pago = vender(L)
    L.req("POST", f"/pedidos/{pid}/cancelar", "admin", json={"motivo": "prueba de cancelacion"})
    pid2, _ = vender(L)
    pid3 = L.req("POST", "/pedidos", "caja", json={"canal": "MOSTRADOR", "lineas": [{"producto_id": GASEOSA, "cantidad": 1}]}).json()["id"]
    L.req("POST", f"/caja/pedidos/{pid3}/cobrar", "caja", json={"pagos": [{"metodo": "VALE", "monto": "5500", "vale_cliente_nombre": "Vecino"}]})
    listo, t = esperar_iguales()
    ok("C1. todo queda idéntico tras cancelar y fiar", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")
    ok("C2. la nube ve el pedido cancelado y su pago devuelto",
       q("nube", "select estado from pedido where id=%s", pid)[0][0] == "CANCELADO" and q("nube", "select estado from pago where id=%s", pago)[0][0] == "DEVUELTO")
    ok("C3. la nube ve el vale pendiente", q("nube", "select count(*) from vale where estado='PENDIENTE'")[0][0] == 1)

    print("\n[D] Lo que se cambia en la caja ya no se revierte")
    uid = q("prueba", "select id from usuario where usuario='mesero'")[0][0]
    L.req("PUT", f"/admin/usuarios/{uid}/estado", "admin", json={"activo": False})
    time.sleep(12)
    ok("D1. un usuario desactivado en la caja sigue desactivado", q("prueba", "select activo from usuario where id=%s", uid)[0][0] is False)
    ok("D2. y también queda desactivado en la nube", q("nube", "select activo from usuario where id=%s", uid)[0][0] is False)
    L.req("PUT", f"/admin/usuarios/{uid}/estado", "admin", json={"activo": True})

    print("\n[E] Sin internet: se sigue vendiendo y al volver se entrega todo")
    detener("nube")
    L.req("PUT", f"/productos/{PAPAS}", "admin", json={"precio": 12500})
    pid_off, _ = vender(L)
    time.sleep(6)
    ok("E1. sin nube, la venta se guarda y queda en cola", pendientes_local() > 0, f"pendientes={pendientes_local()}")
    est = L.req("GET", "/sync/estado", "admin").json()
    ok("E2. la caja informa que está sin conexión", est["online"] is False, str(est.get("ultimo_error")))
    lanzar("nube", 8901, "nube", "NUBE")
    listo, t = esperar_iguales(90)
    ok("E3. al volver la nube todo se entrega solo", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")
    ok("E4. el precio cambiado sin internet se conserva en la caja y llega a la nube",
       q("prueba", "select precio from producto where id=%s", PAPAS)[0][0] == 12500 == q("nube", "select precio from producto where id=%s", PAPAS)[0][0])
    ok("E5. la venta hecha sin internet conserva su hora real",
       q("prueba", "select creado_en from pedido where id=%s", pid_off) == q("nube", "select creado_en from pedido where id=%s", pid_off))

    print("\n[F] Cambios hechos desde el panel web bajan a la caja")
    N.tokens.clear()
    t0 = time.time()
    r = N.req("PUT", f"/productos/{GASEOSA}", "admin", json={"precio": 6000})
    ok("F0. el panel web acepta el cambio de precio", r.status_code == 200, r.text[:100])
    visto, lat = esperar(lambda: q("prueba", "select precio from producto where id=%s", GASEOSA)[0][0] == 6000, 30, 0.2)
    ok("F1. el precio cambiado en la web llega a la caja", visto, f"{lat:.1f}s")
    cat = q("nube", "select categoria_id from producto where id=%s", GASEOSA)[0][0]
    r = N.req("POST", "/productos", "admin", json={"categoria_id": cat, "nombre": "Malteada Prueba", "precio": 9000})
    nuevo = r.json().get("id")
    ok("F2. un producto creado en la web usa numeración de la nube", r.status_code == 201 and nuevo >= 1_000_000, f"id={nuevo}")
    visto, lat = esperar(lambda: q("prueba", "select 1 from producto where id=%s", nuevo), 30, 0.2)
    ok("F3. el producto nuevo aparece en la caja", bool(visto), f"{lat:.1f}s")
    pv = L.req("POST", "/pedidos", "caja", json={"canal": "MOSTRADOR", "lineas": [{"producto_id": nuevo, "cantidad": 1}]})
    ok("F4. la caja puede venderlo", pv.status_code == 201, pv.text[:120])
    L.req("POST", f"/caja/pedidos/{pv.json()['id']}/cobrar", "caja", json={"pagos": [{"metodo": "TARJETA", "monto": "9000"}]})
    r = L.req("POST", "/productos", "admin", json={"categoria_id": cat, "nombre": "Producto Caja Prueba", "precio": 4000})
    ok("F5. un producto creado en la caja usa numeración local", r.status_code == 201 and r.json()["id"] < 1_000_000, f"id={r.json().get('id')}")

    ing = 21  # Pan Hamburguesa
    antes = q("prueba", "select stock_actual from ingrediente where id=%s", ing)[0][0]
    r = N.req("PUT", f"/ingredientes/{ing}", "admin", json={"stock_actual": float(q("nube", "select stock_actual from ingrediente where id=%s", ing)[0][0] + 10)})
    ok("F6. el panel web acepta un ajuste de inventario", r.status_code == 200, r.text[:100])
    visto, lat = esperar(lambda: q("prueba", "select stock_actual from ingrediente where id=%s", ing)[0][0] == antes + 10, 30, 0.2)
    ok("F7. el ajuste de stock hecho en la web se suma en la caja", visto, f"{antes} -> {q('prueba', 'select stock_actual from ingrediente where id=%s', ing)[0][0]} en {lat:.1f}s")

    r = N.req("POST", "/admin/usuarios", "admin", json={"nombre": "Nuevo Web", "usuario": "nuevoweb", "password": "Clave#Web1", "rol": "cajero"})
    ok("F8. el panel web crea un usuario", r.status_code == 201, r.text[:100])
    visto, lat = esperar(lambda: login(URL_L, "nuevoweb", "Clave#Web1") is not None, 30, 0.5)
    ok("F9. ese usuario entra en la caja con SU contraseña", visto, f"{lat:.1f}s")
    nid = r.json()["id"]
    N.req("PUT", f"/admin/usuarios/{nid}/password", "admin", json={"nueva_password": "Otra#Clave2"})
    visto, lat = esperar(lambda: login(URL_L, "nuevoweb", "Otra#Clave2") is not None, 30, 0.5)
    ok("F10. un cambio de contraseña hecho en la web llega a la caja", visto, f"{lat:.1f}s")

    listo, t = esperar_iguales()
    ok("F11. después de todo, caja y nube siguen idénticas", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")

    print("\n[G] Protecciones")
    op = {"op_id": "prueba-intruso-0001", "dispositivo_id": "otra-caja", "tipo": "FILA", "entidad": "usuario", "payload": {"pk": {"id": 1}, "fila": {"id": 1, "activo": False}}}
    r = httpx.post(URL_N + "/sync/push", headers={"X-Sync-Token": TOKEN}, json={"dispositivo_id": "otra-caja-distinta", "operaciones": [op]})
    ok("G1. una segunda caja no puede escribir en el espejo", r.status_code == 409, f"HTTP {r.status_code}")
    r = httpx.post(URL_N + "/sync/push", headers=N.h("admin"), json={"dispositivo_id": "xx", "operaciones": [op]})
    ok("G2. una sesión de usuario no puede usar el canal de sincronización", r.status_code == 401, f"HTTP {r.status_code}")
    r = httpx.post(URL_N + "/sync/push", headers={"X-Sync-Token": "mrburger_sync_secret_token_2026"}, json={"dispositivo_id": "xx", "operaciones": [op]})
    ok("G3. el token antiguo publicado ya no sirve", r.status_code == 401, f"HTTP {r.status_code}")
    ok("G4. la documentación de la API no se publica en la nube", httpx.get(URL_N + "/docs").status_code == 404 and httpx.get(URL_N + "/openapi.json").status_code == 404)
    ok("G5. no quedaron operaciones rechazadas en la caja",
       q("prueba", "select count(*) from registro_sync where estado in ('ERROR','ERROR_SERVIDOR','CONFLICTO')")[0][0] == 0,
       str(q("prueba", "select entidad, left(ultimo_error,90) from registro_sync where estado <> 'APLICADO' and ultimo_error is not null limit 3")))

    cid = q("prueba", "select id from usuario where usuario='cocina'")[0][0]
    L.req("PUT", f"/admin/usuarios/{cid}/password", "admin", json={"nueva_password": "cocina123"})
    esperar(lambda: pendientes_local() == 0, 20)
    time.sleep(1)
    r = httpx.post(URL_N + "/auth/login", data={"username": "cocina", "password": "cocina123"})
    ok("G6. una cuenta con contraseña de fábrica no entra por internet", r.status_code == 403, f"HTTP {r.status_code}")
    ok("G7. pero sí entra en la red local del restaurante", login(URL_L, "cocina", "cocina123") is not None)

    viejo = {"op_id": "prueba-heredada-0001", "dispositivo_id": "SUC-01", "tipo": "CREAR_PEDIDO", "entidad": "pedido", "payload": {"id": 999}}
    antes = q("nube", "select count(*) from pedido")[0][0]
    r = httpx.post(URL_N + "/sync/push", headers={"X-Sync-Token": TOKEN}, json={"dispositivo_id": "SUC-01", "operaciones": [viejo]})
    vinculo = q("nube", "select valor from configuracion where clave='sync_instalacion_vinculada'")[0][0]
    ok("G8. un envío de la versión vieja no aplica, no vincula ni borra nada",
       r.status_code == 200 and q("nube", "select count(*) from pedido")[0][0] == antes and vinculo != "SUC-01", f"HTTP {r.status_code}")

    print("\n[I] Aviso en vivo al panel web")
    import asyncio
    import json as _json
    import websockets

    async def escuchar_y_vender():
        token = login(URL_N, "admin")
        async with websockets.connect(f"ws://127.0.0.1:8901/ws/pedidos?token={token}") as ws:
            t0 = time.time()
            await asyncio.to_thread(vender, L)
            eventos = []
            try:
                while time.time() - t0 < 15:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15 - (time.time() - t0))
                    if msg != "pong":
                        eventos.append((_json.loads(msg), time.time() - t0))
                        if eventos[-1][0].get("evento") == "datos_sincronizados" and "pago" in eventos[-1][0]["data"].get("tablas", []):
                            break
            except asyncio.TimeoutError:
                pass
            return eventos

    eventos = asyncio.run(escuchar_y_vender())
    sincronizados = [(e, t) for e, t in eventos if e.get("evento") == "datos_sincronizados"]
    ok("I1. el panel web recibe un aviso en vivo cuando la caja vende", bool(sincronizados),
       f"primer aviso a los {sincronizados[0][1]:.1f}s de iniciar la venta" if sincronizados else "sin avisos")
    tablas_avisadas = set().union(*[set(e["data"].get("tablas", [])) for e, _ in sincronizados]) if sincronizados else set()
    ok("I2. el aviso incluye pedido, pago e inventario", {"pedido", "pago", "movimiento_inventario"} <= tablas_avisadas, str(sorted(tablas_avisadas)))

    print("\n[H] Reiniciar el espejo a propósito")
    r = httpx.post(URL_N + "/sync/reiniciar-espejo", headers={"X-Sync-Token": TOKEN}, json={"confirmar": "si"})
    ok("H1. sin la frase de confirmación no se reinicia", r.status_code == 422, f"HTTP {r.status_code}")
    r = httpx.post(URL_N + "/sync/reiniciar-espejo", headers={"X-Sync-Token": TOKEN}, json={"confirmar": "REINICIAR ESPEJO"}, timeout=60)
    ok("H2. con la frase, el espejo se vacía", r.status_code == 200 and q("nube", "select count(*) from pedido")[0][0] == 0, f"HTTP {r.status_code}")
    listo, t = esperar_iguales(120)
    ok("H3. la caja lo detecta sola y vuelve a copiar todo", listo, f"{t:.1f}s; difieren: {diferencias()} {detalle_diferencias()}")
    ok("H4. los datos de la caja no se tocaron", q("prueba", "select count(*) from pedido")[0][0] >= 8)
    archivo = q("nube", "select count(*) from information_schema.tables where table_schema='archivo' and table_name like 'pedido\\_\\_%'")[0][0]
    archivados = q("nube", "select coalesce(sum((xpath('/row/c/text()', query_to_xml('select count(*) as c from archivo.'||quote_ident(table_name), false, true, '')))[1]::text::int), 0) "
                           "from information_schema.tables where table_schema='archivo' and table_name like 'producto\\_\\_%'")[0][0]
    ok("H5. antes de vaciarse, la nube guardó una copia de lo que tenía", archivo >= 1 and archivados > 0, f"copias de pedido={archivo}, productos archivados={archivados}")

    fallas = [r for r in resultados if not r[1]]
    print(f"\nRESULTADO: {len(resultados) - len(fallas)} pasan, {len(fallas)} fallan de {len(resultados)}")
    return 1 if fallas else 0


if __name__ == "__main__":
    codigo = 1
    try:
        codigo = main()
    finally:
        for n in list(procesos):
            detener(n)
    sys.exit(codigo)
