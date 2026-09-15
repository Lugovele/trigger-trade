# F-009 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-009 | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula name | Stop calculation and stop rounding | `docs/FORMULA_METRICS_CATALOG.md` |
| Owner | Position Rules | `docs/FORMULA_METRICS_CATALOG.md` |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula family | STOP | `docs/FORMULA_METRICS_CATALOG.md` |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md` |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/POSITION_RULES.md` :: §37, §38, and Part V Tick-size alignment | `docs/FORMULA_METRICS_CATALOG.md` |
| Current implementation pointer | `src/triggertrade/execution/position_lifecycle.py::build_fixed_protective_exit_plan` DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog note | Stop behavior is trading-critical and must remain blocked until formula certification. | `docs/FORMULA_METRICS_CATALOG.md` |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | F-009 row and certification queue | CATALOG / GATE | Identifies F-009 and dependencies F-006, F-007, N-004. |
| 2 | `docs/FORMULA_METRICS_CATALOG.md` | N-004 row | APPROVED_POLICY | Identifies price and quantity tick/step normalization as approved as defined. |
| 3 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §8 User Position Rules configuration | CONFIGURATION | Defines `stop_loss.mode = DYNAMIC | FIXED` and `fixed_pct`. |
| 4 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §9 Fixed Stop Loss semantics | FIXED SL FORMULA | Defines fixed-mode raw SL from Entry and `fixed_sl_pct` for LONG and SHORT. |
| 5 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §10 Dynamic Stop Loss semantics | DYNAMIC SL ROUTING | Defines use of Dynamic Stop Loss methodology and `SL_UNAVAILABLE -> REJECT`. |
| 6 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §14 Deterministic dependency order | PIPELINE | Places fixed/dynamic Stop Loss after Dynamic Limit Entry and before TP, geometry and R:R. |
| 7 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §16 Position geometry gate | GEOMETRY | Defines `SL < Entry < TP` for LONG and `TP < Entry < SL` for SHORT after Entry, SL and TP are resolved. |
| 8 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §41 Fixed SL/TP tick normalization | FIXED ROUNDING | Defines fixed SL rounding direction: LONG down, SHORT up; requires recomputation/revalidation and no Lifecycle repair. |
| 9 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §§42-45 | RESULTS / NO REPAIR | Defines rule result statuses, dependency failures and no-repair invariant. |
| 10 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §49 Technical logical-tranche order specification | OUTPUT CONTRACT | Defines Order Spec `stop_loss` fields. |
| 11 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part V and Appendix D | INVARIANTS | Defines immutable direction, frozen handoff use, versioned/auditable settings, and unchanged Entry/SL/TP rounding rules. |
| 12 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` | §§1-2 | NUMERIC POLICY | Defines exact arithmetic, `floor_q`, `ceil_q`, and price/quantity use of existing instrument tick/quantity step. |
| 13 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` | Governed instrument and fees / instrument metadata | INSTRUMENT FACTS | Defines required instrument metadata including `tick_size` and provenance. |
| 14 | `docs/business-contracts/ORDER_SPEC.md` or `docs/trading-methodology/business-contracts/ORDER_SPEC.md` | Order Spec shape | OUTPUT CONTRACT | Confirms `stop_loss.mode`, `price`, `execution_type`, `trigger_by`, `scope`, and nullable `fixed_pct`. |
| 15 | `docs/formula-certification/F-006/F-006_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified LONG Dynamic SL selected reference, rounded candidate and feasibility result. |
| 16 | `docs/formula-certification/F-007/F-007_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified SHORT Dynamic SL selected reference, rounded candidate and feasibility result. |

## 3. Purpose and Trading Context

F-009 is the Position Rules stop integration formula. It resolves the stop-loss
price for the Position Plan by selecting the configured stop-loss mode, applying
the fixed-mode formula and direction-preserving tick rounding when `FIXED`, or
consuming the already-certified Dynamic SL result when `DYNAMIC`.

F-009 answers:

```text
Given a certified planned entry, a committed LONG/SHORT direction, the active
Position stop-loss configuration, and required tick facts, what stop_loss.price
is carried into Position geometry, downstream sizing/edge checks, and the final
Order Spec?
```

F-009 does not choose entry, infer direction, select dynamic structural
references, compute quantity/notional, determine take profit, compute risk/
reward, approve capital, or submit/manage protective orders.

## 4. Exact Formula / Rule Reconstruction

### 4.1 Mode selection

Configuration:

```yaml
position_rules:
  stop_loss:
    mode: DYNAMIC | FIXED
    fixed_pct: nullable
```

If `stop_loss.mode = FIXED`, use §9 fixed stop semantics.

If `stop_loss.mode = DYNAMIC`, use the approved Dynamic Stop Loss methodology.

If the chosen stop calculation is unusable:

```text
SL_UNAVAILABLE -> REJECT
```

### 4.2 Fixed Stop Loss raw calculation

Let:

```text
E = Entry / planned_entry_reference / final entry price selected by F-008
S = fixed_sl_pct
t = tick_size
```

For LONG:

```text
raw_sl = E * (1 - S / 100)
```

For SHORT:

```text
raw_sl = E * (1 + S / 100)
```

### 4.3 Fixed Stop Loss tick normalization

Canonical mandatory direction-preserving normalization:

```text
LONG Fixed SL -> round DOWN
SHORT Fixed SL -> round UP
```

Using numeric-policy quantizers:

```text
LONG:  stop_loss_price = floor_q(raw_sl), where q = tick_size
SHORT: stop_loss_price = ceil_q(raw_sl), where q = tick_size
```

Rationale in the source:

```text
SL rounding must not move inward through intended protection boundary.
```

After rounding, geometry, gross R:R and Minimum Net Edge must be recomputed and
revalidated. Lifecycle never repairs a rounded result.

### 4.4 Dynamic Stop Loss pass-through

For `stop_loss.mode = DYNAMIC`, F-009 consumes the certified Dynamic SL output:

```text
LONG  -> F-006 rounded_stop_price if usable
SHORT -> F-007 rounded_stop_price / Sstop if usable
```

Certified boundaries:

```text
F-006 owns LONG Dynamic SL reference selection, stop construction and feasibility.
F-007 owns SHORT Dynamic SL reference selection, stop construction and feasibility.
F-009 cannot alter either selected reference, rounded candidate or formula-feasibility result while retaining their certification.
```

### 4.5 Geometry gate after stop resolution

After Entry, SL and TP are resolved:

LONG:

```text
SL < Entry < TP
```

SHORT:

```text
TP < Entry < SL
```

F-009 supplies the `SL` operand to this later geometry gate. It does not certify
TP or risk/reward formulas.

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | Committed `LONG` or `SHORT`; `NONE` rejects upstream. |
| `entry` / `E` | F-008 | Certified positive planned/final entry price for the same handoff/cycle. |
| `stop_loss.mode` | Position Rules configuration | `FIXED` or `DYNAMIC`, pinned for the decision cycle. |
| `fixed_sl_pct` / `S` | Position Rules configuration | Required for `FIXED`; ignored/not applicable for `DYNAMIC` per source. |
| `tick_size` / `t` | N-004 / instrument metadata | Positive exchange price tick fact with provenance. |
| Dynamic SL candidate | F-006 or F-007 | Required when mode is `DYNAMIC`; must be usable/available. |

## 6. Outputs

Primary output:

```text
stop_loss_price
```

Order Spec output fields:

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

Rule/gate result shape:

```yaml
rule_result:
  rule_id:
  enabled:
  configured_value:
  calculated_value:
  operator:
  status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  reason_code:
  dependency_reason:
```

## 7. Units

| Item | Unit |
|---|---|
| Entry, raw SL, rounded SL, tick size | Instrument quote price units |
| `fixed_sl_pct` | Percent units; numeric `1` means one percent |
| Dynamic SL risk diagnostics | As defined by F-006/F-007; not redefined by F-009 |

## 8. Parameters

| Parameter | Class | Notes |
|---|---|---|
| `fixed_sl_pct` | CONFIG_PARAMETER / possibly RESEARCH_PARAMETER | User-supplied configured fixed stop percentage. Catalog separately lists T-004 stop-loss percentage threshold as `RESEARCH_PARAMETER`; F-009 source requires value when fixed mode is selected. |
| `tick_size` | APPROVED_POLICY / exchange fact | Governed by N-004 instrument metadata and exact quantization. |

## 9. Thresholds

Fixed-mode formulas use `fixed_sl_pct = S`. The Source Pack found no certified
default fixed SL percentage value. If fixed mode is enabled and `fixed_sl_pct`
is missing:

```text
CONFIG_INVALID
```

Dynamic-mode thresholds are owned by F-006/F-007 and are not changed here.

## 10. Sign and Direction Semantics

LONG fixed stop:

```text
raw_sl < E when S > 0
round down to avoid inward movement
```

SHORT fixed stop:

```text
raw_sl > E when S > 0
round up to avoid inward movement
```

For dynamic stops, sign and direction semantics are inherited from certified
F-006/F-007. F-009 does not reverse direction or infer side from the stop price.

## 11. Domain and Preconditions

F-009 can evaluate only when:

```text
direction is LONG or SHORT
entry price is available and positive
stop_loss.mode is valid
tick_size is available and positive when tick rounding is required
fixed_sl_pct is available and valid for FIXED mode
corresponding Dynamic SL candidate is available and usable for DYNAMIC mode
```

Missing required values are never zero-filled.

## 12. Boundaries

F-009 includes:

