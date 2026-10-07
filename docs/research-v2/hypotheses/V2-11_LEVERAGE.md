# V2-11 LEVERAGE

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | H LEVERAGE |
| Priority | MUST TEST AFTER POSITIVE UNIT EDGE |
| Hypothesis | 2x/3x полезны только для уже положительного net/notional с полной risk-моделью. |
| Current behavior | R021 удваивает отрицательный baseline net; это не новый edge. |
| Proposed change | Раздельные 1x/2x/3x канонические прогоны, не умножение итогового PnL. |
| Parameter values | `{"first_grid_excludes": 5, "gross_exposure_fraction_max": 1.8, "leverage": [1, 2, 3], "margin_mode": "ISOLATED, auto-add-margin disabled for research assumption; actual venue support/metadata checked", "nominal_margin_fraction": 0.25, "risk_fraction_max": 0.0075, "total_stop_risk_max": 0.015}` |
| Economic mechanism | Увеличить notional при той же выделенной margin, сохраняя risk caps. |
| Expected effect on frequency | Сигналы прежние; sizing/concurrency могут сократить fills. |
| Expected effect on expectancy | Leverage не меняет исходный edge при том же notional; fees растут только если растёт notional. |
| Expected effect on risk | Liquidation uses mark price; LTP-only backtest не достаточен. |
| Expected effect on capital utilization | Леверидж меняет margin efficiency; не значит полную загрузку кошелька. |
| 7D test | Максимум 2 positive-edge families × [2,3] => 4 runs; fee/funding/mark-margin replay required. |
| 7D pass | Фактический risk-capped профиль проходит общий +46.67 gate, stress net>0 и MTM DD<=6%. |
| 7D fail | e_net<=0 на 1x, отсутствует margin model, или edge исчезает под stress. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["positive_unit_edge_required", "V2-08"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
