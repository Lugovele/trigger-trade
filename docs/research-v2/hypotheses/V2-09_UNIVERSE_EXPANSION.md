# V2-09 UNIVERSE_EXPANSION

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | I UNIVERSE |
| Priority | SECONDARY |
| Hypothesis | Дополнительные инструменты увеличат различные прибыльные возможности, а не только BTC-копии. |
| Current behavior | Фактический поток AVAX/SUI/PEPE; остальные в config не равны проверенным рынкам. |
| Proposed change | Парное расширение тройки до исходных десяти при том же signal, параметрах и общем risk budget. |
| Parameter values | `{"base": ["AVAXUSDT", "SUIUSDT", "PEPEUSDT"], "expanded": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SUIUSDT", "PEPEUSDT", "AVAXUSDT", "LINKUSDT", "BNBUSDT"], "fixed_equal_allocation": false, "risk_budget_common": 0.015, "single_margin_cap_per_coin": 0.33}` |
| Economic mechanism | Больше независимых по времени/структуре эпизодов; численность сама не гарантирует независимость. |
| Expected effect on frequency | Не закладывать автоматически 10/3 кратность. |
| Expected effect on expectancy | Нужна проверка incremental net по новым инструментам. |
| Expected effect on risk | Одновременные коррелированные losses; лимит basket-risk общий. |
| Expected effect on capital utilization | Более частое использование свободного капитала без static 70% неиспользуемых budgets. |
| 7D test | Один выживший signal: 3 vs10 symbols, тот же период; не выбирать монеты после просмотра PnL. |
| 7D pass | Добавленные fills и combined net помогают пройти target без нарушения risk. |
| 7D fail | Увеличились только коррелированные сигналы/fees либо экономическая нижняя граница не достигнута. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `[]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
