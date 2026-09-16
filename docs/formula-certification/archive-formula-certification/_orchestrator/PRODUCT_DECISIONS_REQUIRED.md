# Product Decisions Required

Status: RESOLVED_FOR_REVIEW
Updated: 2026-09-15

This register captures product decisions that blocked further autonomous
formula certification and records their resolution for the current review
cycle. It is an orchestration artifact only; it does not change active
methodology, certify a formula, or authorize implementation.

## Blocking Frontier

The former blocking frontier has been resolved by product owner decision.
F-001 and F-002 are now revised candidates pending Full Council re-review. F-004
and the downstream Set/Position formula chain remain dependency-waiting until
F-001 and F-002 are approved and finalized.

## F-001 - Price-move trigger calculation

State: `REVISION_REQUIRED`

Latest Council artifact:

```text
docs/formula-certification/_orchestrator/work/F-001/FULL_COUNCIL_REVIEW_CYCLE_1.md
```

Council-approved partial core:

```text
move_pct_work = Q36(100 * (P_observed - P_reference) / P_reference)
```

The core is only a partial arithmetic definition. It does not define the full
Trigger.

### Decision Resolved

Define complete product semantics for the price-move Trigger:

- observed price basis;
- reference endpoint;
- observed endpoint;
- horizon;
- predicate operator;
- threshold parameter contract;
- evaluation cadence;
- CURRENT_STATE and/or FRESH_EVENT role;
- declared relationship to F-003 ATR/true-range context.

### Selected Option

Adopt a signed endpoint-displacement Trigger over explicitly selected same
instrument/same basis prices:

```text
move_pct_work = Q36(100 * (P_observed - P_reference) / P_reference)
```

Then define the predicate, threshold, horizon and cadence as configuration
contracts around that value.

Tradeoff: narrow and deterministic; does not measure path, volatility-adjusted
move, spread, depth, execution capacity or absolute activity. The F-003
relationship must either be removed or explicitly scoped as downstream/context,
not silently imported.

### Rejected Alternatives

Choose a materially different construct, such as:

- open-to-close move;
- anchor-to-current move;
- absolute move;
- ATR-normalized move;
- timeframe-specific breakout displacement;
- direction-specific LONG/SHORT mapping.

Tradeoff: may better match intended market behavior if F-001 is meant to
detect a different event, but it changes the formula's construct and requires a
new complete candidate.

### Resolution Artifact

```text
docs/formula-certification/_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_1.md
```

## F-002 - Volume confirmation calculation

State: `REVISION_REQUIRED`

Latest Council artifact:

```text
docs/formula-certification/_orchestrator/work/F-002/FULL_COUNCIL_REVIEW_CYCLE_1.md
```

Council-defined partial candidate:

```text
M = (v(30) + v(31)) / 2
K = count(historical volume <= c)
R = c / M
P = 100 * K / 60
predicate = (R >= 2) AND (P >= 90)
```

Equivalent for valid `M > 0`:

```text
c >= v(30) + v(31) AND K >= 54
```

The candidate scope is a pinned Bybit spot instrument, exchange candle
base-asset volume, one completed 1-minute current candle and 60 preceding
completed 1-minute candles.

### Decision Resolved

Decide whether this narrow candidate is the intended F-002 product semantics,
including:

- market coverage;
- volume unit/basis;
- 1-minute/60-bar horizon;
- Set constituent use;
- CURRENT_STATE and/or FRESH_EVENT role;
- scheduler cadence;
- freshness policy;
- whether ordinary 30-completed-day/14-day-warmup baseline policy governs or
  is explicitly not applicable.

### Selected Option

Adopt the Council-defined relative-volume mathematics but bind it to Bybit USDT
linear perpetual futures KLINES base-coin volume, preserving:

- exact median/rank arithmetic;
- inclusive thresholds;
- ties count toward `K`;
- `UNAVAILABLE` for missing/invalid/stale evidence and zero median;
- no exported Set metric for `R` or `P` unless separately defined.

Tradeoff: deterministic and narrow; confirms relative recent participation but
does not establish direction, absolute liquidity, execution quality or
authenticity of activity.

### Rejected Alternatives

Choose a different volume construct, such as:

- quote turnover;
- futures contract volume;
- longer baseline;
- ordinary 30-day/14-day-warmup baseline;
- absolute liquidity floor;
- per-symbol normalized activity score;
- event freshness model different from the 1-minute completed-candle
  candidate.

Tradeoff: may better fit the intended trading universe or liquidity objective,
but changes the formula construct and requires a new complete candidate.

### Resolution Artifact

```text
docs/formula-certification/_orchestrator/work/F-002/F-002_REVISED_SPEC_CYCLE_1.md
```

## Effect On Queue

Until F-001 and F-002 are re-reviewed, approved and finalized:

- F-004 remains `WAITING_FOR_DEPENDENCY`;
- F-005 waits for F-004;
- F-008 waits for F-005;
- F-006 and F-007 wait for F-005 and F-008;
- F-009 waits for F-006 and F-007;
- F-010 waits for F-008;
- F-011 waits for F-008, F-009 and F-010;
- F-012 waits for F-008, F-009 and F-010.

A-002, A-004, A-009 and F-003 are already certified.
