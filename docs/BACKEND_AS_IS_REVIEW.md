# TriggerTrade Backend As-Is Review

This review is an as-is inventory of the current repository implementation. It uses code, tests, scripts, and runtime configuration as evidence. README prose was treated as supporting context only.

## 1. Executive Summary

The current backend is a Python package under `src/triggertrade` with explicit subsystems for configuration, Bybit REST access, market-data parsing, triggers, trigger-set and trading-rule registries, strategies, risk checks, execution, futures position lifecycle, futures accounting, persistence, backtest/research, dashboard read models, and local dashboard HTTP serving.

The current runtime model has multiple executable paths. `python -m triggertrade.services.runtime` now builds `FuturesDualLaneRuntime`, which runs a continuous polling loop over Bybit Demo linear BTCUSDT 1-minute candles, evaluates one ACTIVE lane and zero or more TEST lanes, persists lane lifecycle/checkpoints, and may submit ACTIVE futures orders through a Bybit Demo futures adapter. A legacy `PaperTradingRuntime` class for spot/local-paper flow still exists in the same module. `python -m triggertrade.dashboard` starts a local `ThreadingHTTPServer` dashboard. `python -m triggertrade.backtest` runs historical replay. Scripts provide opt-in smoke/soak entry points.

The persistence model is SQLite-first. Most stores default to `runtime/triggertrade_paper.sqlite3`, while historical kline cache uses JSON files under `runtime/history` and backup/restore uses filesystem backup directories plus manifest files. Runtime candle state, lane state, lifecycle facts, execution facts, futures positions, accounting facts, trigger/rule registries, research orchestration, messages, operator state, audit events, and backtest runs all have SQLite tables.

The exchange integration is Bybit Demo REST through `BybitDemoClient`. Public endpoints are used for time, instruments, tickers, and spot/linear klines. Private signed endpoints are used for wallet balance, spot/linear order create/cancel/realtime/history, execution list, and linear position list. No other exchange adapter implementation was found.

The research/backtest capability is implemented but bounded. Historical replay exists for futures trigger sets using supplied or cached Bybit Demo public linear candles. Research records, backtest runs, demo-run records, selection, archive, comparison, and make-active request code exist. Several research demo/backtest branches explicitly return blocked statuses when required inputs or isolation are unavailable.

Deployment/container capability exists as a dashboard container: `Dockerfile` installs the package, exposes port `8765`, sets dashboard host `0.0.0.0`, stores runtime data under `/app/runtime`, and runs `python -m triggertrade.dashboard`. `scripts/deploy-azure.ps1` builds/pushes an image to Azure Container Registry and updates an Azure Container App, then polls `/healthz`.

Major implementation concentrations are `src/triggertrade/services/futures_runtime.py`, `src/triggertrade/dashboard/read_model.py`, `src/triggertrade/dashboard/__main__.py`, persistence stores, futures execution/accounting, and research/backtest. Major fragmentation areas visible as-is are legacy spot paper flow alongside futures flow, many opt-in demo/smoke scripts, direct dashboard access to stores/services, and multiple execution/accounting paths sharing one SQLite file.

## 2. Repository Backend Map

