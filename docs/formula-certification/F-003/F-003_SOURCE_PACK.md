# F-003 Source Pack - Set ATR and True-Range Calculation

## 1. Formula Identity

| Field | Value | Source |
|---|---|---|
| Formula ID | F-003 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Name | Set ATR and true-range calculation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Set | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula Family | SET_ANALYTICS | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Current methodology baseline | v1.2.14 active package | `docs/trading-methodology/README.md`, package revision/status |
| Numeric policy/version IDs involved | `TT_SET_NUMERIC_V1`; Market Handoff contract version 4; Market Data Request contract version 3; strict wire schema v1.2.14 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, header; `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`, header; `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`, header; `docs/trading-methodology/schemas/wire.schema.json`, schema `$id` |

The active baseline says package revision `v1.2.14` identifies the current documentation baseline, while stable policy IDs and wire contract versions are independent version domains (`docs/trading-methodology/README.md`, package revision/status). The catalog identifies F-003 and its gate, but the formula reconstruction below uses only active `docs/trading-methodology/` material as normative source.

## 2. Canonical Source Index

| Source file | Exact section / heading | Why it is relevant | Authority type |
|---|---|---|---|
| `docs/trading-methodology/README.md` | Package revision/status | Establishes active v1.2.14 package and excludes historical snapshots from current baseline. | VERSION_PINNING |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | Header | Defines `TT_SET_NUMERIC_V1`, Set ownership of derived state, and Position consumption/no replacement indicator library. | VERSION_PINNING |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §1 Source identity, order and completeness | Governs raw decimal parsing, source identities, as-of cutoff, closed-candle ordering, continuity, incomplete/future candle exclusion, ambiguous order and missing interval behavior. | INPUT_CONTRACT |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §1.1 Fixed UTC ordinary normalization calendar | Separates ordinary percentile/normalization windows from recursive ATR ancestry and references Market Data Request membership/completeness. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §2 Working arithmetic and operation order | Defines exact rational arithmetic, formula order, 36-fractional-decimal HALF_EVEN working grid, dependency consumption, no epsilon. | NUMERIC_POLICY |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §3 Wilder ATR(14) seed and recursive state | Primary definition for series anchor, predecessor close, TR, seed, recursive Wilder update, checkpoint, replay, restart and historical revision behavior. | PRIMARY_FORMULA |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §5 Boundary values, quantization and serialization | Defines Market Handoff export rounding, positivity/availability, ATR_PCT calculation from work ATR, decimal-string serialization and Position exact consumption. | OUTPUT_CONTRACT |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §6 Implementation conformance | Names required conformance coverage areas; included only as evidence of restart/raw-history replay boundary examples, not as test requirements for this task. | REPLAY_RESTART |
| `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §7 Internal normalization interface - T05 clarification | Confirms checkpoints retain working value plus policy/source proof and export serialization does not feed internal gates. | NUMERIC_POLICY |
| `docs/trading-methodology/methodology/SET.md` | Part I §6 Market Handoff | States Set owns metric definitions/analytical semantics, numeric policy governs deterministic computation/serialization, Market Data Request governs inputs, and Position must not reconstruct Set. | OWNERSHIP_BOUNDARY |
| `docs/trading-methodology/methodology/SET.md` | Part II §6 Canonical normalization baseline | Defines ordinary 30 completed UTC calendar days, 14 completed UTC calendar day warmup, same-symbol scope, no future observations; neighboring only for ATR percentile/normalization. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | Part II §13 ATR_PCT specification | Defines canonical ATR inputs/timeframe/window/smoothing, True Range formula, ATR_14 label, and ATR_PCT formula. | PRIMARY_FORMULA |
| `docs/trading-methodology/methodology/SET.md` | Part II §14 ATR percentile specification | Defines adjacent ATR percentile consumption of current ATR_PCT and 30-day/14-day fixed UTC population; not part of F-003 certification body. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | Part II §15 Volatility hard gate | Identifies ATR percentile as Set-local gate/diagnostic and `volatility.atr_15m` / `volatility.atr_pct_15m` as Market Handoff baseline fields. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | Part III required volatility package and §10 ATR semantics | Requires `atr_15m` and `atr_pct_15m`, repeats ATR_15m/ATR_PCT_15m formulas and as-of `matched_at` availability. | OUTPUT_CONTRACT |
| `docs/trading-methodology/methodology/SET.md` | Part III §11 Optional volatility-regime context | Clarifies ATR percentile is not a baseline Market Handoff completeness requirement or Position dependency. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | Part III §22 Distance formulas and Wire/calculation projection | Shows downstream geometry may consume `ATR_15m`; maps calculation notation to wire fields and forbids alternate identity/price source/live selection. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | `volatility_scale` availability | Requires `ATR_15m` available and > 0 plus `ATR_PCT_15m` available for volatility scale. | OUTPUT_CONTRACT |
| `docs/trading-methodology/methodology/SET.md` | Set / Position Rules ownership boundary | Defines Set ownership of volatility and Position ownership of Entry/SL/TP/economics. | OWNERSHIP_BOUNDARY |
| `docs/trading-methodology/methodology/SET.md` | §39 Dynamic SL consumer contract | Identifies ATR_15m and ATR_PCT_15m as values Dynamic SL may use from immutable Market Handoff. | NEIGHBORING_DEPENDENCY |
| `docs/trading-methodology/methodology/SET.md` | Market Handoff payload and §43.1 Context production rules | Defines Market Handoff volatility fields and `set_numeric_policy_version`; Position only consumes/validates result. | OUTPUT_CONTRACT |
| `docs/trading-methodology/methodology/SET.md` | §44 Missing-data semantics | Required missing values produce persisted unavailability reason and no valid downstream handoff. | OUTPUT_CONTRACT |
| `docs/trading-methodology/methodology/SET.md` | §45 Audit requirements | Requires handoff to allow reconstruction of volatility scale and related market facts. | OUTPUT_CONTRACT |
| `docs/trading-methodology/methodology/SET.md` | Deterministic numeric and historical-source representation | Declares SET_NUMERIC_POLICY normative for Set arithmetic; binds historical selectors, checkpoint reuse, source gaps and incomplete manifests to PARTIAL/UNAVAILABLE. | REPLAY_RESTART |
| `docs/trading-methodology/methodology/SET.md` | Historical evidence eligibility | Requires exact request/selection/snapshot/page/source-completeness proof consistency and invalidates eligibility on new relevant evidence. | REPLAY_RESTART |
| `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | §§1-3 Authority/version; selection identity; time/ranges/selectors | Set chooses analytical windows/as-of/timeframes/counts; API transports factual selected ranges; KLINES use closed intervals wholly contained in [range_from, range_to). | INPUT_CONTRACT |
| `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | §§4-5 Availability, pagination, completeness and deterministic assembly | Defines AVAILABLE/PARTIAL/UNAVAILABLE, complete coverage/finality/pagination, page assembly, duplicate/changing page behavior, no future records and frozen handoff contradiction behavior. | INPUT_CONTRACT |
| `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | §7 Strict governed payload shapes | Defines KLINES fields: `open_time`, `high`, `low`, `close`, `close_time`, `is_closed`, source endpoint, coverage and provenance envelope. | INPUT_CONTRACT |
| `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | Consumer assembly consistency / V05 / W02 / X02 appendices | Defines immutable selection/snapshot/page identity, changed immutable record conflicts and no rebinding of historical evidence. | REPLAY_RESTART |
| `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Header and Canonical payloads / MARKET_HANDOFF | Defines Set -> Position Rules contract version 4, volatility fields, and `set_numeric_policy_version`. | OUTPUT_CONTRACT |
| `docs/trading-methodology/schemas/wire.schema.json` | MARKET_HANDOFF volatility schema | Requires `atr_15m` and `atr_pct_15m` as canonical Q=1e-18 ROUND_HALF_EVEN decimal strings. | OUTPUT_CONTRACT |
| `docs/trading-methodology/schemas/wire.schema.json` | Market selector and KLINES result schema | Defines selector required fields and KLINES candle payload field types/patterns. | INPUT_CONTRACT |
| `docs/trading-methodology/schemas/wire.schema.json` | Coverage schema | Defines coverage fields for completeness, pagination, expected page IDs and source finality. | INPUT_CONTRACT |
| `docs/trading-methodology/schemas/CONTRACT_REGISTRY.json` | MARKET_HANDOFF and MARKET_DATA_REQUEST entries | Pins Market Handoff v4 Set -> Position Rules and Market Data Request v3 Set -> API. | VERSION_PINNING |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P1 Topology and sequence | Confirms Set -> Position via Market Handoff and no direct Position/API dependency. | OWNERSHIP_BOUNDARY |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P16 Set numeric state and historical market selectors | Makes SET_NUMERIC_POLICY normative and requires fixed selections, exact reassembly after restart, complete selected coverage before availability. | REPLAY_RESTART |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | V05 Known historical identity before semantic rejection | Known historical market-data contradiction invalidates current assembly and blocks new analysis/handoff generation; frozen handoffs preserved. | REPLAY_RESTART |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | X02 Historical accepted ownership independent of both echo IDs | Resolves accepted request/selection/page/snapshot/native-source ownership before trusting incoming IDs; challenges preserve original facts and block new handoffs. | REPLAY_RESTART |
| `docs/trading-methodology/IDENTIFIER_LINEAGE.md` | Historical market-data and indicator checkpoint identities | Defines `selection_id`, `source_snapshot_id`/`page_id`, and indicator checkpoint identity binding. | INPUT_CONTRACT |
| `docs/trading-methodology/IDENTIFIER_LINEAGE.md` | V01-V05 / W01-W03 retained identity history | Historical page ownership and request/selection/page/snapshot/native-source relationships remain authoritative. | REPLAY_RESTART |
| `docs/trading-methodology/methodology/POSITION_RULES.md` | Canonical Set value consumption and actual hold binding | Position consumes exact canonical received ATR values and must not recompute/seed/recover extra precision. | OWNERSHIP_BOUNDARY |
| `docs/trading-methodology/methodology/POSITION_RULES.md` | Entry/SL/TP ATR references and missing ATR reasons | Identifies downstream consumers of ATR_15m and failure reason `MISSING_ATR` when ATR is missing or <= 0. | NEIGHBORING_DEPENDENCY |

