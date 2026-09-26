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
    print("--- INICIANDO PRUEBA E2E KDS COCINA ---")
    mesero_token = login("mesero", "mesero123")
    cocina_token = login("cocina", "cocina123")
    print("1. Tokens autenticados OK")

    # 2. Mesero busca mesa disponible
    mesas = get_json("/pedidos/mesas", mesero_token)
    disponibles = [m for m in mesas if m["estado"] == "DISPONIBLE"]
    mesa_id = disponibles[0]["id"] if disponibles else None

    if mesa_id:
        payload_pedido = {
            "canal": "MESA",
            "mesa_id": mesa_id,
            "nota_interna": "Cliente pide carne bien asada",
            "lineas": [
                {
                    "producto_id": 1,
                    "cantidad": 1,
                    "variacion_snapshot": {
                        "modificaciones": ["Sin cebolla", "Carne bien asada"],
                        "adiciones": [{"id": "adic-1", "nombre": "Tocineta Ahumada", "precio": 3000}]
                    }
                }
            ]
        }
    else:
        payload_pedido = {
            "canal": "MOSTRADOR",
            "nota_interna": "Cliente pide carne bien asada",
            "lineas": [
                {
                    "producto_id": 1,
                    "cantidad": 1,
                    "variacion_snapshot": {
                        "modificaciones": ["Sin cebolla", "Carne bien asada"],
                        "adiciones": [{"id": "adic-1", "nombre": "Tocineta Ahumada", "precio": 3000}]
                    }
                }
            ]
        }
    pedido = post_json("/pedidos", payload_pedido, mesero_token)
    pedido_id = pedido["id"]
    consecutivo = pedido["consecutivo"]
    print(f"2. Pedido #{consecutivo} creado (ID: {pedido_id}) por mesero")

    # 3. Mesero envía comanda a cocina
    pedido_enviado = post_json(f"/pedidos/{pedido_id}/enviar-a-cocina", {}, mesero_token)
    assert pedido_enviado["estado"] == "ENVIADO_A_COCINA"
    print(f"3. Pedido #{consecutivo} enviado a cocina (Estado: {pedido_enviado['estado']})")

    # 4. Cocina consulta la cola de tickets
    cola = get_json("/cocina/cola", cocina_token)
    mi_ticket = next((t for t in cola if t["pedido_id"] == pedido_id), None)
    assert mi_ticket is not None, "El ticket no apareció en la cola de cocina!"
    print(f"4. Ticket encontrado en cola KDS:")
    print(f"   - Consecutivo: #{mi_ticket['consecutivo']}")
    print(f"   - Canal: {mi_ticket['canal']} (Mesa {mi_ticket['mesa_numero']})")
    print(f"   - Nota interna: {mi_ticket['nota_interna']}")
    print(f"   - Rondas: {len(mi_ticket['rondas'])}")
    
    # Verificar regla estricta: Cocina NO ve precios
    assert "precio" not in mi_ticket, "FALLA: Hay campo precio en el ticket de cocina!"
    assert "total" not in mi_ticket, "FALLA: Hay campo total en el ticket de cocina!"

    detalle = mi_ticket["rondas"][0]["detalles"][0]
    detalle_id = detalle["detalle_id"]
    assert detalle["estado"] == "ENVIADO"
    print(f"   - Detalle ID {detalle_id}: {detalle['producto_nombre']} (Estado: {detalle['estado']})")
    print(f"   - Variaciones: {detalle['variacion_snapshot']}")

    # 5. Cocina acepta la comanda (empieza a preparar y descuenta inventario)
    ticket_aceptado = post_json(f"/cocina/detalles/{detalle_id}/aceptar", {}, cocina_token)
    detalle_aceptado = ticket_aceptado["rondas"][0]["detalles"][0]
    assert detalle_aceptado["estado"] == "PREPARANDO", f"Esperado PREPARANDO, obtenido {detalle_aceptado['estado']}"
    print(f"5. Cocina aceptó la comanda:")
    print(f"   - Detalle ID {detalle_id} ahora está en: {detalle_aceptado['estado']}")
    print(f"   - Preparado en: {detalle_aceptado['preparado_en']}")

    # 6. Cocina marca comanda como lista
    ticket_listo = post_json(f"/cocina/detalles/{detalle_id}/listo", {}, cocina_token)
    print(f"6. Cocina marcó listo:")
    print(f"   - Detalle ID {detalle_id} completado con éxito")

    # 7. Verificar estado del pedido en backend
    pedido_final = get_json(f"/pedidos/{pedido_id}", mesero_token)
    assert pedido_final["estado"] == "FINALIZADO", f"Esperado FINALIZADO, obtenido {pedido_final['estado']}"
    print(f"7. Pedido #{consecutivo} pasó automáticamente a: {pedido_final['estado']}")
    print("--- PRUEBA E2E KDS COMPLETADA CON ÉXITO (100% OK) ---")

if __name__ == "__main__":
    main()
