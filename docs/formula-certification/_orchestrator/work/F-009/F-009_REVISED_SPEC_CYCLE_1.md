# F-009 REVISED SPECIFICATION CYCLE 1

# F-009 - Stop Calculation and Stop Rounding

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-009 |
| Formula name | Stop calculation and stop rounding |
| Owner | Position Rules |
| Formula family | STOP |
| Certification artifact | Revised candidate |
| Review cycle | 1 |
| Active methodology baseline | v1.2.14 |

## 2. Council Status

```text
FULL_COUNCIL_APPROVED = NO
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
SPECIFICATION_STATUS = REVISED_CANDIDATE_FOR_REVIEW
```

This candidate closes Cycle 1 blockers:

```text
F009-C01: fixed_sl_pct admissible domain and invalid-value outcomes
F009-C02: fixed-mode positive finite tick-grid output and terminal failure mapping
```

## 3. Intended Purpose

F-009 integrates stop-loss mode selection, stop price calculation and stop price
rounding for Position Rules. It consumes the certified F-008 entry, active
Position stop-loss configuration, N-004 tick facts, and when applicable the
certified F-006/F-007 Dynamic SL branch result. It emits the stop-loss price and
stop-loss output fields used by later Position geometry, gross R:R, minimum net
edge, construction and Order Spec stages.

F-009 answers:

```text
For the current immutable Position decision cycle, which stop_loss.price is
available for the configured stop-loss mode, and is that stop price a valid
positive direction-preserving tick-grid price?
```

It does not choose Entry, infer direction, select dynamic structural references,
calculate TP, size the position, compute gross R:R or net edge, approve
Portfolio capital, or submit/manage native protective orders.

## 4. Actual Construct

F-009 has two mutually exclusive branches:

```text
FIXED:
  configured percent displacement from certified Entry
  + direction-preserving outward tick rounding
  + fixed-output validity checks

DYNAMIC:
  matching certified F-006/F-007 Dynamic SL result pass-through
  + identity/provenance consistency validation
  + no rerounding or repair
```

If the selected branch cannot produce an actionable stop:

```text
SL_UNAVAILABLE -> REJECT
```

or, for configuration invalidity:

```text
CONFIG_INVALID -> REJECT
```

## 5. Exact Formula and Rule

### 5.1 Symbols

```text
direction = LONG | SHORT
E = certified F-008 Entry / planned_entry_reference / final entry price
S = fixed_sl_pct, in percent units
t = tick_size
SL = stop_loss_price
```

`E` and `t` must be exact finite positive decimals before F-009 evaluation.

### 5.2 Mode selection

```yaml
position_rules:
  stop_loss:
    mode: DYNAMIC | FIXED
    fixed_pct: nullable
```

If `mode = FIXED`, evaluate Sections 5.3 through 5.6.

If `mode = DYNAMIC`, evaluate Section 5.7.

Any other mode:

```text
usable = false
reason = CONFIG_INVALID
```

### 5.3 Fixed percentage domain

For fixed mode, `S = fixed_sl_pct` is required and must be an exact finite
percentage where numeric `1` means one percent.

Required:

```text
S > 0
```

For LONG fixed mode, additionally:

```text
S < 100
```

because `S >= 100` makes the raw LONG stop nonpositive before rounding.

No universal SHORT upper bound is inferred from LONG mathematics.

Missing, malformed, nonfinite or out-of-domain fixed configuration returns:

```text
usable = false
reason = CONFIG_INVALID
```

No implicit default is permitted. Dynamic mode does not consume `fixed_pct`;
if it is present in dynamic mode, it remains ignored / NOT_APPLICABLE per the
active methodology.

### 5.4 Fixed raw stop calculation

LONG:

```text
raw_sl = E * (1 - S / 100)
```

SHORT:

```text
raw_sl = E * (1 + S / 100)
```

Use exact rational arithmetic. Do not round intermediate values.

### 5.5 Fixed tick rounding

Let:

```text
floor_q(x) = q * floor(x / q)
ceil_q(x)  = q * ceil(x / q)
q = t
```

LONG:

```text
SL = floor_q(raw_sl)
```

SHORT:

```text
SL = ceil_q(raw_sl)
```

Rounding is direction-preserving and must not move the fixed stop inward
through the intended protection boundary.

### 5.6 Fixed output validity

Before exposing a usable fixed stop, all invariants must hold:

```text
SL is finite
SL > 0
SL / t is an integer
```

LONG:

```text
SL = floor_q(raw_sl)
SL < E
```

SHORT:

```text
SL = ceil_q(raw_sl)
SL > E
```

Arithmetic failure or any post-rounding invariant failure returns:

```text
usable = false
reason = ROUNDING_ERROR
```

No actionable stop is exposed. Diagnostics may retain raw and rounded values,
but they do not authorize an order. F-009 must not clamp, offset, retry,
substitute, reprice, change `S`, change Entry, or route to dynamic mode as a
repair.

### 5.7 Dynamic stop pass-through

For dynamic mode, consume only the matching certified branch:

```text
direction = LONG  -> F-006
direction = SHORT -> F-007
```

The dynamic branch result must satisfy:

```text
usable = true
reason = AVAILABLE
same instrument
same direction
same frozen handoff / decision cycle / set result
same certified F-008 entry
same pinned Position configuration
same tick provenance or validated equivalent tick identity
```

If the matching branch is unavailable or mismatched, F-009 rejects and preserves
the original branch result and reason:

```text
usable = false
reason = SL_UNAVAILABLE or dependency-specific reason
dependency_reason = original branch reason
```

F-009 must not reround, clamp, offset, substitute, retry a weaker reference,
change branch feasibility, or change the branch result while retaining F-006 or
F-007 certification.

### 5.8 Stop output and downstream handoff

Successful F-009 output:

```text
stop_loss_price = SL
```

or in dynamic mode:

```text
stop_loss_price = certified branch rounded_stop_price
```

After final Entry, SL and TP resolution, downstream consumers must recompute and
validate:

```text
geometry
gross R:R
Minimum Net Edge
```

using final prices. No failed downstream gate is repaired by modifying Entry,
SL, TP, leverage, quantity, capital or configuration.

## 6. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | Immutable `LONG` or `SHORT`; `NONE` rejects upstream. |
| `E` | F-008 | Certified positive entry for the same handoff/cycle. |
| `stop_loss.mode` | Position Rules configuration | `FIXED` or `DYNAMIC`, pinned for the decision cycle. |
| `fixed_sl_pct` / `S` | Position Rules configuration | Required exact finite positive percent for `FIXED`; ignored / NOT_APPLICABLE for `DYNAMIC`. |
| `tick_size` / `t` | N-004 / instrument metadata | Positive exact price tick fact with provenance. |
| F-006 result | Certified formula | Required for LONG dynamic mode. |
| F-007 result | Certified formula | Required for SHORT dynamic mode. |

## 7. Outputs

Primary output:

```text
stop_loss_price
```

Order Spec fields:

```yaml
stop_loss:
  mode: DYNAMIC | FIXED
  price: decimal-string
  execution_type: MARKET
  trigger_by: LAST_PRICE
  scope: PARTIAL_QUANTITY
  fixed_pct:
    nullable: decimal-string
```

Rule result:

```yaml
rule_result:
  rule_id: STOP_LOSS
  enabled: true
  configured_value:
  calculated_value:
  operator:
  status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  reason_code:
  dependency_reason:
```

## 8. Units

| Item | Unit |
|---|---|
| Entry, raw SL, rounded SL, tick size | Instrument quote price units |
| `fixed_sl_pct` | Percent units; numeric `1` means one percent |
| Dynamic SL diagnostics | As defined by F-006/F-007; not redefined by F-009 |

## 9. Parameters

| Parameter | Class | Semantics |
|---|---|---|
| `fixed_sl_pct` | CONFIG_PARAMETER / RESEARCH_PARAMETER | Required configured fixed stop percentage in fixed mode; no implicit default. Calibration remains empirical. |
| `tick_size` | APPROVED_POLICY / exchange fact | Positive instrument price grid quantum from N-004 evidence. |

## 10. Domain and Preconditions

F-009 can evaluate only when:

```text
direction is LONG or SHORT
E is finite and > 0
t is finite and > 0
stop_loss.mode is FIXED or DYNAMIC
```

Additional fixed-mode preconditions:

```text
S is finite
S > 0
if LONG: S < 100
```

Additional dynamic-mode preconditions:

```text
matching F-006/F-007 result exists
matching branch result is usable and AVAILABLE
branch identity/provenance matches the current decision cycle
```

Missing required values are never zero-filled.

## 11. Missing / Invalid Behavior

