from __future__ import annotations

import re

from .ai import AIConfig, AIReviewError, ai_review
from .heuristics import local_findings
from .models import ReviewInput
from .personas import PERSONAS
from .prompt import build_review_prompt


NO_FINDINGS = "No high-confidence strategic findings detected."


def clean_ai_output(output: str) -> str:
    text = output.strip()
    text = re.sub(r"(?is)<think>.*?</think>", "", text).strip()
    text = re.sub(r"(?is)</?think>", "", text).strip()
    text = re.sub(r"(?is)^thinking\.\.\..*?\.\.\.done thinking\.\s*", "", text).strip()

    allowed_starts = ("Mistakes to Correct", "Concrete Improvers", NO_FINDINGS)
    for marker in allowed_starts:
        index = text.find(marker)
        if index > 0:
            text = text[index:].strip()
            break

    if text.lower().startswith("jedis"):
        text = text[5:].strip()

    if not text.startswith(allowed_starts):
        return NO_FINDINGS

    return text or NO_FINDINGS


def missing_doctrine_improver(review_input: ReviewInput) -> str:
    if not review_input.missing_target_doctrine:
        return ""

    docs = []
    for persona in PERSONAS:
        docs.extend(persona.minimum_docs[:1])
    unique_docs = list(dict.fromkeys(docs))
    doc_list = "\n".join(f"- {item}" for item in unique_docs)

    return "\n".join(
        [
            "Concrete Improvers",
            "",
            "Title: Add Minimum Project Doctrine For Useful Tripwire Reviews",
            "",
            "Persona: Product Manager, Engineer, Economics Watchdog",
            "",
            "Why: Tripwire could not find target-repository doctrine docs on the PR base branch. Without project-specific doctrine, it cannot responsibly judge drift against intent.",
            "",
            "Improvement: Add the minimum docs Tripwire needs for this project:",
            doc_list,
        ]
    )


def review(
    review_input: ReviewInput,
    *,
    provider: str | None = None,
    model: str | None = None,
    prompt_only: bool = False,
) -> str:
    prompt = build_review_prompt(review_input)
    if prompt_only:
        return prompt

    findings = [] if review_input.missing_target_doctrine else local_findings(review_input)
    ai_warning = ""
    try:
        ai_result = ai_review(prompt, config=AIConfig(provider=provider, model=model))
    except AIReviewError as exc:
        ai_result = None
        ai_warning = f"\nAI provider warning: {exc}\n"
    if ai_result:
        ai_result = clean_ai_output(ai_result)
        if findings:
            rendered_findings = "\n\n---\n\n".join(finding.render() for finding in findings)
            ai_text = ai_result.strip()
            if ai_text == NO_FINDINGS:
                ai_text = ""
            improver = missing_doctrine_improver(review_input)
            return "\n".join(
                part
                for part in [
                    ai_text,
                    "---" if ai_text else "",
                    "Mistakes to Correct",
                    "",
                    rendered_findings,
                    "",
                    improver,
                ]
                if part != ""
            )
        improver = missing_doctrine_improver(review_input)
        if improver and ai_result.strip() == NO_FINDINGS:
            return improver
        if improver:
            return f"{ai_result}\n\n---\n\n{improver}"
        return ai_result

    if findings:
        rendered = "\n\n---\n\n".join(finding.render() for finding in findings)
        improver = missing_doctrine_improver(review_input)
        parts = [
            "Tripwire local review",
            "",
            "Mistakes to Correct",
            "",
            rendered,
        ]
        if improver:
            parts.extend(["", "---", "", improver])
        if ai_warning:
            parts.extend(["", ai_warning.strip()])
        parts.extend(
            [
                "",
                "Note: no AI provider was configured or reachable, so this review used local high-confidence checks only. Use --prompt-only to inspect the full review packet.",
            ]
        )
        return "\n".join(parts)

    improver = missing_doctrine_improver(review_input)
    if improver:
        return "\n".join(
            [
                "Tripwire local review",
                "",
                improver,
                ai_warning,
                "",
                "Note: no AI provider was configured or reachable, so this is not a full AI review. Use --prompt-only to inspect the full review packet.",
            ]
        )

    return "\n".join(
        [
            "Tripwire local review",
            "",
            "No high-confidence strategic findings detected by local checks.",
            ai_warning,
            "",
            "Note: no AI provider was configured or reachable, so this is not a full AI review. Use --prompt-only to inspect the full review packet.",
        ]
    )
