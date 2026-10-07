# J1 J1_TTL_CONTROL

Status: **SPECIFIED_NOT_IMPLEMENTED**. This job is specified only; it has not been implemented or run.

| Field | Value |
|---|---|
| Purpose | TTL-only control |
| Candidate | V2-01 TTL-only |
| Exact profile | J0 except entry TTL=15 minutes; all other rules unchanged |
| Signal | Legacy SET-R-003-V2 |
| Stop | Legacy |
| Entry | J0 except entry TTL=15 minutes |
| Sizing | approx 50 USDT actual tranche / 5% |
| Leverage | 1 |
| Symbols | `["AVAXUSDT", "SUIUSDT", "PEPEUSDT"]` |
| Window | `{"end_exclusive": "2026-08-26T00:00:00Z", "start_inclusive": "2026-08-19T00:00:00Z"}` |
| Warmup | `{"warmup_days": 15}` |
| Dependencies | `["V2-01"]` |
| Differs from control | entry TTL=15 minutes only |
| Must remain equal | All other J0 rules unchanged. |
| Expected metrics | `["actual_net_usdt", "filled_count", "accepted_count", "entry_notional_turnover", "fees", "funding", "MTM_DD", "stress_net", "leave_best_event_out_net", "DATA_INVALID"]` |
| Pass/fail source | common_profile.screen_gates and TriggerTrade_Research_V2_Economic_Redesign_RU.md 7D_SCREENING_PLAN |
