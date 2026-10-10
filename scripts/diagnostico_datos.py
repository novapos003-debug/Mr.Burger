"""Diagnóstico de SOLO LECTURA de la base de datos local de la caja.

No modifica nada. Muestra el estado del catálogo, de los insumos y de la sincronización
para decidir, antes de vincular la caja con la nube, si los datos están limpios.

Uso (desde la carpeta del proyecto):   python scripts/diagnostico_datos.py
"""
import sys

try:
    import psycopg2
except ImportError:
    print("Falta psycopg2. Ejecuta primero actualizar_windows.bat.")
    sys.exit(1)

DSN = dict(host="127.0.0.1", port=5432, dbname="restaurante", user="restaurante", password="restaurante_dev", connect_timeout=5)


def main() -> int:
    try:
        conn = psycopg2.connect(**DSN)
    except Exception as e:
        print(f"No se pudo conectar a la base local: {e}")
        return 1
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor()

    def q(sql):
        cur.execute(sql)
        return cur.fetchall()

    def titulo(t):
        print("\n" + "=" * 64 + f"\n  {t}\n" + "=" * 64)

    titulo("RESUMEN")
    for nombre, sql in (
        ("Productos activos", "select count(*) from producto where activo"),
        ("Productos inactivos", "select count(*) from producto where not activo"),
        ("Insumos activos", "select count(*) from ingrediente where activo"),
        ("Líneas de receta", "select count(*) from detalle_receta"),
        ("Pedidos", "select count(*) from pedido"),
        ("Usuarios", "select count(*) from usuario"),
        ("Turnos de caja abiertos", "select count(*) from cierre where cerrado_en is null"),
    ):
        print(f"  {nombre:28} {q(sql)[0][0]}")

    titulo("INSUMOS CON EL MISMO NOMBRE (posibles duplicados)")
    filas = q("select lower(nombre), string_agg(id::text || case when activo then '' else ' (inactivo)' end, ', ' order by id) "
              "from ingrediente group by 1 having count(*) > 1 order by 1")
    print("  Ninguno." if not filas else "\n".join(f"  {n:34} ids: {ids}" for n, ids in filas))

    titulo("INSUMOS CREADOS AL FINAL (id >= 86): aquí aparecen los que trajo la sincronización vieja")
    for i, nombre, unidad, costo, stock, activo, usos in q(
        "select i.id, i.nombre, i.unidad_base, i.costo_unitario, i.stock_actual, i.activo, "
        "(select count(*) from detalle_receta d where d.ingrediente_id = i.id) from ingrediente i where i.id >= 86 order by i.id"
    ):
        print(f"  {i:>4} {nombre[:32]:32} {unidad:10} costo={costo} stock={stock} {'activo' if activo else 'INACTIVO'} en_recetas={usos}")

    titulo("PRODUCTOS DE PRUEBA O DUPLICADOS")
    filas = q("select id, nombre, activo from producto where nombre ilike '%test%' or nombre ilike '%prueba%' or nombre ilike '%audit%' order by id")
    print("  Ninguno." if not filas else "\n".join(f"  {i:>4} {n} ({'activo' if a else 'inactivo'})" for i, n, a in filas))
    filas = q("select lower(nombre), string_agg(id::text, ', ' order by id) from producto where activo group by 1 having count(*) > 1")
    for n, ids in filas:
        print(f"  DUPLICADO ACTIVO: {n} ids {ids}")

    titulo("RECETAS QUE USAN UN INSUMO INACTIVO")
    filas = q("select p.nombre, i.nombre from detalle_receta d join producto p on p.id = d.product_id "
              "join ingrediente i on i.id = d.ingrediente_id where p.activo and not i.activo order by 1")
    print("  Ninguna." if not filas else "\n".join(f"  {p[:36]:36} -> {i}" for p, i in filas))

    titulo("INSUMOS CON STOCK NEGATIVO O SIN COSTO (en uso)")
    for i, nombre, stock, costo in q(
        "select i.id, i.nombre, i.stock_actual, i.costo_unitario from ingrediente i where i.activo and "
        "(i.stock_actual < 0 or (coalesce(i.costo_unitario, 0) = 0 and exists (select 1 from detalle_receta d where d.ingrediente_id = i.id))) order by i.id"
    ):
        print(f"  {i:>4} {nombre[:34]:34} stock={stock} costo={costo}")

    titulo("COLA DE SINCRONIZACIÓN")
    for tipo, estado, n in q("select tipo, estado, count(*) from registro_sync group by 1, 2 order by 1, 2"):
        print(f"  {tipo:22} {estado:16} {n}")
    for clave, valor in q("select clave, valor from configuracion where clave like 'sync_%' order by 1"):
        print(f"  {clave:28} {valor}")

    print()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
