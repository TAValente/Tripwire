# Tripwire

Tripwire is an AI-powered project reviewer designed to detect drift, contradictions, hidden costs, and poor strategic decisions before they become embedded in a codebase.

It is not a linter, formatter, or code generator. Its primary question is:

> Is the project still becoming what we intended it to become?

## Quick start

```powershell
python -m tripwire review
python -m tripwire review --staged
python -m tripwire review main
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

The git diff is the primary object under review. Doctrine and repository context are supporting evidence.

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
