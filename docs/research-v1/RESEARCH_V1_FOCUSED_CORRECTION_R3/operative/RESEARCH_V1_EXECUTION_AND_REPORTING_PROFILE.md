# TriggerTrade — Research V1 Execution and Reporting Profile

**Revision: RESEARCH_V1_FOCUSED_CORRECTION_R3. Status: APPROVED — specification only, not execution or native-runtime certification.**

This is the mechanical R3 continuation of `RESEARCH_V1_FOCUSED_CORRECTION_R2`, not a new research program. The frozen v1.2.15 archive is unchanged (SHA-256 `3b38c09c6f52daa77d7cc4257a3c420b21d76ac10d039dd708dd205af963b326`). Research authority is the supplied Research V1 product decisions, the focused council `RV1-FOCUSED-BTC-INTRABAR-01`, and the current Focused Research V1 Package Correction instruction. References to RV1-DECISIONS below retain their original user-prompt section numbers. The current correction applies only the approved R-022/C-012 and R-026/C-015 replacements. The four R2 corrections remain closed.

The current document/package revision is R3. Existing immutable `REPORT-R-V1-R2`, `EVIDENCE-R-V1-R2`, `ALLOC-R-V1-FIXED-10X10`, execution `profile_revision=RESEARCH_V1_FOCUSED_CORRECTION_R2` and DEC-R-001/R2 semantic bindings remain supported unchanged. They identify calculation/execution/evidence semantics, never the hypothesis revision. All current research records resolve R3 explicitly; prior runs retain their actual identities. The four run types and eleven report-statistic IDs, formulas and populations are unchanged.

## 1. Authority, ownership, and what approval means

`EXISTING CANONICAL METRICS → RESEARCH TRIGGERS → SET VERSION → POSITION + PORTFOLIO CONFIGURATIONS → HYPOTHESIS / ARM → MANUALLY REQUESTED RUN → REPORT → HUMAN DECISION` remains the construction hierarchy.

The execution order remains Set match → Position APPROVE/REJECT → Portfolio Capital and Limits → immutable Position Order Spec → Portfolio Submit Authorized → Lifecycle submission/management → canonical final result and CLOSED. Position never queries the exchange, Portfolio still owns grants/holds and limits, and Set owns pending invalidation. No research statistic enters that chain. A reporting pipeline can read source evidence; it cannot call a trading gate or write a canonical financial result.

**WEB_RESEARCH_EXECUTABILITY=YES means the hypothesis is a mechanically resolvable specification with named, typed launch inputs and deterministic run/report semantics.** It does not mean a run has been launched, the data exist, an account is connected, or an exchange adapter/UI has been verified. An absent factual launch input makes that particular run `UNAVAILABLE` with reasons; it is not an undefined hypothesis. No placeholder is transmitted as a configuration value.

Source: RV1-DECISIONS §§1–3, 6–10, 16–20; `methodology/ORDER_LIFECYCLE.md` §§1–3, L63–245; `SYSTEM_PROTOCOLS.md` P6–P8, L114–220; `schemas/NUMERIC_POLICY.md` §§1–7, L8–94.

## 2. Immutable universe, fixed allocation, and symbol-specific direction

### 2.1 UNIVERSE-CORE-V1 / ALLOC-R-V1-FIXED-10X10

| Ordinal | Symbol | Segment | Allocation | Trading role |
|---:|---|---|---:|---|
| 1 | BTC | MAJORS | 10% | MAJOR trading subject; generic BTC direction except R-006 |
| 2 | ETH | MAJORS | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 3 | SOL | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 4 | XRP | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 5 | DOGE | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 6 | SUI | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 7 | PEPE | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 8 | AVAX | HIGH_VOLATILITY_HIGH_BETA | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 9 | LINK | DIVERSIFIERS | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |
| 10 | BNB | DIVERSIFIERS | 10% | Trading subject; unchanged F-005 ALTCOIN_VS_BTC |

Exact segment totals: MAJORS 20%; HIGH_VOLATILITY_HIGH_BETA 60%; DIVERSIFIERS 20%. Exact full allocation is 100%. These labels/liquidity assumptions are product bindings, not measured beta, liquidity, correlation or volatility metrics. Coin remains an evaluation dimension, not a separate hypothesis. No dynamic weights, per-run overrides, renormalization, redistribution, or allocation optimization is authorized.

Every launch-enabled Portfolio configuration uses exactly this vector. IDs `PR-R-201`…`PR-R-209` are new immutable successors of `PR-R-101`…`PR-R-109`; old bodies are historical only. `PR-R-203` is an unused provenance alias whose corrected canonical fields equal the baseline; it is **not** a new allocation experiment or an admissible R-023 variant. Global cap and minimum tranche retain their independent frozen meanings as OPERATIVE CONTROLS, not current first-wave interventions. Current Portfolio interventions are R-024 slots, R-025 per-coin slots/grant division, R-027 cooldown and R-028 Daily Loss. Fixed 100% target allocation does not force 100% concurrent investment.

BTC uses `DB-R-BTC-001`: an explicitly non-F-005 generic deterministic Set. At each completed 5m evaluation, Set maps existing `RETURN(asset=BTC,5m)>0` to its LONG branch and `<0` to SHORT. Valid zero qualifies neither; UNAVAILABLE is never zero/FALSE and produces no direction-qualified match. Common predicates in both BTC arms are `DE>=0.30`, `ATR percentile>=15`, `ATR percentile<=97`, and `TOD_REL_TURNOVER>=0.70`. They are actual research predicates, not fabricated classifier gates. The four floor predicates apply at direction-qualified formation endpoints/final match; they are not a new maintained-condition intervention.

The unchanged eight BTC Trigger references and sixteen BTC Set versions (fourteen carried from R2 plus SET-R-BTC-012-V2 and SET-R-BTC-015-V2) are defined in `WEB_RESEARCH_CONFIGURATION_MODEL.md` §§4–5. Every arm resolves an explicit symbol→Set-version map. Non-BTC F-005 trigger/Set bodies and prerequisites are unchanged. Shared scalar predicates retain their canonical formula, comparison and freshness. Only their **enclosing-Set direction prerequisite** is instantiated as generic BTC instead of F-005; the immutable BTC instance records make this explicit. No BTC classifier object, F-004 aggregate score, self-relative normalization, or `direction_classifier.gates.*` evidence is produced.

R-008 uses a same-epoch FALSE→TRUE BTC return-side event; initial TRUE and UNAVAILABLE→TRUE do not qualify. R-010 preserves endpoint-only versus sampled maintained return-side qualification; no baseline direction-change reset is added. The original questions retain their non-BTC wording; BTC instantiation is disclosed rather than mislabeled as F-005 behavior.

**R-006 only:** BTC is `NOT_APPLICABLE`, reason `SOURCE_LOGIC_NOT_MEANINGFUL_FOR_BTC`. BTC-vs-BTC relative return gives no informative treatment. Keep BTC in the universe with its full 10% allocation; do not redistribute it. Show no zero-performance BTC value. R-006 MAJORS treatment reports may contain ETH only and must disclose this. All other 29 current questions support BTC with the approved binding; no extra hypothesis IDs are created.

R3 R-022/C-012 adds inclusive BTC_CONTEXT_SCORE>=0 for LONG / <=0 for SHORT, using SET-R-BTC-012-V2 only for BTC and SET-R-012-V2 for non-BTC. R3 R-026/C-015 adds inclusive VNM_5m_z>=0 / <=0, using SET-R-BTC-015-V2 for BTC and SET-R-015-V2 for non-BTC. Both keep POS-R-001 and PR-R-201. Valid zero passes the side-specific compatibility test; UNAVAILABLE does not. Direction always remains DB-R-BTC-001 on BTC. The canonical BTC-local5m ATR/VNM/normalization closure is `WEB_RESEARCH_CONFIGURATION_MODEL.md` §5.R3.D. C-012 BTC nesting with R-005 and C-015 zero-mean nonbinding interpretation are mandatory; no forced activation.

Source: frozen `methodology/SET.md` Part I §5 L509–530; Part I §§10–12 L1132–1260; Part II §§3–6 L1739–1961, §16.2 L2561–2587, §§11–15 L2317–2508, §8 L2013–2131 and §23 L2823–2858; `methodology/PORTFOLIO_RULES.md` Part I §§5–8 L251–358; focused council §§2.3–2.6, §7; current correction §§2–7, 13.

### 2.2 Instrument binding and units

A launch manifest binds each asset label to **one** evidence-backed instrument identity, native symbol, exchange environment, instrument type, settlement/accounting currency, native base/quantity unit, price tick, quantity step and effective metadata history. The frozen execution context is USDT linear perpetual, hedge mode, isolated margin. Exact API ticker spellings and account IDs are launch facts, not invented here. The BTC benchmark mapping is pinned as well.

