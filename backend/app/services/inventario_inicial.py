"""Conteo físico del 9 de octubre de 2026 (cierre de la noche, lista de don Félix).

Se aplica UNA sola vez, únicamente en la caja del restaurante, al arrancar la versión que lo trae:

1. Deja en $0 el costo unitario de todos los insumos (pedido del dueño: los volverá a cargar
   desde el panel web). No toca el precio de venta de los empaques.
2. Ajusta las existencias de los insumos de la lista, dejando el movimiento en el kardex.

Reglas de seguridad:
- Un insumo solo se ajusta si se encuentra por su nombre, está activo, no hay otro activo con
  el mismo nombre y su unidad es la esperada. Si algo no cuadra, se omite y queda anotado.
- Los insumos que no están en la lista no cambian de existencias.
- No crea, renombra ni borra insumos.
"""
import logging
import unicodedata
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.core import replicacion
from app.services.migraciones import _una_sola_vez

logger = logging.getLogger(__name__)

CLAVE = "migracion_inventario_20261009"
REFERENCIA = "Conteo físico del 09/10/2026 (cierre)"
_INFORME = Path(__file__).resolve().parents[3] / "inventario_inicial_resultado.txt"

# (nombres aceptados, cantidad contada, unidad esperada). Un nombre terminado en * es un prefijo.
CONTEO: list[tuple[tuple[str, ...], str, str]] = [
    (("pan hamburguesa",), "60", "UNIDAD"),
    (("pan perro",), "4", "UNIDAD"),
    (("pan brillo",), "34", "UNIDAD"),
    (("salchicha ideal",), "22", "UNIDAD"),
    (("salchicha ranchera",), "22", "UNIDAD"),
    (("salchicha suiza",), "21", "UNIDAD"),
    (("salchicha americana",), "30", "UNIDAD"),
    (("queso tajado",), "80", "LONJA"),  # 1 bloque, unas 80 tajadas
    (("tocineta",), "3000", "GRAMO"),
    (("gaseosa 400ml",), "55", "UNIDAD"),
    (("gaseosa litro 1/5", "gaseosa litro 1.5", "gaseosa 1.5 litros"), "31", "UNIDAD"),
    (("coca cola 400ml",), "150", "UNIDAD"),
    (("agua botella", "agua"), "54", "UNIDAD"),
    (("salsa mr burger", "salsa mrburger"), "4000", "MILILITRO"),
    (("chimichurry", "chimichurri"), "4000", "MILILITRO"),
    (("salsa pina dieffer", "pina dieffer", "salsa pina diefer"), "8000", "MILILITRO"),
    (("salsa de tomate", "salsa tomate"), "4000", "MILILITRO"),
    (("mostaza",), "4000", "MILILITRO"),
    (("papa a la francesa", "papas a la francesa"), "3112", "GRAMO"),
    (("mazorcas", "mazorca"), "3", "UNIDAD"),
    (("ripio de papa", "ripio"), "5000", "GRAMO"),
    (("salsa bbq",), "116", "MILILITRO"),
    (("c1*",), "143", "UNIDAD"),
    (("p1*",), "90", "UNIDAD"),
    (("vaso 12oz", "vaso 12 oz"), "27", "UNIDAD"),
    (("vaso grande",), "50", "UNIDAD"),
    (("vaso pequeno",), "100", "UNIDAD"),
    (("servilletas", "servilleta"), "1112", "UNIDAD"),
    (("porta perro",), "100", "UNIDAD"),
    (("copa y tapa", "copas y tapas"), "100", "UNIDAD"),  # 100 copas con sus 100 tapas
    (("rollos impresora termica", "rollo impresora termica", "rollo impresora"), "3", "UNIDAD"),
    (("papel de bano",), "1", "UNIDAD"),
    (("tomate",), "11", "UNIDAD"),
    (("limones", "limon"), "18", "UNIDAD"),
    (("aceite",), "15000", "MILILITRO"),  # 15 litros
    (("limonada de coco*",), "5", "PORCION"),
    (("limpido",), "1", "UNIDAD"),
    (("fabuloso",), "1", "UNIDAD"),
    (("esponjas", "esponja"), "3", "UNIDAD"),  # 2 de alambre + 1 de platos
    # Estos no estaban en el respaldo: se ajustan solo si ya existen en la caja
    (("tapa vaso grande", "tapas vaso grande"), "50", "UNIDAD"),
    (("rollo datafono", "rollos datafono"), "12", "UNIDAD"),
    (("azucar",), "126", "GRAMO"),
    (("sal",), "126", "GRAMO"),
]


