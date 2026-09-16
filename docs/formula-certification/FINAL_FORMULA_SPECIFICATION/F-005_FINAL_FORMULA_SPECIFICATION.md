# FINAL_FORMULA_SPECIFICATION

# F-005 — Set Direction Classifier and LONG/SHORT Handoff

**Artifact:** `F-005_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review — Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-005 |
| Formula name | Set direction classifier and LONG/SHORT handoff |
| Owner | Set |
| Formula family | LONG_SHORT |
| Reviewed candidate | `F-005_COUNCIL_DEFINED_CYCLE_1` |
| Active methodology baseline | v1.2.14 |
| Numeric policy | `TT_SET_NUMERIC_V1` |
| Direction classifier | `TT-METH-014`, version `0.4.1`, scope `ALTCOIN_VS_BTC` |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_SET_OWNED_ROLE_WITH_LIMITATIONS
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_ESTABLISHED
PARAMETER_CALIBRATION = NOT_ESTABLISHED
IMPLEMENTATION_AND_LIVE_DEPLOYMENT = NOT_CERTIFIED
```

Approval covers the Set-owned direction classifier and handoff/no-handoff
resolution defined here. It is not approval of entry, stop, take-profit,
position sizing, risk/reward, Portfolio approval, exchange execution or live
deployment.

## 3. Intended Purpose

F-005 converts certified F-004 analytical evidence into a deterministic
`classifier_direction` of `LONG`, `SHORT` or `NONE`, then determines whether
Set may commit a matched directional Set Result and Market Handoff.

F-005 answers:

```text
Did the approved Set evidence satisfy a LONG or SHORT directional branch for
this evaluation, or should Set remain unmatched/NONE?
```

## 4. Actual Construct

F-005 is a deterministic threshold-and-veto classifier over the certified F-004
score, hard gates, required-data status and side-specific veto diagnostics. It
also defines the Set-owned boundary between a successful classifier result,
complete Set match, valid Market Handoff, and no-handoff outcomes.

It does not recalculate F-004, infer missing values, add vetoes, reverse
direction, rank multiple Set configurations, or authorize execution.

## 5. Exact Formula / Rule

### 5.1 Required-data gate

All eleven required inputs and their required derived diagnostics must be
available:

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

If any required item or required derived diagnostic is missing, malformed,
contradictory or incompatible:

```text
classifier_direction = NONE
primary_rejection_stage = DATA_UNAVAILABLE
matched = false
```

A numeric score alone is insufficient, particularly when local 5m veto evidence
is unavailable. Missing evidence is never clamped, substituted, inferred,
treated as false, or converted to a neutral contribution.

### 5.2 Hard gates

F-004 owns the gate predicates:

```text
DE_15m < 0.30 -> DIRECTIONAL_EFFICIENCY_GATE
TOD_REL_TURNOVER < 0.70 -> ACTIVITY_GATE
ATR_PCT_15m_PERCENTILE < 15 -> VOLATILITY_GATE
ATR_PCT_15m_PERCENTILE > 97 -> VOLATILITY_GATE
```

Equality passes these gates. If any hard gate fails, F-005 returns `NONE` and
does not force the opposite side.

### 5.3 Threshold classifier

Using canonical Q36 `DIRECTION_SCORE` from F-004:

```text
if required data unavailable:
    classifier_direction = NONE

else if hard gate fails:
    classifier_direction = NONE

else if DIRECTION_SCORE >= +0.35:
    candidate_side = LONG
    if any LONG-side veto active:
        classifier_direction = NONE
    else:
        classifier_direction = LONG

else if DIRECTION_SCORE <= -0.35:
    candidate_side = SHORT
    if any SHORT-side veto active:
        classifier_direction = NONE
    else:
        classifier_direction = SHORT

else:
    classifier_direction = NONE
    primary_rejection_stage = SCORE_DEAD_ZONE
```

The dead zone is the open interval:

```text
(-0.35, +0.35)
```

There is no forced opposite classification. A LONG-side veto blocks only a LONG
candidate. A SHORT-side veto blocks only a SHORT candidate.

### 5.4 Candidate-side vetoes

Active direction-specific vetoes:

```text
BTC contradiction veto
Relative contradiction veto
Local momentum contradiction veto
```

Disabled / not present in v0.4:

```text
raw aggressive-flow veto
undefined strong-HTF-structure veto
OI veto
funding veto
premium veto
```

F-005 applies only the candidate side's three vetoes. Opposite-side vetoes are
retained as upstream diagnostics but do not block or reverse the candidate.

### 5.5 Set resolution

```text
classifier_direction = LONG
-> directional criterion satisfied for LONG branch
```

```text
classifier_direction = SHORT
-> directional criterion satisfied for SHORT branch
```