| Area | Path | Key Classes / Functions | Apparent Responsibility | Runtime-Critical? | Persistence-Critical? | Notes |
|---|---|---|---|---|---|---|
| Package metadata | `src/triggertrade/__init__.py` | `__version__` | Package version marker. | No | No | Version is `0.1.0`. |
| Accounting | `src/triggertrade/accounting/futures.py` | `FuturesFillEvent`, `FuturesFundingEvent`, `ClosedTradeResult`, `EquitySnapshot`, `compute_vwap`, `gross_pnl`, `close_futures_trade`, `calculate_unrealized_pnl`, `calculate_drawdown_snapshot` | Deterministic futures accounting calculations and contracts. | Yes | Indirect | Used by runtime, backtest, lifecycle, stores. |
| Analytics | `src/triggertrade/analytics/futures.py` | `TradePerformanceFact`, `FuturesPerformanceMetrics`, `compute_futures_performance`, `compare_baseline` | Closed-trade metrics, quality warnings, baseline comparison. | No for order path | Indirect | Used by dashboard/research/backtest. |
| Backtest CLI | `src/triggertrade/backtest/__main__.py` | `main` | CLI for deterministic historical replay. | Separate runtime | Yes | Requires explicit assumptions/env. |
| Backtest data | `src/triggertrade/backtest/data.py` | `HistoricalKlineCache`, `BybitHistoricalDataSource`, `validate_historical_candles` | Historical candle validation, JSON cache, Bybit public historical fetch. | Backtest only | Yes | Files under `runtime/history`. |
| Backtest engine | `src/triggertrade/backtest/engine.py` | `BacktestEngine`, `run_backtest` | Replays futures trigger sets using runtime components and simulator. | Backtest only | Yes | Persists traces/accounting/backtest runs. |
| Backtest models | `src/triggertrade/backtest/models.py` | `BacktestPlan`, `BacktestRun`, `BacktestResult` | Versioned replay contracts. | Backtest only | Yes | Includes simulator/data/cost/accounting version fields. |
| Backtest simulator | `src/triggertrade/backtest/simulator.py` | `BacktestFuturesSimulator` | Simulates closed futures trades for replay. | Backtest only | Yes | Rejects funding-boundary positions. |
| Backtest store | `src/triggertrade/backtest/store.py` | `BacktestStore` | SQLite persistence for replay runs/results/comparisons/run-trade mapping. | Backtest only | Yes | Immutable-conflict checks. |
| Config | `src/triggertrade/config/settings.py` | `AppConfig`, `BybitConfig`, `PaperRuntimeConfig`, `FuturesRuntimeConfig`, `load_config`, `load_bybit_credentials` | Env parsing, defaults, safety gates, credential loading. | Yes | No | Restricts loaded config to paper/live-disabled. |
| Dashboard server | `src/triggertrade/dashboard/__main__.py` | `DashboardServer`, `DashboardHandler`, `create_server_from_env`, `main` | Local HTTP dashboard, JSON APIs, operator/research/rules actions. | Dashboard runtime | Yes | Uses in-process stores/services and token. |
| Dashboard product UI | `src/triggertrade/dashboard/product_ui.py` | HTML/JS render helpers | Server-rendered dashboard HTML fragments/scripts. | Dashboard runtime | No | Contains substantial UI string generation. |
| Dashboard read model | `src/triggertrade/dashboard/read_model.py` | `DashboardReadModel`, many `*View` dataclasses | SQLite read projections for dashboard, readiness, portfolio, rules, research, analytics. | Dashboard runtime | Yes | Opens SQLite read-only URI. |
| Exchanges contracts | `src/triggertrade/exchanges/contracts.py` | `ExchangeAdapter`, `ExchangeHealth` | Generic exchange boundary contract. | No direct use found | No | Interface exists. |
| Bybit exchange client | `src/triggertrade/exchanges/bybit.py` | `BybitDemoClient`, `BybitApiError`, `BybitResponse` | Bybit Demo REST public/private client and signing. | Yes | No | Uses stdlib `urllib`. |
| Spot Bybit execution | `src/triggertrade/execution/bybit.py` | `BybitExecutionAdapter`, `map_bybit_order_status` | Spot order create/cancel/reconcile adapter. | Legacy/demo spot | Indirect | Uses category `spot`. |
| Futures Bybit execution | `src/triggertrade/execution/bybit_futures.py` | `BybitFuturesExecutionAdapter` | Linear futures order create/cancel/reconcile adapter. | Yes | Indirect | Uses reduce-only for closes. |
| Execution contracts | `src/triggertrade/execution/contracts.py` | `TradeIntent`, `RiskDecision`, `OrderStatus`, `Side`, `OrderType` | Spot/paper execution contracts. | Legacy/demo spot | Yes | Used by legacy paper path. |
| Futures execution | `src/triggertrade/execution/futures.py` | `FuturesTradeIntent`, `FuturesRiskDecision`, `FuturesRiskManager`, `FuturesExecutionService`, `estimate_costs`, `estimate_net_edge` | Futures risk and execution service contract. | Yes | Yes | Enforces demo linear environment and precision/margin/operator checks. |
| Paper execution | `src/triggertrade/execution/paper.py` | `PaperExecutionAdapter` | Deterministic local order adapter. | Legacy paper | Indirect | No external API. |
| Position lifecycle | `src/triggertrade/execution/position_lifecycle.py` | `FuturesPositionLifecycleService`, `PositionRiskConfig`, `build_fixed_protective_exit_plan`, `calculate_position_size`, `close_all_positions`, `recover_after_restart` | Futures open/close/protective exit/recovery logic. | Yes | Yes | Persists positions, events, closed positions. |
| Precision | `src/triggertrade/execution/precision.py` | `validate_limit_order_precision` | Spot-style limit order tick/quantity validation. | Legacy/demo spot | No | Futures has its own validation in `futures.py`. |
| Governance | `src/triggertrade/governance/experiment.py` | `GovernancePolicy`, `GovernanceEvidence`, `evaluate_readiness` | Evidence-readiness evaluation for recommendations. | No | No | Research/decision support. |
| Instruments | `src/triggertrade/instruments/catalog.py` | `FuturesInstrument`, `InstrumentCatalogRefreshResult`, `instrument_from_bybit`, `normalize_qty_for_instrument`, `normalize_price_for_instrument` | Futures instrument catalog parsing, validation, normalization, snapshots. | Yes | Yes | Bybit linear catalog specific. |
| Market data parsing | `src/triggertrade/market_data/bybit.py` | `BybitInstrument`, `BybitTicker`, `BybitCandle`, `parse_spot_*`, `parse_linear_*` | Parse Bybit API payloads to domain objects. | Yes | No | Linear parser returns futures metadata. |
| Futures market models | `src/triggertrade/market_data/futures.py` | `FuturesInstrumentMetadata`, `FuturesAccountState`, `MarketRegimeContext` | Futures/account/regime domain data. | Yes | Indirect | Shared across runtime, rules, accounting. |
| Futures event adapter | `src/triggertrade/market_data/futures_runtime.py` | `FuturesMarketEvent`, `futures_event_from_completed_candle`, `volume_window_from_futures_event` | Convert completed candle to futures event and trigger inputs. | Yes | No | Used by runtime/backtest. |
| Market observation | `src/triggertrade/market_data/models.py` | `MarketObservation` | Spot-style observation object with staleness check. | Yes | No | Used by TRG-001. |
| Market regime | `src/triggertrade/market_data/regime.py` | `RegimeEvaluationWindow`, `evaluate_market_regime` | Deterministic CTX-REGIME classifier. | Yes | Yes | Persisted by `RuntimeStore`. |
| Persistence stores | `src/triggertrade/persistence/*.py` | `RuntimeStore`, `TraceStore`, `ExecutionStore`, `FuturesExecutionStore`, `FuturesPositionStore`, `FuturesAccountingStore`, `TriggerSetStore`, `TradingRulesStore`, `ResearchStore`, `OperatorStateStore`, `MessageStore`, `DailyLossStore`, `InstrumentCatalogStore` | SQLite storage boundaries. | Yes | Yes | Core durable backend state. |
| Risk | `src/triggertrade/risk/manager.py` | `RiskManager` | Demo spot/local-paper risk checks. | Legacy/demo spot | Yes | Rules `RSK-001` through `RSK-005`. |
| Trading rules | `src/triggertrade/rules/trading.py` | `TradingRulesService`, `TradingRulesVersionDraft`, `build_initial_trading_rules`, `validate_rules_draft`, `apply_changes` | Versioned futures trading-rule model and mutation service. | Yes | Yes | Dashboard writes through service. |
| Backup/restore | `src/triggertrade/services/backup_restore.py` | `BackupService`, `critical_state_fingerprint` | SQLite backup, verification, restore checks, secret scan. | Operational | Yes | Uses filesystem backup dirs. |
| Bootstrap | `src/triggertrade/services/bootstrap.py` | `merged_runtime_env`, `runtime_db_path`, `ensure_runtime_registry_initialized` | `.env` loading, runtime config, registry bootstrap. | Yes | Yes | Used by runtime/dashboard/backtest. |
| Daily loss | `src/triggertrade/services/daily_loss.py` | `DailyLossEvaluator`, `read_only_daily_loss_state` | Daily loss baseline/latch evaluation. | Yes if enabled | Yes | Uses accounting snapshots and `DailyLossStore`. |
| DB audit | `src/triggertrade/services/db_integrity_audit.py` | `DatabaseIntegrityAudit`, `run_database_integrity_audit` | SQLite integrity/check/query-plan audit. | Operational | Yes | Tested but not an executable script. |
| Dual lane legacy | `src/triggertrade/services/dual_lane_runtime.py` | `DualLaneRuntime` | Earlier/spot dual-lane runtime. | UNCLEAR active | Yes | Exists alongside futures dual-lane runtime. |
| Futures accounting bridge | `src/triggertrade/services/futures_accounting_bridge.py` | `FuturesAccountingBridge` | Ingest execution fills and close trades from Bybit execution rows. | Yes | Yes | Calls adapter fill lookup. |
| Futures runtime | `src/triggertrade/services/futures_runtime.py` | `FuturesDualLaneRuntime` | Continuous ACTIVE/TEST futures runtime. | Yes | Yes | Main current trading loop. |
| Instrument catalog service | `src/triggertrade/services/instrument_catalog.py` | `InstrumentCatalogService` | Refresh/search/validate Bybit linear instruments. | Yes | Yes | Public Bybit only. |
| Regime smoke | `src/triggertrade/services/regime_smoke.py` | `main` | Local smoke for regime classifier. | No | No | Executable module. |
| Research service | `src/triggertrade/services/research.py` | `ResearchService`, `ResearchDemoIsolation`, `ResearchCompareResult` | Backend orchestration for research/backtest/demo/selection/promotion requests. | Dashboard/research | Yes | Some flows blocked when inputs/isolation unavailable. |
| Runtime service | `src/triggertrade/services/runtime.py` | `PaperTradingRuntime`, `build_runtime_from_env`, `main` | Legacy paper runtime and current futures runtime entry builder. | Yes | Yes | `main` builds futures runtime. |
| System history | `src/triggertrade/services/system_history.py` | `SystemHistoryExporter` | Public-safe dashboard/system export text. | Dashboard support | Yes | Used by dashboard API. |
| Test simulator | `src/triggertrade/services/test_futures_simulator.py` | `TestFuturesSimulator` | Deterministic TEST-lane futures closed-trade simulation. | TEST lane | Yes | No exchange calls. |
| Strategies | `src/triggertrade/strategies/*.py` | `BuyCandidateStrategy`, `IntegrationDirectionalFuturesStrategy`, `RegimeStrategyContext` | Convert signals/context into spot/futures trade intents. | Yes | Indirect | Futures strategy docstring says demo-only integration strategy. |
| Trigger contracts | `src/triggertrade/triggers/contracts.py` | `SignalType`, `Signal` | Trigger output contract. | Yes | Yes | Persisted by trace store. |
| TRG-001 | `src/triggertrade/triggers/percentage_price_move.py` | `PercentagePriceMoveTrigger` | Percentage price move trigger. | Yes | Yes | Uses config threshold/window. |
| TRG-002 | `src/triggertrade/triggers/volume_confirmation.py` | `RobustVolumeConfirmationTrigger` | Volume confirmation trigger. | Yes if in set | Yes | Uses 60-candle median and percentile thresholds. |
| Trigger sets | `src/triggertrade/trigger_sets/contracts.py` | `RuleDefinition`, `TriggerSetVersion`, `Recommendation`, `RegistrySyncReport` | Registry contracts for rules/sets/recommendations. | Yes | Yes | Supports multiple rule types. |
| Scripts | `scripts/*.py`, `scripts/deploy-azure.ps1` | `main`, smoke harnesses, deploy script | Opt-in smoke/soak, deployment. | Some operational | Some | Most smoke scripts are guarded by env flags. |
| Runtime config | `pyproject.toml`, `.env.example`, `Dockerfile`, `.dockerignore` | Package/test/env/container settings | Build, test, env defaults, dashboard container. | Yes | Yes | Docker runs dashboard only. |

## 3. Current Runtime Topology

Executable entry points identified:

| Entry Point | Path | Behavior |
|---|---|---|
| `python -m triggertrade.services.runtime` | `src/triggertrade/services/runtime.py` | Loads `.env`/env, bootstraps registries, loads Bybit credentials, constructs `FuturesDualLaneRuntime`, runs forever. |
| `python -m triggertrade.dashboard` | `src/triggertrade/dashboard/__main__.py` | Starts `ThreadingHTTPServer` dashboard on configured host/port. |
| `python -m triggertrade.backtest` | `src/triggertrade/backtest/__main__.py` | Runs deterministic historical replay CLI. |
| `python -m triggertrade.services.regime_smoke` | `src/triggertrade/services/regime_smoke.py` | Runs local regime smoke. |
| Smoke/soak scripts | `scripts/*.py` | Manual opt-in public/private Bybit, paper, futures, accounting, instrument catalog, e2e, soak checks. |
| Azure deploy | `scripts/deploy-azure.ps1` | Build/push/deploy dashboard container and poll health. |

Long-running processes:

| Process | Code | Loop | Notes |
|---|---|---|---|
| Futures runtime | `FuturesDualLaneRuntime.run_forever` in `src/triggertrade/services/futures_runtime.py` | `while not self._stop_requested`, sleep `config.futures_runtime.poll_interval_seconds` | Records runtime heartbeat before/after cycles. |
| Legacy paper runtime | `PaperTradingRuntime.run_forever` in `src/triggertrade/services/runtime.py` | `while not self._stop_requested`, sleep `config.paper_runtime.poll_interval_seconds` | Class exists; current module `main` does not build it. |
| Legacy dual-lane runtime | `DualLaneRuntime.run_forever` in `src/triggertrade/services/dual_lane_runtime.py` | Poll loop | Current active entry point not found. |
| Dashboard | `ThreadingHTTPServer.serve_forever` in `src/triggertrade/dashboard/__main__.py` | HTTP server loop | In-process direct store/service access. |
| Demo soak | `scripts/triggertrade_demo_soak.py` | Bounded cycle loop | Requires opt-in env flag. |

