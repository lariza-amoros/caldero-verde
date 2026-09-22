import unittest
from datetime import date

from services import availability_for_recipe, build_inventory_lots, consumption_plan, convert_quantity, names_match


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        products = [
            {"id": 1, "name": "Arroz", "quantity": 2, "unit": "lb", "expiration_date": "2026-10-15"},
            {"id": 4, "name": "Tomates", "quantity": 4, "unit": "unidad", "expiration_date": "2026-09-25"},
        ]
        leftovers = [
            {"id": 2, "name": "Arroz", "quantity": 1, "unit": "taza", "expiration_date": "2026-09-25"}
        ]
        self.lots = build_inventory_lots(products, leftovers, date(2026, 9, 21))

    def test_leftover_is_reused_as_ingredient(self):
        ingredients = [{"ingredients_name": "Arroz", "quantity": 1, "unit": "taza"}]
        result = availability_for_recipe(ingredients, self.lots)
        self.assertTrue(result["can_prepare"])

    def test_incompatible_unit_is_reported(self):
        ingredients = [{"ingredients_name": "Arroz", "quantity": 1, "unit": "unidad"}]
        result = availability_for_recipe(ingredients, self.lots)
        self.assertFalse(result["can_prepare"])
        self.assertEqual(result["missing"][0]["reason"], "incompatible_unit")

    def test_dry_rice_converts_pounds_to_cups(self):
        cups = convert_quantity(1, "lb", "taza", "Arroz")
        self.assertAlmostEqual(float(cups), 2.45185, places=4)

    def test_consumption_uses_earliest_expiration(self):
        ingredients = [{"ingredients_name": "Tomates", "quantity": 2, "unit": "unidad"}]
        updates = consumption_plan(ingredients, self.lots)
        self.assertEqual(updates[0]["id"], 4)
        self.assertEqual(updates[0]["remaining"], 2.0)

    def test_common_singular_plural_names_match(self):
        self.assertTrue(names_match("Tomate", "Tomates"))

    def test_zero_quantity_is_not_available(self):
        lots = build_inventory_lots(
            [{"id": 9, "name": "Arroz", "quantity": 0, "unit": "lb", "expiration_date": "2026-10-15"}],
            [],
            date(2026, 9, 21),
        )
        self.assertEqual(lots, [])


if __name__ == "__main__":
    unittest.main()
