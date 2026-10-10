import urllib.request
import urllib.parse
import json
import ssl
import time

RENDER_URL = "https://mrburger-api.onrender.com"

ctx = ssl.create_default_context()

def test_req(name, url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, str):
            body = data.encode("utf-8")
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            elapsed = time.time() - t0
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
            except:
                parsed = content[:100]
            print(f"[PASS] {name} ({elapsed:.2f}s) -> HTTP {status}")
            return status, parsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        err_content = e.read().decode("utf-8")
        print(f"[FAIL] {name} ({elapsed:.2f}s) -> HTTP {e.code}: {err_content[:200]}")
        return e.code, err_content
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[ERR]  {name} ({elapsed:.2f}s) -> {e}")
        return 0, str(e)

def main():
    print("=== PROBANDO RENDER & SUPABASE EN VIVO ===")
    test_req("1. Root /", f"{RENDER_URL}/")
    test_req("2. Health /health", f"{RENDER_URL}/health")
    test_req("3. Health /api/health", f"{RENDER_URL}/api/health")
    test_req("4. Sync Health /sync/health", f"{RENDER_URL}/sync/health")
    test_req("5. Sync Health /api/sync/health", f"{RENDER_URL}/api/sync/health")

    print("\n--- Autenticación ---")
    login_body = urllib.parse.urlencode({"username": "admin", "password": "admin123"})
    st, res = test_req("6. Login Admin", f"{RENDER_URL}/api/auth/login", method="POST", data=login_body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if st != 200:
        print("Fallo login admin!")
        return
    token = res["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    print("\n--- Endpoints de Negocio y Catálogo ---")
    test_req("7. GET /api/productos", f"{RENDER_URL}/api/productos", headers=auth_headers)
    test_req("8. GET /api/ingredientes", f"{RENDER_URL}/api/ingredientes", headers=auth_headers)
    test_req("9. GET /api/categorias", f"{RENDER_URL}/api/categorias", headers=auth_headers)
    test_req("10. GET /api/admin/usuarios", f"{RENDER_URL}/api/admin/usuarios", headers=auth_headers)
    test_req("11. GET /api/admin/configuracion", f"{RENDER_URL}/api/admin/configuracion", headers=auth_headers)
    test_req("12. GET /api/pedidos/hoy", f"{RENDER_URL}/api/pedidos/hoy", headers=auth_headers)
    test_req("13. GET /api/caja/resumen-hoy", f"{RENDER_URL}/api/caja/resumen-hoy", headers=auth_headers)
    test_req("14. GET /api/caja/historial", f"{RENDER_URL}/api/caja/historial", headers=auth_headers)
    test_req("15. GET /api/caja/movimientos", f"{RENDER_URL}/api/caja/movimientos", headers=auth_headers)

    print("\n--- Sincronización Push ---")
    sync_headers = {"X-Sync-Token": "mrburger_sync_secret_token_2026", "Content-Type": "application/json"}
    test_req("16. Push Health Check", f"{RENDER_URL}/sync/push", method="POST", data={"dispositivo_id": 1, "operaciones": []}, headers=sync_headers)

if __name__ == "__main__":
    main()