Asset labels are reporting aliases, not price-unit conversion instructions. In particular, a native contract whose denomination contains a multiplier must use its native price/quantity units consistently throughout the canonical formulas and instrument metadata. Do not divide a quote by an assumed factor or mix differently denominated price/volume series. A mapping the frozen arithmetic cannot represent is `UNAVAILABLE`, not silently repaired. Native symbol mappings and their digests must match across comparable arms. Never drop an unavailable asset and recalculate weights over the survivors.

Source: RV1-DECISIONS §§3, 11–12; `methodology/ORDER_LIFECYCLE.md` §§4A–5, L362–407; `methodology/POSITION_RULES.md` Part I §§17–22A, L576–908; `api-contracts/MARKET_DATA_REQUEST.md`; `SYSTEM_PROTOCOLS.md` P7.1.

## 3. Run profiles, intervals, and manual launch

| Run type / profile ID | Interval | User action |
|---|---|---|
| BACKTEST_90D | `[endpoint − 90 × 86400 seconds, endpoint)` | User requests this window for a selected hypothesis arm |
| BACKTEST_30D | `[endpoint − 30 × 86400 seconds, endpoint)` | Independent manual request |
| BACKTEST_7D | `[endpoint − 7 × 86400 seconds, endpoint)` | Independent manual request |
| DEMO_7D | `[selected_start, selected_start + 7 × 86400 seconds)` | User selects and starts Demo in the Demo environment |

Backtest endpoints are timezone-aware, completed canonical 5-minute boundaries; reject an unaligned endpoint rather than silently rounding it. Store the UTC instants, user display timezone, and original selection. Durations are elapsed 24-hour days, not Israel civil-day counts. **Accounting day remains ACCOUNTING_DAY_V1 / Asia/Jerusalem**, including its daylight-saving boundaries. A run may contain partial accounting days; no reporting window rewrites a trade's economic accounting day.

The three nested historical windows are views of the **same hypothesis**, not three hypotheses or three independent samples. They may overlap heavily. Do not pool their trades or treat them as independent confirmations. Equal endpoint is a controlled comparison requirement for two arms within a window, not an automatic instruction to run all windows.

No automatic Backtest→Demo, Research→Active, or “next experiment” transition exists. Four-cell interaction studies may be run cell by cell manually; an interaction interpretation requires all four compatible cells, but the system never launches the missing cells automatically.

Source: RV1-DECISIONS §§4–6, 14; `methodology/SET.md` Part II §§34A–37, L3155–3435; `SYSTEM_PROTOCOLS.md` P8, L193–220.

### 3.1 Launch inputs — values supplied when a run is requested

| Required binding | Exact meaning and validation |
|---|---|
| research_id, arm_id | Existing final record and baseline/variant or 00/10/01/11 arm; resolve immutable contents |
| run_id, comparison_group_id | Research-only unique identity and manually selected comparison group; not canonical trading IDs |
| run_type, endpoint or start | One of the four profiles above and aligned historical endpoint or actual Demo start |
| universe_version | Exactly UNIVERSE-CORE-V1 |
| configuration digest | All symbol-specific Set versions + Position config + corrected Portfolio config + profile/report/evidence revisions + instrument-map digest |
| source manifest | Immutable actual datasets, available granularities, price bases, ordering domains, parent/child refinement map, selected ranges/pages, coverage/finality and availability timestamps; common source-manifest hash across arms |
| account/environment | Simulation namespace for Backtest; factual dedicated Demo account/environment for Demo; never a Live write target |
| starting capital | Positive exact amount in pinned accounting currency; separately evidenced Demo wallet balance; equal between controlled arms |
| starting state | Clean arm: no pre-existing owned exposure, entry remainder, reservation, close intent, consumed grant, cooldown or daily-loss latch; explicit canonical initialization snapshot |
| fee/cost/funding inputs | Effective historical schedules/events and units for the simulator; native complete financial facts for Demo; never assumed zero |
| execution evidence basis | Exact profile §4, historical price-observation coverage manifest, historical ordering policy and model version |
| native conformance evidence | For Demo, actual acceptance, protection, reconciliation and financial-profile proofs required by frozen contracts |
| retention destination/manifest | Durable export namespace, access boundary and source-copy/reference policy in §9; no ephemeral-only sources |

These are ordinary run parameters with specified interpretation, not unresolved definitions. They must be bound before launch; do not insert made-up account IDs, fee rates, wallet amounts, native ticker symbols or historical endpoints into the hypothesis.

### 3.2 Warm-up, isolation, and controlled inputs

Warm-up supplies the canonical 1m/5m/15m/1h histories, authentic ATR seed/checkpoint ancestry, ordinary 30 completed UTC-day populations (14-day minimum only where the canonical initialization rules permit it), same-clock turnover population, benchmark histories, and all required reference/cost/instrument evidence. A 7-day test still needs its full pre-window warm-up. Warm-up builds metric state only; it creates no pre-window Set events, active formation, trades or Portfolio commitments in the clean arm. Start a new authoritative formation epoch at the run boundary.

Each Backtest arm has an independent simulated exchange ledger, logical Portfolio state, Set event-consumption state and identifier namespace. All arms receive the same immutable exogenous history and starting balance; each recomputes its own endogenous grants, fills, fees, capital, slots, cooldown and Daily Loss. Never replay baseline capital decisions into the variant or share a mutable budget between hypotheses. Identical input manifests do not imply statistically independent outcomes.

Demo arms require genuinely isolated native exposure/wallet/side state and dedicated TriggerTrade activity. Two logical research labels in one netted or shared-budget account do not establish isolation. Parallel Demo comparison requires separate qualified isolated environments with compatible start/end and initial balance. A manually run sequential Demo remains useful descriptive evidence but is explicitly noncontemporaneous, not a controlled paired estimate. Configuration-specific leverage/size effects are not “held fixed” downstream.

If a user changes configuration, capital, instruments, manual trading actions, or account state mid-run, preserve the evidence and annotate the deviation; do not silently relabel the run as the preregistered arm. A new intended configuration receives a new run/configuration identity.

Source: RV1-DECISIONS §§3–5, 10, 16; `methodology/SET.md` Part I §2.1A, L181–185; Part II §§3–8; `SYSTEM_PROTOCOLS.md` P16–P17, L353–365; `methodology/ORDER_LIFECYCLE.md` §§4A–5 and §42.

### 3.3 Source and comparison preflight

Canonical signals consume exactly their frozen histories/timeframes: F-001/F-002 require actual canonical 1m source series; 5m/15m/1h dependencies and warm-up remain unchanged. Missing required signal data makes that metric/run unavailable. No 5m-for-1m or 15m-for-5m substitution, synthetic signal candles, or current-for-historical replacement is allowed. An execution dataset may be finer than a signal dataset only when those factual observations actually exist, without changing signal timeframes.

Before any paired interpretation, pin one common historical inventory/refinement map and all price-basis mappings for all comparable arms. Dataset choice is not driven by which arm would win or become ambiguous. Later source improvements produce a new common manifest and manually requested reruns; never splice favorable observations into an old result. Ordinary source unavailability is a run outcome, not a reason to invent a new trading metric or reopen B-01.

The baseline and variant start with the same clean initialization and positive exact capital chosen before outcomes. Smaller 10% allocations can reduce treatment activation; do not retune unrelated minimums or weights to force activity. All admitted/refused grants and final construction amounts must be retained. The historical R2 cap/minimum reachability qualifications remain in provenance, not current first-wave treatments. Current R-022/C-012 and R-026/C-015 record valid predicate disagreement separately from executable and finalized economic differences; source unavailability is never disagreement.

## 4. HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1 with corrected intrabar resolution

### 4.1 Simulator boundary and provenance

The simulator occupies the factual/execution side of the **existing API boundary** in a research namespace. It does not replace Position/Portfolio/Set/Lifecycle logic. Model acknowledgements, executions, protective-order states, fees and wallet facts are **simulated facts within that run**, not authentic historical exchange order evidence. Every resulting event/result carries research envelope provenance identifying the model, input manifest, simulated sequence and original historical source references. Canonical wire schemas are not extended: research provenance is a separately joined envelope.

No queue position, self-impact, order-book competition, microsecond priority, exact POST_ONLY placement, or hypothetical acknowledgement latency is modeled. Zero modeled acknowledgement delay and full-quantity touch fills are explicit assumptions, not assertions about Bybit. Results can be optimistic relative to Demo/Live. Market gaps and unresolved intrabar chronology remain disclosed; high liquidity is not proof of identical realized execution.

### 4.2 Exact intrabar policy and immutable binding

```text
BACKTEST_EXECUTION_MODEL:
HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1

INTRABAR_RESOLUTION_POLICY:
FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1

Priority:
1. Source-valid, authoritative ordered historical execution-price observations
2. Progressively finer factual historical bars actually available for that price basis
3. Order-invariant safe execution outcome under the pinned liquidity model
4. Otherwise: research ambiguity + dependency-aware run censoring

FIXED_SYNTHETIC_HIGH_LOW_PATH:
NONE
```

