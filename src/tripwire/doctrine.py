from __future__ import annotations

from pathlib import Path

from .models import DoctrineDocument


DOCTRINE_PATHS = (
    "docs/principles.md",
    "docs/economics.md",
    "docs/current_phase.md",
    "docs/anti_patterns.md",
    "docs/architecture.md",
    "docs/decisions.md",
    "docs/learning.md",
)

DOCTRINE_PURPOSES = {
    "docs/principles.md": "core product principles, review priorities, and non-negotiable values",
    "docs/economics.md": "cost assumptions, paid APIs, model usage, hosting, storage, and cost controls",
    "docs/current_phase.md": "current project phase, near-term validation goal, and what to avoid right now",
    "docs/anti_patterns.md": "project-specific mistakes, distractions, and review noise to avoid",
    "docs/architecture.md": "major modules, data flow, storage boundaries, and external services",
    "docs/decisions.md": "intentional decisions, accepted tradeoffs, dependencies, and deviations",
    "docs/learning.md": "how reviews should teach judgment without becoming tutorials or noise",
}


def load_doctrine(root: Path) -> tuple[DoctrineDocument, ...]:
    documents: list[DoctrineDocument] = []
    for relative_path in DOCTRINE_PATHS:
        path = root / relative_path
        if path.exists():
            documents.append(
                DoctrineDocument(
                    path=relative_path,
                    content=path.read_text(encoding="utf-8").strip(),
                )
            )
    return tuple(documents)


def missing_doctrine_paths(root: Path) -> tuple[str, ...]:
    return tuple(path for path in DOCTRINE_PATHS if not (root / path).exists())


def missing_doctrine_document_paths(documents: tuple[DoctrineDocument, ...]) -> tuple[str, ...]:
    existing = {document.path for document in documents}
    return tuple(path for path in DOCTRINE_PATHS if path not in existing)


def render_doctrine_sufficiency(documents: tuple[DoctrineDocument, ...], *, source: str) -> str:
    missing = missing_doctrine_document_paths(documents)
    lines = [
        "Doctrine sufficiency",
        "",
        f"Source: {source}",
        f"Found: {len(documents)}/{len(DOCTRINE_PATHS)} doctrine docs",
    ]
    if documents:
        lines.extend(["", "Found docs:"])
        lines.extend(f"- {document.path}" for document in documents)
    if missing:
        lines.extend(["", "Missing docs:"])
        lines.extend(f"- {path}: {DOCTRINE_PURPOSES[path]}" for path in missing)
        lines.extend(
            [
                "",
                "Substantive review: limited",
                "Reason: Missing doctrine narrows Tripwire's ability to judge drift without inventing project intent.",
            ]
        )
    else:
        lines.extend(["", "Substantive review: available"])
    return "\n".join(lines)


def render_doctrine_completeness(root: Path) -> str:
    existing = load_doctrine(root)
    missing = missing_doctrine_paths(root)
    lines = [
        "Tripwire doctrine completeness",
        "",
        f"Root: {root}",
        f"Found: {len(existing)}/{len(DOCTRINE_PATHS)} doctrine docs",
    ]

    if existing:
        lines.extend(["", "Found docs:"])
        lines.extend(f"- {document.path}" for document in existing)

    if not missing:
        lines.extend(
            [
                "",
                "No missing doctrine docs.",
                "",
                "Concrete Improver",
                "",
                "Title: Keep Doctrine Specific As The Project Learns",
                "",
                "Why: Complete docs only help if they stay tied to real decisions, tradeoffs, and failure modes.",
                "",
                "Improvement: When Tripwire produces weak or noisy reviews, update doctrine with sharper principles, current-phase boundaries, economics assumptions, or known anti-patterns.",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "Missing docs:",
        ]
    )
    lines.extend(f"- {path}: {DOCTRINE_PURPOSES[path]}" for path in missing)
    lines.extend(
        [
            "",
            "Concrete Improver",
            "",
            "Title: Add Minimum Doctrine Before Trusting Drift Review",
            "",
            "Why: Tripwire reviews project alignment against project intent. Missing doctrine makes it easier for Tripwire to either stay vague or invent intent.",
            "",
            "Improvement: Add the missing docs above with short, specific notes. Start with the current phase, architecture boundaries, economics assumptions, and anti-patterns most likely to cause rework.",
        ]
    )
    return "\n".join(lines)
