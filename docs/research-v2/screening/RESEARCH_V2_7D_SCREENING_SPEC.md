# Research V2 7D Screening Spec

Status: **SPECIFIED_NOT_IMPLEMENTED**.

- 7D is fast economic screening.
- 30D confirmation is only for promising candidates.
- 90D is out of scope for now.
- First window: `2026-08-19T00:00:00Z` inclusive to `2026-08-26T00:00:00Z` exclusive.
- Research arms are isolated.
- Full calendar stream is required; do not reuse old MATCHED-only cohorts for V2 signal generation.
- Open positions are marked to market at the end window with estimated exit fees.
- Pending orders are cancelled at boundary.
- Post-window fills/PnL are not counted as 7D.
- Funding facts are required.
- Do not silently convert DATA_INVALID to zero PnL.

## Gates

| Field | Value |
|---|---|
| status | SPECIFIED_NOT_IMPLEMENTED |
| source | common_profile.screen_gates plus redesign report 7D_SCREENING_PLAN |
| main_economic_pass_threshold_usdt | 46.666666666666664 |
| stretch_threshold_usdt | 70.0 |
| dynamic_minimum_fills_formula | ceil(46.6666666667/(mean_actual_notional*0.006666666666667)); this is an economic envelope, not statistical power |
| pf_required_formula | 1 + 46.6666666667 / abs(sum of net losses), when all PnL closed; do not interpret infinite PF with no losses as proof |
| risk_constraints | `{"gross_notional_fraction_max": 1.8, "portfolio_open_and_pending_stop_risk_fraction_max": 0.015, "risk_per_trade_fraction_max": 0.0075, "screen_drawdown_fraction_max": 0.06, "total_margin_fraction_max": 0.6}` |
| stress_net_condition | stress net > 0 |
| leave_best_event_out_condition | leave-best-event-out net > 0 |
| data_invalid_conditions | `["missing funding", "timeline violations", "ambiguous config/units", "unfinished data censor", "unmodeled leverage liquidation"]` |
| near_zero_handling | full-profile net <=0 => reject this configuration on this window; positive but below economic threshold => no 30D unless frozen plausible scaling is validated in canonical replay |
| confirmation30_advancement_rule | 30D confirmation only for promising candidates after 7D screen and holdout; no 90D in current program. |
| robustness | leave-best-event-out net > 0; stress net > 0; no absent funding, timeline violations, unfinished data censor, or unmodeled leverage liquidation; risk gates satisfied |
| confidence | PASS is economic screening only; no claim of stable monthly return or independence |
