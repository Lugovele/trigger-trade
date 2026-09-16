```yaml
formula_id: F-010
review_mode: REVALIDATION
FULL_COUNCIL_APPROVED: NO
ANOTHER_REVIEW_CYCLE_REQUIRED: YES
reviewed_candidate_sha256: 0a154a6886279f9f8c0f1eebcb924f191acf4f00816fb544b92ba1e396c9601e
```

**eight_expert_verdicts**

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | CHANGES_REQUIRED | Geometry-capability gate still lacks an executable definition. |
| Mathematical Correctness Reviewer | APPROVE | Inclusive `4*d >= 3*A` and `d <= 4*A` comparisons and inward rounding are correct. Six exact arithmetic checks passed, covering both sides and rounding-induced rejection. |
| Numeric Precision and Determinism Reviewer | APPROVE_WITH_LIMITATIONS | Exact arithmetic, unchanged Q18 ATR and Unicode code-point ordering resolve calculation determinism; overall availability still depends on the undefined gate. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Structural priority, too-close continuation and too-far termination are coherent. Their effectiveness remains empirical. |
| Risk and Trade Management Reviewer | APPROVE_WITH_LIMITATIONS | Terminal post-rounding rejection and prohibitions on Entry/SL-derived repair are preserved. Downstream gates remain mandatory. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | Inward quantization is sound; tick validity establishes neither acceptance nor fills. |
| Dependency and Architecture Boundary Reviewer | CHANGES_REQUIRED | F-008 Entry ownership and F-009 stop independence are preserved, but capability evidence has no defined dependency mapping. |
| Replay / State / Auditability Reviewer | CHANGES_REQUIRED | Configuration, bindings, ordering and outcomes are preserved; capability evidence or its deterministic derivation is missing. |

**blocker_closure_assessment**

- **F010-C01: CLOSED.** Producer identity, availability, uniqueness and binding failures reject before selection. `NONE` requires a null pair; `REQUIRED` cannot fall back; `PREFERRED` fallback cannot repair producer evidence. Apply §5.15 identity-error precedence over thesis eligibility reasons.
- **F010-C02: CLOSED.** Ordering specifies family/type priority, latest exact availability, smallest exact distance, then case-sensitive Unicode code points with shorter prefixes first. `TOO_FAR` stops before later same-type candidates.
- **F010-C03: PARTIALLY_CLOSED.** Permitted types, pools and primary reason ordering are explicit. The capability predicate remains undefined.

**blockers**

**F010-C03 - SPECIFICATION_DEFECT:** [Candidate §5.6](C:/Users/Елена/Documents/trigger-trade/docs/formula-certification/_orchestrator/work/F-010/F-010_REVISED_SPEC_CYCLE_1.md:198) describes capability as "unavailable" without identifying a source field or deriving that state from declared inputs. Neither the input table nor replay requirements supply it. The referenced [Market Handoff v4 schema](C:/Users/Елена/Documents/trigger-trade/docs/trading-methodology/schemas/wire.schema.json:1364) provides `reference_geometry.levels` and rejects additional geometry properties.

Consequently, the same declared inputs do not determine whether capability is available and selection may proceed, or `NO_FAVORABLE_SIDE_GEOMETRY` must reject. An empty eligible pool cannot resolve this: the candidate separately assigns it `NO_ELIGIBLE_REFERENCE`.

**required_revision_instructions**

1. Define capability as an explicit deterministic predicate over identified, frozen inputs, including missing, invalid and unavailable cases.
2. Reconcile that predicate with Market Handoff v4. If an additional dependency is required, specify its version, binding and persistence; otherwise define when this branch is reachable using existing inputs.
3. Add fixtures distinguishing unavailable capability, available capability with no basic candidates, and available capability with a selectable target. Verify primary reasons and restart equality.
4. Preserve the closed C01/C02 semantics and all selection, rounding and ownership boundaries.

**limitations_to_preserve**

- Thresholds, hierarchy and recency preference remain unvalidated research parameters.
- Frozen references may become stale; inward rounding does not guarantee profitability, acceptance or execution.
- Diagnostic alternatives must never change primary selection or terminal rejection.
- Implementation, persistence and execution remain uncertified. F-008’s corrected-history limitation remains inherited. F-011 and F-012 are outside this review.

**empirical_validation_required**

Chronological out-of-sample evaluation must include rejected and unfilled opportunities, segmented by instrument, direction, family, thesis policy, regime, reference age and tick/ATR ratio. Assess threshold sensitivity, hierarchy/recency effects, too-far rejections and realized outcomes after costs. Candle touches do not establish fills or exit ordering.

**final_approval_record**

Not issued. One specification blocker remains. No files were modified; no additional agents were spawned.
