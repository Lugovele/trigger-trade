# V2-06 EXHAUSTION_REVERSAL

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | B REVERSAL; J DIRECTION |
| Priority | MUST TEST FIRST |
| Hypothesis | Возврат после истощения — независимый механизм относительно momentum continuation. |
| Current behavior | Текущее LONG/SHORT переключение не доказывает наличие reversal edge. |
| Proposed change | Новый reversal Set с подтверждённым возвратом, не немедленное контртрендовое усреднение. |
| Parameter values | `{"buy_after_down_impulse": "r15<=-1%; latest close>=15m low+0.5ATR; last two 1m closes rising", "confirm_bars_1m": 2, "extreme_lookback_minutes": 15, "impulse_abs_return15_pct_points": 1.0, "reset": "abs(r15)<0.50% for 2 completed minutes", "retrace_from_extreme_ATR15": 0.5, "sell_after_up_impulse": "r15>=1%; latest close<=15m high-0.5ATR; last two 1m closes falling", "turnover_acceleration_max": 1.0, "validity_minutes": 15}` |
| Economic mechanism | Поймать exhaustion после retracement, отдельно от стратегии продолжения. |
| Expected effect on frequency | Добавляет другие события; допустимая частота должна пройти target filter. |
| Expected effect on expectancy | Знак неизвестен; сильный trend может систематически вредить. |
| Expected effect on risk | Контртрендовые последовательные SL; никаких martingale/averaging. |
| Expected effect on capital utilization | Независимый по механизму, но не гарантированно по рыночным событиям поток. |
| 7D test | J6 G0; LONG/SHORT reported separately, без выбора стороны по старым выигрышам. |
| 7D pass | Общий gate, stress positive; нет зависимости от одной сделки. |
| 7D fail | Убыток/непроходимый economic envelope; не менять направление только ради известного эпизода. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `[]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
