# F-001 — N-008 Dependency Evidence

## 1. N-008 Identity

```text
N008_ID: N-008
N008_NAME: Canonical Set numeric output precision
N008_TYPE: NORMALIZATION_RULE
N008_OWNER: Set
N008_FAMILY: SET_ANALYTICS
N008_STATUS: APPROVED_AS_DEFINED
N008_BACKEND_GATE: IMPLEMENT_ALLOWED
```

The active catalog identifies N-008 as `Canonical Set numeric output precision`, owned by Set, with type `NORMALIZATION_RULE`, family `SET_ANALYTICS`, status `APPROVED_AS_DEFINED`, and backend gate `IMPLEMENT_ALLOWED` (`docs/FORMULA_METRICS_CATALOG.md`, Formula / Metric Catalog table). The same catalog maps N-008 to `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md :: §2 Canonical Set Value Representation`.

The active normative document uses the stable policy identifier `TT_SET_NUMERIC_V1`, not the identifier `N-008`, as the operative rule name (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, title and Overview). The catalog is therefore the authoritative identifier mapping; `SET_NUMERIC_POLICY.md` is the authoritative rule body.

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Formula / Metric Catalog row `N-008` | CATALOG_METADATA | Defines N-008 identity, name, owner, type, family, status, backend gate, and primary source pointer. |
| 2 | `docs/FORMULA_METRICS_CATALOG.md` | Certification Queue row `F-001` | CATALOG_METADATA | Declares F-001 dependencies as `F-003, N-008`. |
| 3 | `docs/FORMULA_METRICS_CATALOG.md` | Approved System / Accounting Calculations | CATALOG_METADATA | Lists `N-008 Canonical Set numeric output precision` as approved. |
| 4 | `docs/FORMULA_METRICS_CATALOG.md` | Backend Traceability Cross-Check | CATALOG_METADATA | Links N-008 to allowed Set contracts/state surface and to blocked final Set numeric calculations. |
| 5 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | Title / Overview | PRIMARY_POLICY | Defines `TT_SET_NUMERIC_V1` as the computation and serialization contract for Set-derived numeric formulas, timeframes, windows, and thresholds. |
| 6 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §1 Source identity, exact parsing, and ordering | PRIMARY_POLICY | Defines exact raw decimal parsing, source identity, closed-candle ordering, as-of cutoff, completeness, ambiguity, and availability rules for Set-derived computations. |
| 7 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §2 Working arithmetic and operation order | PRIMARY_POLICY | Defines exact arithmetic, no binary floating point, formula-order evaluation, 36-fractional-place work grid, `ROUND_HALF_EVEN`, dependency consumption, exact comparisons, and no epsilon. |
| 8 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §5 Boundary values and serialization classes | PRIMARY_POLICY | Defines Market Handoff/export rounding, canonical decimal strings, exact Position consumption, and the rule that display rounding must not be used for gates. |
| 9 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §7 Internal normalization operation and tests | PRIMARY_POLICY | Defines `normalize_working`, `serialize_normalized_for_handoff`, checkpoint retention, exact-threshold tests, and no epsilon or policy-version change. |
| 10 | `docs/trading-methodology/methodology/SET.md` | Market Handoff | OWNERSHIP_BOUNDARY | States Set owns canonical metric definitions and semantics, points to `SET_NUMERIC_POLICY.md` §§1-5, and prohibits Position from reconstructing or reinterpreting Set output. |
| 11 | `docs/trading-methodology/methodology/SET.md` | Append-only v1.2.14 numeric-policy addendum | PRIMARY_POLICY | States `SET_NUMERIC_POLICY.md` is normative for all existing Set-derived arithmetic, while existing formulas, timeframes, trigger logic, normalization windows, and thresholds are unchanged. |
| 12 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P16 - Set numeric state and historical market selectors | SYSTEM_PROTOCOL | States Set-derived computation and Market Handoff v4 use `SET_NUMERIC_POLICY.md`; source ordering, checkpoints, work precision, handoff quantization, and Position exact comparisons are normative technical rules. |
| 13 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | Internal Set normalized working values | SYSTEM_PROTOCOL | Defines internal `normalize_working` behavior and states serialization cannot mutate working state or checkpoint and must occur after gates needing work precision. |
| 14 | `docs/trading-methodology/schemas/README.md` | Current Schemas and Numeric Policies | CONTRACT_INDEX | States `SET_NUMERIC_POLICY.md` governs deterministic Set indicator computation and handoff serialization; package revision is v1.2.14. |
| 15 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` | §7 Exact hold and separate Set arithmetic | NUMERIC_BOUNDARY | Separates monetary `TT_NUMERIC_V1` from Set `TT_SET_NUMERIC_V1`; monetary rules do not choose indicator seeds, square roots, or handoff approximation. |
| 16 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Market Handoff v4 shape and invariants | OUTPUT_CONTRACT | Shows `set_numeric_policy_version: TT_SET_NUMERIC_V1`; states strict schema is in `wire.schema.json` and decimal values are exact strings. |
| 17 | `docs/trading-methodology/schemas/wire.schema.json` | MARKET_HANDOFF volatility / `set_numeric_policy_version` | OUTPUT_CONTRACT | Defines canonical TT_SET_NUMERIC_V1 wire value descriptions for ATR fields and requires `set_numeric_policy_version` const `TT_SET_NUMERIC_V1`. |
| 18 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` | Identifier lineage table | REPLAY_RESTART | Defines indicator checkpoint identity as Set-owned after canonical ordered source processing, with TT_SET_NUMERIC_V1 state and source-manifest digest. |
| 19 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Canonical Set value consumption and actual hold binding | DOWNSTREAM_CONSUMPTION | States Market Handoff v4 requires TT_SET_NUMERIC_V1 and Position must parse and compare exact received Set volatility fields without recomputation or display rounding. |

