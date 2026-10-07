# V2-08 RISK_BASED_SIZING

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | F SIZING |
| Priority | MUST TEST FIRST AS ECONOMIC ENVELOPE; CANONICAL SCALE AFTER EDGE |
| Hypothesis | Размер должен зависеть от риска и фактического ордера, а не скрытого деления coin allocation. |
| Current behavior | 10% coin budget / 2 slots даёт ~50; 3 slots даёт ~33.33. |
| Proposed change | Явный nominal margin + risk-based Q; убрать только исследовательское автоматическое дробление. |
| Parameter values | `{"formula": "common.capital_risk.sizing_formula", "initial": 0.25, "margin_fraction_values": [0.2, 0.25, 0.33], "max_coin_margin_fraction": 0.33, "min_tranche_usdt": 25, "risk_fraction_max": 0.0075}` |
| Economic mechanism | Увеличить account impact положительного edge, сохраняя заранее заданную потерю. |
| Expected effect on frequency | Сигналы не меняются; actual accepted count может измениться от concurrency. |
| Expected effect on expectancy | Не создаёт edge; в исправном constant-price replay net/notional сохраняется. |
| Expected effect on risk | Плановый риск <=0.75% per trade; gaps могут превысить. |
| Expected effect on capital utilization | Фактический margin 20–33% только если не ограничен риском; не автоматически номинальное значение. |
| 7D test | Сначала J2–J7 nominal25%/1x; затем у максимум 2 положительных семей risk-capped 2x/3x. |
| 7D pass | Фактический Q, equity, caps и target согласованы. |
| 7D fail | Только номинальное увеличение, а fills/Q остаются малы или risk cap нарушен. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["V2-01", "V2-02", "V2-03", "V2-04", "V2-05", "V2-06"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
