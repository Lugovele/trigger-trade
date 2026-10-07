# J4 J4_CONTINUATION_G0

Status: **SPECIFIED_NOT_IMPLEMENTED**. This job is specified only; it has not been implemented or run.

| Field | Value |
|---|---|
| Purpose | Momentum continuation quality test |
| Candidate | V2-04 |
| Exact profile | RET_OR + local trend + RVOL>=1.2; common G0 |
| Signal | RET_OR + local trend + RVOL>=1.2 |
| Stop | G0 |
| Entry | Common profile |
| Sizing | 25% nominal margin |
| Leverage | 1 |
| Symbols | `["AVAXUSDT", "SUIUSDT", "PEPEUSDT"]` |
| Window | `{"end_exclusive": "2026-08-26T00:00:00Z", "start_inclusive": "2026-08-19T00:00:00Z"}` |
| Warmup | `{"warmup_days": 15}` |
| Dependencies | `["V2-04", "V2-03", "V2-01", "V2-02", "V2-07", "V2-08"]` |
| Differs from control | continuation filters |
| Must remain equal | G0 scaffold, 1x, symbols/window. |
| Expected metrics | `["actual_net_usdt", "filled_count", "accepted_count", "entry_notional_turnover", "fees", "funding", "MTM_DD", "stress_net", "leave_best_event_out_net", "DATA_INVALID"]` |
| Pass/fail source | common_profile.screen_gates and TriggerTrade_Research_V2_Economic_Redesign_RU.md 7D_SCREENING_PLAN |