## 3. Canonical N-008 Definition

N-008 is not a standalone trading formula. It is the catalog identifier for the Set numeric precision and serialization policy implemented by `TT_SET_NUMERIC_V1`.

The canonical behavior is:

- Set-derived calculations use `SET_NUMERIC_POLICY.md` / `TT_SET_NUMERIC_V1` as their technical computation and serialization contract (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, Overview).
- Raw decimal source values are parsed exactly as signed integer plus scale. Binary floating point, context-dependent parsing, NaN, and infinity are not allowed (`SET_NUMERIC_POLICY.md`, §1).
- Source facts must retain authoritative identities, times, symbol, dataset, and series. Equal source IDs are deduplicated; conflicting equal IDs are an integrity condition (`SET_NUMERIC_POLICY.md`, §1).
- Set fixes one as-of cutoff and persists selectors before dispatch; closed candles are sorted by interval-open time, must be non-overlapping and continuous, and must not be incomplete or after `as_of` (`SET_NUMERIC_POLICY.md`, §1).
- Set arithmetic evaluates exact integer or rational expressions in the specified formula order. Implementations may not regroup algebraically to introduce extra rounding (`SET_NUMERIC_POLICY.md`, §2).
- At each named continuous Set metric output, recursive state update, and normalization output, the value is rounded once to the work grid `10^-36` using `ROUND_HALF_EVEN` (`SET_NUMERIC_POLICY.md`, §2).
- The 36-place grid is fractional decimal scale, not significant digits; large integer digits are retained (`SET_NUMERIC_POLICY.md`, §2).
- Dependent formulas consume the persisted working value of named dependencies, not hidden library precision (`SET_NUMERIC_POLICY.md`, §2).
- Percent conversion uses exact multiplication or division by 100. Clamps, signs, and comparisons occur in formula order with no epsilon (`SET_NUMERIC_POLICY.md`, §2).
- Market Handoff and governed diagnostic/export boundaries use their explicitly defined serialization classes; serialization does not replace internal gate values (`SET_NUMERIC_POLICY.md`, §5; `SYSTEM_PROTOCOLS.md`, Internal Set normalized working values).
- Canonical decimal strings use no exponent, plus sign, negative zero, redundant leading integer zero, or trailing fractional zeros (`SET_NUMERIC_POLICY.md`, §5).

## 4. Inputs / Preconditions