Worker separation: no separate worker process, queue, task runner, or broker was found. Runtime and dashboard are separate executable processes if started separately, but the dashboard itself directly opens the same SQLite path and constructs stores/services in-process.

ACTIVE / TEST / DEMO / BACKTEST separation as implemented:

| Path | Separation Evidence |
|---|---|
| ACTIVE futures lane | `FuturesDualLaneRuntime._process_lane` with `Lane.ACTIVE`; current active trigger set from `TriggerSetStore.get_active_trading_pair`; active execution venue must be `BYBIT_DEMO_FUTURES`. |
| TEST futures lane | `list_testing_sets`, `Lane.TEST`, `TestFuturesSimulator`, local test execution venue required. |
| Demo exchange | `BybitEnvironment.DEMO`, `BYBIT_BASE_URL=https://api-demo.bybit.com`, Bybit Demo clients/adapters. |
| Legacy spot/paper | `PaperTradingRuntime`, `RiskManager`, `ExecutionService`, `ExecutionStore`, spot parsers/adapters. |
| Backtest | `BACKTEST_EVIDENCE_SOURCE`, `BacktestEngine`, `BacktestStore`, `BacktestFuturesSimulator`; no private Bybit calls in replay engine. |

Local-machine dependencies:

- `.env` is loaded by `services/bootstrap.py` if present.
- Default runtime DB is `runtime/triggertrade_paper.sqlite3`.
- Historical cache default is `runtime/history`.
- Smoke scripts write runtime SQLite files under `runtime/`.
- Dashboard default host is `127.0.0.1`; Docker changes it to `0.0.0.0`.
- Operator token is generated in memory on dashboard server startup.

Textual current futures flow:

```text
Bybit Demo public linear candles/catalog
-> FuturesDualLaneRuntime
-> RuntimeStore checkpoint/lifecycle and market regime
-> TriggerSetStore active/testing sets
-> TRG-001 and optional TRG-002
-> TradingRulesStore current rules
-> IntegrationDirectionalFuturesStrategy
-> FuturesRiskManager plus DailyLossEvaluator/operator state/instrument metadata
-> ACTIVE: FuturesPositionLifecycleService -> FuturesExecutionService -> BybitFuturesExecutionAdapter -> Bybit private order APIs
-> TEST: TestFuturesSimulator
-> FuturesAccountingBridge/FuturesAccountingStore/FuturesPositionStore/TraceStore
-> DashboardReadModel/dashboard APIs
```

Legacy spot/paper flow present in code:

```text
Bybit Demo public spot instrument/candles
-> PaperTradingRuntime
-> PercentagePriceMoveTrigger
-> BuyCandidateStrategy
-> RiskManager
-> ExecutionService -> PaperExecutionAdapter
-> ExecutionStore/TraceStore/RuntimeStore
```

## 4. Persistence Inventory

| Store / Module | Path | Storage Technology | State Owned | Key Tables / Files | Restart Significance | Shared Across Processes? | Notes |
|---|---|---|---|---|---|---|---|
| Runtime store | `src/triggertrade/persistence/runtime_store.py` | SQLite | Legacy checkpoint/lifecycle; lane checkpoint/lifecycle; market regime; heartbeats | `runtime_candle_state`, `runtime_candle_lifecycles`, `runtime_lane_state`, `runtime_lane_lifecycles`, `market_regime_evaluations`, `runtime_heartbeats` | High | Yes, via same SQLite path | Lane checkpoints drive candle continuity. |
| Trace store | `src/triggertrade/persistence/trace_store.py` | SQLite | Trigger evaluations, strategy decisions, risk decisions, audit events | `trigger_evaluations`, `strategy_decisions`, `risk_decisions`, `audit_events` | High | Yes | Redacts safe metadata. |
| Legacy execution store | `src/triggertrade/persistence/execution_store.py` | SQLite | Spot/paper execution orders/fills/idempotency | `execution_orders`, `execution_fills` | High for legacy path | Yes | Unique `intent_id`, `risk_decision_id`, `client_order_id`. |
| Futures execution store | `src/triggertrade/persistence/futures_execution_store.py` | SQLite | Futures execution order facts | `futures_execution_orders` | High | Yes | Unique intent/risk/client order ids. |
| Futures position store | `src/triggertrade/persistence/futures_position_store.py` | SQLite | Open/closed futures positions, position events, close-all operations | `futures_positions`, `futures_position_events`, `futures_closed_positions`, `futures_close_all_operations` | High | Yes | Unique open position per symbol where status in `OPEN`, `CLOSING`, `UNKNOWN`. |
| Futures accounting store | `src/triggertrade/persistence/futures_accounting_store.py` | SQLite | Fills, funding, closed trades, equity snapshots | `futures_accounting_fills`, `futures_accounting_funding`, `futures_closed_trades`, `futures_equity_snapshots` | High | Yes | Includes realized day queries and latest equity snapshots. |
| Daily loss store | `src/triggertrade/persistence/daily_loss_store.py` | SQLite | Daily baseline/latch/notification state | `daily_loss_state` | High if daily loss enabled | Yes | One row per trading day. |
| Instrument catalog store | `src/triggertrade/persistence/instrument_catalog_store.py` | SQLite | Bybit linear instrument catalog and refresh history | `futures_instrument_catalog`, `futures_instrument_catalog_refreshes` | Medium/high | Yes | Runtime validates symbols and precision from this store/service. |
| Trigger set store | `src/triggertrade/persistence/trigger_set_store.py` | SQLite | Rule definitions, trigger set versions, memberships, transitions, recommendations | `rule_definitions`, `trigger_set_versions`, `trigger_set_memberships`, `trigger_set_transitions`, `recommendations`, `recommendation_transitions` | High | Yes | Bootstrapped at runtime/dashboard startup. |
| Trading rules store | `src/triggertrade/persistence/trading_rules_store.py` | SQLite | Immutable trading rule versions, current pointer, coin rules, usage | `trading_rules_versions`, `trading_rules_current`, `trading_rules_coin_rules`, `trading_rules_usage` | High | Yes | Current rules pointer used by runtime. |
| Research store | `src/triggertrade/persistence/research_store.py` | SQLite | Research entities, backtest/demo runs, decision events | `research_entities`, `research_backtest_runs`, `research_demo_runs`, `research_decision_events` | Medium/high | Yes | Dashboard/research workflow state. |
| Message store | `src/triggertrade/persistence/message_store.py` | SQLite | User/operator messages, read state, dedupe, expiry, metadata | `user_messages` | Medium | Yes | Metadata redaction exists. |
| Operator state store | `src/triggertrade/persistence/operator_state_store.py` | SQLite | Trading pause/resume state and operator audits | `operator_trading_state`, `operator_action_audit`, `operator_trading_state_audit` | High | Yes | Dashboard writes operator actions. |
| Backtest store | `src/triggertrade/backtest/store.py` | SQLite | Historical replay runs/results/comparisons/trade mappings | `backtest_runs`, `backtest_results`, `backtest_comparisons`, `backtest_run_trades` | Medium | Yes | Defaults to runtime DB. |
| Historical kline cache | `src/triggertrade/backtest/data.py` | Local JSON files | Historical candles and metadata | `runtime/history/*.json`, `*.metadata.json` | Medium for backtest reuse | Shared if same filesystem | Content hash and metadata validation. |
| Backup service | `src/triggertrade/services/backup_restore.py` | Local filesystem plus SQLite backup copy | Backups, manifests, restore verification | backup directories/manifests, copied DB files | High operationally | Shared if same filesystem | Default backup dir inferred from service construction/tests; exact runtime default not fully visible from inventory output: UNCLEAR. |
| Smoke/runtime fixture DBs | `scripts/*.py`, `tests/**/*.py` | SQLite files | Isolated smoke/test runtime state | `runtime/*smoke*.sqlite3`, `tmp_path/*.sqlite3` | Low/medium | Usually local only | Generated files ignored by `.dockerignore`. |

State that survives restart:

- SQLite facts in the configured runtime DB: checkpoints, lane lifecycles, traces, executions, positions, accounting, rules/sets, messages, operator state, research, backtests.
- Historical JSON cache under `runtime/history`.
- Backup artifacts if retained on disk.

State that does not survive restart:

- In-memory dashboard `operator_control_token`.
- Runtime instance `_stop_requested`, `_account_snapshot_sequence`, injected mocks/providers/adapters.
- Any process-local logger/sleeper/clock callables.

## 5. External Integration Inventory

