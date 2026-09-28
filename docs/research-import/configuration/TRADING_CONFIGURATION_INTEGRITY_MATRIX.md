# Trading Configuration Integrity Matrix

## Summary

Audit scope: Metrics -> Triggers -> Sets -> Trading Rules.

Frozen methodology v1.2.15 and certified/final corrected source artifacts were
treated as authoritative over backend and UI presentation.

| Layer | Verified | Defects corrected | Defects remaining |
|---|---:|---:|---:|
| Metrics | 47/47 | 0 | 0 |
| Triggers | 31/31 | 1 | 0 |
| Sets | 33/33 | 1 | 0 |
| Trading Rules | 16/16 | 0 | 0 |

## Matrix

| Layer | Object ID | Version | Source-authoritative semantics | Current backend semantics | Current UI semantics | Classification | Severity | Exact correction | Corrected |
|---|---|---|---|---|---|---|---|---|---|
| Metrics | ALL | n/a | 47 mixed formula/policy/metric/normalization/state/architecture objects | 47 structured records from packaged registry | 47 Trading Configuration rows and detail content | MATCH | n/a | None | n/a |
| Triggers | TR-R-001 / TR-R-002 / TR-R-029 / TR-R-030 | 1.0.0 | F-001 predicates differ by `theta_move_pct` 0.50 vs 1.00 | Parameters preserved in raw definition/read model | Parameters now visible in Trigger list/detail | DISPLAY_SEMANTIC_LOSS | MEDIUM | Expose Parameters column and detail section | YES |
| Triggers | TR-R-004 / TR-R-005 / TR-R-015 / TR-R-016 | 1.0.0 | CURRENT_STATE classifier predicates differ from FRESH_EVENT predicates | Freshness semantics preserved in raw definition/read model | Evaluation semantics now visible in Trigger list/detail | DISPLAY_SEMANTIC_LOSS | MEDIUM | Expose Evaluation column and detail section | YES |
| Triggers | TR-R-BTC-001..004 | 1.0.1 | Corrected BTC branches return LONG/SHORT, ZERO, UNAVAILABLE with CURRENT_STATE/FRESH_EVENT distinction | Current versions project as 1.0.1 with corrected outputs | Current versions, outputs, parameters, and evaluation semantics visible | MATCH | n/a | None beyond Trigger presentation correction above | YES |
| Sets | Non-BTC classifier-driven Sets | V1/V2 as applicable | Final side equals same current classifier side; not a runtime NONE result | Direction semantics preserved in Set record | Compact direction no longer collapses to `NONE`; detail shows full source semantics | READ_MODEL_PROJECTION_DEFECT | MEDIUM | Project compact direction as `CLASSIFIER SIDE` | YES |
| Sets | Affected BTC Set versions | listed in Set report | Corrected BTC trigger references use 1.0.1; no superseded 1.0.0 references | 16/16 affected Sets reference corrected versions | Trigger memberships visible in Set detail | MATCH | n/a | None | n/a |
| Sets | BTC `TR-R-BTC-001..004@1.0.1` member snapshots | 1.0.1 | Copied Set member predicate metadata must match the exact referenced Trigger version | 34/34 BTC `1.0.1` member snapshots regenerated from Trigger source | Detail/read model now exposes corrected member output states through Set membership | STALE_EMBEDDED_TRIGGER_METADATA | HIGH | Regenerate copied BTC member fields and affected semantic hashes | YES |
| Trading Rules | 16 combined versions | source package | Combined TradingRulesVersion owns Position Rules, Portfolio Rules, and Coins together | 16/16 web import records validate against backend constructor tests | Single Trading Rules page preserves columns, Save New Rules, and History | MATCH | n/a | None | n/a |

## Cross-Layer Integrity

| Edge | Result |
|---|---:|
| Metrics/formula IDs referenced by Triggers | Resolved where canonical formula IDs are used |
| Trigger versions referenced by Sets | 242/242 |
| Affected BTC Sets referencing superseded BTC 1.0.0 versions | 0 |
| BTC 1.0.1 Set member snapshots matching referenced Trigger versions | 34/34 |
| Set -> combined TradingRulesVersion relationships | 33/33 resolved by Rules reconciliation package |
| Versionless `latest` references introduced | 0 |
| Production data mutations | 0 |

## Remaining Work Outside This Task

Research-specific combined Rules versions are source/backend valid but were not
imported to production in this task, by instruction. No production data was
mutated.
