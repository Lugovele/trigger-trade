# V2-01 ENTRY_TTL

Status: **SPECIFIED_NOT_IMPLEMENTED**. This is a source-faithful Research V2 specification, not implementation or backtest result.

| Field | Value |
|---|---|
| Family | C ENTRY; execution validity |
| Priority | MUST TEST FIRST |
| Hypothesis | Близкий пассивный вход и короткая валидность устраняют запоздалые сделки и резервы без edge. |
| Current behavior | Одна базовая заявка ждёт fill ~110 часов; одна не заполнена. |
| Proposed change | Отдельный TTL-only control, затем entry scaffold. Жизнь уже открытой позиции не ограничивается TTL заявки. |
| Parameter values | `{"TTL_grid_minutes": [5, 15, 30], "TTL_minutes_initial": 15, "entry_grid_ATR15": [0.05, 0.1, 0.25], "entry_pullback_ATR15_initial": 0.1, "no_reprice": true}` |
| Economic mechanism | Проверить вероятность своевременного fill и оборачиваемость вместо пятидневного GTC. |
| Expected effect on frequency | Fill может вырасти от близости и упасть от TTL; знак не установлен. |
| Expected effect on expectancy | Проверяется, исчезает ли поздний adverse selection; не гарантируется улучшение. |
| Expected effect on risk | Более близкий вход может увеличить неблагоприятные fills. |
| Expected effect on capital utilization | Pending capital-time должен уменьшиться; нельзя подменить его filled exposure. |
| 7D test | J1: legacy Set/POS/50 USDT, только TTL 15m против J0; J2: legacy Set + полный G0. J2 — bundle, не оценка одной причины. |
| 7D pass | TTL исполняется, возврат капитала терминален, механизм экономически пригоден только в кандидате, проходящем общий gate. |
| 7D fail | Ни одна допустимая TTL не даёт timely fills/положительный net edge; не удлинять TTL ради старого winner. |
| Target feasibility requirement | При фактическом notional 750 USDT: 10–14 fills/7D и необходимая net expectancy 0.6222%–0.4444% notional для +46.67 USDT; +70 требует 0.9333%–0.6667%. При меньшем notional пересчитать. Это требования, не ожидаемые доходности. |
| Inherits | common_profile.json unless explicitly overridden |
| Dependencies | `[]` |
| Source status | PROPOSED_NOT_RUN; effects directional hypotheses, not estimated outcomes |

## Provenance

- candidates_12.json
- TriggerTrade_Research_V2_Economic_Redesign_RU.md
- TriggerTrade_Research_V2_Target_Model.xlsx:Candidates