| Condition | Reason |
|---|---|
| invalid stop-loss mode | `CONFIG_INVALID` |
| FIXED mode missing `fixed_sl_pct` | `CONFIG_INVALID` |
| malformed, nonfinite or nonpositive `fixed_sl_pct` | `CONFIG_INVALID` |
| LONG FIXED `fixed_sl_pct >= 100` | `CONFIG_INVALID` |
| missing, nonfinite or nonpositive Entry | `DEPENDENCY_ENTRY_UNAVAILABLE` or source-specific entry reason |
| missing, nonfinite or nonpositive tick size | `MISSING_EXCHANGE_FACT` |
| arithmetic failure or invalid fixed rounded stop | `ROUNDING_ERROR` |
| dynamic branch unavailable | `SL_UNAVAILABLE` with original branch `dependency_reason` |
| dynamic branch identity/provenance mismatch | `SL_UNAVAILABLE` or `IDENTITY_INVALID`, preserving mismatch diagnostics |

## 12. Boundaries

F-009 includes:

```text
stop_loss mode dispatch
fixed stop percentage domain validation
fixed stop raw calculation
fixed stop direction-preserving tick rounding
fixed stop output validity checks
dynamic stop pass-through from certified F-006/F-007
stop_loss output construction for downstream geometry and Order Spec
SL unavailable / dependency failure propagation
```

F-009 excludes:

```text
dynamic structural reference selection
dynamic stop formula feasibility already certified by F-006/F-007
planned entry selection
take profit selection
position size and quantity
gross R:R / net edge formula
Portfolio grant/hold
Order Lifecycle native protective order submission, trigger semantics, reconciliation or fills
exchange adapter implementation
```

## 13. Precision / Rounding

Use exact decimal-safe arithmetic from `TT_NUMERIC_V1`. No binary floats,
nonfinite numbers, exponent-encoded canonical decimals, epsilon comparisons, or
finite-precision intermediate rounding.

Fixed mode uses exact quantizers:

```text
floor_q(x) = q * floor(x / q)
ceil_q(x)  = q * ceil(x / q)
q = tick_size
```

Outward fixed rounding adds distance `delta`, where:

```text
0 <= delta < t
```

The resulting distance can exceed the configured percentage. This is expected
and must be considered by downstream geometry, gross R:R and net edge checks.

Dynamic mode consumes the certified rounded stop candidate and must not reround
it.

## 14. Time Semantics

The Position configuration is pinned for the decision cycle. Activation of an
edited configuration does not mutate an already-started Position decision
cycle. Dynamic mode uses the frozen Market Handoff through F-006/F-007. The
final Order Spec provenance carries `position_rules_version` and
`instrument_metadata_revision`.

## 15. State, Replay and Restart

Replay/restart must restore:

```text
F-009 specification identity/version
dependency identities and versions
decision_cycle_id
set_result_id
position_decision_id
frozen handoff digest
position_rules_version
configuration identity/version/content digest
instrument_metadata_revision
tick_size provenance
entry selected by F-008
stop_loss.mode
fixed_sl_pct if FIXED
fixed raw and rounded outputs if FIXED
linked dynamic branch result if DYNAMIC
validation outcomes and reason codes
```

Restart must reproduce the result without refreshing configuration, entry or
tick metadata.

