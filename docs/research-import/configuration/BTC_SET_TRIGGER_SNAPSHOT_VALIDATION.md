# BTC Set Trigger Snapshot Validation

## Validation Summary

Validation proves every BTC Set member snapshot that references a corrected
BTC Trigger `1.0.1` version now matches the exact referenced Trigger version.

| Validation | Result |
|---|---:|
| Affected BTC Set versions inspected | 16/16 |
| All Set versions parse | 33/33 |
| Trigger references resolved | 242/242 |
| BTC `1.0.1` member snapshots verified | 34/34 |
| Stale BTC `1.0.0` refs in affected Sets | 0 |
| Non-BTC Set regression | NO |
| Set composition regression | NO |
| Set direction regression | NO |
| Hypothesis mapping regression | NO |

## BTC Trigger Output-State Verification

| Trigger version | Expected output states | Verified members |
|---|---|---:|
| `TR-R-BTC-001@1.0.1` | `LONG, ZERO, UNAVAILABLE` | 16 |
| `TR-R-BTC-002@1.0.1` | `SHORT, ZERO, UNAVAILABLE` | 16 |
| `TR-R-BTC-003@1.0.1` | `LONG, ZERO, UNAVAILABLE` | 1 |
| `TR-R-BTC-004@1.0.1` | `SHORT, ZERO, UNAVAILABLE` | 1 |

## Evaluation Semantics

Evaluation semantics remain Trigger-owned and are verified through the exact
referenced Trigger definitions:

- `TR-R-BTC-001@1.0.1`: CURRENT_STATE
- `TR-R-BTC-002@1.0.1`: CURRENT_STATE
- `TR-R-BTC-003@1.0.1`: FRESH_EVENT
- `TR-R-BTC-004@1.0.1`: FRESH_EVENT

The current Set member schema does not persist separate freshness/timeframe
fields; it carries the member predicate snapshot fields and links to the exact
Trigger version. The Trigger read model remains the source for full
freshness/timeframe text.

## Regression Test Evidence

Added regression coverage in `tests/unit/test_research_trigger_web_read.py`:

- validates all 34 BTC `1.0.1` embedded member snapshots against the referenced
  Trigger definitions;
- rejects a synthetic `TR-R-BTC-001@1.0.1` member when `LONG` is removed;
- rejects a synthetic `TR-R-BTC-002@1.0.1` member when `SHORT` is removed;
- rejects a synthetic `TR-R-BTC-003@1.0.1` member when `LONG` is removed;
- rejects a synthetic `TR-R-BTC-004@1.0.1` member when `SHORT` is removed.

Focused test result:

`python -m pytest tests\unit\test_research_trigger_web_read.py -q`

Result: `9 passed`.