# Insumos que se usan "a ojo": salen de las recetas y pasan a gasto operativo (decisión del 10/10/2026)
CLAVE_GASTOS = "migracion_gastos_operativos_20261010"
PASAN_A_GASTO = ("aceite", "mantequilla", "vinagreta")


def pasar_a_gasto_operativo(conn) -> None:
    """Quita de las recetas los insumos de PASAN_A_GASTO y los marca como gasto operativo.
    Se ejecuta una sola vez y solo en la caja. Deja anotado en el informe qué líneas quitó,
    con su cantidad, por si hay que volver a ponerlas."""
    if not _una_sola_vez(conn, CLAVE_GASTOS, "Aceite, mantequilla y vinagreta pasan a gasto operativo"):
        return

    replicar = replicacion.captura_activa()
    informe = ["", "Insumos que pasan a GASTO OPERATIVO (ya no descuentan por receta):"]
    activos = [(f.id, f.nombre, _normalizar(f.nombre)) for f in conn.execute(text("SELECT id, nombre FROM ingrediente WHERE activo"))]

    for alias in PASAN_A_GASTO:
        candidatos = [a for a in activos if a[2] == alias]
        if len(candidatos) != 1:
            motivo = "no existe un insumo activo con ese nombre" if not candidatos else "hay varios con ese nombre"
            informe.append(f"  OMITIDO   {alias}: {motivo}.")
            continue
        ing_id, nombre, _ = candidatos[0]
        lineas = conn.execute(
            text(
                "SELECT d.id, p.nombre, d.cantidad, d.unidad FROM detalle_receta d "
                "JOIN producto p ON p.id = d.product_id WHERE d.ingrediente_id = :i ORDER BY p.nombre"
            ),
            {"i": ing_id},
        ).all()
        for linea in lineas:
            conn.execute(text("DELETE FROM detalle_receta WHERE id = :d"), {"d": linea.id})
            if replicar:
                replicacion.encolar_borrado(conn, "detalle_receta", {"id": linea.id})
            informe.append(f"      quitado de la receta de {linea.nombre}: {Decimal(str(linea.cantidad)).normalize():f} {linea.unidad}")
        conn.execute(
            text(
                "UPDATE ingrediente SET tipo_articulo = 'GASTO_OPERATIVO', "
                "categoria_insumo_id = COALESCE((SELECT id FROM categoria_insumo WHERE id = 10), categoria_insumo_id) "
                "WHERE id = :i"
            ),
            {"i": ing_id},
        )
        if replicar:
            replicacion.encolar_fila(conn, "ingrediente", {"id": ing_id})
        informe.append(f"  GASTO     {nombre}: salió de {len(lineas)} receta(s).")

    logger.warning("Insumos pasados a gasto operativo: %s", ", ".join(PASAN_A_GASTO))
    try:
        with _INFORME.open("a", encoding="utf-8") as f:
            f.write("\n".join(informe) + "\n")
    except OSError:
        pass


def _normalizar(nombre: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre or "") if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.lower().split())


def _coincide(nombre_normalizado: str, alias: str) -> bool:
    if alias.endswith("*"):
        prefijo = alias[:-1]
        resto = nombre_normalizado[len(prefijo):]
        # "c1*" acepta "c1" y "c1 (empaque termico)", pero no "c10"
        return nombre_normalizado.startswith(prefijo) and (not resto or not resto[0].isalnum())
    return nombre_normalizado == alias


