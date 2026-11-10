-- IPL Auction Assistant: database tables. Paste this into Supabase > SQL Editor > Run.

create table if not exists public.setups (
  user_id uuid primary key references auth.users(id) on delete cascade default auth.uid(),
  data jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.sales (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  player text not null,
  buyer text not null,
  price numeric not null,
  created_at timestamptz not null default now()
);

alter table public.setups enable row level security;
alter table public.sales enable row level security;

drop policy if exists "own setup" on public.setups;
create policy "own setup" on public.setups
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "own sales" on public.sales;
create policy "own sales" on public.sales
  for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
