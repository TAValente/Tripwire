from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .doctrine import DOCTRINE_PATHS, missing_doctrine_paths
from .github import gh_executable


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


def render_doctor(root: Path, *, provider: str | None = None, model: str | None = None) -> tuple[str, bool]:
    checks = [
        check_package_import(),
        check_doctrine(root),
        check_github_cli(),
        check_github_auth(),
        check_ai(provider=provider, model=model),
    ]
    ready = all(check.status != "FAIL" for check in checks)
    lines = ["Tripwire doctor", "", f"Root: {root}", ""]
    lines.extend(f"[{check.status}] {check.name}: {check.detail}" for check in checks)
    if ready:
        lines.extend(["", "Tripwire is ready for local review workflows."])
    else:
        lines.extend(["", "Tripwire needs attention before all review workflows are ready."])
    return "\n".join(lines), ready


def check_package_import() -> DoctorCheck:
    return DoctorCheck("Python package", "OK", "tripwire imports successfully")


def check_doctrine(root: Path) -> DoctorCheck:
    missing = missing_doctrine_paths(root)
    found = len(DOCTRINE_PATHS) - len(missing)
    if not missing:
        return DoctorCheck("Doctrine", "OK", f"found {found}/{len(DOCTRINE_PATHS)} docs")
    return DoctorCheck(
        "Doctrine",
        "WARN",
        f"found {found}/{len(DOCTRINE_PATHS)} docs; run `tripwire doctrine` for missing docs",
    )


def check_github_cli() -> DoctorCheck:
    path = gh_executable()
    if not path:
        return DoctorCheck("GitHub CLI", "FAIL", "`gh` was not found on PATH")
    try:
        result = subprocess.run(
            [path, "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return DoctorCheck("GitHub CLI", "FAIL", str(exc))
    first_line = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else path
    return DoctorCheck("GitHub CLI", "OK" if result.returncode == 0 else "FAIL", first_line)


def check_github_auth() -> DoctorCheck:
    path = gh_executable()
    if not path:
        return DoctorCheck("GitHub auth", "FAIL", "install GitHub CLI first")
    try:
        result = subprocess.run(
            [path, "auth", "status"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return DoctorCheck("GitHub auth", "FAIL", str(exc))
    if result.returncode == 0:
        return DoctorCheck("GitHub auth", "OK", "authenticated")
    message = result.stderr.strip() or result.stdout.strip() or "not authenticated"
    return DoctorCheck("GitHub auth", "FAIL", f"{message}; run `gh auth login`")


def check_ai(*, provider: str | None = None, model: str | None = None) -> DoctorCheck:
    selected_provider = (provider or os.environ.get("TRIPWIRE_PROVIDER") or "").lower()
    selected_model = model or os.environ.get("TRIPWIRE_MODEL")
    if not selected_provider and selected_model:
        selected_provider = "ollama"

    if selected_provider == "ollama":
        return check_ollama(selected_model or "llama3.1")
    if selected_provider == "openai":
        if os.environ.get("OPENAI_API_KEY"):
            return DoctorCheck("AI provider", "OK", f"OpenAI configured with model {selected_model or 'gpt-5-mini'}")
        return DoctorCheck("AI provider", "FAIL", "OPENAI_API_KEY is not set")
    if selected_provider:
        return DoctorCheck("AI provider", "FAIL", f"unsupported provider `{selected_provider}`")
    return DoctorCheck("AI provider", "WARN", "no AI provider configured; local guardrails will still run")


def check_ollama(model: str) -> DoctorCheck:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    request = urllib.request.Request(f"{host}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return DoctorCheck("AI provider", "FAIL", f"Ollama is not reachable at {host}: {exc}")
    models = {item.get("name") for item in data.get("models", [])}
    if model in models:
        return DoctorCheck("AI provider", "OK", f"Ollama reachable with model {model}")
    if models:
        available = ", ".join(sorted(str(item) for item in models if item))
        return DoctorCheck("AI provider", "FAIL", f"Ollama reachable but model {model} is missing; available: {available}")
    return DoctorCheck("AI provider", "FAIL", f"Ollama reachable but no models are installed; run `ollama pull {model}`")
