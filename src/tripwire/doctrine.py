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
)


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
