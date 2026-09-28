# Research Web Forensic Audit After 55a4663

## Scope

Audit target: `55a4663 feat: expose research triggers and sets in dashboard`.

Current HEAD inspected: `4e94185 docs: add research v1 builder specification`. No dashboard/UI files changed between `55a4663` and current HEAD.

This report is diagnostic only. No application code, routes, CSS, tests, production data, triggers, Sets, or Rules were modified.

## Executive Finding

The implementation at `55a4663` did add backend read APIs and desktop Research sub-tabs for Triggers and Sets. The broad claim that Research Triggers/Sets are exposed is partly true for the current desktop `render_product_dashboard(...)` path.

The manual inspection mismatch is concentrated in three places:

1. Rules were not added to the Research navigation. Rules remain under Trading Configuration only.
2. Rules History is not Research Rules history. It is the existing Trading Configuration `TradingRulesVersion` history from the configured rules store/registry.
3. Research Rules are not visible because the corrected Research Rules package is not imported to production as `TradingRulesVersion` rows. Source package existence is not the same as production/web data presence.

## Current Actual Navigation Tree

Actual rendered desktop navigation from `render_product_dashboard(initial_page="research")`:

`Top`

- Overview
- Trading Configuration
- Research

Actual Research sub-navigation inserted by `src/triggertrade/dashboard/product_ui.py::_inject_research_registry_panels`:

`Research`

- Overview
- Triggers
- Sets

There is no Research `Rules` tab and no Research `History` tab.

Trading Configuration still contains:

- Metrics
- Trading Rules

`55a4663` intentionally removes imported Research Triggers/Sets from Trading Configuration by `_remove_config_research_registry_panels`.

## Intended Minimal Navigation Tree

Minimum tree needed for the product behavior described by manual inspection:

`Research`

- Overview
- Triggers
- Sets
- Rules
- Research list / runs

This audit does not implement that tree.

## Route And Visibility Matrix

| Area | Route/API | Exists | Visible from normal UI | Classification | Responsible file/function |
|---|---:|---:|---:|---|---|
| Research overview | `/research` | YES | YES | `EXISTED_BEFORE_AND_STILL_VISIBLE` | `__main__.py` product page map; `product_ui.py::showPage` |
| Research Triggers UI | `/research/triggers` | YES | YES, desktop Research sub-tab | `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH` | `__main__.py` route map; `product_ui.py::openResearchView`; `_research_registry_panels` |
| Research Trigger API list | `/api/research/triggers` | YES | N/A | `BACKEND_READY` | `__main__.py::DashboardHandler.do_GET`; `_research_triggers_payload` |
| Research Trigger API detail | `/api/research/triggers/{id}/{version}` | YES | N/A | `BACKEND_READY` | `__main__.py::_research_trigger_detail` |
| Research Sets UI | `/research/sets` | YES | YES, desktop Research sub-tab | `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH` | `__main__.py` route map; `product_ui.py::openResearchView`; `_research_registry_panels` |
| Research Set API list | `/api/research/sets` | YES | N/A | `BACKEND_READY` | `__main__.py::_research_sets_payload` |
| Research Set API detail | `/api/research/sets/{set_id}/{version}` | YES | N/A | `BACKEND_READY` | `__main__.py::_research_set_detail` |
| Research Rules UI | none under Research | NO | NO | `GENUINELY_MISSING` | Not implemented in `55a4663` |
| Rules current API | `/api/rules/current` | YES | Trading Configuration only | `EXISTED_BEFORE_AND_STILL_VISIBLE` | `__main__.py::_current_rules_payload` |
| Rules history API | `/api/rules/history` | YES | Trading Configuration only | `EXISTED_BEFORE_AND_STILL_VISIBLE` | `__main__.py::_rules_history_payloads` |
| Rules detail API | `/api/rules/version/{id}` | YES | not clearly reachable from current reference Rules history rows | `BACKEND_READY_UI_WEAKLY_REACHABLE_OR_UNREACHABLE` | `__main__.py::_rules_version_detail_payload`; `product_ui.py::renderRules` |

## Before vs After 55a4663

Files changed by `55a4663`:

- `src/triggertrade/dashboard/__main__.py`
- `src/triggertrade/dashboard/product_ui.py`
- `src/triggertrade/dashboard/research_triggers.py`
- `src/triggertrade/dashboard/research_sets.py`
- related tests and completion report

### Parent of 55a4663

- Research trigger read model existed from earlier trigger work.
- `/research/triggers` route existed and mapped to `initial_page="trigger-catalog"`, which resolved through the Trading Configuration page mapping.
- No Research Sets read model file existed.
- Research Set API/UI did not exist.
- Research navigation did not contain Triggers/Sets sub-tabs.
- Imported Research Triggers were presented through the old Trading Configuration trigger panel path.

Classification:

- Triggers: `EXISTED_BEFORE_BUT_NOT_AS_RESEARCH_SECTION`
- Sets: `GENUINELY_MISSING`
- Rules: `EXISTED_BEFORE_AND_STILL_VISIBLE` under Trading Configuration only

