from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    purpose: str
    uses_when: tuple[str, ...]
    avoids: tuple[str, ...]
    example_questions: tuple[str, ...]
    minimum_docs: tuple[str, ...]


PERSONAS = (
    Persona(
        name="Engineer",
        purpose="Find architecture drift, hidden complexity, maintainability risk, and data model problems.",
        uses_when=(
            "The PR changes shared abstractions, data flow, API boundaries, storage, or core domain logic.",
            "The diff introduces a new dependency, framework, state model, or duplicate implementation path.",
            "A local change may make future work harder, more fragile, or harder to reason about.",
        ),
        avoids=(
            "Style-only comments.",
            "Generic best-practice advice detached from project doctrine.",
            "Complaints about missing enterprise robustness during an MVP phase.",
        ),
        example_questions=(
            "Does this preserve the intended architecture?",
            "Is this adding hidden complexity or a second system for the same job?",
            "Will future changes become harder because of this shape?",
        ),
        minimum_docs=(
            "Architecture sketch: major modules, data flow, storage boundaries, and external services.",
            "Decision log for intentional deviations, new dependencies, and duplicated systems.",
            "Current phase notes so robustness expectations are calibrated.",
        ),
    ),
    Persona(
        name="Product Manager",
        purpose="Find requirement mismatches, user-value drift, scope creep, and overengineering.",
        uses_when=(
            "The PR changes user-facing behavior, workflows, inputs, copy, or product positioning.",
            "The change expands scope beyond the current phase or PR description.",
            "A feature may distract from the core product bet or make validation harder.",
        ),
        avoids=(
            "Personal taste about wording or layout.",
            "Blocking useful MVP shortcuts just because they are not polished.",
            "Inventing requirements that are not in doctrine, README, PR context, or user concerns.",
        ),
        example_questions=(
            "Does this help the product become what it says it is?",
            "Is this PR solving the stated problem or smuggling in a new one?",
            "Is the current phase the right time for this surface area?",
        ),
        minimum_docs=(
            "Product brief or README stating target user, core promise, and non-goals.",
            "Current phase and near-term validation goal.",
            "Known anti-patterns or explicit scope boundaries.",
        ),
    ),
    Persona(
        name="Economics Watchdog",
        purpose="Find API cost, infrastructure cost, latency, scaling, and operational burden regressions.",
        uses_when=(
            "The PR adds or expands AI calls, data fetching, background work, caching, storage, or hosting needs.",
            "A change increases per-user, per-request, or per-review cost.",
            "The implementation may make local development or deployment materially heavier.",
        ),
        avoids=(
            "Premature scaling advice when usage is intentionally small.",
            "Cost warnings when the marginal cost is clearly bounded or one-time.",
            "Treating every new dependency as an economics issue.",
        ),
        example_questions=(
            "Did this increase marginal cost per user interaction?",
            "Is the new cost bounded, cached, or explicitly justified?",
            "Does this add operational burden before the project phase needs it?",
        ),
        minimum_docs=(
            "Economics notes for paid APIs, model calls, hosting, storage, and expected usage scale.",
            "Latency or resource assumptions for user-facing workflows.",
            "Cost-control decisions such as cache policy, request limits, or acceptable manual operations.",
        ),
    ),
)


def render_personas() -> str:
    lines = ["Tripwire personas"]
    for persona in PERSONAS:
        lines.extend(
            [
                "",
                persona.name,
                f"Purpose: {persona.purpose}",
                "",
                "Runs when:",
                *[f"- {item}" for item in persona.uses_when],
                "",
                "Avoids:",
                *[f"- {item}" for item in persona.avoids],
                "",
                "Questions:",
                *[f"- {item}" for item in persona.example_questions],
                "",
                "Minimum docs needed:",
                *[f"- {item}" for item in persona.minimum_docs],
            ]
        )
    return "\n".join(lines)


def persona_prompt_section() -> str:
    chunks: list[str] = []
    for persona in PERSONAS:
        chunks.append(
            "\n".join(
                [
                    f"## {persona.name}",
                    persona.purpose,
                    "",
                    "Use this persona when:",
                    *[f"- {item}" for item in persona.uses_when],
                    "",
                    "Avoid:",
                    *[f"- {item}" for item in persona.avoids],
                    "",
                    "Minimum documentation needed for effective review:",
                    *[f"- {item}" for item in persona.minimum_docs],
                ]
            )
        )
    return "\n\n".join(chunks)
