# F-009 FULL COUNCIL REVIEW CYCLE 2

formula_id: F-009
review_mode: REVALIDATION
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
specification_status: FINAL_APPROVED
trading_fitness: ADEQUATE_FOR_DECLARED_STOP_INTEGRATION_ROLE_WITH_LIMITATIONS

## Result

The Council reviewed `F-009_REVISED_SPEC_CYCLE_1.md` against certified F-006,
F-007 and F-008. Blockers F009-C01 and F009-C02 are closed. No regression was
identified in fixed or dynamic stop integration semantics.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | APPROVE_WITH_LIMITATIONS | Mode dispatch, fixed-domain validation, terminal failures and dynamic integration are sufficiently specified. |
| Mathematical Correctness Reviewer | APPROVE | LONG floor and SHORT ceiling preserve adverse-side geometry. Final distance equals `E*S/100 + delta`, with `0 <= delta < t`. |
| Numeric Precision and Determinism Reviewer | APPROVE_WITH_LIMITATIONS | Exact rational arithmetic and explicit positive tick-grid invariants implement the included N-004/TT_NUMERIC_V1 rules; diagnostic-order limitation is preserved. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Adequate for the declared stop-integration role; percentage displacement and inherited structural stops are coherent, but effectiveness and calibration remain unproven. |
| Risk and Trade Management Reviewer | APPROVE_WITH_LIMITATIONS | Invalid configuration and failed calculations reject without repair. Final-price downstream checks remain mandatory; planned distance does not bound realized loss. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | Outward tick construction is sound. Venue constraints, trigger behavior, protective coverage and fills remain outside this certification. |
| Dependency and Architecture Boundary Reviewer | APPROVE | F-008 retains entry ownership; F-006/F-007 retain dynamic selection, calculation and feasibility. No downstream formula is certified. |
| Replay / State / Auditability Reviewer | APPROVE_WITH_LIMITATIONS | Frozen inputs, dependency identities, configuration digests, tick provenance and persisted outcomes support replay; persistence implementation is unverified. |

## Blocker Closure Assessment

| Blocker | Classification | Disposition |
|---|---|---|
| F009-C01 | SPECIFICATION_DEFECT | CLOSED. Sections 5.2-5.3 and 11 require finite exact percent units, `S > 0` and LONG `S < 100`; invalid FIXED configuration returns `CONFIG_INVALID`. No implicit default or inferred SHORT upper bound; DYNAMIC ignores `fixed_pct`. |
| F009-C02 | SPECIFICATION_DEFECT | CLOSED. Sections 5.1 and 5.4-5.6 require positive finite `E`/`t`, exact arithmetic, outward quantization, finite positive grid-aligned `SL` and strict adverse-side geometry. Arithmetic or output-invariant failure terminates with `ROUNDING_ERROR` and no actionable stop. |

## Limitations To Preserve

- Simultaneous invalid-input primary-reason priority is not fully specified, and
  some outer reason aliases are permitted. All such outcomes reject; approval
  does not establish canonical cross-implementation diagnostic ordering. Replay
  must retain reproducible reasons.
- No fixed-percentage default or universal SHORT upper bound is approved. Any
  future policy requires explicit specification.
- Outward rounding can materially widen percentage distance; LONG stops can
  round to zero and must reject.
- Exchange acceptance, fills, liquidation protection and maximum realized loss
  are not guaranteed.
- Dynamic `post_rounding.pct` remains uncertified, non-decision diagnostics.
- Inherited dependency limitations remain, including F-008's unresolved F-003
  corrected-history acceptance.
- F-010, F-011 and F-012 remain uncertified.

## Empirical Validation Required

Chronological out-of-sample evaluation of T-004 and inherited dynamic
parameters across symbols, sides, regimes and tick-to-stop ratios, including
rejected and unfilled opportunities. Measure adverse excursion, stop frequency,
realized loss, costs, slippage, gaps and partial fills. Candle touches cannot
establish fills or exit ordering.

## Final Approval Record

```yaml
approved_by: FULL_COUNCIL
review_date: 2026-09-15
reviewed_candidate: F-009_REVISED_SPEC_CYCLE_1.md
reviewed_candidate_sha256: 16163cecdbd310aacb0de111b826142b1caa23df3933d35b6a8d210bf030a15c
specification_status: FINAL_APPROVED
trading_fitness: ADEQUATE_FOR_DECLARED_STOP_INTEGRATION_ROLE_WITH_LIMITATIONS
blocker_disposition: {F009-C01: CLOSED, F009-C02: CLOSED}
approved_semantics: Preserve candidate Sections 3-25, including output fields, failure mappings, immutable dependency boundaries and replay requirements.
pinned_identity: Baseline v1.2.14; Market Handoff v4; TT_SET_NUMERIC_V1; TT_NUMERIC_V1; N-004 tick provenance; Order Spec v5; supplied certified F-006/F-007/F-008 specifications.
new_council_semantic_definitions: NONE
excluded_certifications: [F-010, F-011, F-012, implementation, execution, deployment]
execution_live_money_git_authority: NOT_GRANTED
```
