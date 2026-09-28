# BTC Set Trigger Snapshot Correction Report

## Scope

Focused correction for BTC Research Set member snapshots after the approved
BTC Trigger `1.0.1` rebind.

No methodology, Trigger registry semantics, non-BTC Sets, Trading Rules,
Research records, production data, or builder logic were changed.

## Root Cause

Classification: STALE_EMBEDDED_TRIGGER_METADATA.

The affected BTC Set artifacts correctly referenced
`TR-R-BTC-001..004@1.0.1`, but the embedded Set member snapshots still carried
pre-correction copied Trigger output metadata. In particular, copied
`output_states` for `TR-R-BTC-001..004@1.0.1` omitted the matched directional
state and showed only `ZERO, UNAVAILABLE`.

The defect was in the canonical Set source/import artifacts, not in the
Trigger source definitions, methodology, runtime Trigger registry semantics, or
production data.

## Affected Set Versions

All 16 approved BTC-rebound Set versions were inspected and corrected:

- `SET-R-BTC-001-V1`
- `SET-R-BTC-001-V2`
- `SET-R-BTC-003-V2`
- `SET-R-BTC-007-V2`
- `SET-R-BTC-008-V2`
- `SET-R-BTC-009-V2`
- `SET-R-BTC-011-V2`
- `SET-R-BTC-012-V2`
- `SET-R-BTC-015-V2`
- `SET-R-BTC-016-V2`
- `SET-R-BTC-019-V1`
- `SET-R-BTC-019-V2`
- `SET-R-BTC-020-V1`
- `SET-R-BTC-020-V2`
- `SET-R-BTC-021-V1`
- `SET-R-BTC-021-V2`

## Corrected Member Snapshot Fields

For each embedded member referencing `TR-R-BTC-001..004@1.0.1`, the copied
Trigger-level fields were mechanically regenerated from
`docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`:

- condition
- operator
- threshold
- threshold unit
- metric references
- formula references
- output states
- direction applicability

Set-owned fields were preserved:

- membership position
- membership role
- Set composition logic
- Set direction semantics
- hypothesis/source mappings
- coin/scope metadata
- trigger ordering

## Before / After

| Trigger member | Before stale output states | Corrected output states |
|---|---|---|
| `TR-R-BTC-001@1.0.1` | `ZERO, UNAVAILABLE` | `LONG, ZERO, UNAVAILABLE` |
| `TR-R-BTC-002@1.0.1` | `ZERO, UNAVAILABLE` | `SHORT, ZERO, UNAVAILABLE` |
| `TR-R-BTC-003@1.0.1` | `ZERO, UNAVAILABLE` | `LONG, ZERO, UNAVAILABLE` |
| `TR-R-BTC-004@1.0.1` | `ZERO, UNAVAILABLE` | `SHORT, ZERO, UNAVAILABLE` |

## Counts

| Check | Result |
|---|---:|
| Affected BTC Set versions inspected | 16/16 |
| Affected BTC Set versions corrected | 16/16 |
| BTC `1.0.1` member references verified | 34/34 |
| BTC `1.0.1` embedded semantics verified | 34/34 |
| All Set versions parsed | 33/33 |
| Trigger references resolved | 242/242 |
| Superseded BTC `1.0.0` refs in affected Sets | 0 |
| Stale BTC `1.0.0` metadata remaining in `1.0.1` members | 0 |

## Regression Scope

Exactly the 16 affected BTC Set records changed in each Set artifact. No
non-BTC Set records changed. Set composition logic, direction semantics,
hypothesis mappings, trigger ordering, roles, and trigger references were
preserved.

## Files Corrected

- `docs/research-import/sets/RESEARCH_V1_SETS.json`
- `docs/research-import/sets/RESEARCH_V1_SETS_WEB_IMPORT.json`

