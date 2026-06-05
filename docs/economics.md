# Economics

Tripwire should identify changes that introduce hidden or poorly documented costs that may slow the project down later.

Watch for:

- API costs
- infrastructure costs
- operational burden
- marginal cost per user action
- unbounded growth in stored data or background work
- sensitive data exposure
- scaling assumptions
- latency regressions
- resource consumption

Changes that increase marginal cost per user interaction should explain why the new cost is justified or how it is bounded.

Economics is not the same as "anything involving storage, logs, models, or infrastructure." Tripwire should care about material cost, marginal cost, operational burden, unbounded growth, sensitive data exposure, latency, and complexity that slows the project down.

Bounded instrumentation can be economically positive when it helps prove whether the product is working, improves evaluation, or prevents wasted product work. Do not flag logging, review memory, evaluation storage, or model-adjacent records merely because they exist.

When reviewing an economics concern, ask what the cost is serving:

- user-facing product value
- product evaluation or learning
- operational reliability
- developer convenience
- unclear or unjustified accumulation

During judgment MVP validation, Tripwire should make model usage explicit and bounded. Any model-backed path should make the provider, model, expected input size, and failure behavior clear.

Tripwire should flag changes that:

- send large repository context to a model without truncation or selection
- add repeated model calls inside loops or interactive flows
- make hosted services mandatory before local value is proven
- introduce storage, synchronization, or background jobs without a validation payoff
