# V2-04 MOMENTUM_CONTINUATION

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | B SIGNAL QUALITY; J TREND |
| Priority | MUST TEST FIRST |
| Hypothesis | Продолжение импульса с трендом и относительным объёмом даёт более высокий net edge. |
| Current behavior | Отбор Set меняет исходы, но выборка слишком мала для оценки качества. |
| Proposed change | V2-03 плюс trend/RVOL, без BTC veto в первом запуске. |
| Parameter values | `{"BTC_filter_initial": false, "RVOL5_min_initial": 1.2, "RVOL_grid": [1.0, 1.2, 1.5], "base_signal": "V2-03 initial", "trend_long": "EMA20(15m)>EMA50(15m) and return15>0", "trend_short": "EMA20(15m)<EMA50(15m) and return15<0"}` |
| Economic mechanism | Убирать импульсы против локального движения и без повышенного оборота. |
| Expected effect on frequency | Ниже J3; сокращение допустимо только с достаточным ростом expectancy. |
| Expected effect on expectancy | Гипотеза повышения, не факт. |
| Expected effect on risk | Корреляция с рыночным трендом; whipsaw. |
| Expected effect on capital utilization | Меньше слабых заявок, но риск простоя. |
| 7D test | J4 против J3 на том же G0; J7 отдельно меняет только stop family. |
| 7D pass | Общий target gate после risk-constrained sizing; достаточное число новых filled episodes. |
| 7D fail | PF растёт, но turnover падает так, что даже допустимый scaling не достигает цели. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["V2-03"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