```text
classifier_direction = NONE
-> no directional branch is satisfied
-> matched = false
-> direction = NONE
```

Directional classification satisfies only the corresponding directional
criterion. Matching additionally requires the governing versioned Set expression
to be authoritatively `TRUE`, with exact Core Set, constituent evidence, active
formation epoch, configuration, source/evaluation identities and applicable
sequence, freshness, expiry, reset/re-arm and event-consumption rules retained.

`FALSE` or `UNAVAILABLE` cannot become a match. Event-dependent formation
inherits authoritative same-epoch `FALSE -> TRUE`, no bridging across
`UNAVAILABLE` and durable once-only consumption. These are Set-owned
dependencies, not new F-005 trading predicates.

## 6. Inputs

| Input | Meaning | Unit/type | Dependency |
|---|---|---|---|
| `DIRECTION_SCORE` | Pre-classification score | Q36 dimensionless value in `[-1,+1]` | F-004 certified |
| Required-data status | Completeness over eleven required items | AVAILABLE / UNAVAILABLE | F-004 certified |
| Hard gate diagnostics | Data, DE, activity, volatility gates | Discrete statuses with values/thresholds | F-004 certified |
| Side-specific veto diagnostics | BTC, relative, local momentum vetoes for both sides | Boolean/status plus values/reasons | F-004 certified |
| Set formation evidence | Core Set and constituent state | Versioned Set-owned contract | Active Set methodology |
| Market Handoff primitives | Identity, timestamps, immutable direction, reference price, volatility, geometry and policy contexts | Strict contract fields | Market Handoff v4 |
| Numeric policy | Working values and serialization | `TT_SET_NUMERIC_V1` | Approved policy |

F-001 sign evidence is not final direction. F-002 is direction-neutral. F-003
is volatility context. F-004 is the immediate mathematical dependency.

## 7. Outputs

| Output | Meaning |
|---|---|
| `classifier_direction` | `LONG`, `SHORT` or `NONE`. |
| `candidate_side` | `LONG`, `SHORT` or absent when no trustworthy candidate exists. |
| `matched` | Boolean Set match state after classifier, Set formation and handoff validation. |
| `direction` | `LONG` or `SHORT` only for a committed matched Set; `NONE` only in unmatched evaluation records. |
| `primary_rejection_stage` | First applicable classification rejection, or separate Set-resolution reason after classifier success. |
| `all_failed_gates[]` | Known failed hard gates in canonical order, including data unavailable when applicable. |
| `all_active_vetoes[]` | Known active candidate-side vetoes in canonical order. |
| Upstream veto evidence | All six F-004 side-specific veto statuses, values and availability reasons, preserved separately. |
| `decision_cycle_id` | Created only when a matched result and valid handoff commit. |
| `set_result_id` | Created only when a matched result and valid handoff commit. |
| Market Handoff | Emitted only for committed `LONG` or `SHORT`. |

## 8. Units

F-005 operates on dimensionless F-004 working scores, discrete diagnostics and
contract identifiers. Market Handoff decimal fields use exact canonical decimal
strings under `TT_SET_NUMERIC_V1` and Market Handoff v4.

## 9. Parameters

| Parameter | Approved value |
|---|---|
| `LONG_THRESHOLD` | `+0.35` |
| `SHORT_THRESHOLD` | `-0.35` |
| Required data | all eleven required F-004 items available |
| Rejection priority | `DATA_UNAVAILABLE > DIRECTIONAL_EFFICIENCY_GATE > ACTIVITY_GATE > VOLATILITY_GATE > BTC_VETO > RELATIVE_VETO > LOCAL_MOMENTUM_VETO > SCORE_DEAD_ZONE` |
| Candidate veto order | BTC, relative, local momentum |
| Handoff contract | Market Handoff v4 |

Thresholds and veto parameters are pinned methodology values. Their empirical
performance remains a research question.

## 10. Domain / Preconditions

Before F-005 can commit a matched result:

1. F-004 final specification outputs are available for one coherent symbol,
   configuration and governed evaluation.
2. All required F-004 inputs and diagnostics are available.
3. No hard gate fails.
4. Q36 `DIRECTION_SCORE` crosses `+0.35` or `-0.35`.
5. The candidate side's vetoes are all inactive and available.
6. The governing Set formation expression is authoritatively `TRUE`.
7. Market Handoff v4 required fields and semantic invariants are satisfied.

## 11. Missing / Invalid Behavior

