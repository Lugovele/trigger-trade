# F-001 REVISED SPEC CYCLE 1

Formula: F-001 - Price-move trigger calculation
Cycle: 1
Status: CANDIDATE_FOR_FULL_COUNCIL_REVALIDATION
Revision basis: Product owner decision, 2026-09-15

This revised candidate resolves the Cycle 1 product-decision blockers. It is
self-contained for Full Council re-review and does not change active
methodology.

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-001 |
| Name | Price-move trigger calculation |
| Owner | Set |
| Type | TRADING_FORMULA |
| Formula family | TRIGGER |
| Active methodology baseline | v1.2.14 |
| Source Pack | `docs/formula-certification/F-001/F-001_SOURCE_PACK.md` |
| Prior review artifact | `docs/formula-certification/_orchestrator/work/F-001/FULL_COUNCIL_REVIEW_CYCLE_1.md` |

## 2. Full Council Cycle 1 Closure

Cycle 1 accepted the narrow arithmetic core as a partial Council-defined
candidate:

```text
move_pct_work = Q36(100 * (P_observed - P_reference) / P_reference)
```

The blocking ambiguity was product-level: price basis, endpoints, horizon,
predicate, cadence, role, direction ownership, and F-003 relationship were not
defined. The product owner has now resolved those choices. This candidate
incorporates that resolution.

## 3. Intended Purpose

F-001 answers:

```text
Did price move sufficiently over the latest completed 1m interval?
```

It is a direction-neutral Set Trigger for short-horizon price displacement. It
does not determine whether the movement is a good trade, does not determine
LONG or SHORT, and does not validate liquidity, execution quality, trend,
regime, profitability or position eligibility.

## 4. Actual Construct

F-001 measures signed percentage displacement between the close of the
immediately preceding completed 1-minute candle and the close of the current
completed 1-minute candle for the same venue, product and instrument.

The predicate applies absolute value to the signed working displacement so that
both upward and downward sufficiently large 1-minute moves can satisfy the
Trigger. The signed value remains preserved as Set evidence.

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

Comparison is inclusive. The numerical value `1` means one percent.

## 6. Inputs

| Input | Requirement |
|---|---|
| Venue/product/instrument | Same bound source, product and instrument for both candles. |
| `reference_price` | `KLINES.close` of the immediately preceding completed 1-minute candle. |
| `observed_price` | `KLINES.close` of the current completed 1-minute candle. |
| Candle completion evidence | Both candles must be completed and source-final under the governed market-data selection. |
| Evaluation slot | Current completed 1-minute slot. |
| `theta_move_pct` | Mandatory positive pinned research parameter in percent units. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for the active Set formation epoch. |
| Source coverage/finality | Complete selected KLINES coverage and no unresolved contradiction. |

## 7. Outputs

| Output | Requirement |
|---|---|
| Trigger result | `TRUE`, `FALSE` or `UNAVAILABLE`. |
| `move_pct_work` | Signed Q36 working percent displacement. |
| Sign evidence | `UP`, `DOWN` or `FLAT` evidence retained for Set. |
| Effective time | Current completed 1-minute slot/evaluation timestamp. |
| Role satisfaction | CURRENT_STATE only for the current completed 1-minute slot. |

Sign evidence:

```text
UP   if move_pct_work > 0
DOWN if move_pct_work < 0
FLAT if move_pct_work = 0
```

F-001 does not emit LONG or SHORT.

## 8. Units

Prices are exact decimal price values in the source KLINES units for the same
instrument. `move_pct_work` and `theta_move_pct` are percent units where `1`
means one percent.

## 9. Parameters

| Parameter | Class | Requirement |
|---|---|---|
| `theta_move_pct` | RESEARCH_PARAMETER | Mandatory, positive, pinned for the active Set/Trigger configuration. |
| Timeframe | Fixed product decision | 1 minute. |
| Price basis | Fixed product decision | Trade-price-derived KLINES close. |

Parameter performance remains subject to empirical validation. Certification
does not choose or optimize the threshold value.

## 10. Domain / Preconditions

F-001 can evaluate only when:

1. The symbol is in active Set analysis scope for the active formation epoch.
2. The Trigger configuration and `theta_move_pct` are pinned.
3. The current and immediately preceding 1-minute KLINES candles are selected
   from the same venue/product/instrument and factual source.
4. Both candles are completed, source-final, within the evaluation cutoff, and
   have complete coverage.
5. `reference_price > 0`.
6. `observed_price >= 0`.
7. Price values are finite exact decimals with no NaN, infinity, binary float
   conversion or inferred fallback.
8. No unresolved source contradiction or identity mismatch exists.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Missing current or reference candle | `UNAVAILABLE`. |
| Incomplete/still-forming candle | `UNAVAILABLE`. |
| Mismatched venue/product/instrument/source | `UNAVAILABLE`. |
| Missing source finality or incomplete coverage | `UNAVAILABLE`. |
| `reference_price <= 0` | `UNAVAILABLE`. |
| Invalid, NaN, infinite or binary-float-derived price | `UNAVAILABLE`. |
| Missing, zero or negative `theta_move_pct` | `UNAVAILABLE`. |
| Source contradiction | `UNAVAILABLE` / reconciliation-blocked; do not substitute stale data. |
| Valid zero observed price | Compute normally; yields `-100%` if `reference_price > 0`. |

