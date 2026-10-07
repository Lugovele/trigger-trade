# V2-10 BTC_CONTEXT

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | J DIRECTION / REGIME; B BTC |
| Priority | SECONDARY |
| Hypothesis | Мягкое contextual veto лучше абсолютного BTC agreement, если не убивает частоту. |
| Current behavior | В V1 Set-варианты часто совпадают; механизм не идентифицирован полными гипотезами. |
| Proposed change | Сначала BTC strong-opposition veto; direction specialization позже на новых данных. |
| Parameter values | `{"BTC_self_filter": false, "BTC_veto_return15_pct_points": 0.3, "LONG_veto": "BTC r15<=-0.30% AND BTC EMA20(15m)<EMA50(15m)", "SHORT_veto": "BTC r15>=0.30% AND BTC EMA20(15m)>EMA50(15m)", "high_vol_stop_competing_ATR": [1.0, 1.5], "initial_sides": "BOTH", "later_side_arms": ["LONG_ONLY", "SHORT_ONLY"], "report_only_UTC_sessions": ["00:00-08:00", "08:00-16:00", "16:00-24:00"]}` |
| Economic mechanism | Пропускать явный встречный market trend; анализ asymmetry не привязан к старому PEPE winner. |
| Expected effect on frequency | Меньше событий; если ниже target envelope, candidate отбраковывается. |
| Expected effect on expectancy | Проверяется улучшение conditional selection; disagreement исследуется через V2-06. |
| Expected effect on risk | Режимная зависимость и корреляция. |
| Expected effect on capital utilization | Idle-time может вырасти. |
| 7D test | На одном survivor baseline vs BTC veto. Затем только 1 direction/regime split, без одновременного поиска сессий. |
| 7D pass | Прирост net survives opportunity loss и отдельный 7D holdout. |
| 7D fail | Выигрыш существует только на уже изученной стороне/сессии либо target не проходит. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `["V2-03", "V2-04"]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