| Case | Approved behavior |
|---|---|
| Required F-004 evidence unavailable | `NONE`, `DATA_UNAVAILABLE`, no match/handoff. |
| Unknown individual gate | Record unavailable, not failed or passed. |
| Hard gate failed | `NONE`, primary priority among failed gates, no opposite side. |
| No trustworthy score candidate | `all_active_vetoes[]` empty with explicit unavailable-score or dead-zone reason. |
| Score in dead zone | `NONE`, `SCORE_DEAD_ZONE`. |
| Candidate-side veto active | `NONE`; primary veto order BTC, relative, local. |
| Opposite-side veto active only | Does not block or reverse candidate. |
| Classifier succeeds but Set formation fails | `matched=false`, final `direction=NONE`, separate Set-resolution reason; no committed IDs/handoff. |
| Classifier and formation succeed but required handoff validation fails | `matched=false`, final `direction=NONE`, separate handoff-validation reason; no committed IDs/handoff. |
| Delivery failure after committed match/handoff | Existing match remains committed; retry same committed handoff. |

`UNAVAILABLE` is not zero, false, neutral, `NONE` as a successful classification
state, or a stale value.

## 12. Boundaries

- `DIRECTION_SCORE = +0.35` qualifies for LONG when all other requirements
  pass.
- `DIRECTION_SCORE = -0.35` qualifies for SHORT when all other requirements
  pass.
- `0.35 - 10^-36` is dead-zone `NONE`.
- `-0.35 + 10^-36` is dead-zone `NONE`.
- One scalar score cannot select both directions.
- A directional Set may never emit `matched=true, direction=NONE`.
- Successful classification is not sufficient for a committed match or handoff.

## 13. Precision / Rounding

Q36 F-004 working values govern classification. Do not use binary floats,
epsilon comparisons, display-rounded values, exported diagnostic contributions
or summed contribution diagnostics.

Market Handoff volatility uses prescribed Q18 serialization. Reference ages use
exact nonnegative timestamp deltas rounded upward to integer seconds.

## 14. Time Semantics

F-005 uses the governed completed-5m evaluation cadence and eligible completed
5m/15m/1h evidence selected by Set/F-004. Persist analytical cutoff,
authoritative match time and frozen snapshot identity. Restart time, receipt
time or current wall clock cannot replace these.

For unmatched `NONE`, Set records an evaluation only. For committed LONG/SHORT,
Set freezes the result and handoff evidence.

## 15. State / Replay / Restart

Persist:

- F-004 final specification identity;
- classifier configuration;
- Set definition/version;
- numeric policy;
- handoff contract version;
- analytical cutoff and source selector identities;
- `DIRECTION_SCORE`, gates, vetoes, all availability reasons and preserved
  upstream diagnostics;
- classifier direction and candidate side;
- Set formation evidence and resolution reason;
- if committed, match state, consumption bindings, cycle/result identities,
  frozen contexts and handoff outbox record.

Match state, consumption bindings, cycle/result identities, frozen contexts and
handoff outbox commit together. Replay restores the same committed identities
and evidence; it cannot create a fresh opportunity, refresh an event or replace
frozen facts with current observations.

## 16. Configuration Pinning

F-005 pins:

```text
direction_classifier_id = TT-METH-014
direction_classifier_version = 0.4.1
scope = ALTCOIN_VS_BTC
LONG_THRESHOLD = +0.35
SHORT_THRESHOLD = -0.35
F-004 final specification identity
Set definition/version
Market Handoff contract version = 4
set_numeric_policy_version = TT_SET_NUMERIC_V1
```

Configurations needing arbitration among multiple eligible Core Sets must
supply a deterministic Set-owned rule consistent with this classifier. Missing
or conflicting resolution makes the configuration ineligible. No first-arrival,
lexical or strongest-score tie-break is invented here.

## 17. Dependencies

| Dependency | Class | Status |
|---|---|---|
| F-004 | CERTIFIED_FORMULA | Supplies score, gates, required-data and veto diagnostics. |
| F-001 | CERTIFIED_FORMULA | Formation evidence only; not final direction. |
| F-002 | CERTIFIED_FORMULA | Direction-neutral confirmation. |
| F-003 | CERTIFIED_FORMULA | Volatility context via F-004/handoff. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Strict Set-to-Position output contract. |
| Active Set methodology | DOCUMENTATION_DEPENDENCY | Set formation, classifier and output semantics. |
| `TT_SET_NUMERIC_V1` | APPROVED_POLICY | Working values and serialization. |

## 18. Ownership

Set owns direction classification, match state, Set Result creation, producer
thesis bindings and Market Handoff production. Position Rules consume/validate
the frozen handoff but cannot supply missing references, infer direction,
reverse direction or rerun Set. Portfolio Rules do not determine LONG/SHORT.
Order Lifecycle does not create direction.

## 19. Pipeline Role

```text
F-004 analytics -> F-005 direction classifier / Set match -> Market Handoff -> Position Rules
```

