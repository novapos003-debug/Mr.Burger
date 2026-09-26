from decimal import Decimal, ROUND_HALF_UP

# ============================================================
# MOTOR UNIVERSAL DE CONVERSIÓN DE UNIDADES
# Sistema Gastronómico POS Mr. Burger
# ============================================================

# Dimensiones soportadas: MASA, VOLUMEN, CONTEO
# Cada dimensión tiene una unidad base estricta en el sistema:
#   - MASA:    GRAMO     (g)
#   - VOLUMEN: MILILITRO (ml)
#   - CONTEO:  UNIDAD    (u)

# Alias y factores respecto a la unidad base de su dimensión
TABLA_UNIDADES = {
    # --- MASA (Base: GRAMO) ---
    "g": ("MASA", Decimal("1")),
    "gr": ("MASA", Decimal("1")),
    "gramo": ("MASA", Decimal("1")),
    "gramos": ("MASA", Decimal("1")),
    "gram": ("MASA", Decimal("1")),
    "grams": ("MASA", Decimal("1")),
    "kg": ("MASA", Decimal("1000")),
    "kilo": ("MASA", Decimal("1000")),
    "kilos": ("MASA", Decimal("1000")),
    "kilogramo": ("MASA", Decimal("1000")),
    "kilogramos": ("MASA", Decimal("1000")),
    "lb": ("MASA", Decimal("500")),  # Libra comercial estándar en Colombia (500g)
    "libra": ("MASA", Decimal("500")),
    "libras": ("MASA", Decimal("500")),
    "oz": ("MASA", Decimal("28.3495")),
    "onza": ("MASA", Decimal("28.3495")),
    "onzas": ("MASA", Decimal("28.3495")),
    "mg": ("MASA", Decimal("0.001")),
    "miligramo": ("MASA", Decimal("0.001")),
    "miligramos": ("MASA", Decimal("0.001")),

    # --- VOLUMEN (Base: MILILITRO) ---
    "ml": ("VOLUMEN", Decimal("1")),
    "cc": ("VOLUMEN", Decimal("1")),
    "mililitro": ("VOLUMEN", Decimal("1")),
    "mililitros": ("VOLUMEN", Decimal("1")),
    "l": ("VOLUMEN", Decimal("1000")),
    "lt": ("VOLUMEN", Decimal("1000")),
    "litro": ("VOLUMEN", Decimal("1000")),
    "litros": ("VOLUMEN", Decimal("1000")),
    "oz_fl": ("VOLUMEN", Decimal("29.5735")),
    "fl_oz": ("VOLUMEN", Decimal("29.5735")),
    "onza_liquida": ("VOLUMEN", Decimal("29.5735")),
    "galon": ("VOLUMEN", Decimal("3785.41")),
    "gal": ("VOLUMEN", Decimal("3785.41")),

    # --- CONTEO (Base: UNIDAD / Discretas) ---
    "u": ("CONTEO", Decimal("1")),
    "un": ("CONTEO", Decimal("1")),
    "und": ("CONTEO", Decimal("1")),
    "unidad": ("CONTEO", Decimal("1")),
    "unidades": ("CONTEO", Decimal("1")),
    "unit": ("CONTEO", Decimal("1")),
    "lonja": ("CONTEO", Decimal("1")),
    "lonjas": ("CONTEO", Decimal("1")),
    "porcion": ("CONTEO", Decimal("1")),
    "porciones": ("CONTEO", Decimal("1")),
    "rebanada": ("CONTEO", Decimal("1")),
    "rebanadas": ("CONTEO", Decimal("1")),
    "tajada": ("CONTEO", Decimal("1")),
    "tajadas": ("CONTEO", Decimal("1")),
    "paquete": ("CONTEO", Decimal("1")),
    "paquetes": ("CONTEO", Decimal("1")),
    "docena": ("CONTEO", Decimal("12")),
    "docenas": ("CONTEO", Decimal("12")),
}

# Mapeo a las unidades base oficiales en base de datos
UNIDADES_BASE_OFICIALES = {
    "MASA": "GRAMO",
    "VOLUMEN": "MILILITRO",
    "CONTEO": "UNIDAD",
}


