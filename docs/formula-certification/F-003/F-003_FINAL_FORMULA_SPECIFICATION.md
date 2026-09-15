# FINAL_FORMULA_SPECIFICATION

# F-003 — Set ATR and true-range calculation

**Artifact:** `F-003_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Re-Review — Cycle 3
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-003 |
| Name | Set ATR and true-range calculation |
| Formula family | SET_ANALYTICS |
| Owner | Set |
| Formula-specific candidate reviewed | `F-003_REVISED_SPEC_CYCLE_2.md`, supplied as `F-003_REVISED_SPEC_CYCLE_2(1).md` |
| Review framework | TriggerTrade — Universal Full Expert Council Formula Review Framework, as attached |
| Final approval cycle | 3 |
| Referenced methodology baseline | v1.2.14; retained provenance, not a newly published system baseline |

### Evidence and document authority

This document contains the complete approved F-003 rules and the approval record from this review. The current Cycle-2 candidate was evaluated on its own merits using all eight roles in the attached Universal Full Expert Council framework. Its `TARGET_CLOSED` labels were not accepted as proof of closure. Prior reviews, the original Source Pack and repository files were not required or used to supply missing operative rules.

Sections 2–18 restate the candidate's corresponding operative sections, remove historical-source/workflow dependencies and record the current parameter assessment. Sections 19–21 contain the final expert verdicts, closure disposition and approval record. No change to the candidate's accepted formula, parameters, numeric policy, eligibility, state continuity, ownership or wire payload is introduced by finalization.

Source digests identify only the two actual reviewed attachments; they are provenance, not independent evidence of correctness:

```text
reviewed_candidate_sha256: e3b6b10d6bd4321a505d00eeb72dc215c85125a778dd6f4625b5b3ecc6914ff6
review_framework_sha256: abdba07ed68ff222849782fab88f0c6c711f015ff4952891e3326210aa9d2034
```

The retained interface references are `TT_SET_NUMERIC_V1`, Market Handoff contract version 4, Market Data Request contract version 3, and v1.2.14 wire-schema provenance. These identifiers have separate version domains. This final formula document does not publish an amended full-system baseline, modify contract payload shapes, assign a new numeric-policy identifier or certify external source-recovery governance.

## Final Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_NARROW_ROLE_WITH_LIMITATIONS
F003-C01 = CLOSED
F003-C02 = CLOSED
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_ESTABLISHED
PARAMETER_CALIBRATION = NOT_ESTABLISHED
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies the current formula specification and conceptual fitness for its declared narrow role. It is not approval of a complete trading strategy, downstream Entry/SL/TP formulas, financial performance, an exchange implementation, or automatic recovery from revised history. The unresolved external recovery boundary in Section 18 remains explicitly non-blocking for this formula approval.

## 2. Intended Purpose

**Decision problem.** Supply a consistent scale for interpreting market-movement distances and volatility context in TriggerTrade intraday decisions.

**Market construct.** Recent completed-candle true-range magnitude, recursively smoothed in the governed series' price units; ATR_PCT expresses that work-state magnitude relative to the corresponding current completed-candle close.

**Intended downstream role.** Set-local volatility-context consumers may use the appropriate working outputs. Market Handoff provides the canonical exported ATR and ATR_PCT to Position-owned trade geometry and risk-context calculations. Entry, Stop Loss, Take Profit, economics, and trading approval remain downstream responsibilities.

F-003 measures a smoothed range statistic. It does not provide return variance, a future price-path distribution, a direction choice, or a calibrated probability of an exit outcome. Its intended contribution is a movement scale, not a standalone decision to trade. Actual improvement in TriggerTrade outcomes is not established.


## 3. Exact Formula

Throughout this document:

```text
Q_d(x) = the exact value x rounded to the decimal grid 10^-d
         using ROUND_HALF_EVEN.

H_t = High of completed candle t.
L_t = Low of completed candle t.
C_t = Close of completed candle t.
C_(t-1) = factual close of the immediately preceding candle.
A_t = persisted ATR work value for candle t.
P_t = ATR_PCT work output for candle t, when available.
```

Each index denotes canonical chronological candle order, not arrival order. Eligibility, source completeness, and ancestry requirements apply before a derived value is usable. `UNAVAILABLE` denotes absence of an eligible output, not a numeric value.

### 3.1 True Range

```text
TR_t = max(
    H_t - L_t,
    abs(H_t - C_(t-1)),
    abs(L_t - C_(t-1))
)
```

TR has the same price unit as its factual inputs. Differences, absolute values, and the maximum are evaluated exactly. No standalone intermediate TR quantizer is added before the seed mean or recursive update.

The current close participates in candle eligibility and subsequent predecessor binding even though it is not a direct operand of the current TR expression. The predecessor close is not required to fall within the current candle's range.

### 3.2 ATR Seed

Canonical parameters remain:

```text
input_timeframe = 15m
window = 14
smoothing = Wilder
```

The canonical anchor remains the **first complete native candle history for the instrument/series with factual preceding close available and authoritative history completeness proven**. An immutable source manifest identifies:

```text
series_id
seed_anchor
predecessor_close
source_digest
first_complete_history_evidence_ref
ordered seed_candle_ids
```

Index the first fourteen consecutive seed candles from that anchor as 1 through 14. Their factual predecessor chain includes `C_0`, the close immediately preceding candle 1.

```text
A_14 = Q_36((TR_1 + TR_2 + ... + TR_14) / 14)
```

The fourteen TR observations MUST be distinct, consecutive, eligible observations in the canonical history. Calculate their arithmetic mean exactly and round once, ROUND_HALF_EVEN, to the `10^-36` fractional grid.

Fewer than fourteen TR observations means ATR is `UNAVAILABLE`. A malformed candle does not authorize omitting an observation, moving the anchor, or selecting a later convenient block of fourteen candles. An unproven anchor/history or unproven descendant checkpoint does not authorize a rolling bootstrap or library-default initialization.

**First availability boundary:** the first ATR work state can become available at the fourteenth eligible completed seed candle, after its required source/history proof is established. Fourteen seed candles and the factual initial predecessor close are required; this does not add a requirement for a full extra predecessor-candle payload beyond the existing factual-close/provenance requirement. Positive handoff eligibility is a separate boundary.

### 3.3 Recursive Wilder ATR

For every subsequent eligible completed candle, in canonical order:

```text
A_t = Q_36((13 * A_(t-1) + TR_t) / 14)
```

`A_(t-1)` is the prior **persisted work-rounded ATR**, not an unrounded library value and not the handoff-rounded ATR. `TR_t` is the exact current TR. Multiplication, addition, and division are exact until the single `Q_36` update quantizer.

The update and processed source identity MUST be persisted together. Same-candle replay is idempotent; an out-of-order incremental fact requires ordered replay, not an additional arrival-order recurrence step. Section 11 preserves the full checkpoint/restart requirements.

Zero is a mathematically valid ATR work value. Fourteen zero TRs seed zero; from zero state the next update is `Q_36(TR_t / 14)`. Neither internal zero nor a failed positive-export condition changes the recurrence into a reset or reseed rule. An otherwise eligible zero-close candle follows Section 6.

### 3.4 ATR_PCT

When the current ATR work state is available and `C_t > 0`:

```text
P_t = Q_36((100 * A_t) / C_t)

