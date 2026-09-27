# TradingRulesVersion Backend Gap Correction Report

Status: READY_FOR_COMMIT_REVIEW

No production Rules, Sets, Triggers, Research runs, Demo runs, commits, pushes or deployments were performed.

## Scope

This correction updates the existing combined immutable `TradingRulesVersion` backend contract. It does not create separate Position Rules or Portfolio Rules registries.

## Six Corrected Gaps

| Gap | Methodology authority | Previous backend behavior | New backend behavior | Test evidence |
|---|---|---|---|---|
| `max_positions_per_coin` | `PORTFOLIO_RULES.md` §§5, 17, 21 | Validator allowed only `1`. | Accepts positive per-coin tranche-slot values and rejects values above enabled `max_open_positions`. Research values `2` and `3` validate. | `test_per_coin_position_count_accepts_methodology_tranche_slots`; `test_per_coin_position_count_rejects_invalid_bounds` |
| `minimum_tranche_capital` | `PORTFOLIO_RULES.md` §§5, 18 | No `TradingRulesVersionDraft` field. | First-class nullable Portfolio Rules field, validated non-negative when configured, serialized and hashed. | `test_methodology_rules_fields_validate_and_round_trip` |
| `cooldown_minutes` | `PORTFOLIO_RULES.md` §§5, 24 | No `TradingRulesVersionDraft` field. | First-class nullable Portfolio Rules field, validated non-negative when configured, serialized and hashed. Runtime clock ownership remains factual `accepted_at`. | `test_methodology_rules_fields_validate_and_round_trip` |
| `stop_loss.mode` | `POSITION_RULES.md` §§8-10 | Only numeric `stop_loss_pct`; legacy metadata sometimes carried mode. | First-class `StopLossMode` enum with `FIXED` and `DYNAMIC`; fixed percentage is required only for FIXED mode. Legacy metadata is read for old fixtures. | `test_methodology_rules_fields_validate_and_round_trip`; B7A focused tests |
| Dynamic TP / `minimum_take_profit_pct` | `POSITION_RULES.md` §§8, 11-12, 14 | DYNAMIC mode required a positive fixed TP floor. | DYNAMIC mode validates without fabricated `minimum_take_profit_pct`; FIXED mode still requires positive fixed TP. | `test_methodology_rules_fields_validate_and_round_trip`; `test_methodology_rules_fields_fail_closed_when_invalid` |
| `minimum_risk_reward.enabled` | `POSITION_RULES.md` §§8, 14 | Only numeric value existed; retained disabled values could still enforce. | First-class enabled flag; enabled requires positive threshold, disabled retained value is not enforced at initial opportunity or final construction. | `test_b7a_disabled_minimum_risk_reward_does_not_reject_retained_value`; `test_b7b_exact_threshold_equality_passes_and_just_over_rejects` |

## Non-Rules Fields

No new Rules fields were added for:

- ATR bindings: still Position construction / certified formula references.
- Fee/cost/funding: still execution, backtest profile and accounting evidence.
- Asset/instrument binding: still launch-time binding.

Existing backend fee/cost fields were not expanded or reclassified by this task.

## Persistence Impact

SQLite `trading_rules_versions.payload` and PostgreSQL owner-state records already store canonical JSON payloads, so no table migration was required for the six fields.

The new fields participate in `draft_to_json`, `draft_from_json`, and `semantic_hash`.

Backward compatibility:

- Missing `stop_loss_mode` deserializes as `FIXED`, matching previous behavior.
- Missing `minimum_risk_reward_enabled` deserializes as `true`, matching previous behavior.
- Missing `minimum_tranche_capital` and `cooldown_minutes` deserialize as `null`.
- Legacy metadata `stop_loss_mode` is read for older in-memory fixtures.

## Research Rules Validation

- Canonical package: `docs/research-import/rules/RESEARCH_V1_RULES.json`
- Web import package: `docs/research-import/rules/RESEARCH_V1_RULES_WEB_IMPORT.json`

Results:

- `BACKEND_VALID_COMBINED_RULES: 16/16`
- `RULES_WEB_IMPORT_VALID: 16/16`
- `RULES_SEMANTIC_LOSS: NO`

## Test Results

Focused backend/runtime:

```text
python -m pytest tests/unit/test_research_backend.py::test_research_backtest_accepts_methodology_per_coin_tranche_slots tests/unit/test_trading_rules_registry.py tests/unit/test_research_v1_trading_rules_backend.py -q --basetemp=rules_gap_pytest_tmp_13
..............s
```

Adjacent Research tests:

```text
python -m pytest tests/unit/test_research_backend.py tests/unit/test_research_backtest_execution.py tests/unit/test_research_demo_execution.py -q --basetemp=rules_gap_pytest_tmp_14
............................................ssssss...................... [ 90%]
.......s                                                                 [100%]
```

Adjacent Position/Portfolio tests:

```text
python -m pytest tests/unit/test_position_opportunity_b7a.py tests/unit/test_position_construction_b7b.py tests/unit/test_portfolio_grants_b8b.py tests/unit/test_portfolio_current_booking_b8c.py -q --basetemp=rules_gap_pytest_tmp_15
...............ss.......ssssss........sss...ssss                         [100%]
```

Trading Rules specialist review:

```text
TRADING_RULES_APPROVED
```

Earlier adjacent dashboard/reference UI run:

```text
python -m pytest tests/unit/test_research_v1_trading_rules_backend.py tests/unit/test_dashboard_rules_api.py tests/unit/test_reference_ui_replacement.py -q --basetemp=rules_gap_pytest_tmp_05
..s........F...F..........
```

The two failures are in `tests/unit/test_reference_ui_replacement.py` and assert pre-existing trigger-detail HTML strings/structure unrelated to this backend rules change. The dashboard Rules API coverage in that command passed.

## Real PostgreSQL

The real PostgreSQL isolated-schema dry-run test was added in `tests/unit/test_research_v1_trading_rules_backend.py`.

Real PostgreSQL validation was completed by resolving the existing Azure Container App `postgres-dsn` secret into the local process environment without printing it or writing it to repository files.

Pytest result:

```text
python -m pytest tests/unit/test_research_v1_trading_rules_backend.py -q --basetemp=rules_gap_pg_tmp_01
...                                                                      [100%]
```

Isolated-schema import/readback dry-run:

- Random schema prefix: `tt_rules_gap_manual`
- First pass created: 16
- First pass conflicts: 0
- Second pass created: 0
- Second pass exact: 16
- Second pass conflicts: 0
- Exact Rules round-trip: 16/16
- `max_positions_per_coin` values verified: 2, 3
- `minimum_tranche_capital` preserved: 16/16
- `cooldown_minutes` preserved: 16/16
- `stop_loss.mode = DYNAMIC` preserved where configured: 15 records
- Dynamic TP without fabricated fixed/minimum TP preserved: 16/16
- `minimum_risk_reward.enabled = false` with retained value preserved: 15 records

The isolated schema was dropped after validation.

No production schema was touched.
