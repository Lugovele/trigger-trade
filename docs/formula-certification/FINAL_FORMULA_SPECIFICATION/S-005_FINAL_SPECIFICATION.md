# FINAL_SPECIFICATION

# S-005 - Market Regime Classifier

**Artifact:** `S-005_FINAL_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED_RESEARCH_DEMO_DIAGNOSTIC_ONLY`
**Review:** Full Expert Council Review - Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Object ID | S-005 |
| Object name | Market regime classifier |
| Owner | Research |
| Object family | STATE_CLASSIFICATION_RULE |
| Reviewed candidate | `S-005_SOURCE_PACK` |
| Active methodology baseline | v1.2.14 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED_RESEARCH_DEMO_DIAGNOSTIC_ONLY
TRADING_FITNESS = UNVALIDATED_NOT_APPROVED_FOR_TRADING_DECISIONS
BLOCKING_FINDINGS_REMAINING = NONE_FOR_RESEARCH_DEMO_DIAGNOSTIC_BOUNDARY
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
CANONICAL_TRADING_INPUT_APPROVED = NO
IMPLEMENTATION_AND_LIVE_DEPLOYMENT = NOT_CERTIFIED
```

Approval is limited to research/demo diagnostic retention. It does not approve a
canonical formula, live trading input, runtime dependency, Set matching input,
Position input, Portfolio gate, Order Lifecycle input or execution behavior.

## 3. Intended Purpose

S-005 may be retained as a research/demo diagnostic context for examining market
regime labels in isolated, pinned research/backtest/demo runs.

It is not approved to answer a live trading decision question.

## 4. Actual Construct

The current implementation candidate, `CTX-REGIME@0.1.0`, is non-normative
current-code evidence. It describes recent BTCUSDT linear 1m close-to-close
price direction over 30 completed candles using hardcoded research thresholds.

Canonical formula, canonical domain, canonical input/output contract, canonical
numeric policy and live trading semantics remain undefined and uncertified.

## 5. Exact Formula / Rule

Non-normative candidate:

```text
window_return_pct =
  100 * (latest_close - first_close) / first_close

avg_abs_step_return_pct =
  mean(abs(step_return_pct over 29 steps))

normalized_trend =
  0 if avg_abs_step_return_pct == 0
  else window_return_pct / avg_abs_step_return_pct

directional_persistence =
  (up_steps - down_steps) / 29
```

Candidate labels:

```text
STRONG_UPTREND:
  window_return_pct >= 0.50
  AND normalized_trend >= 5
  AND directional_persistence >= 0.65

UPTREND:
  window_return_pct >= 0.15
  AND normalized_trend >= 2
  AND directional_persistence >= 0.35

STRONG_DOWNTREND:
  window_return_pct <= -0.50
  AND normalized_trend <= -5
  AND directional_persistence <= -0.65

DOWNTREND:
  window_return_pct <= -0.15
  AND normalized_trend <= -2
  AND directional_persistence <= -0.35

