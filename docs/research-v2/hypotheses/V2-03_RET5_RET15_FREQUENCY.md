# V2-03 RET5_RET15_FREQUENCY

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | A SIGNAL FREQUENCY |
| Priority | MUST TEST FIRST |
| Hypothesis | OR двух временных импульсов увеличит число новых событий, а не копий одного импульса. |
| Current behavior | В архиве 32 различных MATCHED за условные 30D; полнота потока неизвестна. |
| Proposed change | Новые именованные RET5/RET15, не объявлять их тождественными существующим F-001. |
| Parameter values | `{"cadence_seconds": 60, "coarse_threshold_pairs_pct_points": [[0.2, 0.4], [0.3, 0.5], [0.5, 1.0]], "first_pair": [0.3, 0.5], "logic": "LONG if r5>=0.30% OR r15>=0.50%; SHORT if r5<=-0.30% OR r15<=-0.50%; simultaneous opposing conditions=>NONE", "reset": "new episode only after both absolute returns below their thresholds for 2 consecutive 1m evaluations", "return15_threshold_pct_points": 0.5, "return5_threshold_pct_points": 0.3}` |
| Economic mechanism | Увеличить поток свежих импульсов без механического размножения Set versions. |
| Expected effect on frequency | Требуется ~60 trades/month path; не предсказывается кратность роста. |
| Expected effect on expectancy | Ослабление может ухудшить expectancy; это cheap failure test. |
| Expected effect on risk | Кластеры коррелированных сигналов и fees. |
| Expected effect on capital utilization | Больше turnover лишь при реальных fills. |
| 7D test | J3, G0, базовая тройка; затем максимум одна соседняя пара при положительном механизме. |
| 7D pass | Канонический масштабированный replay проходит +46.67 и условие достаточного turnover. |
| 7D fail | Рост MATCHED без роста profitable fills либо экономика не проходит после 3x и risk caps. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `[]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
