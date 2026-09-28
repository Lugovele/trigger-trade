# Trading Rules Integrity Report

## Scope

Audit target: Trading Configuration -> Trading -> Trading Rules.

Authoritative artifacts inspected:

- `docs/research-import/rules/RESEARCH_V1_RULES.json`
- `docs/research-import/rules/RESEARCH_V1_RULES_WEB_IMPORT.json`
- `docs/research-import/rules/RESEARCH_V1_RULES_CATALOG.md`
- `docs/research-import/rules/RESEARCH_V1_RULE_IMPORT_MAP.md`
- `docs/research-import/rules/RESEARCH_V1_RULE_VALIDATION_REPORT.md`
- `docs/research-import/rules/RESEARCH_V1_RULES_RECONCILIATION_REPORT.md`
- `src/triggertrade/rules/trading.py`
- Trading Configuration Rules rendering in `src/triggertrade/dashboard/product_ui.py`

## Result

Corrected Research V1 combined TradingRulesVersion package integrity: PASS.

| Check | Result |
|---|---:|
| Combined TradingRulesVersion source versions | 16/16 |
| Backend-valid web import versions | 16/16 |
| Web import-valid versions | 16/16 |
| Semantic loss | NO |
| Split Position/Portfolio version objects introduced | NO |
| Fake production Research Rules rendered | NO |

## Methodology-Owned Fields Checked

The corrected web-import package preserves the methodology-owned fields required
for the combined TradingRulesVersion contract, including:

- `max_positions_per_coin`
- `minimum_tranche_capital`
- `cooldown_minutes`
- `stop_loss.mode`
- dynamic take-profit representation
- `minimum_risk_reward.enabled`
- position size
- entry/TP/SL configuration
- minimum net edge flags
- leverage
- portfolio caps
- global and per-coin slot controls
- daily loss fields
- direction mode
- coin allocation and enabled state

## UI Checks

Trading Rules remains one page with Position Rules, Portfolio Rules, Coins,
Save New Rules, and History. Historical versions are rendered through the same
combined TradingRulesVersion history mechanism. Research-specific Rules are not
fabricated in the UI because they have not been imported to production in this
task.

## Remaining Defects

No Rules semantic, backend, read-model, or UI projection defects remain in the audited package/UI path.
