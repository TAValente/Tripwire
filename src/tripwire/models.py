from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class ReviewMode(str, Enum):
    STANDARD = "standard"
    PARANOID = "paranoid"
    ARCHITECTURE = "architecture"
    PROJECT_SCAN = "project_scan"


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
    missing_target_doctrine: bool = False


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

    def stable_key(self) -> str:
        payload = {
            "title": self.title,
            "category": self.category,
            "persona": self.reviewer_persona,
            "evidence": self.evidence,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def render(self) -> str:
        return "\n".join(
            [
                f"Title: {self.title}",
                "",
                f"Persona: {self.reviewer_persona}",
                "",
                f"Severity: {self.severity}",
                "",
                f"Category: {self.category}",
                "",
                f"Confidence: {self.confidence}",
                "",
                f"Evidence: {self.evidence}",
                "",
                f"Why: {self.why_it_matters}",
                "",
                f"Acceptable For Current Phase? {self.acceptable_for_current_phase}",
                "",
                f"Correction: {self.recommended_action}",
            ]
        )
