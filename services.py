from collections import defaultdict
from datetime import date
from decimal import Decimal
import unicodedata

from rapidfuzz.fuzz import ratio

from catalog import MASS_TO_GRAMS, PRODUCT_CATALOG, UNIT_ALIASES, VOLUME_TO_ML


def normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return "".join(character for character in text if not unicodedata.combining(character))


def number(value: object) -> Decimal:
    return Decimal(str(value or 0))


def canonical_unit(value: object) -> str:
    unit = normalized(value)
    return UNIT_ALIASES.get(unit, unit)


def product_profile(name: object) -> dict | None:
    target = normalized(name)
    for product in PRODUCT_CATALOG:
        names = [product["name"], *product.get("aliases", [])]
        if target in {normalized(candidate) for candidate in names}:
            return product
    return None


def names_match(left: object, right: object) -> bool:
    """Match pantry names while avoiding unsafe broad substring matches."""
    left_text = normalized(left)
    right_text = normalized(right)
    if left_text == right_text:
        return True
    left_profile = product_profile(left)
    right_profile = product_profile(right)
    if left_profile and right_profile:
        return left_profile["name"] == right_profile["name"]
    return min(len(left_text), len(right_text)) >= 4 and ratio(left_text, right_text) >= 92


def convert_quantity(value: object, from_unit: object, to_unit: object, ingredient: object) -> Decimal | None:
    amount = number(value)
    source = canonical_unit(from_unit)
    target = canonical_unit(to_unit)
    if source == target:
        return amount
    if source in MASS_TO_GRAMS and target in MASS_TO_GRAMS:
        return amount * Decimal(str(MASS_TO_GRAMS[source])) / Decimal(str(MASS_TO_GRAMS[target]))
    if source in VOLUME_TO_ML and target in VOLUME_TO_ML:
        return amount * Decimal(str(VOLUME_TO_ML[source])) / Decimal(str(VOLUME_TO_ML[target]))

    profile = product_profile(ingredient)
    grams_per_cup = profile.get("grams_per_cup") if profile else None
    if grams_per_cup and source in MASS_TO_GRAMS and target in VOLUME_TO_ML:
        grams = amount * Decimal(str(MASS_TO_GRAMS[source]))
        cups = grams / Decimal(str(grams_per_cup))
        return cups * Decimal(str(VOLUME_TO_ML["cup"])) / Decimal(str(VOLUME_TO_ML[target]))
    if grams_per_cup and source in VOLUME_TO_ML and target in MASS_TO_GRAMS:
        cups = amount * Decimal(str(VOLUME_TO_ML[source])) / Decimal(str(VOLUME_TO_ML["cup"]))
        grams = cups * Decimal(str(grams_per_cup))
        return grams / Decimal(str(MASS_TO_GRAMS[target]))
    return None


def build_inventory_lots(products: list[dict], leftovers: list[dict], today: date) -> list[dict]:
    lots: list[dict] = []
    for source, rows in (("product", products), ("leftover", leftovers)):
        for row in rows:
            if number(row.get("quantity")) <= 0:
                continue
            expiration = date.fromisoformat(row["expiration_date"])
            item = dict(row)
            item["source"] = source
            item["expired"] = expiration < today
            item["days_until_expiration"] = (expiration - today).days
            lots.append(item)
    return sorted(lots, key=lambda item: (item["expired"], item["expiration_date"], item["name"]))


def availability_for_recipe(ingredients: list[dict], lots: list[dict]) -> dict:
    available: defaultdict[tuple[str, str], Decimal] = defaultdict(Decimal)
    units_by_name: defaultdict[str, set[str]] = defaultdict(set)
    for lot in lots:
        if lot["expired"]:
            continue
        name = normalized(lot["name"])
        unit = canonical_unit(lot["unit"])
        available[(name, unit)] += number(lot["quantity"])
        units_by_name[name].add(str(lot["unit"]))

    details = []
    missing = []
    for ingredient in ingredients:
        name = normalized(ingredient["ingredients_name"])
        unit = canonical_unit(ingredient["unit"])
        required = number(ingredient["quantity"])
        current = Decimal("0")
        convertible = False
        for lot in lots:
            if lot["expired"] or not names_match(lot["name"], ingredient["ingredients_name"]):
                continue
            converted = convert_quantity(lot["quantity"], lot["unit"], ingredient["unit"], ingredient["ingredients_name"])
            if converted is not None:
                current += converted
                convertible = True
        detail = {
            "ingredient": ingredient["ingredients_name"],
            "unit": ingredient["unit"],
            "required": float(required),
            "available": float(current),
            "enough": current >= required,
        }
        if current < required:
            detail["missing"] = float(required - current)
            if not convertible and units_by_name[name]:
                detail["reason"] = "incompatible_unit"
                detail["available_units"] = sorted(units_by_name[name])
            else:
                detail["reason"] = "insufficient_quantity"
            missing.append(detail)
        details.append(detail)

    return {
        "can_prepare": not missing,
        "status": "Puedes preparar" if not missing else "Te faltan ingredientes",
        "details": details,
        "missing": missing,
    }


def consumption_plan(ingredients: list[dict], lots: list[dict]) -> list[dict]:
    updates: list[dict] = []
    for ingredient in ingredients:
        needed = number(ingredient["quantity"])
        candidates = [
            lot
            for lot in lots
            if not lot["expired"]
            and names_match(lot["name"], ingredient["ingredients_name"])
            and convert_quantity(lot["quantity"], lot["unit"], ingredient["unit"], ingredient["ingredients_name"]) is not None
        ]
        for lot in candidates:
            if needed <= 0:
                break
            current = number(lot["quantity"])
            available_in_recipe_unit = convert_quantity(current, lot["unit"], ingredient["unit"], ingredient["ingredients_name"])
            consumed_in_recipe_unit = min(available_in_recipe_unit, needed)
            consumed = convert_quantity(consumed_in_recipe_unit, ingredient["unit"], lot["unit"], ingredient["ingredients_name"])
            remaining = current - consumed
            needed -= consumed_in_recipe_unit
            lot["quantity"] = float(remaining)
            updates.append(
                {
                    "source": lot["source"],
                    "id": lot["id"],
                    "consumed": float(consumed),
                    "remaining": float(remaining),
                }
            )
    return updates