| Integration | Path | Purpose | Auth Required? | Failure Handling | Runtime Mode(s) | Notes |
|---|---|---|---|---|---|---|
| Bybit public market time | `src/triggertrade/exchanges/bybit.py` | `/v5/market/time` connectivity/time. | No | `BybitApiError` on transport/API/JSON issues. | Smoke/client | Public REST. |
| Bybit public spot instruments | `BybitDemoClient.instrument_metadata` | Spot instrument metadata. | No | Parser `ValueError` or client `BybitApiError`. | Legacy spot/paper/smoke | Category `spot`. |
| Bybit public linear instruments | `BybitDemoClient.linear_instrument_metadata`, `linear_instruments_info`; `InstrumentCatalogService` | Linear futures instrument metadata/catalog. | No | `CatalogError`, failed refresh records/messages. | Futures runtime/rules/dashboard/smoke | Category `linear`. |
| Bybit public spot ticker/candles | `ticker`, `recent_candles` | Spot market observation. | No | Runtime catches `BybitApiError`, `ValueError`. | Legacy spot/paper/smoke | BTCUSDT 1m. |
| Bybit public linear klines | `linear_recent_candles`, `linear_historical_candles` | Runtime candles and backtest historical data. | No | Runtime/backtest catches/raises data errors. | Futures runtime/backtest/smoke | Historical source paginates public klines. |
| Bybit private wallet balance | `wallet_balance`; `parse_wallet_balance` | Account/equity/balance inputs. | Yes | Credential load errors, `BybitApiError`, runtime returns `account_data_unavailable`. | Futures ACTIVE, spot demo smoke | Signed REST. |
| Bybit private spot orders | `_create_spot_limit_order`, `_cancel_spot_order`, `_order_realtime`, `_order_history`; `BybitExecutionAdapter` | Spot demo order submission/cancel/reconcile. | Yes | Execution records `UNKNOWN` on adapter errors; maps unknown statuses. | Legacy/demo spot smoke/e2e | Category `spot`. |
| Bybit private linear orders | `_create_linear_limit_order`, `_cancel_linear_order`, `_order_realtime`, `_order_history`; `BybitFuturesExecutionAdapter` | Futures ACTIVE order submission/cancel/reconcile. | Yes | Execution records `UNKNOWN`; environment validation before submit. | Futures ACTIVE/demo smoke | Category `linear`; close orders use reduce-only. |
| Bybit private executions/fills | `_EXECUTION_LIST_PATH`, adapter fill ingestion | Fill facts for futures accounting. | Yes | Bridge records what adapter returns; errors handled by caller. | Futures ACTIVE/accounting smoke | Exact adapter method details exist in `bybit_futures.py`/client. |
| Bybit private positions | `linear_position_list` | ACTIVE account/position state. | Yes | Runtime catches `BybitApiError`/`ValueError`. | Futures ACTIVE | Used to construct `FuturesAccountState`. |
| Azure CLI/Docker Registry/Container App | `scripts/deploy-azure.ps1` | Build, push, deploy dashboard container, health polling. | Yes, CLI auth | Script throws on nonzero exit/failed health. | Deployment | External to trading runtime. |

Credentials/config handling:

- Credential env keys are `BYBIT_API_KEY` and `BYBIT_API_SECRET`.
- `load_bybit_credentials` rejects empty or placeholder values.
- Bybit signing is contained in `src/triggertrade/exchanges/bybit.py`.
- Several safe/public error paths sanitize secret-like words before message/API output.

## 6. Execution and Order Management Inventory

| Topic | Current Evidence | Current As-Is Behavior |
|---|---|---|
| Spot order submission | `ExecutionService.submit_approved_limit_order`, `BybitExecutionAdapter`, `PaperExecutionAdapter` | Creates durable record, validates risk/env/balance/operator state, submits limit order, updates to submitted or unknown. |
| Futures order submission | `FuturesExecutionService.submit_approved_limit_order`, `BybitFuturesExecutionAdapter` | Creates durable futures execution record, validates demo linear env, risk, precision, margin, operator state, submits order, updates status. |
| Execution contracts | `execution/contracts.py`, `execution/futures.py` | Separate spot/paper `TradeIntent`/`RiskDecision` and futures `FuturesTradeIntent`/`FuturesRiskDecision`. |
| Paper execution | `execution/paper.py` | In-memory adapter returns deterministic accepted/reconcile rows; no external calls. |
| Futures execution | `execution/futures.py`, `execution/bybit_futures.py` | Bybit Demo linear only by config checks; supports open/close actions and order status reconciliation. |
| Position lifecycle | `execution/position_lifecycle.py` | Opens positions after execution/reconcile, persists position snapshots, supports monitor protective exits, manual close, close-all, restart recovery. |
| Precision/normalization | `instruments/catalog.py`, `execution/futures.py`, `execution/precision.py`, `position_lifecycle.py` | Instrument metadata normalization exists; futures execution validates price/qty/leverage against instrument metadata; spot precision validates tick/qty/min notional. |
| Fills | `FuturesAccountingBridge`, `FuturesAccountingStore`, `ExecutionStore.save_fill` | Futures bridge records exchange fill rows as accounting fill events; legacy execution store has fill table. |
| Partial fills | `OrderStatus.PARTIALLY_FILLED`, status mapping, lifecycle `_position_status_from_open_record` | Partial-filled statuses are represented; lifecycle treats positive filled quantity as open. |
| Protection | `build_fixed_protective_exit_plan`, `should_trigger_protective_exit` | Fixed take-profit/stop-loss plans are calculated and persisted with positions; monitoring can trigger close. |
| Close handling | `close_position`, `close_all_positions`, reduce-only adapter args | Closes open/closing/unknown positions through generated close intents; close-all records operation. |
| Reconciliation | `ExecutionService.reconcile`, `FuturesExecutionService.reconcile`, `FuturesPositionLifecycleService.reconcile_position/recover_after_restart` | Re-query order status; unknown/not-found paths persist `UNKNOWN`/reconcile state. |
| Idempotency | Stores unique intent/risk/client order ids; deterministic `client_order_id_for_intent` and `futures_client_order_id` | Duplicate create returns existing or blocks depending store/service path. |
| Execution fact persistence | `execution_orders`, `futures_execution_orders`, trace/audit tables | Submission/reconcile facts are durable in SQLite. |

Lifecycle guarantees not implemented or UNCLEAR from code:

- Exchange-level open-order reconciliation breadth beyond known persisted intents is UNCLEAR.
- Fill completeness for all order states depends on adapter/client responses; no independent streaming feed was found.
- Worker/queue-based exactly-once execution was not found.

## 7. Accounting and Financial State Inventory

| Value / State | Code | Computed / Persisted / Exchange / Simulated / UI-only |
|---|---|---|
| Realized P&L | `accounting/futures.py::close_futures_trade`; `FuturesAccountingStore.realized_net_pnl_for_utc_day` | Computed from persisted fills/funding/fees; closed result persisted. |
| Unrealized P&L | `calculate_unrealized_pnl`; `_account_from_bybit`; dashboard read model | Can be computed from mark and persisted position; active account may read exchange `unrealisedPnl`; dashboard renders persisted/exchange-derived fields. |
| Fees | `FuturesFillEvent.fee`, `close_futures_trade`, `estimate_costs` | Persisted from fills for accounting; estimated for risk/backtest/test. |
| Funding | `FuturesFundingEvent`, `_funding_amount`, `FundingEstimate` | Funding events can be persisted; risk uses estimates; smoke notes unavailable unless Bybit returns attributed transaction facts. |
| Equity | `FuturesAccountState`, `EquitySnapshot`, `_account_from_bybit`, `FuturesAccountingStore.record_equity_snapshot` | Exchange-read for ACTIVE account snapshots, simulated for TEST/backtest, persisted as equity snapshots. |
| Drawdown | `calculate_drawdown_snapshot`, analytics metrics | Computed and persisted in equity snapshots; analytics accepts `max_drawdown`. |
| Accounting records | `futures_accounting_*` tables | Persisted in SQLite. |
| Futures accounting | `futures-accounting-v1` | Versioned computation code. |
| Data provenance | `source`, `evidence_source`, `simulation_model_version`, trigger/rules ids | Persisted across fills/closed trades/snapshots/traces. |
| UI rendered totals | `dashboard/read_model.py` | Derived from SQLite rows; not authoritative by itself. |

## 8. Research / Backtest / Demo Inventory

| Capability | Current Code | Current Status | Persistence | UI/API Exposure | Notes |
|---|---|---|---|---|---|
| Research records | `ResearchStore.create_research`, `ResearchService.create_research` | IMPLEMENTED | `research_entities` | `/api/research`, dashboard research pages | Requires exact trigger set/rules version. |
| Research runs | `research_backtest_runs`, `research_demo_runs` | IMPLEMENTED | SQLite | Research APIs/read model | Status transitions exist. |
| Backtests | `BacktestEngine`, `run_backtest`, `BacktestStore` | IMPLEMENTED | SQLite plus accounting store | CLI and research API, but research service needs candles/instrument/config injected | Historical replay is bounded to futures sets. |
| Historical data | `HistoricalKlineCache`, `BybitHistoricalDataSource` | IMPLEMENTED | JSON cache | Backtest CLI/source | Public Bybit Demo linear only. |
| Simulator | `TestFuturesSimulator`, `BacktestFuturesSimulator` | IMPLEMENTED | Futures accounting store | TEST lane/backtest | OPEN_LONG only in test simulator; backtest simulator rejects funding boundary. |
| Comparison | `compare_backtest_runs`, `ResearchService.compare` | PARTIAL | `backtest_comparisons`, closed-trade facts | `/api/research/{id}/compare` | Requires comparable assumptions and overlapping facts. |
| Metrics | `analytics/futures.py`, `_backtest_metrics` | IMPLEMENTED | Persisted metrics JSON and closed trades | Dashboard/read model | Quality warnings are computed. |
| Demo runs | `ResearchService.start_demo_run/stop_demo_run` | PARTIAL | `research_demo_runs` | Research APIs | Start is blocked unless `ResearchDemoIsolation.available` with scopes. |
| Selecting runs | `select_backtest_run`, `select_demo_run` | IMPLEMENTED | Selection flags/current ids | Research APIs | Backtest requires completed/completed-no-trades; demo requires stopped. |
| Promotion/make-active | `ResearchService.make_active` | PARTIAL | Trigger set/rules/research tables, audit | `/api/research/{id}/decision/make-active` | Can promote if code checks pass; blocked reasons persisted. |
| Archiving | `ResearchStore.archive_research` | IMPLEMENTED | `archived_at`, status/decision | Research APIs | Archived research immutable. |
| Version pinning | Backtest/run/research contracts | IMPLEMENTED | Backtest payloads, research ids, rules ids | UI/read model | Exact set/rules version fields are stored. |
| Result persistence | `BacktestStore.save_result`, `FuturesAccountingStore.record_closed_trade` | IMPLEMENTED | SQLite | Dashboard/read model | Immutable-conflict checks in backtest store. |