These are research profile references only. The liquidity approximation's zero modeled acknowledgement latency, full-quantity touch assumption, source-provenance envelope and canonical finality requirements remain, except that an unresolved ordering no longer acquires a synthetic path. This corrected package assigns the new execution-profile revision/digest; old low-first runs retain their old identity and cannot be silently mixed with corrected runs. [R08; current prompt §§5–10]

Before a comparison, pin one common source inventory, interval/refinement map, price-basis mapping and policy revision. All compared arms receive the same available factual observations for a symbol/time interval, regardless of which arm encounters an ambiguity. Do not fetch finer data only for a favorable arm, use a different fallback by side, or select a dataset after inspecting relative P/L. A later source improvement creates a new common source-manifest revision and manually requested reruns; previous runs remain in the export.

### 4.3 Hierarchy levels

| Level | Required source / ordering authority | Fill and protection resolution | Unavailable/ambiguous boundary | Mandatory exported evidence |
|---|---|---|---|---|
| L1 — ordered factual observations | Complete trade/tick/quote/required trigger-price records with documented source time and actual ordering semantics | Process eligible orders against subsequent factual observations; apply pinned full-fill/acceptance model; use exact causal activation order | Missing required price basis/coverage or unresolved order between competing facts cannot be invented | Source record IDs, timestamps, sequence domain, selector/page manifest, model-vs-factual event type and trigger/execution joins |
| L2 — finer factual candles | Complete real child bars with known boundaries, correct price basis and consistent source/parent coverage | Process child intervals chronologically; a child is not assumed to have an O-L-H-C order; use L3 within it if needed | Finest available child still permits different execution states/results, or a required child interval is missing | Parent/child interval references, resolution selected, available and missing finer ranges, consistency checks |
| L3 — order-invariant safe cell | Remaining factual OHLC cell plus pre-cell order/protection state; explicit common touch/time approximation below | Commit only a pre-approved case whose relevant execution order/state is the same under all admissible threshold-touch orders; actual O and C constrain, not invent, that order | Competing exits, entry-versus-favorable-touch uncertainty, price-basis races or material timing alternatives → L4 | Touched-level set, known causal constraints, unique-case reason, modeled timestamp interval/basis, confirmed states, diagnostic limitations |
| L4 — unresolved | The same factual cell and unresolved alternatives; no additional source assumed | No invented exit/fill chain for the ambiguous portion; retain last defensible checkpoint and censor its shared-Portfolio dependency suffix | `run_status=UNAVAILABLE`, reason `INTRABAR_ORDER_UNRESOLVED` for a completed headline result | Ambiguity cell, competing orders/thresholds, alternative event relations, affected tranches/symbols, shared-capital frontier, last checkpoint and report population exclusions |

Native market trades establish price sequence, not execution of a hypothetical TriggerTrade order. Even L1 fills remain simulator-produced execution evidence in Backtest. Actual Demo fills/acceptance use native evidence and never pass through this candle resolver. [S10–S13; R08 L103–110, L151–163]

### 4.4 Bounded L3 admissibility — no hidden path generator

L3 is not a mandate to build a general exhaustive path or counterfactual simulator. Its safe cases are intentionally narrow. An implementation may reject an unproven case; it may not turn “no proof found” into favorable or adverse execution.

1. Use only orders already eligible at the cell start, or a causally proven within-cell Entry/protection chain. First process any known opening-price jump. Then examine remaining threshold eligibility. Do not credit the just-finished signal bar to an order created from its close.
2. If no eligible execution threshold is reached, no fill is established. If exactly one relevant threshold is reached and there is no competing cancellation/protection/timing dependency, its trigger/fill outcome can be unique under the full-touch model.
3. A nested Entry→Stop can be unique under the pinned threshold-touch model when Entry was resting before the cell, the opening price is on the nonfilled side, Stop is further beyond Entry in the same adverse direction, and no TP or competing event can resolve first. This is a model crossing inference, not proof of a native fill at either price.
4. A new Entry and favorable TP touch are not automatically chronological. A final factual close beyond TP after an established Entry can supply a later favorable observation; a high/low alone cannot. The opposite-side mirror is required.
5. A unique exit label is insufficient if feasible order/timing changes quantity, protection coverage, close authority, fees/funding eligibility, economic accounting day, capital availability, slot/grant decisions, or the subsequent portfolio state. Refine or censor that cell.
6. Canonical TP and SL in this frozen baseline are **MARKET when triggered**, not resting TP limit orders. In an ordinary unique touch case without an observed jump, the model's threshold execution price is an acknowledged zero-unobserved-slippage approximation. With a factual jump, use the first factual executable market-price observation under the price-basis mapping; never the skipped favorable threshold. If trigger and executable-price histories cannot be aligned, do not manufacture a price. [S11 L903–909]

**Coarse event time, explicitly modeled:** when L3 establishes the execution chain but not the interior timestamps, use a common cell-end discretization only if item 5 passes. For a source cell `[a,b)`, give its model-inferred interior execution chain the timestamp `b − 1 microsecond`, with separate causal model ordinals; known factual opening events retain their factual/model opening boundary. Canonical timestamp representation allows microsecond precision; this timestamp is a deterministic simulator clock point, **not** a claim of native microsecond matching priority. Store the full uncertainty interval `[a,b)`, `MODEL_CELL_END` time basis, and all causal ordinals. It creates no synthetic prices, candles or high/low timepoints.

Do not use that clock convention when an intervening funding instant, accounting-day boundary, accepted cancellation, model/native event, grant decision or run endpoint could lie before or after the execution and change the result. Require finer factual ordering or L4. Source intervals too short to represent the convention safely also require finer ordered facts. Accounting still applies the unchanged P8 rule to the modeled closing execution; the research envelope identifies its non-native time provenance. [S09 timestamp form; S13 P8]

This limited timing/ordinary-touch approximation is kept separate from uncertain **which-event-first** outcomes. It cannot resolve a Stop/TP conflict. Fills from a finished source cell are never revealed to an earlier Set decision using future candle information. Canonical computations see only the original source observations at their proper cutoffs; execution-cell resolution is buffered until its evidence is available. If a decision needed the unresolved intra-cell state earlier, L3 is inapplicable, not a license to replay that decision with hindsight.

### 4.5 L4 propagation, reporting and comparison

Mark ambiguity in the **research envelope**, not as a new canonical lifecycle state or an invented exchange error. Do not issue a fake Set invalidation, Manual Close, CANCELLED_ZERO_FILL, CLOSED, financial result, or capital release to make the run terminate.

The first unresolved cell defines a conservative dependency frontier at the last committed, unambiguous shared-Portfolio checkpoint. Resolve the cell before publishing its modeled events; if the cell cannot be resolved, keep the checkpoint and the full raw evidence/constraints. In V1, stop the affected arm's whole coupled Portfolio simulation at that frontier. Do not continue other coins as though the unresolved trade consumed no capital, had closed, or had never existed. Unrelated earlier finalized facts remain retained.

A fully processed interval may still have endpoint-open exposure under the existing profile. That is distinct from an interval not processed because intrabar execution was unresolved. For the latter, full-window P/L, trade rate, profit factor, drawdown and other dependent headline statistics are UNAVAILABLE/incomplete. Display any defensible finalized-prefix subtotal only as such, with its actual cutoff, sample counts and unresolved suffix—not as a complete BACKTEST_7D/30D/90D result.

Do not exclude just ambiguous trades from win-rate/expectancy denominators while treating their hypothetical downstream trades as real. Censoring is configuration-dependent; the surviving trades are not a random sample. There is no automatic “good” or “bad” strategy decision.

For a baseline/variant or four-cell comparison, retain each run's full evidence and coverage. A same-window point comparison is unavailable if a necessary arm is incomplete. An optional descriptive common-prefix report uses the earliest unambiguous frontier shared by the selected arms and labels the reduced interval and selection limitation. It is not a new hypothesis, an independent validation window, a full-window causal estimate, or an instruction to run anything automatically.

### 4.6 Financial facts and Portfolio economics

Canonical accounting and numeric policies are unchanged. Simulated fees/rebates use the pinned effective maker/taker schedules and native cash quantum for the modeled executions. Simulated funding uses complete applicable historical settlement events, native settlement basis and the canonical funding attribution algorithm. Other supported costs are included under the same source/currency/coverage rules. No universal fee number, spread surcharge, funding zero, or FX conversion is invented. No-row cost/funding coverage proves zero only when complete coverage or evidenced non-applicability actually establishes that result for the simulated profile.

