# V2-07 TAKE_PROFIT

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | E TAKE PROFIT |
| Priority | SECONDARY |
| Hypothesis | TP в R-множителях согласуется с новым stop и обеспечивает payout после fees. |
| Current behavior | Динамический TP часто отклоняет; RR>=2 в V1 удалил единственный baseline winner. |
| Proposed change | Сравнить gross R=1.5/2/3 на выжившем signal, не включать RR gate как замену edge. |
| Parameter values | `{"conditional_net_TP_floor_fraction": 0.003, "gross_R_values": [1.5, 2.0, 3.0], "initial_G0_R": 2.0, "initial_extra_structural_target_gate": false, "strategy_partial_close": false}` |
| Economic mechanism | Баланс hit rate, payoff и издержек; не смешивать planned TP с expectancy. |
| Expected effect on frequency | APPROVE может меняться; closed count при далёком TP может упасть. |
| Expected effect on expectancy | Неизвестный компромисс win probability vs payout. |
| Expected effect on risk | Длительность/funding растут с дальним TP. |
| Expected effect on capital utilization | Более долго занятые позиции могут снизить turnover. |
| 7D test | На одном прошедшем signal сравнить initial2 с максимум двумя альтернативами; full equity at end. |
| 7D pass | Target gate выполнен при фактическом hit rate и fees. |
| 7D fail | Растёт только теоретический RR, а net или turnover падает. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["V2-02"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