def aplicar_conteo_inicial(conn) -> None:
    if not _una_sola_vez(conn, CLAVE, "Conteo físico inicial y costos de insumos en cero"):
        return

    replicar = replicacion.captura_activa()
    informe: list[str] = [REFERENCIA, ""]
    tocados: set[int] = set()

    # 1. Costos en cero (solo el costo; el precio de venta de los empaques no se toca)
    con_costo = [f[0] for f in conn.execute(text("SELECT id FROM ingrediente WHERE COALESCE(costo_unitario, 0) <> 0"))]
    if con_costo:
        conn.execute(text("UPDATE ingrediente SET costo_unitario = 0 WHERE COALESCE(costo_unitario, 0) <> 0"))
        tocados.update(con_costo)
    informe.append(f"Costo unitario puesto en $0 a {len(con_costo)} insumos.")
    informe.append("")

    # 2. Existencias contadas
    usuario_id = conn.execute(
        text(
            "SELECT u.id FROM usuario u JOIN rol r ON r.id = u.rol_id "
            "ORDER BY (lower(r.nombre) = 'admin') DESC, u.activo DESC, u.id LIMIT 1"
        )
    ).scalar()
    activos = [
        (fila.id, fila.nombre, _normalizar(fila.nombre), fila.unidad_base, Decimal(str(fila.stock_actual or 0)))
        for fila in conn.execute(text("SELECT id, nombre, unidad_base, stock_actual FROM ingrediente WHERE activo"))
    ]

    ajustados = omitidos = 0
    for alias, cantidad, unidad in CONTEO:
        candidatos = [a for a in activos if any(_coincide(a[2], al) for al in alias)]
        etiqueta = alias[0].rstrip("*")
        if not candidatos:
            informe.append(f"  OMITIDO   {etiqueta}: no existe un insumo activo con ese nombre.")
            omitidos += 1
            continue
        if len(candidatos) > 1:
            nombres = ", ".join(f"{c[1]} (id {c[0]})" for c in candidatos)
            informe.append(f"  OMITIDO   {etiqueta}: hay varios insumos posibles: {nombres}.")
            omitidos += 1
            continue
        ing_id, nombre, _, unidad_actual, anterior = candidatos[0]
        if (unidad_actual or "").upper() != unidad:
            informe.append(f"  OMITIDO   {nombre}: está en {unidad_actual} y el conteo viene en {unidad}.")
            omitidos += 1
            continue
        nuevo = Decimal(cantidad)
        if nuevo != anterior:
            conn.execute(text("UPDATE ingrediente SET stock_actual = :n WHERE id = :i"), {"n": nuevo, "i": ing_id})
            tocados.add(ing_id)
            if usuario_id is not None:
                mov_id = conn.execute(
                    text(
                        "INSERT INTO movimiento_inventario (ingrediente_id, usuario_id, cantidad, unidad, "
                        "saldo_anterior, saldo_nuevo, costo_unitario_momento, tipo, referencia) "
                        "VALUES (:i, :u, :c, :un, :a, :n, 0, 'AJUSTE', :r) RETURNING id"
                    ),
                    {"i": ing_id, "u": usuario_id, "c": nuevo - anterior, "un": unidad_actual, "a": anterior, "n": nuevo, "r": REFERENCIA},
                ).scalar()
                if replicar:
                    replicacion.encolar_fila(conn, "movimiento_inventario", {"id": mov_id})
        estado = "AJUSTADO " if nuevo != anterior else "YA ESTABA"
        informe.append(f"  {estado} {nombre}: {anterior.normalize():f} -> {nuevo.normalize():f} {unidad_actual}")
        ajustados += 1

    if replicar:
        for ing_id in sorted(tocados):
            replicacion.encolar_fila(conn, "ingrediente", {"id": ing_id})

    informe.insert(3, f"Existencias: {ajustados} insumos ajustados, {omitidos} omitidos.")
    logger.warning("Conteo inicial aplicado: %s ajustados, %s omitidos, %s costos en cero", ajustados, omitidos, len(con_costo))
    try:
        _INFORME.write_text("\n".join(informe) + "\n", encoding="utf-8")
    except OSError:
        pass