## 16. Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
Position Rules configuration pinned per decision cycle
Market Handoff v4 for dynamic mode
TT_SET_NUMERIC_V1 for Set handoff values
TT_NUMERIC_V1 for Position numeric policy
Order Spec contract_version = 5
N-004 instrument tick/step metadata with provenance
F-006 final specification for LONG dynamic mode
F-007 final specification for SHORT dynamic mode
```

## 17. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-006 | CERTIFIED_FORMULA | LONG Dynamic SL stop candidate and feasibility. |
| F-007 | CERTIFIED_FORMULA | SHORT Dynamic SL stop candidate and feasibility. |
| F-008 | CERTIFIED_FORMULA | Entry price consumed by fixed and dynamic stop integration. |
| N-004 | APPROVED_POLICY | Price tick normalization and instrument tick facts. |
| T-004 | RESEARCH_PARAMETER | Stop-loss percentage calibration for fixed mode. |
| Position Rules configuration | CONFIG_PARAMETER | Selects fixed/dynamic mode and fixed percentage. |
| TT_NUMERIC_V1 | APPROVED_POLICY | Exact arithmetic and quantizer definitions. |
| Order Spec v5 | DOCUMENTATION_DEPENDENCY | Final `stop_loss` output shape. |

## 18. Ownership

Position Rules owns F-009. API / instrument facts own tick size through N-004.
F-008 owns entry. F-006/F-007 own dynamic stop branch calculations. Position
Rules owns fixed stop calculation and the final stop field in its Order Spec.
Order Lifecycle owns technical submission, native acknowledgement, fills,
cancellation, reconciliation and protective children.

## 19. Pipeline Role

```text
F-008 Entry + Position stop configuration
-> F-009 stop_loss.price
-> Position geometry gate
-> F-012 gross R:R / minimum net edge
-> Order Spec stop_loss block
-> Order Lifecycle protective handling after authorization
```

## 20. Approved Uses Requested

If approved, F-009 may be used to:

```text
compute fixed stop prices for configured fixed mode
consume certified dynamic stop candidates for configured dynamic mode
produce final stop_loss.price for Position geometry and Order Spec
reject invalid stop configuration or invalid fixed stop output
preserve certified dynamic stop results without alteration
```

## 21. Prohibited Interpretations

F-009 must not be interpreted as:

```text
a dynamic structural-reference formula
a TP formula
a gross R:R or net edge formula
a position sizing formula
a guarantee of exchange acceptance
a guarantee of stop fill
a maximum realized loss guarantee
a liquidation-risk model
a permission to repair a failed trade
a permission to reround or alter certified F-006/F-007 outputs
```

## 22. Known Limitations

1. `fixed_sl_pct` calibration and any default remain empirical/product
   configuration questions.
2. Outward fixed rounding can create a farther stop than the configured raw
   percentage.
3. A planned stop does not guarantee maximum realized loss, liquidation
   protection, coverage of every fill, exchange acceptance or execution.
4. Dynamic `post_rounding.pct` remains uncertified, non-decision diagnostics.
5. F-010, F-011 and F-012 remain uncertified.

## 23. Research Parameters

```text
fixed_sl_pct / T-004
dynamic SL constants inherited from F-006/F-007
```

## 24. Empirical Validation Requirements

Evaluate fixed percentages and inherited dynamic parameters chronologically out
of sample across symbols, sides, regimes and tick-to-stop-distance ratios,
including rejected and unfilled opportunities. Measure adverse excursion, stop
frequency, realized loss, costs, slippage, gaps and partial-fill outcomes.
Candle touches cannot establish fills or exit ordering.

## 25. Edge and Regression Fixtures

### Fixed off-grid rounding

```text
E = 100
S = 1.03
t = 0.25

LONG:
raw_sl = 98.97
SL = 98.75

SHORT:
raw_sl = 101.03
SL = 101.25
```

### Fixed exact-grid rounding

```text
E = 100
S = 1
t = 0.5

LONG:
raw_sl = 99
SL = 99

SHORT:
raw_sl = 101
SL = 101
```

### Invalid fixed percentages

```text
S missing -> CONFIG_INVALID
S <= 0 -> CONFIG_INVALID
S nonfinite -> CONFIG_INVALID
LONG S >= 100 -> CONFIG_INVALID
```

### Rounded zero

```text
E = 1
S = 1
t = 1

LONG:
raw_sl = 0.99
SL = 0
result = ROUNDING_ERROR
```

### Dynamic unchanged pass-through

```text
direction = LONG
F-006 usable = true
F-006 reason = AVAILABLE
F-006 rounded_stop_price = X

F-009 stop_loss_price = X
```

F-009 performs no rerounding or repair.

### Dependency failure / mismatch

```text
direction = SHORT
F-007 usable = false
F-007 reason = SL_TOO_WIDE

F-009 result = SL_UNAVAILABLE
dependency_reason = SL_TOO_WIDE
```

Mismatched handoff/cycle/entry/tick identity also rejects and preserves
diagnostics.

### Restart equality

Restart with the same frozen handoff, configuration, entry, tick metadata and
branch result must reproduce the same raw stop, rounded stop, status, reason
and diagnostics.

## 26. Revision Record

| Cycle | Change | Reason |
|---:|---|---|
| 1 | Defined fixed percentage domain: finite percent, `S > 0`, LONG `S < 100`, no implicit default. | Closes F009-C01. |
| 1 | Added fixed output invariants: finite positive grid-aligned SL, strict adverse-side geometry and terminal `ROUNDING_ERROR`. | Closes F009-C02. |
| 1 | Made dynamic branch pass-through identity and no-repair rules explicit. | Preserves certified F-006/F-007 boundaries. |
| 1 | Added replay evidence and conformance fixtures. | Supports deterministic re-review and future tests. |
