# J0 J0_LEGACY_CONTROL

Status: **SPECIFIED_NOT_IMPLEMENTED**. This job is specified only; it has not been implemented or run.

| Field | Value |
|---|---|
| Purpose | Legacy control |
| Candidate | CONTROL |
| Exact profile | SET-R-003-V2 + POS001/PR201; 50 USDT actual tranche, 1x; old GTC |
| Signal | Legacy SET-R-003-V2 |
| Stop | Legacy |
| Entry | Legacy geometry/GTC |
| Sizing | approx 50 USDT actual tranche / 5% |
| Leverage | 1 |
| Symbols | `["AVAXUSDT", "SUIUSDT", "PEPEUSDT"]` |
| Window | `{"end_exclusive": "2026-08-26T00:00:00Z", "start_inclusive": "2026-08-19T00:00:00Z"}` |
| Warmup | `{"warmup_days": 15}` |
| Dependencies | `[]` |
| Differs from control | N/A |
| Must remain equal | Source window, symbols, legacy POS001/PR201, 1x, old GTC. |
| Expected metrics | `["actual_net_usdt", "filled_count", "accepted_count", "entry_notional_turnover", "fees", "funding", "MTM_DD", "stress_net", "leave_best_event_out_net", "DATA_INVALID"]` |
| Pass/fail source | common_profile.screen_gates and TriggerTrade_Research_V2_Economic_Redesign_RU.md 7D_SCREENING_PLAN |
