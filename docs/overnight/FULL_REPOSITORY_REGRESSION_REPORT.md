# Full Repository Regression Report

## Baseline

- Branch: `main`
- HEAD: `584ec2207dbbc4a7c5b3b68971d6a236db152e6b`
- Python: `Python 3.13.3`
- Pytest config: `pyproject.toml` defines `testpaths = ["tests"]`, `pythonpath = ["src"]`, and `addopts = "-q -p no:cacheprovider"`.
- Working tree before this report: no tracked application/test/methodology diff was present; existing unrelated untracked artifacts were present, including `.tt-e2e/`, `.tt-tmp/`, frontend snapshots, zipped methodology/spec artifacts, and `docs/research-v1/`.
- `git status --short` emitted many pre-existing permission-denied warnings for old temporary pytest/review directories, then listed the untracked artifacts above.
- Testing was performed against the current repository state. No cleanup, reset, production data mutation, Demo interaction, or Backtest interaction was performed.

## Test Summary

| Command | Passed | Failed | Skipped | XFailed | XPassed | Duration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `python -m pytest --basetemp "$env:TEMP\tt-full-repo-regression"` | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| `python -m pytest --basetemp C:\Users\Public\tt-full-repo-regression` | 1091 | 8 | 134 | 0 | 0 | 358.62s |
| `python -m pytest --basetemp C:\Users\Public\tt-runtime-recovery-regression tests\unit\test_futures_runtime_integration.py tests\unit\test_market_regime_v1.py tests\unit\test_postgres_runtime_store.py tests\unit\test_research_demo_execution.py tests\unit\test_trading_worker.py tests\unit\test_durable_messages.py tests\unit\test_research_backtest_execution.py tests\unit\test_backtest_replay.py tests\unit\test_research_backend.py tests\unit\test_dashboard_research_api.py` | 180 | 0 | 13 | 0 | 0 | 179.80s |

The first full-suite attempt reached 100% progress but crashed during pytest temp cleanup with `PermissionError: [WinError 5]` against `%TEMP%\tt-full-repo-regression`, before emitting a numeric summary. It was rerun with an ASCII `C:\Users\Public` basetemp and completed normally.

## Failure Analysis

### tests/e2e/test_dashboard_user_journeys.py::test_e2e_research_create_detail_backtest_demo_compare_export_and_reject

- Classification: `TEST_DEFECT`
- Evidence: after clicking `Run Demo 7D`, the test expected `rdm-` in `#demo-body`, but the UI still rendered `No runs.`
- Suspected cause: the e2e fixture creates a local dashboard server without a canonical Research Demo worker handoff. Current Demo semantics require canonical worker handoff; the test appears to assert older immediate local Demo visibility.
- Relation to current code changes: not implicated by the focused runtime/recovery regression, which passed.

### tests/integration/test_v1_2_15_canonical_backend_flow.py::test_b13_fail_closed_paths_do_not_reach_legacy_demo_or_position_api

- Classification: `CURRENT_REGRESSION`
- Evidence: a subprocess importing `triggertrade.services.owner_dispatch` and `triggertrade.services.trading_worker` loaded forbidden legacy modules: `triggertrade.execution.bybit` and `triggertrade.execution.position_lifecycle`.
- Suspected cause: backend/worker imports now pull execution modules earlier than this canonical boundary test allows.
- Relation to current code changes: plausibly related to recent worker/runtime wiring and should be reviewed before release.

### tests/unit/test_container_runtime.py::test_deploy_script_can_target_web_worker_and_scheduler_roles

- Classification: `TEST_DEFECT`
- Evidence: test expects `"trading-worker" = "triggertrade-trading-worker-centralus"`; `scripts/deploy-azure.ps1` now contains `"trading-worker" = "triggertrade-worker-uae"`.
- Suspected cause: stale topology expectation; user-provided production context identifies current worker as `triggertrade-worker-uae`.
- Relation to current code changes: not a runtime recovery regression.

### tests/unit/test_container_runtime.py::test_github_workflow_has_cloud_build_only_mode_before_deploy

