# Formula / Metric Inventory and Backend Implementation Gate Catalog

Status: CANONICAL BACKEND IMPLEMENTATION GATE
Scope: inventory, classification, and implementation gating only
Methodology baseline: approved `docs/trading-methodology/` package

This catalog does not approve formula correctness, change thresholds, or modify
trading semantics. It records what the backend may implement now, what must
remain structural only, and what requires separate formula or research review.

Archived methodology under `docs/archive/trading-methodology-pre-v1.2.14/` is
not used as normative authority.

## Classification Model

Certification Status values:

- `CERTIFICATION_REQUIRED`: final calculation semantics must not be implemented
  until separately reviewed and approved.
- `APPROVED_AS_DEFINED`: approved methodology defines the calculation or rule
  sufficiently for backend implementation.
- `RESEARCH_PARAMETER`: mechanics may be implemented, but values remain
  configurable research/calibration inputs.
- `REVIEW_NEEDED`: evidence is insufficient to permit final implementation.
- `NOT_APPLICABLE`: no formula or metric certification gate applies.

Backend Gate values:

- `IMPLEMENT_ALLOWED`: backend may implement the approved calculation exactly.
- `IMPLEMENT_STRUCTURE_ONLY`: backend may implement contracts, interfaces,
  state, persistence, orchestration, version pins, and integration boundaries,
  but not final calculation logic.
- `BLOCK_FINAL_IMPLEMENTATION`: backend must not implement final calculation
  logic until the item is certified or reclassified.
- `PARAMETERIZE_ONLY`: backend may implement configurable mechanics, but must
  not freeze research values as canonical truth.
- `NOT_APPLICABLE`: no formula-specific implementation gate applies.

## Master Catalog

