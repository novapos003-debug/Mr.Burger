"""Pruebas de la Fase 1 contra una BD desechable (copia del respaldo). Nunca toca la nube."""
import os
import sys
from decimal import Decimal

os.environ["DATABASE_URL"] = "postgresql://restaurante:restaurante_dev@127.0.0.1:55432/prueba"
os.environ["CLOUD_SYNC_ENABLED"] = "false"
os.environ["CLOUD_SYNC_URL"] = ""
os.environ["SECRET_KEY"] = "clave_solo_para_pruebas_locales"
os.environ["PYTHONUTF8"] = "1"

sys.path.insert(0, sys.argv[1])  # ruta a backend/

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.security import create_access_token  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402

ADMIN, CAJA, MESERO, COCINA = 1, 2, 3, 4
HAMB, PAPAS, GASEOSA = 7, 55, 63
resultados: list[tuple[str, bool, str]] = []


def H(uid: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(uid))}"}


def D(v) -> Decimal:
    return Decimal(str(v))


def ok(nombre: str, cond: bool, detalle: str = "") -> None:
    resultados.append((nombre, bool(cond), detalle))
    print(("  PASA  " if cond else "  FALLA ") + nombre + (f"  -> {detalle}" if detalle else ""))


def sql(q: str, **p):
    with engine.begin() as c:
        r = c.execute(text(q), p)
        return r.fetchall() if r.returns_rows else None


def stock(ing_id: int) -> Decimal:
    return D(sql("select stock_actual from ingrediente where id=:i", i=ing_id)[0][0])


def turno(c) -> dict:
    return c.get("/caja/turno", headers=H(CAJA)).json()


def crear(c, uid, canal="MOSTRADOR", lineas=None, **extra) -> dict:
    body = {"canal": canal, "lineas": lineas or [{"producto_id": HAMB, "cantidad": 1}], **extra}
    r = c.post("/pedidos", json=body, headers=H(uid))
    assert r.status_code == 201, r.text
    p = r.json()
    r = c.post(f"/pedidos/{p['id']}/enviar-a-cocina", headers=H(uid))
    assert r.status_code == 200, r.text
    return r.json()


def pedido(c, pid) -> dict:
    return c.get(f"/pedidos/{pid}", headers=H(ADMIN)).json()


def cobrar(c, pid, metodo="EFECTIVO", **extra):
    total = pedido(c, pid)["total"]
    pago = {"metodo": metodo, "monto": total, **extra}
    if metodo == "EFECTIVO":
        pago["recibido"] = total
    return c.post(f"/caja/pedidos/{pid}/cobrar", json={"pagos": [pago]}, headers=H(CAJA))


def cocinar(c, pid, listo=True):
    for d in pedido(c, pid)["detalles"]:
        if d["estado"] == "ENVIADO":
            r = c.post(f"/cocina/detalles/{d['id']}/aceptar", headers=H(COCINA))
            assert r.status_code == 200, r.text
        if listo and d["estado"] in ("ENVIADO", "PREPARANDO"):
            r = c.post(f"/cocina/detalles/{d['id']}/listo", headers=H(COCINA))
            assert r.status_code == 200, r.text


def en_cola(c, pid) -> bool:
    return any(t["pedido_id"] == pid for t in c.get("/cocina/cola", headers=H(COCINA)).json())