- Classification: `TEST_DEFECT`
- Evidence: test expects `triggertrade-trading-worker-centralus`; `.github/workflows/deploy-production.yml` now contains `TRADING_WORKER_APP: triggertrade-worker-uae`.
- Suspected cause: stale topology expectation.
- Relation to current code changes: not a runtime recovery regression.

### tests/unit/test_dashboard_messages_api.py::test_operator_actions_create_factual_user_messages

- Classification: `TEST_DEFECT`
- Evidence: close-one form request without an `idempotency_key` expected `503`, but current handler returned `400`.
- Suspected cause: stale fixture/request shape; other dashboard close-one tests include an idempotency key and exercise the no-bridge `503` path.
- Relation to current code changes: not implicated by the recent runtime/recovery focused suite.

### tests/unit/test_futures_performance_analytics.py::test_readiness_uses_accounting_closed_trades_when_tables_exist

- Classification: `TEST_DEFECT`
- Evidence: `DashboardReadModel(db).list_test_set_evidence()` returned no rows; test indexed `[0]`.
- Suspected cause: stale assertion that a TESTING candidate set exists. Current approved selectability/registry cleanup archives `triggertrade-futures-candidate@v2-test`.
- Relation to current code changes: not a new recovery regression.

### tests/unit/test_futures_performance_analytics.py::test_dashboard_performance_uses_accounting_metrics_and_no_frontend_math

- Classification: `TEST_DEFECT`
- Evidence: `list_baseline_comparisons()` returned no rows; test indexed `[0]`.
- Suspected cause: stale expectation that a TESTING candidate set participates in current comparison.
- Relation to current code changes: not a new recovery regression.

### tests/unit/test_intraday_governance.py::test_dashboard_readiness_and_pause_controls_render

- Classification: `TEST_DEFECT`
- Evidence: `model.list_test_set_evidence()` returned no rows; test indexed `[0]`.
- Suspected cause: stale expectation that a TESTING set exists after bootstrapping.
- Relation to current code changes: not a new recovery regression.

## Recent Runtime/Recovery Regression

- Demo recovery: `PASS` in focused regression.
- Checkpoint recovery: `PASS` in focused regression.
- Market-regime replay/idempotency: `PASS` in focused regression covering futures runtime integration, market regime, PostgreSQL runtime store, Research Demo execution, and trading worker.
- Owner-state projection: `PASS` in focused regression.
- Persistence immutability: `PASS` in focused regression.
- Worker execution: `PASS` in focused regression.
- Backtest path: `PASS` in focused regression.
- Environment isolation: `PASS` for local/test coverage; no production Demo, Backtest, Azure, PostgreSQL, or Bybit mutation was performed.

## Static Checks

- `python -m compileall src\triggertrade`: `PASS`
- `git diff --check`: `PASS`
- Repo-native lint/type/schema checks: no configured lint/type tool was found in `pyproject.toml`; no new lint/type system was introduced.

## Repository Integrity Findings

1. `CURRENT_REGRESSION`: canonical backend import-boundary test detects `triggertrade.execution.bybit` and `triggertrade.execution.position_lifecycle` loaded by importing `owner_dispatch` and `trading_worker`.
2. `TEST_DEFECT`: multiple tests still assume an ordinary current TESTING candidate set after the approved cleanup made `triggertrade-futures-candidate@v2-test` archived/non-selectable.
3. `TEST_DEFECT`: container runtime tests still expect the old Central US trading-worker app name instead of the current UAE worker name.
4. `TEST_DEFECT`: one dashboard message API test omits the now-required close-one idempotency key and therefore hits `400` before the intended no-bridge `503` assertion.
5. `TEST_DEFECT`: one e2e Research Demo journey appears not to provide the canonical Demo handoff fixture required by current Demo semantics.

No broken imports were found by `compileall`. No tracked application code, tests, methodology, Trigger, Set, Trading Rules, or Research package files were changed by this verification pass.

## Production Safety

- Production PostgreSQL mutated: `NO`
- Azure resources mutated: `NO`
- Bybit mutated: `NO`
- Deployed: `NO`
- Existing BACKTEST_90D interacted with: `NO`
- Existing Research Demo recovery interacted with: `NO`
- Git staged/committed/pushed: `NO`

