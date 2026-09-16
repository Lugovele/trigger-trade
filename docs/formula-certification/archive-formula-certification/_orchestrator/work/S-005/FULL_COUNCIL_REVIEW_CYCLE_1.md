# FULL_COUNCIL_REVIEW_CYCLE_1

# S-005 - Market Regime Classifier

## Council Record

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = APPROVED_SOLELY_AS_RESEARCH_DEMO_DIAGNOSTIC_BOUNDARY
TRADING_FITNESS_STATUS = UNVALIDATED_NOT_APPROVED_FOR_TRADING_DECISIONS
```

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_DIAGNOSTIC_ONLY | Candidate describes recent BTCUSDT price direction; it does not establish tradable trend, entry quality, continuation probability or suitability for another instrument. |
| Market Microstructure & Order Flow Researcher | APPROVE_DIAGNOSTIC_ONLY | Close-to-close returns contain no direct evidence of spread, depth, order flow, liquidity or execution quality. |
| Market Regime & Context Analyst | APPROVE_DIAGNOSTIC_ONLY | Canonical regime meaning, domain and timeframe remain undefined; diagnostic use is acceptable within candidate scope. |
| Quant Strategy Researcher | APPROVE_RESEARCH_ONLY | No empirical evidence validates features or thresholds; approval covers research examination, not estimator validity or predictive value. |
| Risk & Trade Management Architect | APPROVE_BOUNDARY_ONLY | S-005 receives no decision authority and must not affect Set, Position, sizing, exits, Portfolio approvals or execution eligibility. |
| Execution & Exchange Mechanics Specialist | APPROVE_RESEARCH_ONLY | Candidate preconditions are not certified exchange-data guarantees; demo runs require pinned sources/adapters and no live side effects. |
| Adversarial Strategy Reviewer | APPROVE_BOUNDARY_ONLY | Do not promote hardcoded thresholds, SIDEWAYS label or BTC proxy into methodology or hidden dependencies. |
| Performance & Strategy Diagnostics Analyst | APPROVE_RESEARCH_ONLY | Diagnostic studies need chronological out-of-sample evaluation; deterministic reproduction is not evidence of trading usefulness. |

## Status

No blocker exists to the explicitly limited diagnostic boundary. Canonical or
trading-input approval remains blocked by missing methodology, missing product
role, missing canonical domain/input/output contracts and absent empirical
validation.

## Known Limitations

- S-005 cannot appear as unknown baseline wire fields.
- S-005 cannot be silently consumed by current Position formulas.
- CTX-REGIME v0.1.0 remains a non-normative candidate.
- Any proposed trading use or canonical incorporation requires explicit product
  and methodology decision followed by new formula certification.

## Empirical Questions

- How stable are labels across windows, thresholds, volatility conditions and
  historical periods?
- Which price-path conditions accumulate in `SIDEWAYS`?
- Does BTC context explain relevant instrument behavior beyond each instrument's
  own history out of sample?
- How do candle revisions, gaps, flat steps, data availability and numeric
  precision affect label assignment?
- Does the diagnostic add measurable information beyond simpler baselines?
