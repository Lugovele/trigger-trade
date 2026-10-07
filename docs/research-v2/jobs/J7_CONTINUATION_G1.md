# J7 J7_CONTINUATION_G1

Status: **SPECIFIED_NOT_IMPLEMENTED**. This job is specified only; it has not been implemented or run.

| Field | Value |
|---|---|
| Purpose | G1 stop comparison against J4 |
| Candidate | V2-02 / V2-04 |
| Exact profile | Same J4 signal and all parameters; only G0 stop -> G1 ATR-only stop |
| Signal | Same as J4 |
| Stop | G1 |
| Entry | Common profile |
| Sizing | 25% nominal margin |
| Leverage | 1 |
| Symbols | `["AVAXUSDT", "SUIUSDT", "PEPEUSDT"]` |
| Window | `{"end_exclusive": "2026-08-26T00:00:00Z", "start_inclusive": "2026-08-19T00:00:00Z"}` |
| Warmup | `{"warmup_days": 15}` |
| Dependencies | `["V2-02", "V2-04", "V2-03", "V2-01", "V2-07", "V2-08"]` |
| Differs from control | only G0 stop -> G1 ATR-only stop relative to J4 |
| Must remain equal | Same signal/profile as J4 and all non-stop parameters. |
| Expected metrics | `["actual_net_usdt", "filled_count", "accepted_count", "entry_notional_turnover", "fees", "funding", "MTM_DD", "stress_net", "leave_best_event_out_net", "DATA_INVALID"]` |
| Pass/fail source | common_profile.screen_gates and TriggerTrade_Research_V2_Economic_Redesign_RU.md 7D_SCREENING_PLAN |