## 9. Rules / Sets / Triggers Inventory

| Topic | Configuration Model | Runtime Evaluation | UI Representation | Persistence |
|---|---|---|---|---|
| Rule registry | `RuleDefinition`, `RuleVersion`, bootstrap functions in `trigger_set_store.py` | Runtime resolves versions from `TriggerSetStore` | Dashboard trigger catalog/details | `rule_definitions` |
| Trigger registry | TRG-001 and TRG-002 implementation files, registry definitions | `PercentagePriceMoveTrigger`, `RobustVolumeConfirmationTrigger` | Trigger catalog/details/read model formulas | `rule_definitions`, trace rows |
| Trigger sets | `TriggerSetVersion`, memberships, statuses `DRAFT/TESTING/ACTIVE/ARCHIVE` | ACTIVE and TEST futures sets selected per symbol/timeframe | Sets pages and detail routes | `trigger_set_versions`, `trigger_set_memberships`, transitions |
| Versioning | Rule version, set version, rules version, hashes | Runtime resolves exact versions from sets/current rules | History/detail pages | Versioned SQLite rows and current pointers |
| Current/active pointers | Active set via status and unique active index; trading rules current pointer | `get_active_trading_pair`, `get_current_rules_version` | Current rules and ACTIVE set dashboard | `trigger_set_versions`, `trading_rules_current` |
| Coin configuration | `CoinRule`, `TradingRulesVersionDraft.coins` | `_rules_skip_reason`, `coin_rule_for`, symbol validator | Rules editor and catalog search | `trading_rules_coin_rules` |
| Strategy configuration | Legacy `StrategyRuleConfig`; futures strategy pinned in set membership | `BuyCandidateStrategy`, `IntegrationDirectionalFuturesStrategy` | Rule/trigger set detail | Rule definitions and config snapshots |
| Risk configuration | Legacy `RiskRulesConfig`; futures `TradingRulesVersionDraft` and runtime config | `RiskManager`, `FuturesRiskManager`, `DailyLossEvaluator`, position risk config | Rules editor/read model | Trading rules tables, trace risk decisions |
| Rule editing | Dashboard POST `/api/rules/versions` to `TradingRulesService.create_rules_version_from_current` | Current pointer changes only through service/store | Rules page | New immutable version plus current pointer |
| Immutable identities | Hash-based IDs for signals/intents/rules/backtests, unique DB keys | Used for dedupe/replay | Shown in details | SQLite primary/unique keys |
| Bootstrap behavior | `ensure_runtime_registry_initialized`, `bootstrap_current_trigger_sets`, `ensure_initial_version` | Runtime/dashboard/backtest initialize registries | Dashboard depends on bootstrapped state | Writes initial rules/sets/current pointer if absent |

## 10. Current Formula / Threshold Inventory

| Entity | Path | Current Formula / Threshold Location | Configurable? | Hardcoded? | Used At Runtime? | Notes |
|---|---|---|---|---|---|---|
| TRG-001 price move | `src/triggertrade/triggers/percentage_price_move.py` | `(current - previous) / previous * 100 <= threshold_pct` | Yes via `TRIGGERTRADE_TRG_001_THRESHOLD_PCT` | Formula hardcoded | Yes | Default `-1.0`. |
| TRG-001 lookback/window | `config/settings.py`, `percentage_price_move.py` | `lookback_window` must match observation window | Yes | Default hardcoded | Yes | Default `1m`. |
| Stale observation | `market_data/models.py`, config | `observation.is_stale(now)` using `stale_after_seconds` | Yes | Default `60` | Yes | Used by risk/triggers. |
| TRG-002 volume lookback | `triggers/volume_confirmation.py` | `lookback_candles = 60` | Constructor config | Default hardcoded | Yes if set contains TRG-002 | Uses prior candles. |
| TRG-002 median volume | `triggers/volume_confirmation.py` | Median of previous 60 volumes | No direct env | Formula hardcoded | Yes if TRG-002 active/testing | Stores `median_volume_60`. |
| TRG-002 relative volume | `triggers/volume_confirmation.py` | `current_volume / median >= 2.0` | Constructor config | Default hardcoded | Yes if TRG-002 | Default threshold `2.0`. |
| TRG-002 percentile | `triggers/volume_confirmation.py` | `count(previous <= current) / len(previous) * 100 >= 90` | Constructor config | Formula/default hardcoded | Yes if TRG-002 | Default threshold `90`. |
| Regime lookback | `market_data/regime.py` | `REGIME_LOOKBACK_CANDLES` | No env found | Hardcoded | Yes | Exact constant value in code; table inventory notes location. |
| Regime classification | `market_data/regime.py` | Window return, normalized trend, directional persistence thresholds | No env found | Hardcoded | Yes | Threshold constants in same module. |
| Legacy buy price | `strategies/buy_candidate.py` | `current_price * 0.80`, floored to price tick | No | Hardcoded | Legacy spot path | Demo/legacy strategy. |
| Legacy demo quantity | `strategies/buy_candidate.py` | Max of min quantity, notional/price, min-notional quantity | Partly via max demo notional | Formula hardcoded | Legacy spot path | Uses instrument limits. |
| Legacy max demo notional | `config/settings.py`, `risk/manager.py` | Reject if `notional > max_demo_order_notional` | Yes | Default `6` | Legacy spot path | `RSK-001`. |
| Available quote balance | `risk/manager.py` | Reject BUY if balance `< notional` | Input | Formula hardcoded | Legacy spot path | `RSK-003`. |
| Futures minimum net edge | `config/settings.py`, `execution/futures.py` | `expected_gross_move - costs/funding >= minimum_net_edge` | Yes | Default `0.01` | Yes | Can be disabled in trading rules. |
| Futures max position notional | `config/settings.py`, `execution/futures.py` | Reject/sizing cap | Yes | Default `10` | Yes | Runtime/risk. |
| Futures position size pct | `config/settings.py`, `position_lifecycle.py`, `rules/trading.py` | Available capital/equity times pct times leverage, step-normalized | Yes | Default `0.10` | Yes | Rules can version it. |
| Futures aggregate capital cap | `config/settings.py`, `rules/trading.py` | `max_total_position_notional / 100`, capped at `1` for rules bootstrap | Yes | Formula hardcoded | Yes | Default max total notional `30`. |
| Futures max open positions | `config/settings.py`, `rules/trading.py` | Positive integer threshold | Yes | Default `3` | Yes | Rules can enable/disable. |
| Max positions per coin | `rules/trading.py` | Must be `1` when enabled | Through rules API | Validation hardcoded | Yes | Pyramiding not represented as supported. |
| Futures take profit | `config/settings.py`, `position_lifecycle.py`, `rules/trading.py` | Fixed TP pct applied to entry price and tick-normalized | Yes | Default `0.01` | Yes | Dynamic mode exists but runtime rejects active execution. |
| Futures stop loss | `config/settings.py`, `position_lifecycle.py`, `rules/trading.py` | Fixed SL pct applied to entry price and tick-normalized | Yes | Default `0.0025` | Yes | Positive validation. |
| Minimum risk/reward | `config/settings.py`, `position_lifecycle.py`, `rules/trading.py` | Reward/risk must meet threshold | Yes | Default `1.5` | Yes | Used in protective plan validation. |
| Fee/cost rates | `config/settings.py`, `execution/futures.py`, `backtest/engine.py` | Maker/taker fee, spread, slippage, funding costs in cost estimate | Yes | Defaults `0.0002`, `0.00055`, `0`, `0`, `0` | Yes | Backtest treats spread/slippage as bps. |
| Passive ACTIVE price | `services/futures_runtime.py` | `reference - instrument.price_tick * 10`, floored | No env found | Hardcoded | Yes for ACTIVE | TEST uses reference price. |
| Test account capital | `services/futures_runtime.py`, `backtest/engine.py` | `max_position_notional * 10` | Indirect | Formula hardcoded | TEST/backtest | Simulated account state. |
| Daily loss threshold | `services/daily_loss.py`, `rules/trading.py` | `baseline_equity * limit_pct`, block when loss used reaches amount | Rules configurable | Formula hardcoded | Yes if enabled | Baseline from first equity snapshot/account. |
| Analytics sample warning | `analytics/futures.py` | `minimum_closed_trades = 50`, `high_fee_drag_pct = 30` | Policy constructor | Defaults hardcoded | Dashboard/research analytics | Quality warning only. |