| ID | Entity | Owner | Type | Canonical Definition | Current Implementation | Certification Status | Backend Gate | Formula Family | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | Price-move trigger calculation | Set | TRADING_FORMULA | `docs/trading-methodology/methodology/SET.md` :: trigger/setup conditions | `src/triggertrade/triggers/percentage_price_move.py::PercentagePriceMoveTrigger.evaluate` LEGACY/DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | TRIGGER | Current code computes percentage move, but canonical Set trigger semantics must be certified before final backend implementation. |
| F-002 | Volume confirmation calculation | Set | TRADING_FORMULA | `docs/trading-methodology/methodology/SET.md` :: volume/setup confirmation | `src/triggertrade/triggers/volume_confirmation.py::{median_decimal, empirical_percentile_rank, RobustVolumeConfirmationTrigger.evaluate}` LEGACY/DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | TRIGGER | Current code contains median and percentile mechanics; canonical use requires formula certification. |
| F-003 | Set ATR and true-range calculation | Set | TRADING_FORMULA | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` :: §3 Wilder ATR(14) Canonicalization | NONE | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | SET_ANALYTICS | Numeric policy defines arithmetic mechanics, but Set formula integration is still formula-gated by traceability. |
| F-004 | Set normalization, percentile, and score calculation | Set | TRADING_FORMULA | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` :: §2 Canonical Set Value Representation and `docs/trading-methodology/methodology/SET.md` :: Set analytics | `src/triggertrade/triggers/volume_confirmation.py::empirical_percentile_rank` LEGACY/DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | MARKET_NORMALIZATION | Do not promote demo percentile or score behavior as canonical without certification. |
| F-005 | Set direction classifier and LONG/SHORT handoff | Set | TRADING_FORMULA | `docs/trading-methodology/methodology/SET.md` :: Set outcome and direction handoff | `src/triggertrade/services/futures_runtime.py::_direction_skip_reason` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | LONG_SHORT | Direction is trading-critical and feeds Position Rules. |
| F-006 | Position Rules LONG formula | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: §37 Mathematical Formula - LONG | NONE | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | LONG_SHORT | Includes entry, stop candidate, ATR-risk checks, and tick rounding for LONG. |
| F-007 | Position Rules SHORT formula | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: §38 Mathematical Formula - SHORT | NONE | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | LONG_SHORT | Includes entry, stop candidate, ATR-risk checks, and tick rounding for SHORT. |
| F-008 | Planned entry reference selection | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Position construction and canonical Set value consumption | `src/triggertrade/services/futures_runtime.py::_intent_price` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | ENTRY | Current runtime derives demo intent price; target entry semantics are not yet certified for backend final logic. |
| F-009 | Stop calculation and stop rounding | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: §37, §38, and Part V Tick-size alignment | `src/triggertrade/execution/position_lifecycle.py::build_fixed_protective_exit_plan` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | STOP | Stop behavior is trading-critical and must remain blocked until formula certification. |
| F-010 | Dynamic Take Profit selection and rounding | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Part IV Dynamic Take Profit and §45-§46 algorithms | NONE | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | DYNAMIC_TAKE | Includes favorable-side eligibility, priority, distance ranking, ATR constraints, and tick rounding. |
| F-011 | Position size, quantity, and actual notional construction | Position Rules | TRADING_FORMULA | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §4 Position Final Construction and `docs/trading-methodology/methodology/POSITION_RULES.md` :: Appendix D | `src/triggertrade/execution/position_lifecycle.py::calculate_position_size` DEMO_ONLY; `src/triggertrade/services/futures_runtime.py::_intent_quantity` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | POSITION_SIZING | Numeric mechanics are defined, but final Position Rules sizing semantics remain formula-gated. |
| F-012 | Risk/reward and minimum net edge calculation | Position Rules | TRADING_FORMULA | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Part V Minimum R:R and minimum net edge invariants | `src/triggertrade/execution/position_lifecycle.py::evaluate_risk_reward` DEMO_ONLY; `src/triggertrade/execution/futures.py::{estimate_costs, estimate_net_edge}` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | RISK_REWARD | Backend may carry fields and contracts, but final edge/risk math needs certification. |
| F-013 | Set pending invalidation and stale-signal eligibility | Set | SYSTEM_FORMULA | `docs/trading-methodology/methodology/SET.md` :: Set lifecycle and pending invalidation | `src/triggertrade/services/futures_runtime.py::_rule_evaluation_snapshot` DEMO_ONLY | REVIEW_NEEDED | IMPLEMENT_STRUCTURE_ONLY | SET_ANALYTICS | Implement state boundaries only until the exact canonical calculation boundary is reviewed. |
| F-014 | Portfolio free-capital and grant calculation | Portfolio Rules | SYSTEM_FORMULA | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §3 Portfolio Grant and Atomic Capacity Gates | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | CAPITAL_ALLOCATION | Backend may implement exactly specified free-capital flooring, equal split request, and capacity gates. |
| F-015 | Actual committed capital from final quantity | Portfolio Rules | SYSTEM_FORMULA | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §4 Position Final Construction | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | CAPITAL_ALLOCATION | Backend may implement committed capital arithmetic exactly as specified. |
| F-016 | Attempt-scoped cooldown contribution and effective symbol cooldown | Portfolio Rules | SYSTEM_FORMULA | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` :: §24, §25, §26, Appendix A, and Appendix G | `src/triggertrade/execution/futures.py::FuturesRiskManager.evaluate` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | PORTFOLIO_LIMITS | Cooldown contribution is `entry_accepted_at + pinned_cooldown_duration`; effective symbol cooldown is the maximum surviving contribution. Requires durable attempt lineage before implementation. |
| A-001 | Gross PnL calculation | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: Financial factual response and lifecycle attribution | `src/triggertrade/accounting/futures.py::gross_pnl` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | PNL | Directional gross PnL mechanics are safe when implemented against approved lifecycle facts. |
| A-002 | Net final result calculation | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: Financial factual response; `docs/BACKEND_IMPLEMENTATION_TRACEABILITY.md` :: Formula Parallelization Map, Accounting final result | `src/triggertrade/accounting/futures.py::close_futures_trade` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | PNL | Traceability marks accounting final result as formula-gated. |
| A-003 | Fee cashflow calculation and attribution | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Fee/funding/realized cash postings | `src/triggertrade/backtest/simulator.py::BacktestFuturesSimulator.simulate_closed_trade` RESEARCH/DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | FEES_COSTS | Fee postings are implementable as factual cashflows; research fee assumptions remain parameters. |
| A-004 | Funding calculation and allocation | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Funding postings; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: funding remains separate algorithm | `src/triggertrade/backtest/simulator.py::_crosses_funding_boundary` RESEARCH/DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | FUNDING | Current simulator uses simplified funding boundaries; final canonical allocation requires review. |
| A-005 | Cumulative fill quantity, remaining quantity, and VWAP | Order Lifecycle | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: Order events, executions, and financial factual response | `src/triggertrade/accounting/futures.py::compute_vwap` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | EXECUTION | Backend may aggregate execution facts exactly; this is factual lifecycle accounting, not trading decision logic. |
| A-006 | Execution-linked cashflow allocation and residue assignment | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §2 Output Classes and execution-linked cashflow allocation | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | PNL | Quantized residue behavior is defined by numeric policy. |
| A-007 | Equity, unrealized PnL, and drawdown snapshot | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Account facts and balances | `src/triggertrade/accounting/futures.py::{calculate_unrealized_pnl, calculate_drawdown_snapshot}` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | EQUITY | Backend may implement factual snapshots from approved account and position facts. |
| A-008 | Pre-close partial-entry capital apportionment | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §5 Pre-Close Partial-Entry Apportionment | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | CAPITAL_ALLOCATION | Exact apportionment formulas are explicitly defined. |
| A-009 | Accounting-day realized totals and daily loss gate input | Accounting | ACCOUNTING_FORMULA | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Accounting day and cash postings | `src/triggertrade/services/daily_loss.py` DEMO_ONLY | CERTIFICATION_REQUIRED | BLOCK_FINAL_IMPLEMENTATION | DRAWDOWN | Accounting-day boundary is defined; final daily-loss calculation/gate must remain blocked until certified. |
| M-001 | Research net P/L metric | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::compute_futures_performance` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Backend may compute configurable research metrics without freezing values as product truth. |
| M-002 | Win rate metric | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::compute_futures_performance` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Research metric only. |
| M-003 | Profit factor metric | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::{_profit_factor, _profit_factor_reason}` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Research metric only. |
| M-004 | Max drawdown research metric | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::compute_futures_performance` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | DRAWDOWN | Research metric; live accounting drawdown is A-007/A-009. |
| M-005 | Expectancy, average winner, and average loser metrics | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::compute_futures_performance` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Research metric only. |
| M-006 | Fee drag, concentration, and research quality warnings | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::{PerformanceQualityPolicy, _quality_warnings, _top_concentration_pct}` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Threshold values remain research/calibration parameters. |
| M-007 | Backtest spread, slippage, and cost assumptions | Research | RESEARCH_METRIC | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/backtest/simulator.py::{_apply_cost_bps, simulate_closed_trade}` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | BACKTEST | Backend may parameterize assumptions for research only. |
| M-008 | Research grouping, direction mix, and regime aggregation | Research | AGGREGATION_RULE | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/analytics/futures.py::compute_futures_performance` RESEARCH_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RESEARCH_PERFORMANCE | Aggregation mechanics may exist as research outputs only. |
| T-001 | Position size percentage parameter | Position Rules | CONFIG_PARAMETER | `docs/trading-methodology/methodology/POSITION_RULES.md` :: research parameters and versioned settings | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.position_size_pct` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | POSITION_SIZING | Do not freeze as canonical truth. |
| T-002 | Leverage parameter | Position Rules | CONFIG_PARAMETER | `docs/trading-methodology/methodology/POSITION_RULES.md` :: position construction and versioned settings | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.leverage`; `src/triggertrade/services/futures_runtime.py::_position_risk_config_from_rules` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | POSITION_SIZING | Mechanics may validate configured leverage; values remain configurable. |
| T-003 | Fixed take-profit and minimum take-profit thresholds | Position Rules | THRESHOLD | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Dynamic Take Profit and research parameters | `src/triggertrade/rules/trading.py::{fixed_take_profit_pct, minimum_take_profit_pct}` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | DYNAMIC_TAKE | Thresholds must not replace certified Dynamic Take Profit logic. |
| T-004 | Stop-loss percentage threshold | Position Rules | THRESHOLD | `docs/trading-methodology/methodology/POSITION_RULES.md` :: stop and research parameters | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.stop_loss_pct` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | STOP | Demo threshold only until certified formulas land. |
| T-005 | Minimum risk/reward threshold | Position Rules | THRESHOLD | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Part V Minimum R:R | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.minimum_risk_reward` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RISK_REWARD | Backend may parameterize; final gate semantics need certification through F-012. |
| T-006 | Minimum net edge threshold | Position Rules | THRESHOLD | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Part V minimum net edge | `src/triggertrade/rules/trading.py::{minimum_net_edge_enabled, minimum_net_edge_pct}` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | RISK_REWARD | Backend may carry configuration only. |
| T-007 | Concurrent slot and per-coin position limits | Portfolio Rules | THRESHOLD | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §3 Portfolio Grant and Atomic Capacity Gates | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.max_open_positions_per_coin` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | PORTFOLIO_LIMITS | Gate mechanics are defined; exact configured limits remain parameters. |
| T-008 | Max capital and per-coin allocation caps | Portfolio Rules | CONFIG_PARAMETER | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §3 Portfolio Grant and Atomic Capacity Gates | `src/triggertrade/rules/trading.py::{max_capital_in_positions_pct, coin_rules}` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | CAPITAL_ALLOCATION | Backend may implement cap mechanics with configurable values. |
| T-009 | Daily loss limit threshold | Portfolio Rules | THRESHOLD | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Accounting day and realized postings | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.daily_loss_limit_pct`; `src/triggertrade/services/daily_loss.py` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | DRAWDOWN | Threshold value remains configurable; final daily-loss formula is A-009. |
| T-010 | Fee, spread, slippage, and funding assumption parameters | Research | CONFIG_PARAMETER | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary | `src/triggertrade/rules/trading.py::{maker_fee_rate, taker_fee_rate, assumed_spread_bps, assumed_slippage_bps, assumed_funding_cost_pct}` RESEARCH/DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | FEES_COSTS | Research assumptions may be configurable; factual accounting uses exchange facts. |
| T-011 | Cooldown duration parameter | Portfolio Rules | CONFIG_PARAMETER | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` :: §24 and Appendix A | `src/triggertrade/rules/trading.py::TradingRulesVersionDraft.cooldown_minutes` DEMO_ONLY | RESEARCH_PARAMETER | PARAMETERIZE_ONLY | PORTFOLIO_LIMITS | Backend may pin and apply configured duration per attempt, but the configured value remains parameterized. |
| N-001 | Exact decimal arithmetic and no intermediate rounding | Cross-System | NUMERIC_POLICY | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §1 Exact Arithmetic and No Intermediate Rounding | `src/triggertrade/canonical_json.py` PARTIAL; Decimal use across current code | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | MARKET_NORMALIZATION | Applies cross-system; does not itself approve trading formulas. |
| N-002 | Quantization classes: Qcapital, Qratio, tick, step | Cross-System | NUMERIC_POLICY | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §2 Output Classes | `src/triggertrade/execution/position_lifecycle.py::{floor_to_step, ceil_to_step}` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | MARKET_NORMALIZATION | Backend may implement quantization exactly where an approved formula permits it. |
| N-003 | Canonical JSON and digest encoding | Cross-System | NUMERIC_POLICY | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §6 Canonical Numeric Encoding | `src/triggertrade/canonical_json.py::{canonical_json_bytes, canonical_json_digest}` | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | OTHER:CANONICAL_IDENTITY | TD-006 is already resolved by source implementation. |
| N-004 | Price and quantity tick/step normalization | API | NORMALIZATION_RULE | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Instrument facts and `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §2 Output Classes | `src/triggertrade/execution/bybit_futures.py` PARTIAL; `src/triggertrade/execution/position_lifecycle.py` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | EXECUTION | Implementable as exchange fact validation and approved quantization. |
| N-005 | Native exchange fact sign and source normalization | API | NORMALIZATION_RULE | `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md` :: Native fact profile; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Source sign convention | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | MARKET_NORMALIZATION | API normalization can be implemented without formula certification. |
| N-006 | Governed accounting currency and no implicit FX conversion | Accounting | NORMALIZATION_RULE | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §2A Governed Accounting Unit Policy | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | PNL | Unsupported currency blocks finalization rather than inventing conversion. |
| N-007 | UTC factual windows and Asia/Jerusalem accounting day | Cross-System | NORMALIZATION_RULE | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` :: §1 Calendar; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Accounting day | `src/triggertrade/backtest/simulator.py::_crosses_funding_boundary` RESEARCH/DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | MARKET_NORMALIZATION | Window mechanics are implementable; formula-specific use remains separately gated. |
| N-008 | Canonical Set numeric output precision | Set | NORMALIZATION_RULE | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` :: §2 Canonical Set Value Representation | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | SET_ANALYTICS | Numeric encoding is approved, while Set formulas using it remain gated. |
| S-001 | Portfolio capacity and eligibility state classification | Portfolio Rules | STATE_CLASSIFICATION_RULE | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` :: §3 Portfolio Grant and Atomic Capacity Gates | `src/triggertrade/execution/futures.py::FuturesRiskManager.evaluate` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | PORTFOLIO_LIMITS | Backend may implement state outcomes from approved capacity gates. |
| S-002 | Set outcome and unavailable state classification | Set | STATE_CLASSIFICATION_RULE | `docs/trading-methodology/methodology/SET.md` :: Set lifecycle and outcomes | NONE | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | SET_ANALYTICS | State surface may be implemented; calculations feeding it remain formula-gated. |
| S-003 | Position validation outcome and rejection reason classification | Position Rules | STATE_CLASSIFICATION_RULE | `docs/trading-methodology/methodology/POSITION_RULES.md` :: invalidation/rejection and proof requirements | `src/triggertrade/execution/position_lifecycle.py` DEMO_ONLY | APPROVED_AS_DEFINED | IMPLEMENT_ALLOWED | EXECUTION | Reason-code scaffolding is allowed without final formula implementation. |
| S-004 | Order Lifecycle finality and closed-state predicate | Order Lifecycle | STATE_CLASSIFICATION_RULE | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: financial finality and lifecycle closure | `src/triggertrade/accounting/futures.py::close_futures_trade` DEMO_ONLY | REVIEW_NEEDED | BLOCK_FINAL_IMPLEMENTATION | EXECUTION | State predicate is coupled to final accounting; block final behavior until lifecycle/accounting review completes. |
| S-005 | Market regime classifier | Research | STATE_CLASSIFICATION_RULE | MISSING_CANONICAL_DEFINITION | `src/triggertrade/market_data/regime.py::evaluate_market_regime` RESEARCH/DEMO_ONLY | REVIEW_NEEDED | IMPLEMENT_STRUCTURE_ONLY | RESEARCH_PERFORMANCE | Current classifier is not a canonical trading input until defined or marked research-only. |
| S-006 | Research/demo/live path classification | Cross-System | NOT_A_FORMULA | `docs/BACKEND_TARGET_MODEL.md` :: §13 Research / Backtest / Optimization Boundary and §17 Cloud / Container Runtime Requirements | `src/triggertrade/services/runtime.py::build_runtime_from_env`; `src/triggertrade/services/futures_runtime.py` | NOT_APPLICABLE | NOT_APPLICABLE | OTHER:RUNTIME_BOUNDARY | Runtime isolation is an architecture rule, not a formula. |

