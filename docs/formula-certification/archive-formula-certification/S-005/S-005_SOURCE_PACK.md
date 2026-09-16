# S-005 Source Pack

# S-005 - Market Regime Classifier

## 1. Identity

| Field | Value |
|---|---|
| Object ID | S-005 |
| Object name | Market regime classifier |
| Owner | Research |
| Object family | STATE_CLASSIFICATION_RULE |
| Certification phase | Source Pack |
| Active methodology baseline | v1.2.14 |
| Source Pack status | Immutable pre-review provenance |

S-005 covers the current market regime classifier candidate. The catalog marks
it as missing a canonical methodology definition and not approved as a canonical
trading input.

## 2. Source Index

| Source | Evidence |
|---|---|
| `docs/FORMULA_METRICS_CATALOG.md` | S-005 row: Market regime classifier; area Research; source `MISSING_CANONICAL_DEFINITION`; current implementation `src/triggertrade/market_data/regime.py::evaluate_market_regime` is RESEARCH/DEMO_ONLY; REVIEW_NEEDED; IMPLEMENT_STRUCTURE_ONLY; current classifier is not a canonical trading input until defined or marked research-only. |
| `docs/FORMULA_METRICS_CATALOG.md` unmapped current calculations | S-005 may remain research/demo-only or be defined later; it must not enter canonical runtime as a trading input now. |
| `docs/FORMULA_METRICS_CATALOG.md` M-001 through M-008 rows | Research metrics and aggregation are research-only / research-parameter objects. |
| `docs/FORMULA_METRICS_CATALOG.md` implementation gates | Research/backtest mechanics may be parameterized; formula certification harness may scaffold only and must not approve formulas by implementation. |
| `docs/BACKEND_TARGET_MODEL.md` lines 273-277 | Research/backtest/demo execution should run with pinned methodology/config/source/adapters and no live side effects; backend promotion workflow is not fully specified. |
| `docs/BACKEND_TARGET_MODEL.md` lines 310-318 | Research/backtest tests prove isolated deterministic runs with version pins, historical selectors, metrics and no live side effects. |
| `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | API transports facts and does not choose a market regime, trigger, history window, reference or fallback. |
| `docs/trading-methodology/methodology/SET.md` lines 2960-2975 | Optional volatility-regime context may be retained in Set-local diagnostics, not baseline wire fields. |
| `docs/trading-methodology/methodology/SET.md` lines 4043-4051 | Optional research/diagnostic contexts remain Set-local unless incorporated by explicit versioned wire extension; they cannot be emitted as unknown fields or silently used by a current Position formula. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` | Order Lifecycle does not inspect market regime. |
| `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` | Portfolio Rules does not own market regime. |
| `src/triggertrade/market_data/regime.py` | Non-normative current code defines `CTX-REGIME@0.1.0`, BTCUSDT linear 1m, 30 completed candles and threshold labels; catalog marks it RESEARCH/DEMO_ONLY. |

## 3. Purpose and Trading Context

S-005 asks whether the current market regime classifier can be certified for any
role in TriggerTrade.

Possible roles:

1. canonical live trading input;
2. Set-local diagnostic/research context only;
3. research/backtest reporting aggregation only;
4. not certified / future product work required.

Current catalog evidence does not approve S-005 as a live trading input.

## 4. Exact Formula If Available

No active canonical methodology formula is available.

Non-normative implementation candidate in `src/triggertrade/market_data/regime.py`:

```text
rule_id = CTX-REGIME
version = 0.1.0
symbol = BTCUSDT
category = linear
timeframe = 1m
lookback = 30 completed candles

window_return_pct = 100 * (latest_close - first_close) / first_close
avg_abs_step_return_pct = mean(abs(step_return_pct over 29 steps))
normalized_trend =
  0 if avg_abs_step_return_pct == 0
  else window_return_pct / avg_abs_step_return_pct
directional_persistence = (up_steps - down_steps) / 29
```

Labels:

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

Invalid/unsupported cases return `UNKNOWN` or `INSUFFICIENT_DATA`.

This formula is current-code evidence only. It is not an active methodology
definition.

## 5. Inputs

For the non-normative implementation candidate:

| Input | Semantics |
|---|---|
| `symbol` | Must be BTCUSDT in current code. |
| `category` | Must be linear in current code. |
| `timeframe` | Must be 1m. |
| `observed_at` | Must equal last candle close time. |
| `candles` | At least 30 contiguous completed 1m candles. |
| `close` prices | Positive close values. |

Canonical methodology input requirements are missing.

## 6. Outputs

Non-normative implementation outputs a `MarketRegimeContext` with:

- `context_id`;
- normalized symbol/timeframe/observed_at;
- capability;
- label;
- input snapshot;
- normalized features;
- thresholds;
- reason.

Labels include `UNKNOWN`, `INSUFFICIENT_DATA`, `STRONG_UPTREND`, `UPTREND`,
`SIDEWAYS`, `DOWNTREND` and `STRONG_DOWNTREND`.

