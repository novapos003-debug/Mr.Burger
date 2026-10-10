import urllib.request
import urllib.parse
import json
import ssl

RENDER_URL = "https://mrburger-api.onrender.com"
ctx = ssl.create_default_context()

def http_req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, str):
            body = data.encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_content)
        except:
            return e.code, err_content
    except Exception as e:
        return 0, str(e)

def main():
    print("=== TEST COMPLETO DE ENDPOINTS SYNC EN RENDER ===")
    
    # 1. Health
    st, res = http_req(f"{RENDER_URL}/sync/health")
    print(f"1. /sync/health -> HTTP {st} : {res}")
    
    # 2. Estado
    st, res = http_req(f"{RENDER_URL}/sync/estado", headers={"X-Sync-Token": "mrburger_sync_secret_token_2026"})
    print(f"2. /sync/estado -> HTTP {st} : {res}")

    # 3. Push con payload de prueba idempotente
    test_push = {
        "dispositivo_id": "CAJA_1",
        "operaciones": [
            {
                "op_id": "audit-test-uuid-001",
                "sucursal_id": "SUC-01",
                "dispositivo_id": "CAJA_1",
                "tipo": "CREAR_USUARIO",
                "entidad": "usuario",
                "entidad_id": 9999,
                "payload": {
                    "id": 9999,
                    "nombre": "Test Audit User",
                    "usuario": "test_audit_user",
                    "rol_id": 2,
                    "password_hash": "$2b$12$UR9zR9cwj5ffRV9B9oJdteyUkDG5MKTTuANe8aYzqZ1hv0VO70cc.",
                    "activo": False,
                    "es_demo": True
                },
                "origen": "LOCAL"
            }
        ]
    }
    st, res = http_req(
        f"{RENDER_URL}/sync/push",
        method="POST",
        data=test_push,
        headers={"X-Sync-Token": "mrburger_sync_secret_token_2026"}
    )
    print(f"3. /sync/push -> HTTP {st} : {res}")

    # 4. Pull
    st, res = http_req(
        f"{RENDER_URL}/sync/pull?desde_id=0&limite=10",
        headers={"X-Sync-Token": "mrburger_sync_secret_token_2026"}
    )
    print(f"4. /sync/pull -> HTTP {st} : {len(res.get('operaciones', [])) if isinstance(res, dict) else res} operaciones")

if __name__ == "__main__":
    main()
