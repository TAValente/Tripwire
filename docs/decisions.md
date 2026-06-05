# Decisions

Initial CLI targets:

- `tripwire review`
- `tripwire review --staged`
- `tripwire review main`
- `tripwire review-pr`
- `tripwire github`
- `tripwire personas`
- `tripwire paranoid`
- `tripwire architecture`

Reviewer personas:

- Engineer: maintainability, architecture drift, technical debt, hidden complexity, data model integrity.
- Product Manager: user value, requirement compliance, scope creep, overengineering, feature prioritization.
- Economics Watchdog: API costs, infrastructure costs, operational burden, scaling assumptions, latency regressions, resource consumption.

Finding categories:

- Architecture Drift
- Economics Regression
- Requirement Violation
- Scope Creep
- Premature Abstraction
- Hidden Complexity
- Maintainability Risk
- Data Model Risk
- Operational Risk
- Security Risk
- Strategic Inconsistency

MVP validation decisions:

- The CLI is the primary interface.
- Local-first operation is required.
- A thin local control panel is acceptable to remove command memorization from ordinary use.
- Tripwire is model-driven; AI judgment is core to the product.
- Deterministic local guardrails are support and fallback, and should still run when AI is configured.
- Local SQLite memory is acceptable for validating whether findings are useful over time.
- Supabase and other hosted backends are optional and should not become required for ordinary local use.
- GitHub PR review is a manual command, not a bot or CI gate during MVP validation.
- Tripwire's own doctrine must not be used as replacement doctrine for projects it reviews.