Canonical output role is not approved.

## 7. Units

- `window_return_pct`: percent.
- `avg_abs_step_return_pct`: percent.
- `normalized_trend`: unitless ratio.
- `directional_persistence`: unitless ratio over 29 steps.
- labels: categorical.

## 8. Parameters

All candidate thresholds and windows are research/demo parameters unless
Council defines a narrower research-only status:

- 30 completed 1m candles;
- BTCUSDT-only scope;
- linear category;
- strong/mild return thresholds;
- strong/mild normalized-trend thresholds;
- strong/mild directional-persistence thresholds.

## 9. Thresholds

Current-code thresholds are inclusive and hardcoded. No active methodology
evidence validates them as product truth or trading decision thresholds.

## 10. Sign / Direction Semantics

Positive return/trend/persistence produces uptrend labels; negative produces
downtrend labels. The classifier does not own TriggerTrade LONG/SHORT Set
direction and must not override certified F-005 direction.

## 11. Domain / Preconditions

Current-code candidate domain is BTCUSDT linear 1m completed-candle context. It
does not cover the full traded altcoin universe, instrument-specific regime,
Bybit USDT perpetual watchlist classification or live trade eligibility.

Canonical domain is missing.

## 12. Boundaries

S-005 must not enter canonical live trading decisions unless explicitly
incorporated by active methodology or a future certified formula/spec.

API does not choose market regime. Order Lifecycle and Portfolio Rules do not
inspect market regime. Current Position formulas do not consume S-005.

## 13. Precision

Current code uses `Decimal` arithmetic but is not a canonical numeric policy.
The active methodology does not assign S-005 to `TT_SET_NUMERIC_V1` or another
approved precision policy.

## 14. Time Semantics

Current implementation uses a 30-candle 1m window and requires `observed_at` to
equal the last candle close time. Active methodology does not approve this as a
canonical regime timeframe or evaluation cadence.

## 15. State / Replay / Restart

Research/backtest/demo runs should pin methodology package revision, contract
versions, configuration IDs/content digests, numeric policy IDs, historical
selectors/source snapshots, adapter/profile assumptions and execution simulation
assumptions.

No live runtime state machine depends on S-005 in the active certified baseline.

## 16. Version / Configuration Pinning

Current-code candidate has `CTX-REGIME@0.1.0`. This version is implementation
metadata, not an approved active methodology version.

## 17. Ownership

Owner: Research.

S-005 is not owned by Set as a canonical Market Handoff or Position Rules input
under current evidence.

## 18. Downstream Consumers

Current allowed consumers appear limited to:

- research/backtest diagnostics;
- reporting/aggregation;
- possible future product research.

It has no approved live trading consumer in the certified primary formula
pipeline.

## 19. Dependencies

| Dependency | Classification | Notes |
|---|---|---|
| Active methodology canonical definition | UNKNOWN / MISSING | Catalog states missing canonical definition. |
| M-008 | RESEARCH_PARAMETER | Research grouping, direction mix and regime aggregation. |
| BACKEND_TARGET_MODEL research boundary | DOCUMENTATION_DEPENDENCY | Research/backtest isolation and no live side effects. |
| Current implementation | DOCUMENTATION_DEPENDENCY / NON_NORMATIVE | Evidence of existing candidate only; not product authority. |

## 20. Existing Worked Examples

No canonical worked examples are present in active methodology.

Implementation boundary examples:

- unsupported symbol -> `UNKNOWN`;
- unsupported category -> `UNKNOWN`;
- unsupported timeframe -> `UNKNOWN`;
- incomplete current candle -> `UNKNOWN`;
- fewer than 30 completed candles -> `INSUFFICIENT_DATA`;
- non-positive close -> `INSUFFICIENT_DATA`;
- otherwise classify into trend labels using hardcoded thresholds.

## 21. Explicit Source Gaps

1. No approved canonical methodology definition exists for S-005.
2. No approved product role exists for S-005 in live Set/Position/Portfolio/
   Lifecycle decision-making.
3. No evidence validates the hardcoded thresholds, BTCUSDT proxy scope,
   30-minute lookback, labels or usefulness for TriggerTrade's traded universe.
4. No active wire contract carries S-005 as a baseline dependency.
5. No empirical validation evidence is included.

## 22. Reviewer Handoff Summary

Council should decide whether S-005 can be certified only as a research/demo
diagnostic boundary, with `FULL_COUNCIL_APPROVED = YES` for a non-live,
non-canonical-trading-input role, or whether lack of canonical definition
requires rejection/product decision.

If approved, the narrowest defensible approval appears to be:

```text
S-005 is research/demo-only diagnostic context.
It is not a certified live trading input.
It must not affect Set matching, Position decisions, Portfolio approvals, Order
Lifecycle behavior or live execution until a future canonical methodology
definition and formula certification approve such use.
```

Council should not silently promote the current implementation thresholds to
canonical product truth.
