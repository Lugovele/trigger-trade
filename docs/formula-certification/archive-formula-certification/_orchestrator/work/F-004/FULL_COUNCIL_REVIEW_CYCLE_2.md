# F-004 Full Council Review Cycle 2

```text
formula_id: F-004
review_mode: REVALIDATION
all_eight_perspectives_applied: YES
full_council_approved: NO
another_review_cycle_required: YES
blocking_findings_remaining: F004-C02
```

## Council Decision

The arithmetic subset and local 5m ATR dependency passed re-review. F004-C02
was partially closed, but residual population-selection ambiguities remain
blocking:

1. inception and initialization-day eligibility;
2. midnight same-clock turnover reference selection.

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | CHANGES_REQUIRED | Composite is conceptually suitable as directional evidence, but initial-history and midnight selection must be deterministic. |
| Market Microstructure & Order Flow Researcher | CHANGES_REQUIRED | Quote-notional turnover and aggressive flow remain distinct from F-002 base volume; inception-day and same-clock membership remain incomplete. |
| Market Regime & Context Analyst | CHANGES_REQUIRED | Completed-day normalization is coherent; ambiguous initialization-day treatment changes distribution and warmup availability. |
| Quant Strategy Researcher | CHANGES_REQUIRED | Exact arithmetic, population variance, Q36 sqrt, inclusive percentile rank and weighted aggregation pass; population still needs unique determination. |
| Risk & Trade Management Architect | CHANGES_REQUIRED | Missing factors cannot become neutral contributions; initial-history eligibility must be reproducible. |
| Execution & Exchange Mechanics Specialist | CHANGES_REQUIRED | 5m ATR instance, precision and replay obligations are supported; same-clock selector remains ambiguous. |
| Adversarial Strategy Reviewer | CHANGES_REQUIRED | Partial inception days, legitimate pre-seed unavailability and midnight current-bucket exclusion remain exposed cases. |
| Performance & Strategy Diagnostics Analyst | CHANGES_REQUIRED | Diagnostics remain distinguishable; reproducible cohort membership requires closure. |

## Finding Closure

| Finding | Closure status |
|---|---|
| F004-C01 | CLOSED through cited dependency. Preserve SET Part II §4 completed 5m/15m/1h selection dependency. |
| F004-C02 | PARTIALLY CLOSED; BLOCKING. Fixed UTC boundaries, ordinary missing-data rejection and historical unavailable-value handling improved, but initial partial/initialization days and midnight same-clock selection remain unresolved. |
| F004-C03 | CLOSED through explicit local 5m definition and numeric-policy dependency; does not extend F-003's 15m certification. |
| F004-C04 | CLOSED. F-004 owns analytics/diagnostics; F-005 owns thresholds, side choice, veto consumption, direction and handoff. |
| F004-C05 | CLOSED. Score uses exact weighted products and one final Q36 quantizer; rounded contributions are diagnostics only. |
| F004-C06 | RETAINED; NON_BLOCKING empirical questions. |
| F004-C07 | RETAINED; NON_BLOCKING limitations. |

## Required Revisions

### F004-C02: inception and initialization days

Classification: `SPECIFICATION_DEFECT`, with a narrow product-behavior choice
needed only if the orchestrator could not select a deterministic interpretation.

Required language:

- define whether a partial inception day counts;
- identify the first countable full UTC day for each metric;
- specify whether proven initial derived-value unavailability permits exclusion
  of a leading initialization prefix;
- preserve canonical ATR processing through that prefix;
- prohibit omitting later unavailable observations;
- state historical zero-close ATR_PCT and non-positive VNM denominator
  consequences.

### F004-C02: midnight same-clock references

Classification: `SPECIFICATION_DEFECT`, with a product-behavior choice needed
only if the intended selector cannot be derived.

Required language:

- choose and state the exact selector;
- define lower boundary, current-bucket exclusion, reference count and
  fourteen-reference minimum;
- persist selected bucket identities.

The Council noted that retaining `[D-30 days,D)` and excluding a midnight
current bucket yields 29 references with full history, while selecting thirty
days preceding the current bucket's date reaches one day farther back.

## Compatibility and Fitness

The Cycle 1 arithmetic subset is preserved. F-001 remains current-slot,
direction-neutral formation evidence; F-002 remains separate 60-minute
base-volume confirmation; F-003 supplies 15m work ATR_PCT only. The local 5m
instance is supported by numeric-policy anchor, consecutive seed, update,
identity persistence, idempotence and replay requirements.

Trading fitness is conceptually adequate for the declared analytical role once
population selection is complete. Empirical effectiveness, parameter optimality
and live readiness remain unestablished.
