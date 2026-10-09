"""Migraciones idempotentes ejecutadas al arrancar (lifespan).

- Marcas `fijado` / `es_demo` en usuarios y `es_demo` en tablas transaccionales.
- Etiquetado retroactivo (una sola vez) de lo generado por cuentas demo.
- Empaque de "para llevar" por defecto en platos de cocina que aún no lo tengan (una sola vez).
"""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

TABLAS_TRAZABLES = (
    "pedido",
    "pago",
    "vale",
    "movimiento_caja",
    "cierre",
    "turno_laboral",
    "movimiento_inventario",
    "compra",
    "historial_accion",
    "preparado",
)


def _una_sola_vez(conn, clave: str, descripcion: str) -> bool:
    """True únicamente la primera vez que se invoca con esa clave (usa la tabla configuracion)."""
    res = conn.execute(
        text(
            "INSERT INTO configuracion (clave, valor, descripcion) VALUES (:c, '1', :d) "
            "ON CONFLICT (clave) DO NOTHING"
        ),
        {"c": clave, "d": descripcion},
    )
    return res.rowcount == 1


def migrar_demo_y_fijados(conn) -> None:
    conn.execute(text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS fijado BOOLEAN NOT NULL DEFAULT FALSE;"))
    conn.execute(text("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;"))
    conn.execute(text("ALTER TABLE turno_laboral ADD COLUMN IF NOT EXISTS rol VARCHAR(50) NOT NULL DEFAULT 'cajero';"))
    for tabla in TABLAS_TRAZABLES:
        conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS es_demo BOOLEAN NOT NULL DEFAULT FALSE;"))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{tabla}_es_demo ON {tabla}(es_demo);"))

    if not _una_sola_vez(conn, "migracion_demo_fijados_v1", "Marcado inicial de cuentas demo y fijadas"):
        return

    # Cuentas de práctica del sistema
    conn.execute(text("UPDATE usuario SET es_demo = TRUE WHERE usuario IN ('caja', 'mesero', 'cocina');"))
    # Todas las cuentas existentes quedan protegidas contra resets (el dueño puede desfijarlas)
    conn.execute(text("UPDATE usuario SET fijado = TRUE;"))

    # Etiquetado retroactivo de lo ya generado por cuentas demo
    demo_users = "(SELECT id FROM usuario WHERE es_demo)"
    demo_pedidos = "(SELECT id FROM pedido WHERE es_demo)"
    conn.execute(text(f"UPDATE pedido SET es_demo = TRUE WHERE usuario_id IN {demo_users};"))
    conn.execute(text(f"UPDATE pago SET es_demo = TRUE WHERE usuario_id IN {demo_users} OR pedido_id IN {demo_pedidos};"))
    conn.execute(text(f"UPDATE vale SET es_demo = TRUE WHERE pedido_id IN {demo_pedidos};"))
    conn.execute(
        text(f"UPDATE movimiento_caja SET es_demo = TRUE WHERE usuario_id IN {demo_users} OR pedido_id IN {demo_pedidos};")
    )
    conn.execute(text(f"UPDATE cierre SET es_demo = TRUE WHERE usuario_id IN {demo_users};"))
    conn.execute(text(f"UPDATE turno_laboral SET es_demo = TRUE WHERE usuario_id IN {demo_users};"))
    conn.execute(
        text(
            f"UPDATE movimiento_inventario SET es_demo = TRUE "
            f"WHERE usuario_id IN {demo_users} OR pedido_id IN {demo_pedidos};"
        )
    )
    conn.execute(text(f"UPDATE compra SET es_demo = TRUE WHERE usuario_id IN {demo_users};"))
    conn.execute(text(f"UPDATE historial_accion SET es_demo = TRUE WHERE usuario_id IN {demo_users};"))
    conn.execute(
        text(f"UPDATE preparado SET es_demo = TRUE WHERE usuario_id IN {demo_users} OR pedido_origen_id IN {demo_pedidos};")
    )
    logger.info("Migración demo/fijados aplicada")


def completar_empaques_llevar(conn) -> None:
    """Agrega C1 (P1 en perros calientes, categoría 3) a los platos de cocina con receta
    que todavía no tengan ningún empaque 'solo para llevar'. Se ejecuta una sola vez para
    no revertir decisiones posteriores del administrador."""
    if not _una_sola_vez(conn, "migracion_empaques_llevar_v1", "Empaque para llevar por defecto en platos"):
        return

    for patron, filtro_cat in (("C1%", "c.id <> 3"), ("P1%", "c.id = 3")):
        fila = conn.execute(
            text("SELECT id FROM ingrediente WHERE nombre ILIKE :p AND activo = TRUE ORDER BY id LIMIT 1"),
            {"p": patron},
        ).first()
        if not fila:
            continue
        conn.execute(
            text(
                f"""
                INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad, solo_llevar)
                SELECT p.id, :ing, 1, 'u', TRUE
                FROM producto p JOIN categoria c ON c.id = p.categoria_id
                WHERE p.activo = TRUE AND c.tipo_id = 1 AND {filtro_cat}
                  AND EXISTS (SELECT 1 FROM detalle_receta d WHERE d.product_id = p.id)
                  AND NOT EXISTS (SELECT 1 FROM detalle_receta d WHERE d.product_id = p.id AND d.solo_llevar)
                ON CONFLICT (product_id, ingrediente_id) DO NOTHING
                """
            ),
            {"ing": fila[0]},
        )
    logger.info("Empaques para llevar completados")
