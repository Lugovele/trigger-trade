# FINAL_FORMULA_SPECIFICATION

# F-002 - Volume confirmation calculation

**Artifact:** `F-002_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Revalidation - Cycle 2
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-002 |
| Name | Volume confirmation calculation |
| Owner | Set |
| Formula family | TRIGGER |
| Type | TRADING_FORMULA |
| Methodology baseline | v1.2.14 |
| Source Pack | `F-002_SOURCE_PACK.md` |
| Approved revision | `_orchestrator/work/F-002/F-002_REVISED_SPEC_CYCLE_1.md` |
| Final approval cycle | 2 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = APPROVED_AS_SHORT_HORIZON_RELATIVE_PARTICIPATION_CONFIRMATION
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = RESEARCH_VALIDATION_REQUIRED
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies F-002 as a Set-owned direction-neutral CURRENT_STATE Trigger
for short-horizon relative participation confirmation. It does not certify
implementation, deployment, exchange integration, profitability, absolute
liquidity, execution quality, authenticity of activity, or trade direction.

## 3. Intended Purpose

F-002 determines whether the latest completed 1-minute futures candle shows
unusually high base-volume participation relative to the immediately preceding
hour for the same instrument.

It supports Set formation as confirmation evidence. It does not choose LONG or
SHORT and does not determine whether a trade is good.

## 4. Actual Construct

F-002 compares the current completed 1-minute Bybit USDT linear perpetual
futures base-coin KLINES volume to:

- the median of the immediately preceding 60 completed 1-minute volumes; and
- the empirical rank of the current volume within that same 60-candle
  historical population.

The ordinary 30 completed day / 14 day warmup baseline is not applicable.

## 5. Exact Formula / Rule

Definitions:

```text
market = Bybit USDT linear perpetual futures
volume_basis = exchange KLINES.volume in base-coin units
timeframe = 1 minute
c = current completed 1m candle volume
v(1)..v(60) = immediately preceding 60 completed 1m candle volumes
```

Sort historical values ascending:

```text
v_sorted(1) <= ... <= v_sorted(60)
```

Median:

```text
M = (v_sorted(30) + v_sorted(31)) / 2
```

Rank:

```text
K = count(v(i) <= c)
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

Equivalent valid-domain boundary:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

This equivalent boundary may be used only after establishing `M > 0`.

## 6. Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Bybit USDT linear perpetual futures, same instrument and factual source across all candles. |
| `c` | Exchange KLINES.volume in base-coin units for the current completed 1-minute candle. |
| Historical population | Exactly 60 immediately preceding completed consecutive 1-minute KLINES.volume values. |
| Candle identities | Persisted source identities/revisions for current and historical candles. |
| Evaluation slot | Current completed 1-minute slot. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for the active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

## 7. Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| `M` | Trigger-local median baseline. |
| `K` | Trigger-local integer rank count. |
| `R` | Trigger-local relative-volume intermediate. |
| `P` | Trigger-local empirical-rank percent intermediate. |
| Effective time | Current completed 1-minute slot/evaluation timestamp. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

`M`, `K`, `R` and `P` are not exported Set metrics unless a later certified
formula or handoff contract explicitly exposes them.

## 8. Units

All volumes are exchange KLINES base-coin units for the same Bybit USDT linear
perpetual futures instrument.

Do not substitute:

- quote turnover;
- contract count;
- raw-trade notional;
- spot-market volume.

`R` is dimensionless. `P` is percent units.

## 9. Parameters

| Parameter | Approved value |
|---|---|
| Market | Bybit USDT linear perpetual futures |
| Volume basis | KLINES.volume in base-coin units |
| Timeframe | 1 minute |
| Historical population | 60 immediately preceding completed candles |
| Relative threshold | `R >= 2` |
| Rank threshold | `P >= 90`, equivalently `K >= 54` |
| Trigger role | CURRENT_STATE |
| Ordinary 30-day/14-day baseline | NOT_APPLICABLE |

Threshold performance remains subject to empirical validation. Certification
does not establish profitability or optimality.

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

`UNAVAILABLE` is neither `FALSE` nor negative evidence.

## 12. Boundaries

All comparisons are inclusive:

```text
R = 2 -> relative threshold passes
P = 90 -> rank threshold passes
K = 54 -> rank threshold passes
```