The simulated exchange wallet books its modeled executions/cashflows; Portfolio reads that wallet/equity and canonical receipts through the unchanged ownership boundaries. Final research reporting aggregates canonical finalized tranche results, **not** wallet cashflows plus the same results a second time. Portfolio daily base/realized loss and exact capital commitments still follow the frozen formulas. Displayed research drawdown or expectancy never substitutes for them. Foreign-currency or otherwise inadmissible required amounts remain finality-blocking; research cannot convert them to finish a report.

No queue data are necessary for this model. Financial or required market-data absence can still make an individual run unavailable; it is not permission to fabricate FINAL.

Source for §§4.1–4.6: RV1-DECISIONS §§2–3, 7–9; `methodology/ORDER_LIFECYCLE.md` §§1–11, §§32–34, §42; `SYSTEM_PROTOCOLS.md` P5–P8 and P11–P15; `api-contracts/NATIVE_FACT_PROFILE.md` §§1–5; `schemas/NUMERIC_POLICY.md`; `methodology/POSITION_RULES.md` Part I §§17–40. Proxy acceptance, full-quantity touch assumptions and genuinely tied cross-symbol scheduling are retained research-model conventions, not native facts. The previous deterministic OHLC path is superseded by the approved causal-invariance-or-censor hierarchy; no fixed high/low order remains operative.

### 4.7 Execution edge cases and retained emulator assumptions

#### 4.7.1 Entry and protective-event cases

| Case | Required treatment |
|---|---|
| LONG already open; Stop and TP both touched in one unresolved cell | First seek finer factual order. If opening facts do not already determine a close and both first-exit orders remain feasible, L4. Do not select Stop first or TP first. Keep both candidate event relations in research evidence; no canonical FINAL for either hypothetical branch |
| SHORT already open; both protective levels touched | Exact side mirror. Same policy and censoring test; no change of path orientation or automatic favorable/adverse preference |
| Already open; only one protective level touched | L3 may resolve the unique trigger under the common touch-price/time model only if protection was active and there is no competing cancellation, quantity, price-basis, funding or portfolio-timing ambiguity. Otherwise refine/L4 |
| Pending LONG buy LIMIT; Entry and TP touched, no Stop | Do not assume the high occurred after Entry. For example O=100, Entry=99, H=105, L=98.5, TP=104, C=101 admits a prior high followed by Entry without TP, or Entry followed by TP. L4 unless finer data or a subsequent factual observation establishes the same terminal outcome in every admissible case |
| Same case, with closing observation at/above TP | Once Entry eligibility before that closing observation is established, the closing price can prove a post-Entry favorable reach under the model. L3 is possible only if it also establishes protection availability and all material timing/price dependencies; do not infer a native TP execution from the candle alone |
| Pending SHORT sell LIMIT; Entry and TP touched | Mirror the LONG logic: a low before Entry cannot count as a TP; a later factual close at/below TP may establish a post-Entry reach. Otherwise L4 |
| Pending LONG Entry and Stop touched, TP not touched | With Entry already accepted before the cell and opening above Entry above Stop, adverse nested threshold crossing gives Entry→protection→Stop under the retained full-touch/zero-latency model. L3 only with the explicit gap/timing guards; no pre-Entry Stop execution. If Entry activation was inside the cell, or ordering is otherwise not established, refine/L4 |
| Pending SHORT Entry and Stop touched | Mirror: opening below Entry below Stop. Same guards and causal sequence |
| Entry, Stop and TP all touched | Evaluate opening facts and known causal activation first. If TP can occur after Entry before Stop in one feasible order, but before Entry or after Stop in another, L4. Never assemble Entry from one assumed path and an exit from another |
| Entry was submitted/accepted partway through an unresolved cell | Entire-cell high/low cannot prove a post-acceptance fill. Use later ordered/finer facts or a sufficient later endpoint observation. If the possible touch is before or after acceptance and affects state, L4 |
| Price touches Entry before acceptance or protection before Entry fill | Ineligible event; never retroactively fill or activate a child. The finishing candle is not reusable for a new order created from that candle's completed signal |
| Entry remains untouched | Retain the ordinary pending order, accepted_at-based cooldown and capital hold. No bar-count expiry, chasing, repricing, cancellation timer or market Entry fallback is added |
| Cancellation competes with a possible same-cell Entry fill | Source-proven prior execution/cancel order governs. If ordering changes remaining quantity/close authority and is not established, refine/L4. The previous catch-all “fill first” convention cannot invent ordering for this unresolved case |

#### 4.7.2 Acceptance, gaps, quantity and protection

**POST_ONLY with factual quotes:** only the research exchange emulator performs the acceptance approximation; Position and Lifecycle do not acquire a new local business-price gate. Use the valid as-of bid/ask mapping already specified by the profile. Equality/crossing follows the pinned modeled exchange rule. This is not proof of the hypothetical exchange acknowledgement. [S10; R08 §4.4]

**POST_ONLY with candle-only history:** retain the explicit last-known-price proxy, using only a completed historical observation available at submission. Buy at/above that proxy and sell at/below it are model rejections under the existing profile; noncrossing eligible instructions receive model acceptance with zero latency after dispatch. Label `acceptance_evidence_basis=MODEL_LAST_PRICE_PROXY`, preserve the referenced price/cutoff and the non-native acknowledgement. Never use the future cell's high, low, close, or eventual profit to decide acceptance. A missing required valid as-of price/metadata yields unavailable execution, not assumed acceptance. Actual Demo has no such proxy. [R08 L125–131]

**Observed gaps:** a first factual observation beyond a protective trigger is a price jump, not movement through an interpolated line. For the frozen MARKET-on-trigger protective orders, use the first eligible factual executable market-price observation and retain trigger/execution bases separately. A LONG gap below Stop cannot be booked at the more favorable skipped Stop. A SHORT gap above Stop is symmetric. A resting Entry limit filled under the approximation remains at its approved limit, as the retained model specifies; no discretionary favorable price improvement or price chasing is added. The emulator may model immediate protection after that Entry, but cannot backdate a child ahead of the fill. [S10–S11; R08 §§4.4–4.5]

**Unobserved interior gap/slippage:** an ordinary OHLC touch price is not evidence that no interior jump occurred. Where L3 is used, zero unobserved intrabar slippage remains an explicit liquidity-model assumption. Do not describe it as gap-proof native execution. If source observations actually show a jump or incompatible trigger/execution-price chronology, the factual constraint overrides that ordinary-touch case; refine or use L4 where no unique executable observation is available.

**Missing required trigger-price series:** last-trade OHLC cannot silently substitute for a required mark/index/other native trigger basis. Match the immutable Order Spec/native-profile requirement. Data on another price basis can be retained as supplementary evidence, but cannot certify the absent required selector. [S09; R08 L137]

**Quantity and partial fills:** absent hypothetical-order quantity-level evidence, Backtest retains its stated full-remaining-quantity fill approximation. Public market-trade volume is not proof of the hypothetical order's own partial fill. Do not invent partial percentages from bar volume or copy one arm's native fills into another counterfactual arm. Actual native partial fills in Demo retain the complete canonical PARTIALLY_FILLED path, quantity-scoped protection and remaining-entry management. [S11 §§7, 16–17; R08 §4.4]

**Protection activation:** modeled protective children become effective only after Entry quantity is modeled filled and the simulator produces the required protection-confirmation evidence. A submit command alone is not protection proof. Live/Demo require actual native confirmation. A later Set direction change is not a new exit strategy. If protection state cannot be established, preserve the canonical unresolved/reconciliation behavior; do not invent a protected interval to credit TP. [S11]

#### 4.7.3 Same-time events, cross-symbol effects and endpoints

| Case | Required treatment |
|---|---|
| Ordered records share a timestamp but have an authoritative source sequence | Use that actual order. Source sequence domain and original IDs must be retained |
| Same-symbol conflicting records share a timestamp without ordering authority | Do not treat a lexical trade ID, file order, receipt order or OHLC high/low label as chronology. If the conflict matters, L4 |
| Same-timestamp multi-symbol snapshots/opportunities | Retain the existing **research scheduling** convention: factual within-source causal order first, then the fixed UNIVERSE-CORE-V1 ordinal for genuinely tied cross-symbol cohorts. Pin it across arms and log capacity-sensitive ties. It is not a market-path assertion or a new Core Set winner rule |
| Events are only known to lie somewhere in overlapping cells, not truly at the same timestamp | Do not manufacture a “tie” to use universe ordinal. Apply L3's material-timing test; refine or censor when order affects shared capital, grants, slots, funding or Daily Loss |
| Several tranches/long and short positions share one symbol | Check all affected eligible children/quantities against one factual constraint set. Never select separate incompatible price paths per tranche. If a joint unique outcome is not established, censor the shared Portfolio dependency suffix |
| Funding or accounting boundary lies in an uncertain execution interval | Do not select the side of the boundary that gives cheaper funding or a preferred Daily Loss day. Use finer timing proof; otherwise L4. P8 accounting day remains derived from the final closing execution, not reporting/ingestion time |
| Run endpoint cuts an unresolved source cell | Do not use that cell's later high/low/close to decide a pre-endpoint event. Seek factual subinterval data wholly admissible to the endpoint; otherwise retain the unresolved/open checkpoint and incomplete report. Never synthesize a truncated candle or silently move the endpoint |
| Position/order still open at an otherwise fully processed endpoint | Retain actual modeled exposure, children, pending Entry, commitments and incomplete finance. Endpoint is not a forced exit, Entry TTL, FINAL event or capital release. Completed observation and fully closed trades remain different concepts |
| Normal later evidence finalizes a proved pre-endpoint economic close | Preserve the original economic event and issue a new report revision, under the existing profile. Do not rewrite a frozen canonical result or move the close into the delivery day |
| Finer historical data are obtained after an ambiguity | Preserve the old run and ambiguity record. A new common source-manifest revision supports a manually requested replay/rerun. Do not splice selected favorable outcomes into the old canonical result stream |

