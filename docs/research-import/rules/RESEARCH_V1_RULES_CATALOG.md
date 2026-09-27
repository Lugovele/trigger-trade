# TriggerTrade Research V1 Combined Rules Catalog

Status: READ_ONLY_RECONCILED_PACKAGE
Package revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
Backend contract: `TradingRulesVersion`

## Summary

Research V1 Rules are reconciled to the existing TriggerTrade backend decision that Position Rules and Portfolio Rules are delivered together as one immutable `TradingRulesVersion`.

Component source definitions remain visible:

| Component type | Count | IDs |
|---|---:|---|
| Position components | 12 | POS-R-001, POS-R-002, POS-R-003, POS-R-005, POS-R-006, POS-R-007, POS-R-008, POS-R-010, POS-R-011, POS-R-012, POS-R-013, POS-R-014 |
| Portfolio components | 5 | PR-R-201, PR-R-204, PR-R-205, PR-R-207, PR-R-208 |
| Combined TradingRulesVersion packages | 16 | `TRV-R-POS-*-PR-*` listed below |

The earlier separate-registry interpretation is rejected. It split source components along methodology ownership boundaries, but TriggerTrade intentionally versions those sections together as one `TradingRulesVersion`.

## Allocation

Operative allocation policy: `ALLOC-R-V1-FIXED-10X10`

| Segment | Coins | Total |
|---|---|---:|
| MAJORS | BTC 10%, ETH 10% | 20% |
| HIGH_VOLATILITY_HIGH_BETA | SOL 10%, XRP 10%, DOGE 10%, SUI 10%, PEPE 10%, AVAX 10% | 60% |
| DIVERSIFIERS | LINK 10%, BNB 10% | 20% |

Total allocation is exactly 100%. No dynamic allocation, reweighting, redistribution, or optimization is operative. Old `PR-R-101..109` and `PR-R-203` remain provenance only.

## Combined Versions

| Combined rules version | Position component | Portfolio component | Source usage |
|---|---|---|---|
| TRV-R-POS-001-PR-201 | POS-R-001 | PR-R-201 | Baseline and Set-only variants; 41 source arms |
| TRV-R-POS-001-PR-204 | POS-R-001 | PR-R-204 | R-024 variant |
| TRV-R-POS-001-PR-205 | POS-R-001 | PR-R-205 | R-025 variant |
| TRV-R-POS-001-PR-207 | POS-R-001 | PR-R-207 | R-027 variant |
| TRV-R-POS-001-PR-208 | POS-R-001 | PR-R-208 | R-028 variant |
| TRV-R-POS-002-PR-201 | POS-R-002 | PR-R-201 | R-012 variant |
| TRV-R-POS-003-PR-201 | POS-R-003 | PR-R-201 | R-013 variant, R-030 variant |
| TRV-R-POS-005-PR-201 | POS-R-005 | PR-R-201 | R-014 variant |
| TRV-R-POS-006-PR-201 | POS-R-006 | PR-R-201 | R-015 variant |
| TRV-R-POS-007-PR-201 | POS-R-007 | PR-R-201 | R-023 replacement variant |
| TRV-R-POS-008-PR-201 | POS-R-008 | PR-R-201 | R-016 variant |
| TRV-R-POS-010-PR-201 | POS-R-010 | PR-R-201 | R-017 variant |
| TRV-R-POS-011-PR-201 | POS-R-011 | PR-R-201 | R-018 variant |
| TRV-R-POS-012-PR-201 | POS-R-012 | PR-R-201 | R-019 variant |
| TRV-R-POS-013-PR-201 | POS-R-013 | PR-R-201 | R-020 variant |
| TRV-R-POS-014-PR-201 | POS-R-014 | PR-R-201 | R-021 variant |

These 16 packages are mechanically derived from `BASELINE_CONFIGURATION` and `VARIANT_CONFIGURATION` pairings in the final 30 hypotheses. No Cartesian product is introduced.

## Position Component Fields

