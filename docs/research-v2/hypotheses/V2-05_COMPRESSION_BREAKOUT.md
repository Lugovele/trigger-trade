# V2-05 COMPRESSION_BREAKOUT

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | A FREQUENCY; B VOLATILITY |
| Priority | MUST TEST FIRST |
| Hypothesis | Выход из сжатия волатильности с ускорением turnover даёт отдельное семейство возможностей. |
| Current behavior | В архиве нет самостоятельного широкого compression-breakout теста. |
| Proposed change | Новый range-breakout вместо добавления ещё одного фильтра старому Set. |
| Parameter values | `{"LONG": "completed 5m close>prior range high+buffer", "RVOL5_min": 1.5, "SHORT": "completed 5m close<prior range low-buffer", "breakout_buffer_ATR15": 0.1, "compression": "ATR15(14)/median preceding 96 completed ATR15 values <=0.80 at prior completed 15m bar", "range": "preceding 12 completed 5m bars, excluding breakout bar", "reset": "close back within prior range then a new confirmed breakout", "trigger_validity_minutes": 15, "turnover_acceleration_min": 1.2}` |
| Economic mechanism | Тест продолжения после расширения диапазона, а не числа пересечений одного threshold. |
| Expected effect on frequency | Новый поток, возможно редкий; частота не предполагается. |
| Expected effect on expectancy | Проверка payoff expansion против ложных пробоев. |
| Expected effect on risk | Gap/slippage на выходах; пропущенные post-only входы. |
| Expected effect on capital utilization | Зависит от passive retest fill; chasing запрещён. |
| 7D test | J5 G0; если редкость исключает target, не направлять автоматически на 30D. |
| 7D pass | Тот же economic feasibility gate; при 10 fills и Q750 необходим e>=0.6222% для нижней 7D цели. |
| 7D fail | Нет своевременных fills либо необходимая expectancy превышает attainable net win geometry. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `[]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
