"""Catalogos locales del MVP.

Las conversiones masa-volumen son aproximadas y dependen del alimento y su
estado. Solo se habilitan cuando ``grams_per_cup`` esta definido.
"""

PRODUCT_CATALOG = [
    {"name": "Arroz", "category": "Granos", "default_unit": "lb", "aliases": ["arroz blanco"], "state": "seco", "grams_per_cup": 185},
    {"name": "Habichuelas", "category": "Legumbres", "default_unit": "lb", "aliases": ["frijoles", "habichuelas secas"], "state": "secas"},
    {"name": "Gandules", "category": "Legumbres", "default_unit": "lata", "aliases": ["gandules enlatados"]},
    {"name": "Garbanzos", "category": "Legumbres", "default_unit": "lata", "aliases": []},
    {"name": "Lentejas", "category": "Legumbres", "default_unit": "lb", "aliases": []},
    {"name": "Pasta", "category": "Granos", "default_unit": "lb", "aliases": ["macarrones", "espaguetis"]},
    {"name": "Avena", "category": "Granos", "default_unit": "taza", "aliases": []},
    {"name": "Harina de maiz", "category": "Granos", "default_unit": "lb", "aliases": []},
    {"name": "Pan", "category": "Granos", "default_unit": "rebanada", "aliases": []},
    {"name": "Galletas de soda", "category": "Granos", "default_unit": "paquete", "aliases": []},
    {"name": "Pollo", "category": "Proteinas", "default_unit": "lb", "aliases": []},
    {"name": "Carne de res", "category": "Proteinas", "default_unit": "lb", "aliases": ["res"]},
    {"name": "Cerdo", "category": "Proteinas", "default_unit": "lb", "aliases": []},
    {"name": "Pescado", "category": "Proteinas", "default_unit": "lb", "aliases": []},
    {"name": "Atun enlatado", "category": "Proteinas", "default_unit": "lata", "aliases": ["atun"]},
    {"name": "Huevos", "category": "Proteinas", "default_unit": "unidad", "aliases": ["huevo"]},
    {"name": "Tomates", "category": "Vegetales", "default_unit": "unidad", "aliases": ["tomate"]},
    {"name": "Cebolla", "category": "Vegetales", "default_unit": "unidad", "aliases": []},
    {"name": "Ajo", "category": "Vegetales", "default_unit": "diente", "aliases": []},
    {"name": "Pimiento", "category": "Vegetales", "default_unit": "unidad", "aliases": ["pimientos"]},
    {"name": "Aji dulce", "category": "Vegetales", "default_unit": "unidad", "aliases": []},
    {"name": "Calabaza", "category": "Vegetales", "default_unit": "lb", "aliases": []},
    {"name": "Guineos", "category": "Frutas", "default_unit": "unidad", "aliases": ["guineo"]},
    {"name": "Platanos", "category": "Frutas", "default_unit": "unidad", "aliases": ["platano"]},
    {"name": "Yuca", "category": "Viandas", "default_unit": "lb", "aliases": []},
    {"name": "Yautia", "category": "Viandas", "default_unit": "lb", "aliases": []},
    {"name": "Batata", "category": "Viandas", "default_unit": "lb", "aliases": []},
    {"name": "Aceite", "category": "Aceites y grasas", "default_unit": "ml", "aliases": ["aceite de oliva", "aceite de maiz"]},
    {"name": "Leche", "category": "Lacteos", "default_unit": "taza", "aliases": []},
    {"name": "Sal", "category": "Condimentos", "default_unit": "cucharadita", "aliases": []},
    {"name": "Azucar", "category": "Condimentos", "default_unit": "taza", "aliases": []},
]


UNIT_ALIASES = {
    "g": "g", "gramo": "g", "gramos": "g",
    "kg": "kg", "kilogramo": "kg", "kilogramos": "kg",
    "oz": "oz", "onza": "oz", "onzas": "oz",
    "lb": "lb", "libra": "lb", "libras": "lb",
    "ml": "ml", "mililitro": "ml", "mililitros": "ml",
    "l": "l", "litro": "l", "litros": "l",
    "taza": "cup", "tazas": "cup", "cup": "cup", "cups": "cup",
    "cucharada": "tbsp", "cucharadas": "tbsp", "tbsp": "tbsp",
    "cucharadita": "tsp", "cucharaditas": "tsp", "tsp": "tsp",
    "unidad": "unit", "unidades": "unit",
}

MASS_TO_GRAMS = {"g": 1.0, "kg": 1000.0, "oz": 28.349523125, "lb": 453.59237}
VOLUME_TO_ML = {"ml": 1.0, "l": 1000.0, "tsp": 4.92892159375, "tbsp": 14.78676478125, "cup": 236.5882365}
