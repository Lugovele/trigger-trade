# F-002 REVISED SPEC CYCLE 1

Formula: F-002 - Volume confirmation calculation
Cycle: 1
Status: CANDIDATE_FOR_FULL_COUNCIL_REVALIDATION
Revision basis: Product owner decision, 2026-09-15

This revised candidate resolves the Cycle 1 product-decision blockers. It is
self-contained for Full Council re-review and does not change active
methodology.

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-002 |
| Name | Volume confirmation calculation |
| Owner | Set |
| Type | TRADING_FORMULA |
| Formula family | TRIGGER |
| Active methodology baseline | v1.2.14 |
| Source Pack | `docs/formula-certification/F-002/F-002_SOURCE_PACK.md` |
| Prior review artifact | `docs/formula-certification/_orchestrator/work/F-002/FULL_COUNCIL_REVIEW_CYCLE_1.md` |

## 2. Full Council Cycle 1 Closure

Cycle 1 found the relative-volume construction mathematically defensible but
blocked certification because market scope, baseline policy, Set use, role,
cadence and freshness were unresolved. The product owner has now selected the
futures universe binding and Set role while preserving the relative-volume
mathematics.

## 3. Intended Purpose

F-002 answers whether the latest completed 1-minute futures candle shows
unusually high short-horizon participation relative to the immediately
preceding hour for the same instrument.

It is a direction-neutral CURRENT_STATE confirmation for Set formation. It does
not determine LONG or SHORT, absolute liquidity, execution quality,
authenticity of activity, trade direction or profitability.

## 4. Actual Construct

F-002 computes current base-coin KLINES volume against the median and empirical
rank of the immediately preceding 60 completed 1-minute KLINES volumes for the
same Bybit USDT linear perpetual futures instrument and factual source.

The ordinary 30 completed day / 14 day warmup baseline is explicitly not
applicable to this Trigger. F-002 is a short-horizon relative participation
confirmation, not an ordinary normalization baseline.

## 5. Exact Formula / Rule

Definitions:

```text
market = Bybit USDT linear perpetual futures
volume_basis = exchange KLINES.volume in base-coin units
timeframe = 1 minute
c = current completed 1m candle volume
v(1)..v(60) = immediately preceding 60 completed 1m candle volumes
```

Sort the 60 historical values ascending:

```text
v_sorted(1) <= ... <= v_sorted(60)
```

Median:

```text
M = (v_sorted(30) + v_sorted(31)) / 2
```

Empirical rank count:

```text
K = count(historical volume <= c)
```

Relative volume and rank percent:

```text
R = c / M
P = 100 * K / 60
```

Predicate:

```text
trigger_true = (R >= 2) AND (P >= 90)
```

Equivalent boundary for valid `M > 0`:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

All comparisons are inclusive. Ties count toward `K`.

## 6. Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Bybit USDT linear perpetual futures, same instrument and factual source across all candles. |
| `c` | Exchange KLINES.volume in base-coin units for the current completed 1-minute candle. |
| Historical population | Exactly 60 immediately preceding completed consecutive 1-minute KLINES.volume values. |
| Candle completion evidence | Current and historical candles must be completed and source-final under governed selection. |
| Evaluation slot | Current completed 1-minute slot. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for the active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

## 7. Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| `R` | Trigger-local relative-volume intermediate. |
| `P` | Trigger-local empirical-rank percent intermediate. |
| `M` | Trigger-local median baseline. |
| `K` | Trigger-local integer rank count. |
| Effective time | Current completed 1-minute slot/evaluation timestamp. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

`R`, `P`, `M` and `K` do not become exported Set metrics unless a later
certified formula or handoff contract explicitly exposes them.

## 8. Units

All volumes are exchange KLINES base-coin units for the same Bybit USDT linear
perpetual futures instrument. Do not replace base volume with quote turnover,
contract count, raw-trade notional, or spot-market volume during this
certification.

`R` is a dimensionless ratio. `P` is percent units.

## 9. Parameters

F-002 fixed product parameters:

| Parameter | Value |
|---|---|
| Market | Bybit USDT linear perpetual futures |
| Volume basis | KLINES.volume in base-coin units |
| Timeframe | 1 minute |
| Historical population | 60 immediately preceding completed candles |
| Relative threshold | `R >= 2` |
| Rank threshold | `P >= 90` / `K >= 54` |
| Trigger role | CURRENT_STATE |
| Ordinary 30-day/14-day baseline | NOT_APPLICABLE |

Threshold empirical performance remains subject to later research validation,
but the mathematical thresholds are not silently changed during certification.

## 10. Domain / Preconditions

F-002 can evaluate only when:

1. The symbol is in active Set analysis scope for the active formation epoch.
2. The Trigger configuration is pinned.
3. The current candle and all 60 historical candles are selected from the same
   Bybit USDT linear perpetual futures instrument and factual source.
4. All 61 candles are completed, consecutive, source-final, within the
   evaluation cutoff, and have complete coverage.
5. Every volume is a finite exact nonnegative decimal in base-coin units.
6. `M > 0`.
7. No unresolved source contradiction, identity mismatch or basis mismatch
   exists.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Missing current candle | `UNAVAILABLE`. |
| Fewer than 60 immediately preceding candles | `UNAVAILABLE`. |
| Non-consecutive historical population | `UNAVAILABLE`. |
| Incomplete/still-forming candle | `UNAVAILABLE`. |
| Mismatched venue/product/instrument/source | `UNAVAILABLE`. |
| Missing source finality or incomplete coverage | `UNAVAILABLE`. |
| Invalid, negative, NaN, infinite or binary-float-derived volume | `UNAVAILABLE`. |
| `M = 0` | `UNAVAILABLE`. |
| Source contradiction | `UNAVAILABLE` / reconciliation-blocked; do not substitute stale data. |
| Valid `c = 0` with `M > 0` | `FALSE`. |