| Field | Baseline value | Owner | Backend status |
|---|---|---|---|
| stop_loss.mode | DYNAMIC | POSITION | DIRECT_MATCH |
| stop_loss.fixed_pct | 1, ignored while DYNAMIC | POSITION | PARTIAL |
| take_profit.mode | DYNAMIC | POSITION | DIRECT_MATCH, but runtime unsupported for Research |
| take_profit.fixed_pct | null | POSITION | DIRECT_MATCH |
| minimum_risk_reward | enabled false, value 2 | POSITION | DIRECT_MATCH |
| minimum_net_edge | enabled false, pct 1 | POSITION | DIRECT_MATCH |
| leverage | 1 | POSITION | DIRECT_MATCH |

Position variants:

| Component | Change |
|---|---|
| POS-R-002 | `MIN_ENTRY_IMPROVEMENT_ATR` 0.25 |
| POS-R-003 | `MAX_ENTRY_DEVIATION_ATR` 2.00 |
| POS-R-005 | stop_loss.mode FIXED, fixed_pct 1 |
| POS-R-006 | `BUFFER_ATR_MULTIPLIER` 0.40 |
| POS-R-007 | `MIN_DISTANCE_ATR` 0.75; R-023 replacement |
| POS-R-008 | `MAX_DISTANCE_ATR` 1.50 |
| POS-R-010 | `MIN_TP_DISTANCE_ATR` 1.25 |
| POS-R-011 | `MAX_TP_DISTANCE_ATR` 3.00 |
| POS-R-012 | minimum_risk_reward enabled true, value 2 |
| POS-R-013 | minimum_net_edge enabled true, pct 1 |
| POS-R-014 | leverage 2 |

## Portfolio Component Fields

All five Portfolio components use `ALLOC-R-V1-FIXED-10X10`, ten 10% allocations, `max_capital_in_positions_pct=60`, `minimum_tranche_capital=25`, and `daily_loss_limit.pct=5`.

| Component | Max open | Max per coin | Daily loss enabled | Cooldown minutes | Derived from |
|---|---:|---:|---|---:|---|
| PR-R-201 | 6 | 2 | false | 5 | PR-R-101 |
| PR-R-204 | 3 | 2 | false | 5 | PR-R-104 |
| PR-R-205 | 6 | 3 | false | 5 | PR-R-105 |
| PR-R-207 | 6 | 2 | false | 15 | PR-R-107 |
| PR-R-208 | 6 | 2 | true | 5 | PR-R-108 |

## Set Relationships

All 33 Set versions resolve at the Research arm/configuration layer. A Set version is not always unique to one Rules version. `SET-R-001-V1` and `SET-R-BTC-001-V1` are reused by many Position/Portfolio variants; other Set-specific variants use `TRV-R-POS-001-PR-201`.

Resolved relationships: 33/33.

Pending external note: `PENDING_BTC_TRIGGER_VERSION_REBIND`. This affects later Set trigger references, not Rules definitions.

## Backend Readiness

`POSTGRES_RULES_IMPORT_PATH: POSTGRES_IMPORT_READY`

PostgreSQL can persist combined `TradingRulesVersion` records through the Research configuration registry. The existing `TradingRulesVersionDraft` now represents all 16 Research V1 combined packages without runtime semantic loss.

Corrected backend gaps:

- `max_positions_per_coin` values 2 and 3 are accepted as methodology-owned Portfolio tranche-slot values.
- `minimum_tranche_capital` is a first-class Portfolio Rules field.
- `cooldown_minutes` is a first-class Portfolio Rules field.
- `stop_loss.mode` DYNAMIC/FIXED is first-class Position Rules configuration.
- Dynamic TP no longer requires a fabricated `minimum_take_profit_pct`.
- `minimum_risk_reward.enabled` is first-class Position Rules configuration.

Non-Rules blockers removed by methodology-first reconciliation:

- Position ATR bindings remain preserved as Position construction / certified formula references.
- Fee/cost/funding fields remain launch, execution, backtest-profile and accounting evidence.
- Asset labels remain Research universe metadata and launch-time instrument bindings.

`RESEARCH_V1_RULES_WEB_IMPORT.json` is created for import review. Production import remains intentionally unrun.
