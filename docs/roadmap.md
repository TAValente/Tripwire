# Roadmap

This roadmap is organized around review quality and project drift prevention, not feature volume.

## 1. Judgment MVP

Prove that Tripwire can review realistic diffs and identify meaningful project-alignment issues without becoming noisy.

Exit criteria:

1. Tripwire catches avoidable mistakes that would cause rework, dead ends, hidden cost, or strategic drift.
2. Tripwire stays silent on nitpicks and low-leverage concerns.
3. Tripwire explains the principle behind important findings when that improves future judgment.
4. Tripwire handles missing doctrine with Concrete Improvers instead of inventing intent.

## 2. Local Review Memory

Use local storage to learn whether Tripwire's reviews are useful.

Scope:

- store review runs
- store findings
- classify follow-up outcomes
- distinguish useful findings, false positives, ignored findings, addressed findings, and calibration questions

Local review memory is allowed because it improves review quality without adding product surface area. Hosted storage remains optional until local value is proven.

## 3. Doctrine Builder

Doctrine Builder evolves Tripwire from a local diff reviewer into a doctrine-aware project governance system.

The value is not document generation. The value is forcing clear thinking before AI-generated code creates drift.

Purpose:

Tripwire should help project owners create the doctrine docs that Tripwire later uses for review.

Core behavior:

- conduct a structured interview before or early in a project
- ask probing questions about product goals, users, non-goals, success criteria, failure modes, technical constraints, economic constraints, and deliberate tradeoffs
- challenge vague answers
- identify contradictions
- ask for specificity
- produce draft doctrine docs

Doctrine Builder should be able to draft:

- `docs/principles.md`
- `docs/economics.md`
- `docs/current_phase.md`
- `docs/anti_patterns.md`
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/learning.md`

Future reviews should cite doctrine when identifying drift:

- "This violates the economics doctrine because..."
- "This conflicts with the current phase because..."
- "This adds complexity inconsistent with the architecture doctrine because..."

MVP sequencing:

1. Doctrine completeness checker / Concrete Improver.
2. Interactive CLI doctrine interview.
3. Generate draft doctrine docs.
4. Doctrine-aware review citations.
5. Later, optional richer UI or GitHub workflow after CLI value is proven.

## 4. GitHub Review Workflow

Make manual PR review smooth enough to use while moving fast.

Scope:

- clear errors when GitHub CLI or auth is missing
- reliable PR diff loading
- target-repository doctrine loading
- optional local storage of review runs
- concise terminal output

GitHub review should remain a manual command during MVP validation. Bots and CI gates should wait until review quality is proven.

## 4.5. Doctrine Lifecycle Management

Doctrine Lifecycle Management is a future phase for keeping project doctrine stable enough to prevent drift while still allowing evidence-based evolution.

This phase should not be built until doctrine-aware review has proven valuable in ordinary review work. Before implementation, Tripwire should document the concept and the review-facing interfaces only: waivers, doctrine revision triggers, and doctrine history.

Problem:

Projects learn. Doctrine that never changes becomes wrong. Doctrine that changes constantly becomes meaningless.

Capabilities:

- doctrine review reminders
- explicit doctrine waivers
- waiver tracking
- repeated-waiver detection
- doctrine revision recommendations
- doctrine history and rationale

Example outputs:

- "This change violates doctrine but an approved waiver exists."
- "Three recent waivers have overridden the current phase doctrine. Consider updating the doctrine."
- "This doctrine has not been revisited since MVP despite multiple contradictory decisions."

Out of scope until the review value is proven:

- persistent waiver storage
- dashboards
- workflow systems
- approval routing
- notification systems
- automatic doctrine rewriting

See `docs/doctrine_lifecycle.md` for the conceptual interfaces.