The symbol order for genuine research scheduler ties remains BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB. With BTC newly eligible to trade, the cohort can have different capacity usage than an old benchmark-only run. This is why the corrected portfolio/source/configuration version must be pinned and compared within the same revision. The ordinal is not a change in the fixed 10% allocations.


**Normative guard:** all enum-like execution-resolution, ambiguity, model-time, frontier and report-completeness values in §4 are research metadata. They do not extend canonical Lifecycle states or wire schemas. `FACTUAL_ORDER_RESOLVED` describes source price ordering; the hypothetical Backtest fill remains simulated under the full-remaining-quantity model. Native Demo uses neither the candle resolver nor the model POST_ONLY proxy.

No fixed high/low path or manufactured event timestamp can resolve a competing outcome. `MODEL_CELL_END` is allowed only after a proved order-invariant causal chain and the material timing test; it does not resolve quantity, funding, accounting-day, cancellation, grant, slot or endpoint uncertainty.

## 5. Demo, run boundary, and finality

Demo uses the actual Demo exchange/API environment and real-time data. The historical approximation is **not** applied to native acceptance, fills, partial fills, fees or protection. All existing native conformance gates remain deployment obligations. Failed or ambiguous native evidence is reported as such; a successful specification review does not attest to a connected adapter.

At the observation endpoint E, no new research opportunities are admitted to the run. **The endpoint is not an Entry TTL, Manual Close, Cancel Signal or artificial financial finality.** Existing lifecycle management and protection remain active in Demo; the user remains responsible for continuing supervision. In Backtest, persist the exact simulator state at E without injecting a fake “missing market” event or forced close. Ending the evidence window does not release capital or a slot.

Run `COMPLETE` means the requested observation interval was processed, not that every position is CLOSED or every report is final. Store separately `observation_status`, `evidence_completeness`, outstanding lifecycles, endpoint exposure, pending Entry attempts and unresolved financial results. A monetary subtotal from currently finalized trades must be labeled `FINALIZED_SUBSET` whenever unresolved or missing evidence remains; do not describe it as the entire run's definitive P/L.

Final results whose **economic closing execution** is before E may arrive later because cleanup or financial proof completes later. They enter a new immutable report revision with the same original run window and economic accounting day. Results with economic exit at/after E do not enter the original window's performance even when the lifecycle belongs to that run. Preserve them as linked continuation evidence. No shadow trade or assumed endpoint mark-to-market is substituted for a realized result.

Run status vocabulary: `NOT_RUN`, `RUNNING`, `COMPLETE`, `FAILED`, `UNAVAILABLE`. Canonical lifecycle states remain in their own field. Human-managed research notes/status may be stored with actor and time; no automated strategy recommendation is authoritative.

Source: RV1-DECISIONS §§3.4–6, 8–10, 15; `methodology/ORDER_LIFECYCLE.md` §§7–11, L522–740; `SYSTEM_PROTOCOLS.md` P6–P8, L114–220, and chronology/finality proof rules, L296–333.

## 6. Research-only reporting contract

### 6.1 Common populations, identity, time and numeric rules

Profile: `REPORT-R-V1-R2`. All entries in this section belong exclusively to the research reporting namespace and have `allowed_trading_consumers = []`.

A **trade** is one logical tranche that obtained positive Entry execution and has a canonical finalized net result with canonical CLOSED eligibility. A zero-fill cancellation/rejection is not a completed trade even when its operational record is terminal. Count by the immutable tranche/result identity, not native order count or aggregate native side position. Deduplicate canonical result receipts; conflicting evidence is an integrity incident, not another trade.

For window `[S,E)`, eligible performance population F comprises those filled tranches with `accounting_effective_at` (the permanent final economic closing execution instant) in `[S,E)`, canonical `FINAL` financial evidence, correct pinned currency and canonical closure eligibility established by the report's evidence-as-of revision. Canonical `result_id`/`tranche_id` joins and finality proofs must both resolve. No provisional/unrealized/native aggregate P/L is added. Later evidence delivery never moves the economic exit date. Standard clean research arms have no carry-in exposure; ACTIVE can have carry-in and must disclose it rather than imply equivalence.

A report retains `window`, `evidence_as_of`, `report_revision`, numerator/denominator populations, coverage, excluded/unfinalized counts, and zero-result count. A complete genuinely empty Overall population has `Trades=0` and realized sum `0`, with no evidence of profitability. Missing coverage is never a complete empty population. An absent LONG/SHORT cohort has monetary/rate cells `UNAVAILABLE`; R-006 BTC has scope status `NOT_APPLICABLE` and unavailable (null, reason-coded) monetary/rate cells; supporting observed counts may still be zero. Do not display zero performance for an unobserved side or unsupported source domain.

All sums retain the canonical exact monetary amounts/currencies; all research ratios retain exact numerator and denominator or an exact rational representation. No binary-float tolerance or pre-display rounding changes classifications. Render ratios/percentages to six fractional digits with HALF_EVEN only in presentation; preserve exact underlying values and unit. Undefined/unbounded values are typed, not arbitrary finite numbers or JSON NaN. Canonical numeric policies are not changed by this reporting format.

### 6.2 Required comparison statistics

Let `N=|F|`, `p_i=canonical net_realized_result` of finalized filled trade i, `W={i:p_i>0}`, `L={i:p_i<0}`, `Z={i:p_i=0}`, `G=sum(p_i for i in W)`, and `A=abs(sum(p_i for i in L))`. These are descriptive report populations/aggregates, **not new canonical metrics**.

| Reporting ID | Display name | Exact definition, unit and boundary behavior |
|---|---|---|
| RR-V1-001 | Net Realized P/L | `sum p_i`; pinned accounting currency. Primary monetary outcome. Complete empty Overall = 0; incomplete/unsupported scope not silently zero. Display finalized-subset coverage where applicable. |
| RR-V1-002 | Trades | N finalized **filled** logical tranches. Rejected opportunities and zero-fill attempts are excluded. Support counts distinguish no observation, unavailable scope and an actually empty eligible population. |
| RR-V1-003 | Win Rate | `|W|/N`, displayed percent. Z remains in N and is never a win. N=0 → UNAVAILABLE/NO_FINALIZED_TRADES. Store win/loss/zero counts separately. |
| RR-V1-004 | Expectancy | `sum p_i / N`, accounting currency per finalized trade. N=0 → UNAVAILABLE, never 0. |
| RR-V1-005 | Profit Factor | G/A. A>0 → exact finite ratio, including 0 when there are losses but no wins. A=0 and G>0 → UNBOUNDED_POSITIVE with null finite numeric value and NO_LOSING_TRADES flag. G=A=0 → UNAVAILABLE/ZERO_OVER_ZERO. N=0 → UNAVAILABLE/NO_FINALIZED_TRADES. |
| RR-V1-006 | Max Drawdown | Absolute currency decline on the **realized result path**, defined in §6.3; excludes unrealized exposure and is not account/liquidation drawdown. |
| RR-V1-007 | Average Winner | `G/|W|`, accounting currency per winning finalized trade; no winners → UNAVAILABLE. |
| RR-V1-008 | Average Loser | `sum(p_i for i in L)/|L|`, **signed negative** currency per losing finalized trade; no losers → UNAVAILABLE. Z belongs to neither average. |
| RR-V1-009 | Fill Rate | As-of-window Entry-attempt statistic in §6.4. Store counts, censored attempts and observation endpoint. |
| RR-V1-010 | MAE | Per-trade maximum adverse **unlevered price** excursion while actually open; displayed aggregate is arithmetic mean of available finalized-trade MAE percentages, with complete-coverage denominator (§6.5). |
| RR-V1-011 | MFE | Corresponding maximum favorable open-interval price excursion and equally weighted mean percentage (§6.5). |

### 6.3 Exact realized Max Drawdown

