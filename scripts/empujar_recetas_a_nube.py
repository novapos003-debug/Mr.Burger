"""
Script para empujar todas las recetas locales existentes a la nube (Render).
Útil tras actualizar la aplicación para garantizar que cualquier receta que Don Félix
haya configurado previamente en la base de datos local quede 100% reflejada en la nube.
"""
import os
import sys
import json
import urllib.request
import urllib.parse

# Añadir backend al path para poder usar los modelos
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models import DetalleReceta, Producto

RENDER_URL = "https://mrburger-api.onrender.com"

def http_req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            res_body = resp.read().decode("utf-8")
            try:
                return status, json.loads(res_body)
            except:
                return status, res_body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, err_body
    except Exception as e:
        return 0, str(e)

def main():
    print("==================================================")
    print(" Sincronizador de Recetas Locales -> Nube (Render)")
    print("==================================================")
    
    print("\n1. Autenticando con la nube...")
    login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
    status, res = http_req(
        f"{RENDER_URL}/api/auth/login",
        method="POST",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if status != 200:
        print(f"Error autenticando con la nube: {status} {res}")
        return
    token = res["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Conexión con la nube autenticada correctamente.")

    print("\n2. Leyendo recetas de la base de datos local...")
    db = SessionLocal()
    try:
        productos = db.query(Producto).all()
        total_subidas = 0
        total_lineas = 0

        for p in productos:
            lineas = db.query(DetalleReceta).filter(DetalleReceta.product_id == p.id).all()
            if not lineas:
                continue
            
            payload = [
                {
                    "ingrediente_id": l.ingrediente_id,
                    "cantidad": float(l.cantidad),
                    "unidad": l.unidad,
                    "solo_llevar": l.solo_llevar or False,
                }
                for l in lineas
            ]

            status_rec, res_rec = http_req(
                f"{RENDER_URL}/api/ingredientes/productos/{p.id}/receta",
                method="PUT",
                data=payload,
                headers=headers
            )
            if status_rec in (200, 201):
                total_subidas += 1
                total_lineas += len(lineas)
                print(f"  [OK] Producto #{p.id} ({p.nombre}): {len(lineas)} insumos sincronizados.")
            else:
                print(f"  [WARN] Producto #{p.id} ({p.nombre}) no sincronizó: HTTP {status_rec} - {res_rec}")

        print(f"\n==================================================")
        print(f" ¡Listo! Se subieron {total_subidas} recetas ({total_lineas} insumos) a la nube exitosamente.")
        print(f"==================================================")
    finally:
        db.close()

if __name__ == "__main__":
    main()
