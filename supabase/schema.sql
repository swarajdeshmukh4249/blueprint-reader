create extension if not exists "pgcrypto";

create table if not exists public.analysis_jobs (
  id uuid primary key default gen_random_uuid(),
  file_name text not null,
  file_path text not null unique,
  file_type text,
  storage_bucket text not null default 'blueprints',
  status text not null default 'queued' check (status in ('queued', 'processing', 'completed', 'failed')),
  result jsonb,
  error text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create or replace function public.set_analysis_jobs_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists analysis_jobs_set_updated_at on public.analysis_jobs;

create trigger analysis_jobs_set_updated_at
before update on public.analysis_jobs
for each row
execute function public.set_analysis_jobs_updated_at();

alter table public.analysis_jobs enable row level security;

create policy "Allow public read access to analysis jobs"
on public.analysis_jobs
for select
to anon, authenticated
using (true);

create policy "Allow public insert access to analysis jobs"
on public.analysis_jobs
for insert
to anon, authenticated
with check (true);

create policy "Allow service role to update analysis jobs"
on public.analysis_jobs
for update
to service_role
using (true)
with check (true);

insert into storage.buckets (id, name, public)
values ('blueprints', 'blueprints', false)
on conflict (id) do nothing;

create policy "Allow uploads into blueprints bucket"
on storage.objects
for insert
to anon, authenticated
with check (bucket_id = 'blueprints');

create policy "Allow read access to blueprints bucket metadata"
on storage.objects
for select
to anon, authenticated
using (bucket_id = 'blueprints');
