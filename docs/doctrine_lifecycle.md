# Doctrine Lifecycle Management

Doctrine Lifecycle Management is a future Tripwire phase.

It exists to keep doctrine stable enough to prevent drift while allowing evidence-based evolution when the project learns something real.

Tripwire should not build storage, dashboards, approval workflow, notifications, or automated doctrine editing for this phase until doctrine-aware review has proven valuable in normal review use.

## Problem

Projects learn. Doctrine that never changes becomes wrong. Doctrine that changes constantly becomes meaningless.

Doctrine lifecycle work should protect two things at the same time:

1. Doctrine should remain strong enough to guide reviews and stop drift.
2. Doctrine should be revisable when repeated evidence shows that the documented guidance no longer matches good project judgment.

## Review Concept

Doctrine Lifecycle Management should begin as review language and interface design, not as product infrastructure.

The review engine should be able to reason about:

- whether a change violates active doctrine
- whether an explicit waiver applies
- whether repeated waivers suggest the doctrine itself may be stale
- whether doctrine has gone unrevisited through major project phase changes
- whether past doctrine rationale explains why the current rule still matters

The first useful version may only emit findings or calibration questions. That is enough until repeated use proves what data is worth storing.

## Waiver Interface

A doctrine waiver is an explicit, bounded exception to current doctrine.

Conceptual fields:

- doctrine reference: the document, section, or rule being waived
- change reference: the PR, diff, commit, or decision the waiver applies to
- rationale: why violating the doctrine is acceptable in this case
- scope: what the waiver permits and what it does not permit
- approver: the person or role accepting the exception
- expiration or revisit condition: when the waiver should stop applying
- review note: how Tripwire should describe the waiver during review

Example review output:

> This change violates doctrine but an approved waiver exists.

Tripwire should treat waivers as evidence, not as silence. A valid waiver can downgrade or explain a finding, but it should still preserve the fact that doctrine was overridden.

## Doctrine Revision Trigger Interface

A doctrine revision trigger is evidence that current doctrine may need review.

Conceptual trigger types:

- repeated waivers against the same doctrine
- contradictory accepted decisions
- phase change without doctrine revisit
- doctrine cited frequently but ignored in practice
- doctrine that no longer matches product, economic, or technical constraints
- doctrine that produces repeated false positives

Conceptual fields:

- doctrine reference: the rule or document under pressure
- evidence: waivers, accepted decisions, ignored findings, or review outcomes
- pattern summary: what has changed in practice
- recommendation: revisit, clarify, narrow, retire, or preserve the doctrine
- urgency: whether this is informational, worth review soon, or blocking useful review

Example review output:

> Three recent waivers have overridden the current phase doctrine. Consider updating the doctrine.

Revision triggers should recommend review, not mutate doctrine automatically.

## Doctrine History Interface

Doctrine history explains why doctrine changed and what tradeoff was accepted.

Conceptual fields:

- doctrine reference: the document or rule that changed
- previous guidance: the prior version or summary
- revised guidance: the new version or summary
- reason: what evidence justified the change
- decision context: project phase, constraints, or incidents that mattered
- author or approver: who accepted the revision
- effective date: when the revision started guiding reviews
- superseded rationale: what earlier reasoning is no longer valid, if any

Example review output:

> This doctrine has not been revisited since MVP despite multiple contradictory decisions.

Doctrine history should make doctrine more trustworthy. It should not become a separate governance system.

## Boundaries

Do not implement lifecycle infrastructure before doctrine-aware review is useful.

Specifically, avoid:

- persistent waiver storage
- dashboards
- approval routing
- notification systems
- workflow state machines
- automatic doctrine rewriting
- organization-wide policy management

The near-term goal is to make the review interface clear enough that future storage or workflows, if needed, follow observed review value instead of imagined process.
