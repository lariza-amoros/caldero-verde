create or replace function public.apply_inventory_consumption(p_updates jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  item jsonb;
  item_id bigint;
  item_source text;
  amount numeric;
  new_quantity numeric;
  result jsonb := '[]'::jsonb;
begin
  if jsonb_typeof(p_updates) <> 'array' then
    raise exception 'p_updates must be a JSON array';
  end if;

  for item in select value from jsonb_array_elements(p_updates)
  loop
    item_id := (item->>'id')::bigint;
    item_source := item->>'source';
    amount := (item->>'consumed')::numeric;

    if item_id is null or amount is null or amount <= 0 then
      raise exception 'Invalid inventory consumption item';
    end if;

    if item_source = 'product' then
      update public.products
      set quantity = quantity - amount
      where id = item_id and quantity >= amount
      returning quantity into new_quantity;
    elsif item_source = 'leftover' then
      update public.leftovers
      set quantity = quantity - amount
      where id = item_id and quantity >= amount
      returning quantity into new_quantity;
    else
      raise exception 'Invalid inventory source: %', item_source;
    end if;

    if not found then
      raise exception 'Inventory changed; reload and try again (source %, id %)', item_source, item_id;
    end if;

    result := result || jsonb_build_array(jsonb_build_object(
      'source', item_source,
      'id', item_id,
      'consumed', amount,
      'remaining', new_quantity
    ));
  end loop;

  return result;
end;
$$;

revoke all on function public.apply_inventory_consumption(jsonb) from public;
revoke all on function public.apply_inventory_consumption(jsonb) from anon;
revoke all on function public.apply_inventory_consumption(jsonb) from authenticated;
grant execute on function public.apply_inventory_consumption(jsonb) to service_role;
