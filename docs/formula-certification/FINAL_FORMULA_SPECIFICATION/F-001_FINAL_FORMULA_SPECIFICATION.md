# FINAL_FORMULA_SPECIFICATION

# F-001 - Price-move trigger calculation

**Artifact:** `F-001_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Revalidation - Cycle 3
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-001 |
| Name | Price-move trigger calculation |
| Owner | Set |
| Formula family | TRIGGER |
| Type | TRADING_FORMULA |
| Methodology baseline | v1.2.14 |
| Source Pack | `F-001_SOURCE_PACK.md` |
| Approved revision | `_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_2.md` |
| Final approval cycle | 3 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_NARROW_ROLE_WITH_LIMITATIONS
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = RESEARCH_VALIDATION_REQUIRED
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies F-001 as a Set-owned direction-neutral CURRENT_STATE Trigger
for completed-minute endpoint displacement. It does not certify implementation,
deployment, trading profitability, direction selection, execution quality,
liquidity, or trade authorization.

## 3. Intended Purpose

F-001 answers:

```text
Did price move sufficiently over the latest completed 1m interval?
```

It detects sufficiently large signed close-to-close displacement and supplies
direction-neutral evidence to Set formation. It does not determine whether the
movement is a good trade.

## 4. Actual Construct

F-001 measures signed percentage displacement between the close of the
immediately preceding completed 1-minute candle and the close of the current
completed 1-minute candle for the same venue, product, instrument and factual
source.

The predicate uses absolute magnitude, while the rounded signed value remains
available as UP/DOWN/FLAT evidence when arithmetic is available.

## 5. Exact Formula / Rule

Definitions:

```text
price_basis = trade-price-derived KLINES.close
timeframe = 1 minute
reference_price = close of the immediately preceding completed 1m candle
observed_price = close of the current completed 1m candle
```

Working displacement:

```text
move_pct_work =
Q36(100 * (observed_price - reference_price) / reference_price)
```

Predicate:

```text
trigger_true = abs(move_pct_work) >= theta_move_pct
```

Comparison is exact and inclusive. The numerical value `1` means one percent.

## 6. Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Same bound source, product and instrument for both candles. |
| `reference_price` | `KLINES.close` of the immediately preceding completed 1-minute candle. |
| `observed_price` | `KLINES.close` of the current completed 1-minute candle. |
| Candle completion evidence | Both candles completed and source-final under governed market-data selection. |
| Evaluation slot | Current completed 1-minute slot. |
| `theta_move_pct` | Mandatory positive pinned research parameter in percent units. |
| Freshness policy | `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

