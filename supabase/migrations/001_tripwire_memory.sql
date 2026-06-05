create extension if not exists pgcrypto;

create table if not exists tripwire_projects (
  id uuid primary key default gen_random_uuid(),
  github_owner text not null,
  github_repo text not null,
  default_branch text,
  doctrine_snapshot jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (github_owner, github_repo)
);

create table if not exists tripwire_pull_requests (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references tripwire_projects(id) on delete cascade,
  github_pr_number integer not null,
  title text not null default '',
  author_login text not null default '',
  base_branch text not null default '',
  head_branch text not null default '',
  state text not null default 'open',
  url text not null default '',
  last_seen_head_sha text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  merged_at timestamptz,
  unique (project_id, github_pr_number)
);

create table if not exists tripwire_review_runs (
  id uuid primary key default gen_random_uuid(),
  pull_request_id uuid references tripwire_pull_requests(id) on delete cascade,
  trigger text not null default 'manual',
  provider text,
  model text,
  prompt_version text not null default 'concise-v1',
  user_concerns text not null default '',
  doctrine_snapshot jsonb not null default '[]'::jsonb,
  diff_summary jsonb not null default '{}'::jsonb,
  output_text text not null default '',
  inferred_signal text,
  outcome_state text,
  outcome_note text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists tripwire_findings (
  id uuid primary key default gen_random_uuid(),
  review_run_id uuid not null references tripwire_review_runs(id) on delete cascade,
  stable_key text not null,
  finding_type text not null default 'mistake',
  title text not null,
  severity integer,
  confidence text,
  category text,
  persona text,
  evidence text not null default '',
  why_it_matters text not null default '',
  recommended_action text not null default '',
  acceptable_for_current_phase text,
  status text not null default 'open',
  value_score numeric,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists tripwire_finding_events (
  id uuid primary key default gen_random_uuid(),
  finding_id uuid not null references tripwire_findings(id) on delete cascade,
  event_type text not null,
  github_comment_url text,
  evidence_snapshot text,
  rationale text,
  created_at timestamptz not null default now()
);

create table if not exists tripwire_project_memory (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references tripwire_projects(id) on delete cascade,
  memory jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (project_id)
);

create table if not exists tripwire_author_memory (
  id uuid primary key default gen_random_uuid(),
  author_login text not null unique,
  memory jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists tripwire_findings_stable_key_idx on tripwire_findings(stable_key);
create index if not exists tripwire_review_runs_created_at_idx on tripwire_review_runs(created_at desc);
