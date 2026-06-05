# Roadmap

This roadmap is organized around review quality and project drift prevention, not feature volume.

## Next Work Item: Doctrine Understanding Cache

Improve review power cheaply by helping the local model understand doctrine before each review.

Tripwire should create a cached project understanding packet from doctrine docs. The cache should be keyed by doctrine file hashes and reused in PR review and project scan so the model does not have to rediscover the project from scratch every run.

This is not embeddings yet. Start with a local, structured, inspectable cache.

Purpose:

Tripwire's hardest job is not reading more files. It is understanding what the project is trying to build, what matters now, and whether current work makes those priorities better, worse, unchanged, or unknown. A doctrine understanding cache should make cheap local models more effective by giving them stable, high-signal context every time.

The cached packet should include:

- project purpose
- current phase
- what matters most right now
- non-goals
- architecture constraints
- economics constraints
- anti-patterns
- important decisions
- open tensions or contradictions
- review guidance and what Tripwire should watch for

Requirements:

- local-first storage
- invalidates when doctrine files change
- inspectable by the user
- raw doctrine docs remain authoritative
- cached understanding is a compact aid to review quality, not a replacement for doctrine
- cached understanding must not become an unchallengeable source of truth
- if the cache is low-confidence, stale, or inconsistent with doctrine, Tripwire should disclose that rather than confidently reviewing from it

This is different from PR review memory. Doctrine cache is reusable context. PR memory is historical evidence about prior reviews, feedback, false positives, ignored findings, and changed PR outcomes.

MVP shape:

1. Compute hashes for loaded doctrine docs.
2. Generate a structured project understanding packet from those docs.
3. Store it locally with the source hashes and confidence notes.
4. Reuse it in PR review and project scan.
5. Add a CLI/UI inspection command so the user can see the packet and source hashes.
6. Disclose stale, missing, low-confidence, or contradictory doctrine understanding in review output.

Embeddings can come later if doctrine or repo context becomes too large. For now, structured cached understanding is higher leverage, easier to inspect, and easier to debug.

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

## 4.1. Local Control Panel

Make Tripwire usable as an out-of-the-box local project helper after one setup pass.

Purpose:

The user should not need to remember command syntax for routine review work.

Scope:

- run doctor checks
- choose a local model/provider
- list open GitHub PRs for a repository
- review a selected PR
- optionally store the review locally
- inspect local memory status

The control panel should wrap existing local commands. It should not introduce hosted deployment, product dashboards, required accounts beyond GitHub/Ollama setup, or new workflow machinery.

Setup should ask for only the choices that matter:

- model provider
- model name or model type
- GitHub authentication status
- local storage location only if the default is not acceptable

Exit criteria:

1. A user can review a GitHub PR without remembering the PowerShell command.
2. The UI makes local readiness visible before review.
3. The UI does not change Tripwire's local-first architecture.
4. The CLI remains available and authoritative.

## 4.2. Project Scan

Run a less frequent review that is not tied to one PR.

Purpose:

PR review should judge whether a PR introduced or worsened a meaningful issue. Project scan should catch longer-running problems that accumulate across PRs.

Scope:

- doctrine inconsistencies
- doctrine conflicts
- stale current-phase assumptions
- architecture/economics contradictions
- accumulated project drift
- repeated false positives that suggest doctrine or reviewer calibration needs work

Doctrine conflicts are a first-class scan concern. A useful scan finding should cite the conflicting docs or sections and explain how the conflict would slow the project down.

Project scan should not become a broad code review. It should stay focused on project direction, doctrine consistency, and review quality.

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