## 7. Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| Arithmetic status | `AVAILABLE` or `UNAVAILABLE`. |
| `move_pct_work` | Signed Q36 working percent displacement when arithmetic status is `AVAILABLE`; otherwise unavailable. |
| Sign evidence | `UP`, `DOWN`, `FLAT` when arithmetic status is `AVAILABLE`; otherwise unavailable. |
| Trigger-result status reason | Reason code for `UNAVAILABLE`, if applicable. |
| Effective slot | Current completed 1-minute slot. |
| Freshness policy/version | `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

Sign evidence:

```text
UP   if move_pct_work > 0
DOWN if move_pct_work < 0
FLAT if move_pct_work = 0
```

F-001 does not emit LONG or SHORT.

## 8. Units

Prices are exact decimal price values in source KLINES units for the same
instrument. `move_pct_work` and `theta_move_pct` are percent units where `1`
means one percent.

## 9. Parameters

| Parameter | Class | Requirement |
|---|---|---|
| `theta_move_pct` | RESEARCH_PARAMETER | Mandatory, positive, pinned for active Set/Trigger configuration. |
| Timeframe | Fixed product decision | 1 minute. |
| Price basis | Fixed product decision | Trade-price-derived KLINES close. |
| Freshness policy | Fixed configuration contract | Current completed 1-minute slot membership only. |

Certification does not select or optimize the threshold value.

## 10. Domain / Preconditions

F-001 can evaluate only when:

1. The symbol is in active Set analysis scope for the active formation epoch.
2. The Trigger configuration and `theta_move_pct` are pinned.
3. Current and preceding 1-minute KLINES candles are selected from the same
   venue/product/instrument and factual source.
4. Both candles are completed, source-final, within the evaluation cutoff, and
   have complete coverage.
5. `reference_price > 0`.
6. `observed_price >= 0`.
7. Price values are finite exact decimals with no NaN, infinity, binary float
   conversion or inferred fallback.
8. No unresolved source contradiction or identity mismatch exists.
9. The persisted freshness policy is
   `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`.

Missing intervals cannot be bridged by choosing an older reference.

## 11. Missing / Invalid Behavior

| Case | Arithmetic status | `move_pct_work` / sign evidence | Trigger result |
|---|---|---|---|
| Missing current or reference candle | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Incomplete/still-forming candle | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Mismatched venue/product/instrument/source | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing source finality or incomplete coverage | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| `reference_price <= 0` | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Invalid, NaN, infinite or binary-float-derived price | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing, zero or negative `theta_move_pct` with otherwise valid arithmetic inputs | `AVAILABLE` | Computed and retained as non-satisfying diagnostic evidence | `UNAVAILABLE` |
| Missing, zero or negative `theta_move_pct` with invalid arithmetic inputs | `UNAVAILABLE` | Unavailable | `UNAVAILABLE` |
| Missing/unknown freshness policy version | Depends on arithmetic inputs | Arithmetic may be retained if otherwise valid | `UNAVAILABLE` |
| Source contradiction | `UNAVAILABLE` / reconciliation-blocked | Unavailable | `UNAVAILABLE` |
| Valid zero observed price with valid reference and threshold | `AVAILABLE` | `-100%`, `DOWN` | Predicate result by threshold |

Absent arithmetic evidence must never become fabricated zero, `FLAT`, or a
previous value. Retained diagnostics cannot satisfy CURRENT_STATE while the
Trigger result is `UNAVAILABLE`.

## 12. Boundaries

Equality passes:

```text
abs(move_pct_work) = theta_move_pct -> TRUE
```

Below threshold fails:

```text
abs(move_pct_work) < theta_move_pct -> FALSE
```

Zero movement:

```text
move_pct_work = 0
sign_evidence = FLAT
trigger_true = false
```

for every valid positive threshold.

Valid observed zero produces exactly `-100%` and `DOWN`; the predicate result
depends on the pinned threshold. If that zero becomes the next reference, the
next evaluation is `UNAVAILABLE` because `reference_price <= 0`.

## 13. Precision / Rounding

Evaluate subtraction, multiplication and division exactly according to
`TT_SET_NUMERIC_V1` / N-008 principles. Apply exactly one named working
quantizer:

```text
Q36 = 36 fractional decimal places, ROUND_HALF_EVEN
```

Q36 retains integer digits. Quantization precedes both sign evidence and
threshold comparison.

The predicate compares:

```text
abs(move_pct_work) >= theta_move_pct
```

with no epsilon, no intermediate rounding, no binary float conversion, no
display-rounded gate and no additional threshold quantizer.

## 14. Time Semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`:

- observed candle is the completed 1-minute candle for `S`;
- reference candle is the immediately preceding completed 1-minute candle.

The result is valid only for the current completed 1-minute slot.

## 15. State / Replay / Restart

F-001 is a CURRENT_STATE Trigger. It is satisfied only when:

```text
trigger_result == TRUE
AND arithmetic_status == AVAILABLE
AND freshness_policy_version == F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
AND evaluation_slot == requested_current_slot
```

Freshness policy:

```text
F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
fresh_for_slot(evaluation_slot, requested_current_slot)
= evaluation_slot == requested_current_slot
```

There is no additional timeout, grace period, wall-clock age, scheduler-age or
receipt-time freshness condition.

Set derives the requested slot from its governed completed-minute evaluation,
not receipt, restart or scheduler time. Restart restores the persisted slot and
compares it to the currently requested slot; restart does not renew freshness.

## 16. Configuration Pinning

F-001 material configuration includes:

- Trigger ID/version;
- price basis;
- timeframe;
- endpoint selection;
- `theta_move_pct`;
- CURRENT_STATE role;
- freshness policy version
  `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`;
- numeric policy.

Started Set formation epochs use the pinned configuration selected for that
epoch. Later edits apply only to future epochs/cycles.

## 17. Dependencies

