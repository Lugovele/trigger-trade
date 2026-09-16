# F-002 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-002 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Volume confirmation calculation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Set | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | TRIGGER | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/SET.md` :: volume/setup confirmation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog current implementation pointer | `src/triggertrade/triggers/volume_confirmation.py::{median_decimal, empirical_percentile_rank, RobustVolumeConfirmationTrigger.evaluate}` LEGACY/DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/README.md`; `docs/trading-methodology/methodology/SET.md` |

Catalog note: "Current code contains median and percentile mechanics; canonical use requires formula certification."

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Classification Model; Master Catalog; Formula Certification Queue | CATALOG / GATE | Identifies F-002, classification, dependency and implementation gate. |
| 2 | `docs/trading-methodology/methodology/SET.md` | Header and Purpose | PRIMARY SET METHODOLOGY | Defines Set as market-analysis owner. |
| 3 | `docs/trading-methodology/methodology/SET.md` | Part I §§8-12 and §17 | TRIGGER FRAMEWORK | Defines approved Trigger composition, tri-state result, CURRENT_STATE/FRESH_EVENT and windows. |
| 4 | `docs/trading-methodology/methodology/SET.md` | Part I §9 | TRI-STATE LOGIC | Missing evidence is not negative evidence; UNAVAILABLE is distinct. |
| 5 | `docs/trading-methodology/methodology/SET.md` | Part I §10 | TRIGGER RESULT / EVENT CONTRACT | Generic Trigger contract; explicitly does not define a market predicate, signal, threshold or heuristic. |
| 6 | `docs/trading-methodology/methodology/SET.md` | Part II §6 | ORDINARY NORMALIZATION CALENDAR | Defines 30 completed UTC calendar days and 14-day warmup for ordinary normalization baselines. |
| 7 | `docs/trading-methodology/methodology/SET.md` | Part II §8 | TIME_OF_DAY_RELATIVE_TURNOVER | Defines a canonical turnover ratio using quote notional turnover and median prior same-clock 5m bucket. |
| 8 | `docs/trading-methodology/methodology/SET.md` | Part II §21 | AGGRESSIVE_VOLUME_DELTA_PCT | Defines an aggressive-volume delta metric using quote notional raw trades. |
| 9 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §§1-2, §5, §7 | NUMERIC POLICY / N-008 | Defines exact decimal parsing, source ordering/completeness, no binary float, no epsilon, working-grid rules and integer/rational count semantics. |
| 10 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | Response datasets | INPUT CONTRACT | Defines KLINES `volume`, VOLUME point value, RAW_TRADES and QUOTE_TURNOVER factual payloads. |
| 11 | `docs/trading-methodology/business-contracts/COINS.md` | OPEN/CLOSE analysis scope | INPUT CONTRACT | Defines Set analysis scope and formation epoch reset/carryover. |
| 12 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Producer and provenance | OUTPUT CONTRACT | Matched Core Set creates handoff; Trigger occurrences/references may be provenance. |
| 13 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P16, P17, V05 | CROSS-DOCUMENT PROTOCOL | Source eligibility, fixed selectors, replay/restart, immutable config binding and contradiction behavior. |
| 14 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` | Trigger evaluation / event binding | IDENTITY / REPLAY | Defines Set-owned formation epoch and Trigger evaluation/event lineage. |
| 15 | `src/triggertrade/triggers/volume_confirmation.py` | `RobustVolumeConfirmationTrigger.evaluate`; helpers | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo implementation for median, relative volume and empirical percentile. |
| 16 | `src/triggertrade/persistence/trigger_set_store.py` | TRG-VOLUME rule definitions and recommendation | NON-NORMATIVE CANDIDATE EVIDENCE | Candidate rule `relative_volume >= 2.0 AND volume_percentile >= 90`; TESTING candidate, not ACTIVE proof. |
| 17 | `tests/unit/test_trg_002_volume_confirmation.py` | Unit tests | NON-NORMATIVE TEST EVIDENCE | Confirms demo helper behavior and fail-closed cases. |

## 3. Purpose and Trading Context

F-002 is catalogued as a Set-owned Trigger formula. The certification queue says confirmation affects whether Set evidence is eligible. Set is the market-analysis component; it evaluates approved Triggers, combines them, tracks formation state and produces a matched Set Result and Market Handoff only when its configured logic is satisfied.

The active methodology does not provide a named canonical F-002 volume-confirmation predicate. It provides generic Trigger mechanics, Set numeric/source policy, several volume-related Set analytics, and factual market-data payload shapes.

Source-supported purpose:

- F-002 is intended as a volume confirmation Trigger that can participate in Set formation.
- The likely trading construct is abnormal or meaningful participation accompanying a price/setup condition.
- Active methodology does not establish whether F-002 is a required filter, optional diagnostic, CURRENT_STATE, FRESH_EVENT, branch-specific constituent, or Set-local analytics input.

## 4. Exact Formula Reconstruction

### Active methodology reconstruction

```text
MISSING_CANONICAL_DEFINITION
```

No active methodology section found in this extraction defines the exact F-002 volume confirmation formula. The catalog points to `SET.md` volume/setup confirmation, but the active Set trigger sections define generic trigger mechanics and state that they do not define market predicates, signals, thresholds or analysis heuristics.

Active methodology does define related but not identical constructs:

- `TIME_OF_DAY_RELATIVE_TURNOVER`: current 5m quote turnover divided by median prior same-clock 5m turnover over prior completed eligible days.
- `AGGRESSIVE_VOLUME_DELTA_PCT`: 100 times buyer-initiated minus seller-initiated notional over their sum.
- ordinary normalization/percentile policies for Set analytics.

These do not establish the F-002 candidate rule as canonical.

### Non-normative current implementation / candidate evidence

The catalog labels the current implementation as LEGACY/DEMO_ONLY. It computes:

```text
median_volume_60 = median(previous 60 completed candle volumes)
relative_volume = current_volume / median_volume_60
volume_percentile = count(previous_volume <= current_volume) / 60 * 100
condition = relative_volume >= 2.0 AND volume_percentile >= 90
```

For the even 60-count median, the demo helper averages sorted positions 30 and 31 using one-based language, implemented as zero-based indices 29 and 30.

Candidate registry evidence records logical name `TRG-VOLUME`, rule `TRG-002@0.1.0`, condition `relative_volume >= 2.0 AND volume_percentile >= 90`, missing-data behavior `NOT_CONFIRMED` for fewer than 60 previous candles, missing current volume or zero median, and provenance as candidate recommendation `REC-TRG-VOLUME-001`, not validated profitable production rule.

This evidence is not treated as canonical formula authority because the catalog still requires certification.

## 5. Inputs

| Input | Meaning | Unit | Source | Required? | Reconstruction status |
|---|---|---|---|---|---|
| `symbol` | Instrument under Set analysis | Identifier | Generic Set/Coins scope | Required | Complete generic rule |
| Active analysis scope | OPEN/CLOSE eligibility for Set analysis | State | `COINS.md`; `SET.md` | Required | Complete generic rule |
| Trigger ID/version/config digest | Pinned Trigger identity and configuration | Identifier/version/digest | Generic Trigger/P17 | Required | Complete generic rule; F-002 concrete config source missing |
| Evaluation as-of/selection | Governed instant/source selection | UTC timestamp plus selector | Generic Set / Market Data Request | Required | Complete generic rule |
| Current volume | Current observation volume or turnover | Decimal | MARKET_DATA_REQUEST KLINES `volume`, VOLUME value, QUOTE_TURNOVER or RAW_TRADES depending on chosen construct | Required by formula | Exact canonical source not specified |
| Reference volume population | Historical comparison values | Decimal series | Not specified for F-002 | Required by candidate formulas | Missing canonical selector/window |
| Timeframe | Candle/bucket timeframe | Duration | Demo uses 1m; active related turnover metric uses 5m; active source does not define F-002 | Required | Source gap |
| Lookback length | Number or time window for reference population | Count/time | Demo uses 60 previous candles; active ordinary baseline uses 30 completed UTC days for normalization | Required | Source gap |
| Baseline statistic | Median, mean, percentile or other | Function | Active related turnover uses median; demo uses median and empirical percentile | Required | Source gap |
| Thresholds | Relative-volume and percentile thresholds | Ratio/percent | Demo uses 2.0 and 90 | Required for trigger | Source gap / candidate evidence only |
| Source coverage/finality | Proof selected data is complete/final | Evidence envelope | Market Data Request and P16/V05 | Required | Complete generic rule |

## 6. Outputs

| Output | Meaning | Unit / type | Consumer | Reconstruction status |
|---|---|---|---|---|
| Trigger evaluation result | Result of configured Trigger predicate | TRUE / FALSE / UNAVAILABLE | Set formation engine | Generic output defined; concrete predicate missing |
| Effective timestamp | Governed instant at which predicate is established | UTC timestamp | Set sequencing/windows/freshness | Generic output defined |
| FRESH_EVENT / CURRENT_STATE role | Whether current TRUE or transition event satisfies Set role | Discrete role satisfaction | Set expression/formation | Generic roles defined; F-002 role not specified |
| `relative_volume` | Candidate current/reference ratio | Ratio | Set-local diagnostics or trigger predicate | Non-normative candidate only |
| `volume_percentile` | Candidate empirical rank of current volume | Percent | Set-local diagnostics or trigger predicate | Non-normative candidate only |
| Matched constituent evidence | Trigger occurrence/provenance in matched Set | IDs/references | Set Result / Market Handoff provenance | Generic output defined |

No active source found that exposes an F-002 numeric value as a required Market Handoff field.

## 7. Units

The active market-data contracts expose several possible volume-like bases:

- KLINES `volume`: decimal-string, exchange-provided candle volume.
- VOLUME point value: decimal-string.
- QUOTE_TURNOVER: `turnover_quote` with unit USDT.
- RAW_TRADES notional quote and quantity base.

Candidate/demo evidence uses Bybit spot base volume in one rule definition and Bybit linear perpetual contract volume in another candidate definition. This creates a material basis distinction: base volume, contract volume and quote notional turnover are not interchangeable.

Canonical F-002 unit is therefore unresolved.

## 8. Parameters and Thresholds

| Parameter | Active canonical status | Candidate/demo value |
|---|---|---|
| Rule ID | Missing canonical F-002 definition | `TRG-002` / `TRG-VOLUME` in demo/candidate |
| Timeframe | Missing | `1m` in demo/candidate |
| Lookback | Missing | 60 previous completed candles |
| Relative volume threshold | Missing | `2.0` |
| Percentile threshold | Missing | `90` |
| Stale-after | Missing as canonical formula semantics | 120 seconds in demo config |
| Baseline statistic | Missing for F-002 | Median of prior 60 volumes |
| Percentile tie rule | Missing for F-002 | Count previous values `<= current` |

## 9. Sign / Direction Semantics

Volume is non-directional in the demo/candidate rule. Active methodology does not state that F-002 determines LONG or SHORT direction. Set owns direction and the matched Set emits deterministic LONG or SHORT through configured Set logic.

F-002's role appears more plausibly to confirm participation or evidence strength than to choose direction, but active methodology does not canonically state that role.

## 10. Domain and Preconditions

| Domain / precondition | Evidence | Reconstruction status |
|---|---|---|
| Active OPEN scope | Set analyzes latest OPEN symbols only | Complete generic rule |
| Completed data | Market Data Request and Set policy exclude incomplete/future candles | Complete generic rule |
| Exact decimal parsing | N-008 / TT_SET_NUMERIC_V1 | Complete generic rule |
| Source completeness/finality | Market Data Request and P16/V05 | Complete generic rule |
| Positive denominator | Demo treats median <= 0 as missing; active F-002 denominator rule missing | Source gap |
| Nonnegative raw volumes | Market-data decimal-string; exact stricter domain not extracted for F-002 | Partial generic rule |
| Consecutive previous candles | Demo uses last 60 previous candles; active F-002 selector missing | Source gap |
| Candidate current candle | Demo requires current completed candle; active F-002 source selection missing | Source gap |

## 11. Boundaries

| Boundary case | Active canonical behavior | Candidate/demo behavior |
|---|---|---|
| Exactly equal to relative threshold | Not defined for F-002 | Passes with `>= 2.0` |
| Exactly equal to percentile threshold | Not defined for F-002 | Passes with `>= 90` |
| Tied historical volumes | Integer count/rank exact semantics are generic; F-002 tie rule missing | Ties count as `<= current` |
| Fewer than required previous values | Required selected source unavailable under generic completeness; F-002 count missing | NOT_CONFIRMED with reason |
| Missing current volume | Missing required fact is UNAVAILABLE generically | NOT_CONFIRMED with reason |
| Zero median / zero denominator | F-002 denominator rule missing | NOT_CONFIRMED with reason |
| Current volume zero | F-002 rule missing | If median > 0, relative 0 and likely not confirmed |
| All previous volumes zero | F-002 rule missing | zero median -> not confirmed |
| Stale current candle | Generic as-of/freshness must be explicit | stale reason in demo |

The candidate implementation collapses many invalid/unavailable cases into `NOT_CONFIRMED`; active Set methodology distinguishes `UNAVAILABLE` from FALSE. This is a likely certification issue.

## 12. Precision

N-008 / `TT_SET_NUMERIC_V1` requires exact raw decimal parsing, no binary floating point, formula-order evaluation, exact integer/rational counts/ranks, no epsilon comparisons, and canonical working/export behavior at defined Set numeric boundaries.

F-002-specific gaps:

- Whether `relative_volume` is a named continuous Set metric output is not defined.
- Whether `volume_percentile` is a named Set metric output or trigger-local intermediate is not defined.
- Whether these candidate metrics are retained only diagnostically, participate in F-004, or appear in a handoff is not defined.

## 13. Time Semantics

Generic Set and Market Data rules require persisted `as_of`, exact selectors, completed intervals, no future data, source completeness, and replay/restart using the same selection identity.

F-002 gaps:

- canonical timeframe is not defined;
- whether the current observation is a candle, point VOLUME fact, turnover bucket, or raw-trade aggregate is not defined;
- whether reference window is 60 prior candles, 30 completed UTC calendar days, same-clock bucket, or another selector is not defined;
- whether evaluation cadence is per completed candle, per setup event, or scheduler loop is not defined.

## 14. State / Replay / Restart

Generic Trigger state applies:

- evaluations bind Trigger ID/version, symbol, active OPEN formation epoch, pinned configuration, exact as-of/selection and source evidence;
- UNAVAILABLE is retained and is not FALSE;
- FRESH_EVENT requires a proven FALSE -> TRUE transition in the same active epoch;
- duplicate evaluation identity is not a new event;
- hydration restores retained Trigger result, interruption, event identity, consumed flags and deadlines.

F-002-specific calculation state is not defined. It is not clear whether only the boolean trigger result is persisted or whether relative volume / percentile work values and reference windows are checkpointed as named Set-derived metrics.

## 15. Version / Configuration Pinning

P17 pins Set/Trigger/Core Set configuration for started epochs and matched cycles. Changing material Set/Trigger components creates a new version.

F-002 gaps:

- no active methodology defines canonical F-002 Trigger ID/version;
- no canonical parameter snapshot is defined;
- no canonical threshold/config version is defined.

Non-normative registry evidence uses `TRG-002@0.1.0` and marks it as a TESTING candidate recommendation, not validated profitable production rule.

## 16. Ownership

Set owns Trigger evaluation, Set formation state, match/direction and Market Handoff. API supplies factual data and must not choose market logic or fallback. Position consumes the frozen Market Handoff and must not reconstruct Set trigger logic.

F-002 calculation owner is Set if/when F-002 is defined as a Set Trigger. Threshold/config ownership is Set/Trigger/Core Set configuration under P17, but concrete values are missing from active methodology.

## 17. Downstream Consumers

| Consumer | Relationship | Evidence |
|---|---|---|
| Set formation engine | F-002 confirmation can affect whether Set evidence is eligible. | Catalog queue |
| Core Set / matched Set Result | If configured as a constituent, matched output records trigger occurrence/provenance. | Generic Set output contract |
| F-004 | Catalog lists F-004 depending on F-001, F-002 and F-003. | Catalog queue |
| F-005 | Indirect via F-004. | Catalog queue |
| Position Rules | Consumes final frozen Market Handoff, not raw F-002 metric unless a governed context exposes it. | Set/Market Handoff contracts |

## 18. Dependencies

| Dependency | Class | Status |
|---|---|---|
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Required by catalog; governs Set arithmetic, exact rank/count semantics and precision. |
| Generic Set Trigger framework | DOCUMENTATION_DEPENDENCY | Active methodology defines state/event contract but not F-002 predicate. |
| Market Data Request factual volume/turnover/trade datasets | DOCUMENTATION_DEPENDENCY | Provides possible factual inputs but does not choose the formula. |
| F-004 | DOWNSTREAM UNCERTIFIED_FORMULA | Consumes F-002 after certification; not upstream for F-002. |

## 19. Worked / Conformance Examples Present

No active methodology worked example for F-002 volume confirmation was found.

Non-normative unit examples:

- median of 60 values uses the middle-pair average;
- percentile rank counts ties as less-or-equal;
- current volume 2 versus previous volumes mostly 1 can yield `relative_volume = 2` and `volume_percentile = 90.0`;
- insufficient data, missing current volume, zero median, stale and incomplete windows fail closed in the demo implementation.

These examples are useful for candidate comparison only; they are not canonical methodology authority.

## 20. Source Gaps and Ambiguities

| # | Gap | Impact |
|---:|---|---|
| 1 | Exact canonical F-002 formula is missing. | Blocks final reconstruction. |
| 2 | Volume basis is undefined: base volume, contract volume, quote turnover, point VOLUME or raw-trade aggregate. | Changes economic meaning and cross-symbol comparability. |
| 3 | Timeframe is undefined. | 1m, 5m, 15m or same-clock buckets would differ materially. |
| 4 | Reference population is undefined. | 60 previous candles versus 30 completed UTC days versus same-clock buckets differ materially. |
| 5 | Baseline statistic is undefined. | Median, mean, percentile and normalized score are different constructs. |
| 6 | Threshold values and provenance are undefined. | Blocks trigger TRUE/FALSE boundary. |
| 7 | Equality boundary is undefined. | Candidate uses inclusive thresholds; active methodology does not say. |
| 8 | Tie handling in percentile rank is undefined for F-002. | Affects boundary cases. |
| 9 | Missing/invalid data behavior conflicts with generic Set tri-state if candidate `NOT_CONFIRMED` is treated as FALSE. | May require revision to use UNAVAILABLE for evidence gaps. |
| 10 | F-002 role mode is undefined. | CURRENT_STATE versus FRESH_EVENT changes Set formation. |
| 11 | Direction relationship is undefined. | Must not infer LONG/SHORT from volume alone. |
| 12 | Whether candidate metrics feed F-004 is undefined. | Affects downstream dependency contract. |
| 13 | Candidate/demo rule registry is TESTING/non-profitability evidence, not active canonical methodology. | Blocks treating demo code as final authority. |

## 21. Reviewer Handoff Summary

```text
FORMULA_ID: F-002
FORMULA_NAME: Volume confirmation calculation

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
PARTIALLY

PARAMETER_PROVENANCE_COMPLETE:
NO

STATE_REPLAY_SEMANTICS_COMPLETE:
YES_GENERIC_TRIGGER_ONLY

SOURCE_GAP_COUNT:
13

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES_AFTER_F001_ACTIONABLE_STATUS

BLOCKING_EXTRACTION_GAPS:
- Active methodology does not define the exact F-002 volume confirmation predicate.
- Active methodology does not define volume basis, timeframe, reference population, thresholds, equality/tie behavior, or Trigger role.
- Candidate/demo code provides plausible mechanics but is explicitly not canonical authority.
- Candidate missing-data behavior may need reconciliation with Set's TRUE/FALSE/UNAVAILABLE contract.
```