### Commit 55a4663

`55a4663` added:

- `src/triggertrade/dashboard/research_sets.py`
- `/api/research/sets`
- `/api/research/sets/{set_id}/{version}`
- `research_sets_payload`
- Research sub-tabs: Overview, Triggers, Sets
- Research Trigger list/detail improvements
- Research Set list/detail rendering
- CURRENT/HISTORICAL classification for Triggers and Sets

`55a4663` did not add:

- Research Rules tab
- Research Rules read API backed by corrected Research Rules package
- Research Rules history/detail UI under Research
- production import/read projection for corrected Research Rules

Classification:

- Triggers: `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH`
- Sets: `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH`
- Rules: `GENUINELY_MISSING` from Research navigation

### Current HEAD

No dashboard UI/read-model changes exist after `55a4663`. Current HEAD only adds Research V1 build spec docs.

## Trigger UI Audit

Findings:

- `/research/triggers` route exists.
- `/api/research/triggers` exists.
- `/api/research/triggers/{id}` and `/api/research/triggers/{id}/{version}` exist.
- Desktop Research navigation includes a visible `Triggers` sub-tab.
- Trigger list table renders columns: Trigger, Version, Metric, Formula, Condition, Output, Applicability, Status, Version State.
- Trigger detail renders implementation key, Metric, Formula, Condition, Operator/Threshold, Output, Applicability, coin applicability, raw immutable config, Used in Set Versions, and Version History.
- CURRENT/HISTORICAL is computed generically in `research_triggers.py`.
- Old versions remain inspectable via detail Version History buttons.
- Metric/Formula split is rendered.
- Navigation from Trigger detail to Set detail is wired through `.js-open-set`.

Responsible code:

- `src/triggertrade/dashboard/__main__.py::DashboardHandler.do_GET`
- `src/triggertrade/dashboard/__main__.py::_research_triggers_payload`
- `src/triggertrade/dashboard/__main__.py::_research_trigger_detail`
- `src/triggertrade/dashboard/research_triggers.py::research_trigger_payload`
- `src/triggertrade/dashboard/research_triggers.py::research_trigger_detail_payload`
- `src/triggertrade/dashboard/product_ui.py::renderTriggers`
- `src/triggertrade/dashboard/product_ui.py::window.showTrigger`
- `src/triggertrade/dashboard/product_ui.py::_research_registry_panels`

Classification: `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH`.

## Set UI Audit

Findings:

- `/research/sets` route exists.
- `/api/research/sets` exists.
- `/api/research/sets/{set_id}/{version}` exists.
- Desktop Research navigation includes a visible `Sets` sub-tab.
- Set list table renders columns: Set, Version, Hypothesis, Direction, Coin / Scope, Trigger Count, Status, Version State.
- Set detail renders hypothesis/scope, trigger versions used, membership order, composition/direction semantics, raw immutable Set config, and Version History.
- CURRENT/HISTORICAL is computed generically in `research_sets.py`.
- Membership trigger links are wired through `.js-open-trigger`.
- The detail panel is inline within the Sets page; there is no separate browser route per Set detail.

Responsible code:

- `src/triggertrade/dashboard/__main__.py::_research_sets_payload`
- `src/triggertrade/dashboard/__main__.py::_research_set_detail`
- `src/triggertrade/dashboard/research_sets.py::research_sets_payload`
- `src/triggertrade/dashboard/research_sets.py::research_set_detail_payload`
- `src/triggertrade/dashboard/product_ui.py::renderSets`
- `src/triggertrade/dashboard/product_ui.py::window.showSet`
- `src/triggertrade/dashboard/product_ui.py::_research_registry_panels`

Classification: `NEW_VISIBLE_IN_DESKTOP_REFERENCE_PATH`.

## Rules UI Audit

Findings:

- Rules backend model exists: `TradingRulesVersion`, `TradingRulesVersionDraft`, `TradingRulesStore`.
- `/api/rules/current`, `/api/rules/history`, and `/api/rules/version/{identity}` exist.
- Visible Rules UI remains under Trading Configuration, not Research.
- `product_ui.py::renderRules` renders a `Version History` block inside the Trading Rules panel.
- The visible history rows are built from `state.rules.history`.
- In the current reference path, history row buttons are rendered as `<button class="link">...` without a detail-opening handler.
- A legacy `window.openRulesVersion` function exists in the older `_PRODUCT_UI_HTML` path, but the current reference-rendered Rules history rows do not use it.
- Research Rules source package exists under `docs/research-import/rules/`, but that is not equivalent to production import.
- The Research Rules package is absent from visible web history unless those versions are imported into the active rules registry/store returned by `_registry_rules_versions`.

Responsible code:

- `src/triggertrade/dashboard/__main__.py::_current_rules_payload`
- `src/triggertrade/dashboard/__main__.py::_rules_history_payloads`
- `src/triggertrade/dashboard/__main__.py::_rules_version_detail_payload`
- `src/triggertrade/dashboard/product_ui.py::renderRules`

