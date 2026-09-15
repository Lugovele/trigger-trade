# F-005 Full Council Review Cycle 1

```text
formula_id: F-005
review_mode: FULL_REVIEW
all_eight_perspectives_applied: YES
full_council_approved: YES
another_review_cycle_required: NO
blocking_findings_remaining: NONE_FOR_COUNCIL_DEFINED_CANDIDATE
```

Approval applies to `F-005_COUNCIL_DEFINED_CYCLE_1`, defined as the Source Pack
plus the mandatory Council clarifications. The Source Pack alone left
determinism gaps, all closed by the Council-defined specification language.

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Inclusive thresholds, abstention and candidate-side vetoes form a coherent directional filter. Classification does not establish a profitable opportunity. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | F-004 activity and flow evidence is consumed consistently. It supplies neither executable liquidity nor spread, slippage or participation-authenticity assurance. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | BTC context and volatility gates constrain classification without becoming a complete regime model. Fixed thresholds and historical normalization remain regime-sensitive. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Exact Q36 comparisons produce mutually exclusive LONG/SHORT regions and an open dead zone. The Council definitions make rejection resolution deterministic. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Required-data failure overrides a calculable score. Classification, complete Set matching and valid handoff remain separate requirements; none supplies risk approval. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Strict handoff validation, atomic match persistence and replay identity preserve the producer/consumer contract. No execution authority is introduced. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Missing veto inputs, simultaneous failures, opposite-side vetoes, conflicting branches and restart duplication have defined outcomes under the candidate. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Complete upstream diagnostics plus candidate-specific rejection evidence support attribution. Primary rejection alone must not be interpreted as causal strategy performance. |

## Findings

| ID | Classification | Disposition |
|---|---|---|
| F005-C01 | SPECIFICATION_DEFECT | Closed by Council: primary veto tie-break is BTC, then relative, then local momentum; this orders diagnostics only. |
| F005-C02 | SPECIFICATION_DEFECT | Closed by Council: retain complete F-004 evidence separately and define F-005 diagnostic projections. |
| F005-C03 | DEPENDENCY_GAP | Closed for this generic formula: require pinned, traceable Set formation contract. Concrete configurations lacking that evidence are ineligible. |
| F005-C04 | SPECIFICATION_DEFECT | Closed by Council: distinguish classifier success, match readiness, missing handoff data and delivery failure through explicit resolution and atomic persistence rules. |
| F005-C05 | DEPENDENCY_GAP | Closed by Council: Set resolves producer thesis bindings; downstream calculation candidates cannot supply or replace them. |
| F005-C06 | PRODUCT_DECISION | Accepted scope restriction: preserve pinned symmetric thresholds, dead zone and no-opposite policy; no hysteresis or branch-ranking heuristic. |
| F005-C07 | EMPIRICAL_QUESTION | Retained non-blocking: predictive value, veto benefit, side/symbol asymmetry, regime stability, turnover and net performance after costs remain unestablished. |
| F005-C08 | NON_BLOCKING_LIMITATION | Retained: score is heuristic, not probability, expected return or risk-adjusted edge. |

## Final Council Record

```text
reviewed_candidate: F-005_COUNCIL_DEFINED_CYCLE_1
specification_status: APPROVED_WITH_RECORDED_COUNCIL_DEFINITIONS
trading_fitness: ADEQUATE_FOR_DECLARED_SET_OWNED_ROLE_WITH_LIMITATIONS
expert_verdicts: 8_APPROVE_WITH_LIMITATIONS
findings_C01_through_C05: CLOSED_BY_RECORDED_SPECIFICATION
finding_C06: ACCEPTED_PRODUCT_SCOPE
findings_C07_C08: RETAINED_NON_BLOCKING
unresolved_dependency_or_product_blockers: NONE_WITHIN_DECLARED_SCOPE
empirical_effectiveness_and_parameter_calibration: NOT_ESTABLISHED
implementation_and_live_deployment: NOT_CERTIFIED

full_council_approved: YES
another_review_cycle_required: NO
```
