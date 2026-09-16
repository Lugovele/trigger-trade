# FULL_COUNCIL_REVIEW_CYCLE_3

Formula: F-001 - Price-move trigger calculation
Mode: REVALIDATION_AFTER_CYCLE_2_FIXES
Date: 2026-09-15
Council model: FULL_COUNCIL

## Council Record

F-001 is approved for its declared narrow Trigger role, with limitations. Both
prior blockers are closed.

```text
formula_id: F-001
review_mode: REVALIDATION_AFTER_CYCLE_2_FIXES
council_verdict: APPROVE_WITH_LIMITATIONS
F001-RV01: CLOSED
F001-RV02: CLOSED
blocking_findings_remaining: NONE
full_council_approved: YES
another_review_cycle_required: NO
trading_fitness: ADEQUATE_FOR_DECLARED_NARROW_ROLE_WITH_LIMITATIONS
empirical_effectiveness_and_parameter_calibration: NOT_ESTABLISHED
```

Evidence reviewed:

- `docs/formula-certification/_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_2.md`
- `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md`

All eight perspectives were applied within this single review. No other files,
subagents, tests, edits or trading actions were used by the Council.

## Findings and Closure

| Item | Classification | Council disposition |
|---|---|---|
| F001-RV01: operative freshness | SPECIFICATION_DEFECT - closed | Sections 15-17 supply the policy identifier, operative slot-equality predicate, authoritative requested-slot basis, persistence requirements and restart behavior. Missing/unknown policy prevents satisfaction. No unspecified timeout remains necessary. |
| F001-RV02: associated-output availability | SPECIFICATION_DEFECT - closed | Sections 7, 11-13 and 16 distinguish arithmetic availability from Trigger availability. Invalid price/source evidence produces unavailable arithmetic and sign. Invalid threshold with otherwise valid arithmetic requires computed diagnostic evidence and an unavailable Trigger. Diagnostics cannot satisfy CURRENT_STATE. |
| Diagnostic retention under policy/configuration failure | PRODUCT_DECISION - accepted | Independently valid arithmetic may survive these failures. The "may be retained" provision is permissive and must not be silently rewritten as mandatory retention for every configuration/policy failure. Whenever arithmetic is available, its signed value and corresponding sign are defined. |
| One-minute endpoints, positive research threshold, magnitude predicate and slot-only freshness | PRODUCT_DECISION - accepted | These choices define the intended detector. Certification selects no threshold and adds no wall-clock freshness limit, directional mapping or ATR normalization. |
| External source governance and recovery | DEPENDENCY_GAP - non-blocking | Set/KLINES governance remains an external contract. F-003 leaves corrected-history acceptance/release unresolved and supplies no automatic recovery authority for F-001. |
| Threshold usefulness and downstream contribution | EMPIRICAL_QUESTION - open | Calibration, regime outcomes, execution-cost effects and incremental strategy benefit remain research obligations. |
| Endpoint measurement and freshness limits | NON_BLOCKING_LIMITATION | Endpoint displacement omits path and microstructure. Slot equality establishes logical freshness, not feed liveness or guaranteed wall-clock recency. |

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Suitable for detecting sufficiently large completed-minute displacement. It does not establish an attractive entry. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Same-source, completed, final and contiguous endpoint selection supports the measurement. Trade-derived closes do not establish spread, depth, activity, order-flow imbalance or executable capacity. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | A fixed percentage threshold is interpretable, but equal readings need not mean equal opportunity or risk across regimes or symbols. F-003 remains separate volatility context. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Signed return, percent units, positive denominator, Q36 HALF_EVEN quantizer and exact inclusive magnitude comparison are coherent. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Unavailable Trigger results and retained diagnostics cannot satisfy formation. TRUE establishes no position eligibility, acceptable loss, sizing or execution permission. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Source binding, cutoff eligibility, persisted identities and duplicate handling support reproducible analytical evaluation. Q36 is analytical precision, not an exchange price increment. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Invalid-threshold/invalid-price cases avoid fabricated diagnostics, restart cannot renew a slot, and legacy behavior is excluded. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Available FALSE, unavailable evaluation and retained diagnostics are distinguishable research populations. Performance evidence is not supplied. |

## Approved Semantic Record

1. F-001 is a Set-owned `TRADING_FORMULA`, family `TRIGGER`, under v1.2.14
   provenance. It measures signed close-to-close displacement over the latest
   completed one-minute interval and contributes direction-neutral
   CURRENT_STATE evidence to Set formation.
2. Use trade-price-derived `KLINES.close` from the current completed one-minute
   candle and its immediately preceding one-minute candle, with the same venue,
   product, instrument and factual source.
3. Compute:

```text
move_pct_work = Q36(100 * (observed_price - reference_price) / reference_price)
```

Then evaluate:

```text
abs(move_pct_work) >= theta_move_pct
```

exactly and inclusively.
4. `theta_move_pct` remains mandatory, positive and pinned; certification
   chooses no value. Derive UP/DOWN/FLAT from the Q36 result.
5. Preserve separate arithmetic status and tri-state Trigger result. Invalid
   price/source evidence means unavailable displacement and sign, never zero,
   FLAT or a previous value. Invalid threshold with otherwise valid arithmetic
   retains computed diagnostics but yields `UNAVAILABLE`.
6. Preserve freshness policy
   `F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY` and
   `fresh_for_slot = (evaluation_slot == requested_current_slot)`.
7. Restore accepted state before new evaluation. Restart does not renew
   freshness. Conflicts require integrity/reconciliation handling.
8. Set owns evaluation, persistence, formation and final direction. F-003
   supplies separate downstream volatility context only. Do not divide F-001 by
   ATR or import F-003 timeframe/cutoff/smoothing/export quantizer.

Approval scope: specification correctness and conceptual fitness for this
completed-minute displacement Trigger. This Council record establishes no
strategy-performance or live-deployment certification.
