-- Speeds up joins and foreign-key maintenance for leftovers linked to recipes.
create index if not exists leftovers_recipe_id_idx
  on public.leftovers (recipe_id);
