# Known accepted canonical limitations

These are accepted limitations, not defects.

1. Endpoint sensitivity.
2. Terminal settlement binding.
3. Hard material-establishment boundary.
4. Partial-prefix contribution to J.
5. Opposing-phase veto granularity.
6. Local p/w discrete boundary effects.
7. Capped retention / large proportional givebacks.
8. RMS48 regime-transition sensitivity.
9. Reviewer provenance limitations.
10. Same-corpus fresh-panel validation rather than later untouched temporal data.
11. Origin-shift sensitivity.
12. Single-source-step precision dependence near boundaries.

## Exact precision limitation evidence

- `ENVELOPE_OVERLAP_ROWS`: 1,267,500
- `EXACTLY_ACCOUNTED_ROWS`: 1,267,500
- `ATTAINABLE_PREDICATE_CROSSINGS`: 264,460
- `PREDICATE_CROSSING_LABEL_UNCHANGED`: 212,904
- `ATTAINABLE_LABEL_CROSSING`: 51,556
- `NO_ATTAINABLE_CROSSING`: 1,003,040
- `DISTINCT_LABEL_CROSSING_ORIGIN_HORIZONS`: 35,854

The study measures **single-source-step attainability**: exactly one raw close at one timestamp is perturbed by ±1 origin-aligned observed/source price step, with only the minimal same-timestamp high/low adjustment needed for OHLC ordering. It does not allow coordinated multi-timestamp perturbation. It makes no exchange-tick claim.

## Reviewer provenance limitations

- Reviewer 1 — Claude: `METHOD_DEVIATION: PRESENT`; `TYPE: ADDITIONAL_PRE_T_MATERIALITY_BASELINE`.
- Reviewer 2 — GPT-6 Pro: `CONTEXT_ISOLATION: NOT_VERIFIED`.
- Reviewer agreement is **not ground truth**.