## 11. Configuration Inventory

| Config Key / Group | Source | Default | Runtime Consumer | Secret? | Notes |
|---|---|---|---|---|---|
| `TRIGGERTRADE_RUNTIME_MODE` | Env/`.env.example` | `development` | `load_config` | No | Enum: development/test/production. |
| `TRIGGERTRADE_TRADING_MODE` | Env | `paper` | All runtime safety checks | No | `live` currently rejected by `load_config` unless safety branch raises first. |
| `TRIGGERTRADE_LIVE_TRADING_ENABLED` | Env | `false` | Config/runtime/execution safety | No | Must be false for current integration slice. |
| `TRIGGERTRADE_EXECUTION_VENUE` | Env | `local_paper`; `.env.example` says `bybit_demo` | Config/risk/runtime/backtest | No | Futures runtime rejects `LOCAL_PAPER`. |
| `TRIGGERTRADE_ACTIVE_EXECUTION_VENUE` | Env | `bybit_demo_futures` | Futures runtime | No | ACTIVE lane must use this. |
| `TRIGGERTRADE_TEST_EXECUTION_VENUE` | Env | `local_test_simulation` | Futures runtime | No | TEST lane must use this. |
| `TRIGGERTRADE_EXCHANGE` | Env | `paper`; `.env.example` says `bybit` | Config | No | Minimal consumer found. |
| `TRIGGERTRADE_BYBIT_ENV` | Env | `demo` | Config/runtime safety | No | Only `demo` enum exists. |
| `BYBIT_BASE_URL` | Env | `https://api-demo.bybit.com` | Bybit client/runtime safety | No | Non-demo base URL rejected in runtime/smokes. |
| `BYBIT_API_KEY` | Env | none/placeholder in `.env.example` | Private Bybit calls | Yes | Placeholder rejected. |
| `BYBIT_API_SECRET` | Env | none/placeholder in `.env.example` | Private Bybit signing | Yes | Placeholder rejected. |
| `TRIGGERTRADE_MARKET` / `TRIGGERTRADE_CATEGORY` | Env | `spot` for market, `linear` fallback in futures category | Runtime safety/backtest | No | Futures runtime requires linear. |
| `TRIGGERTRADE_WATCHLIST` | Env | empty; `.env.example` `BTCUSDT` | Config | No | Runtime itself is hard-bound to BTCUSDT. |
| `TRIGGERTRADE_RUNTIME_SYMBOL` | Env | `BTCUSDT` | Paper/futures runtime | No | Runtime safety requires BTCUSDT. |
| `TRIGGERTRADE_CANDLE_INTERVAL` | Env | `1` | Runtime/backtest | No | Runtime supports only 1 minute. |
| `TRIGGERTRADE_POLL_INTERVAL_SECONDS` | Env | `30` | Runtime loops | No | Positive integer. |
| `TRIGGERTRADE_RUNTIME_DB_PATH` | Env/Docker | `runtime/triggertrade_paper.sqlite3`; Docker `/app/runtime/triggertrade_paper.sqlite3` | Stores/dashboard/runtime/backtest | No | Shared SQLite path. |
| `TRIGGERTRADE_PAPER_QUOTE_BALANCE` | Env | `100` | Legacy paper runtime | No | Decimal. |
| `TRIGGERTRADE_TRG_001_LOOKBACK_WINDOW` | Env | `1m` | TRG-001 | No | Must match observation. |
| `TRIGGERTRADE_TRG_001_THRESHOLD_PCT` | Env | `-1.0` | TRG-001/bootstrap | No | Decimal. |
| `TRIGGERTRADE_STR_001_ENABLED` | Env | `true` | Legacy strategy config | No | Boolean. |
| `TRIGGERTRADE_MAX_DEMO_ORDER_NOTIONAL` | Env | `6` | Legacy risk | No | Decimal. |
| `TRIGGERTRADE_STALE_AFTER_SECONDS` | Env | `60` | Trigger/risk observations | No | Positive integer. |
| Futures leverage/mode | Env keys `TRIGGERTRADE_FUTURES_LEVERAGE`, `TRIGGERTRADE_FUTURES_MARGIN_MODE`, `TRIGGERTRADE_FUTURES_POSITION_MODE` | `1`, `ISOLATED`, `ONE_WAY` | Futures runtime/rules/execution | No | Leverage validated against catalog metadata. |
| Futures limits/costs | Env keys for minimum edge, max notional, position size, caps, TP, SL, R/R, maker/taker, spread/slippage/funding, demo gross move | Defaults in `FuturesRuntimeConfig` | Futures rules/runtime/backtest | No | Some values copied into initial trading rules. |
| Dashboard host/port | Env keys `TRIGGERTRADE_DASHBOARD_HOST`, `TRIGGERTRADE_DASHBOARD_PORT` | `127.0.0.1`, `8765`; Docker host `0.0.0.0` | Dashboard server | No | Host allowlist is `127.0.0.1` and `0.0.0.0`. |

Secrets handling:

- No actual secret values are printed here.
- `.dockerignore` excludes `.env`, secrets, credentials, local credential directories, runtime DBs, logs, and backup-like artifacts.
- Several stores/read models sanitize metadata/text containing secret-like tokens.

## 12. UI / Backend Coupling

The dashboard is server-rendered/in-process:

- `src/triggertrade/dashboard/__main__.py` uses `BaseHTTPRequestHandler` and `ThreadingHTTPServer`.
- `create_server_from_env` builds stores/services against one SQLite path.
- `render_dashboard` and helpers render HTML directly.
- `src/triggertrade/dashboard/product_ui.py` contains large static/dynamic HTML and browser-side JS strings.
- JSON APIs and HTML routes live in the same handler.

API endpoints found include:

| Endpoint Group | Behavior |
|---|---|
| `/healthz` | Returns `ok`. |
| `/api/rules/current`, `/api/rules/history`, `/api/rules/version/{id}` | Read current/history/exact trading rules. |
| `POST /api/rules/versions` | Create new trading rules version from current after token check. |
| `/api/messages`, `/api/messages/unread-count`, `POST /api/messages/mark-read` | Message listing/read state. |
| `/api/readiness` | Dashboard readiness payload. |
| `/api/research`, `/api/research/{id}`, compare/backtests/demo/archive/make-active routes | Research orchestration and detail. |
| `/api/instruments/search`, `POST /api/instruments/refresh` | Instrument catalog search/refresh. |
| `/api/system-history/export` | Backend-built system history text. |
| Operator POST routes/forms | Pause/resume/close single/close all actions are present in dashboard server code. |

Coupling observations:

- Dashboard read model directly opens SQLite and queries many tables.
- Dashboard action handlers directly call `OperatorStateStore`, `TradingRulesService`, `InstrumentCatalogService`, `ResearchService`, `MessageStore`, and position close helpers.
- Browser does not appear to call Bybit directly; Bybit catalog refresh is backend-mediated.
- Operator control token is process-local and created on server startup.
- UI/backend separation into independent deployable services is not currently represented. Running dashboard and runtime as separate processes is possible via separate entry points sharing SQLite, but the dashboard code is not separated behind a remote API client boundary.

## 13. Restart / Recovery / Idempotency Inventory

| Mechanism | Path | Current Behavior | Durable? | Restart-Safe? | Notes |
|---|---|---|---|---|---|
| Legacy candle checkpoint | `RuntimeStore.checkpoint/get_checkpoint` | Stores last processed candle per symbol/timeframe. | Yes | Yes for legacy path | Used by `PaperTradingRuntime`. |
| Futures lane checkpoint | `RuntimeStore.lane_checkpoint/get_lane_checkpoint` | Stores last processed candle per lane/set/version. | Yes | Yes | Used by futures runtime continuity and recovery. |
| Runtime lifecycle rows | `runtime_candle_lifecycles`, `runtime_lane_lifecycles` | Records statuses per candle or lane/set/candle. | Yes | Yes | Used to avoid already-durable reprocessing. |
| Active checkpoint gap recovery | `FuturesDualLaneRuntime._recover_active_checkpoint_gap` and constants | Attempts bounded recovery from recent/historical candles. | Yes for checkpoint output | Partial/UNCLEAR | Implementation exists; exact completeness depends on available Bybit history and code path. |
| Unresolved execution recovery | `FuturesDualLaneRuntime._recover_active_unresolved`, `ExecutionService.reconcile`, `FuturesExecutionService.reconcile` | Reconciles known unresolved persisted records. | Yes | Partial | Unknown exchange state without local record remains UNCLEAR. |
| Position recovery | `FuturesPositionLifecycleService.recover_after_restart/reconcile_position` | Reconciles open/closing/unknown stored positions. | Yes | Partial | Requires persisted position/execution records. |
| Idempotent execution keys | Execution stores and client order id functions | Unique primary/unique keys prevent duplicates by intent/risk/client id. | Yes | Yes for known intents | SQLite constraints enforce. |
| Immutable backtest runs | `BacktestStore` | Same run/result/comparison payload may be reused; conflicts raise. | Yes | Yes | Hash-based run ids. |
| Research immutability/archive | `ResearchStore` | Archived research cannot mutate. | Yes | Yes | Store checks. |
| Trigger/rules versioning | `TriggerSetStore`, `TradingRulesStore` | Versioned rows and current pointers. | Yes | Yes | Bootstrap fills absent state. |
| Daily loss latch | `DailyLossStore`, `DailyLossEvaluator` | Baseline/latch/notified state stored per UTC day. | Yes | Yes if enabled | Uses persisted equity snapshots or account at evaluation. |
| Heartbeat/health | `RuntimeStore.record_heartbeat`, dashboard `/healthz` | Runtime heartbeat rows; dashboard health endpoint. | Heartbeat yes; token no | Heartbeat yes | `/healthz` only proves server responds. |
| Backup/restore verification | `BackupService` | Creates backups, integrity checks, critical fingerprint. | Yes | Operational | Restore path evidence in tests. |