def main() -> int:
    with TestClient(app, raise_server_exceptions=False) as c:
        # Estado inicial limpio: cerrar turno abierto del respaldo y abrir uno con base conocida
        if turno(c):
            c.post("/caja/turno/cerrar", json={}, headers=H(CAJA))
        r = c.post("/caja/turno/abrir", json={"monto_inicial": 100000}, headers=H(CAJA))
        assert r.status_code == 201, r.text
        base = D(turno(c)["total_efectivo_final"])
        ok("0. turno abre con base 100000", base == D(100000), f"efectivo_final={base}")

        print("\n[1] Cobro anticipado no debe sacar el ticket de cocina")
        pan_antes = stock(21)
        p = crear(c, CAJA)
        r = cobrar(c, p["id"])
        ok("1a. cobro anticipado aceptado", r.status_code == 200, f"HTTP {r.status_code}")
        ok("1b. el ticket sigue en la cola de cocina", en_cola(c, p["id"]))
        ok("1c. cobrar antes de cocinar no descuenta inventario", stock(21) == pan_antes, f"pan {pan_antes}->{stock(21)}")
        cocinar(c, p["id"])
        pf = pedido(c, p["id"])
        ok("1d. al terminar cocina queda PAGADO", pf["estado"] == "PAGADO", pf["estado"])
        ok("1e. inventario descontado una sola vez", stock(21) == pan_antes - 1, f"pan {pan_antes}->{stock(21)}")
        ok("1f. no se puede cobrar dos veces", cobrar(c, p["id"]).status_code == 409)

        print("\n[2] Gasto operativo")
        r = c.post("/caja/movimientos", headers=H(CAJA), json={
            "tipo": "SALIDA", "categoria": "GASTO_OPERATIVO", "valor": 5000, "descripcion": "Jabon Axion"})
        ok("2. se guarda un gasto operativo", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")

        print("\n[3] Arqueo con devolucion en efectivo")
        antes = D(turno(c)["total_efectivo_final"])
        p = crear(c, CAJA)
        cocinar(c, p["id"])
        r = cobrar(c, p["id"])
        pago_id = r.json()["pagos"][0]["id"]
        tras_venta = D(turno(c)["total_efectivo_final"])
        ok("3a. la venta en efectivo sube el efectivo esperado", tras_venta == antes + D(18900), f"{antes}->{tras_venta}")
        r = c.post(f"/caja/pagos/{pago_id}/devolver", json={"motivo": "cliente se arrepintio"}, headers=H(CAJA))
        ok("3b. devolucion aceptada", r.status_code == 200, f"HTTP {r.status_code}")
        tras_dev = D(turno(c)["total_efectivo_final"])
        ok("3c. tras devolver, el efectivo esperado vuelve al valor anterior", tras_dev == antes, f"esperado {antes}, dio {tras_dev}")

        print("\n[4] Cancelar pedido pagado con tarjeta / vale")
        t0 = turno(c)
        p = crear(c, CAJA)
        cocinar(c, p["id"])
        cobrar(c, p["id"], "TARJETA")
        r = c.post(f"/pedidos/{p['id']}/cancelar", json={"motivo": "prueba cancelacion tarjeta"}, headers=H(ADMIN))
        t1 = turno(c)
        ok("4a. cancelacion aceptada", r.status_code == 200, f"HTTP {r.status_code}")
        ok("4b. cancelar pago con tarjeta no saca efectivo de la gaveta",
           D(t1["total_efectivo_final"]) == D(t0["total_efectivo_final"]),
           f"{t0['total_efectivo_final']}->{t1['total_efectivo_final']}")
        p = crear(c, CAJA)
        cocinar(c, p["id"])
        cobrar(c, p["id"], "VALE", vale_cliente_nombre="Cliente Prueba")
        c.post(f"/pedidos/{p['id']}/cancelar", json={"motivo": "prueba cancelacion vale"}, headers=H(ADMIN))
        pend = sql("select count(*) from vale where pedido_id=:p and estado='PENDIENTE'", p=p["id"])[0][0]
        ok("4c. cancelar un pedido con vale no deja deuda pendiente", pend == 0, f"vales pendientes={pend}")

        print("\n[5] Devolver un pago hecho con vale")
        p = crear(c, CAJA)
        cocinar(c, p["id"])
        r = cobrar(c, p["id"], "VALE", vale_cliente_nombre="Cliente Prueba 2")
        pago_id = r.json()["pagos"][0]["id"]
        r = c.post(f"/caja/pagos/{pago_id}/devolver", json={"motivo": "error de digitacion"}, headers=H(CAJA))
        ok("5a. se puede devolver un pago con vale", r.status_code == 200, f"HTTP {r.status_code} {r.text[:100]}")
        pend = sql("select count(*) from vale where pedido_id=:p and estado='PENDIENTE'", p=p["id"])[0][0]
        ok("5b. el vale deja de estar pendiente", pend == 0, f"vales pendientes={pend}")

        print("\n[6] Cocina cancela un item")
        p = crear(c, MESERO, "MESA", mesa_id=1, lineas=[{"producto_id": HAMB, "cantidad": 1}, {"producto_id": PAPAS, "cantidad": 1}])
        det_papas = next(d for d in p["detalles"] if d["producto_id"] == PAPAS)
        r = c.post(f"/cocina/detalles/{det_papas['id']}/cancelar", headers=H(COCINA))
        ok("6a. cocina cancela el item", r.status_code == 200, f"HTTP {r.status_code}")
        ok("6b. el total baja al cancelar", D(pedido(c, p["id"])["total"]) == D(18900), f"total={pedido(c, p['id'])['total']}")
        r = c.post(f"/pedidos/{p['id']}/rondas", headers=H(MESERO), json={"ronda": 2, "lineas": [{"producto_id": GASEOSA, "cantidad": 1}]})
        ok("6c. una ronda nueva no vuelve a sumar lo cancelado", D(r.json()["total"]) == D(18900 + 5500), f"total={r.json().get('total')}")
        cocinar(c, p["id"])
        ok("6d. se cobra el total correcto", cobrar(c, p["id"]).status_code == 200)
        mesa = sql("select estado from mesa where id=1")[0][0]
        ok("6e. la mesa queda libre", mesa == "DISPONIBLE", mesa)

        p = crear(c, MESERO, "MESA", mesa_id=2, lineas=[{"producto_id": PAPAS, "cantidad": 1}])
        c.post(f"/cocina/detalles/{p['detalles'][0]['id']}/cancelar", headers=H(COCINA))
        pf = pedido(c, p["id"])
        mesa = sql("select estado from mesa where id=2")[0][0]
        ok("6f. si cocina cancela todo, el pedido se cierra y libera la mesa",
           pf["estado"] == "CANCELADO" and mesa == "DISPONIBLE", f"pedido={pf['estado']} mesa={mesa}")

        print("\n[7] Entregar pedido de mesa ya pagado")
        p = crear(c, MESERO, "MESA", mesa_id=3)
        cobrar(c, p["id"])            # paga por adelantado en mesa
        r = c.post(f"/pedidos/{p['id']}/entregar", headers=H(MESERO))
        ok("7a. entregar no produce error 500", r.status_code == 200, f"HTTP {r.status_code}")
        pf = pedido(c, p["id"])
        mesa = sql("select estado from mesa where id=3")[0][0]
        ok("7b. pedido prepagado y entregado queda PAGADO con mesa libre",
           pf["estado"] == "PAGADO" and mesa == "DISPONIBLE", f"pedido={pf['estado']} mesa={mesa}")
        movs = sql("select count(*) from movimiento_inventario where pedido_id=:p", p=p["id"])[0][0]
        ok("7c. y su inventario se descuenta aunque cocina no lo marcara", movs > 0, f"movimientos={movs}")
        ok("7d. ya no aparece en la cola de cocina", not en_cola(c, p["id"]))

        print("\n[8] Preparado en pedido para llevar")
        a = crear(c, CAJA)
        cocinar(c, a["id"], listo=False)
        c.post(f"/pedidos/{a['id']}/cancelar", json={"motivo": "cliente se fue"}, headers=H(ADMIN))
        prep = sql("select id from preparado where pedido_origen_id=:p and estado='DISPONIBLE'", p=a["id"])
        ok("8a. cancelar algo ya cocinado crea un preparado", len(prep) == 1)
        b = crear(c, CAJA, tipo_consumo="LLEVAR", lineas=[{"producto_id": PAPAS, "cantidad": 1}])
        rec_antes = D(b["recargo_empaque"])
        r = c.post(f"/preparados/{prep[0][0]}/asignar", json={"pedido_id": b["id"]}, headers=H(CAJA))
        bf = pedido(c, b["id"])
        ok("8b. preparado asignado", r.status_code == 200, f"HTTP {r.status_code}")
        ok("8c. el pedido para llevar conserva el cobro de empaque",
           rec_antes > 0 and D(bf["recargo_empaque"]) == rec_antes * 2
           and D(bf["total"]) == D(12000 + 18900) + D(bf["recargo_empaque"]),
           f"total={bf['total']} recargo={bf['recargo_empaque']} (antes {rec_antes})")

        print("\n[10] Merma de un plato completo")
        pan0, carne0 = stock(21), stock(10)
        r = c.post("/ingredientes/merma", headers=H(CAJA), json={"producto_id": HAMB, "cantidad": 2, "motivo": "se cayeron al piso"})
        ok("10a. se registra la merma de un plato", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
        ok("10b. descuenta la receta completa por la cantidad dañada", stock(21) == pan0 - 2 and stock(10) == carne0 - 250, f"pan {pan0}->{stock(21)} carne {carne0}->{stock(10)}")
        tipos = sql("select distinct tipo from movimiento_inventario where referencia like 'Merma plato:%'")
        ok("10c. queda en el kardex como MERMA", tipos == [("MERMA",)], str(tipos))
        r = c.post("/ingredientes/merma", headers=H(CAJA), json={"ingrediente_id": 21, "cantidad": 3, "motivo": "pan vencido"})
        ok("10d. merma de un insumo suelto", r.status_code == 201 and stock(21) == pan0 - 5, f"pan={stock(21)}")

        print("\n[11] Ronda reenviada por Wi-Fi inestable")
        p = crear(c, MESERO, "MESA", mesa_id=4)
        ronda = {"ronda": 2, "idempotency_key": "ronda-prueba-001", "lineas": [{"producto_id": GASEOSA, "cantidad": 2}]}
        r1 = c.post(f"/pedidos/{p['id']}/rondas", headers=H(MESERO), json=ronda)
        r2 = c.post(f"/pedidos/{p['id']}/rondas", headers=H(MESERO), json=ronda)
        lineas = sql("select count(*) from detalle_pedido where pedido_id=:p and ronda=2", p=p["id"])[0][0]
        ok("11a. el reintento responde bien", r1.status_code == 201 and r2.status_code in (200, 201), f"{r1.status_code}/{r2.status_code}")
        ok("11b. la ronda no se duplica", lineas == 1 and D(pedido(c, p["id"])["total"]) == D(18900 + 11000), f"lineas={lineas} total={pedido(c, p['id'])['total']}")
        cocinar(c, p["id"])
        cobrar(c, p["id"])

        print("\n[12] Compra a proveedor")
        s0 = stock(21)
        r = c.post("/admin/compras", headers=H(ADMIN), json={"descripcion": "Pan de prueba", "detalles": [{"ingrediente_id": 21, "cantidad": 50, "costo_unitario": 800}]})
        ok("12a. se registra la compra", r.status_code in (200, 201), f"HTTP {r.status_code} {r.text[:120]}")
        mov = sql("select unidad, saldo_anterior, saldo_nuevo, costo_unitario_momento from movimiento_inventario where tipo='COMPRA' order by id desc limit 1")
        ok("12b. el kardex guarda unidad, saldos y costo", bool(mov) and mov[0][0] is not None and D(mov[0][1]) == s0 and D(mov[0][2]) == s0 + 50 and D(mov[0][3]) == D(800), str(mov))

        print("\n[13] El cajero ingresa facturas de proveedor (orden del dueño)")
        s0 = stock(22)
        r = c.post("/admin/compras", headers=H(CAJA), json={"descripcion": "Proveedor: Panadería. #Factura: 77", "detalles": [{"ingrediente_id": 22, "cantidad": 30, "costo_unitario": 900}]})
        ok("13a. el cajero registra la compra", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}")
        ok("13b. suben las existencias", stock(22) == s0 + 30, f"{s0} -> {stock(22)}")
        mov = sql("select usuario_id, tipo, cantidad from movimiento_inventario where ingrediente_id=22 order by id desc limit 1")
        ok("13c. el kardex dice quién la ingresó", bool(mov) and mov[0][0] == CAJA and mov[0][1] == "COMPRA" and D(mov[0][2]) == 30, str(mov))
        r = c.get("/admin/compras", headers=H(CAJA))
        ok("13d. el cajero ve las facturas ingresadas", r.status_code == 200 and len(r.json()) >= 2, f"HTTP {r.status_code}")
        r = c.get("/ingredientes/para-caja", headers=H(CAJA))
        lista = r.json() if r.status_code == 200 else []
        ok("13e. el cajero recibe la lista corta de insumos, sin costos",
           r.status_code == 200 and len(lista) > 20 and "costo_unitario" not in lista[0] and "precio_venta" not in lista[0], f"HTTP {r.status_code}")
        ok("13f. el inventario completo sigue siendo solo del admin", c.get("/ingredientes", headers=H(CAJA)).status_code == 403)
        r_mes = c.post("/admin/compras", headers=H(MESERO), json={"detalles": [{"ingrediente_id": 22, "cantidad": 1, "costo_unitario": 1}]})
        r_coc = c.post("/admin/compras", headers=H(COCINA), json={"detalles": [{"ingrediente_id": 22, "cantidad": 1, "costo_unitario": 1}]})
        ok("13g. mesero y cocina no pueden ingresar compras", r_mes.status_code == 403 and r_coc.status_code == 403, f"{r_mes.status_code}/{r_coc.status_code}")
        ok("13h. el resto de administración sigue cerrado al cajero",
           all(c.get(u, headers=H(CAJA)).status_code == 403 for u in ("/admin/dashboard", "/admin/usuarios", "/admin/auditoria", "/admin/stock-critico")))
        r = c.post("/admin/compras", headers=H(CAJA), json={"detalles": [{"ingrediente_id": 22, "cantidad": -5, "costo_unitario": 1}]})
        ok("13i. una cantidad negativa se rechaza", r.status_code == 422 and stock(22) == s0 + 30, f"HTTP {r.status_code}")

        print("\n[9] Reiniciar el backend no revierte ajustes del admin")
        sql("update ingrediente set precio_venta=400, costo_unitario=123 where id=61")
        sql("update configuracion set valor='BLOQUEAR' where clave='politica_stock_insuficiente'")
        sql("update producto set activo=true where id=1")

    with TestClient(app, raise_server_exceptions=False):
        pass  # segundo arranque: vuelve a ejecutar las migraciones de inicio
    pv, cu = sql("select precio_venta, costo_unitario from ingrediente where id=61")[0]
    pol = sql("select valor from configuracion where clave='politica_stock_insuficiente'")[0][0]
    act = sql("select activo from producto where id=1")[0][0]
    ok("9a. el precio del empaque C1 se conserva", D(pv) == D(400) and D(cu) == D(123), f"precio={pv} costo={cu}")
    ok("9b. la politica de stock se conserva", pol == "BLOQUEAR", pol)
    ok("9c. un producto reactivado por el admin sigue activo", act is True, str(act))
    dup = sql("select count(*) from ingrediente where nombre='P1 (Porta Perro Caliente)'")[0][0]
    ok("9d. no se duplica el insumo P1", dup == 1, f"hay {dup}")

    fallas = [r for r in resultados if not r[1]]
    print(f"\nRESULTADO: {len(resultados) - len(fallas)} pasan, {len(fallas)} fallan de {len(resultados)}")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
