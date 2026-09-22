import os
import hmac
from datetime import date

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import Client, create_client

from catalog import PRODUCT_CATALOG, UNIT_ALIASES
from services import availability_for_recipe, build_inventory_lots, consumption_plan


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_KEY en .env")
    return create_client(url, key)


def required_json(fields: tuple[str, ...]) -> tuple[dict | None, str | None]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, "El cuerpo debe ser JSON."
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        return None, f"Faltan campos requeridos: {', '.join(missing)}"
    return payload, None


def positive_quantity(value: object) -> float:
    quantity = float(value)
    if quantity <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    return quantity



def create_app(client: Client | None = None) -> Flask:
    app = Flask(__name__)
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500"
    ).split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    db = client or get_supabase_client()

    @app.before_request
    def protect_writes():
        expected = os.getenv("APP_ACCESS_PIN", "")
        if request.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"} and expected:
            supplied = request.headers.get("X-Caldero-Pin", "")
            if not hmac.compare_digest(supplied, expected):
                return jsonify({"error": "Código de acceso requerido o incorrecto."}), 401

    def inventory_rows() -> tuple[list[dict], list[dict]]:
        products = db.table("products").select("*").order("expiration_date").execute().data or []
        leftovers = db.table("leftovers").select("*").order("expiration_date").execute().data or []
        return products, leftovers

    def recipe_bundle(recipe_id: int) -> tuple[dict | None, list[dict]]:
        recipes = db.table("recipes").select("*").eq("id", recipe_id).limit(1).execute().data or []
        ingredients = (
            db.table("recipe_ingredients")
            .select("*")
            .eq("recipe_id", recipe_id)
            .order("id")
            .execute()
            .data
            or []
        )
        return (recipes[0] if recipes else None), ingredients

    @app.errorhandler(Exception)
    def handle_error(error: Exception):
        app.logger.exception("Error procesando la solicitud")
        response = {"error": "No se pudo completar la operacion."}
        if app.debug:
            response["detail"] = str(error)
        return jsonify(response), 500

    @app.get("/")
    def index():
        return jsonify({"app": "Caldero Verde API", "status": "ok", "flow": "Inventario -> Receta -> Preparacion -> Sobra -> Reutilizacion"})

    @app.get("/api/health")
    def health():
        result = db.table("products").select("id", count="exact").limit(1).execute()
        return jsonify({"status": "ok", "supabase": "connected", "products": result.count})

    @app.get("/api/inventory")
    def inventory():
        products, leftovers = inventory_rows()
        lots = build_inventory_lots(products, leftovers, date.today())
        return jsonify({"items": lots, "count": len(lots)})

    @app.get("/api/catalog/products")
    def product_catalog():
        return jsonify({"products": PRODUCT_CATALOG, "count": len(PRODUCT_CATALOG)})

    @app.get("/api/catalog/units")
    def unit_catalog():
        canonical = sorted(set(UNIT_ALIASES.values()))
        return jsonify({"units": canonical, "aliases": UNIT_ALIASES})

    @app.get("/api/bootstrap")
    def bootstrap():
        recipe_rows = db.table("recipes").select("*").order("name").execute().data or []
        ingredient_rows = db.table("recipe_ingredients").select("*").order("id").execute().data or []
        products, leftovers = inventory_rows()
        lots = build_inventory_lots(products, leftovers, date.today())
        grouped: dict[int, list[dict]] = {}
        for ingredient in ingredient_rows:
            grouped.setdefault(int(ingredient["recipe_id"]), []).append(ingredient)
        for recipe in recipe_rows:
            ingredients = grouped.get(int(recipe["id"]), [])
            recipe["ingredients"] = ingredients
            recipe["availability"] = availability_for_recipe(ingredients, lots)
        return jsonify({
            "inventory": {"items": lots, "count": len(lots)},
            "recipes": {"recipes": recipe_rows, "count": len(recipe_rows)},
            "catalog": {
                "products": PRODUCT_CATALOG,
                "units": sorted(set(UNIT_ALIASES.values())),
                "aliases": UNIT_ALIASES,
            },
        })

    @app.post("/api/inventory")
    def create_inventory_item():
        payload, error = required_json(("name", "category", "quantity", "unit", "expiration_date"))
        if error:
            return jsonify({"error": error}), 400
        try:
            payload["quantity"] = positive_quantity(payload["quantity"])
            date.fromisoformat(str(payload["expiration_date"]))
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        row = {key: payload[key] for key in ("name", "category", "quantity", "unit", "expiration_date")}
        created = db.table("products").insert(row).execute().data
        return jsonify({"item": created[0] if created else row}), 201

    @app.get("/api/recipes")
    def recipes():
        recipe_rows = db.table("recipes").select("*").order("name").execute().data or []
        ingredient_rows = db.table("recipe_ingredients").select("*").order("id").execute().data or []
        products, leftovers = inventory_rows()
        lots = build_inventory_lots(products, leftovers, date.today())
        grouped: dict[int, list[dict]] = {}
        for ingredient in ingredient_rows:
            grouped.setdefault(int(ingredient["recipe_id"]), []).append(ingredient)
        for recipe in recipe_rows:
            ingredients = grouped.get(int(recipe["id"]), [])
            recipe["ingredients"] = ingredients
            recipe["availability"] = availability_for_recipe(ingredients, lots)
        return jsonify({"recipes": recipe_rows, "count": len(recipe_rows)})

    @app.get("/api/recipes/<int:recipe_id>/availability")
    def recipe_availability(recipe_id: int):
        recipe, ingredients = recipe_bundle(recipe_id)
        if recipe is None:
            return jsonify({"error": "Receta no encontrada."}), 404
        products, leftovers = inventory_rows()
        lots = build_inventory_lots(products, leftovers, date.today())
        return jsonify({"recipe": recipe, "ingredients": ingredients, "availability": availability_for_recipe(ingredients, lots)})

    @app.post("/api/leftovers")
    def create_leftover():
        payload, error = required_json(("recipe_id", "name", "quantity", "unit", "expiration_date"))
        if error:
            return jsonify({"error": error}), 400
        try:
            payload["quantity"] = positive_quantity(payload["quantity"])
            payload["recipe_id"] = int(payload["recipe_id"])
            date.fromisoformat(str(payload["expiration_date"]))
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        row = {key: payload[key] for key in ("recipe_id", "name", "quantity", "unit", "expiration_date")}
        created = db.table("leftovers").insert(row).execute().data
        return jsonify({"leftover": created[0] if created else row}), 201

    @app.post("/api/recipes/<int:recipe_id>/prepare")
    def prepare_recipe(recipe_id: int):
        recipe, ingredients = recipe_bundle(recipe_id)
        if recipe is None:
            return jsonify({"error": "Receta no encontrada."}), 404
        products, leftovers = inventory_rows()
        lots = build_inventory_lots(products, leftovers, date.today())
        availability = availability_for_recipe(ingredients, lots)
        if not availability["can_prepare"]:
            return jsonify({"error": "Faltan ingredientes.", "availability": availability}), 409
        updates = consumption_plan(ingredients, lots)
        rpc_updates = [
            {"source": update["source"], "id": update["id"], "consumed": update["consumed"]}
            for update in updates
        ]
        applied = db.rpc("apply_inventory_consumption", {"p_updates": rpc_updates}).execute().data
        return jsonify({"message": "Receta preparada; inventario actualizado.", "recipe": recipe, "updates": applied})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
