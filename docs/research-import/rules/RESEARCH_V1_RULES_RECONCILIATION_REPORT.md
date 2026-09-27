# Research V1 Rules Reconciliation Report

Status: READ_ONLY_RECONCILED_PACKAGE

## Decision

The earlier interpretation treated Position Rules and Portfolio Rules as independently importable registry objects. That interpretation is rejected.

TriggerTrade's actual product/backend contract is one combined immutable `TradingRulesVersion` containing Position-owned and Portfolio-owned sections. Ownership stays explicit, but versioning is combined.

## Mechanical Reconciliation

The extracted source components are retained as provenance:

- 12 Position components.
- 5 Portfolio components.

The operative import population is not 17 objects and not a Cartesian product. It is 16 combined versions derived from actual Research arm pairings:

- POS-R-001 + PR-R-201
- POS-R-001 + PR-R-204
- POS-R-001 + PR-R-205
- POS-R-001 + PR-R-207
- POS-R-001 + PR-R-208
- POS-R-002 + PR-R-201
- POS-R-003 + PR-R-201
- POS-R-005 + PR-R-201
- POS-R-006 + PR-R-201
- POS-R-007 + PR-R-201
- POS-R-008 + PR-R-201
- POS-R-010 + PR-R-201
- POS-R-011 + PR-R-201
- POS-R-012 + PR-R-201
- POS-R-013 + PR-R-201
- POS-R-014 + PR-R-201

## Methodology-First Blocker Classification

Frozen methodology v1.2.15 is the controlling authority for the following table. Current backend shape is used only to test representability after methodology ownership is known.

| BLOCKER | CONTROLLING_METHODOLOGY_SECTION_OR_OBJECT | METHODOLOGY_OWNER | RESEARCH_SOURCE_MEANING | CURRENT_BACKEND_BEHAVIOR | CLASSIFICATION | ACTION | REMAINS_BLOCKING |
|---|---|---|---|---|---|---|---|
| `max_positions_per_coin = 2/3` | `PORTFOLIO_RULES.md` §§5, 17, 21 | PORTFOLIO | Per-symbol tranche/slot capacity used by first-wave Portfolio grant division and gates; R-025 varies it to 3. | Field exists and validation accepts Research values 2/3 under tranche-slot semantics. | DIRECT_MATCH | Corrected in backend validator. | NO |
| `minimum_tranche_capital` | `PORTFOLIO_RULES.md` §§5, 18 | PORTFOLIO | User rule and hard grant gate requiring requested capital per tranche to meet the minimum. | First-class `TradingRulesVersionDraft` field. | DIRECT_MATCH | Corrected in backend model/serialization. | NO |
| `cooldown_minutes` | `PORTFOLIO_RULES.md` §§5, 24 | PORTFOLIO | User rule pinned before submit authorization; cooldown begins from proven `entry_accepted_at`. | First-class `TradingRulesVersionDraft` field; runtime clock/event ownership remains factual `accepted_at`. | DIRECT_MATCH | Corrected in backend model/serialization. | NO |
| `stop_loss.mode` / dynamic stop | `POSITION_RULES.md` §§8-10 | POSITION | Immutable Position configuration selecting FIXED or DYNAMIC stop construction; DYNAMIC consumes approved stop methodology and pass-through evidence. | First-class `stop_loss_mode` with conditional fixed percentage validation. | DIRECT_MATCH | Corrected in backend model/validation/runtime selection. | NO |
| Position ATR bindings | `POSITION_RULES.md` §§10, 12, 14 and certified F-006/F-007/F-008/F-010 construction dependencies | POSITION | Source constants/reference bindings for Dynamic Entry, Dynamic Stop and Dynamic Take Profit construction. | No first-class TradingRules fields. | OWNED_BY_OTHER_COMPONENT | Remove from backend Rules blocker list; preserve as Position construction/formula references and provenance. | NO |
| Dynamic TP vs `minimum_take_profit_pct > 0` | `POSITION_RULES.md` §§8, 11-12, 14 | POSITION | DYNAMIC TP uses approved Dynamic Take Profit methodology; FIXED TP uses `fixed_tp_pct`. | DYNAMIC mode validates without requiring a fabricated fixed floor. | DIRECT_MATCH | Corrected in backend validation. | NO |
| Disabled minimum-risk-reward with retained value | `POSITION_RULES.md` §§8, 14 | POSITION | Position Rules carry both enabled/disabled state and numeric value; baseline disables the gate and POS-R-012 enables value 2. | First-class enabled flag; runtime does not enforce retained value while disabled. | DIRECT_MATCH | Corrected in backend model and runtime gates. | NO |
| Fee / cost / funding fields | `RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md` §3.1, §4; `ORDER_LIFECYCLE.md` financial evidence sections; `PORTFOLIO_RULES.md` §56 | EXECUTION | Launch/backtest execution-profile inputs and factual Demo/Lifecycle/Accounting evidence; never assumed zero. | Draft requires maker/taker fee, spread, slippage and funding cost values inside immutable Rules. | EXECUTION_EVIDENCE | Remove from Rules blocker list; preserve under launch/execution/backtest/accounting evidence. | NO |
| Source asset labels / instrument binding | `RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md` §3.1 and source-manifest requirements | LAUNCH_BINDING | Research universe labels and exact native symbols resolved by launch/source manifest. | Draft `coins` requires backend symbols. | LAUNCH_TIME_BINDING | Keep Research labels separately; bind native symbols at launch/import review without making labels Rules semantics. | NO |

## Corrections Made

| Old Research package representation | Corrected representation | Runtime semantic change |
|---|---|---|
| 17 independent Rules definitions | 16 combined `TradingRulesVersion` packages with component provenance | No |
| Separate registry import recommendation | Existing combined PostgreSQL Research configuration path, incomplete | No |
| Set version implied as one-to-one Rules binding | Research arm/configuration binds Set version plus combined Rules version; some Sets are reused | No |
| ATR bindings listed as backend Rules blockers | Preserved as Position construction / certified formula references outside the TradingRulesVersion import payload | No |
| Fee/cost/funding listed as Rules blockers | Preserved as launch, execution, backtest-profile and accounting evidence | No |
| Source asset labels listed as Rules blockers | Preserved as Research universe metadata and launch-time instrument binding | No |
| Disabled minimum R:R treated as nonblocking provenance only | Reclassified as backend gap because the methodology's Position Rules object includes an operative enabled/disabled state | No source change; import remains blocked |

No frozen methodology value was changed. No source Rule value was rewritten to satisfy current backend validation.

## Import Conclusion

`RESEARCH_V1_RULES_WEB_IMPORT.json` is created. It contains 16 combined `TradingRulesVersion` records generated through the backend draft serializer.

After methodology-first correction, no genuine TradingRulesVersion backend gaps remain for the Research V1 package.

The removed non-Rules blockers are ATR construction bindings, fee/cost/funding evidence, and launch-time asset binding.
