# F-004 Full Council Review Cycle 3

```text
formula_id: F-004
review_mode: REVALIDATION
all_eight_perspectives_applied: YES
full_council_approved: YES
another_review_cycle_required: NO
blocking_findings_remaining: NONE
```

The Council approved `F-004_REVISED_SPEC_CYCLE_2.md` for its declared
Set-local analytical role. Both residual F004-C02 blockers are closed.
Approval covers specification correctness and conceptual fitness; empirical
effectiveness and implementation remain uncertified.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Initialization and midnight eligibility are deterministic. The composite supplies directional evidence; centered momentum can oppose raw-return sign, and trading benefit remains unestablished. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Same-clock quote-notional references exclude the current bucket and require source coverage. Turnover and aggressive flow remain distinct from F-002 base volume and do not establish executable liquidity or authentic activity. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Metric-specific first full days and restricted initialization exclusions define reproducible warmup populations. Thresholds and comparability across regimes remain empirical. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Population variance, prescribed sqrt rounding, inclusive ranks, clipping and exact weighted aggregation are retained. Population membership now has explicit boundaries and minimums. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Missing required evidence remains unavailable, including local-momentum veto inputs. A calculable score cannot override required-data failure or authorize downstream eligibility. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Separate 5m ATR ancestry, work precision, source identities and restart requirements remain intact. Analytical approval confers no execution authority. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Partial inception days, initialization prefixes, later invalid observations, midnight self-inclusion, insufficient references and duplicate identities have defined outcomes. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Population identities, availability reasons, gates, side-specific vetoes and contributions support attribution. Calibration and incremental performance remain research questions. |

## Finding Closure

| Finding | Status |
|---|---|
| F004-C01 | CLOSED. Eleven required inputs, `ALTCOIN_VS_BTC` scope, directional-efficiency gate/modifier and completed-source selection dependency remain operative. |
| F004-C02 | CLOSED. First-day eligibility, initialization exclusions, subsequent unavailable-value consequences, midnight membership, counts, minimums and bucket identity persistence are defined. |
| F004-C03 | CLOSED. Explicit local 5m Wilder(14) dependency and numeric-policy ancestry requirements are retained. F-003 certification remains limited to 15m. |
| F004-C04 | CLOSED. F-004 produces analytics/diagnostics; F-005 owns classification thresholds, side choice, veto consumption, final direction, rejection priority and handoff. |
| F004-C05 | CLOSED. Exact weighted products feed one final score quantizer; rounded contribution diagnostics never become score operands. |
| F004-C06 | RETAINED — EMPIRICAL_QUESTION. Thresholds, weights, factor redundancy, centered-sign usefulness, symbol/side asymmetry and net benefit remain unestablished and non-blocking. |
| F004-C07 | RETAINED — NON_BLOCKING_LIMITATION. Heuristic interpretation and measurement limitations remain. Corrected-history acceptance and reconciliation release remain externally unresolved. |

No new blockers were identified under `SPECIFICATION_DEFECT`,
`DEPENDENCY_GAP` or `PRODUCT_DECISION`.

## Final Council Record

```text
FINAL_COUNCIL_RECORD
reviewed_candidate: F-004_REVISED_SPEC_CYCLE_2
methodology_baseline: v1.2.14
numeric_policy: TT_SET_NUMERIC_V1
specification_status: FINAL_APPROVED
trading_fitness: ADEQUATE_FOR_DECLARED_NARROW_ROLE_WITH_LIMITATIONS
expert_verdicts: 8 x APPROVE_WITH_LIMITATIONS
required_specification_revisions: NONE
empirical_effectiveness_and_parameter_calibration: NOT_ESTABLISHED
implementation_and_live_deployment: NOT_CERTIFIED

full_council_approved: YES
another_review_cycle_required: NO
```

## Language To Preserve

1. Use `[D - 30 UTC days, D)`, with `D` derived from the persisted analytical cutoff. For each metric, the first countable day starts at `ceil_UTC_midnight(max(instrument/series inception, metric-source inception, first possible availability of all required derived dependencies))`.
2. Exclude only a proven leading prefix attributable to inception or legitimate initialization. Missing history, fetch truncation or later unavailable observations cannot move the first-countable boundary or justify skipping days.
3. Zero-close ATR_PCT is unavailable while otherwise eligible TR/ATR processing continues. Non-positive ATR_PCT denominators make VNM unavailable.
4. For current same-clock bucket `[s,e)`, select candidate references `[s-k UTC days,e-k UTC days)` for `k=1..30`. Never include the current bucket or search farther back to replace missing references.
5. Use exact median; persist selected bucket identities, UTC intervals, source coverage, cutoff, policies and configuration.
6. Preserve explicit 5m Wilder(14) seed/update, canonical predecessor and ancestry requirements, Q36 work values and percent-to-decimal conversion.
7. Preserve all eleven required inputs, completed 5m/15m/1h selection semantics, exact gate/veto inequalities, fixed weights and unavailable-data propagation. F-005 retains classification and handoff ownership.
8. Preserve centered-sign behavior, regime sensitivity, participation-versus-liquidity distinctions and unresolved empirical calibration.
