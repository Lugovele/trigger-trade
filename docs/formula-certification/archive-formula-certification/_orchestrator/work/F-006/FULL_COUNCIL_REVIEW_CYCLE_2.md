# F-006 FULL COUNCIL REVIEW CYCLE 2

formula_id: F-006
review_mode: REVALIDATION
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO

## Result

The Council reviewed `F-006_REVISED_SPEC_CYCLE_1.md` against certified F-003,
F-005 and F-008. Both Cycle 1 blockers are closed. No regression was identified
within the reviewed specification and dependency boundaries.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | APPROVE_WITH_LIMITATIONS | Eligibility, selection, stop construction and terminal rejection are coherent and sufficiently specified. |
| Mathematical Correctness Reviewer | APPROVE | Pre-rounding distance equals `max(E - R + 0.20A, 0.50A)`. Outward rounding preserves the structural buffer and minimum distance; both cap checks are inclusive. |
| Numeric Precision and Determinism Reviewer | APPROVE | Exact received decimals, floor rounding, positive grid invariants and Unicode code-point ordering close both defects. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Adequate for the declared LONG structural-stop role. Reference quality, hierarchy and calibration remain empirically unvalidated. |
| Risk and Trade Management Reviewer | APPROVE_WITH_LIMITATIONS | Infeasible stops reject the plan without inward adjustment or weaker-reference retry. The cap bounds planned price distance only. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | Positive tick-grid construction is sound; exchange acceptance, trigger mechanics, liquidity and realized fills remain outside certification. |
| Dependency and Architecture Boundary Reviewer | APPROVE_WITH_LIMITATIONS | Preserves F-003 received Q18 ATR, F-005 committed immutable LONG direction and F-008 frozen entry. F-009 cannot alter the approved reference, candidate or feasibility result. |
| Replay / State / Auditability Reviewer | APPROVE_WITH_LIMITATIONS | Frozen inputs, exact ordering, pinned configuration and persisted selection evidence support reproducible results without refreshing or repairing state. |

## Blocker Closure Assessment

| Blocker | Closure |
|---|---|
| F006-C01 | CLOSED. Section 5.12 requires finite positive rounded stops, exact grid membership, correct outward rounding and prices below both `R` and `E`. Failure terminates with `ROUNDING_ERROR`; diagnostic prices are non-actionable. |
| F006-C02 | CLOSED. Section 5.7 orders by latest exact availability, smallest exact entry distance, then ascending case-sensitive ordinal Unicode code points. Section 5.5 rejects duplicate/conflicting IDs and invalid producer bindings before selection. |

## Blockers

None.

## Limitations To Preserve

- Strict one-tick exclusion and terminal selected-reference failure remain deliberate constraints.
- When F-008 entry and REQUIRED SL share reference `r`, `E <= r` makes it SL-ineligible: return `THESIS_REFERENCE_INVALID`, without rebinding or repricing.
- F-003 corrected-history acceptance and reconciliation release remain externally unresolved and non-blocking for this formula; approval supplies no recovery authority.
- ATR multipliers, family priority, recency preference and opportunity rejection rates remain empirically unvalidated.
- ATR lag, frozen geometry, coarse ticks, slippage, gaps, liquidation, latency, partial fills and outages limit practical effectiveness.
- A usable stop supplies neither complete-plan approval nor a realized-loss guarantee.
- `post_rounding.pct` remains diagnostic and uncertified; it must not feed selection, feasibility, sizing or risk/reward decisions.

## Empirical Validation Required

YES. Preserve chronological out-of-sample evaluation of all LONG opportunities,
including rejections and nonfills, stratified by symbol, regime, reference age,
thesis policy and tick/ATR ratio. Evaluate pinned defaults, family/recency
rules, adverse excursion, stop frequency, loss severity, costs and downstream
outcomes. Candle touches do not establish fills or exit ordering. No empirical
validation was performed here.

## Final Approval Record

```yaml
formula_id: F-006
reviewed_candidate: F-006_REVISED_SPEC_CYCLE_1.md
reviewed_candidate_sha256: 4e60b7dde3093d038b92fb6d51aa2df6bbc826ead8b997840527e7dfd546100d
specification_status: FINAL_APPROVED
trading_fitness: ADEQUATE_FOR_DECLARED_LONG_DYNAMIC_SL_ROLE_WITH_LIMITATIONS
blocker_disposition: {F006-C01: CLOSED, F006-C02: CLOSED}
approved_scope: LONG Dynamic SL reference selection, stop construction and feasibility
pinned_identity: TT-METH-016 v0.2.1; baseline v1.2.14; Market Handoff v4; TT_SET_NUMERIC_V1
pinned_constants: {buffer: 0.20, minimum_distance: 0.50, maximum_distance: 2.00, corroboration: 0.25}
final_artifact: F-006_FINAL_FORMULA_SPECIFICATION.md
finalization_rule: Update approval/title/status metadata and append this record; preserve all operative candidate semantics, fixtures and limitations.
new_council_semantic_definitions: NONE
excluded_certifications: [F-007, F-009, F-010, F-011, F-012]
implementation_execution_live_deployment: NOT_CERTIFIED
```
