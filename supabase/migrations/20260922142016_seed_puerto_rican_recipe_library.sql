do $$
declare
  recipe_id_value bigint;
begin
  select id into recipe_id_value from public.recipes where lower(name) = lower('Arroz con gandules') limit 1;
  if recipe_id_value is null then
    insert into public.recipes (name, category, description, instructions)
    values ('Arroz con gandules', 'Plato principal', 'Clásico puertorriqueño para aprovechar arroz y gandules de la alacena.', 'Sofríe los condimentos, añade gandules, arroz y agua; cocina tapado hasta que el arroz esté tierno.')
    returning id into recipe_id_value;
  end if;
  insert into public.recipe_ingredients (recipe_id, ingredients_name, quantity, unit)
  select recipe_id_value, ingredient, quantity, unit
  from (values ('Arroz', 2::numeric, 'taza'), ('Gandules', 1::numeric, 'lata'), ('Cebolla', 1::numeric, 'unidad')) as items(ingredient, quantity, unit)
  where not exists (select 1 from public.recipe_ingredients ri where ri.recipe_id = recipe_id_value and lower(ri.ingredients_name) = lower(items.ingredient));

  select id into recipe_id_value from public.recipes where lower(name) = lower('Habichuelas guisadas') limit 1;
  if recipe_id_value is null then
    insert into public.recipes (name, category, description, instructions)
    values ('Habichuelas guisadas', 'Acompañamiento', 'Guiso sencillo de habichuelas con vegetales de la despensa.', 'Sofríe cebolla y pimiento, incorpora las habichuelas y cocina a fuego bajo hasta espesar.')
    returning id into recipe_id_value;
  end if;
  insert into public.recipe_ingredients (recipe_id, ingredients_name, quantity, unit)
  select recipe_id_value, ingredient, quantity, unit
  from (values ('Habichuelas', 1::numeric, 'lb'), ('Cebolla', 1::numeric, 'unidad'), ('Pimiento', 1::numeric, 'unidad')) as items(ingredient, quantity, unit)
  where not exists (select 1 from public.recipe_ingredients ri where ri.recipe_id = recipe_id_value and lower(ri.ingredients_name) = lower(items.ingredient));

  select id into recipe_id_value from public.recipes where lower(name) = lower('Sopa de calabaza') limit 1;
  if recipe_id_value is null then
    insert into public.recipes (name, category, description, instructions)
    values ('Sopa de calabaza', 'Sopa', 'Sopa cremosa para aprovechar calabaza y aromáticos antes de que se deterioren.', 'Hierve la calabaza con cebolla y ajo; licúa con parte del caldo y ajusta la sazón.')
    returning id into recipe_id_value;
  end if;
  insert into public.recipe_ingredients (recipe_id, ingredients_name, quantity, unit)
  select recipe_id_value, ingredient, quantity, unit
  from (values ('Calabaza', 1::numeric, 'lb'), ('Cebolla', 1::numeric, 'unidad'), ('Ajo', 1::numeric, 'diente')) as items(ingredient, quantity, unit)
  where not exists (select 1 from public.recipe_ingredients ri where ri.recipe_id = recipe_id_value and lower(ri.ingredients_name) = lower(items.ingredient));

  select id into recipe_id_value from public.recipes where lower(name) = lower('Ensalada de garbanzos') limit 1;
  if recipe_id_value is null then
    insert into public.recipes (name, category, description, instructions)
    values ('Ensalada de garbanzos', 'Almuerzo', 'Ensalada rápida con ingredientes de alacena y vegetales frescos.', 'Escurre los garbanzos, mezcla con tomate, cebolla y aceite, y sazona al gusto.')
    returning id into recipe_id_value;
  end if;
  insert into public.recipe_ingredients (recipe_id, ingredients_name, quantity, unit)
  select recipe_id_value, ingredient, quantity, unit
  from (values ('Garbanzos', 1::numeric, 'lata'), ('Tomates', 2::numeric, 'unidad'), ('Cebolla', 1::numeric, 'unidad')) as items(ingredient, quantity, unit)
  where not exists (select 1 from public.recipe_ingredients ri where ri.recipe_id = recipe_id_value and lower(ri.ingredients_name) = lower(items.ingredient));

  select id into recipe_id_value from public.recipes where lower(name) = lower('Avena con leche') limit 1;
  if recipe_id_value is null then
    insert into public.recipes (name, category, description, instructions)
    values ('Avena con leche', 'Desayuno', 'Desayuno económico para aprovechar avena y leche disponibles.', 'Cocina la avena con leche a fuego bajo, mueve hasta espesar y endulza al gusto.')
    returning id into recipe_id_value;
  end if;
  insert into public.recipe_ingredients (recipe_id, ingredients_name, quantity, unit)
  select recipe_id_value, ingredient, quantity, unit
  from (values ('Avena', 1::numeric, 'taza'), ('Leche', 2::numeric, 'taza')) as items(ingredient, quantity, unit)
  where not exists (select 1 from public.recipe_ingredients ri where ri.recipe_id = recipe_id_value and lower(ri.ingredients_name) = lower(items.ingredient));
end;
$$;
