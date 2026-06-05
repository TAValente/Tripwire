# Architecture

Tripwire is a local-first project consistency checker.

Version 1 should:

1. Load doctrine documents.
2. Load repository context.
3. Read git diff.
4. Generate structured findings.
5. Output findings through a small local surface.

The git diff is the primary object under review. Repository context, doctrine documents, test output, build status, and evaluation results may provide supporting context.

Tripwire is not a coding assistant, code generator, linter, formatter, full test runner, CI gate, or autonomous refactoring tool.

Tripwire is not primarily a test runner or CI gate. It may consume test output, build status, or evaluation results as supporting evidence, but its core job is project-alignment review.

The CLI remains the review engine and most inspectable interface. A local browser control panel may wrap common commands so the project owner can click through doctor checks, GitHub PR selection, review runs, and local memory. That UI must stay local, thin, and practical. It should not require hosted accounts, remote databases, deployment, or workflow automation.

## Doctrine Boundaries

Tripwire's own doctrine governs development of Tripwire only.

When reviewing another project, Tripwire must use that project's doctrine, explicit user concerns, and repository evidence. It must not import Tripwire's own current phase, architecture preferences, or product constraints into the reviewed project.

If a target project lacks doctrine, Tripwire should say that useful drift review is limited and recommend the minimum missing doctrine. It should not pretend that Tripwire's doctrine is a safe substitute.

## Boundaries

Tripwire should keep the review engine separable from input sources and output surfaces. Git, GitHub, local storage, and model providers are adapters around the core review flow, not the center of the product.

The core review flow should stay understandable:

1. Gather doctrine.
2. Gather the change under review.
3. Gather only enough repository context to judge the change.
4. Produce findings or explain why useful review is not possible.
5. Optionally record the review for validation.

New architecture should be justified by review quality, not by imagined future scale.

## Judgment Guardrails

Tripwire should be careful with deterministic suppression rules.

Deterministic checks are useful for factual plumbing: missing doctrine, missing GitHub auth, malformed output, unavailable model providers, and other conditions where the tool can know the state directly.

Deterministic rules should not quietly replace reviewer judgment. A hardcoded suppression can remove noise, but it can also create blindspots. When Tripwire produces a false positive, prefer storing the outcome and feeding that calibration into future reviews over adding narrow hidden filters.

Any deterministic suppression that affects findings should be:

1. Narrow.
2. Visible in code and tests.
3. Based on repeated confirmed false positives.
4. Revisited when project doctrine changes.
