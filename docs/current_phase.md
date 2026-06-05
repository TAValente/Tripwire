# Current Phase

Tripwire is in MVP validation.

The first objective is proving that Tripwire consistently catches avoidable mistakes that would slow a project down later.

Success in this phase means Tripwire can repeatedly do three things on realistic changes:

1. Flag avoidable mistakes that would cause rework, dead ends, hidden cost, or strategic drift.
2. Stay silent on nitpicks and low-leverage concerns.
3. Ask useful calibration questions when uncertainty is worth learning from.

Feature breadth is secondary to judgment quality.

Acceptable in this phase:

- a command-line interface
- a simple local control panel that wraps common commands
- terminal output
- simple repository and diff loading
- narrow, high-confidence review findings
- fixture-based evaluation
- local-only review memory used to validate finding quality over time
- manual review of real or realistic changes
- lightweight local storage when it directly improves review quality, evaluation, learning, or review memory
- one-time local setup with a few explicit choices, such as model provider, model, GitHub auth, and storage location
- a less frequent project scan for doctrine conflicts and accumulated drift

Avoid in this phase:

- dashboards
- hosted web apps
- product dashboards or hosted app complexity
- product databases before the product needs one
- premature workflow automation
- CI integrations
- GitHub bots
- broad autonomous refactoring behavior

Do not build a product database before the product needs one. Local memory and evaluation storage are acceptable when they increase review quality without adding product surface area.

Local review memory should serve judgment calibration. It should help answer whether findings were useful, ignored, false positive, addressed, or worth asking about later. It should not become a dashboard, analytics product, or required hosted service during this phase.

Tripwire should feel like an out-of-the-box local project helper after setup. The user should not need to remember command syntax for ordinary work. A local UI is acceptable when it reduces friction around existing review, doctor, GitHub, and memory flows without adding hosted infrastructure or changing the product into a dashboard.

PR review and project scan are different workflows. PR review should ask whether a change introduced or worsened a meaningful issue. Project scan should ask whether the project is accumulating drift, doctrine conflicts, stale assumptions, or review-quality problems across changes.

Both lanes must make their review target visible. PR review should combine the PR diff with the target repository's doctrine from the PR base branch. Project scan should name the repository being scanned and disclose whether enough doctrine exists for substantive review before making broad drift claims.
