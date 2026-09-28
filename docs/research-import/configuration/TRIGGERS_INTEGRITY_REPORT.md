# Triggers Integrity Report

## Scope

Audit target: Trading Configuration -> Signal Logic -> Triggers.

Authoritative artifacts inspected:

- `docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`
- `docs/research-import/triggers/RESEARCH_V1_TRIGGERS.json`
- `src/triggertrade/dashboard/research_triggers.py`
- Trading Configuration Trigger rendering in `src/triggertrade/dashboard/product_ui.py`

## Result

Trigger source and read-model integrity: PASS.

| Check | Result |
|---|---:|
| Current imported-style trigger definitions | 31/31 |
| Current/historical version classification | PASS |
| BTC corrected current versions | 4/4 |
| Stale BTC 1.0.0 current-version usage | 0 |
| Mutation path added | NO |

## Targeted Semantic Checks

| Trigger | Required distinction | Result |
|---|---|---|
| TR-R-001 | F-001 trigger_result = TRUE, `theta_move_pct = 0.50`, CURRENT_STATE | MATCH |
| TR-R-002 | F-001 trigger_result = TRUE, `theta_move_pct = 1.00`, CURRENT_STATE | MATCH |
| TR-R-029 | F-001 trigger_result = FALSE, `theta_move_pct = 0.50`, CURRENT_STATE | MATCH |
| TR-R-030 | F-001 trigger_result = FALSE, `theta_move_pct = 1.00`, CURRENT_STATE | MATCH |
| TR-R-004 | classifier LONG, CURRENT_STATE | MATCH |
| TR-R-005 | classifier SHORT, CURRENT_STATE | MATCH |
| TR-R-015 | classifier LONG, FRESH_EVENT | MATCH |
| TR-R-016 | classifier SHORT, FRESH_EVENT | MATCH |
| TR-R-BTC-001@1.0.1 | RETURN(BTC,5m) > 0, CURRENT_STATE, LONG/ZERO/UNAVAILABLE | MATCH |
| TR-R-BTC-002@1.0.1 | RETURN(BTC,5m) < 0, CURRENT_STATE, SHORT/ZERO/UNAVAILABLE | MATCH |
| TR-R-BTC-003@1.0.1 | RETURN(BTC,5m) > 0, FRESH_EVENT, LONG/ZERO/UNAVAILABLE | MATCH |
| TR-R-BTC-004@1.0.1 | RETURN(BTC,5m) < 0, FRESH_EVENT, SHORT/ZERO/UNAVAILABLE | MATCH |
| TR-R-BTC-005 | DE >= 0.30 | MATCH |
| TR-R-BTC-006 | ATR percentile >= 15 | MATCH |
| TR-R-BTC-007 | ATR percentile <= 97 | MATCH |
| TR-R-BTC-008 | TOD_REL_TURNOVER >= 0.70 | MATCH |

## Corrected Defect

| Classification | Object | Defect | Correction |
|---|---|---|---|
| DISPLAY_SEMANTIC_LOSS | Trigger list UI | The list rendered condition/output but not existing authoritative parameters or evaluation semantics, making valid trigger pairs appear indistinguishable. | Added table columns for Parameters and Evaluation, and exposed Evaluation Semantics in detail from the backend read model. |

## Remaining Defects

No Trigger semantic, backend, read-model, or UI projection defects remain in the audited source-backed path.
