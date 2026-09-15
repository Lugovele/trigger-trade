# F-005 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-005 | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula name | Set direction classifier and LONG/SHORT handoff | `docs/FORMULA_METRICS_CATALOG.md` |
| Owner | Set | `docs/FORMULA_METRICS_CATALOG.md` |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula family | LONG_SHORT | `docs/FORMULA_METRICS_CATALOG.md` |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md` |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/SET.md` :: Set outcome and direction handoff | `docs/FORMULA_METRICS_CATALOG.md` |
| Current implementation pointer | `src/triggertrade/services/futures_runtime.py::_direction_skip_reason` DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md` |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies F-005, dependency F-004 and implementation gate. |
| 2 | `docs/trading-methodology/methodology/SET.md` | Part I §§4-6 | SET OUTPUT / OWNERSHIP | Defines matched vs unmatched Set outputs, Set-owned direction and Market Handoff boundary. |
| 3 | `docs/trading-methodology/methodology/SET.md` | Part II §§33-37 | DIRECTION CLASSIFIER | Defines thresholds, veto set, Set resolution, required-data gate, rejection diagnostics and audit payload. |
| 4 | `docs/trading-methodology/methodology/SET.md` | Part III §§43-45 | MARKET HANDOFF | Defines canonical handoff payload, required fields, missing-data semantics and audit requirements. |
| 5 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Contract v4 | OUTPUT CONTRACT | Defines strict Set-to-Position handoff payload and producer/consumer boundary. |
| 6 | `docs/formula-certification/F-004/F-004_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies approved F-004 score, gate, veto and availability diagnostics. |
| 7 | `docs/formula-certification/F-001/F-001_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Upstream formation evidence; sign is not final direction. |
| 8 | `docs/formula-certification/F-002/F-002_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Upstream direction-neutral participation confirmation. |
| 9 | `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Certified 15m volatility values used by F-004 and Market Handoff. |
| 10 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §§1-5, 7 | NUMERIC POLICY | Governs Set working values and serialization boundaries. |

## 3. Purpose and Trading Context

F-005 converts Set-owned analytical evidence into a deterministic direction
classification and, only for a matched directional Set, authorizes creation of
the Set Result and Market Handoff boundary consumed by Position Rules.

It answers:

```text
Did the approved Set evidence satisfy a LONG or SHORT directional branch for
this evaluation, or should Set remain unmatched/NONE?
```

F-005 is trading-critical because it is the first formula in the queue that can
produce a direction sent downstream to Position Rules. It does not calculate
entry price, stop, take profit, position size, risk/reward, execution order or
Portfolio approval.

## 4. Exact Formula Reconstruction

### Required-data gate

Required for altcoin classification:

```text
asset structure 1h
asset structure 15m
DE 15m
VNM 15m
VNM 5m
relative return 15m
aggressive delta 5m
time-of-day relative turnover 5m
ATR_PCT 15m percentile
BTC structure 1h
BTC return 15m z-score
```

If a required item is unavailable:

```text
classifier_direction = NONE
matched = false
rejection_stage = DATA_UNAVAILABLE
```

Context-only metrics may be unavailable without failing classification.

### Threshold classifier

Initial calibration:

```text
LONG_THRESHOLD  = +0.35
SHORT_THRESHOLD = -0.35
```

Decision:

```text
if hard gate fails:
    classifier_direction = NONE

else:
    consume DIRECTION_SCORE from F-004

    if DIRECTION_SCORE >= +0.35:
        if LONG veto active:
            classifier_direction = NONE
        else:
            classifier_direction = LONG

    else if DIRECTION_SCORE <= -0.35:
        if SHORT veto active:
            classifier_direction = NONE
        else:
            classifier_direction = SHORT

    else:
        classifier_direction = NONE
```

There is no forced opposite classification. A LONG-side veto can only block a
LONG candidate; it cannot produce SHORT. A SHORT-side veto can only block a
SHORT candidate; it cannot produce LONG.

### Set resolution

```text
classifier_direction = LONG
-> directional criterion satisfied for LONG branch
-> if all other Set requirements are satisfied:
   matched = true
   direction = LONG
