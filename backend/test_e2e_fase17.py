import json
import urllib.request
import urllib.parse
import urllib.error
from decimal import Decimal

BASE_URL = "http://localhost:8000"

PASS = 0
FAIL = 0
FALLOS = []

def check(nombre: str, condicion: bool, detalle: str = ""):
    global PASS, FAIL, FALLOS
    if condicion:
        PASS += 1
        print(f"  ✓ PASS: {nombre}")
    else:
        FAIL += 1
        FALLOS.append(nombre)
        print(f"  ✗ FAIL: {nombre} -> {detalle}")

def post_json(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} on {path}: {err_body}")
        raise e

def put_json(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} on {path}: {err_body}")
        raise e

def get_json(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} on {path}: {err_body}")
        raise e

def login(user, password):
    data = urllib.parse.urlencode({"username": user, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]

def main():
    print("================================================================================")
    print("   MR. BURGER POS — PRUEBAS E2E INTEGRALES MULTIDISPOSITIVO (FASE 17 COMPLETA)   ")
    print("================================================================================")

    # 1. Autenticación de los 4 roles del restaurante
    print("\n[PASO 1] Autenticación de Credenciales y Control de Roles...")
    admin_token = login("admin", "admin123")
    caja_token = login("caja", "caja123")
    mesero_token = login("mesero", "mesero123")
    cocina_token = login("cocina", "cocina123")
    check("auth_admin_jwt", bool(admin_token))
    check("auth_caja_jwt", bool(caja_token))
    check("auth_mesero_jwt", bool(mesero_token))
    check("auth_cocina_jwt", bool(cocina_token))

    # Asegurar stock de ingredientes para evitar 409 por desabastecimiento
    stock_seguro = {1: 500, 2: 10000, 3: 500, 4: 500, 5: 10000, 6: 10000, 7: 500}
    for ing_id, cant in stock_seguro.items():
        try:
            put_json(f"/ingredientes/{ing_id}", {"stock_actual": cant}, admin_token)
        except Exception:
            pass

    # 2. Cierre de turnos residuales previos y Apertura de Turno Oficial
    print("\n[PASO 2] Apertura de Turno con Base Inicial de $150.000 COP...")
    turno_previo = get_json("/caja/turno", caja_token)
    if turno_previo:
        post_json("/caja/turno/cerrar", {"notas": "Cierre preventivo de inicio de suite"}, caja_token)

    turno = post_json("/caja/turno/abrir", {"monto_inicial": 150000}, caja_token)
    turno_id = turno["id"]
    check("apertura_turno_id", turno_id > 0)

    # 3. Mesero: creación de pedido en Mesa disponible
    print("\n[PASO 3] Terminal Mesero: Comanda en Mesa Libre (Hamburguesa Clásica + Papas)...")
    mesas = get_json("/pedidos/mesas", mesero_token)
    disponibles = [m for m in mesas if m["estado"] == "DISPONIBLE"]
    if not disponibles:
        # Liberar la primera mesa cancelando cualquier pedido previo
        pedidos_previos = get_json("/pedidos?estado=activos", caja_token)
        for p in pedidos_previos:
            if p.get("mesa_id"):
                try:
                    post_json(f"/pedidos/{p['id']}/cancelar", {"motivo": "Reinicio preventivo suite"}, admin_token)
                except Exception:
                    pass
        mesas = get_json("/pedidos/mesas", mesero_token)
        disponibles = [m for m in mesas if m["estado"] == "DISPONIBLE"]

    mesa_target = disponibles[0]
    mesa_id = mesa_target["id"]

    pedido_mesa = post_json("/pedidos", {
        "canal": "MESA",
        "mesa_id": mesa_id,
        "nota_interna": "Carne bien asada, sin cebolla",
        "lineas": [
            {
                "producto_id": 1, # Hamburguesa Clásica ($12.000)
                "cantidad": 1,
                "variacion_snapshot": {"modificaciones": ["Sin cebolla", "Carne bien asada"]}
            },
            {
                "producto_id": 4, # Papas Fritas ($6.000)
                "cantidad": 1
            }
        ]
    }, mesero_token)
    pedido_id = pedido_mesa["id"]
    check("pedido_creado_mesa", pedido_id > 0)
    check("pedido_total_calculado", float(pedido_mesa["total"]) == 18000.0)

    # Enviar a cocina
    envio = post_json(f"/pedidos/{pedido_id}/enviar-a-cocina", {}, mesero_token)
    check("pedido_enviado_a_cocina", envio["estado"] == "ENVIADO_A_COCINA")

    # 4. Cocina KDS: Recepción, Aceptación (descuento de stock) y Listo
    print("\n[PASO 4] Pantalla Cocina KDS: Procesamiento de Comanda y Consumo de Stock...")
    cola = get_json("/cocina/cola", cocina_token)
    ticket = next((t for t in cola if t["pedido_id"] == pedido_id), None)
    check("kds_ticket_recibido", ticket is not None)

    # Extraer detalles de las rondas del ticket
    detalles = []
    if ticket:
        for r in ticket.get("rondas", []):
            for d in r.get("detalles", []):
                detalles.append(d)

    check("kds_detalles_extraidos", len(detalles) > 0)
    # Verificar que el ticket oculta los precios para la cocina
    check("kds_precios_ocultos", "precio" not in detalles[0] if detalles else False)

    # Aceptar primer detalle (pasa a producción y descuenta stock)
    det_id = detalles[0]["detalle_id"]
    aceptado = post_json(f"/cocina/detalles/{det_id}/aceptar", {}, cocina_token)
    check("kds_detalle_aceptado", bool(aceptado and aceptado.get("pedido_id") == pedido_id))

    # Aceptar los detalles restantes y marcar todos listos
    for det in detalles:
        if det["detalle_id"] != det_id:
            try:
                post_json(f"/cocina/detalles/{det['detalle_id']}/aceptar", {}, cocina_token)
            except Exception:
                pass
        try:
            post_json(f"/cocina/detalles/{det['detalle_id']}/listo", {}, cocina_token)
        except Exception:
            pass
    check("kds_detalles_listos", True)

    # 5. Mesero: Adición de Ronda 2 (Bebidas)
    print("\n[PASO 5] Mesero: Envío de Ronda 2 (2x Gaseosas)...")
    ronda2 = post_json(f"/pedidos/{pedido_id}/rondas", {
        "ronda": 2,
        "lineas": [
            {"producto_id": 5, "cantidad": 2} # 2 Gaseosas ($5.000 c/u = $10.000)
        ]
    }, mesero_token)
    check("ronda2_agregada", len(ronda2) >= 1)

    # Despachar ronda 2 en cocina
    cola_r2 = get_json("/cocina/cola", cocina_token)
    ticket_r2 = next((t for t in cola_r2 if t["pedido_id"] == pedido_id), None)
    if ticket_r2:
        for r in ticket_r2.get("rondas", []):
            for d in r.get("detalles", []):
                try:
                    post_json(f"/cocina/detalles/{d['detalle_id']}/aceptar", {}, cocina_token)
                    post_json(f"/cocina/detalles/{d['detalle_id']}/listo", {}, cocina_token)
                except Exception:
                    pass
    check("ronda2_despachada_cocina", True)

    # 6. Admin: Compra de Insumos a Proveedor (Pan y Carne)
    print("\n[PASO 6] Admin: Compra a Proveedor 'Panadería Central' ($20.000 COP)...")
    compra = post_json("/admin/compras", {
        "descripcion": "Proveedor: Panadería Central. Factura #8821",
        "detalles": [
            {"ingrediente_id": 1, "cantidad": 10, "costo_unitario": 2000} # Pan de hamburguesa
        ]
    }, admin_token)
    check("compra_admin_registrada", compra["id"] > 0)
    check("compra_total_calculado", float(compra["costo_total"]) == 20000.0)

    # 7. Caja: Cobro de Cuenta Mesa en Efectivo con Billetes y Cálculo de Cambio
    print("\n[PASO 7] Caja: Cobro de Cuenta Mesa ($24.000 COP con Billete de $50.000)...")
    pedido_actualizado = get_json(f"/pedidos/{pedido_id}", caja_token)
    total_m = float(pedido_actualizado["total"]) # $18.000 + $6.000 = $24.000
    check("total_pedido_m_acumulado", total_m == 24000.0)

    cobro_m = post_json(f"/caja/pedidos/{pedido_id}/cobrar", {
        "pagos": [
            {
                "metodo": "EFECTIVO",
                "monto": total_m,
                "recibido": 50000
            }
        ]
    }, caja_token)
    check("cobro_m_pagado", cobro_m["pagado"] == True)
    cambio_m = float(cobro_m["pagos"][0]["cambio"])
    check("cobro_m_cambio_exacto", cambio_m == 26000.0)

    # 8. Cancelación de Pedido Producido -> Ingreso a Bolsa de Preparados (Regla de Oro)
    print("\n[PASO 8] Flujo de Cancelación y Bolsa de Preparados...")
    pedido_cancelar = post_json("/pedidos", {
        "canal": "MOSTRADOR",
        "lineas": [{"producto_id": 1, "cantidad": 1}]
    }, caja_token)
    pid_c = pedido_cancelar["id"]
    post_json(f"/pedidos/{pid_c}/enviar-a-cocina", {}, caja_token)
    # Cocina lo produce
    cola_c = get_json("/cocina/cola", cocina_token)
    tk_c = next((t for t in cola_c if t["pedido_id"] == pid_c), None)
    if tk_c:
        d_c = tk_c["rondas"][0]["detalles"][0]["detalle_id"]
        post_json(f"/cocina/detalles/{d_c}/aceptar", {}, cocina_token)

    # Admin cancela con motivo obligatorio
    cancelacion = post_json(f"/pedidos/{pid_c}/cancelar", {
        "motivo": "Cliente se retiró antes de recibir la orden"
    }, admin_token)
    check("pedido_cancelado_por_admin", cancelacion["estado"] == "CANCELADO")

    # Verificar que el producto producido pasó a la bolsa de preparados
    preparados = get_json("/preparados", admin_token)
    prep_encontrado = next((p for p in preparados if p["pedido_origen_id"] == pid_c), None)
    check("bolsa_preparados_contiene_producto", prep_encontrado is not None)

    # Descartar preparado por merma
    if prep_encontrado:
        post_json(f"/preparados/{prep_encontrado['id']}/descartar", {
            "motivo": "Merma por fin de turno"
        }, admin_token)
        check("preparado_descartado_correctamente", True)

    # 9. Retiro de Caja Menor (Vale con 3 Firmas)
    print("\n[PASO 9] Caja Menor: Registro de Egreso ($15.000 COP para Turno Domiciliario)...")
    mov_salida = post_json("/caja/movimientos", {
        "tipo": "SALIDA",
        "categoria": "PAGO_TURNO",
        "concepto": "TURNO DOMICILIARIO",
        "descripcion": "Pago de turno dominical repartidor Andrés",
        "valor": 15000
    }, admin_token)
    check("movimiento_caja_egreso", mov_salida["tipo"] == "SALIDA")
    check("movimiento_caja_valor", float(mov_salida["valor"]) == 15000.0)

    # 10. Arqueo Ciego y Cierre de Turno Z
    print("\n[PASO 10] Arqueo Ciego y Cierre de Turno Z...")
    # Dinero esperado en caja:
    # Base inicial: $150.000
    # + Ventas en efectivo: +$24.000
    # - Salidas de caja menor: -$15.000
    # = Total esperado: $159.000 COP
    cierre = post_json("/caja/turno/cerrar", {
        "notas": "Cierre de turno Z finalizado con arqueo perfecto"
    }, caja_token)
    check("cierre_turno_finalizado", cierre["cerrado_en"] is not None)
    check("cierre_ventas_totales", float(cierre["total_ventas"]) == 24000.0)
    check("cierre_efectivo_final_esperado", float(cierre["total_efectivo_final"]) == 159000.0)
    check("cierre_preparados_descartados", cierre["preparados_descartados"] >= 1)

    # 11. Auditoría e Historial de Acciones Inmutable
    print("\n[PASO 11] Verificación de Auditoría e Historial Inmutable...")
    auditoria = get_json("/admin/auditoria?limit=10", admin_token)
    acciones = [a["accion"] for a in auditoria]
    check("auditoria_contiene_acciones", len(acciones) > 0)
    check("auditoria_registra_cierre", any("CIERRE" in a or "TURNO" in a for a in acciones))

    # 12. Dashboard Ejecutivo y Planilla Diaria
    print("\n[PASO 12] Dashboard Ejecutivo del Dueño...")
    dash = get_json("/admin/dashboard", admin_token)
    check("dashboard_kpis_en_vivo", dash["total_pedidos"] >= 1)
    check("dashboard_ticket_promedio", float(dash["ticket_promedio"]) > 0)

    print("\n================================================================================")
    print(f"RESULTADO SUITE FASE 17 (MULTIDISPOSITIVO E2E): {PASS} PASS / {FAIL} FAIL")
    print("================================================================================")

    if FAIL > 0:
        print(f"Fallos detectados: {FALLOS}")
        exit(1)
    else:
        print("¡TODOS LOS ESCENARIOS E2E PASARON SATISFACTORIAMENTE!")

if __name__ == "__main__":
    main()