| Input / Precondition | Canonical Source | Requirement |
|---|---|---|
| Raw decimal source values | `SET_NUMERIC_POLICY.md`, §1 | Exact signed-integer-and-scale parsing; no binary float, context-dependent parsing, NaN, or infinity. |
| Source fact identity | `SET_NUMERIC_POLICY.md`, §1 | Authoritative source identities, times, symbol, dataset, and series must be preserved. |
| Duplicate source identity | `SET_NUMERIC_POLICY.md`, §1 | Equal source IDs are deduplicated; conflicting equal IDs are an integrity condition. |
| As-of cutoff / selectors | `SET_NUMERIC_POLICY.md`, §1; `SYSTEM_PROTOCOLS.md`, P16 | Set fixes and persists selection identity, as-of cutoff, interval, count, timeframe, and cursor requests before Market Data Request dispatch. |
| Closed-candle source ordering | `SET_NUMERIC_POLICY.md`, §1 | Closed candles are sorted by interval-open time; non-overlap and continuity are verified. |
| Incomplete or future source facts | `SET_NUMERIC_POLICY.md`, §1 | No incomplete/still-forming candle and no candle after the fixed `as_of` cutoff may enter the selected Set source range. |
| Formula expression / operation order | `SET_NUMERIC_POLICY.md`, §2 | Arithmetic follows the specified formula order using exact integer/rational expressions. |
| Named dependency work values | `SET_NUMERIC_POLICY.md`, §2 | Dependent formulas consume persisted working values of named dependencies. |
| Existing formula/threshold/window semantics | `SET.md`, Append-only v1.2.14 numeric-policy addendum | `TT_SET_NUMERIC_V1` does not change existing formulas, timeframes, trigger logic, normalization windows, or thresholds. |
| Checkpoint proof | `IDENTIFIER_LINEAGE.md`, Identifier lineage table; `SET_NUMERIC_POLICY.md`, §7 | Indicator checkpoints retain TT_SET_NUMERIC_V1 state and source-manifest digest, and restore only matching policy/ancestry. |

N-008 does not itself define F-001's price inputs, trigger threshold, timeframe, reference price, direction treatment, or trigger event. It governs numeric representation, arithmetic precision, ordering, serialization, and replay/checkpoint proof for Set-derived numeric computation where the active methodology has a defined Set calculation.

## 5. Outputs / Effect

N-008 produces or constrains the following effects:

| Output / Effect | Source | Canonical Requirement |
|---|---|---|
| Working continuous Set metric value | `SET_NUMERIC_POLICY.md`, §2 | Round once to `10^-36` fractional scale with `ROUND_HALF_EVEN` at each named continuous Set metric output. |
| Recursive state update | `SET_NUMERIC_POLICY.md`, §2 | Round once to the same 36-fractional-place work grid at recursive state update. |
| Normalization output | `SET_NUMERIC_POLICY.md`, §2 and §7 | `normalize_working` returns the canonical working-grid result as a decimal string. |
| Dependent formula input | `SET_NUMERIC_POLICY.md`, §2 | Downstream formulas consume persisted working values, not hidden library precision. |
| Handoff/export representation | `SET_NUMERIC_POLICY.md`, §5; `MARKET_HANDOFF.md`; `wire.schema.json` | Governed Market Handoff values use `TT_SET_NUMERIC_V1` wire serialization where defined; volatility fields are described as Q=`1e-18`, `ROUND_HALF_EVEN`. |
| Serialization format | `SET_NUMERIC_POLICY.md`, §5 | Canonical decimal strings have no exponent, plus sign, negative zero, redundant leading integer zero, or trailing fractional zeros; object serialization uses sorted-key compact UTF-8 JSON. |
| Checkpoint state | `SET_NUMERIC_POLICY.md`, §7; `IDENTIFIER_LINEAGE.md` | Checkpoints retain working value plus policy/source proof; indicator checkpoint ID binds TT_SET_NUMERIC_V1 state and source-manifest digest. |

## 6. Runtime Role

```text
N008_RUNTIME_REQUIREMENT:
YES
```

N-008 is runtime behavior for Set-derived computation and governed handoff/diagnostic serialization. `SYSTEM_PROTOCOLS.md` P16 states that Set-derived computation and Market Handoff v4 use `SET_NUMERIC_POLICY.md`, and that source ordering, recursive initialization/checkpoints, work precision, handoff quantization, and Position exact comparisons are normative technical rules.

The runtime role is bounded: `SET_NUMERIC_POLICY.md` states it is a computation and serialization contract for existing Set formulas, timeframes, windows, and thresholds and does not add a new signal, indicator, fallback, or heuristic. It does not independently define F-001's formula.

## 7. Relationship to F-001

The catalog explicitly declares F-001 dependencies as `F-003, N-008` (`docs/FORMULA_METRICS_CATALOG.md`, Certification Queue row `F-001`). The catalog also classifies F-001 as Set-owned `TRADING_FORMULA` in family `SET_ANALYTICS`.

