from __future__ import annotations

import re

from .models import Finding, ReviewInput, ReviewMode


def local_findings(review_input: ReviewInput) -> list[Finding]:
    diff = review_input.diff
    findings: list[Finding] = []

    if not diff.strip() and review_input.mode != ReviewMode.ARCHITECTURE:
        return findings

    added_lines = "\n".join(
        line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
    )

    if re.search(r"\b(fastapi|flask|django|react|vite|next|dashboard|websocket)\b", added_lines, re.I):
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

    if re.search(r"\b(openai|anthropic|llm|embedding|tokens|completion|responses)\b", added_lines, re.I) and not re.search(
        r"\b(cache|budget|limit|quota|max_tokens|cost)\b", added_lines, re.I
    ):
        findings.append(
            Finding(
                title="AI Cost Controls Are Not Evident",
                severity=3,
                confidence="Medium",
                category="Economics Regression",
                reviewer_persona="Economics Watchdog",
                evidence="The diff appears to add AI-provider usage without nearby budgeting, caching, token limits, or cost controls.",
                why_it_matters="Tripwire explicitly tracks unit economics regressions. Unbounded AI calls can make each review more expensive as repository size or usage grows.",
                acceptable_for_current_phase="Questionable",
                recommended_action="Document the expected cost envelope and add a bounded request strategy such as explicit token limits, input truncation, or a cache where appropriate.",
            )
        )

    if re.search(r"\b(sqlalchemy|postgres|sqlite|migration|alembic|database|redis)\b", added_lines, re.I):
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