## 3. Canonical Formula Reconstruction

### 3.1 True Range

F-003 True Range is defined in active Set methodology Part II §13 and SET_NUMERIC_POLICY §3.

```text
TR_t =
max(
    High_t - Low_t,
    abs(High_t - Close_(t-1)),
    abs(Low_t - Close_(t-1))
)
```

The numeric policy states the same definition as `max(high-low, abs(high-previous_close), abs(low-previous_close))` (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, §3). It also requires exact raw decimal parsing and forbids binary floating point (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, §1).

### 3.2 ATR Seed

The canonical ATR parameters are `input_timeframe = 15m`, `window = 14`, and `smoothing = Wilder` (`docs/trading-methodology/methodology/SET.md`, Part II §13). The seed rule is in SET_NUMERIC_POLICY §3:

- The canonical series anchor is the first complete native candle history for the instrument/series with factual preceding close available and authoritative history completeness proven.
- The immutable source manifest identifies `series_id`, `seed_anchor`, `predecessor_close`, `source_digest`, `first_complete_history_evidence_ref`, and ordered `seed_candle_ids`.
- The seed is the arithmetic mean of the first 14 consecutive true ranges.
- The seed is rounded once HALF_EVEN to 36 fractional decimals.
- Fewer than 14 true ranges is `UNAVAILABLE`.

