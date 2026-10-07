# V2-02 STOP_GEOMETRY

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | D STOP; C ENTRY |
| Priority | MUST TEST FIRST |
| Hypothesis | Свежая структурная геометрия или отдельный ATR-stop дадут иной trade set, чем слепое расширение стопа. |
| Current behavior | База 23/32 STOP_SL_TOO_WIDE; fixed 1% даёт 23 approves, но имеющийся R014 path зависим от дефектов/цензуры. |
| Proposed change | Конкурирующие G0 и G1. Не срезать структурный stop внутрь invalidation. |
| Parameter values | `{"ATR_only_grid": [0.75, 1.0, 1.5], "G0": "common.stop_G0", "G1": "common.stop_G1", "age_grid_minutes": [30, 60, 120], "initial_ATR_only": 1.0, "initial_age_minutes": 60}` |
| Economic mechanism | Связать горизонт свежего триггера с reference/ATR; ограничить account risk через sizing, а не только ширину стопа. |
| Expected effect on frequency | APPROVE может увеличиться; число и прибыльность fills неизвестны. |
| Expected effect on expectancy | Проверяется отдельно от количества APPROVE. |
| Expected effect on risk | Меньший stop повышает частоту stop-out; широкий уменьшает Q при risk cap. |
| Expected effect on capital utilization | Больше допустимых исходов без бессрочных pending. |
| 7D test | J4 G0 против J7 G1 при одинаковом momentum signal. Возраст/ATR grid — позже не более 2 альтернатив. |
| 7D pass | Нет цензуры; кандидат проходит общий экономический gate; преимущество существует не только за счёт одного эпизода. |
| 7D fail | Больше approvals при net expectancy <=0 либо target недостижим при risk-capped Q. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["V2-01"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
