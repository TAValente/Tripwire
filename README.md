# Tripwire

Tripwire is an AI-powered project reviewer designed to detect drift, contradictions, hidden costs, and poor strategic decisions before they become embedded in a codebase.

It is not a linter, formatter, or code generator. Its primary question is:

> Is the project still becoming what we intended it to become?

## Quick start

From PowerShell in this repo, use the local wrapper:

```powershell
.\tw.cmd doctor
.\tw.cmd ui
.\tw.cmd scan
.\tw.cmd review-pr TAValente/TrainingTweaks 5
.\tw.cmd eval
```

The wrapper sets `PYTHONPATH=src` and defaults to Ollama with `qwen3:8b`. Use `tw.cmd` on Windows because PowerShell may block local `.ps1` scripts by policy.

```powershell
python -m tripwire review
python -m tripwire review --staged
python -m tripwire review main
python -m tripwire review-pr TAValente/Tripwire 12
python -m tripwire github
python -m tripwire ui
python -m tripwire scan
python -m tripwire personas
python -m tripwire doctrine
python -m tripwire doctor --provider ollama --model qwen3:8b
python -m tripwire paranoid
python -m tripwire architecture
python -m tripwire eval
```

Install the local CLI entry point:

```powershell
python -m pip install -e .
tripwire review
```

By default Tripwire is local-first. It will try Ollama when configured, otherwise it runs local high-confidence checks and can print the full review packet.
Deterministic local guardrails still run when an AI provider is configured, so obvious doctrine violations do not disappear when a model is timid.

```powershell
$env:TRIPWIRE_PROVIDER = "ollama"
```

Optional settings:

```powershell
$env:OLLAMA_HOST = "http://localhost:11434"
```

You can also pass provider settings per command:

```powershell
tripwire review --provider ollama --model llama3.1
```

If you omit `--model`, Ollama defaults to `llama3.1`.

### Ollama setup

Install Ollama, then pull the default local model:

```powershell
$env:OLLAMA_MODELS = "D:\Ollama\models"
$env:OLLAMA_LLM_LIBRARY = "cpu"
ollama pull qwen2.5-coder:3b
ollama serve
```

In another terminal:

```powershell
tripwire eval --provider ollama --model qwen2.5-coder:3b --show-output
```

OpenAI-compatible review is still available when explicitly configured:

```powershell
$env:TRIPWIRE_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:TRIPWIRE_MODEL = "gpt-5-mini"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
```

## Doctrine

Tripwire loads these project doctrine files before reviewing a diff:

- `docs/principles.md`
- `docs/economics.md`
- `docs/current_phase.md`
- `docs/anti_patterns.md`
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/learning.md`

The git diff is the primary object under review. Doctrine and repository context are supporting evidence.

## GitHub PRs

Review an open GitHub pull request directly:

```powershell
tripwire review-pr TAValente/Tripwire 12 --concerns "Watch for scope creep and model cost regressions."
```

Tripwire uses the authenticated GitHub CLI session to fetch PR metadata, PR diff, and doctrine docs from the PR base branch. If the target repository does not have doctrine docs, Tripwire does not fall back to its own doctrine; it emits a Concrete Improver explaining the minimum docs needed for useful review.

Install and authenticate GitHub CLI before using GitHub PR commands:

```powershell
gh auth login
```

If `gh` is missing, Tripwire exits with an actionable setup message instead of a Python traceback.

Store a review:

```powershell
tripwire review-pr TAValente/Tripwire 12 --store
```

By default this stores locally in `.tripwire/tripwire.db`. Set `TRIPWIRE_STORE=supabase` only if you want hosted storage. See [docs/backend.md](docs/backend.md) for local memory and optional Supabase setup.

Inspect local memory:

```powershell
tripwire memory stats
```

Use the interactive picker:

```powershell
tripwire github --provider ollama --model qwen2.5-coder:3b
```

Tripwire lists repositories, narrows to repositories with open PRs when it can, lets you choose an open PR, asks for optional concerns, and then runs the same review engine.

Check local readiness:

```powershell
tripwire doctor --provider ollama --model qwen3:8b
```

Doctor checks package import, doctrine completeness, GitHub CLI/auth, and the configured AI provider/model.

Run a project scan:

```powershell
.\tw.cmd scan
```

Project scan is not tied to one PR. It looks for longer-running drift, especially doctrine inconsistencies, doctrine conflicts, stale phase assumptions, and architecture/economics contradictions.

Run the local control panel:

```powershell
.\tw.cmd ui
```

The control panel runs on `127.0.0.1`, wraps the local review workflow, and does not require hosted deployment.

## Personas

Explain how the reviewer personas work:

```powershell
tripwire personas
```

Tripwire uses personas selectively:

- Engineer: architecture drift, hidden complexity, maintainability risk, data model integrity.
- Product Manager: user value, requirement compliance, scope creep, overengineering, feature prioritization.
- Economics Watchdog: API costs, infrastructure costs, operational burden, scaling assumptions, latency/resource regressions.

If a project does not have enough documentation for a persona to judge drift responsibly, Tripwire should prefer a Concrete Improver recommending the minimum missing docs over inventing project intent.

## Evaluation

Run the fixture suite:

```powershell
tripwire eval
```

Run the same fixtures through Ollama:

```powershell
tripwire eval --provider ollama --model qwen2.5-coder:3b
```

`qwen2.5-coder:3b` is currently the more practical local default for CPU-only evaluation. `llama3.1` works as a model install target, but may be too slow without GPU acceleration.

Fixture files live in `eval/fixtures/*.json`. Each fixture defines a diff, repository context, required terms, and forbidden terms. The evaluator scores the rendered Tripwire review text so it can test local guardrails, a locally hosted LLM, or the hybrid path.