The exact relationship supported by active evidence is:

- N-008 is not an upstream market input to F-001.
- N-008 is not itself the F-001 trigger formula.
- N-008 is not a threshold/configuration value for F-001.
- N-008 is a Set numeric precision, operation-order, serialization, and replay/checkpoint policy that F-001 must comply with to the extent F-001 is a Set-derived numeric calculation or emits/compares a named continuous Set metric.
- The catalog makes N-008 a certification dependency for F-001.

```text
F001_MUST_APPLY_N008:
PARTIALLY
```

Compliance is clear at the policy level: any Set-derived arithmetic in F-001 must use exact decimal/rational arithmetic, avoid binary floating point and epsilon comparisons, preserve formula order, round named continuous outputs to the 36-fractional-place work grid with `ROUND_HALF_EVEN`, consume persisted working dependency values, and serialize only at governed boundaries.

Concrete application to F-001 is not fully reconstructable from N-008 alone because N-008 does not define F-001's reference price, price-move formula, named output, threshold comparison, or whether F-001 persists a continuous metric in addition to a boolean trigger predicate.

```text
F001_CERTIFICATION_DEPENDS_ON_N008:
YES
```

This follows from the catalog's F-001 dependency list and from the active methodology's statement that `SET_NUMERIC_POLICY.md` is normative for all existing Set-derived arithmetic (`docs/trading-methodology/methodology/SET.md`, Append-only v1.2.14 numeric-policy addendum).

## 8. Configuration / Versioning

The stable policy identifier is:

```text
TT_SET_NUMERIC_V1
```

`docs/trading-methodology/schemas/README.md` states the package revision is `v1.2.14` and that stable policy IDs and contract-family versions are independent from the package revision.

`docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` includes `set_numeric_policy_version: TT_SET_NUMERIC_V1` in the Market Handoff shape, and `docs/trading-methodology/schemas/wire.schema.json` requires `set_numeric_policy_version` to be the constant `TT_SET_NUMERIC_V1`.

`docs/trading-methodology/schemas/NUMERIC_POLICY.md`, §7 separates Set arithmetic from monetary arithmetic: Set-derived calculations use `TT_SET_NUMERIC_V1`; monetary rules do not choose indicator seeds, square roots, or a handoff approximation.

`docs/trading-methodology/methodology/SET.md`, Append-only v1.2.14 numeric-policy addendum states that existing formulas, timeframes, trigger logic, normalization windows, and thresholds are unchanged by `TT_SET_NUMERIC_V1`. Therefore N-008 is not a configurable F-001 parameter in the active evidence; it is a stable Set numeric policy.

## 9. Boundary / Error Behavior

The following N-008 boundary and invalid-data behaviors are explicitly defined:

| Case | Canonical Behavior | Source |
|---|---|---|
| Binary floating point, context-dependent parsing, NaN, infinity | Not allowed for raw decimal source parsing. | `SET_NUMERIC_POLICY.md`, §1 |
| Equal source IDs with identical facts | Deduplicate equal source IDs. | `SET_NUMERIC_POLICY.md`, §1 |
| Equal source IDs with conflicting facts | Integrity condition. | `SET_NUMERIC_POLICY.md`, §1 |
| Ambiguous order or missing interval | Affected data are unavailable. | `SET_NUMERIC_POLICY.md`, §1 |
| Incomplete/still-forming candle | Cannot enter selected closed-candle computation range. | `SET_NUMERIC_POLICY.md`, §1 |
| Candle after fixed `as_of` cutoff | Cannot enter selected Set source range. | `SET_NUMERIC_POLICY.md`, §1 |
| Algebraic regrouping that changes rounding | Not allowed; formula order must be preserved. | `SET_NUMERIC_POLICY.md`, §2 |
| Extra intermediate rounding | Not allowed beyond the named output/state/normalization rounding points. | `SET_NUMERIC_POLICY.md`, §2 |
| Threshold epsilon | Not allowed; comparisons use exact values with no epsilon. | `SET_NUMERIC_POLICY.md`, §2 |
| Diagnostic/export serialization used for internal gates | Not allowed; diagnostic rounding must not replace internal gate values. | `SET_NUMERIC_POLICY.md`, §5 and §7 |
| Negative zero in canonical decimal strings | Not allowed. | `SET_NUMERIC_POLICY.md`, §5 |
| Invalid checkpoint ancestry | Restore only matching policy/ancestry; checkpoint retains working value plus policy/source proof. | `IDENTIFIER_LINEAGE.md`, Identifier lineage table; `SET_NUMERIC_POLICY.md`, §7 |

