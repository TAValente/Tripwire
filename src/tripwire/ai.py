from __future__ import annotations

import os
from dataclasses import dataclass
import json
import socket
import urllib.error
import urllib.request


class AIReviewError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIConfig:
    provider: str | None = None
    model: str | None = None


def ai_review(prompt: str, config: AIConfig | None = None) -> str | None:
    config = config or AIConfig()
    configured_model = config.model or os.environ.get("TRIPWIRE_MODEL")
    provider = (config.provider or os.environ.get("TRIPWIRE_PROVIDER") or "").lower()
    if not provider and configured_model:
        provider = "ollama"

    if provider == "openai":
        return _openai_review(prompt, config.model)
    if provider == "ollama":
        return _ollama_review(prompt, config.model)
    if provider:
        raise AIReviewError(f"Unsupported AI provider: {provider}")

    return None


def _openai_review(prompt: str, model: str | None = None) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    selected_model = model or os.environ.get("TRIPWIRE_MODEL", "gpt-5-mini")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/responses"
    payload = {
        "model": selected_model,
        "input": prompt,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AIReviewError(f"AI review failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIReviewError(f"AI review failed: {exc}") from exc

    text = data.get("output_text")
    if text:
        return str(text).strip()

    output = data.get("output", [])
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip() or None


def _ollama_review(prompt: str, model: str | None = None) -> str | None:
    selected_model = model or os.environ.get("TRIPWIRE_MODEL", "llama3.1")
    timeout = int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "300"))

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    url = f"{host}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1200,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AIReviewError(f"Ollama review failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIReviewError(f"Ollama review failed: {exc}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AIReviewError(f"Ollama review timed out after {timeout} seconds") from exc

    text = data.get("response")
    return str(text).strip() if text else None
