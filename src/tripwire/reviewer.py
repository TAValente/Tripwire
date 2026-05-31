from __future__ import annotations

from .ai import AIConfig, AIReviewError, ai_review
from .heuristics import local_findings
from .models import ReviewInput
from .prompt import build_review_prompt


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

    findings = local_findings(review_input)
    ai_warning = ""
    try:
        ai_result = ai_review(prompt, config=AIConfig(provider=provider, model=model))
    except AIReviewError as exc:
        ai_result = None
        ai_warning = f"\nAI provider warning: {exc}\n"
    if ai_result:
        if findings:
            rendered_findings = "\n\n---\n\n".join(finding.render() for finding in findings)
            ai_text = ai_result.strip()
            if ai_text == "No high-confidence strategic findings detected.":
                ai_text = ""
            return "\n".join(
                part
                for part in [
                    ai_text,
                    "---" if ai_text else "",
                    "Mistakes to Correct",
                    "",
                    rendered_findings,
                ]
                if part != ""
            )
        return ai_result

    if findings:
        rendered = "\n\n---\n\n".join(finding.render() for finding in findings)
        return "\n".join(
            [
                "Tripwire local review",
                "",
                "Mistakes to Correct",
                "",
                rendered,
                ai_warning,
                "",
                "Note: no AI provider was configured or reachable, so this review used local high-confidence checks only. Use --prompt-only to inspect the full review packet.",
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
