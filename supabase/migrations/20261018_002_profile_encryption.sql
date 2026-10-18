begin;

grant update (encrypted_profile)
on public.profiles
to authenticated;

drop policy if exists
  "Customers can update their own encrypted profile"
on public.profiles;

create policy "Customers can update their own encrypted profile"
on public.profiles
for update
to authenticated
using (
  id = (select auth.uid())
  and role = 'customer'
)
with check (
  id = (select auth.uid())
  and role = 'customer'
);

commit;
