import re
import urllib.request
import urllib.parse
import json

RENDER_URL = "https://mrburger-api.onrender.com"
SQL_FILE = "C:/Users/jhona/Downloads/mrburger/mrburger/database/backup_restaurante_completo.sql"

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

def main():
    print("1. Autenticando en Render API...")
    login_data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
    status, res = http_req(
        f"{RENDER_URL}/api/auth/login",
        method="POST",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if status != 200:
        print(f"Error login: {status} {res}")
        return
    token = res["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Autenticado exitosamente como admin en Render!")

    # Parse SQL file
    print("2. Leyendo y parseando backup_restaurante_completo.sql...")
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse categoria_insumo
    cat_insumos = []
    cat_match = re.search(r"COPY public\.categoria_insumo \((.*?)\) FROM stdin;\n(.*?)\\\.", content, re.DOTALL)
    if cat_match:
        for line in cat_match.group(2).strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 4:
                cat_insumos.append({
                    "id": int(parts[0]),
                    "nombre": parts[1],
                    "descripcion": parts[2] if parts[2] != "\\N" else None,
                    "activo": parts[3] == "t"
                })
        print(f"Categorías de insumos encontradas en local: {len(cat_insumos)}")

    # Parse ingrediente
    ingredientes = []
    ing_match = re.search(r"COPY public\.ingrediente \((.*?)\) FROM stdin;\n(.*?)\\\.", content, re.DOTALL)
    if ing_match:
        cols = [c.strip() for c in ing_match.group(1).split(",")]
        for line in ing_match.group(2).strip().split("\n"):
            parts = line.split("\t")
            if len(parts) == len(cols):
                row = dict(zip(cols, parts))
                ingredientes.append({
                    "id": int(row["id"]),
                    "categoria_insumo_id": int(row["categoria_insumo_id"]) if row["categoria_insumo_id"] != "\\N" else None,
                    "nombre": row["nombre"],
                    "unidad_base": row["unidad_base"],
                    "costo_unitario": float(row["costo_unitario"]) if row["costo_unitario"] != "\\N" else 0.0,
                    "stock_actual": float(row["stock_actual"]) if row["stock_actual"] != "\\N" else 0.0,
                    "stock_minimo": float(row["stock_minimo"]) if row["stock_minimo"] != "\\N" else 0.0,
                    "activo": row["activo"] == "t",
                    "tipo_articulo": row.get("tipo_articulo", "INSUMO_RECETA"),
                    "precio_venta": float(row.get("precio_venta", "0")) if row.get("precio_venta") != "\\N" else 0.0,
                })
        print(f"Ingredientes/Insumos encontrados en local: {len(ingredientes)}")

    # Parse detalle_receta
    recetas_por_prod = {}
    rec_match = re.search(r"COPY public\.detalle_receta \((.*?)\) FROM stdin;\n(.*?)\\\.", content, re.DOTALL)
    if rec_match:
        for line in rec_match.group(2).strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 6:
                p_id = int(parts[1])
                linea = {
                    "ingrediente_id": int(parts[2]),
                    "cantidad": float(parts[3]),
                    "unidad": parts[4],
                    "solo_llevar": parts[5] == "t"
                }
                recetas_por_prod.setdefault(p_id, []).append(linea)
        print(f"Productos con recetas encontrados en local: {len(recetas_por_prod)}")

    # Parse usuarios
    usuarios = []
    usr_match = re.search(r"COPY public\.usuario \((.*?)\) FROM stdin;\n(.*?)\\\.", content, re.DOTALL)
    if usr_match:
        for line in usr_match.group(2).strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 6:
                usuarios.append({
                    "id": int(parts[0]),
                    "rol_id": int(parts[1]),
                    "nombre": parts[2],
                    "usuario": parts[3],
                    "activo": parts[5] == "t"
                })
        print(f"Usuarios encontrados en local: {len(usuarios)}")

    # 3. Sincronizar categorías de insumos en Render
    print("\n3. Sincronizando categorías de insumos en Render...")
    _, r_cats = http_req(f"{RENDER_URL}/api/ingredientes/categorias", headers=headers)
    existing_cat_names = {c["nombre"]: c["id"] for c in r_cats} if isinstance(r_cats, list) else {}
    cat_id_map = {}
    for c in cat_insumos:
        if c["nombre"] in existing_cat_names:
            cat_id_map[c["id"]] = existing_cat_names[c["nombre"]]
        else:
            payload = {"nombre": c["nombre"], "descripcion": c["descripcion"]}
            status, res = http_req(f"{RENDER_URL}/api/ingredientes/categorias", method="POST", data=payload, headers=headers)
            if status in (200, 201):
                cat_id_map[c["id"]] = res["id"]
                print(f"  + Creada categoria insumo: {c['nombre']}")

    # 4. Sincronizar ingredientes en Render
    print("\n4. Sincronizando ingredientes y stock en Render...")
    _, r_ings = http_req(f"{RENDER_URL}/api/ingredientes", headers=headers)
    existing_ing_by_id = {i["id"]: i for i in r_ings} if isinstance(r_ings, list) else {}
    existing_ing_by_name = {i["nombre"].lower().strip(): i for i in r_ings} if isinstance(r_ings, list) else {}

    ing_id_map = {}
    for ing in ingredientes:
        target_cat_id = cat_id_map.get(ing["categoria_insumo_id"], ing["categoria_insumo_id"])
        match = existing_ing_by_id.get(ing["id"]) or existing_ing_by_name.get(ing["nombre"].lower().strip())
        
        unidad = ing["unidad_base"].upper()
        if unidad in ("U", "UND", "UNIDADES"): unidad = "UNIDAD"
        elif unidad in ("G", "GR", "GRAMOS"): unidad = "GRAMO"
        elif unidad in ("KG", "KILOGRAMO", "KILOS"): unidad = "KG"
        elif unidad in ("ML", "MILILITROS"): unidad = "MILILITRO"
        elif unidad in ("L", "LT", "LITRO", "LITROS"): unidad = "LITRO"
        elif unidad in ("LONJA", "LONJAS"): unidad = "LONJA"
        elif unidad in ("PORCION", "PORCIONES"): unidad = "PORCION"

        if match:
            real_id = match["id"]
            ing_id_map[ing["id"]] = real_id
            update_payload = {
                "nombre": ing["nombre"],
                "categoria_insumo_id": target_cat_id if target_cat_id else match.get("categoria_insumo_id"),
                "unidad_base": unidad,
                "costo_unitario": ing["costo_unitario"],
                "stock_actual": ing["stock_actual"],
                "stock_minimo": ing["stock_minimo"],
                "activo": ing["activo"],
                "tipo_articulo": ing["tipo_articulo"],
                "precio_venta": ing["precio_venta"]
            }
            status, res = http_req(f"{RENDER_URL}/api/ingredientes/{real_id}", method="PUT", data=update_payload, headers=headers)
            if status == 200:
                print(f"  ~ Actualizado ingrediente {ing['nombre']} (Stock: {ing['stock_actual']})")
            else:
                print(f"  ! Error actualizando ingrediente {ing['nombre']}: {status} {res}")
        else:
            create_payload = {
                "nombre": ing["nombre"],
                "categoria_insumo_id": target_cat_id if target_cat_id else 1,
                "unidad_base": unidad,
                "costo_unitario": ing["costo_unitario"],
                "stock_actual": ing["stock_actual"],
                "stock_minimo": ing["stock_minimo"],
                "activo": ing["activo"],
                "tipo_articulo": ing["tipo_articulo"],
                "precio_venta": ing["precio_venta"]
            }
            status, res = http_req(f"{RENDER_URL}/api/ingredientes", method="POST", data=create_payload, headers=headers)
            if status in (200, 201):
                new_id = res["id"]
                ing_id_map[ing["id"]] = new_id
                print(f"  + Creado nuevo ingrediente en Render: {ing['nombre']} (ID={new_id}, Stock={ing['stock_actual']})")
            else:
                print(f"  ! Error creando ingrediente {ing['nombre']}: {status} {res}")

    # 5. Sincronizar recetas por producto
    print("\n5. Sincronizando recetas en Render...")
    _, r_prods = http_req(f"{RENDER_URL}/api/productos", headers=headers)
    prod_ids = [p["id"] for p in r_prods] if isinstance(r_prods, list) else []

    def map_unit(u):
        u = u.upper()
        if u in ("U", "UND", "UNIDAD", "UNIDADES"): return "UNIDAD"
        if u in ("G", "GR", "GRAMO", "GRAMOS"): return "GRAMO"
        if u in ("KG", "KILOGRAMO", "KILOS"): return "KG"
        if u in ("ML", "MILILITRO", "MILILITROS"): return "MILILITRO"
        if u in ("L", "LT", "LITRO", "LITROS"): return "LITRO"
        if u in ("LONJA", "LONJAS"): return "LONJA"
        if u in ("PORCION", "PORCIONES"): return "PORCION"
        return "UNIDAD"

    for p_id, lineas in recetas_por_prod.items():
        if p_id not in prod_ids:
            continue
        
        clean_lines = []
        seen_ings = set()
        for l in lineas:
            real_ing_id = ing_id_map.get(l["ingrediente_id"], l["ingrediente_id"])
            if real_ing_id in seen_ings:
                continue
            seen_ings.add(real_ing_id)
            clean_lines.append({
                "ingrediente_id": real_ing_id,
                "cantidad": l["cantidad"],
                "unidad": map_unit(l["unidad"]),
                "solo_llevar": l["solo_llevar"]
            })

        status, res = http_req(f"{RENDER_URL}/api/ingredientes/productos/{p_id}/receta", method="PUT", data=clean_lines, headers=headers)
        if status == 200:
            print(f"  OK Receta sincronizada para Producto ID {p_id} ({len(clean_lines)} ingredientes)")
        else:
            print(f"  ! Error sincronizando receta Producto ID {p_id}: {status} {res}")

    # 6. Sincronizar usuarios (omarvelandia, felix123)
    print("\n6. Sincronizando usuarios...")
    status, r_users = http_req(f"{RENDER_URL}/api/admin/usuarios", headers=headers)
    if status == 200:
        existing_usernames = [u["usuario"] for u in r_users]
        for u in usuarios:
            if u["usuario"] not in existing_usernames:
                rol_str = "cajero" if u["rol_id"] == 2 else ("mesero" if u["rol_id"] == 3 else ("cocina" if u["rol_id"] == 4 else "admin"))
                pwd = "123" if u["usuario"] in ("felix123", "omarvelandia") else "admin123"
                payload = {
                    "nombre": u["nombre"],
                    "usuario": u["usuario"],
                    "password": pwd,
                    "rol": rol_str
                }
                st, res = http_req(f"{RENDER_URL}/api/admin/usuarios", method="POST", data=payload, headers=headers)
                if st in (200, 201):
                    print(f"  + Creado usuario en nube: {u['usuario']} (clave inicial: {pwd})")
                else:
                    print(f"  ! Error creando usuario {u['usuario']}: {st} {res}")

    print("\n¡SINCRONIZACIÓN COMPLETA! Todo el catálogo, insumos, cantidades y recetas de la copia local han sido subidos a la Nube (Render/Supabase).")

if __name__ == "__main__":
    main()
