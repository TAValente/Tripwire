# Tripwire Backend

Tripwire can run fully locally, but passive learning needs persistent memory.

Use Supabase when you want to store:

- review runs
- findings
- rationale
- recommended actions
- follow-up outcomes
- project memory
- author memory

## Setup

1. Create a Supabase project.
2. Run `supabase/migrations/001_tripwire_memory.sql` in the SQL editor or through Supabase CLI.
3. Set environment variables:

```powershell
$env:SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "..."
```

For local experiments, `SUPABASE_ANON_KEY` can be used if row-level security policies allow inserts. For private local tooling, prefer the service-role key and do not expose it to browsers.

## Store A Review

```powershell
tripwire review-pr TAValente/TrainingTweaks 1 --store
```

Tripwire currently stores:

- project row
- pull request row
- review run row
- raw output text
- deterministic local guardrail findings

Model-generated findings are stored in raw output text for now. A later structured-output pass will split model findings into `tripwire_findings` rows too.

## Learning Loop

The next backend milestone is follow-up classification:

```powershell
tripwire watch run
```

That command will compare stored findings against later PR commits/comments and classify each finding as addressed, partially addressed, rejected, stale, false positive, or still open.
