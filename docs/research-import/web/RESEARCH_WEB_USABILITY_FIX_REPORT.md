# Research Web Usability Fix Report

## Scope

This focused correction makes existing Research Triggers, Research Sets, and persisted Rules version information discoverable from the visible Research UI.

No Trigger data, Set data, Rules semantics, Research Rules import state, production data, Demo, or Research execution state was changed.

## Previously Hidden Or Unreachable Paths

| Path | Current route | Defect from forensic audit | Fix |
|---|---|---|---|
| Research Rules destination | `/research/rules` | Rules were not present in the Research navigation. Users had to know Trading Configuration contained Rules. | Added a visible Research `Rules` tab and route mapping to the Research page. |
| Rules version history from Research | Existing Rules read model, previously visible only under Trading Configuration | Rules History existed, but not as a Research-visible object class. | Added a read-only Research Rules panel backed by the existing persisted `TradingRulesVersion` payload. |
| Research Rules production state | Not imported to production | Source artifacts existed, but production Research Rules records were not visible because they have not been imported. | The UI states that Research Rules import is pending and shows only actual persisted Rules records. No fake Research Rules rows are rendered. |

## Visible Research Navigation After Fix

`Research`

- Overview
- Triggers
- Sets
- Rules

The Triggers and Sets tabs continue to use the existing Research registry read models. The Rules tab uses the existing Rules read model and does not derive rows from `docs/research-import/rules/`.

## Trigger Journey

`Research -> Triggers -> Trigger detail -> Triggers`

Result: PASS.

The Research `Triggers` tab remains visible. Trigger list/detail rendering is preserved, including immutable version, CURRENT/HISTORICAL state, Metric/Formula split, raw configuration, Set links, and version history. Trigger detail now includes an explicit `Back to Triggers` control.

## Set Journey

`Research -> Sets -> Set detail -> Sets`

Result: PASS.

The Research `Sets` tab remains visible. Set list/detail rendering is preserved, including the 33 persisted Set versions, memberships, exact trigger ID/version references, CURRENT/HISTORICAL state, membership trigger links, and version history. Set detail now includes an explicit `Back to Sets` control.

## Rules Journey

`Research -> Rules -> Rules version detail -> Rules`

Result: PASS.

The Research `Rules` tab is now visible. It shows actual persisted Rules versions from the existing backend payload and an explicit notice that Research Rules are not imported to production yet. Selecting a persisted Rules version opens read-only detail with a `Back to Rules` control.

## Rules History Behavior

Rules History remains based on persisted `TradingRulesVersion` rows only. The UI is structurally ready to show CURRENT/HISTORICAL state for persisted Rules versions.

Research Rules are still not shown as production records because the controlled Research Rules import has not happened. This is intentional.

## Files Changed

- `src/triggertrade/dashboard/__main__.py`
- `src/triggertrade/dashboard/product_ui.py`
- `tests/unit/test_research_trigger_web_read.py`
- `docs/research-import/web/RESEARCH_WEB_USABILITY_FIX_REPORT.md`

## Production State

Production was not mutated. Research was not started. Demo was not started. No deployment was performed.