Group eligible finalized `p_i` by their permanent economic closing instant, not callback/finalization/receipt time. Where a common authoritative execution sequence exists within an exact timestamp, preserve it; otherwise sum the simultaneous timestamp cohort into one result step rather than manufacture a cross-symbol order. Set `C_0=0`; for each ordered step j, `C_j=C_(j−1)+sum(p_i in step j)` and `H_j=max(0,C_1,...,C_j)`. Report `max_j(H_j−C_j)` in accounting currency. Persist the ordered step population so the path is reproducible.

A complete empty Overall path has amount 0 and NO_FINALIZED_TRADES annotation; unavailable direction/domain has no path and UNAVAILABLE drawdown. No percentage is required in V1, avoiding an invented capital denominator for segment/coin slices. Deposits, withdrawals, unrealized P/L and repeated fee/funding amounts are not additional summands. For each group recompute its path from its own result population; **do not sum or average subgroup drawdowns** to obtain Overall. This statistic measures realized-result drawdown only; open-position risk can be materially larger.

### 6.4 Exact Entry Fill Rate

An Entry attempt enters the denominator when the canonical Lifecycle **actually dispatches** the authorized immutable Entry create request (`SUBMITTING`: request in flight), evidenced by the durable create-request/transport dispatch record and lineage. Merely holding Order Spec/Submit Authorized/READY_TO_SUBMIT is insufficient. Position rejects, Set matches, failed grants and hard pre-dispatch technical failures never enter this denominator.

Deduplicate the logical Entry attempt by run namespace plus `client_order_link_id`/tranche/Order Spec lineage. Retransmission/reconciliation of the same create intent is not another attempt. A reconciled request with uncertain send outcome enters when dispatch is established; until then preserve it in an unresolved-dispatch support count and qualify denominator completeness. Include dispatched requests subsequently rejected by the native/model exchange, including POST_ONLY rejection. Never count a timeout as a proven zero fill before reconciliation.

For dispatched attempts whose first dispatch is in `[S,E)`, the observed numerator is the number with any positive attributable Entry execution **before E**. Partial fill counts as a filled attempt, not a completed trade. `Fill Rate = numerator / denominator`; denominator 0 → UNAVAILABLE/NO_DISPATCHED_ATTEMPTS. Report separately: terminal zero-fill attempts, pending zero-fill attempts at E, uncertain execution outcomes, filled nonfinal trades, and dispatch-evidence completeness. Pending/uncertain attempts are **right-censored**, not alleged permanently missed trades. Where required dispatch or fill-history coverage is incomplete, the headline value is UNAVAILABLE and known support counts remain visible. With complete as-of coverage, a pending attempt may be unfilled at E; the displayed rate is explicitly as-of E, not eventual lifetime fill probability.

### 6.5 Exact MAE / MFE, including partial executions

Use the pinned factual observation series, plus extrema of factual cells proven wholly inside the actual modeled/native positive-exposure interval. There is no synthetic high/low path. Retain source/price basis, sampling resolution, scope and coverage. A whole bar high/low cannot be attributed to a position that entered or exited inside the unresolved bar. Incomplete within-open coverage makes complete MAE/MFE UNAVAILABLE with INTRABAR_DIAGNOSTIC_COVERAGE_INCOMPLETE; keep partial samples as partial evidence, never as the true maximum or zero. Diagnostic unavailability alone does not erase a fully supported canonical monetary result. These are observed-resolution diagnostics, not claims about unobserved continuous-time extremes.

Use the canonical execution ledger to reconstruct intervals with attributed logical quantity strictly positive. For each eligible observation t within those intervals, let `P(t)` be its price and `A(t)` the canonical accumulated Entry average price in force at that point, using only already executed Entry quantity. Let `d=+1` for LONG and `−1` for SHORT. Report-only excursion is `r(t)=100*d*(P(t)−A(t))/A(t)`. `MAE=max(0,−min r(t))`; `MFE=max(0,max r(t))`. Units are positive-magnitude unlevered percentages. They exclude fees/funding and are not return on margin or cash P/L.

Include the first Entry execution price and the final economic exit price as boundary observations. Use the pre-exit average for the closing observation. Additional partial Entry fills update A only after their factual execution; do not retrospectively use the final average before those fills. Partial exits retain the canonical Entry basis for the remaining exposure. Temporary zero-exposure intervals contribute no observations; a later canonical refill, if one occurs in the same lifecycle before permanent closure, starts another positive-exposure interval. No post-permanent-exit price contributes, even when cleanup/CLOSED is later. Missing/contradictory execution chronology makes the diagnostic unavailable rather than guessed.

At an additional Entry fill while quantity was already positive, evaluate that fill-price observation against the pre-fill Entry average, then update the canonical Entry average and evaluate the same price against the new average. The first fill has no pre-fill exposure and uses only its newly established average. On a partial or final exit, use the pre-exit average. At each observed price/basis breakpoint include both defined one-sided values; this removes ambiguity caused by simultaneous price observation and basis change. A missing prerequisite source event is not supplied by this reporting convention.

For a still-open endpoint lifecycle, retain a separately labeled `OPEN_INTERVAL_TO_ENDPOINT` diagnostic; do not mix it into the completed-trade MAE/MFE means. For the main completed-trade means use F members with complete diagnostic coverage, report that count and excluded count, and show partial measurement coverage explicitly. No available diagnostic trades → UNAVAILABLE. No post-exit “would have won” inference is valid.

Source for §6: RV1-DECISIONS §§7–9, 13–15; `methodology/ORDER_LIFECYCLE.md` §§2, 7, 9–10, 32–34, 43; `SYSTEM_PROTOCOLS.md` P6–P8 and chronology rules; `methodology/POSITION_RULES.md` Part II §51, L3220–3244; Part IV §48, L5465–5486.

### 6.6 Incomplete dependency suffix, diagnostic gaps, and revised report populations

For `UNRESOLVED_INTRABAR`, preserve the last committed unambiguous shared-Portfolio checkpoint and stop that arm's dependent Portfolio suffix. Full-window dependent headline statistics are UNAVAILABLE/incomplete, with the requested interval, actual frontier, excluded/unresolved evidence, source/profile revisions and reasons. Do not emit any fabricated fill, exit, FINAL, CLOSED, grant, or release. Do not drop just the ambiguous trade and continue other coins as if shared capacity were known.

Defensible finalized-prefix statistics have a distinct `PREFIX_ONLY` report population and exact cutoff; they are never displayed as complete BACKTEST_7D/30D/90D statistics. A same-window point comparison requires all necessary arms (all four cells for an interaction) to have complete dependent intervals. Any incomplete arm makes that comparison unavailable. Optional common-prefix views use the earliest shared unambiguous frontier and are descriptive selected samples, not unbiased estimates or automatic strategy decisions.

Distinguish four conditions: (a) a fully processed endpoint with legitimately open/pending exposure; (b) an earlier unresolved intrabar frontier; (c) an otherwise finalized trade with incomplete diagnostic price coverage; (d) per-question symbol inapplicability. They have different populations and reasons. None is numeric zero. R-006 BTC is NOT_APPLICABLE; missing factual direction observations are UNAVAILABLE. Report revisions retain their exact population members and as-of evidence, never overwrite canonical results or old reports.

## 7. Supplementary source-required reporting without shadow positions

The eleven headline statistics do not delete the frozen mandatory Entry/TP/Portfolio/Lifecycle diagnostics. Preserve their raw evidence and use the following research-only measurement rules. All count/frequency denominators are **the listed stage population**, not completed trades unless explicitly stated. A zero denominator is UNAVAILABLE; incomplete required stage evidence gives UNAVAILABLE plus known support counts. Source-defined diagnostic amounts/flags are copied, not recomputed under different trading semantics.