Ties count toward `K`.

Both thresholds must pass for `TRUE`. If either comparison fails and all
preconditions hold, the result is `FALSE`.

## 13. Precision / Rounding

Evaluate volumes as exact decimals under `TT_SET_NUMERIC_V1` / N-008
principles. Sorting is exact. `K` is an exact integer count. `R` and `P` are
exact rational/decimal trigger-local intermediates.

No epsilon, binary float, intermediate rounding, display-rounded comparison or
alternative threshold is permitted.

The division-free boundary can be used after `M > 0` is proven:

```text
c >= v_sorted(30) + v_sorted(31)
AND
K >= 54
```

## 14. Time Semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`:

- current observation is the completed 1-minute candle for `S`;
- historical population is the immediately preceding 60 completed consecutive
  1-minute candles `[S-60m, S)`.

The result is valid only for the current completed 1-minute slot. The next
1-minute boundary requires a new evaluation. Receipt time, scheduler time,
restart time and wall-clock loop time cannot substitute for the governed slot.

## 15. State / Replay / Restart

F-002 is a CURRENT_STATE Trigger. It is satisfied only when the authoritative
result for the current completed 1-minute slot is `TRUE` and freshness remains
valid for that slot.

Persist:

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

Rehydration does not renew freshness.

## 16. Configuration Pinning

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

| Dependency | Role |
|---|---|
| N-008 / TT_SET_NUMERIC_V1 | Exact arithmetic, exact rank/count semantics, no epsilon. |
| Generic Set Trigger framework | Tri-state result, CURRENT_STATE, freshness, replay/restart. |
| Market Data Request KLINES | Factual completed 1-minute KLINES volume inputs. |
| Ordinary 30-day/14-day baseline | Explicitly `NOT_APPLICABLE`. |

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
- permission to use still-forming candles;
- deployment or implementation approval.

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
their empirical performance remains subject to later research validation. This
certification makes no profitability or optimality claim.

## 24. Empirical Validation Requirements

Empirical validation should measure:

- confirmation frequency by symbol/regime;
- sensitivity to sparse trading and repeated equal volumes;
- interaction with F-001 price movement;
- false activity and liquidation/event sensitivity;
- relationship between this short-horizon confirmation and downstream Set
  outcomes.

These validation requirements do not change the certified formula.

## 25. Eight Final Expert Verdicts

| Required perspective | Verdict |
|---|---|
| Senior Intraday Crypto Trader | APPROVE |
| Market Microstructure & Order Flow Researcher | APPROVE |
| Market Regime & Context Analyst | APPROVE |
| Quant Strategy Researcher | APPROVE |
| Risk & Trade Management Architect | APPROVE |
| Execution & Exchange Mechanics Specialist | APPROVE |
| Adversarial Strategy Reviewer | APPROVE |
| Performance & Strategy Diagnostics Analyst | APPROVE |

## 26. Final Council Record

```text
FINAL_COUNCIL_RECORD

formula_id: F-002
formula_name: Volume confirmation calculation

senior_intraday_crypto_trader: APPROVE
microstructure_order_flow_researcher: APPROVE
market_regime_context_analyst: APPROVE
quant_strategy_researcher: APPROVE
risk_trade_management_architect: APPROVE
execution_exchange_mechanics_specialist: APPROVE
adversarial_strategy_reviewer: APPROVE
performance_strategy_diagnostics_analyst: APPROVE

specification_status: FINAL_APPROVED
trading_fitness_status: APPROVED_AS_SHORT_HORIZON_RELATIVE_PARTICIPATION_CONFIRMATION

blocking_findings: NONE
precision_decision: EXACT_ARITHMETIC_EXACT_RANK_NO_EPSILON
ordinary_30_day_14_day_baseline: NOT_APPLICABLE
mathematical_dependency_on_F001: NONE

known_limitations:
- inclusive rank is discrete and tie-sensitive
- high relative volume does not establish liquidity, activity authenticity, direction, execution quality or profitability
- threshold usefulness remains empirical

empirical_questions:
- confirmation frequency and threshold performance
- sparse-volume and regime sensitivity
- liquidation/event effects and downstream outcome relationship

full_council_approved: YES
another_review_cycle_required: NO
```
