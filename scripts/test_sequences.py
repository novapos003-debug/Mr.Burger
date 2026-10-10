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
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                return status, json.loads(content)
            except:
                return status, content
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_content)
        except:
            return e.code, err_content
    except Exception as e:
        return 0, str(e)

def main():
    print("1. Login Admin...")
    login_body = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
    st, res = http_req(
        f"{RENDER_URL}/api/auth/login",
        method="POST",
        data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if st != 200:
        print(f"Error login: {st} {res}")
        return
    token = res["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("\n2. Probando creación de un ingrediente de prueba para verificar secuencias...")
    test_ing = {
        "nombre": "__TEST_SEQUENCE_AUDIT__",
        "unidad_base": "UNIDAD",
        "costo_unitario": 100,
        "stock_minimo": 10,
        "tipo_articulo": "INSUMO_RECETA"
    }
    st_ing, res_ing = http_req(f"{RENDER_URL}/api/ingredientes", method="POST", data=test_ing, headers=headers)
    print(f"Resultado crear ingrediente: HTTP {st_ing} -> {res_ing}")

    if st_ing in (200, 201):
        ing_id = res_ing.get("id")
        print(f"Ingrediente creado con ID: {ing_id}")
        print("Eliminando ingrediente de prueba...")
        st_del, res_del = http_req(f"{RENDER_URL}/api/ingredientes/{ing_id}", method="DELETE", headers=headers)
        print(f"Eliminado: HTTP {st_del}")
    else:
        print("ALERTA: Falló la creación de ingrediente en la nube!")

if __name__ == "__main__":
    main()
