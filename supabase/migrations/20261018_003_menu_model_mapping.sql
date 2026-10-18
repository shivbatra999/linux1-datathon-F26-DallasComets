begin;

alter table public.menu_items
add column if not exists model_item_id integer
check (model_item_id > 0);

create unique index if not exists
  menu_items_business_model_item_unique
on public.menu_items (business_id, model_item_id)
where model_item_id is not null;

update public.menu_items as m
set model_item_id = mapping.model_id
from (
  values
    ('10000000-0000-0000-0000-000000000001'::uuid, 1),
    ('10000000-0000-0000-0000-000000000002'::uuid, 2),
    ('10000000-0000-0000-0000-000000000003'::uuid, 3),
    ('10000000-0000-0000-0000-000000000004'::uuid, 4),
    ('10000000-0000-0000-0000-000000000006'::uuid, 5),
    ('10000000-0000-0000-0000-000000000007'::uuid, 6)
) as mapping(menu_id, model_id)
where m.id = mapping.menu_id
  and m.business_id =
    '43064247-2342-48fa-9b3f-f70c6947f313'::uuid;

commit;
