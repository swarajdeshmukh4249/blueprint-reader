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

  -- Auth: who uploaded this and under which org (null = personal)
  user_id text,
  org_id  text,

  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

-- Auto-update updated_at
create or replace function public.set_analysis_jobs_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists analysis_jobs_set_updated_at on public.analysis_jobs;
create trigger analysis_jobs_set_updated_at
before update on public.analysis_jobs
for each row execute function public.set_analysis_jobs_updated_at();

-- Indexes for fast dashboard queries
create index if not exists idx_analysis_jobs_user_id on public.analysis_jobs(user_id);
create index if not exists idx_analysis_jobs_org_id  on public.analysis_jobs(org_id);

-- Row Level Security
alter table public.analysis_jobs enable row level security;

-- Users can read their own personal jobs (org_id is null)
create policy "Users read own personal jobs"
on public.analysis_jobs for select
to authenticated
using (user_id = auth.uid()::text and org_id is null);

-- Users can read all jobs belonging to their org
create policy "Org members read org jobs"
on public.analysis_jobs for select
to authenticated
using (org_id is not null and org_id = (auth.jwt() ->> 'org_id'));

-- Anyone authenticated can insert (user_id enforced in app layer)
create policy "Authenticated users can insert"
on public.analysis_jobs for insert
to authenticated, anon
with check (true);

-- Service role (Python worker) can update any job
create policy "Service role can update jobs"
on public.analysis_jobs for update
to service_role
using (true) with check (true);

-- Storage bucket (150 MB per file — also raise global limit in Dashboard → Storage → Settings)
insert into storage.buckets (id, name, public, file_size_limit)
values ('blueprints', 'blueprints', false, 157286400)
on conflict (id) do update set file_size_limit = excluded.file_size_limit;

create policy "Allow uploads into blueprints bucket"
on storage.objects for insert
to anon, authenticated
with check (bucket_id = 'blueprints');

create policy "Allow read access to blueprints bucket"
on storage.objects for select
to anon, authenticated
using (bucket_id = 'blueprints');