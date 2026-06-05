from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ReviewInput


@dataclass(frozen=True)
class GroundingResult:
    ok: bool
    errors: tuple[str, ...] = ()


REQUIRED_SECTIONS = (
    "Project Understanding",
    "Alignment Assessment",
    "Findings",
    "Emergent Concerns",
    "Suppressed / Calibration",
    "Confidence Limits",
)

PROJECT_UNDERSTANDING_FIELDS = (
    "Current phase:",
    "Economics:",
    "Architecture:",
    "Roadmap/decisions:",
    "Key confidence limits:",
)

ALIGNMENT_FIELDS = (
    "Priority:",
    "Direction:",
    "Confidence:",
    "Evidence:",
)


def source_corpus(review_input: ReviewInput) -> str:
    doctrine = "\n\n".join(
        f"{document.path}\n{document.content}" for document in review_input.doctrine
    )
    return "\n\n".join(
        [
            review_input.source_description,
            review_input.repository_context,
            doctrine,
            review_input.user_concerns,
            review_input.diff,
        ]
    ).lower()


def section(output: str, heading: str) -> str:
    headings = "|".join(re.escape(item) for item in REQUIRED_SECTIONS)
    pattern = rf"(?ms)^{re.escape(heading)}\s*:?\s*\n(.*?)(?=^(?:{headings})\s*:?\s*$|\Z)"
    match = re.search(pattern, output)
    return match.group(1).strip() if match else ""


def evidence_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if line.strip().lower().startswith("evidence:")
        and line.split(":", 1)[1].strip()
    )


def content_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text.lower()))
    stopwords = {
        "about",
        "after",
        "also",
        "because",
        "before",
        "better",
        "change",
        "could",
        "current",
        "evidence",
        "found",
        "from",
        "high",
        "inspect",
        "issue",
        "medium",
        "project",
        "review",
        "tripwire",
        "unknown",
        "worse",
    }
    return tokens - stopwords


def is_grounded(evidence: str, corpus: str) -> bool:
    lowered = evidence.lower()
    if any(
        phrase in lowered
        for phrase in (
            "did not inspect",
            "not inspected",
            "not enough evidence",
            "insufficient evidence",
            "model did not produce",
            "review packet",
        )
    ):
        return True
    tokens = content_tokens(evidence)
    if not tokens:
        return False
    present = sum(1 for token in tokens if token in corpus)
    needed = min(3, max(1, len(tokens) // 2))
    return present >= needed


def validate_grounding(review_input: ReviewInput, output: str) -> GroundingResult:
    errors: list[str] = []
    for required in REQUIRED_SECTIONS:
        if not re.search(rf"(?m)^{re.escape(required)}\s*:?\s*$", output):
            errors.append(f"Missing section: {required}")

    understanding = section(output, "Project Understanding")
    for field in PROJECT_UNDERSTANDING_FIELDS:
        if field.lower() not in understanding.lower():
            errors.append(f"Project Understanding missing field: {field}")

    alignment = section(output, "Alignment Assessment")
    for field in ALIGNMENT_FIELDS:
        if field.lower() not in alignment.lower():
            errors.append(f"Alignment Assessment missing field: {field}")
    if review_input.diff.strip() and "pr causality:" not in alignment.lower():
        errors.append("Alignment Assessment missing field: PR Causality:")

    emergent = section(output, "Emergent Concerns")
    if emergent and not re.search(r"(?im)^\s*none\.?\s*$", emergent):
        if "evidence:" not in emergent.lower():
            errors.append("Emergent Concerns must be None or include Evidence.")

    corpus = source_corpus(review_input)
    for evidence in evidence_lines(alignment) + evidence_lines(section(output, "Findings")) + evidence_lines(emergent):
        if not is_grounded(evidence, corpus):
            errors.append(f"Ungrounded evidence: {evidence[:120]}")

    return GroundingResult(ok=not errors, errors=tuple(errors[:8]))
