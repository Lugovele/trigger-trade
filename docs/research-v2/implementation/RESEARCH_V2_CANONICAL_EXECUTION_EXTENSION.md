# Research V2 Canonical Execution Extension

Status: IMPLEMENTED_FOR_J0_J7_CONTRACT_FIXTURE

Research V2 enters the existing canonical downstream path through:

`Canonical Set Resolution -> MARKET_HANDOFF -> Position -> Portfolio Grant -> Position Construction -> Order Spec -> Lifecycle`

The extension keeps legacy `ORDER_SPEC` contract version 5 readable and behaviorally unchanged. Research V2 uses an in-memory versioned `ORDER_SPEC` contract version 6 for fields that version 5 cannot represent exactly.

## Versioning

- Legacy Order Spec: `ORDER_SPEC` contract version 5.
- Research V2 Order Spec: `ORDER_SPEC` contract version 6.
- Database migration: not required.

Version 5 has no order validity field and remains GTC by default. Version 6 adds canonical entry validity with `GTC` or `TTL`.

## Contract Map

| V2 requirement | Canonical field | Version | Enforcement | Evidence/output | Backward compatibility |
| --- | --- | --- | --- | --- | --- |
| POST_ONLY limit entry | `order_spec.entry.order_type`, `post_only` | v6 | Order Spec validation, lifecycle post-only model | `entry` | v5 unchanged |
| TTL/validity | `order_spec.entry.validity` | v6 | BACKTEST lifecycle entry fill window | lifecycle `ENTRY_ORDER_EXPIRED_UNFILLED` | v5 absent means GTC |
| No chase/reprice/market fallback | `entry.validity.chase/reprice/market_fallback=false` | v6 | Order Spec validation | `entry.validity` | v5 unchanged |
| G0 hybrid structural stop | `stop_loss.mode=HYBRID_STRUCTURAL`, final stop price | v6 | V2 construction bridge | `stop_loss`, `economics.risk_distance` | v5 unchanged |
| G1 ATR-only stop | `stop_loss.mode=ATR_ONLY`, final stop price | v6 | V2 construction bridge | `stop_loss`, `economics.risk_distance` | v5 unchanged |
| TP 2R | `take_profit.mode=R_MULTIPLE`, `r_multiple=2` | v6 | V2 construction bridge | `take_profit`, `economics.gross_r` | v5 unchanged |
| Net TP floor | `economics.planned_conditional_net_tp_fraction`, `net_tp_floor_result` | v6 | V2 construction bridge | `economics` | v5 unchanged |
| Risk-based sizing | `economics.actual_order_notional`, `actual_committed_margin`, `actual_stop_risk` | v6 | V2 construction bridge | `economics` | v5 unchanged |
| Per-trade risk cap | V2 sizing profile plus post-rounding recheck | v6 | V2 construction bridge | sizing rejection reason | v5 unchanged |
| Total margin cap | `V2PortfolioExposureState` and `V2PortfolioGrant` | v6 bridge | V2 portfolio grant | grant reason code | v5 unchanged |
| Per-coin margin cap | `V2PortfolioExposureState` and `V2PortfolioGrant` | v6 bridge | V2 portfolio grant | grant reason code | v5 unchanged |
| Gross notional cap | `V2PortfolioExposureState` and `V2PortfolioGrant` | v6 bridge | V2 portfolio grant | grant reason code | v5 unchanged |
| Total stop-risk cap | `V2PortfolioExposureState` and `V2PortfolioGrant` | v6 bridge | V2 portfolio grant | grant reason code | v5 unchanged |
| Pending-inclusive slots | `open_pending_count`, `coin_open_pending_count` | v6 bridge | V2 portfolio grant | grant reason code | v5 unchanged |
| Venue-rounding revalidation | post-rounding economics fields | v6 | V2 construction bridge | sizing rejection reason | v5 unchanged |
| Execution profile identity | `provenance.research_v2_execution_profile_fingerprint` | v6 | V2 construction bridge | `provenance`, `economics` | Set identity unchanged |

## Enforcement Locations

- `src/triggertrade/research_v2_execution.py`
  - immutable Research V2 execution profile bridge;
  - V2 portfolio grant checks;
  - risk-based sizing and post-rounding revalidation;
  - G0/G1 stop construction;
  - TP 2R and net-TP floor;
  - `ORDER_SPEC` v6 validation.
- `src/triggertrade/order_specs.py`
  - preserves v5 parse path first;
  - accepts v6 through the V2 validator only after v5 parse failure.
- `src/triggertrade/services/research_backtest_execution.py`
  - lifecycle consumes canonical `entry.validity`;
  - absent validity remains legacy GTC.

## Backward Compatibility

The approved v5 wire contract is not mutated. Legacy parsing uses the existing `parse_contract("ORDER_SPEC", ...)` path first, so existing v5 hashes and behavior remain governed by the old schema. Version 6 is accepted as a separate in-memory contract shape and is not persisted through a schema migration.