| Dependency | Role |
|---|---|
| N-008 / TT_SET_NUMERIC_V1 | Exact arithmetic, Q36 working value, exact comparison. |
| Generic Set Trigger framework | Tri-state result, CURRENT_STATE, replay/restart. |
| Market Data Request KLINES | Factual completed 1-minute KLINES close inputs. |
| F-003 ATR/true range | Separate downstream volatility context only. |

F-001 does not divide displacement by ATR and does not import F-003 timeframe,
cutoff rules, smoothing, export quantizer or volatility semantics.

## 18. Ownership

Set owns F-001 Trigger evaluation, source selection, result persistence,
formation and final direction. API supplies factual market data only. Position
consumes frozen Set/Handoff output and does not recompute F-001. Portfolio
owns Coins OPEN/CLOSE scope only.

## 19. Pipeline Role

F-001 contributes direction-neutral price-move state to Set formation.

```text
Market Data KLINES -> Set F-001 CURRENT_STATE -> Set formation/scoring -> Set direction/handoff
```

## 20. Approved Uses

- Detect whether the latest completed 1-minute price displacement magnitude
  meets the pinned threshold.
- Preserve signed UP/DOWN/FLAT evidence when arithmetic is available.
- Supply direction-neutral CURRENT_STATE evidence for Set formation only while
  the result belongs to the current completed 1-minute slot.

## 21. Prohibited Interpretations

F-001 must not be interpreted as:

- a LONG or SHORT decision;
- a BUY_CANDIDATE mapping;
- a legacy negative-threshold dip-buy rule;
- a volatility-adjusted or ATR-divided metric;
- evidence of profitability;
- liquidity or execution-quality confirmation;
- path, spread, depth or order-flow measurement;
- permission to use still-forming candles;
- permission to refresh stale results by restart or receipt time;
- deployment or implementation approval.

## 22. Known Limitations

- Endpoint displacement omits intrabar path, spread, depth, liquidity,
  volatility context, execution capacity and market activity.
- Slot equality establishes logical freshness, not feed liveness or guaranteed
  wall-clock recency.
- Equal percent moves across symbols do not imply equal risk.
- Sign describes rounded movement, not trade direction.
- Threshold performance remains empirical.
- F-003 remains separate context for downstream formulas.

## 23. Research Parameters

`theta_move_pct` is a mandatory positive pinned research parameter.
Certification makes no profitability or optimality claim for any value.

## 24. Empirical Validation Requirements

Empirical validation should measure:

- threshold sensitivity;
- false-positive/false-negative behavior across regimes;
- interaction with F-002 volume confirmation;
- downstream F-004/F-005 use of sign evidence;
- latency and corrected-candle/reconciliation frequency;
- execution-cost and slippage impact if used in a strategy.

These validation requirements do not change the certified formula.

## 25. Eight Final Expert Verdicts

| Required perspective | Verdict |
|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS |

## 26. Final Council Record

```text
FINAL_COUNCIL_RECORD

formula_id: F-001
formula_name: Price-move trigger calculation

senior_intraday_crypto_trader: APPROVE_WITH_LIMITATIONS
microstructure_order_flow_researcher: APPROVE_WITH_LIMITATIONS
market_regime_context_analyst: APPROVE_WITH_LIMITATIONS
quant_strategy_researcher: APPROVE_WITH_LIMITATIONS
risk_trade_management_architect: APPROVE_WITH_LIMITATIONS
execution_exchange_mechanics_specialist: APPROVE_WITH_LIMITATIONS
adversarial_strategy_reviewer: APPROVE_WITH_LIMITATIONS
performance_strategy_diagnostics_analyst: APPROVE_WITH_LIMITATIONS

specification_status: FINAL_APPROVED
trading_fitness_status: ADEQUATE_FOR_DECLARED_NARROW_ROLE_WITH_LIMITATIONS

F001_RV01: CLOSED
F001_RV02: CLOSED
blocking_findings_remaining: NONE
freshness_policy: F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
precision_decision: Q36_ROUND_HALF_EVEN_BEFORE_SIGN_AND_COMPARISON
F003_relationship: DOWNSTREAM_CONTEXT_ONLY

known_limitations:
- endpoint displacement omits path and microstructure
- slot equality is logical freshness, not feed liveness
- TRUE is not trade direction or execution permission
- threshold usefulness remains empirical

empirical_questions:
- threshold calibration
- regime and F-002 interaction
- downstream sign use
- net trading benefit

full_council_approved: YES
another_review_cycle_required: NO
```