The policy explicitly says not to use "an arbitrary rolling bootstrap or library default" when the anchor/history or descendant checkpoint cannot be proven (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, §3).

### 3.3 Recursive Wilder ATR

For each subsequent completed candle after the seed, active methodology defines the unchanged Wilder update (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, §3):

```text
(13 * prior_atr_work + current_TR) / 14
```

The result is rounded once to the same `10^-36` HALF_EVEN work grid. The update and processed source identity are persisted together. Out-of-order incremental facts require ordered replay, not another recursive update (`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, §3).

### 3.4 ATR_PCT

ATR_PCT is canonically defined directly from ATR in Set methodology Part II §13:

```text
ATR_PCT =
100 x ATR_14 / Close_t
```

Set Part III §10 names the baseline field as:

```text
ATR_PCT_15m =
100 x ATR_15m / Close_15m
```

For Market Handoff, SET_NUMERIC_POLICY §5 specifies `volatility.atr_pct_15m`: compute `100 * atr_work / closed_candle_close` exactly, round to work grid, then HALF_EVEN to `10^-18`; do not derive from already wire-rounded ATR.

## 4. Inputs

| Input name | Meaning | Unit | Source document | Exact source field / concept | Required / optional | Availability requirements | Temporal binding | Identity/provenance requirements |
|---|---|---|---|---|---|---|---|---|
| Instrument/series identity | The candle series to which ATR ancestry belongs | Identifier | `SET_NUMERIC_POLICY.md`, §1 and §3 | `series_id`; source facts with symbol and dataset/series identity | Required | Anchor/history completeness or descendant checkpoint must be proven, otherwise ATR `UNAVAILABLE` | Bound to persisted Set selector/as_of and canonical series anchor | Immutable source manifest with `series_id`, `source_digest`, evidence ref; source facts need authoritative identities |
| Candle high | High price for candle t | Price decimal-string | `MARKET_DATA_REQUEST.md`, §7; `wire.schema.json`, KLINES | KLINES candle `high`; TR `High_t` | Required for each TR | KLINES result must be AVAILABLE after complete coverage/finality; raw decimals exact | Closed 15m candle, ordered by interval open, ending at or before as_of | Native/canonical factual interval identity, page/snapshot/source endpoint; raw spelling preserved as provenance |
| Candle low | Low price for candle t | Price decimal-string | `MARKET_DATA_REQUEST.md`, §7; `wire.schema.json`, KLINES | KLINES candle `low`; TR `Low_t` | Required for each TR | Same as candle high | Same as candle high | Same as candle high |
| Current candle close | Close price for candle t; ATR_PCT denominator for current closed candle | Price decimal-string | `MARKET_DATA_REQUEST.md`, §7; `SET.md`, Part II §13 and Part III §10; `SET_NUMERIC_POLICY.md`, §5 | KLINES candle `close`; `Close_t`; `Close_15m`; `closed_candle_close` | Required for ATR_PCT | Must be available for closed candle; ATR_PCT must be positive and available for handoff | Closed 15m candle as-of matched/evaluation cutoff | Same factual candle identity/provenance as KLINES |
| Previous/predecessor close | Close from immediately preceding candle used in TR; factual predecessor for anchor | Price decimal-string | `SET_NUMERIC_POLICY.md`, §3; `SET.md`, Part II §13 | `previous_close`; `predecessor_close`; `Close_(t-1)` | Required for TR and anchor | Factual preceding close must be available; if anchor/history cannot be proven ATR is `UNAVAILABLE` | Predecessor of each ordered candle; anchor predecessor is recorded in manifest | Manifest includes `predecessor_close`; source identities and authoritative interval ordering required |
| Candle open_time | Authoritative interval-open time for ordering | UTC RFC3339 timestamp | `SET_NUMERIC_POLICY.md`, §1; `MARKET_DATA_REQUEST.md`, §7 | KLINES candle `open_time`; authoritative interval-open time | Required by payload schema | Sort closed candles by authoritative interval-open time; ambiguous order needed for recursion is `UNAVAILABLE` | Defines chronological order for recursive computation | Source facts require authoritative times; record identity/provenance retained |
| Candle close_time | Exclusive interval end | UTC RFC3339 timestamp | `SET_NUMERIC_POLICY.md`, §1; `MARKET_DATA_REQUEST.md`, §§3,5,7 | KLINES candle `close_time`; normalized exclusive interval end | Required by payload schema | No candle ending after as_of participates; still-forming candle invalid | Closed interval wholly contained in selected [range_from, range_to); close_time is exclusive end | Adapter documents native millisecond-end normalization |
| is_closed | Completed candle status | Boolean | `MARKET_DATA_REQUEST.md`, §3 and §7; `wire.schema.json`, KLINES | KLINES candle `is_closed`; selector `completed_only=true` | Required | Incomplete/still-forming candles do not participate | Selected KLINES must be closed/completed-only | Factual adapter payload and source finality certificate |
| Selection/as_of cutoff | Fixed economic evaluation cutoff | UTC RFC3339 timestamp | `MARKET_DATA_REQUEST.md`, §§1-3; `SET_NUMERIC_POLICY.md`, §1 | `as_of`; persisted per-dataset selector | Required | range_to <= as_of; no future records; response cannot substitute current data | Fixed before dispatch; recovered cycle reuses cutoff | `selection_id`, selection digest, request/page identity |
| Range/timeframe/count selector | Requested historical KLINES range and 15m timeframe/count | Selector fields | `MARKET_DATA_REQUEST.md`, §§2-3 and §7; `SET.md`, Part II §13 | dataset KLINES; `timeframe`; `count`; `range_from`; `range_to`; completed_only=true | Required for KLINES source history | Missing history cannot be shifted; insufficient count is incomplete, not a shorter available window | 15m candles wholly contained in selected interval | `selection_id` immutable over symbol/dataset/mode/as_of/range/timeframe/count/completed-only/page-size |
| Coverage/finality/pagination proof | Evidence that selected history is complete and final | Coverage envelope | `MARKET_DATA_REQUEST.md`, §§4-5 and §7; `wire.schema.json`, coverage | coverage_complete, pagination_complete, expected_page_ids, source_finality_confirmed, missing_ranges | Required for AVAILABLE assembly | Complete selected coverage and count checks must pass before assembled AVAILABLE | Per selection/page and source snapshot | Stable `source_snapshot_id`, `page_id`, page manifest; changed IDs/content are conflicts |
| Prior ATR work | Persisted ATR work state from previous completed candle | Price | `SET_NUMERIC_POLICY.md`, §2 and §3 | `prior_atr_work`; checkpoint exact work value | Required after seed | Restore only authentic matching checkpoint; otherwise replay from identical anchor | Previous processed ordinal/candle in canonical ordered facts | Checkpoint includes policy, seed manifest, processed source identities, last candle, digest |
| Current true range | Derived TR for current candle | Price | `SET_NUMERIC_POLICY.md`, §3 | `current_TR` | Required for seed/update | Requires high, low, previous close and valid ordering/history | Current completed candle in ordered sequence | Persisted in seed checkpoint for first 14 TRs; update persisted with source identity |
| Numeric policy | Governs arithmetic, rounding and serialization | Policy ID | `SET_NUMERIC_POLICY.md`, header and §5; `MARKET_HANDOFF.md`, payload | `TT_SET_NUMERIC_V1`; `set_numeric_policy_version` | Required | Market Handoff v4 declares it; Position consumes exact canonical handoff | Bound to computation/checkpoint/handoff | Checkpoint includes policy; wire carries policy version |

## 5. Outputs

| Name | Meaning | Unit | Internal or wire value | Precision | Rounding | Availability constraints | Downstream consumer |
|---|---|---|---|---|---|---|---|
| True Range (`TR_t`) | Per-candle maximum of high-low and predecessor-close distances | Price | Internal source-derived value | Exact until seed/checkpoint use | No standalone TR output rounding specified except seed checkpoint stores true ranges under ATR state; seed mean rounded to work grid | Requires high, low, previous close and ordered completed candle | ATR seed and recursive update |
| ATR seed work value | Mean of first 14 consecutive TRs from canonical anchor | Price | Internal work state | `10^-36` fractional grid | ROUND_HALF_EVEN once after mean | Fewer than 14 TRs or unproven anchor/history => ATR `UNAVAILABLE` | Recursive ATR state |
| ATR work state (`prior_atr_work`, current work ATR) | Persisted recursive Wilder ATR state | Price | Internal work/checkpoint value | `10^-36` fractional grid | ROUND_HALF_EVEN once per recursive update | Requires authentic matching checkpoint or full replay from identical anchor | Set gates/internal metrics; export to Market Handoff |
| ATR checkpoint | Durable state for replay/restart | State envelope | Internal | Exact work value plus source/policy digests | Canonical content digest; object serialization sorted-key compact UTF-8 JSON where applicable | Restore only authentic matching checkpoint | Set replay/restart |
| `volatility.atr_15m` | Market Handoff ATR | Price decimal-string | Wire | 18 fractional decimal export class with no trailing zeros | Round persisted ATR work state once HALF_EVEN to `10^-18` | Must be positive and available | Position Rules Entry/SL/TP geometry; Dynamic SL/TP; audit |
| ATR_PCT work value | `100 * atr_work / closed_candle_close` at work grid | Percent | Internal named continuous Set metric output | `10^-36` fractional grid | Exact quotient, round to work grid HALF_EVEN | Requires ATR work and closed candle close; positivity required for handoff | Set-local ATR percentile/VNM neighbors; export to handoff |
| `volatility.atr_pct_15m` | Market Handoff ATR percentage | Percent decimal-string | Wire | 18 fractional decimal export class with no trailing zeros | Compute from work ATR and closed close, round to work grid, then HALF_EVEN to `10^-18`; not from wire-rounded ATR | Must be positive and available | Position Rules exact received value; handoff audit; optional downstream formulas that consume handoff |

SET_NUMERIC_POLICY §5 states Position uses exactly received wire values and display rounding must not feed any gate. SET.md §44 states a required unavailable value causes Set to persist the unavailability reason and emit no valid downstream handoff.

## 6. Domain and Preconditions

| Requirement area | Canonical requirement | Source |
|---|---|---|
| Instrument/series | Source facts must have symbol and dataset/series identity; ATR anchor is instrument/series-specific. | `SET_NUMERIC_POLICY.md`, §1 and §3 |
| Timeframe | Canonical ATR input timeframe is 15m. | `SET.md`, Part II §13 |
| Window | Canonical ATR window is 14. | `SET.md`, Part II §13; `SET_NUMERIC_POLICY.md`, §3 |
| Smoothing | Wilder. | `SET.md`, Part II §13; `SET_NUMERIC_POLICY.md`, §3 |
| Completed candles | KLINES use `completed_only=true`; no incomplete/still-forming candle participates. | `MARKET_DATA_REQUEST.md`, §3; `SET_NUMERIC_POLICY.md`, §1 |
| Predecessor close | Factual preceding close must be available for the anchor; TR uses previous close. | `SET_NUMERIC_POLICY.md`, §3; `SET.md`, Part II §13 |
| History completeness | First complete native candle history and authoritative completeness must be proven; complete selected coverage/count checks are required for AVAILABLE. | `SET_NUMERIC_POLICY.md`, §3; `MARKET_DATA_REQUEST.md`, §5 |
| Minimum observations | First 14 consecutive true ranges for seed; fewer than 14 TRs is `UNAVAILABLE`. | `SET_NUMERIC_POLICY.md`, §3 |
| Ordered continuity | Closed candles sorted by authoritative interval-open time; verify non-overlap and continuity; missing interval is `UNAVAILABLE` until resolved. | `SET_NUMERIC_POLICY.md`, §1 |
| As-of cutoff | Set fixes one as_of cutoff; no candle ending after as_of participates; range_to <= as_of. | `SET_NUMERIC_POLICY.md`, §1; `MARKET_DATA_REQUEST.md`, §3 |
| Valid price domain | KLINES decimal fields match nonnegative decimal-string schema patterns; exact raw decimals required. High/low ordering and strict positive close are NOT EXPLICITLY SPECIFIED except handoff ATR/ATR_PCT positivity. | `wire.schema.json`, KLINES schema; `SET_NUMERIC_POLICY.md`, §1 and §5 |
| ATR positivity | `volatility.atr_15m` must be positive and available at Market Handoff. | `SET_NUMERIC_POLICY.md`, §5 |
| ATR_PCT positivity | `volatility.atr_pct_15m` must be positive and available at Market Handoff. | `SET_NUMERIC_POLICY.md`, §5 |
| Availability at match | ATR_15m and ATR_PCT_15m must be fully available as-of `matched_at`. | `SET.md`, Part III §10 |

## 7. Missing / Unavailable / Invalid Behavior

| Case | Behavior classification | Canonical behavior | Source |
|---|---|---|---|
| Fewer than 14 TRs | Explicitly defined | ATR is `UNAVAILABLE`. | `SET_NUMERIC_POLICY.md`, §3 |
| Missing predecessor close | Explicitly defined | If factual preceding close for anchor is unavailable/proof missing, ATR is `UNAVAILABLE`; do not switch bootstrap/default. | `SET_NUMERIC_POLICY.md`, §3 |
| Missing candle interval | Explicitly defined | Missing source interval is `UNAVAILABLE` until resolved; missing ranges cannot be replaced by current snapshot or shifted baseline. | `SET_NUMERIC_POLICY.md`, §1; `SET.md`, deterministic numeric/historical-source representation |
| Incomplete candle | Explicitly defined | No incomplete/still-forming candle participates; still-forming candle invalid in boundary behavior. | `SET_NUMERIC_POLICY.md`, §1; `MARKET_DATA_REQUEST.md`, §5 |
| Future candle / after as_of | Explicitly defined | No candle ending after as_of participates; any record after as_of is invalid. | `SET_NUMERIC_POLICY.md`, §1; `MARKET_DATA_REQUEST.md`, §5 |
| Ambiguous order | Explicitly defined | Any ambiguous order needed for recursive computation is `UNAVAILABLE` until resolved. | `SET_NUMERIC_POLICY.md`, §1 |
| Invalid checkpoint | Explicitly defined | Restore only authentic matching checkpoint; if checkpoint descending from proven anchor cannot be proven, ATR is `UNAVAILABLE`. | `SET_NUMERIC_POLICY.md`, §3 |
| Conflicting source identity / duplicate source identity | Explicitly defined | Equal source identities are de-duplicated only if equal; conflicting equal IDs are integrity conditions. | `SET_NUMERIC_POLICY.md`, §1 |
| Changed same-ID source content | Explicitly defined | Changed same-ID source content is an integrity condition; changed immutable record/page content invalidates assembled eligibility and blocks new handoffs. | `SET_NUMERIC_POLICY.md`, §3; `MARKET_DATA_REQUEST.md`, §5 and Consumer assembly consistency |
| Revised historical data | Explicitly defined | Revised historical source invalidates affected derived state; do not splice inconsistent history into frozen handoff. | `SET_NUMERIC_POLICY.md`, §3 |
| Unavailable close | Explicitly defined for selected data, implicit for formula | Missing selected data remains unavailable to affected Set computation; ATR_PCT mathematically cannot be produced without closed candle close. | `MARKET_DATA_REQUEST.md`, §4; `SET_NUMERIC_POLICY.md`, §5 |
| Zero/non-positive ATR_PCT denominator | Not defined by methodology | Active docs require handoff ATR_PCT positive/available but do not explicitly state denominator-zero behavior. | Source gap; `SET_NUMERIC_POLICY.md`, §5 |
| Unavailable ATR | Explicitly defined | Required unavailable value means Set persists reason and emits no valid downstream handoff; Position reason is `MISSING_ATR` if ATR_15m missing or <= 0. | `SET.md`, §44; `POSITION_RULES.md`, Entry/SL/TP missing ATR reasons |
| Unavailable ATR_PCT | Explicitly defined for handoff | Volatility must be populated before emission; unavailable required value means no valid downstream handoff. | `SET.md`, §44; `SET_NUMERIC_POLICY.md`, §5 |
| Out-of-order incremental source | Explicitly defined | Requires ordered replay, not another recursive update. | `SET_NUMERIC_POLICY.md`, §3 |
| Same candle replay | Explicitly defined | Replay of same candle is idempotent. | `SET_NUMERIC_POLICY.md`, §3 |
| Conflicting historical ownership/echo IDs | Explicitly defined | Resolve accepted request/selection/page/snapshot/native-source relationships first; challenge preserves facts, invalidates assembly, blocks new analysis/handoff. | `SYSTEM_PROTOCOLS.md`, X02 |

## 8. Precision, Rounding, and Numeric Policy

`TT_SET_NUMERIC_V1` is the governing Set numeric policy (`SET_NUMERIC_POLICY.md`, header). It requires raw decimals to be parsed exactly as signed integer/scale values and forbids binary floating point, context-dependent parsing, NaN and infinity (`SET_NUMERIC_POLICY.md`, §1).

Inputs, sums, differences, products and rational quotients are exact integer/rational expressions in written formula order. At each named continuous Set metric output, recursive state update and normalization output, round once to `10^-36` with ROUND_HALF_EVEN (`SET_NUMERIC_POLICY.md`, §2). The policy states 36 is a fractional scale, not significant digits, and large values retain all integer digits.

Intermediate precision is exact until the named output/update quantizer. Dependent formulas consume persisted working values of named dependencies, not hidden library precision (`SET_NUMERIC_POLICY.md`, §2). For ATR, the seed mean and each recursive update are rounded once to the work grid (`SET_NUMERIC_POLICY.md`, §3).

Market Handoff export uses `10^-18` HALF_EVEN for `volatility.atr_15m`; `volatility.atr_pct_15m` is computed from work ATR and closed-candle close, rounded to work grid, then exported at `10^-18` (`SET_NUMERIC_POLICY.md`, §5). Wire schema descriptions call these canonical Q=1e-18 ROUND_HALF_EVEN values and say exact received value governs Position comparisons (`wire.schema.json`, MARKET_HANDOFF volatility schema).

Serialization uses plain canonical decimal strings: no exponent, plus sign, negative zero, redundant leading integer zero or trailing fractional zeros. Object serialization uses sorted-key compact UTF-8 JSON (`SET_NUMERIC_POLICY.md`, §5). Position uses exactly received wire values, compares ratios by exact rational cross multiplication and must not use display rounding at a gate (`SET_NUMERIC_POLICY.md`, §5; `POSITION_RULES.md`, Canonical Set value consumption).

## 9. Time and Candle Basis

F-003 ATR is 15m, window 14, Wilder (`SET.md`, Part II §13). KLINES select closed intervals wholly contained in `[range_from, range_to)`, with exact timeframe and `completed_only=true`; normalized candle `close_time` is the exclusive interval end (`MARKET_DATA_REQUEST.md`, §3). SET_NUMERIC_POLICY §1 requires sorting closed candles by authoritative interval-open time and verifying non-overlap and continuity.

UTC implications differ by domain. Ordinary normalization/percentile windows use the fixed UTC analytical calendar: one completed UTC day is `[00:00:00Z, next 00:00:00Z)`, and the 30-day lookback is `[D - 30 UTC calendar days, D)` excluding the current incomplete UTC day (`SET_NUMERIC_POLICY.md`, §1.1; `SET.md`, Part II §6). This applies to ATR percentile and normalization neighbors, not to ATR recursive ancestry. SET_NUMERIC_POLICY §3 explicitly says recursive seed ancestry and analytical population windows are distinct.

`as_of` is the fixed economic evaluation cutoff, not request/receipt time (`MARKET_DATA_REQUEST.md`, §3). Set fixes and persists analytical as_of and dataset selectors before dispatch; recovered cycles reuse selection identity/cutoff/checkpoint (`SET.md`, deterministic numeric/historical-source representation).

## 10. State, Checkpoint, Replay, and Restart Semantics

The seed manifest must identify `series_id`, `seed_anchor`, `predecessor_close`, `source_digest`, `first_complete_history_evidence_ref`, and ordered `seed_candle_ids` (`SET_NUMERIC_POLICY.md`, §3). The seed checkpoint includes all 14 ordered source candle IDs/true ranges and the last processed candle, not merely scalar ATR.

A checkpoint includes policy, seed manifest, processed ordinal/source identities, last candle and exact work value, with canonical content digest (`SET_NUMERIC_POLICY.md`, §3). SET_NUMERIC_POLICY §7 adds that checkpoints retain working value plus policy/source proof.

Replay and restart requirements:

- Persist update and processed source identity together (`SET_NUMERIC_POLICY.md`, §3).
- Out-of-order incremental facts require ordered replay (`SET_NUMERIC_POLICY.md`, §3).
- Replay of same candle is idempotent; changed same-ID source content is integrity condition (`SET_NUMERIC_POLICY.md`, §3).
- Restore only authentic matching checkpoint and replay subsequent canonical ordered facts (`SET_NUMERIC_POLICY.md`, §3).
- Full replay from identical anchor must match checkpoint continuation byte for byte (`SET_NUMERIC_POLICY.md`, §3).
- A revised historical source invalidates affected derived state; inconsistent history must not be spliced into frozen handoff (`SET_NUMERIC_POLICY.md`, §3).
- Set reassembles exact immutable selection after restart and requires complete selected coverage before affected data become AVAILABLE (`SYSTEM_PROTOCOLS.md`, P16).
- Historical evidence challenges invalidate current assembly and block new analysis/handoff generation, while already frozen handoffs remain immutable (`SYSTEM_PROTOCOLS.md`, V05 and X02).

Identifier lineage binds `selection_id` to fixed symbol/dataset/window/cutoff across page requests and restart; `source_snapshot_id`/`page_id` bind one governed source selection snapshot; `indicator checkpoint_id` binds `TT_SET_NUMERIC_V1` state and source-manifest digest (`IDENTIFIER_LINEAGE.md`, historical market-data and indicator checkpoint identities).

## 11. Configuration and Version Dependencies

| Dependency | Canonical value / behavior | Source |
|---|---|---|
| Methodology package | v1.2.14 active specification baseline | `README.md`, package revision/status |
| Set numeric policy | `TT_SET_NUMERIC_V1` | `SET_NUMERIC_POLICY.md`, header |
| ATR timeframe | 15m | `SET.md`, Part II §13 |
| ATR window | 14 | `SET.md`, Part II §13; `SET_NUMERIC_POLICY.md`, §3 |
| ATR smoothing | Wilder | `SET.md`, Part II §13 |
| Market Handoff contract | Version 4, Set -> Position Rules | `MARKET_HANDOFF.md`, header; `CONTRACT_REGISTRY.json` |
| Market Data Request contract | Version 3, Set -> API | `MARKET_DATA_REQUEST.md`, header; `CONTRACT_REGISTRY.json` |
| Wire schema | Strict v1.2.14 schema | `wire.schema.json`, `$id` and title |
| Work precision | `10^-36` fractional grid | `SET_NUMERIC_POLICY.md`, §2 |
| Export precision | `10^-18` for handoff ATR/ATR_PCT | `SET_NUMERIC_POLICY.md`, §5 |
| Ordinary percentile/normalization lookback | 30 completed UTC calendar days, minimum warmup 14 completed UTC calendar days | `SET.md`, Part II §6; `SET_NUMERIC_POLICY.md`, §1.1 |

The active docs treat timeframe/window/smoothing as canonical values, not research/config parameters. SET_NUMERIC_POLICY header says the policy is a technical computation/serialization contract and does not add a signal, indicator or fallback. No active source says ATR timeframe/window/smoothing are configurable.

## 12. Ownership and Contract Boundaries

Set owns derived state and volatility; Market Handoff carries the Set-produced frozen market-analysis payload to Position (`SET_NUMERIC_POLICY.md`, header; `SET.md`, Part I §6 and Set/Position ownership boundary). API is a factual transport/normalization interface and does not choose a market regime, trigger, history window, reference or fallback (`MARKET_DATA_REQUEST.md`, §1).

Market Handoff version 4 includes:

- `volatility.atr_15m`
- `volatility.atr_pct_15m`
- `set_numeric_policy_version: TT_SET_NUMERIC_V1`

These are defined in `MARKET_HANDOFF.md`, Canonical payloads / MARKET_HANDOFF, and required by `wire.schema.json`, MARKET_HANDOFF volatility schema.

Position consumes/validates the result and must not call back into Set to reconstruct or reinterpret the match (`SET.md`, Part I §6). Position Rules says Market Handoff v4 requires `TT_SET_NUMERIC_V1`; Position parses and compares exact canonical received `volatility.atr_15m` and `atr_pct_15m`; it must not recompute/seed ATR independently, recover extra precision from another source, or use display rounding at a gate (`POSITION_RULES.md`, Canonical Set value consumption and actual hold binding). SYSTEM_PROTOCOLS P1 states Position Rules has no direct API dependency.

## 13. Downstream Dependencies

| Dependent object | Dependency description | Source |
|---|---|---|
| F-001 Price-move trigger calculation | Catalog lists F-001 depending on F-003 and N-008. No certification review is included here. | `docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue |
| F-004 Set normalization, percentile, and score calculation | Catalog lists F-004 depending on F-003; Set Part II §14 consumes ATR_PCT for ATR percentile. | `docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue; `SET.md`, Part II §14 |
| F-005 Set direction classifier | Catalog lists F-005 depending on F-004; ATR influence is indirect through F-004/volatility gates where applicable. | `docs/FORMULA_METRICS_CATALOG.md`, Formula Certification Queue |
| F-006/F-007 Position Rules LONG/SHORT formulas | Position formulas consume `ATR_15m` for entry-depth, stop geometry, risk and reachability checks. | `POSITION_RULES.md`, ATR references and missing ATR reasons |
| F-009 Stop calculation | Stop buffer/min-distance/risk calculations use `ATR_15m`. | `POSITION_RULES.md`, Dynamic SL ATR formulas |
| F-010 Dynamic Take Profit | Target reachability distance uses `ATR_15m`. | `POSITION_RULES.md`, Dynamic TP ATR formulas |
| F-012 Risk/reward and minimum net edge | Position geometry and risk formulas use ATR-normalized distances as upstream quantities; this source pack does not review F-012. | `POSITION_RULES.md`, ATR-normalized risk references |

## 14. Neighboring Normative Rules

- ATR percentile consumes current `ATR_PCT(15m,14,Wilder)` and ranks it against completed same-symbol 15m ATR_PCT observations in the 30 completed UTC calendar days selected by Set Part II §6 (`SET.md`, Part II §14). ATR percentile is adjacent, not part of F-003 reconstruction.
- Volatility hard gate uses ATR percentile, while Market Handoff carries only baseline ATR and ATR_PCT fields; ATR percentile is not a required baseline Market Handoff field or Position Rules dependency (`SET.md`, Part II §15).
- Ordinary z-scores and percentile baselines use 30 completed UTC calendar days and 14 completed UTC calendar days minimum warmup; recursive ATR seed ancestry is distinct and not replaced by that lookback (`SET_NUMERIC_POLICY.md`, §3).
- Dynamic SL may use `references.levels[]`, `ATR_15m`, `ATR_PCT_15m` and optional approved context from immutable Market Handoff (`SET.md`, §39).
- Position must not recompute/seed ATR or recover extra precision (`POSITION_RULES.md`, Canonical Set value consumption).

## 15. Boundary Examples Present in Methodology

SET_NUMERIC_POLICY §5 contains the only worked example found that is directly relevant to F-003:

- Seed fourteen TR values of 1, then TR=2 gives work ATR `1.071428571428571428571428571428571429`.
- Handoff ATR is `1.071428571428571429`.
- At close=100, canonical ATR percentage is the same number.
- Existing improvement minimum 0.10 ATR is met exactly by `0.1071428571428571429`; below fails and above passes.

Additional boundary examples in SET_NUMERIC_POLICY §1 and §5 cover neighboring `age_seconds` and export/comparison behavior, but they are not F-003 formula examples.

## 16. Source Gaps or Ambiguities

| Category | Gap / ambiguity | Source basis |
|---|---|---|
| MISSING_DEFINITION | Active docs do not explicitly define OHLC domain invariants such as `high >= low`, `high >= close`, or `low <= close`; schema only permits nonnegative decimal strings. | `wire.schema.json`, KLINES schema |
| MISSING_DEFINITION | Active docs do not explicitly define behavior for zero closed-candle close in ATR_PCT denominator; handoff ATR_PCT must be positive/available, but denominator-zero handling is not stated. | `SET_NUMERIC_POLICY.md`, §5 |
| MISSING_DEFINITION | Active docs do not explicitly state whether TR itself is persisted beyond seed checkpoint true ranges and recursive update evidence. | `SET_NUMERIC_POLICY.md`, §3 |
| MISSING_DEFINITION | Active docs do not give an explicit canonical candle ID field in the KLINES payload; they refer to source identities and canonical factual interval identity. | `MARKET_DATA_REQUEST.md`, §5; `SET_NUMERIC_POLICY.md`, §1 |
| CROSS_DOCUMENT_DEPENDENCY | F-003 input provenance is split between SET_NUMERIC_POLICY, Market Data Request, wire schema and Identifier Lineage; no single source enumerates all candle identity fields for ATR. | Source index entries for those files |
| AMBIGUOUS_WORDING | `first complete native candle history` and `authoritative history completeness is proven` are normative but do not prescribe a single proof artifact shape beyond manifest/evidence refs and Market Data coverage. | `SET_NUMERIC_POLICY.md`, §3; `MARKET_DATA_REQUEST.md`, §§4-5 |
| MISSING_DEFINITION | Active docs do not explicitly define recovery after a historical revision invalidates ATR state beyond invalidation/reconciliation/blocking; they do not specify an acceptance policy for corrected replacement history. | `SET_NUMERIC_POLICY.md`, §3; `SYSTEM_PROTOCOLS.md`, V05/X02 |
| MISSING_DEFINITION | Active docs do not explicitly define whether a zero ATR work value can exist internally; they require positive and available only when crossing Market Handoff and Position treats missing or <=0 as `MISSING_ATR`. | `SET_NUMERIC_POLICY.md`, §5; `POSITION_RULES.md`, missing ATR reasons |
| AMBIGUOUS_WORDING | `ATR_14` in SET Part II §13 is a label without seed/update details in that section; reconstruction requires SET_NUMERIC_POLICY §3. | `SET.md`, Part II §13; `SET_NUMERIC_POLICY.md`, §3 |
| MISSING_DEFINITION | Active docs do not explicitly specify the exact `calculated_at` timestamp semantics for ATR/ATR_PCT fields in the Set required package. | `SET.md`, Part III required volatility package |
| IMPLICIT_DOMAIN_ASSUMPTION | ATR_PCT formula uses percent units via factor 100, but docs do not separately state whether `ATR_PCT` display includes a percent sign; wire is decimal-string. | `SET.md`, Part II §13; `SET_NUMERIC_POLICY.md`, §5 |
| CROSS_DOCUMENT_DEPENDENCY | Positivity/availability for volatility scale is in Set Part III, while export positivity is in numeric policy and Position missing behavior is in Position Rules. | `SET.md`, volatility_scale; `SET_NUMERIC_POLICY.md`, §5; `POSITION_RULES.md`, missing ATR reasons |
| MISSING_DEFINITION | Active docs do not provide full worked OHLC-to-TR-to-seed example with real candle high/low/close/predecessor-close inputs; only synthetic TR values are shown. | `SET_NUMERIC_POLICY.md`, §5 |

## 17. Reviewer Handoff Summary

Formula set: F-003 comprises True Range, Wilder ATR(14) seed, recursive Wilder ATR work state, and ATR_PCT as directly derived from work ATR and closed candle close. True Range is `max(high-low, abs(high-previous_close), abs(low-previous_close))`; seed is arithmetic mean of first 14 consecutive TRs; recursive update is `(13 * prior_atr_work + current_TR) / 14`; ATR_PCT is `100 * ATR / Close`.

Input set: 15m completed KLINES high, low, close, predecessor close, open_time, close_time/is_closed, instrument/series identity, Set selection/as_of/range/timeframe/count, source coverage/finality/pagination proof, prior ATR checkpoint/work state after seed, and `TT_SET_NUMERIC_V1` policy identity.

Output set: internal TR values, seed ATR work state, recursive ATR work state/checkpoint, wire `volatility.atr_15m`, internal ATR_PCT work value, and wire `volatility.atr_pct_15m`.

Precision/rounding: exact decimal/rational arithmetic, no binary floating point, work grid `10^-36` ROUND_HALF_EVEN at seed and each recursive update/named output, Market Handoff export `10^-18` ROUND_HALF_EVEN. ATR_PCT handoff is computed from work ATR and closed close, not wire-rounded ATR. Decimal strings have no exponent, plus sign, negative zero, redundant leading integer zero or trailing fractional zeros.

Missing-data behavior: unproven anchor/history/checkpoint, fewer than 14 TRs, missing predecessor close, missing interval, incomplete/future candle, ambiguous recursive order or incomplete page manifest make affected computation unavailable or reconciling as specified. Required unavailable volatility means no valid downstream Market Handoff. Changed same-ID source/page/record content is an integrity condition.

State/replay requirements: seed manifest, checkpoint policy, source manifest, processed ordinal/source identities, last candle, exact work value and digest are required. Same-candle replay is idempotent. Out-of-order facts require ordered replay. Full replay from identical anchor must match checkpoint continuation byte-for-byte. Historical revision invalidates affected derived state and must not be spliced into frozen handoff.

Relevant dependencies: F-004 consumes ATR_PCT for ATR percentile/normalization neighbors; F-005 may be indirectly affected through Set score/direction; Position F-006/F-007/F-009/F-010/F-012 consume Market Handoff ATR values for geometry/gates. Position must not recompute or reseed ATR.

Unresolved source gaps: the active docs leave explicit gaps around OHLC domain invariants, zero denominator handling for ATR_PCT, exact candle identity field shape, recovery policy after historical correction, internal zero ATR behavior, `calculated_at` semantics, and absence of a full OHLC worked example.