Classification:

- Rules backend: `EXISTED_BEFORE_AND_STILL_VISIBLE`
- Research Rules in Research UI: `GENUINELY_MISSING`
- Rules detail from history row: `BACKEND_READY_UI_WEAKLY_REACHABLE_OR_UNREACHABLE`
- Research Rules production visibility: `DATA_NOT_IMPORTED_TO_PRODUCTION`

## History Semantics Audit

| Type | Old versions stored | Read API returns history | UI renders versions | Explicit History view | CURRENT/HISTORICAL computed | Classification |
|---|---:|---:|---:|---:|---:|---|
| Research Triggers | YES, immutable versions in trigger registry | YES, via list/detail payloads | YES, list and detail Version History | Inline detail history, not separate page | YES | `HISTORY_FULLY_VISIBLE_INLINE` |
| Research Sets | YES, immutable versions in Set registry | YES, via list/detail payloads | YES, list and detail Version History | Inline detail history, not separate page | YES | `HISTORY_FULLY_VISIBLE_INLINE` |
| Trading Rules | YES, TradingRulesVersion store/registry | YES | YES as Trading Configuration history rows | Panel exists | `is_current` exists in backend payloads, but UI labels all history rows as Inactive | `HISTORY_UI_EXISTS_BUT_NOT_RESEARCH_RULES` |
| Research Rules | Source package exists; production import not confirmed/absent | NO dedicated Research Rules API | NO Research Rules UI | NO | NO | `HISTORY_NOT_IMPLEMENTED_FOR_RESEARCH_RULES` |

## Production Data vs UI Distinction

### Triggers

- Data exists in source/import artifacts: YES.
- Production trigger registry was reported populated before this audit: YES by prior task context.
- API exists: YES.
- UI route exists: YES.
- Visible navigation exists: YES in desktop Research tabs.

### Sets

- Data exists in source/import artifacts: YES.
- Production Set registry was reported populated 33/33 before this audit: YES by prior task context.
- API exists: YES.
- UI route exists: YES.
- Visible navigation exists: YES in desktop Research tabs.

### Rules

- Backend model exists: YES.
- Corrected Research Rules package exists in docs: YES.
- Production Research Rules imported: NO by current task context; Rules import was explicitly still separate work.
- Rules history route exists: YES for Trading Configuration rules.
- Visible Research Rules navigation exists: NO.

## Manual Path Simulation From `/research`

Using current `render_product_dashboard(initial_page="research")`:

1. First visible page: Research Overview.
2. Visible Research buttons/tabs in desktop reference path: Overview, Triggers, Sets.
3. Reaching Triggers: click Research -> Triggers sub-tab. Direct `/research/triggers` also maps to the Triggers view.
4. Reaching Sets: click Research -> Sets sub-tab. Direct `/research/sets` also maps to the Sets view.
5. Reaching Rules: no Research Rules tab exists. User must leave Research and use Trading Configuration -> Trading Rules, which is not the Research Rules package/history.
6. History:
   - Trigger version history appears inside Trigger detail.
   - Set version history appears inside Set detail.
   - Rules version history appears only inside Trading Configuration Rules and does not represent Research Rules unless Research Rules are imported into the active TradingRulesVersion store/registry.

## Regression Source

No evidence shows that a previously visible Research Rules section was removed by `55a4663`. The more precise diagnosis is:

- `55a4663` added Triggers and Sets to Research but did not add Rules to Research.
- `55a4663` moved imported Research Triggers/Sets out of Trading Configuration by `_remove_config_research_registry_panels`, then inserted them into Research via `_inject_research_registry_panels`.
- If a user expected Triggers/Sets inside Trading Configuration, they are now intentionally removed from that navigation.
- If a user expected Rules under Research, that was never wired by `55a4663`.

Concrete source:

- `src/triggertrade/dashboard/product_ui.py::_research_registry_panels` renders only `Overview`, `Triggers`, and `Sets`.
- `src/triggertrade/dashboard/product_ui.py::openResearchView` accepts only `overview`, `triggers`, and `sets`.
- `src/triggertrade/dashboard/product_ui.py::_remove_config_research_registry_panels` removes `triggers` and `sets` config tabs/panels from Trading Configuration.
- `src/triggertrade/dashboard/product_ui.py::renderRules` remains under `#config-rules`.

## Minimum Fix Scope

Minimum files for a focused UI fix:

- `src/triggertrade/dashboard/product_ui.py`
- `src/triggertrade/dashboard/__main__.py`

Possible additional files if the fix includes Research Rules backend projection after import:

- Rules read-model/API file or existing dashboard rules projection code
- Focused dashboard UI tests

Do not include Trigger or Set semantic changes in the fix.

## Audit Verdict

Research Triggers and Sets are backend/API ready and visible in the desktop Research reference path. The Research web experience is still not complete because Research Rules are not represented under Research, Research Rules are not imported/visible as Research Rules history, and Rules history remains Trading Configuration history.

