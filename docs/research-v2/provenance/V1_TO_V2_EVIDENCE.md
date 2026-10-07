# V1 to V2 Evidence

Status: **EVIDENCE_PROVENANCE**. This file summarizes source-supported evidence only; it is not a new trading rule.

- Corrected V1 records: 1016 cell executions.
- Requested/executed rules matched: 1016 / 1016.
- Certified Set identity matched: 1016 / 1016.
- Unique certified sets: 378.
- Unique execution contexts: 1016.
- Unique portfolio contexts: 36.
- Distinct rules/configs: 16.
- 32 distinct market events are reported in the source redesign; do not sum overlapping arms as one wallet.
- Baseline utilization source: R005 reconstructed saved accepted orders; assumed evaluation 2026-07-20T00:00Z to 2026-08-19T00:00Z; diagnostic not certification
- Baseline filled trade count: 4.
- Average actual tranche/capital: 49.99942387725 USDT.
- Baseline net: -0.06660337062614993 USDT; net_per_notional: -0.00033302069034666824.
- Main rejection reasons preserved from source: STOP_SL_TOO_WIDE, TAKE_PROFIT_TARGET_TOO_FAR, ENTRY_ATR_DISTANCE_OUT_OF_RANGE, MINIMUM_RR_FAIL, TAKE_PROFIT_NO_ELIGIBLE_REFERENCE.
- Stop geometry matters: fixed 1% stop increased approvals in source evidence, but profitability was not proven.
- Leverage alone does not create edge: 2x multiplied the current negative unit edge in V1 evidence.
- Some config IDs share exported numeric drafts; do not collapse them without implementation fingerprints.

## Evidence Files

- checks.json: `{"csv_match": 1016, "csv_rows": 1016, "ids_match": 1016, "pnl_identity": 120, "records": 1016, "rules_match": 1016, "unique_certified_sets": 378, "unique_configs": 16, "unique_contexts": 1016, "unique_portfolios": 36}`
- utilization.json: `{"average_capital": 49.99942387725, "basis": "R005 reconstructed saved accepted orders; assumed evaluation 2026-07-20T00:00Z to 2026-08-19T00:00Z; diagnostic not certification", "entry_notional_turnover": 199.997695509, "fill_wait_minutes": [["E10", 0.9999999833333334], ["E27", 9.999999983333334], ["E28", 26.999999983333332], ["E29", 6597.9999999833335]], "filled_capital_utilization": 0.00010995231646409723, "filled_total_minutes": 95.0, "filled_trade_count": 4, "net": -0.06660337062614993, "net_per_notional": -0.00033302069034666824, "peak_reserved_usdt": 99.99955307100001, "reserved_capital_utilization": 0.05048074800728583}`
- witnesses.json keys: `['source', 'witness_records', 'eight_equal_exported_numeric_configs']`
- CSV summaries: `{"arms_metrics.csv": {"columns": ["research_id", "arm", "cell", "configs", "records", "events", "approve", "portfolio_block", "accepted", "filled", "closed", "censored", "not_filled", "tp", "sl", "net", "gross", "fees", "expectancy", "winrate", "pf", "avgcapital", "rejects"], "rows": 36}, "unique_closed.csv": {"columns": ["event_id", "symbol", "direction", "observed_at", "status", "entry", "stop", "tp", "quantity", "capital", "notional", "leverage", "submitted_at", "filled_at", "closed_at", "reason", "gross", "fees", "funding", "net", "copies", "research_arms"], "rows": 14}}`