ATR_wire_t = Q_18(A_t)
ATR_PCT_wire_t = Q_18(P_t)
```

The denominator is the close of the corresponding completed 15m candle. ATR_PCT is constructed from current **work ATR**, rounded to the work grid, and then rounded to the export grid. It MUST NOT be reconstructed from `ATR_wire_t`.

ATR_PCT is in percent units: numerical `1` denotes one percent. It is not a fractional ratio awaiting a further factor of 100. It also is not a separately smoothed series of historical per-candle percentage ranges.

When `C_t = 0`, the quotient is not evaluated: Section 6 governs ATR_PCT unavailability while preserving an otherwise valid TR/ATR progression. A missing close, malformed candle, or unavailable ATR is not converted into this otherwise-eligible zero-close case.


## 4. Inputs

All prices use the governed instrument/series' price unit and exact raw decimal values. Raw KLINES price fields retain their nonnegative decimal-string domain. No alternative price series, live reference, inferred value, or substituted snapshot is introduced.

| Input | Meaning and unit | Temporal binding | Availability requirement | Validity requirement |
|---|---|---|---|---|
| Instrument/series identity | Symbol and dataset/series to which facts and ATR ancestry belong; identifier | Bound to the persisted selection/cutoff and canonical series anchor | Proven anchor/history or authentic matching descendant state | Consistent authoritative source identity; manifest identifies `series_id` and source proof |
| Candle `high` / `H_t` | Current candle high; price | Current completed 15m interval at or before the cutoff | Required in eligible, complete selected KLINES data | Exact nonnegative decimal; `H_t >= C_t >= L_t >= 0` |
| Candle `low` / `L_t` | Current candle low; price | Same current interval | Required with the high and close | Exact nonnegative decimal; zero allowed; full Section 5 ordering must hold |
| Candle `close` / `C_t` | Current completed close; ATR_PCT denominator and next factual predecessor; price | Same current interval and evaluation binding | Required for candle eligibility and ATR_PCT | Exact nonnegative decimal; within `[L_t, H_t]`; zero uses Section 6, not a substituted value |
| Previous/predecessor close / `C_(t-1)` | Factual close immediately preceding the current interval; price | Immediate canonical predecessor; initial predecessor recorded at the seed anchor | Required for current TR and canonical seed ancestry | Exact factual nonnegative close with source proof; zero allowed; no current-range containment condition |
| Candle `open_time` | Authoritative interval-open time; UTC RFC3339 timestamp | Establishes chronological candle order | Required authoritative time | Order must be unambiguous; intervals non-overlapping and continuous |
| Candle `close_time` | Normalized exclusive interval end; UTC RFC3339 timestamp | End of the same interval | Required for membership/completion checks | Interval wholly within selected range; end no later than `as_of`; native end normalization remains documented factual normalization |
| Candle `is_closed` | Completed status; Boolean | Status of the selected interval | Required; selected candles must be completed | `true`, with `completed_only=true` selection and required finality proof |
| `as_of` and selection identity | Fixed economic evaluation cutoff and immutable selection; timestamp/identifier | Fixed before dispatch; reused for the recovered logical cycle | Required persisted cutoff/selection | `range_to <= as_of`; no future records or substitution of receipt/current time |
| Range/timeframe/count selector | KLINES dataset, range, timeframe, count, and completed-only selection; selector fields | Exact requested historical interval | Required selected coverage/count; insufficient history is not a shorter available window | `timeframe=15m`; immutable selection over the governed symbol/dataset/mode/cutoff/range/timeframe/count/completed-only/page-size fields |
| Source identity, coverage, finality and pagination proof | Factual record/interval ownership, endpoint, snapshot/page evidence and coverage envelope | Bound to the selected history and source snapshot | Coverage, pagination, finality and count checks must establish assembled availability | Consistent `source_snapshot_id`, `page_id`, page manifest, `coverage_complete`, `pagination_complete`, `expected_page_ids`, `source_finality_confirmed`, and `missing_ranges` evidence; immutable conflicts remain disqualifying |
| Prior ATR work and checkpoint | Previous canonical ATR state and its proof; price plus state envelope | Immediately preceding processed candle after seed | Authentic matching checkpoint or established canonical replay | Exact work-grid value, policy, seed manifest, processed ordinal/source identities, last candle and digest |
| Current TR | Source-derived range for the current candle; price | Current canonical completed interval | Required for seed or update | Section 3.1 applied to otherwise eligible facts; no separate intermediate rounding |
| Numeric policy identity | Governing arithmetic/serialization policy; identifier | Bound to calculation, checkpoint and handoff | Required | Retained policy reference `TT_SET_NUMERIC_V1`; handoff declares `set_numeric_policy_version` |

Raw source spelling remains provenance; numerical interpretation is exact. Authoritative record identity is required without inventing a new candle-ID field. `open_time` is a timestamp, not an additional open-price input.


## 5. Candle Eligibility

### 5.1 Complete F003-C01 rule

**Approved candle-eligibility rule — F003-C01 (CLOSED).** For F-003 eligibility, each completed KLINES candle MUST satisfy:

```text
0 <= Low <= Close <= High
```

This condition is additional to the unchanged source-identity, exact-decimal, completion, ordering, continuity, cutoff, and completeness requirements. It is necessary, not by itself sufficient, for eligibility.

If the condition is violated:

1. The candle is ineligible for F-003 and the affected F-003 computation is `UNAVAILABLE`.
2. Set MUST persist a source-validity reason. A finite result from mechanical evaluation does not make the candle or derived output eligible.
3. ATR state MUST NOT form or advance through that candle. The candle MUST NOT be skipped to continue or complete a seed.
4. Values MUST NOT be repaired, substituted, clamped, reordered, or inferred.
5. No valid Market Handoff may depend on the affected computation.

A prior valid state cannot be treated as the current state by holding it constant across the malformed interval. This rule does not authorize moving the canonical anchor or beginning a replacement seed after that interval. It does not prescribe corrected-history acceptance; Section 18 retains that boundary.

Malformed geometry by itself is an **F-003 availability/source-validity problem**. Existing immutable-source conflict semantics remain separate and apply when their own conditions are met. A geometry failure MUST NOT conceal or downgrade a known historical identity/content contradiction; Section 9 preserves accepted-ownership handling.

### 5.2 Equality and zero boundaries

The following table addresses geometry only. Every other eligibility requirement still applies.

| Boundary | Geometry outcome | F-003 consequence |
|---|---|---|
| `Low = 0`, with `0 <= Close <= High` | Admissible | No stricter lower-price threshold is introduced; zero close is handled separately |
| `Close = Low` | Admissible when the full ordering holds | If the common value is zero, apply Section 6 |
| `Close = High` | Admissible when the full ordering holds | No interior-close requirement is introduced |
| `High = Low = Close = k`, where `k >= 0` | Admissible | `TR = abs(k - predecessor_close)`; it is zero only when the predecessor also equals `k` |
| `High = Low = Close = 0` | Admissible geometry | TR still uses the factual predecessor; ATR_PCT is unavailable under Section 6 |
| `High = Low` but `Close` differs from that common value | Malformed | Section 5.1 applies |
| `High < Low` | Malformed | Section 5.1 applies, even if mechanical TR would be finite |
| `Close > High` or `Close < Low` | Malformed | Section 5.1 applies |
| Negative price field | Outside the retained raw numeric domain and admissible ordering | Not eligible; no repair or numeric substitution |

### 5.3 Predecessor-close price gaps remain valid

The predecessor close MUST NOT be required to fall between the current Low and High. A factual price gap is valid input to the two predecessor-distance terms in TR.

For example, `Low=2`, `Close=2`, `High=3`, and factual predecessor close `1` satisfy current-candle geometry and give exact `TR=max(1,2,1)=2`. This is a mathematical illustration, not a trading threshold or empirical result.

A price gap between continuous factual intervals is not a missing candle interval. Missing-interval behavior remains unchanged.


## 6. Zero-Close ATR_PCT Semantics

### 6.1 Complete F003-C02 rule

**Approved zero-close rule — F003-C02 (CLOSED).** When an **otherwise eligible** completed candle has:

```text
closed_candle_close = 0
```

Set MUST NOT perform the ATR_PCT division. The ATR_PCT work output and availability of `volatility.atr_pct_15m` are `UNAVAILABLE`. Set MUST persist the reason, and no valid Market Handoff requiring ATR_PCT may be emitted.

No denominator or result substitution is permitted. In particular, zero, a previous ratio, a minimum positive value, NaN, or infinity cannot stand in for the unavailable ratio.

Zero close alone MUST NOT discard the candle, reset ATR, invalidate otherwise valid TR, prevent an otherwise prescribed ATR update, or reset/reseed ATR ancestry.

Under Section 5, an otherwise eligible zero-close candle necessarily also has `Low=0`. A zero-close candle with `Low>0`, reversed bounds, or another eligibility failure is not within this exception: the applicable source-validity/conflict rule still governs.

### 6.2 Component-specific behavior

| Component | Required behavior for an otherwise eligible zero-close candle |
|---|---|
| Current TR | Calculate exactly from current High/Low and the factual predecessor close; current zero close does not invalidate it |
| Seed population | Its TR remains a member of the canonical consecutive seed population; count it once under existing identity rules |
| ATR before fourteen seed TRs | Remains `UNAVAILABLE` because the seed is incomplete; zero close neither waives nor changes the history requirement |
| ATR at seed completion | Form the prescribed exact fourteen-TR mean and work-rounded seed if all seed requirements are satisfied |
| ATR after seed | Perform the prescribed work-state update and persist it with the processed source identity |
| ATR_PCT work | `UNAVAILABLE`; do not evaluate either positive-ATR-over-zero or zero-over-zero |
| ATR export calculation | Follows the unchanged work-to-export rule if ATR work is available; a calculable ATR alone does not make the required volatility package valid |
| ATR_PCT wire availability | `UNAVAILABLE`; no valid required decimal field is emitted for it |
| Market Handoff | No valid handoff requiring ATR_PCT; baseline Market Handoff v4 requires that field |
| Predecessor binding | The factual zero close remains the immediate predecessor close for the next canonical eligible interval |
| ATR ancestry | Preserved; no discard, reset, gap compression, or reseed due solely to zero close |

`UNAVAILABLE` here is output availability, not a newly permitted string or null in a successful wire payload. Section 7 preserves the required decimal fields and handoff suppression.

### 6.3 Subsequent candles and preserved state

A later otherwise eligible candle with positive close computes ATR_PCT using its **then-current ATR work state**, after the ordinary update for that candle where applicable. No reseeding is permitted. If the immediately preceding eligible interval closed at zero, current TR uses that factual zero predecessor.

“Later” does not authorize crossing a missing or malformed interval. Existing continuity, identity, coverage, history and checkpoint requirements remain in force. Consecutive otherwise eligible zero-close candles continue the normal TR/ATR sequence while their ATR_PCT outputs remain unavailable.

If `ATR_work=0` and the later close is positive, ATR_PCT is mathematically zero, not an undefined quotient. It still cannot satisfy the existing positive-wire conditions. Conversely, available positive work values do not guarantee positive exports after quantization. Neither situation introduces a reset.


## 7. Outputs

| Output | Meaning and unit | Precision / representation | Role and availability |
|---|---|---|---|
| `TR_t` | Current completed-candle true range; price | Exact source-derived number; no standalone pre-seed/update rounding | Input to seed/recurrence; eligible source and factual predecessor required; can equal zero |
| Seed ATR work | First fourteen-TR arithmetic mean; price | `Q_36` once after the exact mean | First recursive state; unavailable before all seed requirements are met; zero is valid internally |
| Current ATR work / `A_t` | Canonical recursively smoothed TR; price | Persisted `10^-36` fractional-grid value | Subsequent recurrence, Set internal dependencies, and export; zero is valid internally |
| ATR wire / `volatility.atr_15m` | Exported ATR for Market Handoff; price | `Q_18(A_t)`, canonical plain decimal string | Must be positive and available in a valid handoff; Position consumes the exact received value |
| ATR_PCT work / `P_t` | Current work ATR relative to current completed close; percent | `Q_36(100*A_t/C_t)` when the quotient is defined | Set internal volatility-context consumers and export; unavailable at zero close or unavailable required inputs |
| ATR_PCT wire / `volatility.atr_pct_15m` | Exported relative volatility; percent | `Q_18(P_t)`, canonical plain decimal string | Must be positive and available in a valid handoff; never derived from wire ATR |
| ATR checkpoint | Durable work state and ancestry evidence; state envelope | Exact work value, policy/source proof and canonical content digest | Restart/replay boundary; required contents in Section 11 |

### Availability and wire eligibility

Source assembly retains its existing `AVAILABLE`, `PARTIAL`, and `UNAVAILABLE` distinctions. Incomplete coverage, pagination, finality, or required history does not become an available shorter computation.

An internal numeric zero and an unavailable output are distinct. Zero TR, zero ATR work, and zero ATR_PCT work at positive close are mathematically valid results. Negative ATR does not arise from eligible nonnegative TRs under the specified mean, recurrence, and rounding.

A computed export number that is zero fails the **existing positive handoff requirement**. For example, a positive ATR work value of `10^-19` rounds to zero at `10^-18`; it cannot be emitted as a valid positive ATR field. This does not change the valid internal state into an invented small positive value.

Whenever a required output is unavailable, Set MUST persist the reason and emit no valid downstream handoff. A payload missing required volatility, or containing `UNAVAILABLE`, null, NaN, infinity, or a substituted zero as its required numeric field, is not a valid Market Handoff. No new wire union, availability field, or reason-code enumeration is introduced by this formula specification.


## 8. Precision / Rounding

### 8.1 Exact arithmetic

Retain `TT_SET_NUMERIC_V1` arithmetic semantics. Raw decimal values MUST be parsed exactly using their integer/scale meaning. Binary floating point, context-dependent parsing, NaN and infinity are prohibited. Signed integer/scale parsing does not relax the raw nonnegative price domain.

Inputs, differences, sums, products and defined rational quotients are exact in the written formula order until the prescribed quantizer. No epsilon comparison, hidden library rounding, or additional TR/input quantizer is introduced.

### 8.2 Working grid and HALF_EVEN

The work grid is `10^-36`, meaning **36 fractional decimal places**, not 36 significant digits. All integer digits are retained for large values.

ROUND_HALF_EVEN selects the nearest grid value; an exact halfway tie selects the grid value whose integer grid coefficient is even. The seed mean and every recursive update are each rounded once to this grid. ATR_PCT is computed exactly from work ATR and positive close, then rounded once to this grid.

### 8.3 Dependency precision and export

A named dependency is consumed at its persisted working value. Hidden precision beyond that value MUST NOT feed recurrence, an internal dependency, or an export.

```text
TR facts -> exact seed mean -> Q_36 -> ATR work
prior ATR work + exact current TR -> exact recurrence -> Q_36 -> ATR work
ATR work -> Q_18 -> ATR export
ATR work + current positive close -> exact percent quotient -> Q_36
    -> ATR_PCT work -> Q_18 -> ATR_PCT export
