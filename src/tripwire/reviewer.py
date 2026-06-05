from __future__ import annotations

import re

from .ai import AIConfig, AIReviewError, ai_review
from .heuristics import local_findings
from .models import ReviewInput
from .personas import PERSONAS
from .prompt import build_review_prompt


NO_FINDINGS = "No high-confidence strategic findings detected."


def build_alignment_retry_prompt(prompt: str) -> str:
    return "\n\n".join(
        [
            prompt,
            "# Required Correction",
            (
                "The previous response used the legacy green-check sentence as the whole review. "
                "That is not a valid Tripwire review anymore. Produce the review again using exactly these sections: "
                "Project Understanding, Alignment Assessment, Findings, Emergent Concerns, "
                "Suppressed / Calibration, Confidence Limits. "
                "Findings may be `None.` and Suppressed / Calibration may be `None.`, but the Alignment Assessment "
                "must identify the important project priorities and judge whether each is better, worse, "
                "unchanged, or unknown from the available evidence. Do not summarize or explain the diff. "
                "Do not treat repository names inside tests, docs, fixtures, or example strings as the review target."
            ),
        ]
    )


def alignment_unavailable_output(review_input: ReviewInput) -> str:
    doctrine_paths = {document.path for document in review_input.doctrine}

    def rating(path: str) -> str:
        return "medium" if path in doctrine_paths else "low"

    current_phase = rating("docs/current_phase.md")
    economics = rating("docs/economics.md")
    architecture = rating("docs/architecture.md")
    roadmap_decisions = "medium" if "docs/decisions.md" in doctrine_paths else "low"
    if review_input.doctrine and all(
        path in doctrine_paths
        for path in (
            "docs/current_phase.md",
            "docs/economics.md",
            "docs/architecture.md",
            "docs/decisions.md",
        )
    ):
        current_phase = economics = architecture = roadmap_decisions = "high"

    return "\n".join(
        [
            "Project Understanding",
            "",
            f"Current phase: {current_phase}",
            f"Economics: {economics}",
            f"Architecture: {architecture}",
            f"Roadmap/decisions: {roadmap_decisions}",
            "Key confidence limits: The configured AI model did not produce the required alignment review after a retry.",
            "",
            "Alignment Assessment",
            "",
            "Priority: Review reliability",
            "Direction: unknown",
            "PR Causality: unknown" if review_input.diff.strip() else "Causality: not tied to one PR",
            "Confidence: high",
            "Evidence: Tripwire could assemble the review packet, but the model returned a legacy no-findings response instead of judging project priorities.",
            "",
            "Findings",
            "",
            "None.",
            "",
            "Emergent Concerns",
            "",
            "The review result is not strong enough to support a confident no-findings conclusion.",
            "",
            "Suppressed / Calibration",
            "",
            "None.",
            "",
            "Confidence Limits",
            "",
            "Tripwire did not receive a valid alignment assessment from the configured model. Inspect the prompt with --prompt-only, retry, or use a stronger local model before treating this as a substantive review.",
        ]
    )


def clean_ai_output(output: str) -> str:
    text = output.strip()
    text = re.sub(r"(?is)<think>.*?</think>", "", text).strip()
    text = re.sub(r"(?is)</?think>", "", text).strip()
    text = re.sub(r"(?is)^thinking\.\.\..*?\.\.\.done thinking\.\s*", "", text).strip()
    text = re.sub(r"(?m)^\s{0,3}\*\*(Project Understanding|Alignment Assessment|Findings|Emergent Concerns|Suppressed / Calibration|Confidence Limits|Mistakes to Correct|Concrete Improvers|Suppressed Finding)\*\*\s*$", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+(?=Project Understanding|Alignment Assessment|Findings|Emergent Concerns|Suppressed / Calibration|Confidence Limits|Mistakes to Correct|Concrete Improvers|Suppressed Finding)", "", text)

    allowed_starts = (
        "Project Understanding",
        "Alignment Assessment",
        "Findings",
        "Mistakes to Correct",
        "Concrete Improvers",
        NO_FINDINGS,
        "Suppressed Finding",
        "Suppressed / Calibration",
    )
    matches: list[tuple[int, str]] = []
    for marker in allowed_starts:
        match = re.search(rf"(?m)^{re.escape(marker)}(?:\s*$|\s*\n)", text)
        if match:
            matches.append((match.start(), marker))
    if matches:
        index, _marker = min(matches, key=lambda item: item[0])
        text = text[index:].strip()

    if text.lower().startswith("jedis"):
        text = text[5:].strip()

    if not text.startswith(allowed_starts):
        return NO_FINDINGS

    if text.startswith("Suppressed Finding") or text.startswith("Suppressed / Calibration"):
        return f"{NO_FINDINGS}\n\n{text}"

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
        if ai_result == NO_FINDINGS:
            try:
                retry_result = ai_review(
                    build_alignment_retry_prompt(prompt),
                    config=AIConfig(provider=provider, model=model),
                )
            except AIReviewError:
                retry_result = ""
            retry_result = clean_ai_output(retry_result) if retry_result else ""
            if retry_result and retry_result != NO_FINDINGS:
                ai_result = retry_result
            else:
                ai_result = alignment_unavailable_output(review_input)
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
