# Rules Backend Contract Analysis

Status: READ_ONLY_RECONCILED_PACKAGE

## Confirmed Contract

TriggerTrade intentionally versions Position-owned and Portfolio-owned Rules fields together as one immutable `TradingRulesVersion`.

The previous separate `POS-R-*` and `PR-R-*` registry interpretation is rejected for this product. Those IDs remain source component provenance inside a combined package.

## PostgreSQL Path

`PostgresResearchConfigurationRegistry.put_trading_rules_version` persists combined `TradingRulesVersion` payloads through owner-state records. The path is real and PostgreSQL-backed.

Classification:

`POSTGRES_RULES_IMPORT_PATH: POSTGRES_IMPORT_READY`

It is not `SQLITE_ONLY`, because PostgreSQL can persist combined `TradingRulesVersion` records. It is now `POSTGRES_IMPORT_READY` for the corrected Research V1 package because the current draft schema can source-faithfully represent the 16 combined versions.

The final constructor check against the actual current `TradingRulesVersionDraft` and `validate_rules_draft` returns `BACKEND_VALID=16/16`. Source-faithful dynamic TP no longer requires a fabricated positive `minimum_take_profit_pct`.

## Current Backend Fields

`TradingRulesVersionDraft` has:

- `position_size_pct`
- `take_profit_mode`
- `fixed_take_profit_pct`
- `minimum_take_profit_pct`
- `stop_loss_pct`
- `minimum_risk_reward`
- `minimum_net_edge_enabled`
- `minimum_net_edge_pct`
- `leverage`
- `max_capital_in_positions_pct`
- `max_open_positions_enabled`
- `max_open_positions`
- `max_positions_per_coin_enabled`
- `max_positions_per_coin`
- `direction_mode`
- `daily_loss_limit_enabled`
- `daily_loss_limit_pct`
- fee/cost/funding fields
- `coins`
- `metadata`

## Contract Gaps After Correction

No methodology-owned TradingRulesVersion backend gaps remain for the corrected Research V1 package.

- `max_positions_per_coin`: validator now accepts methodology-owned 2/3 tranche-slot values, constrained by enabled `max_open_positions`.
- `minimum_tranche_capital`: first-class nullable Portfolio Rules field.
- `cooldown_minutes`: first-class nullable Portfolio Rules field.
- `stop_loss.mode`: first-class Position Rules mode.
- Dynamic TP: DYNAMIC mode validates without fabricated fixed minimum TP percentage.
- `minimum_risk_reward.enabled`: first-class Position Rules enabled flag with retained value.

Methodology-first reconciliation removes the following from the Rules blocker list:

- ATR construction bindings: owned by Position construction / certified formula references, preserved as provenance and not duplicated as TradingRulesVersion fields.
- Fee/cost/funding values: execution, backtest-profile and accounting evidence rather than immutable Rules constants.
- Asset labels/native symbols: launch-time instrument binding and Research universe metadata rather than Rules semantics.