N-008 does not define F-001-specific boundary behavior for exactly-zero price move, threshold equality, zero denominator, malformed OHLC, trigger persistence, or LONG/SHORT semantics.

## 10. Contradictions or Source Gaps

| # | Type | Evidence | Status |
|---|---|---|---|
| 1 | CROSS_DOCUMENT_DEPENDENCY | `docs/FORMULA_METRICS_CATALOG.md` uses identifier `N-008`; active normative methodology uses policy identifier `TT_SET_NUMERIC_V1`. | Not contradictory; catalog maps N-008 to the active policy document. |
| 2 | AMBIGUOUS_WORDING | Catalog pointer says `§2 Canonical Set Value Representation`, while the active heading is `§2 Working arithmetic and operation order`. | Minor label mismatch; the referenced active section defines the numeric representation and operation-order rules. |
| 3 | MISSING_DEFINITION | N-008 does not define the F-001 price-move formula, threshold, reference price, direction handling, or trigger event. | Not an N-008 identity gap; remains relevant to F-001 reconstruction. |
| 4 | MISSING_DEFINITION | N-008 does not specify whether F-001 has a named continuous numeric output, a boolean predicate only, or both. | Concrete F-001 compliance with 36-place named-output rounding cannot be fully judged from N-008 alone. |
| 5 | NONE | No active contradiction was found between the catalog's N-008 mapping and the active `TT_SET_NUMERIC_V1` policy. | N-008 identity and general role are sufficiently evidenced. |

## 11. F001-C02 Closure Assessment

```text
F001-C02:
EVIDENCE_SUFFICIENT

N008_RUNTIME_REQUIREMENT:
YES

F001_MUST_APPLY_N008:
PARTIALLY

F001_CERTIFICATION_DEPENDS_ON_N008:
YES

CURRENT_F001_CANDIDATE_COMPATIBILITY:
CANNOT_DETERMINE
```

`F001-C02 — N-008 dependency identity/semantics unavailable` is resolved as an evidence-availability issue. The catalog identifies N-008 and maps it to `SET_NUMERIC_POLICY.md`; active methodology defines the operative policy as `TT_SET_NUMERIC_V1`.

The exact evidence resolving the dependency is:

- N-008 identity and status in `docs/FORMULA_METRICS_CATALOG.md`.
- F-001 dependency on N-008 in `docs/FORMULA_METRICS_CATALOG.md`, Certification Queue.
- The canonical N-008 rule body in `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`.
- Runtime and replay confirmation in `docs/trading-methodology/SYSTEM_PROTOCOLS.md` P16 and `docs/trading-methodology/IDENTIFIER_LINEAGE.md`.
- Set ownership and downstream consumption boundaries in `docs/trading-methodology/methodology/SET.md`, `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`, `docs/trading-methodology/schemas/wire.schema.json`, and `docs/trading-methodology/methodology/POSITION_RULES.md`.

What remains missing is not N-008 semantics; it is the exact F-001 formula and concrete F-001 application surface to which N-008 would attach. Therefore the current F-001 candidate compatibility with N-008 cannot be determined from the extracted N-008 evidence alone.

## 12. Reviewer Handoff

N-008 is the catalog identifier for `Canonical Set numeric output precision`, a Set-owned `NORMALIZATION_RULE` in `SET_ANALYTICS`, approved as defined and allowed for implementation. Its normative rule body is `TT_SET_NUMERIC_V1` in `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`.

For Set-derived numeric computation, N-008 requires exact decimal/rational arithmetic, no binary floating point, formula-order evaluation, no epsilon comparisons, one `ROUND_HALF_EVEN` rounding to the `10^-36` working grid at named continuous outputs/recursive state/normalization outputs, persisted working dependency values, governed 18-fractional-place handoff serialization where defined, canonical decimal strings, and checkpoint/source proof for replay and restart.

F-001 is catalog-declared to depend on N-008. N-008 is not an input price, threshold, or trigger formula. F-001 must comply with N-008's numeric policy to the extent F-001 performs Set-derived arithmetic or emits/compares a named continuous Set metric. The available evidence is sufficient to close the narrow N-008 identity/semantics finding, but not sufficient to certify F-001 or judge compatibility of an unspecified F-001 candidate.