```text
stop_loss mode dispatch
fixed stop raw calculation
fixed stop direction-preserving tick rounding
dynamic stop pass-through from F-006/F-007
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

## 13. Precision

Use exact decimal-safe arithmetic from `TT_NUMERIC_V1`. No binary floats,
nonfinite numbers, exponent-encoded canonical decimals, epsilon comparisons, or
finite-precision intermediate rounding.

For fixed-mode tick rounding:

```text
floor_q(x) = q * floor(x / q)
ceil_q(x)  = q * ceil(x / q)
q = tick_size
```

For dynamic mode, F-009 consumes the certified rounded stop candidate and must
not reround, clamp, offset, substitute or repair it unless Council determines
F-009's integration boundary requires an explicit validation-only check.

## 14. Time Semantics

The Position configuration is pinned for the decision cycle. Activation of an
edited configuration does not mutate an already-started Position decision
cycle. Dynamic mode uses the frozen Market Handoff through F-006/F-007. The
final Order Spec provenance carries `position_rules_version` and
`instrument_metadata_revision`.

## 15. State, Replay and Restart

Replay/restart must restore:

```text
decision_cycle_id
set_result_id
position_decision_id
position_rules_version
configuration identity/version/content digest
instrument_metadata_revision
tick_size provenance
entry selected by F-008
dynamic SL result if DYNAMIC
fixed_sl_pct if FIXED
```

Replays preserve IDs and content. F-009 cannot repair a failed stop by changing
Entry, SL, TP, fixed percentages, leverage, quantity or capital.

## 16. Version and Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
Position Rules configuration pinned per decision cycle
Market Handoff v4 for dynamic mode
TT_SET_NUMERIC_V1 for Set handoff values
TT_NUMERIC_V1 for Position monetary/economic numeric policy
Order Spec contract_version = 5
N-004 instrument tick/step metadata with provenance
```

## 17. Ownership

Position Rules owns F-009. API / instrument facts own tick size through N-004.
F-008 owns entry. F-006/F-007 own dynamic stop branch calculations. Position
Rules owns fixed stop calculation and the final stop field in its Order Spec.
Order Lifecycle owns technical submission, native acknowledgement, fills,
cancellation, reconciliation and protective children.

## 18. Downstream Consumers

Direct downstream:

```text
Position geometry gate
F-011 — Position size, quantity, and actual notional construction
F-012 — Risk/reward and minimum net edge calculation
Order Spec stop_loss block
Order Lifecycle protective handling after authorization
```

## 19. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-006 | CERTIFIED_FORMULA | LONG Dynamic SL stop candidate and feasibility. |
| F-007 | CERTIFIED_FORMULA | SHORT Dynamic SL stop candidate and feasibility. |
| F-008 | CERTIFIED_FORMULA | Entry price consumed by fixed and dynamic stop integration. |
| N-004 | APPROVED_POLICY | Price tick normalization and instrument tick facts. |
| T-004 | RESEARCH_PARAMETER | Cataloged stop-loss percentage threshold; relevant to fixed-mode parameterization. |
| Position Rules configuration | CONFIG_PARAMETER | Selects fixed/dynamic mode and fixed percentage. |
| TT_NUMERIC_V1 | APPROVED_POLICY | Exact arithmetic and quantizer definitions. |
| Order Spec v5 | DOCUMENTATION_DEPENDENCY | Final `stop_loss` output shape. |

## 20. Existing Worked Examples

The active methodology includes no explicit fixed SL numeric worked example.
F-006 and F-007 finals include dynamic stop edge fixtures but those certify the
dynamic branch formulas, not F-009 integration.

## 21. Explicit Source Gaps

1. The catalog points F-009 to §37 and §38, but those branch formulas are now
   certified by F-006 and F-007. F-009 must not recertify or alter those branch
   formulas.
2. The catalog dependency list names F-006, F-007 and N-004, but fixed-mode stop
   semantics also require `fixed_sl_pct`. Catalog separately lists T-004 as a
   research parameter; Council should decide whether fixed-mode certification
   can approve parameterized semantics without an approved default value.
3. The source says "Then normalize to tick size while preserving direction" in
   §9 and later gives the fixed rounding directions in §41; F-009 should unify
   these without adding new rounding behavior.
4. Dynamic-mode post-rounding percent diagnostics are explicitly uncertified in
   F-006/F-007 and should remain non-decision diagnostics unless F-009 defines a
   governed diagnostic formula.
5. The Source Pack found no F-009-specific worked example for fixed LONG/SHORT
   rounding, zero/negative fixed percentages, or tick rounding to invalid price.

## 22. Reviewer Handoff Summary

F-009 appears to be a stop integration formula:

```text
if stop_loss.mode = FIXED:
    require fixed_sl_pct = S
    if direction = LONG:
        raw_sl = E * (1 - S / 100)
        stop_loss_price = floor_q(raw_sl), q = tick_size
    if direction = SHORT:
        raw_sl = E * (1 + S / 100)
        stop_loss_price = ceil_q(raw_sl), q = tick_size

if stop_loss.mode = DYNAMIC:
    if direction = LONG:
        stop_loss_price = F-006 rounded_stop_price if usable
    if direction = SHORT:
        stop_loss_price = F-007 rounded_stop_price if usable

if SL unavailable:
    reject
```

The Council should review whether this is complete enough for certification,
with special attention to fixed-mode parameter status, positive price/tick-grid
validity, dynamic-mode pass-through boundaries, F-009/F-006/F-007 non-overlap,
N-004 tick evidence, downstream geometry/R:R recomputation, replay/configuration
pinning, and trading fitness of fixed and dynamic stop integration.