`UNAVAILABLE` is not `FALSE` and is not negative evidence.

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
trigger_true = false
```

unless an invalid zero/nonpositive threshold has been supplied, in which case
the result is `UNAVAILABLE` because the threshold contract is violated.

## 13. Precision / Rounding

Evaluate subtraction, multiplication and division exactly according to
`TT_SET_NUMERIC_V1` / N-008 principles. Apply exactly one named working
quantizer:

```text
Q36 = 36 fractional decimal places, ROUND_HALF_EVEN
```

The predicate compares:

```text
abs(move_pct_work) >= theta_move_pct
```

with no epsilon, no intermediate rounding, no binary float conversion, and no
display-rounded gate.

## 14. Time Semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`, select:

- observed candle: completed 1-minute candle for `S`;
- reference candle: immediately preceding completed 1-minute candle.

The result is valid only for the current completed 1-minute slot. The next
1-minute boundary requires a new evaluation. Receipt time, scheduler time,
restart time and wall-clock loop time cannot substitute for the governed
completed-candle slot.

## 15. State / Replay / Restart

F-001 is a CURRENT_STATE Trigger. It is satisfied only when the authoritative
result for the current completed 1-minute slot is `TRUE` and freshness
requirements still hold for that slot.

Persist the evaluation identity:

- Trigger ID/version/configuration;
- symbol and active formation epoch;
- evaluation slot;
- observed/reference candle identities and source revisions;
- `theta_move_pct`;
- numeric policy;
- `move_pct_work`;
- sign evidence;
- tri-state result.

Replay or restart must rehydrate accepted evaluation state and source
identities before accepting new evaluations. Duplicate identical evaluation is
a no-op. Conflicting source content or changed accepted values trigger
reconciliation/integrity handling and do not silently alter downstream frozen
handoffs.

## 16. Version / Configuration Pinning

F-001 material configuration includes:

- Trigger ID/version;
- price basis;
- timeframe;
- endpoint selection;
- `theta_move_pct`;
- CURRENT_STATE role;
- freshness policy;
- numeric policy.

Started Set formation epochs use the pinned configuration selected for that
epoch. Later edits apply only to future epochs/cycles.

## 17. Dependencies

| Dependency | Class | Role |
|---|---|---|
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Exact arithmetic, Q36 working value, exact comparison. |
| Generic Set Trigger framework | DOCUMENTATION_DEPENDENCY | Tri-state result, CURRENT_STATE, freshness, replay/restart. |
| Market Data Request KLINES | DOCUMENTATION_DEPENDENCY | Factual completed 1-minute KLINES close inputs. |
| F-003 ATR/true range | CERTIFIED_FORMULA / DOWNSTREAM_CONTEXT_ONLY | Not part of F-001 arithmetic; separate volatility context for downstream normalization/scoring/decision logic. |

F-001 does not divide displacement by ATR and does not import F-003 timeframe
or volatility semantics.

## 18. Ownership

Set owns F-001 Trigger evaluation, source selection, result persistence and
formation use. API supplies factual market data only. Position consumes frozen
Set/Handoff output and does not recompute F-001. Portfolio owns Coins
OPEN/CLOSE scope only.

## 19. Pipeline Role

F-001 contributes direction-neutral price-move state to Set formation. Set owns
final direction.

```text
Market Data KLINES -> Set F-001 CURRENT_STATE -> Set formation/scoring -> Set direction/handoff
```

## 20. Approved Uses

- Detect whether the latest completed 1-minute price displacement magnitude
  meets the pinned threshold.
- Preserve signed UP/DOWN/FLAT evidence for Set.
- Supply direction-neutral CURRENT_STATE evidence for Set formation.

## 21. Prohibited Interpretations

F-001 must not be interpreted as:

- a LONG or SHORT decision;
- a BUY_CANDIDATE mapping;
- a legacy negative-threshold dip-buy rule;
- a volatility-adjusted or ATR-divided metric;
- evidence of profitability;
- liquidity or execution-quality confirmation;
- path, spread, depth or order-flow measurement;
- permission to use still-forming candles.

## 22. Known Limitations

- Endpoint displacement omits intrabar path, spread, depth, liquidity,
  volatility context, execution capacity and market activity.
- Equal percent moves across symbols do not imply equal risk.
- Threshold performance remains empirical.
- F-003 remains separate context for downstream formulas.

## 23. Research Parameters

`theta_move_pct` is a mandatory positive pinned research parameter. The final
specification should avoid any claim that a particular value is profitable or
optimal.

## 24. Empirical Validation Requirements

Empirical validation should measure:

- threshold sensitivity;
- false-positive/false-negative behavior across regimes;
- interaction with F-002 volume confirmation;
- downstream F-004/F-005 use of sign evidence;
- latency and corrected-candle/reconciliation frequency.

These validation requirements do not change the certified formula.

## 25. Expected Council Revalidation Scope

The re-review should determine whether the product decision resolves prior
blockers F001-R01, F001-R02 and F001-R03, and whether the revised candidate is
fit for certification as a direction-neutral 1-minute signed endpoint
displacement Trigger.