## 14. Test Inventory

Total test files mapped: 55 (`46` unit, `8` integration, `1` contract).

| Area | Test Paths | What Is Actually Covered | Unit / Integration / Smoke | Notable Gaps |
|---|---|---|---|---|
| Triggers | `tests/unit/test_trg_001_percentage_price_move.py`, `tests/unit/test_trg_002_volume_confirmation.py`, `tests/unit/test_completed_candles.py` | Price move, volume confirmation, candle completion/staleness. | Unit | No live runtime proof by itself. |
| Trigger sets/rules registry | `tests/unit/test_trigger_sets.py`, `tests/unit/test_trading_rules_registry.py`, `tests/unit/test_rule_analytics.py` | Registry bootstrap/versioning, trading rules validation/current pointer, analytics relationships. | Unit | Multi-process contention not covered. |
| Strategy/risk | `tests/unit/test_str_001_buy_candidate_strategy.py`, `tests/unit/test_risk_manager.py`, `tests/unit/test_daily_loss.py` | Legacy strategy, demo risk, daily loss. | Unit | Futures strategy dedicated coverage is mostly via runtime/backtest tests. |
| Execution | `tests/unit/test_execution_service.py`, `tests/unit/test_execution_store.py`, `tests/unit/test_execution_precision.py`, `tests/unit/test_paper_execution.py`, `tests/unit/test_order_state_mapping.py`, `tests/unit/test_bybit_execution_adapter.py` | Store idempotency, submit/reconcile/cancel paths, precision, paper adapter, Bybit request/status mapping. | Unit | Real exchange behavior only in skipped smoke tests. |
| Futures lifecycle/execution/accounting | `tests/unit/test_futures_architecture.py`, `test_futures_runtime_integration.py`, `test_futures_position_lifecycle.py`, `test_futures_accounting.py`, `test_futures_performance_analytics.py` | Futures boundaries, dual-lane runtime, position lifecycle, accounting formulas, analytics. | Unit | Exchange outage/recovery breadth limited to fixtures. |
| Bybit/config/market data | `tests/unit/test_bybit_client.py`, `test_bybit_config.py`, `test_bybit_account.py`, `test_bybit_market_data.py`, `test_instrument_catalog.py` | Client signing/requests/parsing/config/catalog. | Unit | Public/private integration tests are opt-in. |
| Runtime/bootstrap/demo hardening | `tests/unit/test_runtime_bootstrap.py`, `test_paper_runtime.py`, `test_dual_lane_runtime.py`, `test_demo_platform_hardening.py`, `test_startup_smoke.py` | Env/bootstrap paths, paper/dual-lane, readiness/heartbeat hardening, startup. | Unit/integration | Actual long-running soak is opt-in. |
| Dashboard | `tests/unit/test_dashboard_http.py`, `test_dashboard_read_model.py`, `test_dashboard_rules_api.py`, `test_dashboard_research_api.py`, `test_dashboard_messages_api.py`, `test_dashboard_visual_dom.py`, fixture `tests/fixtures/triggertrade_v6_visual_fixture.py` | HTTP/API/read-model/render expectations. | Unit/fixture | Browser-level/e2e dashboard not found. |
| Research/backtest | `tests/unit/test_research_backend.py`, `test_backtest_replay.py`, `tests/integration/test_backtest_smoke.py` | Research records/runs, blocked paths, replay, opt-in public backtest smoke. | Unit/integration smoke | Research demo isolation is not fully implemented. |
| Persistence/ops | `tests/unit/test_trace_store.py`, `test_messages_store.py`, `test_backup_restore.py`, `test_db_integrity_audit.py`, `test_system_history_export.py` | Store schemas, redaction, backup/restore, audit checks, exports. | Unit | Operational restore against production-like DB not proven. |
| Governance/agents/contracts | `tests/unit/test_intraday_governance.py`, `test_agent_governance_contracts.py`, `tests/contract/test_module_boundaries.py` | Governance rules and module boundary constraints. | Unit/contract | Does not prove runtime architecture correctness. |
| External smoke | `tests/integration/test_bybit_demo_smoke.py`, `test_bybit_demo_order_smoke.py`, `test_bybit_demo_futures_lifecycle_smoke.py`, `test_triggertrade_e2e_demo_smoke.py`, `test_triggertrade_demo_soak.py`, `test_public_market_dual_lane_smoke.py` | Opt-in Bybit/demo public/private smoke/soak. | Integration smoke | Skipped unless env flags and credentials are present. |

Heavily tested areas: persistence stores, futures accounting/lifecycle, dashboard APIs/read model, registry/bootstrap, Bybit request/parsing, runtime hardening.

Lightly tested or unclear from test names: actual multi-process SQLite behavior, full dashboard browser interactions, private exchange behavior outside opt-in smoke, independent worker/process recovery, research demo isolation runtime.

## 15. Deployment / Cloud Readiness Inventory

| Capability | Current Status | Evidence | Notes |
|---|---|---|---|
| Docker image | IMPLEMENTED | `Dockerfile` | Python 3.13 slim, package install, dashboard command. |
| Runtime volume | IMPLEMENTED | `VOLUME ["/app/runtime"]` | SQLite runtime DB expected under `/app/runtime`. |
| Dashboard host binding | IMPLEMENTED | Docker env `TRIGGERTRADE_DASHBOARD_HOST=0.0.0.0`; dashboard allowlist | Local default remains `127.0.0.1`. |
| Health endpoint | IMPLEMENTED | `/healthz`, Docker `HEALTHCHECK` | Health only checks dashboard response. |
| Config via environment | IMPLEMENTED | `config/settings.py`, Docker env, `.env.example` | Secrets expected via env for private Bybit. |
| Local filesystem dependencies | IMPLEMENTED/ASSUMED | SQLite DB path, `runtime/history`, backups | Container has `/app/runtime`; history/backups also filesystem based. |
| SQLite assumptions | IMPLEMENTED | Store modules use `sqlite3.connect(path)` | Shared-process/process concurrency beyond SQLite defaults not characterized. |
| Secrets assumptions | PARTIAL | `.dockerignore`, env credential loader | No secret manager integration found in code. |
| Process model | PARTIAL | Docker CMD runs dashboard only | Runtime worker is not started by Dockerfile. |
| Azure deployment script | IMPLEMENTED | `scripts/deploy-azure.ps1` | Hardcoded resource group, ACR, app name, custom domain. |
| Azure-specific coupling | IMPLEMENTED | Deploy script Azure CLI calls | Infrastructure script targets one named Azure setup. |

## 16. Legacy / Temporary / Demo-Only Candidates

| Classification | Path | Evidence |
|---|---|---|
| DEMO_ONLY | `src/triggertrade/strategies/futures_directional.py` | Docstring: `STR-FUT-001 demo-only futures directional integration strategy`; class docstring says reduced integration strategy. |
| DEMO_ONLY | `src/triggertrade/risk/manager.py` | Docstring: minimal deterministic risk manager for demo e2e slice; rule names max demo order notional. |
| DEMO_ONLY | `.env.example` | Comment: demo-only deterministic vertical-slice config. |
| DEMO_ONLY | `scripts/bybit_demo_smoke.py` | Manual Bybit Demo read-connectivity smoke. |
| DEMO_ONLY | `scripts/bybit_demo_order_smoke.py` | Opt-in Bybit Demo Spot order lifecycle smoke. |
| DEMO_ONLY | `scripts/bybit_demo_futures_smoke.py` | Opt-in Bybit Demo linear perpetual lifecycle smoke. |
| DEMO_ONLY | `scripts/bybit_demo_futures_lifecycle_smoke.py` | Opt-in Bybit Demo futures position lifecycle smoke. |
| DEMO_ONLY | `scripts/bybit_demo_futures_accounting_smoke.py` | Opt-in Bybit Demo futures accounting smoke. |
| DEMO_ONLY | `scripts/triggertrade_e2e_demo_smoke.py` | Opt-in TriggerTrade e2e demo smoke. |
| DEMO_ONLY | `scripts/triggertrade_demo_soak.py` | Opt-in bounded Bybit Demo soak harness. |
| LOCAL_ONLY | `src/triggertrade/dashboard/__main__.py` | Module docstring: local read-only dashboard; local token; direct SQLite store access. |
| LOCAL_ONLY | `src/triggertrade/services/test_futures_simulator.py` | Docstring: isolated deterministic TEST-lane futures simulator; no exchange calls. |
| LOCAL_ONLY | `scripts/paper_runtime_smoke.py` | Opt-in continuous paper runtime smoke with local DB. |
| LIKELY_TEMPORARY | `src/triggertrade/services/regime_smoke.py` | Smoke executable under services. |
| LEGACY_CANDIDATE | `src/triggertrade/services/dual_lane_runtime.py` | Earlier dual-lane runtime exists while current `services/runtime.py` builds `FuturesDualLaneRuntime`; active entry point not found. |
| LEGACY_CANDIDATE | `src/triggertrade/services/runtime.py::PaperTradingRuntime` | Spot paper runtime class exists but module `main` builds futures runtime. |
| LEGACY_CANDIDATE | `src/triggertrade/execution/bybit.py` and `src/triggertrade/persistence/execution_store.py` | Spot order path exists alongside futures order path; current futures runtime uses futures store/service. |
| UNCLEAR | `src/triggertrade/exchanges/contracts.py` | Generic exchange interface exists; no concrete non-Bybit adapter found. |
| UNCLEAR | `src/triggertrade/governance/experiment.py` | Governance/evidence support exists; runtime criticality not clear from current code path. |

