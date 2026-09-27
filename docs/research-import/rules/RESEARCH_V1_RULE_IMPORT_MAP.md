# Research V1 Combined Rules Import Map

Status: READ_ONLY_RECONCILED_PACKAGE

## Backend Shape

The import shape is the existing combined `TradingRulesVersion`, not independent Position and Portfolio registries.

Current backend fields come from `TradingRulesVersionDraft`:

- Position section: `position_size_pct`, `take_profit_mode`, `fixed_take_profit_pct`, `minimum_take_profit_pct`, `stop_loss_pct`, `minimum_risk_reward`, `minimum_net_edge_enabled`, `minimum_net_edge_pct`, `leverage`.
- Portfolio section: `max_capital_in_positions_pct`, `max_open_positions_enabled`, `max_open_positions`, `max_positions_per_coin_enabled`, `max_positions_per_coin`, `direction_mode`, `daily_loss_limit_enabled`, `daily_loss_limit_pct`, `coins`.
- Backend-required cost fields: `maker_fee_rate`, `taker_fee_rate`, `spread_cost`, `slippage_cost`, `funding_cost`. Methodology-first reconciliation classifies these as execution/backtest/accounting evidence, not Rules-owned fields.

## Field Reconciliation

| Research field | Owner | Backend field | Classification | Notes |
|---|---|---|---|---|
| Position component ID | RESEARCH_ONLY_METADATA | `metadata` only | SOURCE_METADATA_ONLY | Must not become an independent registry key. |
| Portfolio component ID | RESEARCH_ONLY_METADATA | `metadata` only | SOURCE_METADATA_ONLY | Must not become an independent registry key. |
| Combined package ID | RESEARCH_ONLY_METADATA | `rules_version_id` | DIRECT_MATCH | Use combined immutable `TradingRulesVersion` identity. |
| stop_loss.mode | POSITION | `stop_loss_mode` | DIRECT_MATCH | Backend supports FIXED and DYNAMIC. |
| stop_loss.fixed_pct | POSITION | `stop_loss_pct` | DIRECT_MATCH | Required only for FIXED mode; retained/ignored when DYNAMIC if present. |
| take_profit.mode | POSITION | `take_profit_mode` | DIRECT_MATCH | Backend model supports FIXED and DYNAMIC; DYNAMIC no longer requires fabricated fixed TP floor. |
| take_profit.fixed_pct | POSITION | `fixed_take_profit_pct` | DIRECT_MATCH | Source null can map to null. |
| ATR construction bindings | POSITION | formula/construction reference | OWNED_BY_OTHER_COMPONENT | Preserved as Dynamic Entry/Stop/TP certified formula inputs and provenance; not flattened into the Rules import payload. |
| minimum_risk_reward.enabled | POSITION | `minimum_risk_reward_enabled` | DIRECT_MATCH | Frozen Position methodology makes enabled/disabled state operative. |
| minimum_risk_reward.value | POSITION | `minimum_risk_reward` | REPRESENTABLE_BY_EXISTING_FIELD | Value 2 maps when rule is operative. |
| minimum_net_edge.enabled | POSITION | `minimum_net_edge_enabled` | DIRECT_MATCH | Exact. |
| minimum_net_edge.pct | POSITION | `minimum_net_edge_pct` | DIRECT_MATCH | Exact after percent conversion. |
| leverage.value | POSITION | `leverage` | DIRECT_MATCH | Exact. |
| max_capital_in_positions_pct | PORTFOLIO | `max_capital_in_positions_pct` | DIRECT_MATCH | Percent string converts to fraction. |
| max_open_positions | PORTFOLIO | `max_open_positions` | DIRECT_MATCH | Exact. |
| max_positions_per_coin | PORTFOLIO | `max_positions_per_coin` | DIRECT_MATCH | Validation accepts Research values 2/3 under tranche-slot semantics. |
| minimum_tranche_capital | PORTFOLIO | `minimum_tranche_capital` | DIRECT_MATCH | Frozen methodology says this is Portfolio Rules config. |
| daily_loss_limit.enabled | PORTFOLIO | `daily_loss_limit_enabled` | DIRECT_MATCH | Exact. |
| daily_loss_limit.pct | PORTFOLIO | `daily_loss_limit_pct` | DIRECT_MATCH | Exact after percent conversion. |
| cooldown_minutes | PORTFOLIO | `cooldown_minutes` | DIRECT_MATCH | Frozen methodology says this is Portfolio Rules config. |
| allocation vector | PORTFOLIO | `coins[].max_allocation_pct` | REPRESENTABLE_BY_EXISTING_FIELD | Requires launch instrument/catalog binding. |
| asset labels/native symbols | LAUNCH_BINDING | `coins[].symbol` after binding | LAUNCH_TIME_BINDING | Research labels stay separate from launch-time venue symbol binding. |
| fees/cost/funding | EXECUTION/ACCOUNTING | fee/cost fields | EXECUTION_EVIDENCE | Research V1 does not authorize universal immutable Rules constants. |

## Combined Version Population

The package contains 16 operative combined versions. They come from actual source arm pairings and are listed in `RESEARCH_V1_RULES.json`.

`RESEARCH_V1_RULES_WEB_IMPORT.json` is created. All 16 combined records validate through the backend model without dropping methodology-owned Rules fields or inventing unsupported TP/min-R:R values.
