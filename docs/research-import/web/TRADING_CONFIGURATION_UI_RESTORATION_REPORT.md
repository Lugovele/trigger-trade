# Trading Configuration UI Restoration Report

## Scope

This restoration returns configuration-class objects to their approved UI home under `Trading Configuration`.

No Trigger data, Set data, Rules domain semantics, Research hypotheses, methodology, production data, Demo, or Research execution state was changed.

## Historical References Used

- `55a4663^`: preserved the Trading Configuration grouping with `Signal Logic` and `Trading`.
- `55a4663`: introduced Research Trigger/Set read models and later moved those views into Research.
- `4e94185`: retained the post-`55a4663` Research placement before the later usability correction.
- `f7c6f2c`: added the now-rejected Research configuration-class navigation, including Research `Rules`.

The restored structure follows the already-existing reference UI shape:

`Trading Configuration`

- `SIGNAL LOGIC`: Metrics, Triggers, Sets
- `TRADING`: Trading Rules

## Incorrect Recent Changes Removed

- Removed rendered Research sub-navigation for Triggers, Sets, and Rules.
- Removed the separate Research Rules panel.
- Stopped stripping Triggers/Sets out of Trading Configuration.
- Restored final dashboard composition so Trigger and Set panels are injected into `Trading Configuration`.
- Changed Trigger and Set detail back-navigation to return to Trading Configuration.
- Kept Rules history and read-only historical detail on the single Trading Rules page.

## Final Trading Configuration Navigation

`Trading Configuration`

`SIGNAL LOGIC`

- Metrics
- Triggers
- Sets

`TRADING`

- Trading Rules

No separate top-level pages were added for Position Rules, Portfolio Rules, Coins, or Rules History.

## Final Trading Rules Page Structure

The single `Trading Rules` page contains:

- Position Rules
- Portfolio Rules
- Coins
- Save New Rules / Save as New Version control
- History
- Read-only historical Rules detail rendered from persisted `TradingRulesVersion` data

Research Rules are still not imported to production and are not fabricated in the UI.

## Trigger Flow

`Trading Configuration -> Triggers -> Trigger detail -> Triggers`

The Trigger list/detail continues to use the existing Trigger registry/read path and preserves immutable versions, CURRENT/HISTORICAL state, Metric/Formula display, and persisted semantics.

## Set Flow

`Trading Configuration -> Sets -> Set detail -> Sets`

The Set list/detail continues to use the existing Research Set registry/read path and preserves persisted Set versions, CURRENT/HISTORICAL state, ordered Trigger memberships, and exact Trigger version references.

## Rules History Flow

`Trading Configuration -> Trading Rules -> History -> historical version -> Trading Rules`

History shows only persisted backend Rules versions. Historical detail is read-only and belongs to the same Trading Rules page.

## Research Ownership

Research no longer owns configuration classes. It remains the top-level Research area for Research objects, runs, and results.

## Tests Executed

- `python -m py_compile src\triggertrade\dashboard\product_ui.py src\triggertrade\dashboard\__main__.py tests\unit\test_research_trigger_web_read.py tests\unit\test_dashboard_http.py`
- `python -m pytest tests\unit\test_research_trigger_web_read.py -q`
- `python -m pytest tests\unit\test_dashboard_http.py::test_dashboard_http_product_routes_use_new_information_architecture tests\unit\test_dashboard_http.py::test_dashboard_routes_render_bootstrapped_registry_under_new_ia -q`
- `python -m pytest tests\unit\test_reference_ui_replacement.py -q`
- `git diff --check`