## Unmapped Current Calculations

| Current Code | Behavior | Why Unmapped | Required Action |
| --- | --- | --- | --- |
| NONE | All materially relevant current formula-like code discovered in `src/` is mapped to at least one catalog item above. | NOT_APPLICABLE | Keep this section updated when new calculations are added. |

## Missing or Ambiguous Canonical Definitions

| ID / Candidate | Area | Evidence | Why Ambiguous | Backend Gate |
| --- | --- | --- | --- | --- |
| F-013 | Set pending invalidation | `docs/trading-methodology/methodology/SET.md` defines lifecycle concepts, while current runtime has demo snapshot logic in `src/triggertrade/services/futures_runtime.py`. | Exact boundary between final Set calculation and state-only lifecycle behavior needs review before final calculation semantics are implemented. | IMPLEMENT_STRUCTURE_ONLY |
| S-004 | Order Lifecycle closed-state predicate | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` defines finality evidence; traceability marks accounting final result as formula-gated. | Final state predicate is coupled to final accounting result and should not be completed independently. | BLOCK_FINAL_IMPLEMENTATION |
| S-005 | Market regime classifier | Current implementation exists in `src/triggertrade/market_data/regime.py`, but no approved canonical methodology definition was found. | It may remain research/demo-only or be defined later; it must not enter canonical runtime as a trading input now. | IMPLEMENT_STRUCTURE_ONLY |

## Formula Certification Queue

| Certification Order | ID | Formula | Owner | Dependency | Reason Certification Required |
| --- | --- | --- | --- | --- | --- |
| 1 | F-003 | Set ATR and true-range calculation | Set | N-001, N-008 | ATR feeds Set analytics and Position Rules handoff values. |
| 2 | F-001 | Price-move trigger calculation | Set | F-003, N-008 | Trigger activation affects candidate Set formation. |
| 3 | F-002 | Volume confirmation calculation | Set | N-008 | Confirmation affects whether Set evidence is eligible. |
| 4 | F-004 | Set normalization, percentile, and score calculation | Set | F-001, F-002, F-003 | Normalized values can influence ranking and handoff. |
| 5 | F-005 | Set direction classifier and LONG/SHORT handoff | Set | F-004 | Direction is the first trading-critical handoff into Position Rules. |
| 6 | F-008 | Planned entry reference selection | Position Rules | F-005 | Entry reference is consumed by stop, take-profit, and sizing formulas. |
| 7 | F-006 | Position Rules LONG formula | Position Rules | F-005, F-008 | Determines LONG entry/stop eligibility and ATR-risk constraints. |
| 8 | F-007 | Position Rules SHORT formula | Position Rules | F-005, F-008 | Determines SHORT entry/stop eligibility and ATR-risk constraints. |
| 9 | F-009 | Stop calculation and stop rounding | Position Rules | F-006, F-007, N-004 | Stop is protective trading-critical behavior. |
| 10 | F-010 | Dynamic Take Profit selection and rounding | Position Rules | F-008, N-004 | Take-profit selection controls target exit behavior. |
| 11 | F-011 | Position size, quantity, and actual notional construction | Position Rules | F-008, F-009, F-010, F-014, F-015 | Determines exposure and order quantity. |
| 12 | F-012 | Risk/reward and minimum net edge calculation | Position Rules | F-008, F-009, F-010, A-003, T-010 | Final eligibility gate combines trade geometry and costs. |
| 13 | A-002 | Net final result calculation | Accounting | A-001, A-003, A-004, A-005, A-006 | Traceability formula-gates accounting final result. |
| 14 | A-004 | Funding calculation and allocation | Accounting | N-007 | Funding allocation changes realized economics. |
| 15 | A-009 | Accounting-day realized totals and daily loss gate input | Accounting | A-002, N-007, T-009 | Daily-loss gate depends on certified final result aggregation. |

## Approved System and Accounting Calculations

Items with `APPROVED_AS_DEFINED` and `IMPLEMENT_ALLOWED`:

- F-014 Portfolio free-capital and grant calculation
- F-015 Actual committed capital from final quantity
- F-016 Attempt-scoped cooldown contribution and effective symbol cooldown
- A-001 Gross PnL calculation
- A-003 Fee cashflow calculation and attribution
- A-005 Cumulative fill quantity, remaining quantity, and VWAP
- A-006 Execution-linked cashflow allocation and residue assignment
- A-007 Equity, unrealized PnL, and drawdown snapshot
- A-008 Pre-close partial-entry capital apportionment
- N-001 Exact decimal arithmetic and no intermediate rounding
- N-002 Quantization classes: Qcapital, Qratio, tick, step
- N-003 Canonical JSON and digest encoding
- N-004 Price and quantity tick/step normalization
- N-005 Native exchange fact sign and source normalization
- N-006 Governed accounting currency and no implicit FX conversion
- N-007 UTC factual windows and Asia/Jerusalem accounting day
- N-008 Canonical Set numeric output precision
- S-001 Portfolio capacity and eligibility state classification
- S-002 Set outcome and unavailable state classification
- S-003 Position validation outcome and rejection reason classification

## Research / Calibration Parameters

| ID | Object | Generic Mechanics Backend May Implement | Value Must Remain Configurable | Can Research Change Without Methodology Revision |
| --- | --- | --- | --- | --- |
| M-001 | Research net P/L metric | Research/reporting aggregation | Reporting inclusion and comparison policy | YES |
| M-002 | Win rate metric | Research/reporting aggregation | Sampling and acceptance thresholds | YES |
| M-003 | Profit factor metric | Research/reporting aggregation | Acceptance thresholds | YES |
| M-004 | Max drawdown research metric | Research/reporting aggregation | Evaluation windows and acceptance thresholds | YES |
| M-005 | Expectancy and average trade metrics | Research/reporting aggregation | Evaluation windows and thresholds | YES |
| M-006 | Fee drag, concentration, and quality warnings | Warning mechanics | Warning thresholds | YES |
| M-007 | Backtest spread, slippage, and cost assumptions | Configurable simulation inputs | Assumption values | YES |
| M-008 | Research grouping, direction mix, and regime aggregation | Grouping/reporting mechanics | Grouping dimensions and acceptance thresholds | YES |
| T-001 | Position size percentage parameter | Configuration plumbing and validation | Percentage value | YES, unless promoted to canonical methodology |
| T-002 | Leverage parameter | Configuration plumbing and exchange-limit validation | Leverage value | YES, unless promoted to canonical methodology |
| T-003 | Fixed take-profit and minimum take-profit thresholds | Configuration plumbing only | Threshold values | YES |
| T-004 | Stop-loss percentage threshold | Configuration plumbing only | Threshold value | YES |
| T-005 | Minimum risk/reward threshold | Configuration plumbing only | Threshold value | YES |
| T-006 | Minimum net edge threshold | Configuration plumbing only | Threshold value | YES |
| T-007 | Concurrent slot and per-coin position limits | Capacity-gate mechanics | Limit values | YES |
| T-008 | Max capital and per-coin allocation caps | Capacity-gate mechanics | Cap values | YES |
| T-009 | Daily loss limit threshold | Configuration plumbing only | Threshold value | YES |
| T-010 | Fee, spread, slippage, and funding assumptions | Research/backtest mechanics | Assumption values | YES |
| T-011 | Cooldown duration parameter | Attempt-scoped pinning and cooldown contribution mechanics | Duration value | YES, unless promoted to immutable product truth |

## BACKEND IMPLEMENTATION GATE

1. Any catalog item with:
   `Backend Gate = BLOCK_FINAL_IMPLEMENTATION`
   MUST NOT receive final calculation logic.

2. Any catalog item with:
   `Backend Gate = IMPLEMENT_STRUCTURE_ONLY`
   MAY receive interfaces, state, persistence, orchestration, version pins, and integration boundaries, but not final calculation logic.

3. Any catalog item with:
   `Backend Gate = IMPLEMENT_ALLOWED`
   MAY be fully implemented exactly according to approved methodology.

4. Any catalog item with:
   `Backend Gate = PARAMETERIZE_ONLY`
   MAY implement generic configurable mechanics, but MUST NOT freeze research/calibration values as hardcoded canonical truth.

5. Any formula-like behavior not represented in this catalog:
   MUST NOT be newly implemented during backend execution.
   It must be treated as `REVIEW_NEEDED`.

## Traceability Cross-Check

| Implementation ID | Catalog IDs Involved | Gate Impact | Allowed Overnight Work |
| --- | --- | --- | --- |
| TT-BE-INFRA-008 | N-003 | FULLY_ALLOWED | Already complete; methodology integrity validation remains safe. |
| TT-BE-SYS-004 | N-001, N-003 | FULLY_ALLOWED | Already complete; canonical JSON/digest remains safe. |
| TT-BE-SYS-001 | N-003, S-006 | FULLY_ALLOWED | Already complete; contract models remain safe. |
| TT-BE-SYS-006 | S-006 | NONE | Already complete; runtime fencing is not formula work. |
| TT-BE-SYS-008 | S-006 | NONE | Smoke-script fencing may proceed without formula work. |
| TT-BE-SYS-011 | S-006 | NONE | Legacy strategy/risk fencing may proceed without formula work. |
| TT-BE-INFRA-001 | NONE | NONE | PostgreSQL infrastructure/provisioning work may proceed after Wave 1 gate. |
| TT-BE-SYS-002 | N-003, S-001, S-002, S-003 | FULLY_ALLOWED | Version pins/contracts may proceed without final formula logic. |
| TT-BE-SYS-003 | S-001, S-002, S-003, S-004 | STRUCTURE_ONLY | State machines may define structure; final accounting-coupled lifecycle predicates remain blocked. |
| TT-BE-SYS-005 | N-001, N-002, N-004, N-005 | FULLY_ALLOWED | Numeric and normalization helpers may proceed. |
| TT-BE-SYS-007 | S-006 | NONE | Runtime separation work may proceed if no formula behavior is added. |
| TT-BE-SYS-009 | N-003, S-006 | NONE | Replay/proof plumbing may proceed without formula semantics. |
| TT-BE-SYS-010 | F-001 through F-012, A-002, A-004, A-009, M-001 through M-008, T-001 through T-010 | STRUCTURE_ONLY | Target test taxonomy may scaffold formula-gated tests; no final formula assertions. |
| TT-BE-SYS-012 | N-003, S-006 | NONE | Operational/system work may proceed if it does not add formulas. |
| TT-BE-SYS-013 | N-003, S-006 | NONE | Operational/system work may proceed if it does not add formulas. |
| TT-BE-PR-001 | F-014, S-001 | FULLY_ALLOWED | Portfolio Rules contracts/state may implement approved capacity gate mechanics only. |
| TT-BE-PR-002 | F-014, T-007, T-008, S-001 | PARAMETERIZE_ONLY | Capacity mechanics may proceed; configured limit values remain parameters. |
| TT-BE-PR-003 | F-014, F-015, A-008, S-001 | FULLY_ALLOWED | Reservation/release mechanics may implement approved numeric policy. |
| TT-BE-PR-004 | F-014, T-007, T-008, S-001 | PARAMETERIZE_ONLY | Cap/slot enforcement mechanics may proceed with configurable values. |
| TT-BE-PR-005 | A-002, A-009, T-009 | BLOCKED | Final daily loss/final-result calculation is blocked pending certification. |
| TT-BE-PR-006 | F-016, T-011 | PARAMETERIZE_ONLY | Attempt-scoped cooldown pins may implement approved contribution/maximum mechanics; duration value remains configurable and PostgreSQL lineage is required by traceability. |
| TT-BE-SET-001 | S-002, N-008 | FULLY_ALLOWED | Set contracts/state surface may proceed. |
| TT-BE-SET-002 | F-001, F-002, F-003, F-004, F-005 | STRUCTURE_ONLY | Implement interfaces/persistence/proofs only; no final Set calculations. |
| TT-BE-SET-003 | F-003, F-004, N-008 | BLOCKED | Final Set numeric calculations are blocked pending certification. |
| TT-BE-SET-004 | F-005 | BLOCKED | Final LONG/SHORT direction classification is blocked pending certification. |
| TT-BE-SET-005 | F-001, F-002, F-004, F-013 | STRUCTURE_ONLY | Set lifecycle structure may proceed; final trigger/score calculations blocked. |
| TT-BE-SET-006 | F-001 through F-005, F-013 | STRUCTURE_ONLY | End-to-end Set orchestration may scaffold only; no final formulas. |
| TT-BE-POS-001 | F-005, F-006, F-007 | BLOCKED | Final LONG/SHORT Position formulas are blocked pending certification. |
| TT-BE-POS-002 | S-003 | FULLY_ALLOWED | Position Rules contracts/reason codes may proceed. |
| TT-BE-POS-003 | F-008, F-009, F-010, F-011, F-012 | STRUCTURE_ONLY | Position pipeline may scaffold only; no final trading formulas. |
| TT-BE-POS-004 | F-006 through F-012, N-003 | STRUCTURE_ONLY | Specification identity/persistence may proceed structurally; formula values remain blocked. |
| TT-BE-POS-005 | F-008, F-009, F-010 | BLOCKED | Entry/Stop/Dynamic Take final formulas are blocked pending certification. |
| TT-BE-POS-006 | S-003, N-003 | FULLY_ALLOWED | Audit/proof structure may proceed without formula implementation. |
| TT-BE-OL-001 | S-004, A-005 | STRUCTURE_ONLY | Lifecycle state skeleton may proceed; finality predicate remains blocked. |
| TT-BE-OL-002 | A-005, S-004 | FULLY_ALLOWED | Order event ingestion and factual execution aggregation may proceed. |
| TT-BE-OL-003 | A-005, S-004 | STRUCTURE_ONLY | Protective-order state may proceed; final financial finality remains blocked. |
| TT-BE-OL-004 | A-005, S-004 | STRUCTURE_ONLY | Reconciliation structure may proceed; final closed-state predicate remains blocked. |
| TT-BE-OL-005 | A-005, S-004 | FULLY_ALLOWED | Idempotent event handling may proceed without final formulas. |
| TT-BE-OL-006 | A-005, S-004 | FULLY_ALLOWED | Duplicate/terminal state protections may proceed. |
| TT-BE-OL-007 | A-002, A-003, A-004, A-005, A-006 | BLOCKED | Final financial result is blocked pending accounting formula certification. |
| TT-BE-OL-008 | A-005, S-004 | STRUCTURE_ONLY | Lifecycle projection may proceed; finality-coupled logic remains blocked. |
| TT-BE-OL-009 | A-002, A-004, A-009 | BLOCKED | Final accounting/funding/day result is blocked pending certification. |
| TT-BE-OL-010 | A-005, S-004 | FULLY_ALLOWED | Factual replay/event tests may proceed without final formulas. |
| TT-BE-API-001 | N-001, N-002, N-004, N-005, N-006, N-007, F-003, F-004 | STRUCTURE_ONLY | API normalization may proceed; Set formula-derived outputs remain blocked. |
| TT-BE-API-002 | N-005, N-006, N-007 | FULLY_ALLOWED | API adapters/factual normalization may proceed. |
| TT-BE-API-003 | N-004, N-005, A-005 | FULLY_ALLOWED | Execution fact normalization may proceed. |
| TT-BE-API-004 | N-005, N-006, N-007 | FULLY_ALLOWED | API evidence/proof contracts may proceed. |
| TT-BE-RES-001 | M-001 through M-008, T-010, S-006 | PARAMETERIZE_ONLY | Research boundary may proceed with configurable metrics only. |
| TT-BE-RES-002 | F-001 through F-012, M-001 through M-008, T-001 through T-010 | STRUCTURE_ONLY | Formula certification harness may proceed; no formula approval by implementation. |
| TT-BE-RES-003 | M-001 through M-008, T-010 | PARAMETERIZE_ONLY | Research reporting may proceed with configurable parameters. |
| TT-BE-RES-004 | M-001 through M-008, S-006 | PARAMETERIZE_ONLY | Research/backtest isolation may proceed. |

## Current-Code Inventory Cross-Check

The following current formula-like areas were inspected and mapped:

- `src/triggertrade/triggers/percentage_price_move.py` -> F-001
- `src/triggertrade/triggers/volume_confirmation.py` -> F-002, F-004
- `src/triggertrade/services/futures_runtime.py` -> F-005, F-008, F-011, F-013, T-002, S-006
- `src/triggertrade/execution/position_lifecycle.py` -> F-009, F-011, F-012, N-002, S-003
- `src/triggertrade/execution/futures.py` -> F-012, F-016, S-001, T-010
- `src/triggertrade/execution/precision.py` -> N-004
- `src/triggertrade/execution/bybit_futures.py` -> N-004, N-005
- `src/triggertrade/accounting/futures.py` -> A-001, A-002, A-005, A-007
- `src/triggertrade/backtest/simulator.py` -> A-003, A-004, M-007, N-007
- `src/triggertrade/backtest/engine.py` -> M-001 through M-008, T-001 through T-010
- `src/triggertrade/analytics/futures.py` -> M-001 through M-006, M-008
- `src/triggertrade/rules/trading.py` -> T-001 through T-011
- `src/triggertrade/config/settings.py` -> T-007 through T-010, S-006
- `src/triggertrade/risk/manager.py` -> F-012, S-001 LEGACY/DEMO_ONLY
- `src/triggertrade/strategies/buy_candidate.py` -> F-001, F-005 LEGACY/DEMO_ONLY
- `src/triggertrade/strategies/futures_directional.py` -> F-005, F-008, T-003, T-004 DEMO_ONLY
- `src/triggertrade/market_data/regime.py` -> S-005
- `src/triggertrade/services/daily_loss.py` -> A-009, T-009
- `src/triggertrade/instruments/catalog.py` and `src/triggertrade/services/instrument_catalog.py` -> N-004, N-005
- `src/triggertrade/canonical_json.py` -> N-003

## Completeness Audit

| Measure | Count |
| --- | ---: |
| Total catalog items | 58 |
| TRADING_FORMULA | 12 |
| SYSTEM_FORMULA | 4 |
| ACCOUNTING_FORMULA | 9 |
| RESEARCH_METRIC | 7 |
| DERIVED_METRIC | 0 |
| THRESHOLD | 6 |
| CONFIG_PARAMETER | 5 |
| NORMALIZATION_RULE | 5 |
| NUMERIC_POLICY | 3 |
| STATE_CLASSIFICATION_RULE | 5 |
| AGGREGATION_RULE | 1 |
| NOT_A_FORMULA | 1 |
| CERTIFICATION_REQUIRED | 15 |
| APPROVED_AS_DEFINED | 20 |
| RESEARCH_PARAMETER | 19 |
| REVIEW_NEEDED | 3 |
| NOT_APPLICABLE | 1 |
| BLOCK_FINAL_IMPLEMENTATION | 16 |
| IMPLEMENT_STRUCTURE_ONLY | 2 |
| IMPLEMENT_ALLOWED | 20 |
| PARAMETERIZE_ONLY | 19 |
| NOT_APPLICABLE backend gate | 1 |
| Unmapped current calculations | 0 |
| Missing or ambiguous canonical definitions | 3 |

## Readiness Verdict

READY_FOR_BACKEND_WITH_FORMULA_GATES
