from decimal import Decimal
import sys

from app.database import SessionLocal
from app.models import (
    Categoria,
    CategoriaInsumo,
    DetalleReceta,
    Ingrediente,
    MovimientoInventario,
    Producto,
    TipoCategoria,
    Usuario,
)
from app.services.inventario import (
    calcular_costo_y_margen,
    descontar_insumos_de_producto,
    expandir_insumos_producto,
)


def ejecutar_prueba():
    print("=" * 70)
    print("TEST DE VALIDACIÓN CONCEPTUAL — INVENTARIOS, RECETAS Y DESCUENTOS")
    print("=" * 70)

    db = SessionLocal()
    try:
        # 1. Asegurar usuario admin
        admin = db.query(Usuario).filter(Usuario.usuario == "admin").first()
        assert admin is not None, "Usuario admin requerido"

        # 2. Asegurar categoría de prueba
        tipo_comida = db.query(TipoCategoria).filter(TipoCategoria.nombre == "COMIDA").first()
        if not tipo_comida:
            tipo_comida = TipoCategoria(nombre="COMIDA")
            db.add(tipo_comida)
            db.flush()

        cat_test = db.query(Categoria).filter(Categoria.nombre == "TEST_REQUERIMIENTOS").first()
        if not cat_test:
            cat_test = Categoria(tipo_id=tipo_comida.id, nombre="TEST_REQUERIMIENTOS")
            db.add(cat_test)
            db.flush()

        # 3. Categorías de Insumo
        cat_carnes = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "CARNES").first()
        cat_abarrotes = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "ABARROTES_ACEITES").first()
        cat_verduras = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "VERDURAS").first()
        cat_pan = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "PANADERIA").first()
        cat_lacteos = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "LACTEOS").first()
        cat_salsas = db.query(CategoriaInsumo).filter(CategoriaInsumo.nombre == "SALSAS_CONDIMENTOS").first()

        # 4. Crear o Resetear Insumos del Ejemplo
        datos_insumos = {
            "TEST_Papa": {"unidad": "GRAMO", "stock": Decimal("10000"), "costo": Decimal("3"), "cat": cat_abarrotes.id if cat_abarrotes else None},
            "TEST_Carne": {"unidad": "GRAMO", "stock": Decimal("5000"), "costo": Decimal("28"), "cat": cat_carnes.id if cat_carnes else None},
            "TEST_Pan": {"unidad": "UNIDAD", "stock": Decimal("20"), "costo": Decimal("600"), "cat": cat_pan.id if cat_pan else None},
            "TEST_Tomate": {"unidad": "GRAMO", "stock": Decimal("1000"), "costo": Decimal("5"), "cat": cat_verduras.id if cat_verduras else None},
            "TEST_Lechuga": {"unidad": "GRAMO", "stock": Decimal("800"), "costo": Decimal("4"), "cat": cat_verduras.id if cat_verduras else None},
            "TEST_Queso": {"unidad": "UNIDAD", "stock": Decimal("30"), "costo": Decimal("800"), "cat": cat_lacteos.id if cat_lacteos else None},
            "TEST_Aceite": {"unidad": "MILILITRO", "stock": Decimal("2000"), "costo": Decimal("8"), "cat": cat_abarrotes.id if cat_abarrotes else None},
            "TEST_Salsa": {"unidad": "MILILITRO", "stock": Decimal("1000"), "costo": Decimal("5"), "cat": cat_salsas.id if cat_salsas else None},
        }

        mapa_insumos: dict[str, Ingrediente] = {}
        for nombre, d in datos_insumos.items():
            ing = db.query(Ingrediente).filter(Ingrediente.nombre == nombre).first()
            if not ing:
                ing = Ingrediente(
                    nombre=nombre,
                    unidad_base=d["unidad"],
                    stock_actual=d["stock"],
                    stock_minimo=Decimal("50"),
                    costo_unitario=d["costo"],
                    categoria_insumo_id=d["cat"],
                )
                db.add(ing)
                db.flush()
            else:
                ing.stock_actual = d["stock"]
                ing.costo_unitario = d["costo"]
                ing.categoria_insumo_id = d["cat"]
            mapa_insumos[nombre] = ing
        db.commit()

        print("\n[PASO 1] Insumos y stock inicial configurados:")
        for nombre, ing in mapa_insumos.items():
            print(f"  • {nombre}: {ing.stock_actual} {ing.unidad_base} (Costo: ${ing.costo_unitario})")

        # 5. Crear Productos y sus Recetas
        # Producto 1: Hamburguesa
        prod_burger = db.query(Producto).filter(Producto.nombre == "TEST_Hamburguesa").first()
        if not prod_burger:
            prod_burger = Producto(
                categoria_id=cat_test.id,
                nombre="TEST_Hamburguesa",
                descripcion="Hamburguesa de prueba",
                precio=Decimal("18000"),
            )
            db.add(prod_burger)
            db.flush()
        else:
            prod_burger.precio = Decimal("18000")

        db.query(DetalleReceta).filter(DetalleReceta.product_id == prod_burger.id).delete()
        receta_burger = [
            (mapa_insumos["TEST_Pan"].id, Decimal("2"), "u"),
            (mapa_insumos["TEST_Carne"].id, Decimal("150"), "g"),
            (mapa_insumos["TEST_Tomate"].id, Decimal("30"), "g"),
            (mapa_insumos["TEST_Lechuga"].id, Decimal("20"), "g"),
            (mapa_insumos["TEST_Queso"].id, Decimal("1"), "u"),
            (mapa_insumos["TEST_Salsa"].id, Decimal("15"), "ml"),
        ]
        for ing_id, cant, und in receta_burger:
            db.add(DetalleReceta(product_id=prod_burger.id, ingrediente_id=ing_id, cantidad=cant, unidad=und))

        # Producto 2: Papas fritas 70 g
        prod_papas = db.query(Producto).filter(Producto.nombre == "TEST_Papas_70g").first()
        if not prod_papas:
            prod_papas = Producto(
                categoria_id=cat_test.id,
                nombre="TEST_Papas_70g",
                descripcion="Porción de papas fritas 70g",
                precio=Decimal("6000"),
            )
            db.add(prod_papas)
            db.flush()
        else:
            prod_papas.precio = Decimal("6000")

        db.query(DetalleReceta).filter(DetalleReceta.product_id == prod_papas.id).delete()
        receta_papas = [
            (mapa_insumos["TEST_Papa"].id, Decimal("70"), "g"),
            (mapa_insumos["TEST_Aceite"].id, Decimal("20"), "ml"),
        ]
        for ing_id, cant, und in receta_papas:
            db.add(DetalleReceta(product_id=prod_papas.id, ingrediente_id=ing_id, cantidad=cant, unidad=und))
        db.commit()

        print("\n[PASO 2] Recetas y análisis de costo/utilidad:")
        fin_burger = calcular_costo_y_margen(db, prod_burger)
        print(f"  • {prod_burger.nombre}:")
        print(f"    - Costo de producción: ${fin_burger['costo_produccion']}")
        print(f"    - Precio de venta:     ${fin_burger['precio_venta']}")
        print(f"    - Utilidad bruta:      ${fin_burger['utilidad_bruta']} ({fin_burger['margen_porcentaje']}%)")

        fin_papas = calcular_costo_y_margen(db, prod_papas)
        print(f"  • {prod_papas.nombre}:")
        print(f"    - Costo de producción: ${fin_papas['costo_produccion']}")
        print(f"    - Precio de venta:     ${fin_papas['precio_venta']}")
        print(f"    - Utilidad bruta:      ${fin_papas['utilidad_bruta']} ({fin_papas['margen_porcentaje']}%)")

        # 6. Simular Venta: 2 Hamburguesas + 3 Papas Fritas 70g
        print("\n[PASO 3] Simulando Venta de 2 Hamburguesas + 3 Papas Fritas 70g...")
        movs_burger = descontar_insumos_de_producto(
            db=db,
            producto_id=prod_burger.id,
            cantidad=Decimal("2"),
            usuario_id=admin.id,
            referencia_base="Venta #999 - 2x TEST_Hamburguesa",
        )
        movs_papas = descontar_insumos_de_producto(
            db=db,
            producto_id=prod_papas.id,
            cantidad=Decimal("3"),
            usuario_id=admin.id,
            referencia_base="Venta #999 - 3x TEST_Papas_70g",
        )
        db.commit()

        # 7. Verificar Saldos Esperados
        esperados = {
            "TEST_Pan": Decimal("20") - Decimal("4"),       # 20 - 4 = 16 u
            "TEST_Carne": Decimal("5000") - Decimal("300"), # 5000 - 300 = 4700 g
            "TEST_Tomate": Decimal("1000") - Decimal("60"), # 1000 - 60 = 940 g
            "TEST_Lechuga": Decimal("800") - Decimal("40"), # 800 - 40 = 760 g
            "TEST_Queso": Decimal("30") - Decimal("2"),     # 30 - 2 = 28 u
            "TEST_Salsa": Decimal("1000") - Decimal("30"),  # 1000 - 30 = 970 ml
            "TEST_Papa": Decimal("10000") - Decimal("210"), # 10000 - 210 = 9790 g
            "TEST_Aceite": Decimal("2000") - Decimal("60"), # 2000 - 60 = 1940 ml
        }

        print("\n[PASO 4] Verificación de saldos en Inventario:")
        errores = 0
        for nombre, saldo_esperado in esperados.items():
            ing = db.query(Ingrediente).filter(Ingrediente.nombre == nombre).one()
            ok = ing.stock_actual == saldo_esperado
            simbolo = "✓ PASS" if ok else "✗ FAIL"
            if not ok:
                errores += 1
            print(f"  {simbolo}: {nombre} -> Esperado: {saldo_esperado} {ing.unidad_base} | Real en BD: {ing.stock_actual} {ing.unidad_base}")

        # 8. Verificar Movimientos Kardex
        print("\n[PASO 5] Verificación de auditoría en MovimientoInventario:")
        todos_movs = movs_burger + movs_papas
        for m in todos_movs:
            print(f"  • Mov #{m.id}: {m.referencia} | Saldo: {m.saldo_anterior} -> {m.saldo_nuevo} {m.unidad} (Cant: {m.cantidad})")

        assert errores == 0, f"Hubo {errores} discrepancias en los saldos"
        print("\n" + "=" * 70)
        print("¡TODAS LAS VALIDACIONES DEL EJERCICIO PASARON AL 100%!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_prueba()