```

The zero-close branch bypasses the percent quotient only; it does not bypass an otherwise required ATR update. ATR export MUST NOT feed the recurrence, and ATR_PCT MUST NOT be calculated from exported ATR.

### 8.4 Serialization and execution separation

Exports use plain canonical decimal strings: no exponent, plus sign, negative zero, redundant leading integer zero, or trailing fractional zeros. The export grid is not a requirement to pad every value to eighteen printed decimals. The wire value contains no percent symbol. Applicable object serialization remains sorted-key compact UTF-8 JSON.

Position uses exactly the received values and the existing exact rational comparison semantics, including cross multiplication for ratio comparisons. Display rounding MUST NOT feed a gate. The optional presentation of a percent symbol is not defined here.

Exchange tick/quantity increments, fees and execution rounding do not alter F-003's analytical arithmetic or work state. This document adds no execution quantizer or exchange-specific price assumption. Downstream execution constraints remain separate from the ATR calculation.


## 9. Missing / Invalid Data Behavior

The following table consolidates the approved availability, source-integrity and replay rules, including the malformed-candle and zero-close branches.

| Case | Required F-003 behavior |
|---|---|
| Fewer than fourteen consecutive seed TRs | ATR `UNAVAILABLE`; no shorter mean or alternative bootstrap |
| Unproven anchor or first-complete-history evidence | ATR `UNAVAILABLE` unless authentic matching descendant ancestry is established; no fetch-local reseed |
| Missing factual predecessor close | Affected TR/ATR unavailable; do not infer the close or substitute a bootstrap |
| Missing required current high, low or close | Required source/eligibility evidence is incomplete; affected computation remains unavailable; missing is not zero |
| Missing candle interval | `UNAVAILABLE` until resolved under existing source rules; do not skip, compress time, shift the history, or replace it with a current snapshot |
| Incomplete coverage, finality, count or page manifest | Retain source `PARTIAL`/`UNAVAILABLE` as applicable; affected calculation must not claim complete availability |
| Incomplete/still-forming candle | Must not participate; does not satisfy a required completed interval |
| Candle ending after `as_of` / future record | Must not participate; a future record is invalid for the selection |
| Ambiguous authoritative order or unresolved continuity | Affected recursive computation `UNAVAILABLE` until resolved |
| Malformed geometry | Apply Section 5: ineligible, source-validity reason persisted, no state formation/advancement or skipping, no valid dependent handoff |
| Otherwise eligible zero close | Apply Section 6: retain ordinary TR/ATR progression and factual predecessor, but ATR_PCT unavailable and no valid required handoff |
| Zero close with another eligibility failure | The zero-close branch does not waive the other failure; malformed/source-conflicting history must not advance |
| Zero work ATR with positive close | Valid zero internal state and zero internal ratio; existing positive-wire requirements prevent a valid zero-valued volatility handoff |
| Positive work value rounded to zero export | Preserve the work value; no valid handoff using the non-positive required export; do not clamp or reseed |
| Invalid, mismatched or unauthenticated checkpoint | Do not restore it. Only authentic matching state or full replay from proven identical canonical ancestry can establish ATR; otherwise unavailable |
| Identical repeated source identity with identical content | Deduplicate; do not count another seed observation or perform another update |
| Equal source identity with conflicting content | Existing integrity condition; not last-arrival-wins and not ordinary duplicate processing |
| Changed immutable record/page content | Invalidate assembled eligibility and block new handoffs under existing historical-integrity rules |
| Out-of-order incremental fact | Ordered replay, not another arrival-order recursive update |
| Revised historical source | Invalidate affected derived state; prohibit inconsistent continuation and preserve frozen handoffs; no recovery acceptance is invented |
| Conflicting historical ownership or echo identities | Resolve accepted ownership first; preserve original facts, invalidate challenged assembly, and block new analysis/handoff as required |

### Historical identity is not bypassed by semantic rejection

Known accepted request/selection/page/snapshot/native-source relationships MUST be resolved before relying on incoming echo identities. Historical contradictions must still receive their existing integrity treatment when the incoming payload also fails geometry validation. C01 cannot erase a challenge or downgrade a changed immutable record into only an ordinary source-validity reason.

Conversely, malformed geometry alone does not create an immutable-identity conflict where its independent conditions are absent. No new integrity taxonomy or conflict-recovery rule is introduced.

Required unavailable volatility continues to mean persisted reason and no valid downstream handoff. The existing Position `MISSING_ATR` treatment for missing or non-positive received ATR is retained as a neighboring boundary, not as permission for Set to emit an invalid handoff.


## 10. Time and History Basis

F-003 uses **15m completed candles**. KLINES selection is `completed_only=true`; each normalized interval `[open_time, close_time)` must be wholly contained in `[range_from, range_to)`. `close_time` is the exclusive interval end.

Candle order is the authoritative interval-open order, with non-overlap and continuity verified. Arrival order, arbitrary fetch page order, and duplicate arrival do not define the recurrence.

`as_of` is the fixed economic evaluation cutoff, not request time, receipt time, or a newly selected current time. Set persists the cutoff and dataset selectors before dispatch; the recovered cycle reuses them. `range_to <= as_of`, and no candle ending after the cutoff participates. A completed candle ending exactly at `as_of` can participate when it belongs to the selection and satisfies all remaining requirements. Required volatility values remain bound to the match/evaluation cutoff and fully available as-of `matched_at` under the retained Market Handoff boundary.

Canonical seed ancestry remains series-specific and proof-bound. Different API-fetch starting points do not authorize different seeds. An existing matching descendant checkpoint may supply established ancestry; an unproven arbitrary truncated history may not.

### Analytical populations are not recursive ancestry

The neighboring ordinary normalization/percentile baseline remains **30 completed UTC calendar days**, with its existing **14 completed UTC calendar day** minimum warmup. A completed UTC day is `[00:00:00Z, next 00:00:00Z)`; the analytical lookback excludes the current incomplete UTC day. Those same-symbol populations are not F-003's seed population.

The fourteen-TR seed is not fourteen days. Wilder recurrence does not become a rolling fourteen-candle replacement mean after seeding. Neither a new UTC day nor movement of an analytical window resets ATR ancestry.

ATR percentile remains Set-local neighboring context and is not a required baseline Market Handoff field or a required Position dependency. This formula specification does not define or approve the neighboring percentile, normalization, score or Position formulas.


## 11. Replay / Restart

### 11.1 Required durable evidence

The seed manifest retains `series_id`, `seed_anchor`, `predecessor_close`, `source_digest`, `first_complete_history_evidence_ref`, and ordered `seed_candle_ids`.

The seed checkpoint MUST include all fourteen ordered source candle identities and their TR values, plus the last processed candle. A scalar ATR is not a complete seed checkpoint.

A checkpoint retains the numeric policy, seed manifest, processed ordinal/source identities, last candle, exact work value, canonical content digest, and policy/source proof. `selection_id` remains bound to the fixed symbol/dataset/window/cutoff; snapshot/page identities bind the governed source snapshot; indicator checkpoint identity binds the numeric state and source-manifest digest.

No additional standalone TR-retention requirement beyond the existing seed/checkpoint/update evidence is introduced.

### 11.2 Continuation and equality requirements

The update and processed source identity MUST be persisted together. Same-candle replay MUST NOT advance ATR again. Out-of-order incremental facts require canonical ordered replay.

Restore only authentic matching state and replay subsequent canonical ordered facts. Full replay from the identical anchor MUST match matching-checkpoint continuation byte for byte in the canonical results. Exported ATR is not a permissible substitute for checkpoint work ATR.

After restart, Set reassembles the exact immutable selection and requires complete selected coverage before affected data become available. Neither restart nor fetch truncation permits a different economic cutoff, alternate source, rolling seed, or new ancestry.

These rules also apply when the latest processed candle has zero close: its otherwise valid ATR update and processed identity remain state even though no valid ATR_PCT handoff was emitted. Restart must not repeat that update or discard it solely because handoff emission was blocked. C01, conversely, never authorizes an update through a malformed candle.

### 11.3 Historical revisions and frozen outputs

Revised historical source invalidates affected derived state. Historical evidence challenges invalidate the current assembly and block new analysis/handoff generation. Previously frozen handoffs remain immutable; inconsistent history MUST NOT be spliced into them.

C01/C02 do not relax authentic matching-state or source-eligibility requirements. They do not define migration of existing checkpoints, acceptance of replacement history, or release from reconciliation. That unresolved boundary is retained in Section 18.


## 12. Ownership and Boundaries

| Component / boundary | Preserved responsibility |
|---|---|
| Set | Chooses the governed analytical selection/cutoff, owns volatility calculation and derived state, applies F-003 eligibility/availability, persists required evidence/reasons, and produces the frozen market-analysis payload |
| API | Supplies and factually normalizes the selected market data and provenance; does not choose a regime, trigger, analytical window, reference or fallback for Set |
| Market Handoff | Carries `volatility.atr_15m`, `volatility.atr_pct_15m`, and `set_numeric_policy_version: TT_SET_NUMERIC_V1` under the retained version-4 boundary |
| Position Rules | Consumes and validates exact canonical received volatility values; owns downstream trade geometry/economics within its existing scope |

Position MUST NOT recompute or reseed ATR, recover extra precision from another source, call back into Set to reconstruct/reinterpret the match, or use display rounding in a gate. Position has no direct API dependency.

Set internal named dependencies use their prescribed work values; Position uses exported values. The two precision boundaries are deliberate and MUST NOT be interchanged. C01/C02 add no direct Position/API edge, new output field, downstream formula, or altered Entry/SL/TP rule.


## 13. Approved Uses

**Approval scope:** Full Council approval covers the following narrow uses. It does not certify profitability, parameter optimality, downstream formula correctness, calibration, or live-deployment safety.

| Intended role | Permitted interpretation and boundary |
|---|---|
| Volatility scale | A recent observed-range magnitude in source price units |
| Normalized volatility context | That work-state range magnitude relative to the current completed close, expressed in percent |
| Conditional trade-geometry input | One input for interpreting distances used by existing Position-owned Entry/SL/TP geometry; not proof that the resulting geometry is profitable or executable |
| One component of risk context | Context for observed movement magnitude; not a complete model of loss, exposure, execution or tail outcomes |

These are inputs to existing decisions, not new signals or approval gates. Conceptual appropriateness of the narrow role does not establish parameter optimality, downstream empirical benefit, calibration, or live-deployment safety.


## 14. Prohibited Interpretations

F-003 alone MUST NOT be interpreted as any of the following:

| Prohibited interpretation | Limitation of the actual construct |
|---|---|
| LONG/SHORT or other direction signal | Magnitude does not select a direction |
| Trade-quality score | Range does not establish entry quality or positive economic edge |
| Liquidity measure | It does not measure spread, depth, traded size/activity, or executable capacity |
| Expected-return forecast | It does not estimate conditional net future return |
| Continuation probability | It does not estimate whether a current move will persist |
| Target-hit probability | An ATR-scaled distance is not a calibrated probability of reaching a target within a holding horizon |
| Stop-before-target or target-before-stop probability | Candle range and smoothing do not establish intrabar sequence or exit ordering |
| Complete regime classifier | Trend, range and other market structures can share the same ATR/ATR_PCT |
| Complete risk model | It does not encompass all exposure, tail-loss, execution, liquidation or portfolio risks |

Low ATR must not be treated by itself as evidence of safety; high ATR must not be treated by itself as evidence of an attractive opportunity. Decimal precision is numerical representation, not statistical confidence. These role boundaries do not add replacement trading formulas.


## 15. Known Limitations

### 15.1 Measurement and trading limitations retained

| Limitation | Retained consequence |
|---|---|
| Backward-looking input | F-003 summarizes completed historical intervals, not the unresolved path of the current forming candle |
| Wilder lag | Smoothing responds gradually to volatility expansion and contraction; adequate timing for actual TriggerTrade decision/holding horizons remains empirical |
| Shock/outlier persistence | Large genuine ranges can affect later ATR values; no clipping, winsorization, outlier filter or replacement indicator is added |
| Intrabar path loss | Identical candle inputs can hide different oscillation patterns or target/stop ordering |
| Microstructure information absent | Illiquid wicks and well-traded extremes can produce the same range; candle completeness does not establish active liquidity |
| Sparse or stale trading | Low observed movement can coexist with limited activity or poor tradability; no new staleness heuristic is added |
| Current-close normalization | ATR_PCT divides historical price-range state by the current close, not each historical TR by its own price; denominator changes affect the normalized value |
| Cross-symbol interpretation limits | Relative-price normalization does not establish equal execution quality, risk, return distribution or opportunity across symbols |
| Near-zero/zero values | Valid internal work values can be zero or can export to zero; small positive outputs can be economically small relative to trading costs/increments |
| Extreme values | Large ATR is not an assurance of an attainable profit distance or a bound on loss |
| Execution interaction | Exchange constraints and costs can materially change effective ATR-derived geometry; F-003 itself remains independent of execution rounding |
| Limited risk/regime meaning | ATR is one movement-context input, not a full risk model, direction signal, regime classifier, or exit-order probability |

These are not newly identified specification blockers. They are not silently repaired by modifying the formula, adding thresholds, or introducing new market heuristics.

### 15.2 Other retained evidence boundaries

This formula specification does not prescribe one physical canonical candle-ID field, one complete proof-artifact shape for first native history, exact `calculated_at` metadata semantics, or additional standalone TR persistence beyond the checkpoint/update evidence specified here. Required authoritative identity, canonical ancestry, completeness proof, cutoff and checkpoint obligations still apply; unspecified representation does not authorize an arbitrary seed or source.

Percent-symbol display remains presentation-specific and unspecified; wire percent units and plain-decimal representation remain defined. No unspecified metadata convention is substituted for `as_of`.

Corrected replacement-history acceptance/release remains the separate non-blocking boundary described in Section 18.


## 16. Parameters

| Parameter | Canonical value | Specification validity | Conceptual suitability in this review | Empirical validation / calibration |
|---|---|---|---|---|
| Input timeframe | `15m` | VALID: completed native 15m candles, immutable cutoff and continuous authoritative ordering are defined | Reasonable for a completed-candle intraday movement-context input; adequacy for each consumer's decision and holding horizon is not established | `NOT ESTABLISHED`; research validation remains required |
| Window | `14` | VALID: fourteen consecutive eligible seed TRs; subsequent coefficients are exactly 13/14 and 1/14 before quantization | Reasonable smoothing-memory choice for the declared narrow role; not a rolling fourteen-candle replacement window | `NOT ESTABLISHED`; research validation remains required |
| Smoothing | `Wilder` | VALID: exact seed mean, then the specified work-rounded recursive update | Coherent recursive range smoothing; lag and shock persistence are limitations, not unrecorded promises | `NOT ESTABLISHED`; research validation remains required |

These are canonical product semantics of this approved formula, not configurable or automatically optimized research settings. All three parameters are conceptually reasonable for the declared role. None is claimed to be empirically optimal, calibrated, or validated across symbols, sides, market conditions or holding horizons.

**Mathematical interpretation, not additional product behavior.** Fourteen continuous 15m seed candles span 210 minutes (3 hours 30 minutes). After seeding, Wilder recurrence retains older history; it does not have a hard 210-minute memory cutoff. Ignoring the prescribed grid rounding, an isolated contribution decays by a factor of 13/14 per subsequent observation and halves after approximately 9.35 observations (2.34 hours at 15m spacing). This describes the recurrence, not a forecast horizon or an empirical performance finding.

Any future experimental comparison must be explicitly identified as research. It does not silently alter the canonical running formula. The empirical status remains `NOT ESTABLISHED` for timeframe, window and smoothing separately.


## 17. Empirical Validation Still Required

The following empirical questions remain unresolved. This section supplies no acceptance threshold, minimum sample count, performance guarantee, replacement indicator, or production trading rule.

### 17.1 Required cohorts and conditions

| Dimension | Required research question |
|---|---|
| ATR_PCT level / percentile | How do outcomes vary with decision-time ATR_PCT levels and, when separately defined and reviewed, the neighboring percentile? Do not use future population information |
| Symbol | Is benefit broad, or concentrated in particular symbols? Separate per-symbol and pooled effects |
| LONG / SHORT | Are geometry and economic effects consistent across sides rather than assumed symmetric? |
| Liquidity conditions | How do independently observed spread/depth/activity and execution conditions change usefulness? ATR is not the liquidity label |
| Trend / range and other regimes | Does the same ATR interpretation produce different results across prespecified market-condition cohorts? |
| Volatility expansion / contraction | Does smoothing lag impair or improve the actual decision geometry during transitions? |
| Shock aftermath | How does decaying shock influence differ from ordinary volatility and from the shock event itself? |
| Decision / holding horizon | Is the 15m completed-candle update and period-14 memory suited to the duration over which each consumer acts? |
| Execution-cost conditions | Does any apparent benefit survive relevant fees, spread, slippage and funding where applicable? |

### 17.2 Required outcomes

Assess maximum adverse excursion (MAE), maximum favorable excursion (MFE), stop rate with loss severity/timing, target reachability, planned/effective/realized risk-reward (R:R), net P/L, drawdown, and fee/slippage sensitivity.

MAE/MFE should distinguish price, percent, entry-time ATR units and initial planned-risk units, and should separate actual-exit observations from a separately defined fixed-horizon diagnostic. Stop rate alone cannot establish better risk if loss magnitude or holding time changes.

Target reachability concerns reaching the target before the stop or horizon expiry, not merely observing the target price at some later time. Exit-order claims require adequate path evidence; candle extrema do not authorize assuming a favorable target/stop sequence.

Effective geometry must account for applicable execution constraints and costs. Portfolio drawdown and clustering/concentration effects must be distinguished from isolated trade outcomes.

### 17.3 Attribution and evidence discipline

Use prespecified comparisons that isolate the incremental contribution of ATR-dependent decisions at comparable risk. Do not substitute zero for ATR in a consumer requiring positive ATR and call that a valid comparison. Any variant or comparator must have an explicit research definition, not an implicit production change.

Evaluate trade-level and portfolio-level effects and, where evidence allows, the opportunity population before ATR-dependent acceptance/rejection. Preserve chronological out-of-sample separation, forward observation, the number of variants considered, and uncertainty treatment appropriate to dependent/overlapping observations.

Timeframe, window, smoothing, and actual downstream use require separate empirical assessment. Conceptual suitability, precise specification, empirical effectiveness, calibration and live readiness remain different states. No new validation results are supplied by this revision.


## 18. Corrected-History Limitation

**Retained finding:** F003-C03 — non-blocking for this formula specification.

The following existing requirements remain operative: revised history invalidates affected derived state; inconsistent continuation is prohibited; historical evidence challenges invalidate assembly and block new analysis/handoff generation; already frozen handoffs are not rewritten or spliced with inconsistent facts.

This formula specification does **not** define when corrected replacement history becomes accepted, who authorizes replacement acceptance, or when reconciliation blocking is released. Those acceptance/release semantics are **outside this F-003 formula specification** and remain unresolved here.

Given duly admissible canonical ancestry, the arithmetic and ordered replay are specified. That deterministic calculation does not itself authorize a replacement source history. This formula specification introduces no automatic acceptance, unblock rule, reanchoring, reset, reseed, migration or reconciliation workflow.

The same limitation applies when resolving previously malformed historical evidence. C01 does not permit self-repair; C02 is not a correction operation at all, because an otherwise eligible factual zero close is preserved.

## 19. All Eight Final Expert Verdicts

These are the eight role-based assessments in this Full Council review. Each role assessed both specification correctness and trading fitness; none is omitted or treated as merely a vote. `APPROVE_WITH_LIMITATIONS` here means that no correction to the current F-003 specification is required, while the recorded measurement and empirical limitations remain in force.

### 19.1 Independent purpose-fit and misuse checks

In this table, **YES** approves only the scope defined in Sections 2 and 13. **All prohibited interpretations excluded** means that the role verified the exclusions of direction signal, trade-quality score, liquidity measure, expected-return forecast, continuation probability, target-before-stop/stop-before-target probability, standalone target-hit probability, complete regime classifier and complete risk model.

| Expert role | Volatility scale | Normalized volatility context | Conditional trade geometry | One risk-context component | All prohibited interpretations excluded |
|---|---|---|---|---|---|
| Senior Intraday Crypto Trader | YES | YES | YES | YES | YES |
| Market Microstructure & Order Flow Researcher | YES | YES | YES | YES | YES |
| Market Regime & Context Analyst | YES | YES | YES | YES | YES |
| Quant Strategy Researcher | YES | YES | YES | YES | YES |
| Risk & Trade Management Architect | YES | YES | YES | YES | YES |
| Execution & Exchange Mechanics Specialist | YES | YES | YES | YES | YES |
| Adversarial Strategy Reviewer | YES | YES | YES | YES | YES |
| Performance & Strategy Diagnostics Analyst | YES | YES | YES | YES | YES |

### 19.2 Senior Intraday Crypto Trader — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** ATR provides a coherent common scale for discussing observed movement distances. ATR_PCT expresses that scale relative to the current completed close. This is useful context for existing Position-owned entry/stop/target geometry and one input to risk interpretation, but neither value decides whether the proposed trade has an edge. The formula is direction-neutral; the same calculation can be consumed for LONG and SHORT without asserting symmetric outcomes.

The completed 15m input and period-14 Wilder memory are conceptually reasonable for this contextual role. Timeliness for actual trading and holding horizons remains empirical. During trend, range, breakout, reversal and shock conditions, the statistic remains interpretable as smoothed range magnitude, not as confirmation of continuation or target reachability. In low observed volatility it does not establish safety. No intrinsic limitation described here requires changing the current specification.

### 19.3 Market Microstructure & Order Flow Researcher — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** The current specification distinguishes malformed candle geometry from a valid predecessor-close price gap and from missing intervals. This preserves the construct TR is meant to measure without accepting impossible current High/Low/Close ordering. Authoritative identity, coverage, finality and source-conflict handling constrain which observations may enter the scale and its normalized context.

Candle extrema do not reveal depth, spread, traded size, activity or execution at an extreme. A wick supported by little activity and a well-traded range can produce the same inputs. Consequently, ATR-derived geometry and risk context are conditional on separate execution and liquidity evidence; ATR_PCT normalization does not supply that evidence. An admissible factual zero close is a defined data-domain case, not certification of a tradable price or permission to suppress the factual TR. The specification correctly prohibits these microstructure overinterpretations.

### 19.4 Market Regime & Context Analyst — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** F-003 measures smoothed observed-range magnitude and its current-price-normalized counterpart. It can contextualize conditional geometry and one aspect of risk across regimes without claiming to identify those regimes. Two histories can share ATR while having different trend, range or reversal structure. A high value can reflect current large movement, lingering shock influence or a change in the normalization denominator; it is not uniquely interpretable as opportunity or persistent volatility.

Wilder lag can leave context slow to catch expansion and elevated during contraction. The current document records this distinction and retains no-look-ahead completed-candle/cutoff semantics. Current-close normalization is deliberately not an average of separately normalized historical ranges. A universal directional, continuation, probability, liquidity or regime inference is excluded. Suitability across actual market-condition cohorts remains an empirical question rather than an uncorrected formula defect.

### 19.5 Quant Strategy Researcher — APPROVE_WITH_LIMITATIONS

**MATHEMATICAL_CONSEQUENCE / EXPERT_ASSESSMENT.** For eligible geometry, TR is a nonnegative price distance including genuine predecessor gaps. The exact fourteen-TR mean and the 13/14, 1/14 recurrence define a coherent range statistic. ATR remains in price units; multiplication by 100 and division by the corresponding positive close give percent units. The prescribed work quantizer precedes each downstream dependency and export; the deliberate work-to-percent-to-wire order is not interchangeable with computation from wire ATR.

C01 provides necessary eligibility without overconstraining equality or predecessor gaps. C02 removes undefined division while preserving eligible TR, seed/update state and ancestry. Canonical ordering, authenticated checkpoints and idempotent replay determine the same canonical numeric outputs given identical admissible facts. These properties support all four narrow uses but do not turn a range statistic into variance, a distribution, an expected return or an exit-order probability. The three parameters and downstream effectiveness are not empirically validated.

### 19.6 Risk & Trade Management Architect — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** A movement scale and its normalized context can inform conditional stop/target geometry and one component of risk interpretation. The approval does not equate an ATR multiple with a loss bound, a probability or an economically acceptable trade. ATR alone does not establish exposure, liquidation protection, net edge, portfolio concentration or tail safety, and the specification expressly retains those boundaries.

Malformed observations cannot contaminate future canonical ATR through advancement, skipping or carry-forward. Eligible zero-close observations preserve factual state but cannot generate a valid required volatility handoff. Tiny internal values that quantize to zero are not replaced with invented positive values. Conversely, a positive export is not a minimum economically meaningful distance. Rapid changes, large shocks and denominator effects can make an otherwise correct scale misleading when downstream consumers overinterpret it; those consumers and empirical diagnostics remain responsible for the conditional use. No additional threshold is justified by this review.

### 19.7 Execution & Exchange Mechanics Specialist — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** Exact source-price units, percent units, 36-place work values, 18-place exports and canonical decimal strings make the intended analytical values unambiguous. The export grid is not an exchange tick size or a guarantee of executable distance. Position receives the specified wire values rather than hidden precision, and analytical recurrence is not altered by tick/quantity increments or execution rounding.

Both the absolute scale and normalized context are meaningful as conditional inputs to trade geometry and one part of risk context, but actual constraints, fees, spread, slippage and funding can change the effective result. Positive handoff fields do not establish exchange admissibility or cost coverage. Undefined ATR_PCT cannot be encoded as NaN, infinity, null, a placeholder or a stale ratio in a successful handoff. The separation of analytical ownership from execution mechanics is coherent; no new exchange-specific assumption or direct Position/API edge is needed for this formula approval.

### 19.8 Adversarial Strategy Reviewer — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT.** The specification withstands the material boundary distinctions: equal High/Low/Close with and without a predecessor gap; reversed bounds; close outside the range; eligible zero close versus zero close with invalid geometry; zero work ATR versus unavailable ATR_PCT; and positive work values that export to zero. Source duplicates cannot repeat a seed observation or recurrence update. Out-of-order facts cannot create an arrival-order indicator. A geometry failure cannot conceal an independently established immutable-source conflict.

These controls protect the volatility scale, normalized context, conditional geometry input and risk-context contribution from specified source/state errors. They do not protect against every factual wick, sparse market or unfavorable subsequent price path, and they do not authorize any prohibited interpretation. Corrected-history acceptance remains externally unresolved and cannot be used as an implicit unblock or reseed. No remaining specification counterexample requiring revision was identified; this is not proof against every possible implementation or trading failure.

### 19.9 Performance & Strategy Diagnostics Analyst — APPROVE_WITH_LIMITATIONS

**EXPERT_ASSESSMENT / EMPIRICAL_QUESTION.** The absolute scale, current-close-normalized context, conditional geometry role and limited risk-context role are conceptually coherent and sufficiently specified for controlled empirical evaluation. None of those four judgments establishes realized improvement. The document correctly separates conceptual appropriateness, specification certification, empirical effectiveness, calibration and live readiness.

Required diagnostics cover symbols, LONG/SHORT, independently measured liquidity, regimes, expansion/contraction, shock aftermath, horizons and costs. MAE/MFE, stop severity/timing, target-before-stop or horizon outcomes, effective and realized R:R, net P/L and portfolio drawdown are appropriate research questions for the declared use. Chronological out-of-sample/forward evidence, comparable-risk attribution and dependence-aware uncertainty remain necessary. The absence of performance evidence is preserved rather than converted into a favorable claim. It does not prevent approval of a defined contextual formula whose specification makes no empirical-success promise.

### 19.10 Consolidated construct and fitness record

```text
INTENDED_PURPOSE
Decision problem being solved: Provide a consistent observed-movement scale and normalized volatility context for existing intraday decisions.
Market/economic construct intended to measure: Completed-candle true-range magnitude smoothed with the specified Wilder recurrence; the work-state magnitude relative to the corresponding current close.
How the result is used by TriggerTrade: Set-local prescribed work-value dependencies and canonical volatility exports to Position Rules.
What downstream decision it influences: Conditional interpretation of existing Entry/SL/TP geometry and one component of risk context; not direction or standalone trade approval.

