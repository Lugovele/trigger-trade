# F-001 SOURCE PACK

## 1. Formula Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-001 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Price-move trigger calculation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Set | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | TRIGGER | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Expected family in task | SET_ANALYTICS | Discrepancy: catalog says `TRIGGER`, not `SET_ANALYTICS`. |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/SET.md` :: trigger/setup conditions | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog current implementation pointer | `src/triggertrade/triggers/percentage_price_move.py::PercentagePriceMoveTrigger.evaluate` LEGACY/DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/README.md`, package revision/status; `docs/trading-methodology/methodology/SET.md`, header |

Catalog note: "Current code computes percentage move, but canonical Set trigger semantics must be certified before final backend implementation" (`docs/FORMULA_METRICS_CATALOG.md`, Master Catalog). The catalog also states that archived methodology is not normative authority.

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Classification Model; Master Catalog; Formula Certification Queue; Traceability Cross-Check | CATALOG / GATE | Identifies F-001, classification, current demo implementation, dependencies and backend gate. |
| 2 | `docs/trading-methodology/README.md` | Package revision/status | VERSION BASELINE | Establishes active v1.2.14 methodology baseline. |
| 3 | `docs/trading-methodology/methodology/SET.md` | Header and Purpose | PRIMARY SET METHODOLOGY | Defines Set as market-analysis owner and lists Set formation/Trigger composition among responsibilities. |
| 4 | `docs/trading-methodology/methodology/SET.md` | Part I §1 Purpose | TRADING CONTEXT | Set answers whether market configuration formed and what direction it implies. |
| 5 | `docs/trading-methodology/methodology/SET.md` | Part I §2.1 and §2.1A | SCOPE / FORMATION EPOCH | Defines Coins OPEN/CLOSE active analysis scope and formation epoch reset/carryover behavior. |
| 6 | `docs/trading-methodology/methodology/SET.md` | Part I §3 Set responsibilities | OWNERSHIP | Set evaluates approved Triggers, combines them, tracks formation state and determines match/direction. |
| 7 | `docs/trading-methodology/methodology/SET.md` | Part I §4 Set outputs | OUTPUT CONTRACT | Defines unmatched evaluation versus matched Set Result and Market Handoff creation. |
| 8 | `docs/trading-methodology/methodology/SET.md` | Part I §5 Direction belongs to Set | DIRECTION BOUNDARY | Direction is Set-owned; matched Set emits deterministic LONG or SHORT. |
| 9 | `docs/trading-methodology/methodology/SET.md` | Part I §6 Market Handoff | OUTPUT / OWNERSHIP | Market Handoff carries frozen market-analysis payload; Position must not reconstruct/reinterpret original match. |
| 10 | `docs/trading-methodology/methodology/SET.md` | Part I §8 Trigger composition | TRIGGER GOVERNANCE | A Set is composed only from approved versioned Triggers; no hidden metric conditions in prose/operators. |
| 11 | `docs/trading-methodology/methodology/SET.md` | Part I §9 Boolean logic | TRIGGER COMPOSITION | Defines tri-state AND/OR/NOT and "Missing evidence is not negative evidence." |
| 12 | `docs/trading-methodology/methodology/SET.md` | Part I §10 Trigger result and event contract | TRIGGER STATE / REPLAY | Defines TRUE/FALSE/UNAVAILABLE, evaluation identity, CURRENT_STATE, FRESH_EVENT, timestamp, durable identity, restart. |
| 13 | `docs/trading-methodology/methodology/SET.md` | Part I §§11-12 Sequence and temporal windows | TIME SEMANTICS | Defines trigger ordering, strict `THEN`, window anchors and no receipt/restart time substitution. |
| 14 | `docs/trading-methodology/methodology/SET.md` | Part I §§16-20 Lifetime, freshness, reset, re-arm, active attempt | STATE / LIFECYCLE | Defines freshness anchors, reset causes, re-arm policies and one active formation state per Set/version/symbol/epoch. |
| 15 | `docs/trading-methodology/methodology/SET.md` | Part I §§22-24 Multi-timeframe Sets, completion timestamp, identity | VERSION / TIME | Preserves Trigger timeframes and defines `matched_at` and material Set identity. |
| 16 | `docs/trading-methodology/methodology/SET.md` | Part I §26 Runtime auditability | AUDIT | Requires reconstruction of OPEN symbol, Set/version, matched Triggers, match time, direction and handoff values. |
| 17 | `docs/trading-methodology/methodology/SET.md` | Part III §43.1 Context production rules | DOWNSTREAM BINDING | Matched trigger occurrence/reference bindings are producer-bound; Position consumes/validates result. |
| 18 | `docs/trading-methodology/methodology/SET.md` | Part III §44 Missing-data semantics | AVAILABILITY | Unavailable analysis fact is not zero/false; missing required value prevents valid handoff. |
| 19 | `docs/trading-methodology/methodology/SET.md` | Deterministic numeric and historical-source representation; V05 historical evidence eligibility | NUMERIC / SOURCE INTEGRITY | Declares SET_NUMERIC_POLICY normative for Set arithmetic and selectors; missing/incomplete/conflicting history remains PARTIAL/UNAVAILABLE. |
| 20 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | Header; §1 Source identity; §2 Working arithmetic | NUMERIC POLICY | Set owns derived state; exact decimals/no binary float; source identity/order/completeness; 36-place work grid for named continuous Set metrics. |
| 21 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | §§1-7 and appendices | INPUT CONTRACT | Set chooses selections; API provides factual data only; defines TICKER/KLINES fields, availability, coverage, source finality, no future data and restart/page rules. |
| 22 | `docs/trading-methodology/business-contracts/COINS.md` | Purpose, Semantics, Ordering and delta semantics | INPUT CONTRACT | Portfolio Rules opens/closes analysis scope; OPEN creates fresh formation epoch; new epoch inherits no old pre-MATCH Trigger state. |
| 23 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Producer and reference provenance; Canonical payloads | OUTPUT CONTRACT | Concrete MATCHED Core Set creates handoff; event-dependent formation must satisfy Set trigger contract; no Frozen Condition in handoff. |
| 24 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P1, P16, P17, V05, X02 | CROSS-DOCUMENT PROTOCOL | Topology, trigger/event contract summary, historical selectors, immutable config binding, contradiction/replay behavior. |
| 25 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` | Decision cycle, formation epoch/config binding, Trigger evaluation / event binding | IDENTITY / REPLAY | Defines owner and persistence of Set formation epoch and Trigger evaluation/event lineage. |
| 26 | `src/triggertrade/triggers/percentage_price_move.py` | `PercentagePriceMoveTrigger.evaluate` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Legacy/demo formula currently computes `(current - previous) / previous * 100 <= threshold_pct`; catalog labels implementation LEGACY/DEMO_ONLY. |
| 27 | `src/triggertrade/config/settings.py` | `TriggerRuleConfig`; env load | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo defaults/config source: rule/version, lookback `1m`, threshold `-1.0`, stale_after `60`. |
| 28 | `src/triggertrade/persistence/trigger_set_store.py` | `current_rule_definitions` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo rule registry records `price_change_pct <= configured demo threshold pct`, inclusive LTE, demo-only. |
| 29 | `tests/unit/test_trg_001_percentage_price_move.py` | Unit tests | NON-NORMATIVE TEST EVIDENCE | Shows current demo boundary behavior for `-1.0%` threshold; not methodology authority. |

## 3. Formula Purpose and Trading Context

The active Set methodology says Set is the market-analysis component and in `INITIAL_ANALYSIS` answers whether the required market configuration has formed for a requested coin and what direction that configuration implies (`docs/trading-methodology/methodology/SET.md`, Part I §1). Set analyzes only symbols whose latest Portfolio Rules coin status is `OPEN` (`SET.md`, Part I §3.1; `COINS.md`, Semantics). F-001 is catalogued as a Set-owned Trigger formula; the certification queue says "Trigger activation affects candidate Set formation" (`docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue).

