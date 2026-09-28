# Sets Integrity Report

## Scope

Audit target: Trading Configuration -> Signal Logic -> Sets.

Authoritative artifacts inspected:

- `docs/research-import/sets/RESEARCH_V1_SETS.json`
- `docs/research-import/sets/RESEARCH_V1_SETS_WEB_IMPORT.json`
- `docs/research-import/sets/RESEARCH_V1_SET_IMPORT_MAP.md`
- `docs/research-import/sets/RESEARCH_V1_SET_VALIDATION_REPORT.md`
- `src/triggertrade/dashboard/research_sets.py`
- Trading Configuration Set rendering in `src/triggertrade/dashboard/product_ui.py`

## Result

Set source and read-model integrity: PASS.

| Check | Result |
|---|---:|
| Immutable Set versions | 33/33 |
| Trigger references resolved | 242/242 |
| BTC affected Set versions | 16/16 |
| Affected BTC Sets using corrected trigger versions | 16/16 |
| Superseded BTC 1.0.0 references in affected Sets | 0 |
| Set semantic loss | NO |

## Direction Semantics Investigation

Classification: READ_MODEL_PROJECTION_DEFECT, corrected.

The Set definition's direction semantics are not the same as a runtime Set
Result. The source package defines classifier-driven non-BTC Sets as final side
equals the same current classifier side. Those records do not literally contain
the tokens LONG or SHORT in the short direction field, so the previous compact
label collapsed them to `NONE`. That was a projection defect.

Correction: classifier-driven Set definitions now project as `CLASSIFIER SIDE`.
BTC deterministic branch Sets continue to project as `LONG / SHORT`, with the
full source direction semantics visible in detail.

## BTC Set Checks

All 16 affected BTC Set versions use corrected `TR-R-BTC-001..004@1.0.1`
references where required. No affected current BTC Set version references a
superseded `1.0.0` BTC directional trigger.

## Remaining Defects

No Set semantic, backend, read-model, or UI projection defects remain in the audited source-backed path.