| Diagnostic group / source names | Population, definition and handling |
|---|---|
| LONG/SHORT, coin, Set family, selected Entry/target/reference type, source timeframe and reference age | Retain canonical direction/family/type/reference identity; group observations by their owning stage. Ages and improvement ATR/% use canonical outputs. Unavailable type/reference remains a separate reason, not an invented category inference. |
| Time to first/full fill; submit-to-acceptance | First/full Entry execution time minus first dispatch, and acceptance time minus first dispatch, for attempts with the corresponding proven timestamps. Also retain acceptance-to-fill duration separately, labeled by origin. Unreached events at E are right-censored; negative/unknown chronology is UNAVAILABLE. Average only observed durations and disclose uncensored count. |
| Missed-trade rate | V1 display alias for **terminal-unfilled submitted-attempt rate**: terminal zero-fill attempts / all attempts with established terminal Entry outcome in the run's submitted cohort. Pending/uncertain attempts are excluded and reported. This is not a probability of missing profitable opportunities and contains no shadow trade. |
| Entry distance bands / eventual expectancy | Fixed report bands for canonical improvement_atr: `[0,.10)`, `[.10,.25)`, `[.25,.50)`, `[.50,1.25)`, `[1.25,2.00)`, `[2.00,+infinity)`. Negative/invalid/unavailable values are separate evidence errors. For each band use finalized trade results in F and the same expectancy definition; report censored/unfinalized members separately. Later final results create report revisions, not post-exit counterfactual prices. |
| TOO_SHALLOW / TOO_DEEP frequencies | Number of Entry candidate evaluations with that canonical classification / all Entry candidates with completed valid classification. Candidate-level, not opportunity-level. |
| ENTRY_TOO_DEEP_AFTER_ROUNDING frequency | Entry selector invocations terminating with that source reason / completed Entry selector invocations. Preserve chosen candidate and post-round evidence. |
| POST_ONLY rejection/cancellation frequency | Submitted attempts with confirmed native/model POST_ONLY terminal rejection/cancel reason / dispatched Entry attempts with complete outcome evidence. Mark simulator observations MODEL, never native predictions. |
| Hard non-market technical incompatibility frequency | Hard-compatibility evaluations failing with the canonical technical reason / completed hard-compatibility evaluations; pre-dispatch failures remain outside Fill Rate. |
| NO_REACHABLE_TARGET frequency | Dynamic TP selector invocations ending in the canonical reason / completed Dynamic TP selector invocations. |
| Too-close / too-far target frequency | TP candidates classified TOO_CLOSE / TOO_FAR divided by evaluated TP candidates with a completed classification. Also retain source too_close_skipped_count, selection_terminated_by_too_far and first_too_far_distance_atr at invocation level. |
| Thesis override frequency | TP invocations with proven selection of the bound thesis in place of the otherwise selected baseline reference / invocations with applicable, resolvable thesis override evaluation. Under policy NONE the applicable denominator is zero, so NOT_APPLICABLE/UNAVAILABLE rather than a misleading zero success rate. Store all source policy/selection evidence. |
| Target hit rate | Finalized filled trades in F with positive exit execution attributed to their governed TP child / N. A mere later market touch does not count. Also group by actual TP/SL/manual exit reason without inferring counterfactual winners. |
| Time-to-target / MAE before target | For a trade with proven TP-child execution, first such execution minus first Entry execution; compute open-interval MAE only through that TP event using §6.5. No TP event → not observed/censored, not a fabricated future target time. |
| Previous-day versus 1h target behavior | Group the same observed result, excursion, hit/time and selection statistics by actual selected target source type. No alternate unselected target is simulated. |
| Minimum/maximum Entry/TP/Stop distance sensitivity | Compare the already specified baseline/variant arms, not a new within-run target generator or automatic parameter sweep. |
| Submission acceptance/rejection/uncertainty; partial-fill, cancel, race, TP/SL/manual-close frequencies | Preserve event-level counts. Attempt-level frequencies use distinct dispatched Entry attempts with applicable outcome coverage; close frequencies use F. Partial-fill frequency uses attempts whose historical Entry ledger ever satisfied 0<F<Q while remainder was live. Fill ratio per attempt is canonical cumulative filled quantity/intended quantity at E; quantity coverage required. |
| Set/manual/zero-fill/remainder cancel reasons | Counts of distinct cancel intents and affected Entry attempts with source reasons; report both units separately. Cancel-outcome frequencies use intents with resolved terminal outcomes, with unresolved intents separately counted. |
| Reconciliation/restart corrections/duplicates/out-of-order/protection failures/manual intervention | Count distinct evidenced occurrences by source event/incident identity. Report observation duration and raw counts; where a rate is desired, count divided by actual covered run hours. Reconciliation duration is terminal time minus start; unresolved intervals are censored. |
| Portfolio grants/blocks, cooldown/Daily Loss/global cap/coin cap gate frequencies, capacity misses | Count each canonical Capital-and-Limits or submission-hold gate evaluation at its own stage. Numerator = evaluations with that reason; denominator = completed applicable evaluations at that same stage. One evaluation may have multiple diagnostic failures; preserve multi-label membership, never sum reason rates as mutually exclusive. Capacity-miss means a factual capacity-blocked opportunity, not estimated missed P/L. |
| Slot, capital and coin-allocation utilization | Retain time-stamped canonical committed counts/amounts and available limits. Report-only instantaneous ratios use committed/limit for the same snapshot and unit; denominator zero → UNAVAILABLE. Optional run average is the integral of these piecewise-constant ratios over covered elapsed time divided by covered duration; report gaps. No ratio enters a trading limit. |
| Holds/reservations/grants and released rounding deltas | Preserve source IDs, creation/consumption/closure times and exact source amounts. Duration is matching end−start; not-yet-ended items are right-censored at E. Never claim release until canonical receipt/closure evidence establishes it. |
| Gross result, fees/rebates, funding and net result | Preserve canonical financial component records and signed amounts; group each component once by result population/currency with source conservation. Net headline comes from canonical net result, not a new reallocation. |

All mandatory raw fields/chronology remain exportable even when a summary statistic is unavailable. No absent shadow lifecycle blocks Research V1.

Source: RV1-DECISIONS §§7–10, 15; `methodology/POSITION_RULES.md` Part II §51, L3220–3244; Part IV §48, L5465–5486; `methodology/PORTFOLIO_RULES.md` Part VIII §63, L1741–1775; `methodology/ORDER_LIFECYCLE.md` §43, L1774–1830.

## 8. Scopes, comparison columns, and human authority

Required scopes are `OVERALL`, `BY_SEGMENT`, `BY_COIN`, `BY_DIRECTION`. Optional explicit joint filters may be retained, but they are not additional hypotheses. Segments are exactly MAJORS, HIGH_VOLATILITY_HIGH_BETA and DIVERSIFIERS. Direction is immutable factual LONG or SHORT, not inferred from positive/negative P/L. An unavailable or absent direction is not a zero-performance cohort.

Every scope supports this exact column ordering:

`ACTIVE | DEMO_7D | BACKTEST_7D | BACKTEST_30D | BACKTEST_90D`

A comparison cell references **one explicitly selected run/report revision** for a hypothesis arm (or a bound Active observation). Multiple runs of a type remain separate records; neither “latest,” “best” nor an average is silently selected. Baseline and variant each retain their own run references. Interactions have 00/10/01/11 rows/reference groups. Missing columns show NOT_RUN/UNAVAILABLE, not zero values.

ACTIVE is a contextual, read-only observation, not an assumed existing configuration/version and not the experiment's baseline. Bind its exact observed configuration(s), account, covered interval, capital, universe, source/report profile and report evidence. Mixed Active versions require explicit splits/annotations. To compare Active with DEMO_7D quantitatively, select a seven-day observation interval and disclose any nonalignment/carry-in/capital/universe difference. The different historical durations are not equal-exposure monetary estimates. No growth ranking or per-day normalization is silently invented. Ratios and means are recomputed from underlying group populations, not averaged from displayed coin/segment values.

`DEC-R-001` is retained as the research decision-reference identity, but its V1 revision is **HUMAN_REVIEW_ONLY**. It supplies factual comparison context and quality warnings; it emits no automated KEEP, REJECT, NEED_MORE_DATA, winner, continuation mandate, Demo launch or Active promotion. Users decide continuation, promotion/use, new hypotheses and which comparisons matter. A user decision stores actor/time/run/report/configuration references and optional rationale; it cannot rewrite run evidence.

For two-arm designs, show the same eleven reporting statistics and applicable diagnostics with matched window/input provenance. For interactions, expose 10 versus 00 and 11 versus 01, plus complementary controlled pairs, without collapsing the study to 00 versus 11. Evidence inspection is descriptive, not a claim of causal identification, adequate sample size or statistical significance. Common markets, overlapping windows, Portfolio path effects and observational Demo differences remain visible.

Source: RV1-DECISIONS §§4–6, 12–16; existing 30 baseline/variant definitions and pair-overlap register.

## 9. Complete Research-record Evidence / Log Export

### 9.1 Root, reachability and immutable retention

`export_root = RESEARCH_RECORD`, identified by `research_id + research_record_revision + export_cutoff`. Traverse every reachable revision, not just one selected run, the latest successful run, or one report. Export all available hypothesis/configuration revisions and arms, symbol-specific Set bindings, all four run types, reruns, failed/unavailable attempts, ordinary later finalization/report revisions, source manifests and content, metric/Trigger/Set/Position/Portfolio/Lifecycle evidence, fills/protection/exits/finance, reporting populations, Compare revisions, referenced ACTIVE snapshots, endpoint/open-state and ambiguity/frontier records, and human decisions/provenance.

R-023 is a stable register ID with distinct immutable revisions. Its old C-050 allocation study is invalid for new launch but its historical evidence remains exportable. Its new C-036 minimum-Stop study must not inherit or pool old run results. Preserve old `PR-R-101…109` and the old execution/report profile as historical configuration bodies with hashes. A correction, rerun, source improvement or report revision appends evidence rather than overwriting a predecessor. R3 additionally keys R-022/R2=C-049 versus R-022/R3=C-012 and R-026/R2=C-053 versus R-026/R3=C-015. No historical cap or minimum run is relabeled/pooled with a new predicate study. Both old definitions remain historical/conditional; every run resolves research_id + research_revision before arm/configuration lookup.

