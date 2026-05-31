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
