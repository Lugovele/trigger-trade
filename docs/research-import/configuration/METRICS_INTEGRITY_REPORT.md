# Metrics Integrity Report

## Scope

Audit target: canonical Trading Configuration Metrics layer.

Authoritative artifacts inspected:

- `docs/METRICS_LIBRARY_V1.md`
- `docs/metrics_library_v1.json`
- `src/triggertrade/dashboard/data/metrics_library_v1.json`
- `src/triggertrade/dashboard/metrics_library.py`
- Trading Configuration Metrics rendering in `src/triggertrade/dashboard/product_ui.py`

## Result

Metrics registry integrity: PASS.

| Check | Result |
|---|---:|
| Total objects | 47/47 |
| F-series | 16/16 |
| A-series | 9/9 |
| M-series | 8/8 |
| N-series | 8/8 |
| S-series | 6/6 |
| T-series entries | 0 |

## Targeted Semantic Checks

| Object | Expected source-faithful role | Current result |
|---|---|---|
| F-009 | Stop Calculation and Stop Rounding; certified trading formula | MATCH |
| F-010 | Dynamic Take Profit Selection and Rounding; certified trading formula | MATCH |
| F-016 | Attempt Cooldown Contribution; approved policy/system formula | MATCH |
| S-005 | Research-only market regime diagnostic classifier | MATCH |
| S-006 | NOT_A_FORMULA / ARCHITECTURE_RULE runtime path classification | MATCH |

## Defects

No Metrics semantic, backend, read-model, or UI projection defects found.

## Notes

The Metrics Library correctly remains a mixed library of formulas, policies,
research metrics, normalization rules, state rules, and architecture rules.
The UI does not convert every entry into a formula and preserves the approved
status/type taxonomy from the structured registry.
