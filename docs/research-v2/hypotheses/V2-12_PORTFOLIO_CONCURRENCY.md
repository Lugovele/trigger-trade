# V2-12 PORTFOLIO_CONCURRENCY

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | G PORTFOLIO UTILIZATION |
| Priority | LOW PRIORITY UNTIL MEASURABLE BLOCKS |
| Hypothesis | Slot limits менять только когда реальные одновременные profitable opportunities конкурируют. |
| Current behavior | Baseline Portfolio не блокирует; увеличение slot count снижает tranche. |
| Proposed change | Shared risk pool; maxslots тестировать при неизменном order sizing. |
| Parameter values | `{"gross_exposure_cap_fraction": 1.8, "initial_max_open": 3, "initial_per_coin": 1, "margin_cap_fraction": 0.6, "max_open_positions": [2, 3], "max_positions_per_coin": [1, 2], "order_size_not_divided_by_slots": true, "same_episode_duplication": false, "total_stop_risk_cap_fraction": 0.015}` |
| Economic mechanism | Устранить реальный капиталовый bottleneck, не искусственно повысить trading count копиями. |
| Expected effect on frequency | Вырастет только если есть blocked independent opportunities. |
| Expected effect on expectancy | Не меняет signal edge; зависит от предопределённого order priority. |
| Expected effect on risk | Рост concentration и correlated loss. |
| Expected effect on capital utilization | Может увеличить turnover; average time utilization не самоцель. |
| 7D test | После положительного наполненного потока один 2x2 concurrency test с неизменным Q rule. |
| 7D pass | Дополнительный чистый account PnL оправдан без удвоения одного события и risk breaches. |
| 7D fail | Нет блокировок либо больший slot count просто дробит капитал. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["measurable_concurrency_blocks_required"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