F-005 unblocks F-008, F-006 and F-007 only by certifying the Set-owned direction
and handoff/no-handoff boundary. It does not certify downstream entry, stop,
target, sizing or edge formulas.

## 20. Approved Uses

F-005 may be used to:

- classify Set evidence into `LONG`, `SHORT` or `NONE`;
- produce deterministic rejection diagnostics;
- determine whether directional classification criterion is satisfied;
- gate matched Set Result and Market Handoff creation;
- preserve immutable direction for downstream Position consumption.

## 21. Prohibited Interpretations

F-005 must not be interpreted as:

- proof of profitability;
- expected return;
- probability of continuation;
- liquidity or execution-quality measure;
- risk approval;
- Portfolio capital approval;
- entry/stop/target/size calculation;
- execution authorization;
- permission for Position to infer or reverse direction.

## 22. Known Limitations

The score is heuristic, not probability, expected return or risk-adjusted edge.
Centered evidence may oppose raw price movement. Neighboring evaluations may
change direction. Primary rejection is a deterministic diagnostic, not a causal
performance attribution.

## 23. Research Parameters

The predictive value of `+0.35` / `-0.35`, veto benefit, side/symbol asymmetry,
regime stability, turnover interaction and net performance after costs remain
research questions.

## 24. Empirical Validation Requirements

Empirical validation must separately evaluate classification precision/recall,
LONG/SHORT asymmetry, cost-adjusted outcomes, regime sensitivity, veto
incremental value, dead-zone behavior and downstream Position interaction. No
such validation is supplied by this certification.

## 25. Eight Final Expert Verdicts

| Expert perspective | Final verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Inclusive thresholds, abstention and candidate-side vetoes form a coherent directional filter. Classification does not establish a profitable opportunity. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | F-004 activity and flow evidence is consumed consistently. It supplies neither executable liquidity nor spread, slippage or participation-authenticity assurance. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | BTC context and volatility gates constrain classification without becoming a complete regime model. Fixed thresholds and historical normalization remain regime-sensitive. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Exact Q36 comparisons produce mutually exclusive LONG/SHORT regions and an open dead zone. Council definitions make rejection resolution deterministic. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Required-data failure overrides a calculable score. Classification, complete Set matching and valid handoff remain separate requirements; none supplies risk approval. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Strict handoff validation, atomic match persistence and replay identity preserve the producer/consumer contract. No execution authority is introduced. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Missing veto inputs, simultaneous failures, opposite-side vetoes, conflicting branches and restart duplication have defined outcomes. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Complete upstream diagnostics plus candidate-specific rejection evidence support attribution. Primary rejection alone must not be interpreted as causal strategy performance. |

## 26. Final Council Record

```text
FINAL_COUNCIL_RECORD

formula_id: F-005
formula_name: Set direction classifier and LONG/SHORT handoff
reviewed_candidate: F-005_COUNCIL_DEFINED_CYCLE_1
specification_status: APPROVED_WITH_RECORDED_COUNCIL_DEFINITIONS
trading_fitness: ADEQUATE_FOR_DECLARED_SET_OWNED_ROLE_WITH_LIMITATIONS

senior_intraday_crypto_trader: APPROVE_WITH_LIMITATIONS
microstructure_order_flow_researcher: APPROVE_WITH_LIMITATIONS
market_regime_context_analyst: APPROVE_WITH_LIMITATIONS
quant_strategy_researcher: APPROVE_WITH_LIMITATIONS
risk_trade_management_architect: APPROVE_WITH_LIMITATIONS
execution_exchange_mechanics_specialist: APPROVE_WITH_LIMITATIONS
adversarial_strategy_reviewer: APPROVE_WITH_LIMITATIONS
performance_strategy_diagnostics_analyst: APPROVE_WITH_LIMITATIONS

F005-C01: CLOSED_BY_RECORDED_SPECIFICATION
F005-C02: CLOSED_BY_RECORDED_SPECIFICATION
F005-C03: CLOSED_BY_RECORDED_SPECIFICATION
F005-C04: CLOSED_BY_RECORDED_SPECIFICATION
F005-C05: CLOSED_BY_RECORDED_SPECIFICATION
F005-C06: ACCEPTED_PRODUCT_SCOPE
F005-C07: RETAINED_EMPIRICAL_QUESTION_NON_BLOCKING
F005-C08: RETAINED_NON_BLOCKING_LIMITATION

blocking_findings_remaining: NONE
unresolved_dependency_or_product_blockers: NONE_WITHIN_DECLARED_SCOPE
empirical_effectiveness_and_parameter_calibration: NOT_ESTABLISHED
implementation_and_live_deployment: NOT_CERTIFIED

full_council_approved: YES
another_review_cycle_required: NO
```