`UNAVAILABLE` is not `FALSE` and is not negative evidence.

## 12. Boundaries

For valid `M > 0`, equality passes:

```text
R = 2 -> relative threshold passes
P = 90 -> rank threshold passes
K = 54 -> rank threshold passes
```

Both thresholds must pass for `TRUE`. If either comparison fails and all
preconditions hold, the result is `FALSE`.

The equivalent boundary:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

is permitted only under the valid-domain condition `M > 0`.

## 13. Precision

Evaluate volumes as exact decimals under `TT_SET_NUMERIC_V1` / N-008
principles. Sorting is exact. `K` is an exact integer count. `R` and `P` are
exact rational/decimal trigger-local intermediates.

No epsilon, binary float, intermediate rounding, display-rounded comparison or
alternative threshold is permitted.

The exact boundary form may be used to avoid unnecessary division:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

provided the implementation has already proven `M > 0`.

## 14. Time Semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`, select:

- current observation: completed 1-minute candle for `S`;
- historical population: the immediately preceding 60 completed consecutive
  1-minute candles `[S-60m, S)`.

The result is valid only for the current completed 1-minute slot. The next
1-minute boundary requires a new evaluation. Receipt time, scheduler time,
restart time and wall-clock loop time cannot substitute for the governed
completed-candle slot.

## 15. State / Replay / Restart

F-002 is a CURRENT_STATE Trigger. It is satisfied only when the authoritative
result for the current completed 1-minute slot is `TRUE` and freshness
requirements still hold for that slot.

Persist the evaluation identity:

- Trigger ID/version/configuration;
- symbol and active formation epoch;
- evaluation slot;
- current and historical candle identities/source revisions;
- volume basis;
- numeric policy;
- `M`, `K`, `R`, `P`;
- tri-state result.

Replay or restart must rehydrate accepted evaluation state and source
identities before accepting new evaluations. Duplicate identical evaluation is
a no-op. Conflicting source content or changed accepted values trigger
reconciliation/integrity handling and do not silently alter downstream frozen
handoffs.

## 16. Version / Configuration Pinning

F-002 material configuration includes:

- Trigger ID/version;
- market/product;
- volume basis;
- timeframe;
- historical population count;
- thresholds `2` and `90`;
- CURRENT_STATE role;
- freshness policy;
- numeric policy.

Started Set formation epochs use the pinned configuration selected for that
epoch. Later edits apply only to future epochs/cycles.

## 17. Dependencies

| Dependency | Class | Role |
|---|---|---|
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Exact arithmetic, exact rank/count semantics, no epsilon. |
| Generic Set Trigger framework | DOCUMENTATION_DEPENDENCY | Tri-state result, CURRENT_STATE, freshness, replay/restart. |
| Market Data Request KLINES | DOCUMENTATION_DEPENDENCY | Factual completed 1-minute KLINES volume inputs. |
| Ordinary 30-day/14-day baseline | NOT_APPLICABLE | Explicitly excluded for this short-horizon Trigger. |

F-002 has no F-001 mathematical dependency and does not determine direction.

## 18. Ownership

Set owns F-002 Trigger evaluation, source selection, result persistence and
formation use. API supplies factual market data only. Position consumes frozen
Set/Handoff output and does not recompute F-002. Portfolio owns Coins
OPEN/CLOSE scope only.

## 19. Pipeline Role

F-002 supplies short-horizon relative participation confirmation to Set
formation.

```text
Market Data KLINES -> Set F-002 CURRENT_STATE -> Set formation/scoring -> Set direction/handoff
```

## 20. Approved Uses

- Confirm unusually high recent base-volume participation for the current
  completed 1-minute futures candle.
- Supply direction-neutral CURRENT_STATE evidence for Set formation.
- Preserve diagnostic `M`, `K`, `R` and `P` values as trigger-local evidence.

## 21. Prohibited Interpretations

F-002 must not be interpreted as:

- absolute liquidity;
- execution quality;
- authenticity of activity;
- trade direction;
- LONG or SHORT decision;
- profitability evidence;
- quote-turnover replacement;
- spot-market volume rule;
- ordinary 30-day/14-day normalization baseline;
- permission to use still-forming candles.

## 22. Known Limitations

- Relative participation does not prove tradable liquidity.
- High volume may be noisy, manipulative, liquidation-driven or directionally
  ambiguous.
- The empirical rank is discrete and tie-sensitive.
- Threshold performance remains empirical.
- The formula does not verify order book depth, spreads, slippage or execution
  capacity.

## 23. Research Parameters

The thresholds `2` and `90` are fixed product semantics for this candidate, but
their empirical performance remains subject to later research validation. The
final specification should avoid profitability or optimality claims.

## 24. Empirical Validation Requirements

Empirical validation should measure:

- confirmation frequency by symbol/regime;
- sensitivity to sparse trading and repeated equal volumes;
- interaction with F-001 price movement;
- false activity and liquidation/event sensitivity;
- relationship between this short-horizon confirmation and downstream Set
  outcomes.

These validation requirements do not change the certified formula.

## 25. Expected Council Revalidation Scope

The re-review should determine whether the product decision resolves prior
blockers around market scope, baseline policy, Set use, role, cadence,
freshness and UNAVAILABLE behavior, and whether the revised candidate is fit
for certification as a direction-neutral 1-minute futures relative-volume
CURRENT_STATE Trigger.