ACTUAL_CONSTRUCT
What the formula actually measures: A canonical, work-rounded recursive true-range statistic in price units, plus its current-close-normalized percent value when defined.
What it does not measure: Direction, economic edge, liquidity, expected return, continuation, exit-order probabilities, a complete regime or complete risk distribution.
Where the proxy is strong: Reproducible comparison of observed movement magnitudes, including factual price gaps, within the declared price/history basis.
Where the proxy is weak: Intrabar path, executable liquidity, sudden regime changes, forward outcomes, tail losses and cross-symbol equivalence beyond relative price scale.

FITNESS_FOR_PURPOSE
Adequate for declared role: YES
Primary strengths: Coherent range construct; explicit normalization; canonical ancestry; exact numeric boundaries; source eligibility; deterministic state continuity.
Primary limitations: Backward-looking aggregation, lag, shock persistence, missing microstructure/path information, current-close denominator effects and non-equivalence of normalized risk across symbols.
Known misuse risks: Treating ATR/ATR_PCT as any interpretation prohibited in Section 14.
Market regimes where reliability may degrade: Reliability as forward decision context can degrade during rapid expansion/contraction, shocks, reversals, sparse/stale trading or abrupt price-level changes; this does not change the historical statistic it measures.
Downstream decisions where use is appropriate: Existing conditional geometry and limited movement-risk context with separate economic/execution evaluation.
Downstream decisions where use would be inappropriate: Standalone direction, trade-quality, liquidity, expected-return, continuation, target/stop probability, complete regime or complete risk decisions.
Empirical validation still required: YES; all requirements in Section 17 remain unresolved.
```

## 20. Final Closure and Findings Disposition

### 20.1 F003-C01 — CLOSED

Section 5 defines `0 <= Low <= Close <= High` and valid equality cases. Violations make the candle ineligible and the affected computation unavailable, require a persisted source-validity reason, prohibit seed formation or recurrence advancement through the candle, prohibit skipping/carry-forward/reanchoring and repair/substitution, and block a valid dependent Market Handoff. The predecessor close may lie outside the current range. Source-integrity challenges retain separate treatment.

These semantics agree with Sections 3–4, 7–9 and 11. No contradictory requirement authorizes advancement through a malformed candle, a replacement seed, an otherwise invalid handoff or exclusion of a valid factual price gap.

### 20.2 F003-C02 — CLOSED

Section 6 prohibits ATR_PCT division at an otherwise eligible zero close. Both the percent work output and required wire-field availability are unavailable; no denominator or result substitute is permitted, and the required handoff is blocked. Eligible TR remains valid and counts toward the seed or ordinary update. Work state, source identity and ATR ancestry are preserved. The factual zero close remains the immediate predecessor close; the next otherwise eligible positive-close interval uses the then-current ordinary state without reseeding.

These semantics agree with Sections 3–4 and 7–11. No contradictory requirement discards the zero-close observation, evaluates zero-over-zero, uses a stale denominator/ratio, loses the update on restart or crosses a missing/malformed interval.

### 20.3 Remaining limitations, not required revisions

| Item | Current disposition | Approval consequence |
|---|---|---|
| F003-C03 — corrected-history acceptance/release | `SOURCE_GAP`; explicitly outside the formula scope and non-blocking here | Remains unresolved. No authority to accept replacement history or release reconciliation follows from this approval |
| Parameter and downstream-performance questions, including the candidate's F003-C04/C05 research topics | `EMPIRICAL_QUESTION`; validation not established | Research remains necessary; no optimization or effectiveness claim is made |
| ATR measurement, lag, microstructure, normalization and execution limitations | `EXPERT_ASSESSMENT` / `MATHEMATICAL_CONSEQUENCE`; explicitly scoped | Do not invalidate the four narrow approved uses |
| Additional blocking specification findings | NONE IDENTIFIED | No required formula correction and no Cycle-3 revised candidate |

**Blocking findings remaining: NONE.** No issue requires correction to this current formula specification. The external history-recovery boundary is not silently closed, and no downstream formula or live-trading safety finding is inferred from this result.

### 20.4 Review evidence classification

`SUPPORTED_BY_SOURCE_PACK` is the framework's label for supplied normative evidence; in this cycle it denotes the current complete Cycle-2 candidate, not retrieval of a historical Source Pack. Its explicit formula, eligibility, availability, history, precision, ownership and replay rules supply the specification basis. Arithmetic examples and recurrence properties are `MATHEMATICAL_CONSEQUENCE`. Suitability judgments are `EXPERT_ASSESSMENT`. Performance and calibration remain `EMPIRICAL_QUESTION`. The external corrected-history governance boundary remains `SOURCE_GAP`. No `PROPOSED_CHANGE` to operative F-003 behavior is required.

The review used source inspection and synthetic exact-arithmetic checks, not TriggerTrade repository tests, an exchange integration, market-data validation or a backtest. Numeric replay checks establish equality for the reviewed arithmetic examples, not certification of an unseen implementation or its persistence infrastructure.

## 21. Final Approval Record

```text
FINAL_COUNCIL_RECORD

formula_id: F-003
formula_name: Set ATR and true-range calculation

senior_intraday_crypto_trader: APPROVE_WITH_LIMITATIONS
microstructure_order_flow_researcher: APPROVE_WITH_LIMITATIONS
market_regime_context_analyst: APPROVE_WITH_LIMITATIONS
quant_strategy_researcher: APPROVE_WITH_LIMITATIONS
risk_trade_management_architect: APPROVE_WITH_LIMITATIONS
execution_exchange_mechanics_specialist: APPROVE_WITH_LIMITATIONS
adversarial_strategy_reviewer: APPROVE_WITH_LIMITATIONS
performance_strategy_diagnostics_analyst: APPROVE_WITH_LIMITATIONS

F003-C01: CLOSED
F003-C02: CLOSED

blocking_findings_remaining: NONE

full_council_approved: YES
another_review_cycle_required: NO
```
