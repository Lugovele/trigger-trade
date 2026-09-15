# F-001 REVISED SPEC CYCLE 2

Formula: F-001 - Price-move trigger calculation
Cycle: 2
Status: CANDIDATE_FOR_FULL_COUNCIL_REVALIDATION
Revision basis: Full Council Cycle 2 findings F001-RV01 and F001-RV02

This revised candidate preserves the Cycle 1 product decisions and arithmetic.
It only closes the operative freshness contract and associated-output
availability gaps identified by Full Council Cycle 2.

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
| Prior candidate | `docs/formula-certification/_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_1.md` |
| Prior review artifact | `docs/formula-certification/_orchestrator/work/F-001/FULL_COUNCIL_REVIEW_CYCLE_2.md` |

## 2. Full Council Cycle 2 Closure

Cycle 2 accepted the product choices and arithmetic but required two closures:

1. F001-RV01: define operative freshness.
2. F001-RV02: define associated-output availability when evaluation is
   `UNAVAILABLE`.

This candidate resolves those points as follows:

- F-001 freshness consists solely of current completed 1-minute slot
  membership under the persisted policy `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`.
- F-001 has explicit output-availability statuses for arithmetic, sign
  evidence and Trigger result.

No new timeout, threshold, signal, direction mapping, ATR input or legacy demo
behavior is introduced.

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
Trigger. The signed value remains preserved as Set evidence when arithmetic is
available.

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
| Freshness policy | `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`. |
| Trigger identity/config | Pinned Trigger ID/version/configuration for the active Set formation epoch. |
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

Prices are exact decimal price values in the source KLINES units for the same
instrument. `move_pct_work` and `theta_move_pct` are percent units where `1`
means one percent.

## 9. Parameters

| Parameter | Class | Requirement |
|---|---|---|
| `theta_move_pct` | RESEARCH_PARAMETER | Mandatory, positive, pinned for the active Set/Trigger configuration. |
| Timeframe | Fixed product decision | 1 minute. |
| Price basis | Fixed product decision | Trade-price-derived KLINES close. |
| Freshness policy | Fixed product decision / configuration contract | Current completed 1-minute slot membership only. |

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
9. The persisted freshness policy is
   `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`.

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

Associated outputs are never fabricated from absent arithmetic evidence. Missing
or invalid price evidence must not become zero, `FLAT` or a previous value.

Arithmetic evidence may survive threshold/configuration/freshness-policy
failure only when the price inputs and numeric policy are independently valid.
Such retained arithmetic/sign evidence is diagnostic and cannot satisfy
CURRENT_STATE while the Trigger result is `UNAVAILABLE`.

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

If the threshold contract is violated, valid arithmetic/sign evidence may be
retained as diagnostic evidence, but Trigger result is `UNAVAILABLE` and cannot
satisfy Set formation.

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

with no epsilon, no intermediate rounding, no binary float conversion, and no
display-rounded gate.

## 14. Time Semantics

Evaluation cadence is once per completed 1-minute candle.

For slot `S`, select:

- observed candle: completed 1-minute candle for `S`;
- reference candle: immediately preceding completed 1-minute candle.

The result is valid only for the current completed 1-minute slot.

## 15. Freshness Contract

F-001 freshness policy:

```text
F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
```

Operative rule:

```text
fresh_for_slot(evaluation_slot, requested_current_slot)
= evaluation_slot == requested_current_slot
```

There is no additional timeout, grace period, wall-clock age limit, scheduler
age limit or receipt-time freshness condition in this formula. A restored
accepted `TRUE` remains satisfying only while its persisted `evaluation_slot`
equals the currently requested completed 1-minute slot. At the next 1-minute
boundary, the previous slot's result is no longer satisfying and a new
evaluation is required.

Evaluation-time binding:

- `requested_current_slot` is derived from the governed market-data completed
  1-minute slot being evaluated by Set, not from receipt, restart, scheduler or
  wall-clock loop time.
- A restart does not refresh or extend the slot. It restores the persisted
  `evaluation_slot`, source identities and freshness policy version, then
  compares the restored slot to the requested current slot.
- Missing or unknown freshness policy version yields Trigger result
  `UNAVAILABLE` for Set satisfaction, even if arithmetic evidence is otherwise
  available.

Persisted evidence required for reproducibility:

- freshness policy version
  `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY`;
- evaluation slot ID / interval;
- requested current slot ID / interval at evaluation;
- observed/reference candle identities;
- source finality and coverage evidence;
- evaluation creation/acceptance identity.

## 16. State / Replay / Restart

F-001 is a CURRENT_STATE Trigger. It is satisfied only when:

```text
trigger_result == TRUE
AND arithmetic_status == AVAILABLE
AND freshness_policy_version == F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY
AND evaluation_slot == requested_current_slot
```

Persist the evaluation identity:

- Trigger ID/version/configuration;
- symbol and active formation epoch;
- evaluation slot;
- requested current slot;
- observed/reference candle identities and source revisions;
- `theta_move_pct`;
- numeric policy;
- freshness policy version;
- arithmetic status;
- `move_pct_work`, when available;
- sign evidence, when available;
- tri-state Trigger result and status reason.

Replay or restart must rehydrate accepted evaluation state and source
identities before accepting new evaluations. Duplicate identical evaluation is
a no-op. Conflicting source content or changed accepted values trigger
reconciliation/integrity handling and do not silently alter downstream frozen
handoffs. Rehydration does not renew freshness.

## 17. Version / Configuration Pinning

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

## 18. Dependencies

| Dependency | Class | Role |
|---|---|---|
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Exact arithmetic, Q36 working value, exact comparison. |
| Generic Set Trigger framework | DOCUMENTATION_DEPENDENCY | Tri-state result, CURRENT_STATE, replay/restart. |
| Market Data Request KLINES | DOCUMENTATION_DEPENDENCY | Factual completed 1-minute KLINES close inputs. |
| F-003 ATR/true range | CERTIFIED_FORMULA / DOWNSTREAM_CONTEXT_ONLY | Not part of F-001 arithmetic; separate volatility context for downstream normalization/scoring/decision logic. |

F-001 does not divide displacement by ATR and does not import F-003 timeframe,
cutoff rules, smoothing, export quantizer or volatility semantics.

## 19. Ownership

Set owns F-001 Trigger evaluation, source selection, result persistence and
formation use. API supplies factual market data only. Position consumes frozen
Set/Handoff output and does not recompute F-001. Portfolio owns Coins
OPEN/CLOSE scope only.

## 20. Pipeline Role

F-001 contributes direction-neutral price-move state to Set formation. Set owns
final direction.

```text
Market Data KLINES -> Set F-001 CURRENT_STATE -> Set formation/scoring -> Set direction/handoff
```

## 21. Approved Uses

- Detect whether the latest completed 1-minute price displacement magnitude
  meets the pinned threshold.
- Preserve signed UP/DOWN/FLAT evidence when arithmetic is available.
- Supply direction-neutral CURRENT_STATE evidence for Set formation only while
  the result belongs to the current completed 1-minute slot.

## 22. Prohibited Interpretations

F-001 must not be interpreted as:

- a LONG or SHORT decision;
- a BUY_CANDIDATE mapping;
- a legacy negative-threshold dip-buy rule;
- a volatility-adjusted or ATR-divided metric;
- evidence of profitability;
- liquidity or execution-quality confirmation;
- path, spread, depth or order-flow measurement;
- permission to use still-forming candles;
- permission to refresh stale results by restart or receipt time.

## 23. Known Limitations

- Endpoint displacement omits intrabar path, spread, depth, liquidity,
  volatility context, execution capacity and market activity.
- Equal percent moves across symbols do not imply equal risk.
- Sign describes rounded movement, not trade direction.
- Threshold performance remains empirical.
- F-003 remains separate context for downstream formulas.

## 24. Research Parameters

`theta_move_pct` is a mandatory positive pinned research parameter. The final
specification should avoid any claim that a particular value is profitable or
optimal.

## 25. Empirical Validation Requirements

Empirical validation should measure:

- threshold sensitivity;
- false-positive/false-negative behavior across regimes;
- interaction with F-002 volume confirmation;
- downstream F-004/F-005 use of sign evidence;
- latency and corrected-candle/reconciliation frequency.

These validation requirements do not change the certified formula.

## 26. Expected Council Revalidation Scope

The re-review should determine whether this candidate resolves F001-RV01 and
F001-RV02 while preserving the already accepted product decisions and
arithmetic.
