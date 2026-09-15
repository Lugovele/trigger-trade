# F-001 FULL COUNCIL REVIEW CYCLE 1

Mode: DISCOVERY / FULL_REVIEW
Council route: `FULL_COUNCIL`
Result: `FULL_COUNCIL_APPROVED = NO`
Another review cycle required: `YES_AFTER_BLOCKING_SEMANTICS_ARE_RESOLVED`

## Council Summary

F-001 is not certifiable as a complete Trigger specification from the supplied evidence. A narrow calculation core is defensible as `COUNCIL_DEFINED`; its market-data binding, activation semantics, and relationship to F-003 remain unresolved.

## Evidence Reviewed By Council

1. `docs/formula-certification/F-001/F-001_SOURCE_PACK.md`
2. `docs/formula-certification/F-001/F-001_N008_DEPENDENCY_EVIDENCE.md`
3. `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md`

Council reported that only these files were read, all eight perspectives were applied in one review, and no subagents were used.

## Council-Defined Core

Candidate `F001-CD1`, status `COUNCIL_DEFINED`, scope `PARTIAL_CALCULATION_SPECIFICATION`:

```text
move_pct_work = Q36(100 * (P_observed - P_reference) / P_reference)
```

where `Q36` means rounding once to 36 fractional decimal places using `ROUND_HALF_EVEN`; numerical `1` means one percent.

Inputs and domain:

- both prices must be finite exact decimals from explicitly bound, admissible observations of the same instrument, price basis, and units;
- the reference observation precedes the observed endpoint;
- neither observation may exceed the fixed cutoff;
- `P_reference > 0`;
- `P_observed >= 0`;
- missing, conflicting, ineligible, or insufficiently identified evidence yields `UNAVAILABLE`, never substituted zero or `FALSE`;
- a factual zero observed price gives `-100%` only when independently admissible;
- the candidate defines no LONG/SHORT mapping.

N-008 application:

- evaluate difference, multiplication, and division exactly;
- apply one named-output quantizer;
- persist and consume canonical working value with policy, configuration, and source binding;
- no intermediate rounding, epsilon comparison, hidden precision, or display-rounded gates;
- no F-001 handoff field or 18-place export class is defined by this candidate.

Predicate boundary:

- a complete Trigger must explicitly bind price selection, horizon, permitted comparison, threshold parameter contract, and evaluation timing;
- once specified, compare the working value exactly against the governed threshold;
- this review selected no operator or threshold;
- parametric certification requires a complete parameter contract and observation semantics.

## Findings

| ID | Classification | Disposition |
|---|---|---|
| F001-R01 | SOURCE_GAP | Canonical F-001 observation and predicate semantics are absent. `F001-CD1` is a new arithmetic definition, not reconstructed source authority. Blocks complete certification. |
| F001-R02 | PRODUCT_DECISION | Observed price basis, endpoint/reference selection, horizon, predicate contract, cadence and configured formation role require definition. Their choices determine what market condition is detected. Blocks complete Trigger correctness and purpose-fit assessment. |
| F001-R03 | SOURCE_GAP | F-001 evidence declares an F-003 dependency, but does not define the operative relationship. F-003 approval does not prove F-001 uses ATR, prescribe division by ATR, or transfer its 15m timeframe. Resolve declared relationship before certification. |
| F001-C02 | SOURCE_GAP, CLOSED_NARROWLY | N-008 identity and operative semantics are available. `F001-CD1` is compatible at specification level. This closes evidence availability only. |
| F001-R04 | SOURCE_GAP, NON_BLOCKING | Family classification discrepancy remains: F-001 source pack reports `TRIGGER`; N-008 evidence reports `SET_ANALYTICS`. Review scope followed Set Trigger role. |
| F001-R05 | SOURCE_GAP, NON_BLOCKING_LIMITATION | Corrected-history acceptance and reconciliation release remain external governance gaps. |
| F001-R06 | EMPIRICAL_QUESTION | Threshold/horizon suitability and incremental trading benefit remain unestablished. |
| F001-R07 | NON_BLOCKING_LIMITATION | Endpoint displacement omits path, spread, depth, activity and execution capacity; percent normalization does not equalize volatility or risk across symbols. |

## Eight Expert Verdicts

All eight expert perspectives returned `BLOCKED` for complete F-001 certification:

1. Senior Intraday Crypto Trader
2. Market Microstructure & Order Flow Researcher
3. Market Regime & Context Analyst
4. Quant Strategy Researcher
5. Risk & Trade Management Architect
6. Execution & Exchange Mechanics Specialist
7. Adversarial Strategy Reviewer
8. Performance & Strategy Diagnostics Analyst

## Final Council Record

```text
mode: DISCOVERY / FULL_REVIEW
formula_id: F-001
formula_name: Price-move trigger calculation
candidate: F001-CD1
candidate_origin: COUNCIL_DEFINED
candidate_scope: PARTIAL_CALCULATION_SPECIFICATION
calculation_core_correctness: ACCEPTABLE_WITH_STATED_PRECONDITIONS
complete_trigger_specification: NOT_CERTIFIED
trading_fitness: CORE_CONCEPTUALLY_ADEQUATE; COMPLETE_TRIGGER_UNDETERMINED
blocking_findings: F001-R01, F001-R02, F001-R03
full_council_approved: NO
another_review_cycle_required: YES_AFTER_BLOCKING_SEMANTICS_ARE_RESOLVED
empirical_effectiveness: NOT_ESTABLISHED
```

Authority boundary: this record is formula-certification evidence only. It authorizes no implementation, promotion, commit, deployment, paper/live execution, exchange interaction, or runtime trading decision.
