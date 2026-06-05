from __future__ import annotations

import re

from .models import Finding, ReviewInput, ReviewMode


def doctrine_text(review_input: ReviewInput) -> str:
    return "\n\n".join(document.content for document in review_input.doctrine).lower()


def doctrine_supports_cli_mvp_limits(text: str) -> bool:
    return (
        "tripwire" in text
        and "mvp validation" in text
        and "command-line interface" in text
        and ("dashboards" in text or "web interfaces" in text)
    )


def doctrine_supports_database_mvp_limit(text: str) -> bool:
    return "tripwire" in text and "mvp validation" in text and "databases" in text


def doctrine_supports_ai_cost_controls(text: str) -> bool:
    return (
        (
            "openai" in text
            or "llm" in text
            or "model calls" in text
            or "ai usage" in text
            or "api costs" in text
        )
        and ("cost" in text or "token" in text or "bounded" in text or "summaries over raw data" in text)
    )


def diff_updates_tripwire_local_ui_doctrine(added_lines: str) -> bool:
    lowered = added_lines.lower()
    return (
        ("local control panel" in lowered or "local ui" in lowered)
        and ("acceptable" in lowered or "out-of-the-box local project helper" in lowered)
    )


def diff_updates_tripwire_local_storage_doctrine(added_lines: str) -> bool:
    lowered = added_lines.lower()
    return (
        ("local memory" in lowered or "local storage" in lowered or "sqlite" in lowered)
        and ("acceptable" in lowered or "review quality" in lowered or "feedback" in lowered)
    )


def local_findings(review_input: ReviewInput) -> list[Finding]:
    diff = review_input.diff
    findings: list[Finding] = []
    doctrine = doctrine_text(review_input)

    if not diff.strip() and review_input.mode != ReviewMode.ARCHITECTURE:
        return findings

    added_lines = "\n".join(
        line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
    )

    if (
        doctrine_supports_cli_mvp_limits(doctrine)
        and not diff_updates_tripwire_local_ui_doctrine(added_lines)
        and re.search(
        r"\b(fastapi|flask|django|react|vite|next|dashboard|websocket)\b", added_lines, re.I
        )
    ):
        findings.append(
            Finding(
                title="MVP Scope May Be Expanding Beyond CLI Validation",
                severity=4,
                confidence="Medium",
                category="Scope Creep",
                reviewer_persona="Product Manager",
                evidence="The diff appears to add web or application framework surface while current doctrine says to avoid dashboards, web interfaces, and CI integrations during MVP validation.",
                why_it_matters="Tripwire's current phase is about proving review quality through a simple CLI. Expanding interface surface before that proof adds product and maintenance cost without validating the core reviewer.",
                acceptable_for_current_phase="Questionable",
                recommended_action="Keep the change CLI-first unless the doctrine is updated with a specific reason this interface is necessary for validating review quality.",
            )
        )

    if (
        doctrine_supports_ai_cost_controls(doctrine)
        and re.search(
            r"\b(openai|anthropic|llm|embedding|tokens)\b|responses\.create|chat\.completions|/api/generate",
            added_lines,
            re.I,
        )
        and not re.search(r"\b(cache|budget|limit|quota|max_tokens|cost)\b", added_lines, re.I)
    ):
        findings.append(
            Finding(
                title="AI Cost Controls Are Not Evident",
                severity=3,
                confidence="Medium",
                category="Economics Regression",
                reviewer_persona="Economics Watchdog",
                evidence="The diff appears to add AI-provider usage without nearby budgeting, caching, token limits, or cost controls.",
                why_it_matters="The project doctrine explicitly tracks AI economics. Unbounded model usage can make each request more expensive as context size or usage grows.",
                acceptable_for_current_phase="Questionable",
                recommended_action="Document the expected cost envelope and add a bounded request strategy such as explicit token limits, input truncation, or a cache where appropriate.",
            )
        )

    if (
        doctrine_supports_database_mvp_limit(doctrine)
        and not diff_updates_tripwire_local_storage_doctrine(added_lines)
        and re.search(
        r"\b(sqlalchemy|postgres|sqlite|migration|alembic|database|redis)\b", added_lines, re.I
        )
    ):
        findings.append(
            Finding(
                title="Persistent Infrastructure Appears Before Core Review Quality Is Proven",
                severity=4,
                confidence="Medium",
                category="Premature Abstraction",
                reviewer_persona="Engineer",
                evidence="The diff appears to introduce database or infrastructure dependencies while current phase guidance says not to build databases during MVP validation.",
                why_it_matters="Persistence can harden early assumptions and add operational burden before Tripwire has validated that its reviews are useful.",
                acceptable_for_current_phase="No",
                recommended_action="Defer persistent infrastructure unless this change includes a doctrine update explaining why storage is required for the current validation milestone.",
            )
        )

    return findings
