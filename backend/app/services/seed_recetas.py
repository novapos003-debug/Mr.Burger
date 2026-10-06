import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

RECETAS_BASE = [
    # --- HAMBURGUESAS ---
    {
        "producto": "Hamburguesa Especial Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Tocineta", 20, "GRAMO", False),
            ("Queso Americano", 1, "LONJA", False),
            ("Tomate", 1, "UNIDAD", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Especial Doble Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 250, "GRAMO", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tomate", 1, "UNIDAD", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Especial Pollo",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 130, "GRAMO", False),
            ("Tocineta", 20, "GRAMO", False),
            ("Queso Americano", 1, "LONJA", False),
            ("Tomate", 1, "UNIDAD", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Especial Doble Pollo",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 260, "GRAMO", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tomate", 1, "UNIDAD", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Especial Mixta",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Pollo (Pechuga)", 130, "GRAMO", False),
            ("Tocineta", 25, "GRAMO", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tomate", 1, "UNIDAD", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Mr. Burger Doble Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 250, "GRAMO", False),
            ("Aros de Cebolla", 3, "UNIDAD", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Mr. Burger Doble Pollo",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 260, "GRAMO", False),
            ("Aros de Cebolla", 3, "UNIDAD", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Mr. Burger Doble Angus",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne Angus", 300, "GRAMO", False),
            ("Aros de Cebolla", 3, "UNIDAD", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tocineta", 35, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Angus Sencilla",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne Angus", 150, "GRAMO", False),
            ("Queso Cheddar", 1, "LONJA", False),
            ("Tocineta", 25, "GRAMO", False),
            ("Cebolla Morada", 20, "GRAMO", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Angus Doble",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne Angus", 300, "GRAMO", False),
            ("Queso Cheddar", 2, "LONJA", False),
            ("Tocineta", 35, "GRAMO", False),
            ("Cebolla Morada", 20, "GRAMO", False),
            ("Lechuga Batavia", 20, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa T.T Todo Terreno Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Cebolla Cabezona", 30, "GRAMO", False),
            ("Salsa BBQ", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa T.T Todo Terreno Doble Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 250, "GRAMO", False),
            ("Tocineta", 40, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Cebolla Cabezona", 30, "GRAMO", False),
            ("Salsa BBQ", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa T.T Todo Terreno Pollo",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 130, "GRAMO", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Cebolla Cabezona", 30, "GRAMO", False),
            ("Salsa BBQ", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa T.T Todo Terreno Doble Pollo",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 260, "GRAMO", False),
            ("Tocineta", 40, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Cebolla Cabezona", 30, "GRAMO", False),
            ("Salsa BBQ", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa T.T Todo Terreno Mixta",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Pollo (Pechuga)", 130, "GRAMO", False),
            ("Tocineta", 35, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Cebolla Cabezona", 30, "GRAMO", False),
            ("Salsa BBQ", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Ranchera Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Salchicha Ranchera", 2, "UNIDAD", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Chimichurry", 15, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Ranchera Doble Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 250, "GRAMO", False),
            ("Salchicha Ranchera", 2, "UNIDAD", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Chimichurry", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Cinco Estrellas Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 125, "GRAMO", False),
            ("Aros de Cebolla", 2, "UNIDAD", False),
            ("Queso Americano", 1, "LONJA", False),
            ("Tocineta", 20, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Hamburguesa Cinco Estrellas Doble Res",
        "ingredientes": [
            ("Pan Hamburguesa", 1, "UNIDAD", False),
            ("Carne de res", 250, "GRAMO", False),
            ("Aros de Cebolla", 3, "UNIDAD", False),
            ("Queso Americano", 2, "LONJA", False),
            ("Tocineta", 30, "GRAMO", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },

    # --- PERROS CALIENTES ---
    {
        "producto": "Perro Ítalo Suizo",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Suiza", 1, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Lechuga Batavia", 10, "GRAMO", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Perro Mr. Burger",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Ideal", 1, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Lechuga Batavia", 10, "GRAMO", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Perro Ranchero",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Ranchera", 2, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Lechuga Batavia", 10, "GRAMO", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Perro Americano",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Americana", 1, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Americano", 1, "LONJA", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Perro Quesudo",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Americana", 1, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Mazorcas", 0.5, "UNIDAD", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Perro Mexicano",
        "ingredientes": [
            ("Pan Perro", 1, "UNIDAD", False),
            ("Salchicha Ideal", 1, "UNIDAD", False),
            ("Tocineta", 15, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Lechuga Batavia", 10, "GRAMO", False),
            ("Chimichurry", 15, "MILILITRO", False),
            ("Salsa Mr Burger", 15, "MILILITRO", False),
            ("P1 (Porta Perro Caliente)", 1, "UNIDAD", True),
        ],
    },

    # --- PARA COMPARTIR Y ADICIONES ---
    {
        "producto": "Salchipapa Americana",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Salchicha Americana", 1, "UNIDAD", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("Salsa de Tomate", 15, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Salchipapa Especial",
        "ingredientes": [
            ("Papa a la Francesa", 180, "GRAMO", False),
            ("Salchicha Americana", 1, "UNIDAD", False),
            ("Tocineta", 20, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Salsa Mr Burger", 25, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Papas con Queso",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Tocineta", 20, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Papas a la Francesa (Porción)",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Aceite", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Aros de Cebolla (6 unidades)",
        "ingredientes": [
            ("Aros de Cebolla", 6, "UNIDAD", False),
            ("Aceite", 20, "MILILITRO", False),
            ("Salsa BBQ", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },

    # --- ASADOS ---
    {
        "producto": "Costilla St. Louis",
        "ingredientes": [
            ("Costilla", 300, "GRAMO", False),
            ("Salsa BBQ", 40, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Asado Baby",
        "ingredientes": [
            ("Baby Beef", 250, "GRAMO", False),
            ("Chimichurry", 30, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Churrasco a la Brasa",
        "ingredientes": [
            ("Churrasco", 250, "GRAMO", False),
            ("Chimichurry", 30, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Filete de Pollo a la Brasa",
        "ingredientes": [
            ("Pollo (Pechuga)", 250, "GRAMO", False),
            ("Chimichurry", 30, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Chuzo de Res",
        "ingredientes": [
            ("Carne de res", 200, "GRAMO", False),
            ("Chimichurry", 20, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Chuzo de Pollo",
        "ingredientes": [
            ("Pollo (Pechuga)", 200, "GRAMO", False),
            ("Chimichurry", 20, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Chuzo Mixto",
        "ingredientes": [
            ("Carne de res", 100, "GRAMO", False),
            ("Pollo (Pechuga)", 100, "GRAMO", False),
            ("Chimichurry", 20, "MILILITRO", False),
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },

    # --- MAZORCAS Y DESGRANADOS ---
    {
        "producto": "Desgranado Mixto",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Mantequilla", 20, "GRAMO", False),
            ("Carne de res", 80, "GRAMO", False),
            ("Pollo (Pechuga)", 80, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Desgranado Res",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Mantequilla", 20, "GRAMO", False),
            ("Carne de res", 150, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Desgranado Pollo",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Mantequilla", 20, "GRAMO", False),
            ("Pollo (Pechuga)", 150, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Desgranado Ranchero",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Mantequilla", 20, "GRAMO", False),
            ("Salchicha Ranchera", 2, "UNIDAD", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("Ripio de Papa", 15, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Mazorca Ranchera",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Salchicha Ranchera", 1, "UNIDAD", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Mazorca Gratinada",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Queso Tajado", 2, "LONJA", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Mazorca Americana",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Mantequilla", 20, "GRAMO", False),
            ("Salsa Mr Burger", 20, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Mazorca Especial Pollo",
        "ingredientes": [
            ("Mazorcas", 1, "UNIDAD", False),
            ("Pollo (Pechuga)", 100, "GRAMO", False),
            ("Queso Tajado", 1, "LONJA", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },

    # --- ALITAS ---
    {
        "producto": "Alitas BBQ (6 piezas)",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Salsa BBQ", 40, "MILILITRO", False),
            ("Aceite", 30, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Alitas Miel Mostaza (6 piezas)",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Mostaza", 30, "MILILITRO", False),
            ("Aceite", 30, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
    {
        "producto": "Alitas Picantes (6 piezas)",
        "ingredientes": [
            ("Papa a la Francesa", 150, "GRAMO", False),
            ("Salsa BBQ", 30, "MILILITRO", False),
            ("Aceite", 30, "MILILITRO", False),
            ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
        ],
    },
]

COMBOS_BASE = [
    {
        "combo": "Combo Con Papas",
        "hijos": [
            ("Gaseosa Personal", 1),
            ("Papas a la Francesa (Porción)", 1),
        ],
        "empaque": ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
    },
    {
        "combo": "Combo Con Aros de Cebolla",
        "hijos": [
            ("Gaseosa Personal", 1),
            ("Aros de Cebolla (6 unidades)", 1),
        ],
        "empaque": ("C1 (Empaque Térmico)", 1, "UNIDAD", True),
    },
]


def sembrar_recetas_base(conn) -> int:
    """Inserta las recetas oficiales base del restaurante únicamente si el producto
    no tiene ninguna línea configurada en detalle_receta (respeta personalizaciones)."""
    insertadas = 0

    # 1. Recetas de Insumos Tradicionales
    for r in RECETAS_BASE:
        prod_nombre = r["producto"]
        row_p = conn.execute(
            text("SELECT id FROM producto WHERE nombre = :nombre AND activo = TRUE LIMIT 1"),
            {"nombre": prod_nombre},
        ).fetchone()

        if not row_p:
            continue
        prod_id = row_p[0]

        # Verificar si ya tiene líneas de receta
        tiene_receta = conn.execute(
            text("SELECT 1 FROM detalle_receta WHERE product_id = :pid LIMIT 1"),
            {"pid": prod_id},
        ).fetchone()

        if tiene_receta:
            continue

        for ing_nom, cant, unid, solo_llevar in r["ingredientes"]:
            row_i = conn.execute(
                text("SELECT id FROM ingrediente WHERE (nombre = :nombre OR nombre ILIKE :nombre_like) AND activo = TRUE LIMIT 1"),
                {"nombre": ing_nom, "nombre_like": f"%{ing_nom}%"},
            ).fetchone()

            if not row_i:
                logger.warning(f"No se encontró ingrediente base '{ing_nom}' para el producto '{prod_nombre}'")
                continue

            ing_id = row_i[0]
            conn.execute(
                text("""
                    INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad, solo_llevar)
                    VALUES (:pid, :iid, :cant, :unid, :solo_llevar)
                    ON CONFLICT (product_id, ingrediente_id) DO NOTHING
                """),
                {
                    "pid": prod_id,
                    "iid": ing_id,
                    "cant": cant,
                    "unid": unid,
                    "solo_llevar": solo_llevar,
                },
            )
        insertadas += 1

    # 2. Componentes de Combos Oficiales
    for c in COMBOS_BASE:
        combo_nombre = c["combo"]
        row_c = conn.execute(
            text("SELECT id FROM producto WHERE nombre = :nombre AND activo = TRUE LIMIT 1"),
            {"nombre": combo_nombre},
        ).fetchone()

        if not row_c:
            continue
        combo_id = row_c[0]

        tiene_componentes = conn.execute(
            text("SELECT 1 FROM componente_combo WHERE combo_producto_id = :cid LIMIT 1"),
            {"cid": combo_id},
        ).fetchone()

        if not tiene_componentes:
            for hijo_nombre, cant in c["hijos"]:
                row_h = conn.execute(
                    text("SELECT id FROM producto WHERE nombre = :nombre AND activo = TRUE LIMIT 1"),
                    {"nombre": hijo_nombre},
                ).fetchone()

                if row_h:
                    hijo_id = row_h[0]
                    conn.execute(
                        text("""
                            INSERT INTO componente_combo (combo_producto_id, producto_hijo_id, cantidad)
                            VALUES (:cid, :hid, :cant)
                        """),
                        {"cid": combo_id, "hid": hijo_id, "cant": cant},
                    )

        # Si no tiene empaque para llevar en detalle_receta, agregarlo
        tiene_empaque = conn.execute(
            text("SELECT 1 FROM detalle_receta WHERE product_id = :cid LIMIT 1"),
            {"cid": combo_id},
        ).fetchone()

        if not tiene_empaque and "empaque" in c:
            emp_nom, emp_cant, emp_unid, emp_solo_llevar = c["empaque"]
            row_emp = conn.execute(
                text("SELECT id FROM ingrediente WHERE (nombre = :nombre OR nombre ILIKE :nombre_like) AND activo = TRUE LIMIT 1"),
                {"nombre": emp_nom, "nombre_like": f"%{emp_nom}%"},
            ).fetchone()
            if row_emp:
                conn.execute(
                    text("""
                        INSERT INTO detalle_receta (product_id, ingrediente_id, cantidad, unidad, solo_llevar)
                        VALUES (:pid, :iid, :cant, :unid, :solo_llevar)
                        ON CONFLICT (product_id, ingrediente_id) DO NOTHING
                    """),
                    {
                        "pid": combo_id,
                        "iid": row_emp[0],
                        "cant": emp_cant,
                        "unid": emp_unid,
                        "solo_llevar": emp_solo_llevar,
                    },
                )

    return insertadas
