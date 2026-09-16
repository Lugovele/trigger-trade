# F-002 FULL COUNCIL REVIEW CYCLE 1

Mode: DISCOVERY / FULL_REVIEW
Council route: `FULL_COUNCIL`
Result: `FULL_COUNCIL_APPROVED = NO`
Another review cycle required: YES after blocking semantics are resolved.

## Council Summary

F-002 is not certified as a complete formula specification. A narrow
volume-confirmation candidate is mathematically defensible and
`COUNCIL_DEFINED`, but certification remains withheld because intended
applicability, governing baseline policy, Set usage and role/cadence/freshness
binding are unresolved.

Council reported that only `docs/formula-certification/F-002/F-002_SOURCE_PACK.md`
was read, no subagents were used, and no repository search, edits or execution
were performed.

## Council-Defined Candidate

Construct: unusually high completed-candle participation relative to recent
observations.

Scope:

- one pinned Bybit spot instrument;
- exchange candle base-asset volume;
- venue, instrument, market type and volume basis identical throughout sample;
- contract volume and quote turnover outside this candidate.

Selection:

- one governed completed 1-minute current candle `[T, T+1m)`;
- exactly 60 preceding consecutive 1-minute candles `[T-60m, T)`;
- current candle excluded from reference population;
- completion by `as_of`, source finality and governing selector eligibility
  required.

Arithmetic:

```text
M = (v(30) + v(31)) / 2
K = count(historical volume <= c)
R = c / M                       [defined only when M > 0]
P = 100 * K / 60
predicate = (R >= 2) AND (P >= 90)
```

For valid inputs with `M > 0`, exact predicate evaluation is equivalently:

```text
c >= v(30) + v(31) AND K >= 54
```

Both thresholds are inclusive; ties count toward `K`. Use exact
decimal/integer/rational operations with no epsilon or rounding before
comparison. `R` and `P` are trigger-local intermediates and do not create
exported Set metrics.

Result contract:

- `TRUE` when all preconditions hold and both comparisons pass;
- `FALSE` when all preconditions hold and at least one comparison fails;
- `UNAVAILABLE` otherwise;
- missing current/history, incomplete selection, invalid values,
  ineligible/stale evidence, unresolved source contradictions and `M = 0`
  yield `UNAVAILABLE`;
- valid `c = 0` with `M > 0` yields `FALSE`.

Time/state:

- candidate accepts a governed selection;
- it does not choose scheduler cadence or introduce demo 120-second freshness;
- Set configuration must pin selector, freshness policy and
  CURRENT_STATE/FRESH_EVENT consumption;
- `TRUE` is not automatically a fresh event;
- `UNAVAILABLE` is neither a FALSE baseline nor transition proof.

## Findings

| Classification | Disposition |
|---|---|
| SOURCE_GAP | Canonical F-002 predicate, input binding and parameter provenance are absent. Candidate choices are explicit but not source-established. |
| SOURCE_GAP | The pack does not establish whether ordinary 30-completed-day/14-day-warmup policy governs this trigger baseline. Resolve before unqualified certification. |
| PRODUCT_DECISION | Accepting spot/base-volume/1-minute/60-bar scope as F-002 is a substantive selection. Intended broader market coverage, Set constituent use, role, cadence and freshness binding remain unresolved. |
| SPECIFICATION_DEFECT | Missing/invalid required evidence must be `UNAVAILABLE`, including zero median. Treating it as FALSE or `NOT_CONFIRMED = FALSE` contradicts Set tri-state semantics. |
| EMPIRICAL_QUESTION | Fitness of `60`, `2.0` and `90` is unproven. Needs confirmation frequency, timing, regime sensitivity, sparse trading and incremental-value research. |
| NON_BLOCKING_LIMITATION | Empirical rank is discrete and tie-sensitive; `90` is not confidence or calibrated significance. |
| NON_BLOCKING_LIMITATION | Relative participation does not establish direction, absolute liquidity, execution quality or authenticity of activity. |
| SOURCE_GAP | No F-001 mathematical dependency is established by the pack. |

## Perspective Verdicts

The returned Council record used eight analytical perspectives but noted it
could not attest they matched a separately supplied role mapping. For subsequent
Council cycles, the orchestrator must include the eight required role names in
the minimal evidence prompt.

```text
formula_id: F-002
mode: DISCOVERY / FULL_REVIEW
candidate_status: COUNCIL_DEFINED
canonical_specification_certified: NO
full_council_approved: NO
```

Authority boundary: this record is formula-certification evidence only. It
authorizes no implementation, promotion, commit, deployment, paper/live
execution, exchange interaction, or runtime trading decision.