## 17. Existing Assets Likely Worth Preserving

| Asset | Path | Why It Appears Reusable From Engineering Evidence |
|---|---|---|
| SQLite store boundaries | `src/triggertrade/persistence/*.py` | Stores are separated by domain, have schemas, primary/unique keys, and tests. |
| Trace/audit model | `src/triggertrade/persistence/trace_store.py` | Provides durable trigger/strategy/risk/audit records with metadata redaction. |
| Futures accounting contracts | `src/triggertrade/accounting/futures.py` | Pure deterministic calculations with explicit source/version fields and tests. |
| Futures execution contract/service | `src/triggertrade/execution/futures.py` | Separates intent/risk/execution service and environment validation. |
| Position lifecycle service | `src/triggertrade/execution/position_lifecycle.py` | Encapsulates open/close/protection/recovery and persists snapshots/events. |
| Instrument catalog | `src/triggertrade/instruments/catalog.py`, `persistence/instrument_catalog_store.py`, `services/instrument_catalog.py` | Parses exchange constraints into reusable validation/normalization metadata. |
| Runtime checkpoints/lifecycles | `src/triggertrade/persistence/runtime_store.py` | Captures restart-relevant candle/lane progress and status. |
| Versioned rules/sets | `trigger_sets`, `rules`, related stores | Current pointers plus immutable version records support repeatability. |
| Backtest store/engine contracts | `src/triggertrade/backtest/*` | Backtest run ids include assumptions/version/cache hash; immutable persistence checks. |
| Dashboard read model | `src/triggertrade/dashboard/read_model.py` | Centralizes many read projections from persisted facts. |
| Backup/restore verification | `src/triggertrade/services/backup_restore.py` | Operational fingerprint/integrity/secret-scan checks exist. |
| Test suite | `tests/` | Broad unit coverage across core stores, runtime, dashboard, execution, accounting, research. |
| Docker/Azure assets | `Dockerfile`, `scripts/deploy-azure.ps1` | Dashboard container and concrete deployment script exist. |

## 18. Current End-to-End Flows

| Flow | Entry Point | Sequence of Modules | Persistence Touched | External APIs Touched | Final Outputs |
|---|---|---|---|---|---|
| Futures ACTIVE runtime | `python -m triggertrade.services.runtime` | bootstrap/config -> Bybit client -> `FuturesDualLaneRuntime` -> catalog/account/candles -> regime/triggers/rules/strategy/risk/daily loss/operator -> position lifecycle -> futures execution -> accounting bridge | Runtime, trace, trigger set, trading rules, operator, messages, catalog, futures execution, positions, accounting, daily loss | Bybit public linear instruments/klines; private wallet/positions/orders/executions | SQLite facts, Bybit Demo orders, heartbeats, dashboard-visible state. |
| Futures TEST lane | Same runtime | Same market event -> testing sets -> triggers/rules/strategy/risk -> `TestFuturesSimulator` | Runtime, trace, accounting closed trades/fills | Bybit public market data only from shared runtime event | TEST evidence and simulated closed trades. |
| Legacy paper runtime | `PaperTradingRuntime.run_forever` class | Bybit spot metadata/candles -> TRG-001 -> `BuyCandidateStrategy` -> `RiskManager` -> `ExecutionService` -> `PaperExecutionAdapter` | Runtime, trace, legacy execution | Bybit public spot only | Local paper execution rows. |
| Backtest CLI | `python -m triggertrade.backtest` | config/bootstrap -> historical source/cache -> `BacktestEngine` -> triggers/regime/strategy/risk -> simulator -> analytics | Backtest, trace, futures accounting, execution store reads/writes | Bybit public historical klines if cache miss | Backtest result row and metrics. |
| Research workflow | Dashboard API `/api/research*` | Dashboard handler -> `ResearchService` -> stores/backtest runner/analytics | Research, trace, messages, backtest, accounting | Usually none; backtest may require supplied candles in service path | Research records/runs/selection/comparison/promotion decisions. |
| Dashboard read path | `python -m triggertrade.dashboard` GET routes | Handler -> `DashboardReadModel` -> SQLite queries -> HTML/JSON render | Read-only SQLite access | None directly except instrument refresh route | HTML pages and JSON payloads. |
| Dashboard operator control | Dashboard POST routes | Handler token check -> operator store and/or position close helpers | Operator audit/state, positions, executions, messages | Bybit private order APIs for close actions if adapter path available | Pause/resume/close state changes and JSON/redirect responses. |
| Instrument refresh | `POST /api/instruments/refresh`, script smoke | Dashboard/script -> `InstrumentCatalogService` -> Bybit client -> store | Instrument catalog/refreshes, messages on failure | Bybit public linear instruments | Catalog rows and refresh status. |
| Backup/restore | Service/tests | `BackupService` -> SQLite backup/integrity/fingerprint/manifest | DB copy, manifests, backup dir | None | Backup/restore verification artifacts. |

## 19. Highest-Risk As-Is Technical Areas

1. Single SQLite file shared by runtime, dashboard, research, backtest, and scripts. Evidence: most stores default to `runtime/triggertrade_paper.sqlite3`; dashboard and runtime can run as separate processes.
2. Dashboard/backend in-process coupling. Evidence: `DashboardHandler` constructs/calls stores/services directly and renders HTML in the same module/process.
3. Runtime process separation is manual. Evidence: Docker starts dashboard only; runtime has a separate entry point but no supervisor/worker orchestration in repo.
4. Legacy/demo and current futures paths coexist. Evidence: spot `PaperTradingRuntime`, `DualLaneRuntime`, legacy `ExecutionStore` and Bybit spot adapter remain beside futures runtime/execution.
5. Local filesystem persistence assumptions. Evidence: runtime DB, history cache, smoke DBs, backup dirs, `.env` loading, Docker volume.
6. Exchange reconciliation appears bounded to locally persisted known orders/positions. Evidence: services reconcile by stored intent/order ids; broad exchange-state discovery for unknown local state is UNCLEAR.
7. Research demo isolation is partial. Evidence: `ResearchDemoIsolation.available` defaults false and service blocks demo starts without isolation scope.
8. ACTIVE runtime is hard-bound to Bybit Demo BTCUSDT linear 1-minute candles. Evidence: `_validate_safe_config` rejects other symbol/category/interval/base URL.
9. Operator dashboard token is process-local. Evidence: `secrets.token_urlsafe(24)` in `DashboardServer.__init__`; restart invalidates token.
10. Large dashboard read model/server modules concentrate many responsibilities. Evidence: `dashboard/read_model.py` and `dashboard/__main__.py` contain many projections, API handlers, actions, and render helpers.

## 20. Unknowns / Questions for Alignment Phase

- Which current executable path is intended to be the operational default outside local development?
- Should legacy spot/paper modules remain active, compatibility-only, or be retired?
- What state ownership should exist between runtime, dashboard, research, and backtest when run concurrently?
- What restart/recovery guarantees are required for exchange orders or positions that exist on Bybit but are missing locally?
- What production deployment shape is intended for runtime plus dashboard, since the current Dockerfile runs dashboard only?
- What should Research Demo isolation mean operationally, and should it use separate DB/account/execution scope?
- Which formulas/thresholds are canonical versus demo/bootstrap values?
- Which dashboard actions are intended for local-only use versus remotely deployed operation?
- Whether SQLite remains acceptable for shared runtime/dashboard/backtest access under expected concurrency is UNKNOWN.
- Whether historical cache and backups require retention/rotation/encryption policies is UNKNOWN.

## Final Inventory Counts

| Count | Value |
|---|---:|
| Modules/files inventoried in backend/config/script scope | 99 |
| Persistence stores/mechanisms identified | 16 |
| External integration boundaries identified | 11 |
| Runtime entry points identified | 15 |
| Formula/threshold locations inventoried | 26 |
| Test files mapped | 55 |
| Legacy/demo/local-only candidates identified | 19 |