### 9.2 Minimum retained evidence families

| Family | Mandatory content |
|---|---|
| Research identity/revisions | Research ID, record revision, candidate provenance, primary question/axis, replacement lineage, all arm IDs/configuration bodies/digests and applicability rules |
| Universe/configuration | Ten-symbol ordered member vector, segments, 10% each /100% total, Set map per arm/symbol, Position and Portfolio IDs/versions, profile/source/instrument revisions |
| Source manifests | Canonical selectors, actual datasets/granularities, instrument and price bases, ranges/pages/finality/availability, raw IDs/bytes or durable content-addressed objects, warm-up ancestry and coverage |
| Metric/Trigger | Values and availability, canonical metric instance/input/version/cutoff/precision; comparator/freshness/event and reset evidence; no invented BTC classifier diagnostics |
| Set | Arming/formation/expiry/reset/re-arm states, per-step evidence, current/maintained conditions, MATCHED lineage, direction branch and all contexts, frozen pending condition and monitor/cancel evidence |
| Position | APPROVE/REJECT and reasons, canonical construction candidates/values/geometry, Entry/Stop/TP, exact size/economics, calibration bindings, Order Spec and final construction lineage |
| Portfolio | Health, Coins status, grants/holds/authorization outcomes, fixed allocation vector, global/coin free and committed capital, tranche slots, cooldown accepted_at and Daily Loss/accounting-day evidence |
| Lifecycle/execution | Submit/acceptance facts and model/native provenance, order/protection confirmations, fills including quantity and cumulative Entry basis, close reason/authority, cleanup and endpoint exposure/children/remainder state |
| Finance | Canonical final realized result and finality proof; fees, rebates, funding/other costs, coverage/pagination/revisions, source allocation and economic chronology; no premature FINAL |
| Reporting | All eleven statistics and supplementary reports, exact finalized/dispatch/diagnostic populations and exclusions, raw MAE/MFE observations, as-of/endpoint/frontier distinctions, zero/unavailable/nonapplicable/infinite cases |
| Compare/ACTIVE | Every selected report/run/arm/revision and controlled-input fingerprint, exact column/scope key, incompatible/incomplete reason, read-only factual ACTIVE snapshots; no invented Active config |
| Human provenance | Launch/continuation/comparison/decision actor, timestamp, referenced evidence, reason; no automatic disposition, Demo launch or promotion |
| Export manifest | Root/cutoff/revision, complete object inventory/counts/ranges/digests, dependency closure, source companions, omissions/redactions and integrity results |

### 9.3 Intrabar and frontier metadata — research namespace only

| Object | Required fields / behavior |
|---|---|
| SourceResolutionManifest | source_resolution_manifest_id/revision/digest; actual available granularities and ranges; parent/child refinement map; price_basis; source ordering domain; coverage/finality; common comparison identity |
| ExecutionResolutionRecord | execution_resolution_id; status FACTUAL_ORDER_RESOLVED / MODEL_ORDER_INVARIANT / UNRESOLVED_INTRABAR; symbol, eligible orders/quantities/protection state; touched levels; source references and causal constraints; unique-case proof or reason unresolved |
| ModelChronology | factual time/domain/sequence when supported; otherwise uncertainty interval, MODEL_CELL_END and causal ordinals only under §4.4 safeguards; separate knowledge/ingestion/report times |
| AmbiguityRecord | unresolved cell/range, competing event relations, affected positions/symbols and close/cancel authorities, possible differing quantities/fees/funding/day/capacity outcomes, refinement exhaustion reason |
| PortfolioDependencyFrontier | last_shared_portfolio_checkpoint_id/digest; committed canonical identities; frontier interval; affected shared-capital/slot/grant/Daily Loss dependencies; dependent_suffix_stop; no canonical release generated |
| ReportCompleteness | requested interval/end; actual unambiguous frontier; FULL_WINDOW / PREFIX_ONLY / INCOMPLETE population; per-stat diagnostic completeness; per-arm comparison eligibility and reasons; exact included/excluded population IDs |

These objects attach by research envelopes. They cannot be sent as new canonical order states, financial flags, trading parameters or wire fields. Reading any RR-V1 statistic/completeness value from Set/Position/Portfolio is prohibited.

### 9.4 Export closure and reproducibility

COPY / EXPORT COMPLETE RESEARCH LOG means a storable reusable dataset, not screen design or an implementation. Include source bytes or complete content-addressed companion objects available to the authorized analyst. Expired/private URLs without retrievable immutable content do not establish complete export. Preserve configuration bodies, numeric strings, original IDs, accepted revisions, report membership and the deterministic model rules, not just screenshots or current summaries.

Every available run/revision is enumerated exactly once under its own identities. Nested windows, reruns and report revisions are not concatenated into a single performance sample. Missing mandatory material yields `export_completeness=INCOMPLETE` and an explicit gap manifest. Include hashes and object counts for integrity. No API keys, tokens or private credentials are exported; access references are nonsecret/authorized, with explicit redaction metadata. User-authorized deletion and retention obligations remain visible; retention may not silently destroy the evidence needed to reproduce an available report.

Source: focused council §7.3 and current correction §§2.6, 10–11, 20–21; canonical evidence ownership in frozen `SYSTEM_PROTOCOLS.md` P6–P8, `IDENTIFIER_LINEAGE.md`, and native/business contracts. No backend, database or export implementation is made here.

## 10. Optional future Shadow Analysis

`SHADOW_ANALYSIS = OPTIONAL_FUTURE_LAYER`. V1 does not create post-Stop/post-TP virtual exposure, extend MAE/MFE beyond actual exit, or estimate alternative trade outcomes using an arbitrary horizon. Alternative Stop/TP questions are tested through the existing explicit Position baseline/variant configurations. Retained full-interval market/evidence logs may support future offline human/AI inspection and new hypothesis design. Any future shadow layer needs a separately versioned research definition; it cannot retrospectively relabel V1 diagnostics or modify canonical trading results.

Source: RV1-DECISIONS §§9–10, 15.

## 11. Focused closure and operational preflight

B-01/B-02 and all four R2 FCR findings remain closed. R3 mechanically applies C-012 at R-022 and C-015 at R-026, preserving R-023/C-036, the other28 and all accepted execution/reporting semantics. Exactly 30 specifications are final; no run, UI, exchange adapter, source availability or native conformance is certified. The focused council review records the actual document/parameter/reference checks and logical acceptance cases.

All mandatory run inputs remain typed launch prerequisites. A valid hypothesis can have no observed matches, failed admission, an unavailable source or an unresolved historical run; these are not invented zeros or automatic strategy rejections. The 10% allocation and non-fabricated chronology rules are not relaxed to force 30 completed results. No queue-position reconstruction or shadow lifecycle is required.

### 11.1 Immutable identity / precedence

This file's operative document version is RESEARCH_V1_FOCUSED_CORRECTION_R3. The unchanged R2 execution/reporting semantic pins are separately supported as stated above; they never alias research revisions. The full R2 profile remains in ../provenance/r2_operative/. Its original R1 bytes are preserved in `../provenance/TRIGGERTRADE_RESEARCH_V1_FINALIZED.zip`. The focused council is preserved byte-for-byte in `../provenance/RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md`. References to old choices in those provenance objects are historical, not operative fallbacks. Canonical methodology always controls trading ownership/math; the current product/council rules govern this research-only execution/report overlay.

The profile/configuration objects in the normalized model carry immutable revision/digest bindings. A run joins to that exact revision, never to an unversioned 'latest'. Model body digests use UTF-8 compact JSON, sorted keys, ensure_ascii=false and exact decimal strings; the content_sha256 field itself is excluded. This is research identity metadata, not a new trading calculation.

### 11.2 Source-reference resolution for council-derived sections

Sections 4.2–4.5 and 4.7 apply the approved council definitions. Their compact source IDs S00–S15 and R08/R09 refer to the immutable focused council §1.3 source register. S09 is frozen MARKET_DATA_REQUEST §§2–6 L8–46; S10 is ORDER_LIFECYCLE §§4–5 L307–407; S11 is ORDER_LIFECYCLE §7 L522–585 and §§16–22 L903–1016; S12 is ORDER_LIFECYCLE §§32–34 L1208–1377; S13 is SYSTEM_PROTOCOLS P6–P8 L114–220; S14 is PORTFOLIO_RULES §§11–27 L484–980. R08/R09 are the predecessor profile, whose approximation assumptions remain only where explicitly preserved here. The old intrabar-path and BTC restrictions are superseded, not silently reused.