otherwise SIDEWAYS
```

This rule is not promoted to canonical product truth.

## 6. Inputs

Research/demo candidate inputs:

| Input | Candidate semantics |
|---|---|
| `symbol` | BTCUSDT in current code. |
| `category` | linear in current code. |
| `timeframe` | 1m. |
| `observed_at` | Equal to last candle close time. |
| `candles` | At least 30 contiguous completed 1m candles. |
| close prices | Positive values. |

Canonical methodology input requirements are missing.

## 7. Outputs

Research/demo diagnostic outputs may include context ID, symbol, timeframe,
observed time, capability, label, input snapshot, normalized features,
thresholds and reason.

Diagnostic labels may include:

```text
UNKNOWN
INSUFFICIENT_DATA
STRONG_UPTREND
UPTREND
SIDEWAYS
DOWNTREND
STRONG_DOWNTREND
```

`UNKNOWN` and `INSUFFICIENT_DATA` are diagnostic outcomes only and cannot be
interpreted as permission, safety or eligibility.

## 8. Units

- `window_return_pct`: percent.
- `avg_abs_step_return_pct`: percent.
- `normalized_trend`: unitless ratio.
- `directional_persistence`: unitless ratio over 29 steps.
- label: categorical diagnostic.

## 9. Parameters

All windows, thresholds, BTCUSDT scope and labels remain research/demo
parameters. They are not canonical thresholds.

## 10. Domain / Preconditions

Approved domain is research/demo diagnostic analysis only. The current-code
candidate is BTCUSDT linear 1m over completed candles and does not define the
regime of TriggerTrade's traded altcoin universe or any live trade eligibility.

## 11. Missing / Invalid Behavior

Unsupported symbol, category, timeframe, incomplete current candle, insufficient
data, non-contiguous window or non-positive close may produce `UNKNOWN` or
`INSUFFICIENT_DATA` as research diagnostics. These states cannot affect live
trading behavior.

## 12. Boundaries

S-005 must not affect:

- Set matching;
- certified F-005 direction;
- Position decisions;
- sizing;
- stops or take profits;
- Portfolio approvals;
- Order Lifecycle behavior;
- live or paper execution eligibility.

It cannot appear as unknown baseline wire fields or be silently consumed by
current Position formulas.

## 13. Precision / Rounding

The current code uses decimal arithmetic, but no canonical numeric policy is
approved for S-005. Any future canonical use must define numeric precision and
serialization explicitly.

## 14. Time Semantics

The candidate uses 30 completed 1m candles and requires observation at the last
candle close. Active methodology does not approve this as a canonical regime
timeframe or cadence.

## 15. State / Replay / Restart

Research/backtest/demo runs using S-005 must pin methodology package revision,
contract versions, configuration IDs/content digests, numeric policy IDs,
historical selectors/source snapshots, adapter/profile assumptions and execution
simulation assumptions.

No live runtime state machine depends on S-005 in the certified baseline.

## 16. Version / Configuration Pinning

`CTX-REGIME@0.1.0` is implementation metadata for a non-normative candidate. It
is not an approved active methodology version.

## 17. Dependencies

| Dependency | Classification | Notes |
|---|---|---|
| Active canonical methodology definition | UNKNOWN / MISSING | Required for any future live/canonical use. |
| M-008 | RESEARCH_PARAMETER | Research grouping, direction mix and regime aggregation. |
| BACKEND_TARGET_MODEL research boundary | DOCUMENTATION_DEPENDENCY | Research/backtest isolation and no live side effects. |
| Current implementation | NON_NORMATIVE_DOCUMENTATION_DEPENDENCY | Evidence of candidate only, not product authority. |

## 18. Ownership

Owner: Research.

S-005 is not Set's canonical Market Handoff, not a Position Rules input and not
owned by Portfolio or Order Lifecycle.

## 19. Pipeline Role

```text
Research/backtest/demo diagnostics only
→ no certified live trading pipeline authority
```

## 20. Approved Uses

- Isolated research/demo diagnostic calculation.
- Historical analysis and reporting when pins and assumptions are retained.
- Exploration of candidate regime labels without changing trading behavior.

## 21. Prohibited Interpretations

S-005 is not:

- a certified live trading input;
- a Set match condition;
- a Position decision input;
- a risk gate;
- a Portfolio approval gate;
- an Order Lifecycle input;
- a claim of execution quality, liquidity, trend continuation or profitability;
- approval of BTCUSDT as a proxy for all traded instruments;
- approval of hardcoded thresholds as product truth.

## 22. Known Limitations

- No canonical methodology definition exists.
- No live product role exists.
- No empirical validation of thresholds, labels, timeframe, BTC proxy relevance
  or usefulness is included.
- `SIDEWAYS` is residual failure of directional conditions, not proof of a
  ranging or low-volatility market.
- Implementation correctness and isolation are not certified by this document.

## 23. Research Parameters

- Lookback window.
- Timeframe.
- Symbol/proxy universe.
- Return thresholds.
- Normalized-trend thresholds.
- Directional-persistence thresholds.
- Label precedence and grouping.

## 24. Empirical Validation Requirements

Any future use beyond research/demo diagnostics requires out-of-sample analysis
of label stability, threshold sensitivity, BTC proxy relevance, data quality,
overlapping-window bias and incremental information beyond simpler baselines.

## 25. Eight Final Expert Verdicts

| Expert perspective | Final verdict |
|---|---|
| Senior Intraday Crypto Trader | APPROVE_DIAGNOSTIC_ONLY |
| Market Microstructure & Order Flow Researcher | APPROVE_DIAGNOSTIC_ONLY |
| Market Regime & Context Analyst | APPROVE_DIAGNOSTIC_ONLY |
| Quant Strategy Researcher | APPROVE_RESEARCH_ONLY |
| Risk & Trade Management Architect | APPROVE_BOUNDARY_ONLY |
| Execution & Exchange Mechanics Specialist | APPROVE_RESEARCH_ONLY |
| Adversarial Strategy Reviewer | APPROVE_BOUNDARY_ONLY |
| Performance & Strategy Diagnostics Analyst | APPROVE_RESEARCH_ONLY |

## 26. Final Council Record

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = APPROVED_SOLELY_AS_RESEARCH_DEMO_DIAGNOSTIC_BOUNDARY
TRADING_FITNESS_STATUS = UNVALIDATED_NOT_APPROVED_FOR_TRADING_DECISIONS
```
