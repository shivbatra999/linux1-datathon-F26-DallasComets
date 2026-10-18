-- SimpleCater order-creation migration.
-- Prerequisite: existing Supabase public businesses, profiles, menu_items,
-- orders and order_items tables. This is not a full database bootstrap.
-- Function body extracted unchanged from the deployed Supabase export.
-- Records an already-tested deployment; no customer data or credentials.

begin;

alter table public.orders
add column if not exists pickup_date date;

CREATE OR REPLACE FUNCTION public.simplecater_place_order(p_business_id uuid, p_pickup_date date, p_items jsonb)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
    v_customer uuid := auth.uid();
    v_order uuid;
    v_item jsonb;
    v_item_id uuid;
    v_quantity numeric;
    v_price numeric;
    v_total numeric := 0;
    v_seen uuid[] := '{}';
    v_lines jsonb := '[]'::jsonb;
begin
    -- Determine identity from the authenticated session.
    if v_customer is null or not exists (
        select 1 from public.profiles
        where id = v_customer and role = 'customer'
    ) then
        raise exception 'Customer account required.';
    end if;

    if p_pickup_date is null
       or p_pickup_date <
          (now() at time zone 'America/Chicago')::date then
        raise exception 'Choose a valid pickup date.';
    end if;

    if jsonb_typeof(p_items) is distinct from 'array' then
        raise exception 'Cart must be an array.';
    end if;

    if jsonb_array_length(p_items) < 1
       or jsonb_array_length(p_items) > 50 then
        raise exception 'Cart must contain 1 to 50 items.';
    end if;

    perform 1 from public.businesses
    where id = p_business_id and is_active
    for share;

    if not found then
        raise exception 'Business is unavailable.';
    end if;

    for v_item in select value from jsonb_array_elements(p_items)
    loop
        if jsonb_typeof(v_item -> 'menu_item_id')
             is distinct from 'string'
           or jsonb_typeof(v_item -> 'quantity')
             is distinct from 'number' then
            raise exception 'Invalid cart item.';
        end if;

        v_item_id := (v_item ->> 'menu_item_id')::uuid;
        v_quantity := (v_item ->> 'quantity')::numeric;

        if v_quantity < 1 or v_quantity > 1000
           or v_quantity <> trunc(v_quantity) then
            raise exception 'Quantity must be an integer from 1 to 1000.';
        end if;

        if v_item_id = any(v_seen) then
            raise exception 'Duplicate cart item.';
        end if;
        v_seen := array_append(v_seen, v_item_id);

        select price into v_price
        from public.menu_items
        where id = v_item_id
          and business_id = p_business_id
          and is_available
        for share;

        if not found then
            raise exception 'A menu item is unavailable.';
        end if;

        if v_price is null or v_price <= 0
           or v_price > 100000 then
            raise exception 'Menu item price is invalid.';
        end if;

        v_price := round(v_price, 2);
        v_total := v_total + v_price * v_quantity;

        v_lines := v_lines || jsonb_build_array(
            jsonb_build_object(
                'menu_item_id', v_item_id,
                'quantity', v_quantity::integer,
                'unit_price', v_price
            )
        );
    end loop;

    insert into public.orders (
        customer_id, business_id, status, total, pickup_date
    )
    values (
        v_customer, p_business_id, 'pending', v_total, p_pickup_date
    )
    returning id into v_order;

    insert into public.order_items (
        order_id, menu_item_id, quantity, unit_price
    )
    select
        v_order, x.menu_item_id, x.quantity, x.unit_price
    from jsonb_to_recordset(v_lines)
    as x(menu_item_id uuid, quantity integer, unit_price numeric);

    return v_order;
end;
$function$;

revoke execute on function public.simplecater_place_order(uuid, date, jsonb)
from public, anon;

grant execute on function public.simplecater_place_order(uuid, date, jsonb)
to authenticated;

commit;