The active methodology does not provide a named canonical F-001 price-move predicate. It provides the generic trigger/result/event framework into which a configured price-move Trigger would fit. `SET.md` Part I §8 requires every atomic market test to be an explicitly governed, versioned Trigger and says Set must not hide new metric conditions inside prose/operators. `SET.md` Part I §10 then says that the generic Trigger contract defines no market predicate, signal, threshold or analysis heuristic.

Source-supported purpose:

- Explicit: F-001 is a Set Trigger whose activation can affect candidate Set formation (`docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue).
- Explicit: Set combines approved Triggers, tracks formation state and determines whether a Set is matched (`SET.md`, Part I §3.1).
- Not established by active methodology: the trading rationale for price-move magnitude, whether the trigger is bullish/bearish, or whether it encodes a dip-buy, breakout, momentum or mean-reversion thesis.

## 4. Exact Formula Reconstruction

### Active methodology reconstruction

`MISSING_CANONICAL_DEFINITION`

No active `docs/trading-methodology/` section found in this extraction defines the exact F-001 price-move formula: no canonical numerator, denominator, current/reference price, timeframe, sign/absolute treatment, threshold value, or comparison operator is specified for "Price-move trigger calculation." The catalog points only to "`SET.md` :: trigger/setup conditions", but the relevant SET.md trigger sections define generic Trigger mechanics and explicitly state they define no market predicate, signal, threshold or heuristic.

The following F-001-specific elements are therefore not canonically reconstructable from active methodology:

- whether the measured event is open-to-close, previous-close-to-current-close, anchor-to-current, low-to-high, last-price-to-prior-last, or another source;
- whether the move is signed or absolute;
- whether multiplication by 100 is part of the canonical formula;
- whether equality passes or fails;
- threshold value/provenance;
- direction semantics.

### Non-normative current implementation evidence

The catalog labels `src/triggertrade/triggers/percentage_price_move.py::PercentagePriceMoveTrigger.evaluate` as LEGACY/DEMO_ONLY. That implementation computes:

```text
price_change_pct = ((current - previous) / previous) * 100
condition_result = price_change_pct <= threshold_pct
```

It returns `BUY_CANDIDATE` if the condition is true, otherwise `NO_SIGNAL`; it rejects wrong symbol, wrong window, missing prices, non-positive previous price and stale observations. The demo config default is rule `TRG-001`, version `0.1.0`, status `DRAFT_DEMO_ONLY`, lookback `1m`, threshold `-1.0`, stale-after `60` seconds (`src/triggertrade/config/settings.py`, `TriggerRuleConfig`).

This implementation evidence is not used as normative formula authority because the catalog itself says canonical Set trigger semantics must be certified before final backend implementation.

## 5. Inputs

| Input | Meaning | Unit | Source | Timeframe / temporal binding | Required? | Validity / provenance |
|---|---|---|---|---|---|---|
| `symbol` | Instrument/symbol under Set analysis | Identifier | Active: `COINS.md`; `MARKET_DATA_REQUEST.md`; generic Trigger binding in `SET.md` §10.1 | Bound to latest OPEN formation epoch and persisted selection | Required | Trigger evaluation binds symbol, epoch, config and source identities. |
| Active analysis scope | Whether Set may analyze symbol | OPEN/CLOSE state | `COINS.md`; `SET.md` §2.1 and §3.1 | Latest monotonic `scope_revision`; OPEN creates active formation epoch | Required | Older delayed revisions cannot overwrite newer state; CLOSE resets unfinished formation. |
| Trigger ID/version | Configured Trigger identity | Identifier/version | `SET.md` §10.1 and §24; `IDENTIFIER_LINEAGE.md` | Bound to active OPEN formation epoch | Required | Pinned Set/Trigger/Core Set configuration binding must survive replay/restart. |
| Configuration/content digest | Versioned Trigger/Core Set configuration | Identifier/version/digest | `SYSTEM_PROTOCOLS.md` P17; `SET.md` §2.1A | Selected when OPEN epoch starts; retained by MATCHED cycle | Required | Later configuration edits do not affect already-started epoch/cycle. |
| Evaluation as-of/selection | Governed instant/source selection for evaluating predicate | UTC timestamp plus source selector | `SET.md` §10.1; `MARKET_DATA_REQUEST.md` §§1-3 | Must be explicit; not receipt/restart/loop time | Required | Evaluation result bound to exact as-of/selection and source evidence identities. |
| Price input(s) | Price(s) used by price-move formula | Decimal price | Active: NOT EXPLICITLY SPECIFIED for F-001. Possible factual fields are TICKER `last_price/mark_price/index_price` or KLINES OHLC/close in `MARKET_DATA_REQUEST.md` §7. | NOT EXPLICITLY SPECIFIED | Required by formula but undefined | API provides factual data only; cannot choose market logic/fallback. |
| Current/reference price basis | Which current and comparison prices enter formula | Decimal price | NOT EXPLICITLY SPECIFIED in active methodology | NOT EXPLICITLY SPECIFIED | Required by formula but undefined | Source gap blocks exact reconstruction. |
| Price-move threshold | Threshold for trigger TRUE/FALSE | Percent or price units | NOT EXPLICITLY SPECIFIED in active methodology. Demo implementation uses env `TRIGGERTRADE_TRG_001_THRESHOLD_PCT`. | Pinned configuration if used | Required by formula but undefined | P17 requires configured thresholds to be immutable for started epochs; active threshold value absent. |
| Completed candle status | Whether completed candles are required if KLINES used | Boolean | `MARKET_DATA_REQUEST.md` §§3,5,7; `SET_NUMERIC_POLICY.md` §1 | KLINES select closed intervals wholly contained in interval; no candle ending after as_of | Conditional: only if F-001 uses KLINES | Generic rule exists; F-001 source dataset not specified. |
| Source coverage/finality | Proof selected source data is complete/final | Coverage envelope | `MARKET_DATA_REQUEST.md` §§4-5 and appendices | Per selection/page/source snapshot | Required for factual selected data | Missing/partial/conflicting history remains unavailable/reconciling. |
| Prior Trigger state | Retained preceding result for FRESH_EVENT | TRUE/FALSE/UNAVAILABLE plus timestamp | `SET.md` §10.3-§10.5; `IDENTIFIER_LINEAGE.md` | Same active formation epoch | Required if role is FRESH_EVENT | UNAVAILABLE interrupts transition; no bridge; event consumed once. |

## 6. Outputs

| Output | Meaning | Unit / type | Precision | Consumer | Source |
|---|---|---|---|---|---|
| Trigger evaluation result | Result of configured Trigger predicate | `TRUE`, `FALSE`, `UNAVAILABLE` | Discrete | Set formation engine | `SET.md` §10.1 |
| Authoritative effective timestamp | Governed instant at which predicate is established | UTC timestamp | Exact; not rounded for event timing | Set sequencing/windows/freshness | `SET.md` §10.1 and §10.4 |
| CURRENT_STATE satisfaction | State role satisfied when current authoritative result is TRUE | Boolean role satisfaction | Discrete | Set expression/formation | `SET.md` §10.2 |
| FRESH_EVENT | FALSE -> TRUE transition event in same active epoch | Event identity + `event_at` | Discrete + exact timestamp | Set sequencing/windows/freshness | `SET.md` §10.3-§10.5 |
| Consumed-event record | Deduplication/consumption of event by formation role | State record | Exact identity binding | Replay/restart/formation | `SET.md` §10.5 |
| Matched constituent evidence | Trigger occurrence and references that participated in matched Set | IDs and references | Discrete | Set Result / Market Handoff context binding | `SET.md` §4.1 and §43.1; `MARKET_HANDOFF.md` |
| Price-move numeric value | Numeric price-move percentage/amount | NOT EXPLICITLY SPECIFIED | NOT EXPLICITLY SPECIFIED | Not canonically exposed | Source gap |

The demo implementation emits a `Signal` with `condition_result`, `signal_type`, `reason`, `input_snapshot`, and deterministic `signal_id`, but this is non-normative legacy/demo evidence.

## 7. Thresholds and Parameters

| Parameter | Active canonical status | Value / behavior | Evidence |
|---|---|---|---|
| Price-move threshold | MISSING_CANONICAL_DEFINITION | Active methodology does not define F-001 threshold value or comparison operator. | `SET.md` generic Trigger contract; catalog points to trigger/setup conditions but no predicate found. |
| Trigger timeframe/lookback | MISSING_CANONICAL_DEFINITION | Active methodology says Triggers preserve own timeframe/horizon/window, but F-001 timeframe/lookback is not defined. | `SET.md` §22 |
| Trigger state/event mode | Must be explicit in Set configuration | CURRENT_STATE or FRESH_EVENT are distinct; omitted role invalid for SINCE_SET_ARMED. | `SET.md` §17 |
| Configuration pinning | Hard canonical lifecycle rule | Config selected for OPEN epoch/cycle is immutable; later edits apply only to new epoch/cycle. | `SYSTEM_PROTOCOLS.md` P17; `SET.md` §2.1A |
| Demo threshold | Non-normative implementation/config evidence | Default `-1.0`; env `TRIGGERTRADE_TRG_001_THRESHOLD_PCT`; inclusive `<=` in demo registry. | `settings.py`; `trigger_set_store.py` |
| Demo lookback | Non-normative implementation/config evidence | Default `1m`; env `TRIGGERTRADE_TRG_001_LOOKBACK_WINDOW`. | `settings.py`; `trigger_set_store.py` |

No active methodology source classifies F-001 price-move threshold as hard canonical, configuration, or research parameter. P17 supplies generic configuration pinning if a threshold exists.

## 8. Direction / Sign Semantics

Active methodology establishes that market direction belongs to Set and a matched Set must emit deterministic `LONG` or `SHORT` (`SET.md` §5). It also states direction may be fixed by Set definition or explicitly determined by matched branch.

For F-001 specifically:

- Signed versus absolute price move is not defined in active methodology.
- Positive versus negative price move treatment is not defined.
- Whether F-001 determines direction, only supplies one Trigger condition, or only participates in a branch is not defined.
- No active source states that price increase means LONG or price decrease means SHORT for F-001.

The non-normative demo implementation is signed and checks `price_change_pct <= threshold_pct`, with default negative threshold, returning `BUY_CANDIDATE`; this should not be treated as canonical direction semantics.

## 9. Domain and Preconditions

| Domain / precondition | Active canonical evidence | F-001 completeness |
|---|---|---|
| Active symbol scope | Set analyzes only latest OPEN symbols; CLOSE stops new-opportunity analysis. | Complete for scope. |
| Formation epoch | Each effective newer OPEN establishes fresh epoch; CLOSE/newer OPEN resets unfinished pre-MATCH state. | Complete for generic trigger use. |
| Approved Trigger | Set composed only from approved Triggers; new atomic market tests require explicitly governed versioned Trigger. | Complete generic rule; F-001 predicate missing. |
| Price fields | Market Data Request offers TICKER and KLINES price fields; API does not choose market logic. | Incomplete for F-001; exact field/source missing. |
| Completed candle | If KLINES used, closed intervals only, completed_only=true, no still-forming candle. | Conditional; F-001 does not specify KLINES use. |
| As-of cutoff | Set fixes as_of; no future facts; range_to <= as_of. | Complete generic input rule. |
| Source completeness | Complete coverage/finality/page manifest required for AVAILABLE. | Complete generic input rule. |
| Numeric domain | Exact decimals/no binary floating point; NaN/infinity forbidden. | Complete generic numeric rule; F-001 zero denominator/domain missing. |
| Missing evidence | Missing evidence is not negative evidence; unavailable result remains UNAVAILABLE. | Complete generic trigger rule. |

## 10. Boundary Conditions

| Boundary case | Active canonical behavior | Reconstruction status |
|---|---|---|
| Exactly zero movement | Not defined for F-001; no canonical formula/threshold. | Source gap |
| Exactly equal to threshold | Not defined in active methodology. Demo uses inclusive `<=`, but non-normative. | Source gap |
| Infinitesimally below/above threshold | Numeric policy forbids epsilon and requires exact comparisons for Set thresholds, but F-001 operator/threshold absent. | Partial generic rule |
| Zero denominator | Not defined for F-001. Demo treats previous price <= 0 as invalid/no signal; non-normative. | Source gap |
| Negative/zero raw price | KLINES/TICKER schema patterns permit nonnegative decimal strings; F-001 positive-price requirements absent. | Source gap |
| Malformed OHLC | KLINES schema has fields/patterns; OHLC relation constraints not defined for F-001. | Source gap |
| Incomplete candle | If KLINES used, still-forming candle invalid and no candle ending after as_of participates. F-001 data source undefined. | Partial generic rule |
| Missing candle / missing selected data | Missing selected data remains unavailable to affected Set computation. | Generic behavior defined |
| Duplicate data | Identical duplicate pages no-op; same accepted evaluation duplicate not new. | Generic behavior defined |
| Conflicting source data | Changed page/native record/evaluation identity content is integrity/reconciliation condition; blocks new handoffs. | Generic behavior defined |
| Future candle / future record | Any record after as_of invalid; candle ending after as_of excluded. | Generic behavior defined |
| Candle ending exactly at range_to | Completed candle/bucket whose exclusive end equals range_to is included. | Generic behavior defined |
| Initial TRUE | CURRENT_STATE may be satisfied; FRESH_EVENT not created. | Generic trigger behavior defined |
| UNAVAILABLE -> TRUE | CURRENT_STATE may be satisfied; FRESH_EVENT never created by itself. | Generic trigger behavior defined |
| Long-lived TRUE | Does not fire on every evaluation/restart. | Generic trigger behavior defined |

## 11. Precision and Rounding

`TT_SET_NUMERIC_V1` governs Set-derived arithmetic (`SET_NUMERIC_POLICY.md`, header; `SET.md`, deterministic numeric representation). It requires raw decimals parsed exactly as signed integer/scale values; binary floating point, context-dependent parsing, NaN and infinity are forbidden (`SET_NUMERIC_POLICY.md`, §1).

For named continuous Set metric outputs, recursive updates and normalization outputs, the work grid is `10^-36` with ROUND_HALF_EVEN (`SET_NUMERIC_POLICY.md`, §2). Formula order must be preserved; algebraic regrouping must not introduce extra rounding. Percent conversion is exact factor 100 or 1/100; comparisons use canonical values without epsilon.

F-001 gap: active methodology does not state whether the price-move calculation is a named continuous Set metric output subject to work-grid persistence, or a Trigger-local predicate-only intermediate. It also does not define the price-move export/serialization class because no F-001 numeric output is specified as a Market Handoff field.

## 12. Time / Candle Semantics

Active generic time rules:

- Set persists each market-data selection before dispatch; `as_of` is fixed economic evaluation cutoff, not request/receipt time (`MARKET_DATA_REQUEST.md`, §§2-3).
- KLINES select closed intervals wholly contained in `[range_from, range_to)` with exact timeframe and `completed_only=true` (`MARKET_DATA_REQUEST.md`, §3).
- TICKER and other AS_OF datasets return factual point snapshots effective at or before cutoff; no current snapshot substitution is allowed (`MARKET_DATA_REQUEST.md`, §3).
- Trigger evaluation effective timestamp is the governed market/evaluation instant and may not be receipt, loop, restart or wall-clock time (`SET.md`, §10.1).
- FRESH_EVENT `event_at` is the TRUE evaluation timestamp for a proven FALSE -> TRUE transition (`SET.md`, §10.4).
- Set `matched_at` is the final step timestamp for sequences, or first evaluation timestamp at which complete Boolean expression is TRUE (`SET.md`, §23).

F-001 gaps:

- Source timeframe is not defined.
- Current versus previous candle/reference selection is not defined.
- Whether F-001 uses completed bars, AS_OF ticker, raw trades or another source is not defined.
- Whether F-001 is evaluated once, repeatedly per completed candle, or by another cadence is not explicitly defined; generic Set evaluation occurs while symbol is OPEN and one active formation state exists.
- Later arriving data: generic source-integrity rules say contradicted accepted source evidence invalidates current assembly and blocks new analysis/handoff, preserving already frozen handoffs; F-001-specific correction policy is not defined.

## 13. Trigger Formation Semantics

F-001 participates in the generic Set Trigger framework only to the extent configured as a Trigger. Active semantics:

- A Trigger evaluation result is exactly `TRUE`, `FALSE` or `UNAVAILABLE`; `UNAVAILABLE` is not FALSE and interrupts transition proof (`SET.md` §10.1).
- `CURRENT_STATE(T)` is satisfied when current authoritative result is TRUE and declared validity/as-of requirements hold (`SET.md` §10.2).
- `FRESH_EVENT(T)` requires a newly accepted TRUE whose immediately relevant retained prior result in the same active formation epoch is FALSE (`SET.md` §10.3).
- `FALSE -> UNAVAILABLE -> TRUE` does not create a FRESH_EVENT; `UNAVAILABLE -> FALSE -> TRUE` does (`SET.md` §10.3 table).
- Trigger roles and freshness/windows must be explicit; SINCE_SET_ARMED must identify whether role is CURRENT_STATE or FRESH_EVENT (`SET.md` §17).
- Set composition supports explicit AND/OR/NOT tri-state logic; missing evidence is not negative evidence (`SET.md` §9).

What F-001 does within this framework is not fully defined:

- It may be configured as CURRENT_STATE or FRESH_EVENT, but active docs do not specify which.
- It may be one condition among several in a Core Set, but active docs do not define a concrete Core Set containing F-001.
- It does not canonically determine direction by itself in active methodology.

## 14. State / Replay / Restart

Generic state/replay/restart requirements that would apply to F-001 as a Trigger:

- Trigger evaluation is bound to Trigger ID/version, symbol, active OPEN formation epoch, pinned configuration, exact as-of/selection and source identities/revisions (`SET.md` §10.1).
- Distinct evaluations are applied in governed authoritative order, not delivery order (`SET.md` §10.1).
- Set durably retains last accepted result including UNAVAILABLE, predecessor/order evidence, and event identity for accepted FALSE -> TRUE transitions (`SET.md` §10.5).
- Acceptance of evaluation, recording transition event and advancing/consuming it must be one durable atomic update or staged until complete (`SET.md` §10.5).
- Hydration restores retained Trigger results, interruptions, event identities, consumed flags and deadlines before accepting new evaluations (`SET.md` §10.5).
- New OPEN epoch inherits no old pre-MATCH Trigger state; no old FRESH_EVENT crosses epoch boundary (`SET.md` §10.6; `COINS.md`, Ordering and delta semantics).
- P17 pins configuration for started epoch/cycle and forbids consulting latest config on replay/restart (`SYSTEM_PROTOCOLS.md` P17).
- P16 and Market Data Request require exact selection reassembly after restart and complete coverage before AVAILABLE (`SYSTEM_PROTOCOLS.md` P16; `MARKET_DATA_REQUEST.md` §5).

F-001-specific calculation state, if any, is not defined. The active docs do not say whether F-001 persists a price-move work value, only the generic Trigger evaluation/event state.

## 15. Version / Configuration Pinning

Set material identity includes Set ID, version, Trigger IDs/versions, Boolean/sequence structure, state/event modes, time windows, freshness, expiry, reset, re-arm, N-of-M, direction mapping and exact constituent/reference provenance (`SET.md` §24). Changing a material component creates a new Set version.

SYSTEM_PROTOCOLS P17 requires immutable configuration binding for started cycles/attempts. Set binds unfinished formation to the Set/Trigger/Core Set configuration selected when the current OPEN epoch is created; a MATCHED cycle retains that exact binding. Later activation/editing applies only to future epochs/cycles.

F-001 gaps:

- No active methodology defines canonical Trigger ID/version for F-001 beyond catalog ID F-001.
- No active methodology defines a canonical parameter snapshot for F-001.
- No active methodology defines threshold/config version for F-001.

Non-normative current code/demo registry uses `TRG-001` versions `0.1.0` and `0.2.0`; the demo registry marks v0.2.0 as demo-only with no profitability claim.

## 16. Ownership and Responsibility

Set owns market analysis, Trigger evaluation, Set formation state, match/direction and Market Handoff (`SET.md`, Purpose and Part I §3). Portfolio Rules owns only whether symbols are OPEN/CLOSE for analysis (`COINS.md`, Ownership). API is factual transport/normalization and does not choose market regime, trigger, history window, reference or fallback (`MARKET_DATA_REQUEST.md`, §1). Position Rules consumes the frozen Market Handoff and must not call back into Set to reconstruct/reinterpret the original match (`SET.md` §6; `MARKET_HANDOFF.md`, Producer and reference provenance).

For F-001:

- Calculation owner: Set, if/when F-001 is defined as a Set Trigger.
- Parameter/configuration owner: Set/Trigger/Core Set configuration under P17, but specific F-001 threshold owner/value is missing.
- API role: provide requested factual market data only.
- Downstream recomputation: Position consumes the frozen Set result/Market Handoff; no active source permits downstream recomputation of F-001.

## 17. Downstream Consumers

| Consumer | Relationship | Evidence |
|---|---|---|
| Set formation engine | F-001 Trigger activation may affect candidate Set formation. | Catalog certification queue; `SET.md` §3 and §8 |
| Core Set / matched Set Result | If configured as a constituent, matched output records `trigger_id`, `trigger_version`, `trigger_occurrence_id`. | `SET.md` §4.1 |
| Market Handoff | Only a concrete MATCHED Set produces Market Handoff; trigger occurrence/reference bindings may appear in contexts/origin_binding. | `SET.md` §6 and §43.1; `MARKET_HANDOFF.md` |
| Position Rules | Consumes final frozen Market Handoff/direction/context, not raw F-001 metric. | `SET.md` §6; `MARKET_HANDOFF.md` |
| F-004 | Catalog lists F-004 depending on F-001, F-002, F-003. | `docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue |
| F-005 | Catalog lists F-005 depending on F-004; F-001 is indirect through F-004 if applicable. | `docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue |

No active methodology source found that exposes a F-001 numeric value as a required Market Handoff field.

## 18. Neighboring Formula Relationships

| Neighbor | Relationship | Basis |
|---|---|---|
| F-002 Volume confirmation | Independent sibling Trigger formula; catalog says F-002 affects whether Set evidence is eligible. Potential co-constituent relationship is not concretely defined in active methodology. | Catalog Master Catalog and Queue |
| F-003 ATR/TR | Catalog says F-001 depends on F-003 and N-008. Active methodology does not show exact F-001 use of ATR. | Catalog Queue |
| F-004 normalization/percentile/score | Downstream dependency; F-004 depends on F-001/F-002/F-003. | Catalog Queue |
| F-005 direction classifier | Indirect downstream via F-004; Set direction itself is Set-owned and matched Set must emit LONG/SHORT. | Catalog Queue; `SET.md` §5 |
| Set trigger formation | Direct generic framework; F-001 would evaluate TRUE/FALSE/UNAVAILABLE and may satisfy CURRENT_STATE or FRESH_EVENT if configured. | `SET.md` §§8-12, §17 |
| Set lifecycle | Direct generic formation lifecycle; F-001 can contribute to ARMED/PARTIALLY_MATCHED/MATCHED depending on configuration, but concrete role absent. | `SET.md` §§15-20 |
| Market Handoff | Indirect; only after complete Set MATCHED. F-001 raw formula output is not listed as a handoff field. | `SET.md` §4.1 and §6; `MARKET_HANDOFF.md` |
| Threshold/config object | Generic P17 pinning applies, but concrete F-001 threshold object absent in active methodology. | `SYSTEM_PROTOCOLS.md` P17 |

## 19. Worked / Conformance Examples Present in Source

No active `docs/trading-methodology/` worked example for F-001 price-move calculation was found.

Relevant generic examples:

- `SET.md` §10.3 provides a table of Trigger retained history showing when CURRENT_STATE is satisfied and when FRESH_EVENT is created.
- `SET.md` §2.1A and `COINS.md` provide OPEN/CLOSE revision examples showing formation epoch reset/carryover behavior.

Non-normative demo unit tests include boundary examples:

- previous 100, current 99.00, threshold -1.0 -> BUY_CANDIDATE;
- previous 100, current 99.01 -> NO_SIGNAL;
- previous 100, current 98.99 -> BUY_CANDIDATE.

Those tests reflect current demo implementation only; they are not active methodology authority.

## 20. Source Gaps and Ambiguities

| # | Gap | Evidence | Potential Divergence | Exact Reconstruction Impact |
|---:|---|---|---|---|
| 1 | Exact price-move formula is missing. | Catalog points to `SET.md` trigger/setup conditions; `SET.md` §10 says generic contract defines no market predicate/signal/threshold. | Implementations may choose previous-close/current-close, open-close, anchor-current, high-low, signed/absolute. | Blocks exact formula reconstruction. |
| 2 | Numerator and denominator are undefined. | No active F-001 formula section found. | Division by previous price versus current price versus anchor price changes magnitude and sign. | Blocks exact formula reconstruction. |
| 3 | Price source field is undefined. | Market Data Request offers TICKER prices, KLINES OHLC, raw trades; API cannot choose logic. | Implementations may use last_price, close, mark_price, index_price, or trade price. | Blocks exact input reconstruction. |
| 4 | Timeframe/lookback is undefined. | `SET.md` §22 says Triggers preserve own timeframe/horizon/window, but F-001 does not define one. | Implementations may use 1m, 15m, N bars, rolling windows, or AS_OF points. | Blocks exact time semantics. |
| 5 | Completed-candle requirement for F-001 is undefined. | KLINES closed-candle rules exist, but F-001 source dataset absent. | Implementations may evaluate still-forming prices versus completed candles. | Blocks boundary/time reconstruction. |
| 6 | Threshold value/provenance is undefined. | Active docs do not define F-001 threshold; demo env default is non-normative. | Different thresholds change trigger truth and certification result. | Blocks exact formula reconstruction. |
| 7 | Comparison operator/equality boundary is undefined. | Active docs do not define operator; demo uses `<=` non-normatively. | Equality may pass/fail; greater/less direction may invert. | Blocks boundary behavior. |
| 8 | Sign and absolute-value semantics are undefined. | No active F-001 formula; Set direction is separate. | Positive and negative moves may be treated asymmetrically, symmetrically, or directionally. | Blocks direction/sign reconstruction. |
| 9 | Direction role of F-001 is undefined. | `SET.md` says direction belongs to Set; no concrete F-001 branch mapping. | Implementations may treat F-001 as direction-neutral filter, LONG-only, SHORT-only, or branch-specific. | Blocks direction semantics. |
| 10 | Zero denominator behavior is undefined. | Active docs do not define denominator; demo rejects previous <= 0 non-normatively. | Implementations may return UNAVAILABLE, FALSE, zero, exception, or invalid evidence. | Blocks domain/boundary reconstruction. |
| 11 | Output numeric persistence is undefined. | SET_NUMERIC_POLICY defines named continuous metric work grid but no F-001 output name/handoff field. | Implementations may persist raw, rounded, not persist, or serialize differently. | Blocks output/precision reconstruction. |
| 12 | Trigger role mode is undefined. | Generic CURRENT_STATE/FRESH_EVENT rules exist; F-001 role in a Set is not specified. | Implementations may require current TRUE or fresh FALSE->TRUE event. | Blocks formation semantics. |
| 13 | Concrete Core Set containing F-001 is undefined. | Set composition rules generic; no concrete setup conditions found for F-001. | F-001 may be single trigger, one of many, sequence step, reset trigger, or maintained trigger. | Blocks trading context. |
| 14 | Malformed price/OHLC domain is incomplete. | Schemas permit nonnegative decimal strings; active F-001 does not define OHLC relation or positive price requirements. | Implementations may accept/reject zero, high<low, or close outside OHLC differently. | Blocks input-domain completeness. |
| 15 | Evaluation cadence is undefined. | Generic Set active formation while OPEN; no F-001 cadence/selector. | Implementations may evaluate per tick, per completed candle, per page assembly, or scheduler loop. | Blocks time semantics. |
| 16 | Later historical corrections for F-001-specific state are undefined beyond generic source invalidation. | P16/V05/X02 block new analysis on contradictions but no corrected-history acceptance policy for F-001. | Implementations may rebuild, remain reconciling, or handle frozen/unmatched states differently. | Partially blocks replay specifics. |
| 17 | Catalog formula family discrepancy. | Task expects SET_ANALYTICS; catalog says TRIGGER. | Reviewers may scope F-001 as trigger activation versus broader Set analytics. | Does not block formula math, but affects classification. |
| 18 | Current implementation and active methodology authority are separated. | Catalog labels implementation LEGACY/DEMO_ONLY and says canonical semantics must be certified. | Implementers may accidentally promote demo `(current-previous)/previous*100 <= threshold`. | Blocks using implementation as canonical proof. |

## 21. Reviewer Handoff Summary

```text
FORMULA_ID: F-001
FORMULA_NAME: Price-move trigger calculation

EXACT_FORMULA_RECONSTRUCTABLE:
NO

DECLARED_TRADING_PURPOSE_RECONSTRUCTABLE:
PARTIALLY

INPUT_DOMAIN_COMPLETE:
NO

BOUNDARY_BEHAVIOR_COMPLETE:
NO

TIME_SEMANTICS_COMPLETE:
NO

DIRECTION_SEMANTICS_COMPLETE:
NO

PARAMETER_PROVENANCE_COMPLETE:
NO

STATE_REPLAY_SEMANTICS_COMPLETE:
YES

SOURCE_GAP_COUNT:
18

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
- Active methodology does not define the exact F-001 price-move formula.
- Active methodology does not define F-001 price source, timeframe/lookback, threshold, operator, sign treatment, equality boundary, or direction role.
- Current implementation provides only legacy/demo evidence and is explicitly not canonical authority.
```
