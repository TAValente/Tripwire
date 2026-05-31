from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewMode(str, Enum):
    STANDARD = "standard"
    PARANOID = "paranoid"
    ARCHITECTURE = "architecture"


@dataclass(frozen=True)
class DoctrineDocument:
    path: str
    content: str


@dataclass(frozen=True)
class ReviewInput:
    mode: ReviewMode
    diff: str
    doctrine: tuple[DoctrineDocument, ...]
    repository_context: str
    source_description: str
    user_concerns: str = ""


@dataclass(frozen=True)
class Finding:
    title: str
    severity: int
    confidence: str
    category: str
    reviewer_persona: str
    evidence: str
    why_it_matters: str
    acceptable_for_current_phase: str
    recommended_action: str

    def render(self) -> str:
        return "\n".join(
            [
                f"Title:\n{self.title}",
                "",
                f"Severity:\n{self.severity}",
                "",
                f"Confidence:\n{self.confidence}",
                "",
                f"Category:\n{self.category}",
                "",
                f"Reviewer Persona:\n{self.reviewer_persona}",
                "",
                f"Evidence:\n{self.evidence}",
                "",
                f"Why It Matters:\n{self.why_it_matters}",
                "",
                f"Acceptable For Current Phase?\n{self.acceptable_for_current_phase}",
                "",
                f"Recommended Action:\n{self.recommended_action}",
            ]
        )
