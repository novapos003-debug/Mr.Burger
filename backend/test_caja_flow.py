import json
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

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
    print("--- INICIANDO PRUEBA INTEGRAL CAJA & FINANZAS (SUBFASE 17.4) ---")
    caja_token = login("caja", "caja123")
    admin_token = login("admin", "admin123")
    print("1. Tokens autenticados OK (Caja y Admin)")

    # Verificar si hay turno abierto previo; si lo hay, cerrarlo
    turno_previo = get_json("/caja/turno", caja_token)
    if turno_previo:
        print(f"   Cerrando turno previo #{turno_previo['id']} para prueba limpia...")
        post_json("/caja/turno/cerrar", {"notas": "Cierre previo para test"}, caja_token)

    # 2. Apertura de Turno con base inicial de $100.000 COP
    turno = post_json("/caja/turno/abrir", {"monto_inicial": 100000}, caja_token)
    turno_id = turno["id"]
    print(f"2. Turno #{turno_id} abierto con base de $100.000 COP (OK)")

    # 3. Pedido Mostrador con cobro en Efectivo y cálculo de cambio
    pedido_mostrador = post_json("/pedidos", {
        "canal": "MOSTRADOR",
        "nota_interna": "Para llevar en bolsa",
        "lineas": [
            {"producto_id": 1, "cantidad": 1} # Hamburguesa Clásica ($12.000)
        ]
    }, caja_token)
    p_id = pedido_mostrador["id"]
    p_consecutivo = pedido_mostrador["consecutivo"]
    p_total = float(pedido_mostrador["total"])
    print(f"3. Pedido #{p_consecutivo} creado (Total: ${p_total:,.0f} COP)")

    # Enviar a cocina
    post_json(f"/pedidos/{p_id}/enviar-a-cocina", {}, caja_token)
    print(f"   Pedido #{p_consecutivo} enviado a cocina")

    # Cobro en Efectivo: paga con billete de $20.000 COP
    cobro_efectivo = post_json(f"/caja/pedidos/{p_id}/cobrar", {
        "pagos": [
            {
                "metodo": "EFECTIVO",
                "monto": p_total,
                "recibido": 20000
            }
        ]
    }, caja_token)
    pago_ef = cobro_efectivo["pagos"][0]
    cambio_esperado = 20000 - p_total
    assert float(pago_ef["cambio"]) == cambio_esperado, f"Cambio erróneo: {pago_ef['cambio']} vs {cambio_esperado}"
    print(f"   Cobrado en Efectivo: Recibido $20.000 COP => Cambio devuelto: ${pago_ef['cambio']} COP (OK)")

    # 4. Pedido DiDi Food con cobro por plataforma
    pedido_didi = post_json("/pedidos", {
        "canal": "DIDI",
        "didi_orden_id": "#DIDI-TEST-900",
        "cliente": "Repartidor DiDi Carlos",
        "lineas": [
            {"producto_id": 5, "cantidad": 2} # 2 Gaseosas
        ]
    }, caja_token)
    didi_id = pedido_didi["id"]
    didi_total = float(pedido_didi["total"])
    cobro_didi = post_json(f"/caja/pedidos/{didi_id}/cobrar", {
        "pagos": [
            {
                "metodo": "DIDI_TARJETA",
                "monto": didi_total,
                "didi_orden_id": "#DIDI-TEST-900"
            }
        ]
    }, caja_token)
    assert cobro_didi["pagado"] == True
    print(f"4. Pedido DiDi #{pedido_didi['consecutivo']} cobrado con éxito vía DIDI_TARJETA (OK)")

    # 5. Pedido con Vale (Pagaré a crédito)
    pedido_vale = post_json("/pedidos", {
        "canal": "MOSTRADOR",
        "lineas": [
            {"producto_id": 4, "cantidad": 1} # Papas Fritas ($6.000)
        ]
    }, caja_token)
    vale_pid = pedido_vale["id"]
    vale_total = float(pedido_vale["total"])
    cobro_vale_res = post_json(f"/caja/pedidos/{vale_pid}/cobrar", {
        "pagos": [
            {
                "metodo": "VALE",
                "monto": vale_total,
                "vale_cliente_nombre": "Abraham (Empleado)",
                "vale_cliente_cedula": "1144000111",
                "vale_cliente_telefono": "3109998877"
            }
        ]
    }, caja_token)
    vale_creado = cobro_vale_res["vales"][0]
    vale_id = vale_creado["id"]
    assert vale_creado["estado"] == "PENDIENTE"
    print(f"5. Vale #{vale_id} generado a nombre de '{vale_creado['cliente_nombre']}' por ${float(vale_creado['monto']):,.0f} COP (OK)")

    # 6. Cobro del Vale cuando el cliente paga la deuda
    vale_cobrado = post_json(f"/caja/vales/{vale_id}/cobrar", {"descripcion": "Pago en caja por Abraham"}, caja_token)
    assert vale_cobrado["estado"] == "COBRADO"
    print(f"6. Vale #{vale_id} cobrado y liquidado con éxito (OK)")

    # 7. Movimiento de Caja Menor (Retiro para compra de insumos)
    mov = post_json("/caja/movimientos", {
        "tipo": "SALIDA",
        "categoria": "PROVEEDOR",
        "concepto": "PANADERIA CENTRAL",
        "descripcion": "Compra de 5 paquetes de pan hamburguesa con factura",
        "valor": 15000
    }, admin_token)
    assert mov["tipo"] == "SALIDA"
    print(f"7. Movimiento de Caja Menor Folio #{mov['id']} registrado: SALIDA ${float(mov['valor']):,.0f} COP (OK)")

    # 8. Arqueo y Cierre Z del Turno
    cierre_res = post_json("/caja/turno/cerrar", {
        "notas": "Cierre Z de prueba verificado"
    }, caja_token)
    assert cierre_res["cerrado_en"] is not None
    print("8. Turno cerrado con éxito. Fotograma financiero consolidado:")
    print(f"   - Total Ventas Facturadas: ${float(cierre_res['total_ventas']):,.0f} COP")
    print(f"   - Efectivo en Ventas: ${float(cierre_res['total_efectivo']):,.0f} COP")
    print(f"   - DiDi Tarjeta: ${float(cierre_res['total_didi_tarjeta']):,.0f} COP")
    print(f"   - Vales Recaudados: ${float(cierre_res['total_vale']):,.0f} COP")
    print(f"   - Salidas Caja Menor: -${float(cierre_res['total_salidas_caja']):,.0f} COP")
    print(f"   - Efectivo Final Esperado: ${float(cierre_res['total_efectivo_final']):,.0f} COP")

    # 9. Verificar que el turno ahora está cerrado
    turno_actual = get_json("/caja/turno", caja_token)
    assert turno_actual is None, "El turno no debería figurar como abierto"
    print("9. Estado verificado: Caja cerrada correctamente (OK)")

    print("================================================================")
    print("RESULTADO PRUEBA CAJA & FINANZAS: 100% PASS / 0 FAIL")
    print("================================================================")

if __name__ == "__main__":
    main()