def normalizar_clave(unidad: str) -> str:
    """Limpia y estandariza la cadena de texto de una unidad."""
    if not unidad:
        return "u"
    u = unidad.strip().lower()
    # Eliminar puntos (ej: "kg." -> "kg", "u." -> "u")
    u = u.replace(".", "")
    # Tratamiento de mayúsculas previas en BD como "GRAMO", "MILILITRO", "UNIDAD"
    if u in ("gramo", "gramos"):
        return "g"
    if u in ("mililitro", "mililitros"):
        return "ml"
    if u in ("unidad", "unidades"):
        return "u"
    return u


def obtener_info_unidad(unidad: str) -> tuple[str, Decimal]:
    """Retorna (dimension, factor_a_base). Lanza ValueError si no se reconoce."""
    clave = normalizar_clave(unidad)
    info = TABLA_UNIDADES.get(clave)
    if not info:
        # Fallback para unidades personalizadas (ej. LONJA, PORCION)
        clave_upper = unidad.strip().upper()
        if clave_upper in ("LONJA", "LONJAS", "PORCION", "PORCIONES", "PAQUETE", "PAQUETES"):
            return ("CONTEO", Decimal("1"))
        raise ValueError(
            f"Unidad de medida no reconocida: '{unidad}'. "
            f"Unidades válidas: g, kg, lb, ml, l, u, lonja, porcion, tajada, docena, etc."
        )
    return info


def son_unidades_compatibles(u1: str, u2: str) -> bool:
    """Verifica si dos unidades pertenecen a la misma dimensión física."""
    try:
        dim1, _ = obtener_info_unidad(u1)
        dim2, _ = obtener_info_unidad(u2)
        return dim1 == dim2
    except ValueError:
        return False


def convertir_unidad(
    cantidad: Decimal | float | int,
    unidad_origen: str,
    unidad_destino: str,
    precision: Decimal = Decimal("0.0001"),
) -> Decimal:
    """Convierte una cantidad de `unidad_origen` a `unidad_destino`.

    Ejemplo:
        convertir_unidad(10, 'kg', 'g') -> 10000.0000
        convertir_unidad(70, 'g', 'kg') -> 0.0700
        convertir_unidad(1.5, 'l', 'ml') -> 1500.0000
        convertir_unidad(2, 'docena', 'u') -> 24.0000

    Lanza ValueError si las dimensiones son incompatibles (ej. kg a ml).
    """
    cant = Decimal(str(cantidad))
    u_orig = normalizar_clave(unidad_origen)
    u_dest = normalizar_clave(unidad_destino)

    if u_orig == u_dest:
        return cant.quantize(precision, rounding=ROUND_HALF_UP)

    dim_orig, factor_orig = obtener_info_unidad(unidad_origen)
    dim_dest, factor_dest = obtener_info_unidad(unidad_destino)

    if dim_orig != dim_dest:
        raise ValueError(
            f"Incompatibilidad de dimensiones: no se puede convertir '{unidad_origen}' ({dim_orig}) "
            f"a '{unidad_destino}' ({dim_dest})."
        )

    # Convertir primero a la unidad base de la dimensión, luego a la unidad destino
    # cantidad_en_base = cant * factor_orig
    # cantidad_final = cantidad_en_base / factor_dest
    cantidad_en_base = cant * factor_orig
    cantidad_final = cantidad_en_base / factor_dest

    return cantidad_final.quantize(precision, rounding=ROUND_HALF_UP)


def convertir_a_unidad_base(
    cantidad: Decimal | float | int,
    unidad: str,
    unidad_base_esperada: str | None = None,
) -> tuple[Decimal, str]:
    """Convierte cualquier cantidad a la unidad base de su dimensión (o la esperada por el insumo).

    Retorna: (cantidad_convertida, unidad_base)
    """
    dim, _ = obtener_info_unidad(unidad)
    base_oficial = UNIDADES_BASE_OFICIALES.get(dim, "UNIDAD")
    base_destino = unidad_base_esperada or base_oficial

    # Mapear nombre en BD ('GRAMO', 'MILILITRO', 'UNIDAD') a clave normalizada
    destino_norm = normalizar_clave(base_destino)
    cant_convertida = convertir_unidad(cantidad, unidad, destino_norm)
    return cant_convertida, base_oficial