```

```text
classifier_direction = SHORT
-> directional criterion satisfied for SHORT branch
-> if all other Set requirements are satisfied:
   matched = true
   direction = SHORT
```

```text
classifier_direction = NONE
-> no directional branch is satisfied
-> matched = false
-> direction = NONE
```

A directional Set governed by this classifier may never emit:

```text
matched = true
direction = NONE
```

## 5. Inputs

| Input | Meaning | Unit/type | Dependency |
|---|---|---|---|
| `DIRECTION_SCORE` | Pre-classification score | Q36 dimensionless value in `[-1,+1]` | F-004 certified |
| Hard gate diagnostics | Data availability, directional efficiency, activity, volatility | Discrete statuses with values/thresholds | F-004 certified |
| Side-specific veto diagnostics | BTC, relative and local momentum vetoes for LONG and SHORT | Boolean/status plus underlying values | F-004 certified |
| Required input availability | Completeness over eleven required items | AVAILABLE / UNAVAILABLE | F-004 certified |
| Set branch requirements | Other Set/core-set conditions for match | Discrete configured conditions | Active Set methodology |
| Market Handoff primitives | Identity, timestamps, direction, reference price, volatility, references and contexts | Strict contract fields | SET.md / MARKET_HANDOFF.md |
| Numeric policy | Working values and handoff serialization | `TT_SET_NUMERIC_V1` | Approved policy |

F-001 sign evidence is not final direction. F-002 is direction-neutral. F-003
is volatility context. F-004 is the immediate mathematical dependency.

## 6. Outputs

| Output | Meaning |
|---|---|
| `classifier_direction` | One of `LONG`, `SHORT`, `NONE`. |
| `matched` | Boolean Set match state after classifier and other Set requirements. |
| `direction` | `LONG` or `SHORT` only for a matched directional Set; otherwise `NONE` in evaluation record only. |
| `primary_rejection_stage` | Required for every `NONE`. |
| `all_failed_gates[]` | All failed hard gates. |
| `all_active_vetoes[]` | All direction-specific vetoes active for the candidate direction. |
| `decision_cycle_id` | Created only for matched directional Set. |
| `set_result_id` | Created only for matched directional Set. |
| Market Handoff | Emitted only for matched `LONG` or `SHORT`; not emitted for `NONE` or unavailable. |

## 7. Units

The classifier operates on dimensionless F-004 scores, discrete gate/veto
states and contract identities. Market Handoff decimal fields use exact
canonical decimal strings under the Set numeric policy and handoff schema.

## 8. Parameters and Thresholds

| Parameter | Value / source | Type |
|---|---|---|
| `LONG_THRESHOLD` | `+0.35` | Pinned methodology threshold; research calibration remains empirical. |
| `SHORT_THRESHOLD` | `-0.35` | Pinned methodology threshold; research calibration remains empirical. |
| Required-data gate | all eleven required items available | Approved methodology rule. |
| Hard gate priority | data unavailable, DE, activity, volatility | Approved methodology diagnostic priority. |
| Direction-specific veto set | BTC, relative, local momentum | Approved methodology v0.4 veto set. |
| Disabled vetoes | raw aggressive-flow, undefined strong-HTF structure, OI, funding, premium | Explicitly not present in v0.4. |

## 9. Sign and Direction Semantics

Positive score can produce a LONG candidate only if:

```text
DIRECTION_SCORE >= +0.35
```

Negative score can produce a SHORT candidate only if:

```text
DIRECTION_SCORE <= -0.35
```

Scores inside `(-0.35, +0.35)` produce `NONE` via `SCORE_DEAD_ZONE`.
Direction belongs to Set. Portfolio Rules do not determine LONG/SHORT, and
Position Rules must not infer, reverse or reinterpret Set direction.

## 10. Domain and Preconditions

Before F-005 can emit a matched direction:

1. F-004 must be available for the governed evaluation with complete required
   diagnostics.
2. All required data items must be available.
3. No hard gate may fail.
4. The candidate score must satisfy either the LONG or SHORT threshold.
5. The relevant side-specific vetoes for that candidate direction must be
   inactive.
6. Any other configured Set/core-set requirements must be satisfied.
7. Required Market Handoff fields must be available if a match is to be
   emitted.

## 11. Missing / Invalid Behavior

| Case | Expected behavior |
|---|---|
| Required F-004 value unavailable | `NONE`, `DATA_UNAVAILABLE`, no Set Result, no Market Handoff. |
| Any hard gate fails | `NONE`, appropriate gate rejection, no forced opposite side. |
| Score in dead zone | `NONE`, `SCORE_DEAD_ZONE`. |
| Candidate side veto active | `NONE`, side-specific veto rejection. |
| Multiple failed gates/vetoes | Preserve all in arrays; primary stage follows canonical priority. |
| `classifier_direction = NONE` | `matched = false`; no `decision_cycle_id`, `set_result_id` or Market Handoff. |
| Required handoff field unavailable | No valid downstream handoff; persist unavailability reason. |
| Conflicting LONG/SHORT branches at same timestamp | Invalid unless deterministic conflict resolution exists. |

Unavailable facts are not numeric zero, false, neutral factors or implicit
direction.

## 12. Boundaries

- `DIRECTION_SCORE = +0.35` is LONG-threshold eligible if gates pass and LONG
  vetoes are inactive.
- `DIRECTION_SCORE = -0.35` is SHORT-threshold eligible if gates pass and SHORT
  vetoes are inactive.
- `-0.35 < DIRECTION_SCORE < +0.35` is `NONE`.
- LONG and SHORT cannot both arise from a single scalar score under these
  thresholds.
- There is no forced opposite classification after a veto.
- `matched = true, direction = NONE` is forbidden.

Open for Council: whether any additional deterministic conflict rule is needed
when non-score Set branch requirements outside the classifier can satisfy
multiple directional branches at the same canonical timestamp.

## 13. Precision

F-005 consumes F-004 working values before any diagnostic/display serialization.
No epsilon, binary float or display-rounded threshold comparison is permitted.
Threshold comparisons use exact Q36 `DIRECTION_SCORE` and exact signed threshold
values.

Market Handoff serialization must follow contract v4 and `TT_SET_NUMERIC_V1`.
Diagnostic rounded contributions from F-004 must not be summed or substituted
for canonical `DIRECTION_SCORE`.

## 14. Time Semantics

Classification is evaluated at the governed Set analytical cutoff and uses the
latest eligible completed 5m/15m/1h evidence selected by active Set rules and
F-004. `matched_at`, `market_snapshot_at`, source selectors and evaluated
timestamps must be persisted. Receipt time, restart time or current wall clock
cannot replace the governed analytical cutoff.

For `NONE`, Set records an evaluation result only. For matched LONG/SHORT, Set
creates a fresh decision cycle and freezes the handoff evidence.

## 15. State / Replay / Restart

Set must persist:

- classifier inputs and F-004 version;
- `DIRECTION_SCORE` and gate/veto diagnostics;
- required-data availability;
- `primary_rejection_stage`, `all_failed_gates[]` and `all_active_vetoes[]`;
- Set/core-set branch evidence;
- evaluation cutoff and source selector identities;
- if matched, `decision_cycle_id`, `set_result_id`, `matched_at`, matched
  constituents, resolved reference bindings and Market Handoff identity.

Replay from identical admissible facts must reproduce the same classifier
direction, match state, rejection diagnostics and handoff/no-handoff decision.
Restart must not turn a prior `NONE` into a match without a fresh eligible
evaluation, and must not reuse an old Set Result for a new opportunity.

## 16. Version / Configuration Pinning

Material F-005 configuration includes:

- direction classifier id `TT-METH-014`;
- version `0.4.1`;
- scope `ALTCOIN_VS_BTC`;
- thresholds `+0.35` and `-0.35`;
- required-data list;
- hard-gate and veto definitions;
- rejection priority;
- F-004 specification version;
- Market Handoff contract version `4`;
- Set numeric policy `TT_SET_NUMERIC_V1`.

## 17. Ownership

Set owns direction classification, match state, Set Result creation and Market
Handoff production. Position Rules consume frozen handoff direction and must
not recompute, infer or reverse direction. Portfolio Rules do not determine
LONG/SHORT. Order Lifecycle does not create direction.

## 18. Downstream Consumers

| Consumer | Relationship |
|---|---|
| F-008 | Consumes matched direction and frozen handoff context for planned entry reference selection. |
| F-006 / F-007 | Consume immutable LONG/SHORT direction for Position Rules side-specific formulas. |
| Position Rules | Consume Market Handoff; may reject but must not reclassify direction. |
| Order Lifecycle | Later receives order intent/spec, not classifier internals. |
| Diagnostics/dashboard | Display direction, rejection stages, gates, vetoes and evidence. |

## 19. Dependencies

| Dependency | Class | Status |
|---|---|---|
| F-004 score/gates/veto diagnostics | CERTIFIED_FORMULA | Final spec approved. |
| F-001 price-move trigger | CERTIFIED_FORMULA | Formation evidence only; not final direction. |
| F-002 volume confirmation | CERTIFIED_FORMULA | Direction-neutral confirmation. |
| F-003 ATR/TR/ATR_PCT | CERTIFIED_FORMULA | Volatility context via F-004/handoff. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Strict Set-to-Position output contract. |
| Active Set methodology | DOCUMENTATION_DEPENDENCY | Classifier thresholds, vetoes, Set result semantics. |
| `TT_SET_NUMERIC_V1` | APPROVED_POLICY | Working values and serialization. |

## 20. Worked / Conformance Examples Present

Active methodology provides threshold pseudocode but no complete worked example
covering all gates, vetoes, `DIRECTION_SCORE`, rejection arrays and handoff/no
handoff outcomes.

Boundary examples directly implied by the extracted rules:

```text
score = +0.35, no hard gate, no LONG veto -> classifier_direction = LONG
score = -0.35, no hard gate, no SHORT veto -> classifier_direction = SHORT
score = +0.349999... -> classifier_direction = NONE
score = +0.60 and LONG veto active -> classifier_direction = NONE
score = -0.60 and SHORT veto active -> classifier_direction = NONE
required input unavailable -> classifier_direction = NONE
```

## 21. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | Thresholds and veto parameters are pinned methodology values, but empirical predictive quality is not established. | Likely research limitation, not specification blocker if preserved. |
| 2 | The active methodology references "all other Set requirements" after classifier direction. | Council should determine whether the Source Pack is sufficient or whether a narrower F-005 spec must enumerate these requirements as documentation dependencies. |
| 3 | Conflict handling for simultaneous non-score directional branch satisfaction is generic: Set must contain deterministic conflict resolution or is invalid. | Council should decide whether scalar score thresholds already make conflict impossible for F-005 or whether external branch definitions remain a dependency. |
| 4 | No complete worked example exists for rejection priority when hard gates and side-specific vetoes are simultaneously active. | Council should define/confirm primary-stage handling without changing `all_failed_gates[]` and `all_active_vetoes[]`. |
| 5 | Market Handoff requires reference geometry/context fields beyond the direction classifier itself. | F-005 may own handoff/no-handoff gate, but downstream reference-selection formulas may own exact reference content. |

## 22. Reviewer Handoff Summary

```text
FORMULA_ID: F-005
FORMULA_NAME: Set direction classifier and LONG/SHORT handoff

EXACT_FORMULA_RECONSTRUCTABLE:
YES_FOR_DIRECTION_CLASSIFIER

DECLARED_TRADING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
PARTIALLY_WITH_HANDOFF_CONTEXT_DEPENDENCIES

BOUNDARY_BEHAVIOR_COMPLETE:
PARTIALLY

TIME_SEMANTICS_COMPLETE:
YES_GENERIC_SET_CUTOFF_AND_MATCH_TIME

DIRECTION_SEMANTICS_COMPLETE:
YES_FOR_CLASSIFIER

PARAMETER_PROVENANCE_COMPLETE:
YES_FOR_EXTRACTED_ACTIVE_METHOD_VALUES

STATE_REPLAY_SEMANTICS_COMPLETE:
YES_GENERIC_SET_RESULT_AND_HANDOFF_STATE

SOURCE_GAP_COUNT:
5_CLASSIFICATION_OR_SCOPE_DECISION_REQUIRED

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED BY ORCHESTRATOR; COUNCIL SHOULD DEFINE F005/HANDOFF BOUNDARY AND REJECTION PRIORITY DETAILS
```
