# TriggerTrade — Research Hypothesis Design Space — Corrected R3

**OPERATIVE_R3 — `RESEARCH_V1_FOCUSED_CORRECTION_R3`. Status: APPROVED — specification-level package correction only.**

Exactly the two approved assignments are applied: **R-022 = C-012, BTC contextual agreement (AX-08)**; **R-026 = C-015, Local-momentum agreement (AX-11)**. The other 28 questions, treatments, Set mappings, Position/Portfolio configurations and BTC applicability are unchanged. R-023 remains C-036; R-010 retains its unchanged definition and conditional first-wave economic-audit qualification.

Current counts: **30 valid hypotheses; 13 Set / 11 Position / 4 Portfolio / 2 cross-layer**. Sixty candidates remain. Ten fixed 10% allocations total exactly 100%; R-006 BTC remains NOT_APPLICABLE without redistribution. The frozen v1.2.15 archive SHA-256 is `3b38c09c6f52daa77d7cc4257a3c420b21d76ac10d039dd708dd205af963b326` and its bytes are unchanged.

Package/research identity is R3. Existing immutable execution-semantic pins (`profile_revision=RESEARCH_V1_FOCUSED_CORRECTION_R2`), `REPORT-R-V1-R2`, `EVIDENCE-R-V1-R2`, and `DEC-R-001`/R2 deliberately remain unchanged contracts. They do **not** select an R2 hypothesis: launch always resolves the R3 research revision separately. Existing Set/Trigger/configuration revisions and digests are not relabeled. The current profile document explains this compatibility explicitly. No old/new hypothesis runs are pooled.

Authority: frozen methodology; unchanged R2 package; focused BTC/intrabar council; R2 economic and pairwise audits; approved replacement selection and pairwise review; current mechanical-correction instruction. Only `operative/` is current configuration. `provenance/` is HISTORICAL_PROVENANCE. No Backtest, Demo, native API, data availability, statistical independence or profitability is certified.

## 1. Source boundary and current authority

The unchanged v1.2.15 archive, copied to ../provenance/, is canonical for trading semantics. The R2 operative files and all five council/economic/replacement review files are preserved unchanged. The approved selection fixes C-012 and C-015; no candidate generation, economic reranking or source recertification is performed here. Inventory/source sections retain their broader design-space meaning; current use/selection is governed by §12 and the current register, not by historical candidate mentions.

The original R2 source manifest and formula inventory remain in provenance. All source document/section/line references here are archive-relative, not repository paths. Existing metric counts are output/state inventory counts, not numbers of newly invented indicators. Validation records input and output hashes.

## 2. Construction hierarchy and counting convention

```text
Existing canonical metrics/states -> research predicates -> versioned Set
-> pinned Portfolio + Position configurations -> one research question
-> manually requested Backtest/Demo -> canonical outputs + research-only reporting -> human decision
```

The inventory contains **162 qualified canonical calculation outputs, intermediate observations, diagnostics and states**, of which **37** are used as the direct-trigger construction domain. This is not a count of new or distinct mathematical formulas. Work/wire representations and stage-specific states are deliberately separate rows. Source-local dotted names identify nested diagnostics, not new API fields. Optional/context names remain separately constrained in §5. Mandatory report statistics now have Research V1 definitions, kept outside this unchanged canonical metric inventory.

### Ownership and numeric invariants

Set owns metric work state, canonical direction and frozen context. Position consumes the received frozen geometry without querying markets; Portfolio owns capital/slots and grants; Lifecycle owns factual execution/finality. Set uses exact inner calculations with Q36 HALF_EVEN named work outputs and Q18 required handoff exports. Position/Portfolio monetary calculations preserve exact arithmetic and only apply the source output-class quantizer: quantity grid floor, Qcapital=10^-12 capacity floor/liability ceiling, Qratio=10^-18 report floor. Reporting round-off cannot decide a gate. Analytical normalization uses completed UTC days; accounting days use Asia/Jerusalem civil midnights. They are different clocks.

`methodology/SET.md` Part II §§34A–37, lines 3155–3435; `methodology/SET.md` Part III §43.1, lines 4769–4801; `methodology/POSITION_RULES.md` Part I §§17–22A, lines 576–908; `schemas/NUMERIC_POLICY.md` §§1–7, lines 8–94; `schemas/SET_NUMERIC_POLICY.md` §§1–7, lines 19–110; `methodology/PORTFOLIO_RULES.md` Part I §§2–4, lines 98–247; `methodology/PORTFOLIO_RULES.md` Part II §23, lines 776–872; `methodology/ORDER_LIFECYCLE.md` §§33–34, lines 1343–1377

## 3. Existing metric and state inventory

**Scope qualification added by the focused correction:** the inventory and formula semantics are unchanged. F-005 references in canonical-use/dependency notes describe its governed non-BTC scope, not a requirement to run that classifier on every generic Set. Actual BTC dependencies are resolved per symbol by `WEB_RESEARCH_CONFIGURATION_MODEL.md` §§4–5, 8–9. Existing RETURN(asset,5m) is bound to BTC with strict comparisons; no new metric is added. F-004 aggregate, relative normalization, F-005 gates/vetoes/diagnostics are not fabricated for BTC.


### 3.1. F-001 trigger_result

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-001 trigger_result
FAMILY: displacement
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
OWNER: Set
INPUTS: Current and immediately preceding completed 1m KLINES.close; pinned positive theta_move_pct
OUTPUT_TYPE: tri-state
UNIT: none
TIMEFRAME: 1m; current completed slot only
DIRECTION_SENSITIVITY: No LONG/SHORT authority
AVAILABILITY_STATES: TRUE / FALSE / UNAVAILABLE
PRECISION_OR_NUMERIC_POLICY: Signed displacement Q36 before exact inclusive absolute-magnitude comparison
CURRENT_CANONICAL_USE: Canonical magnitude predicate; CURRENT_STATE only
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8A
```

### 3.2. move_pct_work

```yaml
METRIC_ID_OR_CANONICAL_NAME: move_pct_work
FAMILY: displacement
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
OWNER: Set
INPUTS: Same two completed 1m endpoint closes
OUTPUT_TYPE: signed decimal
UNIT: percent; 1 means 1%
TIMEFRAME: 1m
DIRECTION_SENSITIVITY: UP/DOWN sign; not direction
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-001 signed endpoint displacement
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES:
- F-001.move_pct_work
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8A
```

### 3.3. F-001 sign_evidence

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-001 sign_evidence
FAMILY: displacement
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
OWNER: Set
INPUTS: move_pct_work
OUTPUT_TYPE: enum UP / DOWN / FLAT
UNIT: none
TIMEFRAME: current completed 1m slot
DIRECTION_SENSITIVITY: Sign only; never LONG/SHORT
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: Retained F-001 evidence
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- move_pct_work
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8A
```

### 3.4. F-002 trigger_result

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-002 trigger_result
FAMILY: participation
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
OWNER: Set
INPUTS: Current and 60 immediately preceding consecutive completed 1m base-volume candles
OUTPUT_TYPE: tri-state
UNIT: none
TIMEFRAME: 1m current completed slot
DIRECTION_SENSITIVITY: Direction-neutral
AVAILABILITY_STATES: TRUE / FALSE / UNAVAILABLE
PRECISION_OR_NUMERIC_POLICY: Exact rational/decimal comparisons; fixed boundaries; no alternative threshold
CURRENT_CANONICAL_USE: Fixed R>=2 AND P>=90; not absolute liquidity
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8B
```

### 3.5. F-002.M

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-002.M
FAMILY: participation-local
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
OWNER: Set
INPUTS: F-002 current volume and 60-member preceding base-volume population
OUTPUT_TYPE: decimal
UNIT: base-coin volume
TIMEFRAME: 1m
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact median / count / rational; no intermediate rounding
CURRENT_CANONICAL_USE: Trigger-local intermediate; explicitly not exported Set metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8B
```

### 3.6. F-002.K

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-002.K
FAMILY: participation-local
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
OWNER: Set
INPUTS: F-002 current volume and 60-member preceding base-volume population
OUTPUT_TYPE: integer 0..60
UNIT: count
TIMEFRAME: 1m
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact median / count / rational; no intermediate rounding
CURRENT_CANONICAL_USE: Trigger-local intermediate; explicitly not exported Set metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8B
```

### 3.7. F-002.R

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-002.R
FAMILY: participation-local
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
OWNER: Set
INPUTS: F-002 current volume and 60-member preceding base-volume population
OUTPUT_TYPE: exact ratio
UNIT: dimensionless
TIMEFRAME: 1m
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact median / count / rational; no intermediate rounding
CURRENT_CANONICAL_USE: Trigger-local intermediate; explicitly not exported Set metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8B
```

### 3.8. F-002.P

```yaml
METRIC_ID_OR_CANONICAL_NAME: F-002.P
FAMILY: participation-local
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
OWNER: Set
INPUTS: F-002 current volume and 60-member preceding base-volume population
OUTPUT_TYPE: exact ratio
UNIT: percent
TIMEFRAME: 1m
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact median / count / rational; no intermediate rounding
CURRENT_CANONICAL_USE: Trigger-local intermediate; explicitly not exported Set metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §8B
```

### 3.9. TR_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: TR_15m
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry
OUTPUT_TYPE: nonnegative decimal
UNIT: price
TIMEFRAME: 15m, Wilder(14) for ATR
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: Work zero may be valid; percentage unavailable at zero close; both required wire exports
  AVAILABLE and >0
PRECISION_OR_NUMERIC_POLICY: TR exact; ATR and ATR_PCT named work outputs Q36 HALF_EVEN; ATR_15m / ATR_PCT_15m
  Q18 exports; zero/rounded-to-zero exports ineligible
CURRENT_CANONICAL_USE: F-003 work state / positive required handoff export
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§13–15
- §§1–7
```

### 3.10. ATR_work

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR_work
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry
OUTPUT_TYPE: nonnegative decimal
UNIT: price
TIMEFRAME: 15m, Wilder(14) for ATR
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: Work zero may be valid; percentage unavailable at zero close; both required wire exports
  AVAILABLE and >0
PRECISION_OR_NUMERIC_POLICY: TR exact; ATR and ATR_PCT named work outputs Q36 HALF_EVEN; ATR_15m / ATR_PCT_15m
  Q18 exports; zero/rounded-to-zero exports ineligible
CURRENT_CANONICAL_USE: F-003 work state / positive required handoff export
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§13–15
- §§1–7
```

### 3.11. ATR_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR_15m
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry
OUTPUT_TYPE: nonnegative decimal
UNIT: price
TIMEFRAME: 15m, Wilder(14) for ATR
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: Work zero may be valid; percentage unavailable at zero close; both required wire exports
  AVAILABLE and >0
PRECISION_OR_NUMERIC_POLICY: TR exact; ATR and ATR_PCT named work outputs Q36 HALF_EVEN; ATR_15m / ATR_PCT_15m
  Q18 exports; zero/rounded-to-zero exports ineligible
CURRENT_CANONICAL_USE: F-003 work state / positive required handoff export
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§13–15
- §§1–7
```

### 3.12. ATR_PCT_work

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR_PCT_work
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry
OUTPUT_TYPE: nonnegative decimal
UNIT: percent
TIMEFRAME: 15m, Wilder(14) for ATR
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: Work zero may be valid; percentage unavailable at zero close; both required wire exports
  AVAILABLE and >0
PRECISION_OR_NUMERIC_POLICY: TR exact; ATR and ATR_PCT named work outputs Q36 HALF_EVEN; ATR_15m / ATR_PCT_15m
  Q18 exports; zero/rounded-to-zero exports ineligible
CURRENT_CANONICAL_USE: F-003 work state / positive required handoff export
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§13–15
- §§1–7
```

### 3.13. ATR_PCT_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR_PCT_15m
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry
OUTPUT_TYPE: nonnegative decimal
UNIT: percent
TIMEFRAME: 15m, Wilder(14) for ATR
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: Work zero may be valid; percentage unavailable at zero close; both required wire exports
  AVAILABLE and >0
PRECISION_OR_NUMERIC_POLICY: TR exact; ATR and ATR_PCT named work outputs Q36 HALF_EVEN; ATR_15m / ATR_PCT_15m
  Q18 exports; zero/rounded-to-zero exports ineligible
CURRENT_CANONICAL_USE: F-003 work state / positive required handoff export
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§13–15
- §§1–7
```

### 3.14. ATR percentile

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR percentile
FAMILY: volatility
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
OWNER: Set
INPUTS: Current ATR_PCT and eligible completed same-symbol 15m ATR_PCT reference population
OUTPUT_TYPE: numeric 0..100
UNIT: percentile rank
TIMEFRAME: 30 completed UTC days; minimum 14 eligible complete days
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 volatility gate; Set-local, not Position wire dependency
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- ATR_PCT_work
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§13–15
- Part II §§3–6
```

### 3.15. SWING_HIGH_15M

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_HIGH_15M
FAMILY: structure-reference
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed high/low candles; fixed left=2/right=2 pivot; tick metadata
OUTPUT_TYPE: governed level object
UNIT: price and factual timestamps
TIMEFRAME: 15m
DIRECTION_SENSITIVITY: direction-neutral producer reference
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source prices; source pivot/tie rules; availability at confirmation, not pivot
  time
CURRENT_CANONICAL_USE: Reference geometry; two-right-bar confirmation required
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
- Part III §§12–22
```

### 3.16. SWING_LOW_15M

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_LOW_15M
FAMILY: structure-reference
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed high/low candles; fixed left=2/right=2 pivot; tick metadata
OUTPUT_TYPE: governed level object
UNIT: price and factual timestamps
TIMEFRAME: 15m
DIRECTION_SENSITIVITY: direction-neutral producer reference
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source prices; source pivot/tie rules; availability at confirmation, not pivot
  time
CURRENT_CANONICAL_USE: Reference geometry; two-right-bar confirmation required
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
- Part III §§12–22
```

### 3.17. SWING_HIGH_1H

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_HIGH_1H
FAMILY: structure-reference
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed high/low candles; fixed left=2/right=2 pivot; tick metadata
OUTPUT_TYPE: governed level object
UNIT: price and factual timestamps
TIMEFRAME: 1h
DIRECTION_SENSITIVITY: direction-neutral producer reference
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source prices; source pivot/tie rules; availability at confirmation, not pivot
  time
CURRENT_CANONICAL_USE: Reference geometry; two-right-bar confirmation required
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
- Part III §§12–22
```

### 3.18. SWING_LOW_1H

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_LOW_1H
FAMILY: structure-reference
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed high/low candles; fixed left=2/right=2 pivot; tick metadata
OUTPUT_TYPE: governed level object
UNIT: price and factual timestamps
TIMEFRAME: 1h
DIRECTION_SENSITIVITY: direction-neutral producer reference
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source prices; source pivot/tie rules; availability at confirmation, not pivot
  time
CURRENT_CANONICAL_USE: Reference geometry; two-right-bar confirmation required
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
- Part III §§12–22
```

### 3.19. SWING_SEQUENCE_STATE(asset,1h)

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_SEQUENCE_STATE(asset,1h)
FAMILY: structure
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
OWNER: Set
INPUTS: Latest two confirmed highs and lows for named scope; one-tick equality tolerance
OUTPUT_TYPE: enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE
UNIT: none
TIMEFRAME: 1h
DIRECTION_SENSITIVITY: categorical trend; not final direction
AVAILABILITY_STATES: BULLISH / BEARISH / AMBIGUOUS; UNAVAILABLE if required pivots absent
PRECISION_OR_NUMERIC_POLICY: Exact comparisons with one-tick tolerance; no numeric ordering of enums
CURRENT_CANONICAL_USE: F-004 structure factor
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
```

### 3.20. SWING_SEQUENCE_STATE(asset,15m)

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_SEQUENCE_STATE(asset,15m)
FAMILY: structure
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
OWNER: Set
INPUTS: Latest two confirmed highs and lows for named scope; one-tick equality tolerance
OUTPUT_TYPE: enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE
UNIT: none
TIMEFRAME: 15m
DIRECTION_SENSITIVITY: categorical trend; not final direction
AVAILABILITY_STATES: BULLISH / BEARISH / AMBIGUOUS; UNAVAILABLE if required pivots absent
PRECISION_OR_NUMERIC_POLICY: Exact comparisons with one-tick tolerance; no numeric ordering of enums
CURRENT_CANONICAL_USE: F-004 structure factor
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
```

### 3.21. SWING_SEQUENCE_STATE(BTC,1h)

```yaml
METRIC_ID_OR_CANONICAL_NAME: SWING_SEQUENCE_STATE(BTC,1h)
FAMILY: structure
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
OWNER: Set
INPUTS: Latest two confirmed highs and lows for named scope; one-tick equality tolerance
OUTPUT_TYPE: enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE
UNIT: none
TIMEFRAME: 1h
DIRECTION_SENSITIVITY: categorical trend; not final direction
AVAILABILITY_STATES: BULLISH / BEARISH / AMBIGUOUS; UNAVAILABLE if required pivots absent
PRECISION_OR_NUMERIC_POLICY: Exact comparisons with one-tick tolerance; no numeric ordering of enums
CURRENT_CANONICAL_USE: F-004 structure factor
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§9–10
```

### 3.22. RETURN(asset,15m)

```yaml
METRIC_ID_OR_CANONICAL_NAME: RETURN(asset,15m)
FAMILY: return
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
OWNER: Set
INPUTS: Aligned completed-bar closes for named horizon
OUTPUT_TYPE: signed decimal
UNIT: fractional return
TIMEFRAME: 15m
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: Existing RETURN(H) input to momentum/relative/BTC calculations
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§3–6
- Part II §§16–18
- Part II §§19–20
- Part II §§24–27
```

### 3.23. RETURN(BTC,15m)

```yaml
METRIC_ID_OR_CANONICAL_NAME: RETURN(BTC,15m)
FAMILY: return
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
OWNER: Set
INPUTS: Aligned completed-bar closes for named horizon
OUTPUT_TYPE: signed decimal
UNIT: fractional return
TIMEFRAME: 15m
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: Existing RETURN(H) input to momentum/relative/BTC calculations
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§3–6
- Part II §§16–18
- Part II §§19–20
- Part II §§24–27
```

### 3.24. RETURN(asset,5m)

```yaml
METRIC_ID_OR_CANONICAL_NAME: RETURN(asset,5m)
FAMILY: return
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
OWNER: Set
INPUTS: Aligned completed-bar closes for named horizon
OUTPUT_TYPE: signed decimal
UNIT: fractional return
TIMEFRAME: 5m
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: Existing RETURN(H) input to momentum/relative/BTC calculations
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§3–6
- Part II §§16–18
- Part II §§19–20
- Part II §§24–27
```

### 3.25. DE

```yaml
METRIC_ID_OR_CANONICAL_NAME: DE
FAMILY: efficiency
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
OWNER: Set
INPUTS: 15m closes, fixed N=8; DE_STRENGTH consumes DE
OUTPUT_TYPE: numeric 0..1
UNIT: dimensionless
TIMEFRAME: 15m over 8 changes
DIRECTION_SENSITIVITY: unsigned efficiency
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; DE denominator zero maps to canonical 0
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 DE gate / momentum modifier
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES:
- DIRECTIONAL_EFFICIENCY(15m,8)
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§11–12
```

### 3.26. DE_STRENGTH

```yaml
METRIC_ID_OR_CANONICAL_NAME: DE_STRENGTH
FAMILY: efficiency
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
OWNER: Set
INPUTS: 15m closes, fixed N=8; DE_STRENGTH consumes DE
OUTPUT_TYPE: numeric 0..1
UNIT: dimensionless
TIMEFRAME: 15m over 8 changes
DIRECTION_SENSITIVITY: unsigned efficiency
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; DE denominator zero maps to canonical 0
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 DE gate / momentum modifier
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- DE
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§11–12
```

### 3.27. VNM_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: VNM_15m
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: dimensionless
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- RETURN(asset,15m)
- ATR_PCT_work
ALIASES:
- VOLATILITY_NORMALIZED_MOMENTUM(horizon=15m, volatility_input_timeframe=15m, window=14, Wilder)
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.28. momentum_z

```yaml
METRIC_ID_OR_CANONICAL_NAME: momentum_z
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: z-score
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- VNM_15m
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.29. MOMENTUM_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: MOMENTUM_SCORE
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: bounded -1..1
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- momentum_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.30. MOMENTUM_EFFECTIVE

```yaml
METRIC_ID_OR_CANONICAL_NAME: MOMENTUM_EFFECTIVE
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: bounded -1..1
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- MOMENTUM_SCORE
- DE_STRENGTH
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.31. A_t_5m

```yaml
METRIC_ID_OR_CANONICAL_NAME: A_t_5m
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: price
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.32. ATR_PCT_5m

```yaml
METRIC_ID_OR_CANONICAL_NAME: ATR_PCT_5m
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: percent
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- A_t_5m
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.33. VNM_5m

```yaml
METRIC_ID_OR_CANONICAL_NAME: VNM_5m
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: dimensionless
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- RETURN(asset,5m)
- ATR_PCT_5m
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.34. VNM_5m_z

```yaml
METRIC_ID_OR_CANONICAL_NAME: VNM_5m_z
FAMILY: momentum
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
OWNER: Set
INPUTS: Governed named dependencies; separate 5m ATR ancestry for local instance
OUTPUT_TYPE: decimal
UNIT: z-score
TIMEFRAME: 5m local or 15m primary as named; z uses completed UTC-day population
DIRECTION_SENSITIVITY: signed except volatility denominator
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 momentum factor or local veto input
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- VNM_5m
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- schemas/SET_NUMERIC_POLICY.md
SOURCE_SECTION:
- Part II §§16–18
- Part II §§3–6
- §§1–7
```

### 3.35. RELATIVE_RETURN_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: RELATIVE_RETURN_15m
FAMILY: relative
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
OWNER: Set
INPUTS: Aligned asset/BTC completed 15m returns and canonical normalization
OUTPUT_TYPE: signed decimal
UNIT: fractional return / z / bounded score, respectively
TIMEFRAME: 15m; z population 30/14 completed UTC days
DIRECTION_SENSITIVITY: signed relative to BTC
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 relative factor and contradiction veto
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- RETURN(asset,15m)
- RETURN(BTC,15m)
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§19–20
- Part II §§3–6
```

### 3.36. relative_return_z

```yaml
METRIC_ID_OR_CANONICAL_NAME: relative_return_z
FAMILY: relative
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
OWNER: Set
INPUTS: Aligned asset/BTC completed 15m returns and canonical normalization
OUTPUT_TYPE: signed decimal
UNIT: fractional return / z / bounded score, respectively
TIMEFRAME: 15m; z population 30/14 completed UTC days
DIRECTION_SENSITIVITY: signed relative to BTC
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 relative factor and contradiction veto
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- RELATIVE_RETURN_15m
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§19–20
- Part II §§3–6
```

### 3.37. RELATIVE_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: RELATIVE_SCORE
FAMILY: relative
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
OWNER: Set
INPUTS: Aligned asset/BTC completed 15m returns and canonical normalization
OUTPUT_TYPE: signed decimal
UNIT: fractional return / z / bounded score, respectively
TIMEFRAME: 15m; z population 30/14 completed UTC days
DIRECTION_SENSITIVITY: signed relative to BTC
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 relative factor and contradiction veto
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- relative_return_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§19–20
- Part II §§3–6
```

### 3.38. AggBuyNotional

```yaml
METRIC_ID_OR_CANONICAL_NAME: AggBuyNotional
FAMILY: flow
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
OWNER: Set
INPUTS: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership
OUTPUT_TYPE: decimal
UNIT: quote notional
TIMEFRAME: completed 5m horizon
DIRECTION_SENSITIVITY: signed imbalance except positive side sums
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow; no canonical raw-flow veto is introduced
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- api-contracts/MARKET_DATA_REQUEST.md
SOURCE_SECTION:
- Part II §§21–23
- §§1–6
```

### 3.39. AggSellNotional

```yaml
METRIC_ID_OR_CANONICAL_NAME: AggSellNotional
FAMILY: flow
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
OWNER: Set
INPUTS: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership
OUTPUT_TYPE: decimal
UNIT: quote notional
TIMEFRAME: completed 5m horizon
DIRECTION_SENSITIVITY: signed imbalance except positive side sums
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow; no canonical raw-flow veto is introduced
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- api-contracts/MARKET_DATA_REQUEST.md
SOURCE_SECTION:
- Part II §§21–23
- §§1–6
```

### 3.40. AGGRESSIVE_VOLUME_DELTA_PCT

```yaml
METRIC_ID_OR_CANONICAL_NAME: AGGRESSIVE_VOLUME_DELTA_PCT
FAMILY: flow
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
OWNER: Set
INPUTS: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership
OUTPUT_TYPE: decimal
UNIT: percent
TIMEFRAME: completed 5m horizon
DIRECTION_SENSITIVITY: signed imbalance except positive side sums
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow; no canonical raw-flow veto is introduced
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- AggBuyNotional
- AggSellNotional
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- api-contracts/MARKET_DATA_REQUEST.md
SOURCE_SECTION:
- Part II §§21–23
- §§1–6
```

### 3.41. FLOW_RAW

```yaml
METRIC_ID_OR_CANONICAL_NAME: FLOW_RAW
FAMILY: flow
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
OWNER: Set
INPUTS: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership
OUTPUT_TYPE: decimal
UNIT: fraction
TIMEFRAME: completed 5m horizon
DIRECTION_SENSITIVITY: signed imbalance except positive side sums
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow; no canonical raw-flow veto is introduced
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- AGGRESSIVE_VOLUME_DELTA_PCT
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- api-contracts/MARKET_DATA_REQUEST.md
SOURCE_SECTION:
- Part II §§21–23
- §§1–6
```

### 3.42. FLOW_EFFECTIVE

```yaml
METRIC_ID_OR_CANONICAL_NAME: FLOW_EFFECTIVE
FAMILY: flow
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
OWNER: Set
INPUTS: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership
OUTPUT_TYPE: decimal
UNIT: bounded score
TIMEFRAME: completed 5m horizon
DIRECTION_SENSITIVITY: signed imbalance except positive side sums
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow; no canonical raw-flow veto is introduced
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- FLOW_RAW
- PARTICIPATION_STRENGTH
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- api-contracts/MARKET_DATA_REQUEST.md
SOURCE_SECTION:
- Part II §§21–23
- §§1–6
```

### 3.43. TOD_REL_TURNOVER

```yaml
METRIC_ID_OR_CANONICAL_NAME: TOD_REL_TURNOVER
FAMILY: activity
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
OWNER: Set
INPUTS: Current completed 5m quote turnover / exact median of strictly prior same-clock UTC buckets
OUTPUT_TYPE: nonnegative numeric
UNIT: ratio
TIMEFRAME: 5m same-clock, previous 30 UTC dates; minimum 14 eligible buckets
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: Activity hard gate and participation strength
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES: []
ALIASES:
- TIME_OF_DAY_RELATIVE_TURNOVER(5m)
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §8
- Part II §§21–23
```

### 3.44. PARTICIPATION_STRENGTH

```yaml
METRIC_ID_OR_CANONICAL_NAME: PARTICIPATION_STRENGTH
FAMILY: activity
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
OWNER: Set
INPUTS: TOD_REL_TURNOVER
OUTPUT_TYPE: numeric 0..1
UNIT: dimensionless
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: neutral
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004 flow modifier, not F-002 base-volume predicate
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- TOD_REL_TURNOVER
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§21–23
```

### 3.45. BTC_STRUCTURE_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_STRUCTURE_SCORE
FAMILY: btc
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- SWING_SEQUENCE_STATE(BTC,1h)
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.46. BTC_RETURN_Z

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_RETURN_Z
FAMILY: btc
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- RETURN(BTC,15m)
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.47. BTC_MOMENTUM_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_MOMENTUM_SCORE
FAMILY: btc
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- BTC_RETURN_Z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.48. BTC_CONTEXT_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_CONTEXT_SCORE
FAMILY: btc
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- BTC_STRUCTURE_SCORE
- BTC_MOMENTUM_SCORE
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.49. STRUCTURE_1H

```yaml
METRIC_ID_OR_CANONICAL_NAME: STRUCTURE_1H
FAMILY: direction-score
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- SWING_SEQUENCE_STATE(asset,1h)
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.50. STRUCTURE_15M

```yaml
METRIC_ID_OR_CANONICAL_NAME: STRUCTURE_15M
FAMILY: direction-score
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- SWING_SEQUENCE_STATE(asset,15m)
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.51. STRUCTURE_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: STRUCTURE_SCORE
FAMILY: direction-score
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- STRUCTURE_1H
- STRUCTURE_15M
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.52. DIRECTION_SCORE

```yaml
METRIC_ID_OR_CANONICAL_NAME: DIRECTION_SCORE
FAMILY: direction-score
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Named immutable formula dependencies
OUTPUT_TYPE: numeric
UNIT: z-score for BTC_RETURN_Z; otherwise bounded score
TIMEFRAME: Classifier completed-5m evaluation with completed 15m/1h inputs
DIRECTION_SENSITIVITY: signed
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: TT_SET_NUMERIC_V1; exact named calculation; Q36 named work output; no display-rounded
  gates
CURRENT_CANONICAL_USE: F-004; fixed source weights and transforms retained
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- STRUCTURE_SCORE
- MOMENTUM_EFFECTIVE
- RELATIVE_SCORE
- FLOW_EFFECTIVE
- BTC_CONTEXT_SCORE
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§24–27
- Part II §28
- Part II §§31–34
- Part II §§34A–37
```

### 3.53. BTC_VETO_LONG

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_VETO_LONG
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: BTC_CONTEXT_SCORE
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- BTC_CONTEXT_SCORE
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.54. BTC_VETO_SHORT

```yaml
METRIC_ID_OR_CANONICAL_NAME: BTC_VETO_SHORT
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: BTC_CONTEXT_SCORE
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- BTC_CONTEXT_SCORE
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.55. RELATIVE_VETO_LONG

```yaml
METRIC_ID_OR_CANONICAL_NAME: RELATIVE_VETO_LONG
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: relative_return_z
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- relative_return_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.56. RELATIVE_VETO_SHORT

```yaml
METRIC_ID_OR_CANONICAL_NAME: RELATIVE_VETO_SHORT
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: relative_return_z
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- relative_return_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.57. LOCAL_MOMENTUM_VETO_LONG

```yaml
METRIC_ID_OR_CANONICAL_NAME: LOCAL_MOMENTUM_VETO_LONG
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: VNM_5m_z
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- VNM_5m_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.58. LOCAL_MOMENTUM_VETO_SHORT

```yaml
METRIC_ID_OR_CANONICAL_NAME: LOCAL_MOMENTUM_VETO_SHORT
FAMILY: direction-veto
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
OWNER: Set
INPUTS: VNM_5m_z
OUTPUT_TYPE: Boolean with availability
UNIT: none
TIMEFRAME: completed 5m evaluation
DIRECTION_SENSITIVITY: side-specific; opposite veto never reverses a candidate
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact inclusive source comparison; no treating UNAVAILABLE as inactive
CURRENT_CANONICAL_USE: F-004 upstream predicates consumed by F-005
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES:
- VNM_5m_z
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part II §§24–27
- Part II §§19–20
- Part II §§16–18
```

### 3.59. classifier_direction

```yaml
METRIC_ID_OR_CANONICAL_NAME: classifier_direction
FAMILY: direction-state
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
OWNER: Set
INPUTS: All eleven required F-004 inputs, score, hard gates, both sides' veto evidence
OUTPUT_TYPE: enum LONG / SHORT / NONE
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: sole direction authority in F-005-governed scope
AVAILABILITY_STATES: LONG / SHORT / NONE plus required availability/rejection diagnostics; DATA_UNAVAILABLE is
  never a known-negative market condition
PRECISION_OR_NUMERIC_POLICY: F-005 exact thresholds and candidate-side vetoes; no numeric enum operations
CURRENT_CANONICAL_USE: Directional criterion before final Set match
TRIGGER_CONSTRUCTION_USABILITY: YES — existing Set-local predicate; F-005 retained for non-BTC, or explicit generic BTC branch under Part I §5 with the same canonical metric dependencies
DEPENDENCIES:
- DIRECTION_SCORE
- DE
- TOD_REL_TURNOVER
- ATR percentile
- VNM_5m_z
- BTC_VETO_LONG
- BTC_VETO_SHORT
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
- Part I §5
```

### 3.60. direction_classifier.gates.data_available.passed

```yaml
METRIC_ID_OR_CANONICAL_NAME: direction_classifier.gates.data_available.passed
FAMILY: direction-diagnostics
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Canonical classifier dependencies
OUTPUT_TYPE: Boolean / reason enum as named
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: side-filtered where applicable
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Boolean/enum; exact original gate semantics
CURRENT_CANONICAL_USE: Diagnostics / prerequisite evidence; not independent market factors
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
```

### 3.61. direction_classifier.gates.directional_efficiency.passed

```yaml
METRIC_ID_OR_CANONICAL_NAME: direction_classifier.gates.directional_efficiency.passed
FAMILY: direction-diagnostics
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Canonical classifier dependencies
OUTPUT_TYPE: Boolean / reason enum as named
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: side-filtered where applicable
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Boolean/enum; exact original gate semantics
CURRENT_CANONICAL_USE: Diagnostics / prerequisite evidence; not independent market factors
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
```

### 3.62. direction_classifier.gates.activity.passed

```yaml
METRIC_ID_OR_CANONICAL_NAME: direction_classifier.gates.activity.passed
FAMILY: direction-diagnostics
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Canonical classifier dependencies
OUTPUT_TYPE: Boolean / reason enum as named
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: side-filtered where applicable
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Boolean/enum; exact original gate semantics
CURRENT_CANONICAL_USE: Diagnostics / prerequisite evidence; not independent market factors
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
```

### 3.63. direction_classifier.gates.volatility.passed

```yaml
METRIC_ID_OR_CANONICAL_NAME: direction_classifier.gates.volatility.passed
FAMILY: direction-diagnostics
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Canonical classifier dependencies
OUTPUT_TYPE: Boolean / reason enum as named
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: side-filtered where applicable
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Boolean/enum; exact original gate semantics
CURRENT_CANONICAL_USE: Diagnostics / prerequisite evidence; not independent market factors
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
```

### 3.64. direction_classifier.primary_rejection_stage

```yaml
METRIC_ID_OR_CANONICAL_NAME: direction_classifier.primary_rejection_stage
FAMILY: direction-diagnostics
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
OWNER: Set
INPUTS: Canonical classifier dependencies
OUTPUT_TYPE: Boolean / reason enum as named
UNIT: none
TIMEFRAME: completed 5m
DIRECTION_SENSITIVITY: side-filtered where applicable
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Boolean/enum; exact original gate semantics
CURRENT_CANONICAL_USE: Diagnostics / prerequisite evidence; not independent market factors
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part II §§34A–37
```

### 3.65. Set formation state

```yaml
METRIC_ID_OR_CANONICAL_NAME: Set formation state
FAMILY: set-state
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§14–22
  SOURCE_LINES: 1263–1550
OWNER: Set
INPUTS: Governed formation/activation/evidence state
OUTPUT_TYPE: INACTIVE / ARMED / PARTIALLY_MATCHED / MATCHED / EXPIRED / RESET / UNAVAILABLE
UNIT: none
TIMEFRAME: formation epoch or accepted pending remainder
DIRECTION_SENSITIVITY: original frozen direction
AVAILABILITY_STATES: INACTIVE / ARMED / PARTIALLY_MATCHED / MATCHED / EXPIRED / RESET / UNAVAILABLE
PRECISION_OR_NUMERIC_POLICY: State transition and exact identity rules; no arithmetic
CURRENT_CANONICAL_USE: State machine result, not a market Trigger shortcut
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §§14–22
```

### 3.66. Pending monitor state

```yaml
METRIC_ID_OR_CANONICAL_NAME: Pending monitor state
FAMILY: set-state
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§14–22
  SOURCE_LINES: 1263–1550
OWNER: Set
INPUTS: Governed formation/activation/evidence state
OUTPUT_TYPE: MONITORING_INACTIVE / MONITORING_ACTIVE / INVALIDATED / MONITORING_STOPPED / MONITORING_UNAVAILABLE
UNIT: none
TIMEFRAME: formation epoch or accepted pending remainder
DIRECTION_SENSITIVITY: original frozen direction
AVAILABILITY_STATES: MONITORING_INACTIVE / MONITORING_ACTIVE / INVALIDATED / MONITORING_STOPPED / MONITORING_UNAVAILABLE
PRECISION_OR_NUMERIC_POLICY: State transition and exact identity rules; no arithmetic
CURRENT_CANONICAL_USE: State machine result, not a market Trigger shortcut
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part I §§14–22
```

### 3.67. pending_validity

```yaml
METRIC_ID_OR_CANONICAL_NAME: pending_validity
FAMILY: set-state
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
OWNER: Set
INPUTS: Governed formation/activation/evidence state
OUTPUT_TYPE: VALID / INVALID / UNAVAILABLE / STOPPED
UNIT: none
TIMEFRAME: formation epoch or accepted pending remainder
DIRECTION_SENSITIVITY: original frozen direction
AVAILABILITY_STATES: VALID / INVALID / UNAVAILABLE / STOPPED
PRECISION_OR_NUMERIC_POLICY: State transition and exact identity rules; no arithmetic
CURRENT_CANONICAL_USE: State machine result, not a market Trigger shortcut
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part IV §§12–12A
```

### 3.68. Frozen hard-condition evaluation

```yaml
METRIC_ID_OR_CANONICAL_NAME: Frozen hard-condition evaluation
FAMILY: set-state
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
OWNER: Set
INPUTS: Governed formation/activation/evidence state
OUTPUT_TYPE: TRUE / FALSE / UNAVAILABLE / INVALID_CONDITION
UNIT: none
TIMEFRAME: formation epoch or accepted pending remainder
DIRECTION_SENSITIVITY: original frozen direction
AVAILABILITY_STATES: TRUE / FALSE / UNAVAILABLE / INVALID_CONDITION
PRECISION_OR_NUMERIC_POLICY: State transition and exact identity rules; no arithmetic
CURRENT_CANONICAL_USE: State machine result, not a market Trigger shortcut
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part IV §§12–12A
```

### 3.69. set_match_reference_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: set_match_reference_price
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Historical TICKER.last_price in governed match snapshot
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: price
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.70. tick_size

```yaml
METRIC_ID_OR_CANONICAL_NAME: tick_size
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Instrument metadata
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: price increment
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.71. PREVIOUS_DAY_HIGH

```yaml
METRIC_ID_OR_CANONICAL_NAME: PREVIOUS_DAY_HIGH
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed previous UTC day high
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: price
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.72. PREVIOUS_DAY_LOW

```yaml
METRIC_ID_OR_CANONICAL_NAME: PREVIOUS_DAY_LOW
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Completed previous UTC day low
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: price
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.73. relative_position.side

```yaml
METRIC_ID_OR_CANONICAL_NAME: relative_position.side
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Frozen level, frozen match reference, tick
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: enum
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.74. distance_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: distance_price
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Frozen level and match reference
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: price
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.75. distance_pct

```yaml
METRIC_ID_OR_CANONICAL_NAME: distance_pct
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Frozen level and match reference
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: percent
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.76. distance_atr_15m

```yaml
METRIC_ID_OR_CANONICAL_NAME: distance_atr_15m
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: Frozen level, match reference and received ATR_15m
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: ATR multiple
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.77. age_seconds

```yaml
METRIC_ID_OR_CANONICAL_NAME: age_seconds
FAMILY: handoff-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
OWNER: Set
INPUTS: market_snapshot_at and available_at
OUTPUT_TYPE: decimal / enum / integer as named
UNIT: integer seconds
TIMEFRAME: snapshot at matched_at; prior-day references use UTC
DIRECTION_SENSITIVITY: direction-neutral cached side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source facts; named Set outputs per TT_SET_NUMERIC_V1; age is ceiling of exact
  nonnegative timestamp difference
CURRENT_CANONICAL_USE: Handoff fact / frozen geometry; not retroactive initial-match predicate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
- methodology/SET.md
SOURCE_SECTION:
- Part III §§3–10
- Part III §§12–22
```

### 3.78. handoff_capabilities.reference_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.reference_price
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.79. handoff_capabilities.tick_geometry

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.tick_geometry
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.80. handoff_capabilities.volatility_scale

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.volatility_scale
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.81. handoff_capabilities.downside_geometry

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.downside_geometry
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.82. handoff_capabilities.upside_geometry

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.upside_geometry
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.83. handoff_capabilities.dynamic_sl_base

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.dynamic_sl_base
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.84. handoff_capabilities.dynamic_tp_base

```yaml
METRIC_ID_OR_CANONICAL_NAME: handoff_capabilities.dynamic_tp_base
FAMILY: handoff-capability
SOURCE:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§24–28
  SOURCE_LINES: 4101–4276
OWNER: Set
INPUTS: Frozen primitive handoff facts
OUTPUT_TYPE: available Boolean + reason
UNIT: none
TIMEFRAME: at match
DIRECTION_SENSITIVITY: dynamic capabilities depend on frozen side
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Defined Boolean predicate only
CURRENT_CANONICAL_USE: Set-local diagnostic projection, not second wire envelope or hidden extra gate
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/SET.md
SOURCE_SECTION:
- Part III §§24–28
```

### 3.85. planned_entry_reference

```yaml
METRIC_ID_OR_CANONICAL_NAME: planned_entry_reference
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part II §§3–31
```

### 3.86. improvement_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: improvement_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part II §§3–31
```

### 3.87. improvement_pct

```yaml
METRIC_ID_OR_CANONICAL_NAME: improvement_pct
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: percent
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part II §§3–31
```

### 3.88. improvement_atr

```yaml
METRIC_ID_OR_CANONICAL_NAME: improvement_atr
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: ATR multiple
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part II §§3–31
```

### 3.89. Entry candidate classification

```yaml
METRIC_ID_OR_CANONICAL_NAME: Entry candidate classification
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: TOO_SHALLOW / ELIGIBLE / TOO_DEEP
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part II §§3–31
```

### 3.90. stop_loss_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: stop_loss_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part I §§9–10
```

### 3.91. buffer_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: buffer_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.92. minimum_distance_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: minimum_distance_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.93. minimum_distance_adjustment_applied

```yaml
METRIC_ID_OR_CANONICAL_NAME: minimum_distance_adjustment_applied
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: Boolean
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.94. pre_rounding_risk_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: pre_rounding_risk_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.95. pre_rounding_risk_atr

```yaml
METRIC_ID_OR_CANONICAL_NAME: pre_rounding_risk_atr
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: ATR multiple
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.96. corroborating_level_ids[]

```yaml
METRIC_ID_OR_CANONICAL_NAME: corroborating_level_ids[]
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: reference IDs, diagnostic-only
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part III §§3–30
```

### 3.97. take_profit_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: take_profit_price
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: price
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part IV §§3–32
```

### 3.98. target distance ATR

```yaml
METRIC_ID_OR_CANONICAL_NAME: target distance ATR
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: ATR multiple
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part IV §§3–32
```

### 3.99. too_close_skipped_count

```yaml
METRIC_ID_OR_CANONICAL_NAME: too_close_skipped_count
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: integer count
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part IV §§3–32
```

### 3.100. selection_terminated_by_too_far

```yaml
METRIC_ID_OR_CANONICAL_NAME: selection_terminated_by_too_far
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: Boolean
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part IV §§3–32
```

### 3.101. first_too_far_distance_atr

```yaml
METRIC_ID_OR_CANONICAL_NAME: first_too_far_distance_atr
FAMILY: position-geometry
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
OWNER: Position Rules
INPUTS: Same-bound frozen handoff, pinned configuration, eligible source references; Entry where downstream
OUTPUT_TYPE: source-defined scalar / enum / collection
UNIT: ATR multiple
TIMEFRAME: initial opportunity construction
DIRECTION_SENSITIVITY: explicit LONG/SHORT formulas
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact consumed Q18 handoff values; source directional tick normalization; TT_NUMERIC_V1
  reports where specified
CURRENT_CANONICAL_USE: F-008 / F-006–F-010 geometry and diagnostics
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part IV §§3–32
```

### 3.102. target_order_notional

```yaml
METRIC_ID_OR_CANONICAL_NAME: target_order_notional
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: USDT notional
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.103. raw_qty

```yaml
METRIC_ID_OR_CANONICAL_NAME: raw_qty
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: base quantity; exact rational
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.104. final_qty

```yaml
METRIC_ID_OR_CANONICAL_NAME: final_qty
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: base quantity
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.105. actual_order_notional

```yaml
METRIC_ID_OR_CANONICAL_NAME: actual_order_notional
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: USDT notional
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.106. actual_committed_capital_exact

```yaml
METRIC_ID_OR_CANONICAL_NAME: actual_committed_capital_exact
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: own-capital unit
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.107. actual_committed_capital

```yaml
METRIC_ID_OR_CANONICAL_NAME: actual_committed_capital
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: own-capital unit
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.108. margin_required

```yaml
METRIC_ID_OR_CANONICAL_NAME: margin_required
FAMILY: construction-size
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Bound Portfolio grant, configured leverage, final Entry, quantity grid and venue facts
OUTPUT_TYPE: exact finite decimal / rational as defined
UNIT: own-capital unit
TIMEFRAME: post-grant construction
DIRECTION_SENSITIVITY: geometry direction fixed; quantities nonnegative
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact notional; floor quantity to qty_step; exact capital N/L and ceil_Qcapital liability;
  no repair
CURRENT_CANONICAL_USE: F-011; not a Set trigger or independent own-capital sizing rule
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§17–22A
- §§1–7
```

### 3.109. risk_distance_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: risk_distance_price
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: price
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.110. reward_distance_price

```yaml
METRIC_ID_OR_CANONICAL_NAME: reward_distance_price
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: price
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.111. risk_distance_pct

```yaml
METRIC_ID_OR_CANONICAL_NAME: risk_distance_pct
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: percent
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.112. reward_distance_pct

```yaml
METRIC_ID_OR_CANONICAL_NAME: reward_distance_pct
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: percent
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.113. gross_rr

```yaml
METRIC_ID_OR_CANONICAL_NAME: gross_rr
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: dimensionless
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.114. gross_profit_tp

```yaml
METRIC_ID_OR_CANONICAL_NAME: gross_profit_tp
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.115. gross_loss_sl

```yaml
METRIC_ID_OR_CANONICAL_NAME: gross_loss_sl
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: positive gross loss in accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.116. expected_entry_fee

```yaml
METRIC_ID_OR_CANONICAL_NAME: expected_entry_fee
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed cost in accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.117. expected_tp_exit_fee

```yaml
METRIC_ID_OR_CANONICAL_NAME: expected_tp_exit_fee
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed cost in accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.118. expected_sl_exit_fee

```yaml
METRIC_ID_OR_CANONICAL_NAME: expected_sl_exit_fee
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed cost in accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.119. tp_exit_notional

```yaml
METRIC_ID_OR_CANONICAL_NAME: tp_exit_notional
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: notional
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.120. sl_exit_notional

```yaml
METRIC_ID_OR_CANONICAL_NAME: sl_exit_notional
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: notional
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.121. tp_total_cost

```yaml
METRIC_ID_OR_CANONICAL_NAME: tp_total_cost
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed cost
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.122. sl_total_cost

```yaml
METRIC_ID_OR_CANONICAL_NAME: sl_total_cost
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed cost
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.123. net_profit_tp

```yaml
METRIC_ID_OR_CANONICAL_NAME: net_profit_tp
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.124. net_edge_pct

```yaml
METRIC_ID_OR_CANONICAL_NAME: net_edge_pct
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: percent of actual order notional
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.125. net_loss_sl

```yaml
METRIC_ID_OR_CANONICAL_NAME: net_loss_sl
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: signed accounting currency
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.126. net_rr

```yaml
METRIC_ID_OR_CANONICAL_NAME: net_rr
FAMILY: planned-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Position Rules
INPUTS: Validated Entry/Stop/Dynamic TP, final quantity/notional, bound factual signed maker/taker rates where
  required
OUTPUT_TYPE: exact monetary / ratio as named
UNIT: dimensionless or unavailable
TIMEFRAME: gross opportunity stage where inputs exist; full F-012 after grant
DIRECTION_SENSITIVITY: side-aware gross geometry; signed fees preserved
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact pre-report comparisons; Qratio floor only for reported ratios; no estimated
  funding; net_rr unavailable for net_loss_sl<=0
CURRENT_CANONICAL_USE: Existing planned economics; gross_rr is R:R comparator; net_rr diagnostic only
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- Part I §§23–40
- Part I §14
- §§1–7
```

### 3.127. minimum_rr_result

```yaml
METRIC_ID_OR_CANONICAL_NAME: minimum_rr_result
FAMILY: position-state
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
OWNER: Position Rules
INPUTS: Stage-legal prerequisites and pinned configuration
OUTPUT_TYPE: state enum
UNIT: none
TIMEFRAME: initial versus post-grant stages remain separate
DIRECTION_SENSITIVITY: direction immutable
AVAILABILITY_STATES: PASS / FAIL / UNAVAILABLE / NOT_APPLICABLE
PRECISION_OR_NUMERIC_POLICY: Exact branch predicates; disabled is not fabricated PASS
CURRENT_CANONICAL_USE: Decision outcome, not a market Trigger
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part I §14
- Part I §§23–40
```

### 3.128. minimum_net_edge

```yaml
METRIC_ID_OR_CANONICAL_NAME: minimum_net_edge
FAMILY: position-state
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
OWNER: Position Rules
INPUTS: Stage-legal prerequisites and pinned configuration
OUTPUT_TYPE: state enum
UNIT: none
TIMEFRAME: initial versus post-grant stages remain separate
DIRECTION_SENSITIVITY: direction immutable
AVAILABILITY_STATES: PASS / FAIL / UNAVAILABLE / NOT_APPLICABLE
PRECISION_OR_NUMERIC_POLICY: Exact branch predicates; disabled is not fabricated PASS
CURRENT_CANONICAL_USE: Decision outcome, not a market Trigger
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part I §14
- Part I §§23–40
```

### 3.129. OPPORTUNITY_DECISION

```yaml
METRIC_ID_OR_CANONICAL_NAME: OPPORTUNITY_DECISION
FAMILY: position-state
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
OWNER: Position Rules
INPUTS: Stage-legal prerequisites and pinned configuration
OUTPUT_TYPE: state enum
UNIT: none
TIMEFRAME: initial versus post-grant stages remain separate
DIRECTION_SENSITIVITY: direction immutable
AVAILABILITY_STATES: APPROVE / REJECT
PRECISION_OR_NUMERIC_POLICY: Exact branch predicates; disabled is not fabricated PASS
CURRENT_CANONICAL_USE: Decision outcome, not a market Trigger
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part I §14
- Part I §§23–40
```

### 3.130. CONSTRUCTION_RESULT

```yaml
METRIC_ID_OR_CANONICAL_NAME: CONSTRUCTION_RESULT
FAMILY: position-state
SOURCE:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
OWNER: Position Rules
INPUTS: Stage-legal prerequisites and pinned configuration
OUTPUT_TYPE: state enum
UNIT: none
TIMEFRAME: initial versus post-grant stages remain separate
DIRECTION_SENSITIVITY: direction immutable
AVAILABILITY_STATES: CONSTRUCTED / REJECT
PRECISION_OR_NUMERIC_POLICY: Exact branch predicates; disabled is not fabricated PASS
CURRENT_CANONICAL_USE: Decision outcome, not a market Trigger
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/POSITION_RULES.md
- methodology/POSITION_RULES.md
SOURCE_SECTION:
- Part I §14
- Part I §§23–40
```

### 3.131. daily_portfolio_base

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_portfolio_base
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own-capital currency
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§2–4
- §§1–7
- P6–P8
```

### 3.132. current_portfolio_equity

```yaml
METRIC_ID_OR_CANONICAL_NAME: current_portfolio_equity
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: API factual equity
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§2–4
- §§1–7
- P6–P8
```

### 3.133. daily_realized_pnl

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_realized_pnl
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: signed accounting currency
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §23
- §§1–7
- P6–P8
```

### 3.134. unrealized_pnl

```yaml
METRIC_ID_OR_CANONICAL_NAME: unrealized_pnl
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: factual signed accounting currency
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§2–4
- §§1–7
- P6–P8
```

### 3.135. total_pnl

```yaml
METRIC_ID_OR_CANONICAL_NAME: total_pnl
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: signed accounting currency
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§2–4
- §§1–7
- P6–P8
```

### 3.136. global_position_cap

```yaml
METRIC_ID_OR_CANONICAL_NAME: global_position_cap
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§6–8
- §§1–7
- P6–P8
```

### 3.137. coin_allocation_cap[symbol]

```yaml
METRIC_ID_OR_CANONICAL_NAME: coin_allocation_cap[symbol]
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part I §§6–8
- §§1–7
- P6–P8
```

### 3.138. committed_global_capital

```yaml
METRIC_ID_OR_CANONICAL_NAME: committed_global_capital
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.139. committed_coin_capital

```yaml
METRIC_ID_OR_CANONICAL_NAME: committed_coin_capital
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.140. logical_committed_capital[tranche]

```yaml
METRIC_ID_OR_CANONICAL_NAME: logical_committed_capital[tranche]
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.141. free_global_capital

```yaml
METRIC_ID_OR_CANONICAL_NAME: free_global_capital
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.142. free_coin_capital

```yaml
METRIC_ID_OR_CANONICAL_NAME: free_coin_capital
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.143. remaining_global_slots

```yaml
METRIC_ID_OR_CANONICAL_NAME: remaining_global_slots
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: integer slots
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.144. remaining_coin_slots

```yaml
METRIC_ID_OR_CANONICAL_NAME: remaining_coin_slots
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: integer slots
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.145. global_committed_tranches

```yaml
METRIC_ID_OR_CANONICAL_NAME: global_committed_tranches
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: integer tranches
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.146. coin_committed_tranches

```yaml
METRIC_ID_OR_CANONICAL_NAME: coin_committed_tranches
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: integer tranches
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.147. requested_capital_per_tranche

```yaml
METRIC_ID_OR_CANONICAL_NAME: requested_capital_per_tranche
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§11–17
- §§1–7
- P6–P8
```

### 3.148. daily_loss_limit_amount

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_loss_limit_amount
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: exact own-capital threshold
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §23
- §§1–7
- P6–P8
```

### 3.149. daily_loss_used_amount_d

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_loss_used_amount_d
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: own capital
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §23
- §§1–7
- P6–P8
```

### 3.150. cooldown_until[symbol]

```yaml
METRIC_ID_OR_CANONICAL_NAME: cooldown_until[symbol]
FAMILY: portfolio-accounting
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Portfolio Rules
INPUTS: Factual wallet/day state, four mutually exclusive commitment buckets, FINAL receipts and pinned user fields
  as applicable
OUTPUT_TYPE: exact amount / integer / timestamp
UNIT: timestamp
TIMEFRAME: Asia/Jerusalem accounting day; current state; attempt acceptance for cooldown
DIRECTION_SENSITIVITY: per-symbol both directions, not direction-specific cooldown
AVAILABILITY_STATES: AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
PRECISION_OR_NUMERIC_POLICY: Exact source amounts; Qcapital floors for spendable capacity/grant; no leverage-notional
  substitution; original accepted_at + pinned duration for cooldown
CURRENT_CANONICAL_USE: Capital gating/accounting; never Set trading-signal input
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
- schemas/NUMERIC_POLICY.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- Part II §§24–27
- §§1–7
- P6–P8
```

### 3.151. Portfolio health

```yaml
METRIC_ID_OR_CANONICAL_NAME: Portfolio health
FAMILY: portfolio-state
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
OWNER: Portfolio Rules
INPUTS: Canonical accounting/health/receipt and gate state
OUTPUT_TYPE: LIVE / RECONCILING / STALE
UNIT: none
TIMEFRAME: accounting day / scope revision
DIRECTION_SENSITIVITY: scope owns analysis; no direction selection
AVAILABILITY_STATES: LIVE / RECONCILING / STALE
PRECISION_OR_NUMERIC_POLICY: Exact state/revision/latch semantics
CURRENT_CANONICAL_USE: Gating state, not a tradable market metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
SOURCE_SECTION:
- Part II §§11–17
```

### 3.152. daily_loss_status

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_loss_status
FAMILY: portfolio-state
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
OWNER: Portfolio Rules
INPUTS: Canonical accounting/health/receipt and gate state
OUTPUT_TYPE: DISABLED / LATCHED / UNAVAILABLE_OR_FAIL_CLOSED / LIMIT_REACHED / OK
UNIT: none
TIMEFRAME: accounting day / scope revision
DIRECTION_SENSITIVITY: scope owns analysis; no direction selection
AVAILABILITY_STATES: DISABLED / LATCHED / UNAVAILABLE_OR_FAIL_CLOSED / LIMIT_REACHED / OK
PRECISION_OR_NUMERIC_POLICY: Exact state/revision/latch semantics
CURRENT_CANONICAL_USE: Gating state, not a tradable market metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
SOURCE_SECTION:
- Part II §23
```

### 3.153. daily_loss_blocks_new_exposure

```yaml
METRIC_ID_OR_CANONICAL_NAME: daily_loss_blocks_new_exposure
FAMILY: portfolio-state
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
OWNER: Portfolio Rules
INPUTS: Canonical accounting/health/receipt and gate state
OUTPUT_TYPE: Boolean
UNIT: none
TIMEFRAME: accounting day / scope revision
DIRECTION_SENSITIVITY: scope owns analysis; no direction selection
AVAILABILITY_STATES: Boolean
PRECISION_OR_NUMERIC_POLICY: Exact state/revision/latch semantics
CURRENT_CANONICAL_USE: Gating state, not a tradable market metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
SOURCE_SECTION:
- Part II §23
```

### 3.154. Coins status

```yaml
METRIC_ID_OR_CANONICAL_NAME: Coins status
FAMILY: portfolio-state
SOURCE:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
OWNER: Portfolio Rules
INPUTS: Canonical accounting/health/receipt and gate state
OUTPUT_TYPE: OPEN / CLOSE
UNIT: none
TIMEFRAME: accounting day / scope revision
DIRECTION_SENSITIVITY: scope owns analysis; no direction selection
AVAILABILITY_STATES: OPEN / CLOSE
PRECISION_OR_NUMERIC_POLICY: Exact state/revision/latch semantics
CURRENT_CANONICAL_USE: Gating state, not a tradable market metric
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/PORTFOLIO_RULES.md
SOURCE_SECTION:
- Part II §§11–17
```

### 3.155. gross_realized_trading_result

```yaml
METRIC_ID_OR_CANONICAL_NAME: gross_realized_trading_result
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: signed accounting currency
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §§33–34
- P6–P8
- §§1–7
```

### 3.156. actual_fees_rebates

```yaml
METRIC_ID_OR_CANONICAL_NAME: actual_fees_rebates
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: cost-effect signed accounting currency
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §§33–34
- P6–P8
- §§1–7
```

### 3.157. allocated_funding

```yaml
METRIC_ID_OR_CANONICAL_NAME: allocated_funding
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §32
  SOURCE_LINES: 1208–1339
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: wallet-effect signed accounting currency
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §32
- P6–P8
- §§1–7
```

### 3.158. other_supported_exchange_costs

```yaml
METRIC_ID_OR_CANONICAL_NAME: other_supported_exchange_costs
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: cost-effect signed accounting currency
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §§33–34
- P6–P8
- §§1–7
```

### 3.159. net_realized_result

```yaml
METRIC_ID_OR_CANONICAL_NAME: net_realized_result
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: signed accounting currency
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §§33–34
- P6–P8
- §§1–7
```

### 3.160. tranche_open_notional_at_funding_time

```yaml
METRIC_ID_OR_CANONICAL_NAME: tranche_open_notional_at_funding_time
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §32
  SOURCE_LINES: 1208–1339
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: notional
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §32
- P6–P8
- §§1–7
```

### 3.161. total_triggertrade_open_notional_for_symbol_side_at_funding_time

```yaml
METRIC_ID_OR_CANONICAL_NAME: total_triggertrade_open_notional_for_symbol_side_at_funding_time
FAMILY: realized-economics
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §32
  SOURCE_LINES: 1208–1339
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
OWNER: Order Lifecycle
INPUTS: Complete attributed entry/exit executions, actual fee/rebate/funding/cost sources, currency and chronology
  proof
OUTPUT_TYPE: exact monetary amount
UNIT: notional
TIMEFRAME: factual execution/funding time; immutable final closing day
DIRECTION_SENSITIVITY: logical tranche and native-side lineage
AVAILABILITY_STATES: Final logical result only after mandatory COMPLETE evidence and currency/attribution/finality
  proof
PRECISION_OR_NUMERIC_POLICY: Actual native source quantum and signs; funding separate decimal18 algorithm; no
  planned-fee substitution
CURRENT_CANONICAL_USE: A-002 / A-004 financial result and funding attribution
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
- schemas/NUMERIC_POLICY.md
SOURCE_SECTION:
- §32
- P6–P8
- §§1–7
```

### 3.162. lifecycle_state

```yaml
METRIC_ID_OR_CANONICAL_NAME: lifecycle_state
FAMILY: lifecycle-state
SOURCE:
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §7
  SOURCE_LINES: 522–595
- SOURCE_DOCUMENT: SYSTEM_PROTOCOLS.md
  SOURCE_SECTION: P6–P8
  SOURCE_LINES: 114–220
OWNER: Order Lifecycle
INPUTS: Authorized immutable spec; native factual execution/protection/financial evidence
OUTPUT_TYPE: enum
UNIT: none
TIMEFRAME: tranche lifecycle
DIRECTION_SENSITIVITY: frozen direction and native side
AVAILABILITY_STATES: READY_TO_SUBMIT / SUBMITTING / SUBMISSION_UNCERTAIN / PENDING_ENTRY / PARTIALLY_FILLED /
  OPEN / CANCEL_PENDING / CANCELLED_ZERO_FILL / CLOSE_PENDING / CLOSED / SUBMISSION_FAILED / RECONCILING / MANUAL_INTERVENTION_REQUIRED
PRECISION_OR_NUMERIC_POLICY: Identity, chronology and state predicates; no new lifecycle states
CURRENT_CANONICAL_USE: Includes CLOSED only under all six P6 predicates; zero exposure alone is insufficient
TRIGGER_CONSTRUCTION_USABILITY: NO — not an independent initial-formation Trigger input in this design; preserve
  its stated owner/stage/use
DEPENDENCIES: []
ALIASES: []
SOURCE_NAME_NOTE: Qualified instance/path labels identify existing source objects; punctuation is not a new transport
  field or calculation.
SOURCE_DOCUMENT:
- methodology/ORDER_LIFECYCLE.md
- SYSTEM_PROTOCOLS.md
SOURCE_SECTION:
- §7
- P6–P8
```

## 4. Trigger construction matrix

The source-derived operator/type table is retained. Its original “F-005 qualification” narrative applies to the original governed Sets. The eight new BTC trigger instances and the enclosing generic direction scope are specified separately in the normalized model; canonical metric prerequisites remain unchanged. Reporting statistics are not in this trigger domain.


Operators here are typed research-expression spellings, not an extension of a wire schema. A numeric interval is an explicit conjunction of two comparisons; no new calculated metric is introduced. Crossings require a governed temporal predicate with exact previous/current evidence; an operator name in the pending-condition enum does not supply missing metric-specific crossing semantics. No cross is selected without that proof.

### F-001 trigger_result

```yaml
METRIC: F-001 trigger_result
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: F-001 positive theta_move_pct only; F-002 fixed boundaries are not configurable
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: No LONG/SHORT authority
FRESHNESS_REQUIREMENTS: 1m; current completed slot only; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: CURRENT_STATE only; canonical current 1m slot
PREREQUISITES: Current and immediately preceding completed 1m KLINES.close; pinned positive theta_move_pct; TRUE
  / FALSE / UNAVAILABLE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
- Retune F-002 R/P boundaries
- Change F-001/F-002 to FRESH_EVENT
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### F-002 trigger_result

```yaml
METRIC: F-002 trigger_result
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: F-001 positive theta_move_pct only; F-002 fixed boundaries are not configurable
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: Direction-neutral
FRESHNESS_REQUIREMENTS: 1m current completed slot; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: CURRENT_STATE only; canonical current 1m slot
PREREQUISITES: Current and 60 immediately preceding consecutive completed 1m base-volume candles; TRUE / FALSE
  / UNAVAILABLE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
- Retune F-002 R/P boundaries
- Change F-001/F-002 to FRESH_EVENT
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### ATR_work

```yaml
METRIC: ATR_work
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: neutral
FRESHNESS_REQUIREMENTS: 15m, Wilder(14) for ATR; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry; Work
  zero may be valid; percentage unavailable at zero close; both required wire exports AVAILABLE and >0
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### ATR_PCT_work

```yaml
METRIC: ATR_PCT_work
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: neutral
FRESHNESS_REQUIREMENTS: 15m, Wilder(14) for ATR; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Eligible 15m H/L/C; immediate factual predecessor; canonical 14-TR seed/checkpoint ancestry; Work
  zero may be valid; percentage unavailable at zero close; both required wire exports AVAILABLE and >0
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### ATR percentile

```yaml
METRIC: ATR percentile
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: neutral
FRESHNESS_REQUIREMENTS: 30 completed UTC days; minimum 14 eligible complete days; authoritative source completion/cutoff;
  no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Current ATR_PCT and eligible completed same-symbol 15m ATR_PCT reference population; AVAILABLE
  / UNAVAILABLE; missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### SWING_SEQUENCE_STATE(asset,1h)

```yaml
METRIC: SWING_SEQUENCE_STATE(asset,1h)
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: NO, enum only
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: categorical trend; not final direction
FRESHNESS_REQUIREMENTS: 1h; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Latest two confirmed highs and lows for named scope; one-tick equality tolerance; BULLISH / BEARISH
  / AMBIGUOUS; UNAVAILABLE if required pivots absent
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### SWING_SEQUENCE_STATE(asset,15m)

```yaml
METRIC: SWING_SEQUENCE_STATE(asset,15m)
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: NO, enum only
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: categorical trend; not final direction
FRESHNESS_REQUIREMENTS: 15m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Latest two confirmed highs and lows for named scope; one-tick equality tolerance; BULLISH / BEARISH
  / AMBIGUOUS; UNAVAILABLE if required pivots absent
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### SWING_SEQUENCE_STATE(BTC,1h)

```yaml
METRIC: SWING_SEQUENCE_STATE(BTC,1h)
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: NO, enum only
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: categorical trend; not final direction
FRESHNESS_REQUIREMENTS: 1h; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Latest two confirmed highs and lows for named scope; one-tick equality tolerance; BULLISH / BEARISH
  / AMBIGUOUS; UNAVAILABLE if required pivots absent
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### RETURN(asset,15m)

```yaml
METRIC: RETURN(asset,15m)
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: 15m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned completed-bar closes for named horizon; AVAILABLE / UNAVAILABLE; missing evidence is never
  zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### RETURN(BTC,15m)

```yaml
METRIC: RETURN(BTC,15m)
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: 15m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned completed-bar closes for named horizon; AVAILABLE / UNAVAILABLE; missing evidence is never
  zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### RETURN(asset,5m)

```yaml
METRIC: RETURN(asset,5m)
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: 5m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned completed-bar closes for named horizon; AVAILABLE / UNAVAILABLE; missing evidence is never
  zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### DE

```yaml
METRIC: DE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: unsigned efficiency
FRESHNESS_REQUIREMENTS: 15m over 8 changes; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: 15m closes, fixed N=8; DE_STRENGTH consumes DE; AVAILABLE / UNAVAILABLE; DE denominator zero maps
  to canonical 0
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### DE_STRENGTH

```yaml
METRIC: DE_STRENGTH
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: unsigned efficiency
FRESHNESS_REQUIREMENTS: 15m over 8 changes; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: 15m closes, fixed N=8; DE_STRENGTH consumes DE; AVAILABLE / UNAVAILABLE; DE denominator zero maps
  to canonical 0
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### VNM_15m

```yaml
METRIC: VNM_15m
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### momentum_z

```yaml
METRIC: momentum_z
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### MOMENTUM_SCORE

```yaml
METRIC: MOMENTUM_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### MOMENTUM_EFFECTIVE

```yaml
METRIC: MOMENTUM_EFFECTIVE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### ATR_PCT_5m

```yaml
METRIC: ATR_PCT_5m
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### VNM_5m

```yaml
METRIC: VNM_5m
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### VNM_5m_z

```yaml
METRIC: VNM_5m_z
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed except volatility denominator
FRESHNESS_REQUIREMENTS: 5m local or 15m primary as named; z uses completed UTC-day population; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Governed named dependencies; separate 5m ATR ancestry for local instance; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### RELATIVE_RETURN_15m

```yaml
METRIC: RELATIVE_RETURN_15m
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed relative to BTC
FRESHNESS_REQUIREMENTS: 15m; z population 30/14 completed UTC days; authoritative source completion/cutoff; no
  stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned asset/BTC completed 15m returns and canonical normalization; AVAILABLE / UNAVAILABLE; missing
  evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### relative_return_z

```yaml
METRIC: relative_return_z
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed relative to BTC
FRESHNESS_REQUIREMENTS: 15m; z population 30/14 completed UTC days; authoritative source completion/cutoff; no
  stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned asset/BTC completed 15m returns and canonical normalization; AVAILABLE / UNAVAILABLE; missing
  evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### RELATIVE_SCORE

```yaml
METRIC: RELATIVE_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed relative to BTC
FRESHNESS_REQUIREMENTS: 15m; z population 30/14 completed UTC days; authoritative source completion/cutoff; no
  stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Aligned asset/BTC completed 15m returns and canonical normalization; AVAILABLE / UNAVAILABLE; missing
  evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6
  SOURCE_LINES: 1739–1961
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### AGGRESSIVE_VOLUME_DELTA_PCT

```yaml
METRIC: AGGRESSIVE_VOLUME_DELTA_PCT
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed imbalance except positive side sums
FRESHNESS_REQUIREMENTS: completed 5m horizon; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### FLOW_RAW

```yaml
METRIC: FLOW_RAW
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed imbalance except positive side sums
FRESHNESS_REQUIREMENTS: completed 5m horizon; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### FLOW_EFFECTIVE

```yaml
METRIC: FLOW_EFFECTIVE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed imbalance except positive side sums
FRESHNESS_REQUIREMENTS: completed 5m horizon; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: 5m RAW_TRADES.taker_side and notional_quote; exact source-complete membership; AVAILABLE / UNAVAILABLE;
  missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: api-contracts/MARKET_DATA_REQUEST.md
  SOURCE_SECTION: §§1–6
  SOURCE_LINES: 6–46
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### TOD_REL_TURNOVER

```yaml
METRIC: TOD_REL_TURNOVER
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: neutral
FRESHNESS_REQUIREMENTS: 5m same-clock, previous 30 UTC dates; minimum 14 eligible buckets; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Current completed 5m quote turnover / exact median of strictly prior same-clock UTC buckets; AVAILABLE
  / UNAVAILABLE; missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### PARTICIPATION_STRENGTH

```yaml
METRIC: PARTICIPATION_STRENGTH
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: neutral
FRESHNESS_REQUIREMENTS: completed 5m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: TOD_REL_TURNOVER; AVAILABLE / UNAVAILABLE; missing evidence is never zero or FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### BTC_STRUCTURE_SCORE

```yaml
METRIC: BTC_STRUCTURE_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### BTC_RETURN_Z

```yaml
METRIC: BTC_RETURN_Z
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### BTC_MOMENTUM_SCORE

```yaml
METRIC: BTC_MOMENTUM_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### BTC_CONTEXT_SCORE

```yaml
METRIC: BTC_CONTEXT_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### STRUCTURE_1H

```yaml
METRIC: STRUCTURE_1H
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### STRUCTURE_15M

```yaml
METRIC: STRUCTURE_15M
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### STRUCTURE_SCORE

```yaml
METRIC: STRUCTURE_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### DIRECTION_SCORE

```yaml
METRIC: DIRECTION_SCORE
ALLOWED_OPERATORS:
- LT
- LTE
- GT
- GTE
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Finite exact decimal within the canonical metric domain; unit must match
THRESHOLD_ALLOWED: YES, extra research predicate; no change to canonical internal gates
STATE_COMPARISON_ALLOWED: NO numeric-to-state coercion
INTERVAL_COMPARISON_ALLOWED: YES, explicit lower/upper comparisons, inclusivity and availability propagation
DIRECTION_CONTEXT: signed
FRESHNESS_REQUIREMENTS: Classifier completed-5m evaluation with completed 15m/1h inputs; authoritative source
  completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: Named immutable formula dependencies; AVAILABLE / UNAVAILABLE; missing evidence is never zero or
  FALSE
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

### classifier_direction

```yaml
METRIC: classifier_direction
ALLOWED_OPERATORS:
- EQ
- NEQ
ALLOWED_VALUE_TYPES: Existing enum/tri-state value; never numeric ordering
THRESHOLD_ALLOWED: NO, enum only
STATE_COMPARISON_ALLOWED: 'YES'
INTERVAL_COMPARISON_ALLOWED: 'NO'
DIRECTION_CONTEXT: sole direction authority in F-005-governed scope
FRESHNESS_REQUIREMENTS: completed 5m; authoritative source completion/cutoff; no stale fill
CURRENT_STATE_REQUIREMENTS: Current canonical evaluation required; a generic FRESH_EVENT wrapper must satisfy
  uninterrupted same-epoch FALSE->TRUE and final current direction
PREREQUISITES: All eleven required F-004 inputs, score, hard gates, both sides' veto evidence; LONG / SHORT /
  NONE plus required availability/rejection diagnostics; DATA_UNAVAILABLE is never a known-negative market condition
INVALID_TRIGGER_FORMS:
- Treat UNAVAILABLE as FALSE/zero
- Change formula, weights, baseline calendar or canonical timeframe
- Use future/local receipt time
- Use a local diagnostic as an invented wire field
- Unspecified crossing/event semantics
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
```

## 5. Non-admitted trading context and now-authorized research reporting

These names are preserved as source vocabulary, **not newly created metric definitions**. Some are raw factual context fields (for example funding/mark/index), some are optional derived names, and some are non-normative diagnostics. Their presence does not establish a complete active trading predicate with calculation/anchor/freshness semantics. For every missing element the value is `NOT_SPECIFIED_IN_FROZEN_METHODOLOGY`; no formula has been filled in from general trading knowledge. S-005 is explicitly prohibited as a trading gate. Direction strength bands are diagnostics, not automatic sizing or exit rules.

| Context name | Disposition / missing execution contract |
|---|---|
| OI_CHANGE_PCT(15m) | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| OI_CHANGE_PCT(1h) | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| FUNDING_RATE | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| PREMIUM_INDEX | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| MARK_INDEX_SPREAD_PCT | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| VWAP_DISTANCE | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| MARKET_BREADTH | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| RANGE_BOUNDARY | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| DISTANCE_TO_LEVEL | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| atr_1h | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| atr_pct_1h | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| realized_volatility | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| volatility_ratio | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| range.mid | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| range.width_price | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| range.width_pct | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| range.width_atr_15m | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| optional_context.vwap.value | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| relative_turnover | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| trade_intensity | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| turnover_liquidity | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| aggressive_volume_delta_pct_15m | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| current_open_interest | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| momentum_rank | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| relative_volatility | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| dispersion | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| session_id | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| time_of_day_bucket | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| minutes_since_session_start | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| minutes_to_session_boundary | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| current_session_high | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| current_session_low | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| previous_session_high | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| previous_session_low | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| mark_price | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| index_price | Context/raw fact only in this extraction; proposed derived trigger needs complete governed producer, identity, units, timeframe and availability contract |
| S-005 / CTX-REGIME@0.1.0 | Diagnostic-only, forbidden as trading input |
| STRONG_LONG / EXTREME_LONG / STRONG_SHORT / EXTREME_SHORT | Diagnostic band only; no policy effect |

`methodology/SET.md` Part III §§30–36, lines 4304–4486; `SYSTEM_PROTOCOLS.md` Research isolation — S-005 diagnostic-only boundary, lines 887–897; `methodology/SET.md` Part II §39, lines 3470–3492

### Required Entry reporting vocabulary

| Existing report name | Research V1 reporting definition (not a trading metric) |
|---|---|
| fill rate | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| time to fill | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| missed-trade rate | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| TOO_SHALLOW skip frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| too-deep candidate frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| ENTRY_TOO_DEEP_AFTER_ROUNDING frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| native POST_ONLY rejection/cancellation frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| hard non-market technical incompatibility frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| entry-reference age | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| eventual expectancy by entry-distance band | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| adverse excursion after fill | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| favorable excursion after fill | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |

`methodology/POSITION_RULES.md` Part II §§50–51, lines 3205–3244

### Required TP reporting vocabulary

| Existing report name | Research V1 reporting definition (not a trading metric) |
|---|---|
| thesis override frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| NO_REACHABLE_TARGET frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| too-close frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| too-far frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| time-to-target | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| MAE before target | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| MFE | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| target hit rate | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| previous-day vs 1h target behavior | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| minimum-distance sensitivity | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| maximum-distance sensitivity | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |

`methodology/POSITION_RULES.md` Part IV §§47–48, lines 5449–5486

### Required Portfolio reporting vocabulary

| Existing report name | Research V1 reporting definition (not a trading metric) |
|---|---|
| gate failure frequencies | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| cooldown block frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| daily loss block frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| global cap block frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| coin cap block frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| slot utilization | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| capital utilization | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| coin allocation utilization | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| submission hold duration | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| reserved capital duration | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| reconciliation count / frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| concurrency conflicts | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| missed opportunities due to capacity | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |

`methodology/PORTFOLIO_RULES.md` Part VIII §63, lines 1741–1775

### Required Lifecycle reporting vocabulary

| Existing report name | Research V1 reporting definition (not a trading metric) |
|---|---|
| submission acceptance rate | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| ambiguous submission frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| time from submit to acceptance | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| time to first fill | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| time to full fill | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| partial-fill frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| fill ratio | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| cancel frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| cancel/fill race frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| Set-driven cancel frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| manual cancel frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| zero-fill cancel frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| partial-fill remainder cancel frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| TP close frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| SL close frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| Manual Close frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| reconciliation frequency | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| reconciliation duration | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| restart recovery corrections | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| duplicate event count | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| out-of-order event count | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| protection verification failures | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |
| manual intervention count | DEFINED_IN_RESEARCH_V1: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–7; explicit stage denominator, interval, finality, censoring and empty/unavailable behavior |

`methodology/ORDER_LIFECYCLE.md` §43, lines 1774–1830

The complete source-defined raw dimensions and diagnostics remain required. Research V1 now authorizes descriptive aggregation: the eleven comparison statistics are defined in the new profile §6; every supplementary Entry/TP/Portfolio/Lifecycle report family is operationalized in §7. These reporting definitions close B-02 but do not turn optional context/S-005 into trading predicates. No report statistic is added to the canonical inventory or trigger matrix.

## 6. Set design space

| SET_DIMENSION | ALLOWED_VARIATION | DEPENDENCIES | INVALID_VARIATION | SOURCE |
|---|---|---|---|---|
| Trigger membership | Add/remove existing eligible predicates; F-005 and complete handoff remain mandatory in this scoped portfolio. | Metric/source availability and role restrictions. | Cannot replace F-005 with F-001 sign or add an undefined metric. | `methodology/SET.md` Part I §8A, lines 617–843; `methodology/SET.md` Part I §8B, lines 847–1078; `methodology/SET.md` Part II §§34A–37, lines 3155–3435 |
| Boolean AND / OR / NOT | Explicit tri-state composition; NOT preserves UNAVAILABLE. | Typed current metric predicates. | No coercion of missing to FALSE; no arithmetic on enums. | `methodology/SET.md` Part I §9, lines 1082–1128 |
| N-of-M | Only explicit count semantics; a research expression can be expanded into supported AND/OR. | Source says may be supported; native N-of-M wire semantics are not supplied. | Do not assume undocumented evaluator or unavailable-count behavior. | `methodology/SET.md` Part I §9, lines 1082–1128; `methodology/SET.md` Part I §§14–22, lines 1263–1550 |
| Sequence / order | Strict tB>tA, explicit anchor/window/comparison; source permits equal times only when explicitly configured. | Same-epoch evidence, known authoritative chronology. | No loop-time order, old event reuse, implicit window or repeated-TRUE timer refresh. | `methodology/SET.md` Part I §§11–12, lines 1213–1243; `methodology/SET.md` Part I §10, lines 1132–1211 |
| Maintained condition | Predicate required TRUE at declared authoritative evaluations throughout a formation interval. | Explicit evaluation grid and endpoints. | No claim of continuous intra-bar truth from sampled observations. | `methodology/SET.md` Part I §13, lines 1247–1259 |
| CURRENT_STATE / FRESH_EVENT | Generic predicate role may be chosen; F-001/F-002 are CURRENT_STATE-only. | Same-epoch FALSE->TRUE with uninterrupted availability for events. | No initial TRUE event, no UNAVAILABLE->TRUE event, no restart remint. | `methodology/SET.md` Part I §10, lines 1132–1211; `methodology/SET.md` Part I §8A, lines 617–843; `methodology/SET.md` Part I §8B, lines 847–1078 |
| Freshness / SINCE_SET_ARMED | Explicit duration/operator/authoritative anchor; modifier requires explicit role. | No overriding fixed current-slot freshness or macro calendar. | No wall-clock substitution or third event-production semantics. | `methodology/SET.md` Part I §17, lines 1448–1466 |
| Lifetime / expiry / reset | Optional lifetime with declared clock-start; reset trigger, maintained failure, timeout, unavailable or epoch changes as specified. | Research must bind reset and re-arm unambiguously. | No implicit pending TTL or mutating a committed match. | `methodology/SET.md` Part I §§14–22, lines 1263–1550; `methodology/SET.md` Part I §§18–20, lines 1470–1514 |
| Re-arm | AFTER_RESET, AFTER_ALL_REQUIRED_TRIGGERS_CLEAR, NEXT_SESSION with complete conditions. | Clear semantics must be satisfiable; NEXT_SESSION needs governed boundary. | Immediate re-arm is excluded; unspecified sessions cannot be invented. | `methodology/SET.md` Part I §§18–20, lines 1470–1514; `methodology/SET.md` Part III §§30–36, lines 4304–4486 |
| Direction | Governed F-005 scope remains LONG/SHORT/NONE; generic deterministic Sets may explicitly bind fixed/branch direction outside this scope. | Governed and generic non-F-005 definitions must not be mixed. | No forced side, opposite-veto reversal, direction changes inside Position. | `methodology/SET.md` Part I §5, lines 509–530; `methodology/SET.md` Part II §§34A–37, lines 3155–3435 |
| Position context / reference binding | Set family and REQUIRED/PREFERRED/NONE thesis policies with exact constituent producer bindings. | Unique typed references; NONE means null thesis/origin; GENERIC family is not generic direction scope. | No invented role producer or nearest/latest heuristic; Position cannot own Set bindings. | `methodology/SET.md` Part III §43.1, lines 4769–4801; `methodology/SET.md` Part III §§12–22, lines 3757–4059 |
| Conflict handling | Explicit source-legal deterministic rule where configuration requires it; unavailable or conflicting bound identities fail. | Complete source identity and disambiguation. | No unspecified tie/conflict heuristic or non-deterministic branch priority. | `methodology/SET.md` Part I §5, lines 509–530; `methodology/SET.md` Part III §43.1, lines 4769–4801 |
| Multi-timeframe composition | Combine existing source-defined instances without changing their calculation horizons. | Own as-of and source completeness per metric; F-005 cadence remains 5m. | No switching canonical F-001/F-002 to 5m candles or UTC normalization to local time. | `methodology/SET.md` Part II §§3–6, lines 1739–1961; `methodology/SET.md` Part I §8A, lines 617–843; `methodology/SET.md` Part I §8B, lines 847–1078 |
| Pending validity | Freeze at least one typed original-match hard invalidation condition; monitor only after ORDER_PLACED. | Original direction/metric identity; FAIL_SAFE_CANCEL; source-authoritative remainder state. | No rerunning full Set for a new trade; no chasing, filled-exposure exit, or capital release. | `methodology/SET.md` Part IV §§12–12A, lines 4879–5162 |

## 7. Position Rules design space

| POSITION_RULE_DIMENSION | ALLOWED_VALUES_OR_RANGE | DEPENDENCIES | CONSTRAINTS | RESEARCH_USABILITY | SOURCE |
|---|---|---|---|---|---|
| MIN_ENTRY_IMPROVEMENT_ATR | Research baseline 0.10; proposed variant 0.25. A universal allowed parameter range is NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Entry raw/rounded eligible structural reference geometry. | Retain positive price/tick and minimum-versus-maximum consistency; no algorithm redesign. | YES, source explicitly names research parameter. | `methodology/POSITION_RULES.md` Part II §§3–31, lines 2142–2759; `methodology/POSITION_RULES.md` Part II §§50–51, lines 3205–3244 |
| MAX_ENTRY_DEVIATION_ATR | Baseline 1.25; proposed 2.00; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Same selected Entry procedure and tick rounding. | No chase/market fallback and no native bid/ask policy invented. | YES, research parameter. | `methodology/POSITION_RULES.md` Part II §§3–31, lines 2142–2759; `methodology/POSITION_RULES.md` Part II §§50–51, lines 3205–3244 |
| stop_loss.mode / fixed_pct | DYNAMIC or FIXED; fixed_pct finite >0; LONG fixed_pct<100; no extra SHORT ceiling inferred. | Mode pinned at initial Opportunity; Fixed Stop uses final Entry/tick. | Dynamic fixed_pct is ignored; fixed mode does not run Dynamic SL. | YES. | `methodology/POSITION_RULES.md` Part I §8, lines 242–270; `methodology/POSITION_RULES.md` Part I §§9–10, lines 274–365; `methodology/POSITION_RULES.md` Part I §14, lines 465–517 |
| BUFFER_ATR_MULTIPLIER | Baseline 0.20; proposed 0.40; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Selected structural Stop anchor and received ATR. | Do not retry weaker levels on hard failure. | YES, research parameter. | `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974; `methodology/POSITION_RULES.md` Part III §39, lines 4238–4249 |
| MIN_DISTANCE_ATR | Baseline 0.50; reserve 0.75; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Dynamic Stop risk and minimum adjustment. | Equality is not strict minimum-adjustment activation. | YES, reserve. | `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974; `methodology/POSITION_RULES.md` Part III §39, lines 4238–4249 |
| MAX_DISTANCE_ATR | Baseline 2.00; proposed 1.50; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Pre/post-round Stop risk. | Hard reject beyond cap, no alternative-anchor rescue. | YES. | `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974; `methodology/POSITION_RULES.md` Part III §39, lines 4238–4249 |
| CORROBORATION_DISTANCE_ATR | Baseline 0.25; diagnostic reserve 0.50. | Source proximity list/warnings. | Cannot change selected Stop or trade. | NO for distinct trading-effect hypothesis; diagnostic study only. | `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974; `methodology/POSITION_RULES.md` Part III §39, lines 4238–4249 |
| take_profit.mode / fixed_pct | Fields exist, but certified chain requires Dynamic F-010. | Stop dispatch F-009; independent TP geometry and inputs. | Fixed TP retained prose is not a substitute for F-010. | DYNAMIC only in admitted design candidates. | `methodology/POSITION_RULES.md` Part I §8, lines 242–270; `methodology/POSITION_RULES.md` Part I §14, lines 465–517 |
| MIN_TP_DISTANCE_ATR | Baseline 0.75; proposed 1.25; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | TP candidate distance to final Entry. | Too-close candidates may be skipped; stop/TP calculations remain independent. | YES. | `methodology/POSITION_RULES.md` Part IV §§3–32, lines 4320–5056; `methodology/POSITION_RULES.md` Part IV §§47–48, lines 5449–5486 |
| MAX_TP_DISTANCE_ATR | Baseline 4.00; proposed 3.00; universal range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | TP source order and post-round eligibility. | First TOO_FAR terminates; no weaker target retry. | YES. | `methodology/POSITION_RULES.md` Part IV §§3–32, lines 4320–5056; `methodology/POSITION_RULES.md` Part IV §§47–48, lines 5449–5486 |
| minimum_risk_reward.enabled / value | Boolean and finite configured value; no invented positivity rule beyond source. Research value 2; reserve 2.5. | Gross structural reward/risk; pre-grant geometry. | Disabled NOT_APPLICABLE; no net_rr substitution. | YES. | `methodology/POSITION_RULES.md` Part I §39, lines 1332–1366; `methodology/POSITION_RULES.md` Part I §§23–40, lines 912–1436 |
| minimum_net_edge.enabled / pct | Boolean and source-valid finite percentage; research 1%. | After exact grant sizing and factual signed maker/taker rates. | Denominator actual notional, not own capital; funding excluded from planned edge. | YES. | `methodology/POSITION_RULES.md` Part I §40, lines 1370–1436; `methodology/POSITION_RULES.md` Part I §§23–40, lines 912–1436 |
| leverage.value | Finite >0 and <= factual venue maximum; no invented integer or >=1 restriction. Research 1 / 2. | Own-capital grant, quantity grid, factual native-side compatibility. | No Position Size field; no automatic active-side leverage retune. | YES, coupled. | `methodology/POSITION_RULES.md` Part I §22, lines 837–880; `methodology/POSITION_RULES.md` Part I §§17–22A, lines 576–908 |
| Structural hierarchy by Set family | Governed GENERIC/TREND_CONTINUATION/RANGE/BREAKOUT_RECLAIM context. | Set-owned exact context producer/role bindings. | No Position-owned field invented; GENERIC and TREND may be identical in the no-thesis baseline. | CONDITIONAL; source explicitly requests tests but nontrivial alternate bindings are missing here. | `methodology/POSITION_RULES.md` Part II §§50–51, lines 3205–3244; `methodology/POSITION_RULES.md` Part IV §§47–48, lines 5449–5486; `methodology/SET.md` Part III §43.1, lines 4769–4801 |

## 8. Portfolio Rules design space

| PORTFOLIO_RULE_DIMENSION | ALLOWED_VALUES_OR_RANGE | DEPENDENCIES | CONSTRAINTS | RESEARCH_USABILITY | SOURCE |
|---|---|---|---|---|---|
| max_capital_in_positions_pct | Finite governed percentage; source does not grant an arbitrary research range. Proposed 60 / 40. | Fixed daily_portfolio_base and four commitment buckets. | Own capital, not leveraged notional. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part I §§6–8, lines 288–358; `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772 |
| coins[].allocation_pct | Source-supported per-coin target AND hard cap. Research V1 fixes exactly 10% for each of the ten members; no first-wave variation. | Same daily base and remaining coin slots. | Canonical global cap is separate; this campaign fixes allocation sum exactly 100%, with no redistribution. | FIXED CONTROL ONLY; old allocation study C-050 is campaign-invalid | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part I §§6–8, lines 288–358 |
| max_open_positions | Positive admissible slot count; proposed 6 / 3. | All unresolved holds/tranches consume slots. | Global slots are not the coin sizing divisor. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part II §§11–17, lines 484–633; `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772 |
| max_positions_per_coin | Positive admissible slot count; proposed 2 / 3. | Also divides free coin capital into requested tranche capital. | Cannot hold tranche grant fixed and call this unchanged canonical sizing. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part II §§11–17, lines 484–633; `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772 |
| minimum_tranche_capital | Source-governed own-capital floor; proposed 25 / 50. | Requested grant, free global capital and venue minimums. | No shrinking to fit leftovers; no notional substitution. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772 |
| cooldown_minutes | Configured duration; research 5 / 15 minutes. Exhaustive validation range NOT_SPECIFIED_IN_FROZEN_METHODOLOGY | Pinned at authorization, starts at factual proven accepted_at. | Both directions share symbol cooldown; expiry does not cancel old orders. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part II §§24–27, lines 876–980 |
| daily_loss_limit.enabled / pct | Boolean; enabled percentage valid positive; no new percentage ceiling. Research false / true at 5%. | FINAL signed current-day result receipts, fixed base, day/latch recovery. | Inclusive signed comparison; no unrealized PnL, forced closure or pending cancellation. | YES, subject to complete source-valid run bindings | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part II §23, lines 776–872 |
| coins[].symbol / enabled | Source-selected coin and enable flag; campaign membership/enable flags are fixed, not researched. Research V1 UNIVERSE-CORE-V1: BTC/ETH/SOL/XRP/DOGE/SUI/PEPE/AVAX/LINK/BNB; exact native mappings are typed launch inputs in the V1 profile §3.1 | Market source and native product identity; BTC generic trading binding; non-BTC benchmark context remains separate. | Changing enabled universe changes portfolio interference and normalization series; no guessed native symbols. | IMMUTABLE UNIVERSE CONTROL; no first-wave membership or enable intervention | `methodology/PORTFOLIO_RULES.md` Part I §5, lines 251–284; `methodology/PORTFOLIO_RULES.md` Part I §§6–8, lines 288–358 |

## 9. Research axes and independence classification

All 43 original axis definitions remain catalog provenance. **AX-36 (coin allocation) is FIXED_CONTROL_NOT_RESEARCH_VARIABLE for this campaign**; its historical WHAT_CAN_VARY field below describes the pre-correction design space and is not launch authorization. AX-27 is now selected through C-036/R-023. No new axis is minted. Broader frozen configuration permission does not override the narrower campaign constraint.


There are 43 examined non-illegal axis records, including three explicitly redundant/diagnostic mechanisms and context-dependent reserves. The 30 final designs occupy 30 distinct primary axes; this does not prove statistically independent returns. `INDEPENDENT` means independently assignable configuration addresses; `CONDITIONALLY_INDEPENDENT` means separable only after controlling the named shared prerequisites; `COUPLED` means a canonical causal or sizing link; `REDUNDANT` means the contrast adds no distinct trading information.

### AX-01: Displacement magnitude selectivity

```yaml
AXIS_ID: AX-01
MECHANISM: Displacement magnitude selectivity
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'F-001 theta_move_pct: 0.50 -> 1.00'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-001
- C-002
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-02: Participation confirmation

```yaml
AXIS_ID: AX-02
MECHANISM: Participation confirmation
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- F-002 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'F-002 membership: absent -> required'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-003
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-03: Directional efficiency confirmation

```yaml
AXIS_ID: AX-03
MECHANISM: Directional efficiency confirmation
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Additional DE confirmation: absent -> DE>=0.50'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-007
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-04: Central volatility band

```yaml
AXIS_ID: AX-04
MECHANISM: Central volatility band
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Additional central-volatility interval predicate: absent -> inclusive [30,85]'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-008
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-05: Higher-timeframe structural agreement

```yaml
AXIS_ID: AX-05
MECHANISM: Higher-timeframe structural agreement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Side-aligned 1h structural confirmation: absent -> required'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-009
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-06: Raw relative-return agreement

```yaml
AXIS_ID: AX-06
MECHANISM: Raw relative-return agreement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Side-aligned RELATIVE_RETURN_15m sign confirmation: absent -> required'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-010
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-07: Aggressive-flow agreement

```yaml
AXIS_ID: AX-07
MECHANISM: Aggressive-flow agreement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Side-aligned aggressive-flow confirmation: absent -> required'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-011
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-08: BTC contextual agreement

```yaml
AXIS_ID: AX-08
MECHANISM: BTC contextual agreement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Additional BTC_CONTEXT_SCORE sign confirmation
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-012
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-09: Above-normal quote turnover

```yaml
AXIS_ID: AX-09
MECHANISM: Above-normal quote turnover
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Additional TOD_REL_TURNOVER>=1 confirmation
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-013
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-10: Classifier score confidence

```yaml
AXIS_ID: AX-10
MECHANISM: Classifier score confidence
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Additional same-side DIRECTION_SCORE threshold
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-014
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-11: Local-momentum agreement

```yaml
AXIS_ID: AX-11
MECHANISM: Local-momentum agreement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Additional same-side VNM_5m_z sign confirmation
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-015
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-12: New classifier episode

```yaml
AXIS_ID: AX-12
MECHANISM: New classifier episode
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Classifier-direction predicate role: CURRENT_STATE -> same-cutoff FRESH_EVENT'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-016
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-13: Fresh classifier-event age

```yaml
AXIS_ID: AX-13
MECHANISM: Fresh classifier-event age
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Maximum unconsumed classifier-event age: 5 -> 10 minutes'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-017
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-14: Since-arming freshness modifier

```yaml
AXIS_ID: AX-14
MECHANISM: Since-arming freshness modifier
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Add SINCE_SET_ARMED to same-epoch fresh event
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
INDEPENDENCE_CLASS: REDUNDANT
CANDIDATES:
- C-018
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-15: Ordered price then participation

```yaml
AXIS_ID: AX-15
MECHANISM: Ordered price then participation
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- F-002 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Trigger composition: simultaneous AND -> strict ordered sequence'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§11–12
  SOURCE_LINES: 1213–1243
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-019
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-16: Direction maintained through formation

```yaml
AXIS_ID: AX-16
MECHANISM: Direction maintained through formation
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- F-002 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Maintained classifier direction: endpoint-only -> all intervening completed-5m evaluations'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §13
  SOURCE_LINES: 1247–1259
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§11–12
  SOURCE_LINES: 1213–1243
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-020
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-17: Participation conjunction versus disjunction

```yaml
AXIS_ID: AX-17
MECHANISM: Participation conjunction versus disjunction
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- F-002 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Participation composition: AND -> OR with identical member predicates'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-021
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-18: Two of three confirmations

```yaml
AXIS_ID: AX-18
MECHANISM: Two of three confirmations
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Boolean expression: all three -> any pair of F-002, TOD and flow'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§14–22
  SOURCE_LINES: 1263–1550
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-022
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-19: Longer formation expiry

```yaml
AXIS_ID: AX-19
MECHANISM: Longer formation expiry
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: 'Sequence expiry: 10 -> 20 minutes'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§11–12
  SOURCE_LINES: 1213–1243
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§14–22
  SOURCE_LINES: 1263–1550
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-023
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-20: Alternative re-arm policy

```yaml
AXIS_ID: AX-20
MECHANISM: Alternative re-arm policy
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Re-arm policy
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-024
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-21: Session-scoped re-arm

```yaml
AXIS_ID: AX-21
MECHANISM: Session-scoped re-arm
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Re-arm policy -> NEXT_SESSION
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§30–36
  SOURCE_LINES: 4304–4486
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-025
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-22: GENERIC versus TREND label

```yaml
AXIS_ID: AX-22
MECHANISM: GENERIC versus TREND label
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: SET_LAYER
WHAT_CAN_VARY: Set family GENERIC -> TREND_CONTINUATION; all thesis modes NONE
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
INDEPENDENCE_CLASS: REDUNDANT
CANDIDATES:
- C-026
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-23: Entry minimum improvement

```yaml
AXIS_ID: AX-23
MECHANISM: Entry minimum improvement
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MIN_ENTRY_IMPROVEMENT_ATR -> 0.25
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-031
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-24: Entry maximum deviation

```yaml
AXIS_ID: AX-24
MECHANISM: Entry maximum deviation
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MAX_ENTRY_DEVIATION_ATR -> 2.00
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-032
- C-033
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-25: Dynamic versus fixed Stop dispatch

```yaml
AXIS_ID: AX-25
MECHANISM: Dynamic versus fixed Stop dispatch
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_supported_fields.stop_loss.mode -> FIXED
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-034
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-26: Dynamic Stop buffer

```yaml
AXIS_ID: AX-26
MECHANISM: Dynamic Stop buffer
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.BUFFER_ATR_MULTIPLIER -> 0.40
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-035
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-27: Dynamic Stop minimum risk

```yaml
AXIS_ID: AX-27
MECHANISM: Dynamic Stop minimum risk
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MIN_DISTANCE_ATR -> 0.75
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-036
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-28: Dynamic Stop maximum risk

```yaml
AXIS_ID: AX-28
MECHANISM: Dynamic Stop maximum risk
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MAX_DISTANCE_ATR -> 1.50
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-037
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-29: Stop corroboration diagnostic

```yaml
AXIS_ID: AX-29
MECHANISM: Stop corroboration diagnostic
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.CORROBORATION_DISTANCE_ATR -> 0.50
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
INDEPENDENCE_CLASS: REDUNDANT
CANDIDATES:
- C-038
STATUS: RESERVE_OR_NON_EXECUTABLE
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-30: Dynamic TP minimum distance

```yaml
AXIS_ID: AX-30
MECHANISM: Dynamic TP minimum distance
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MIN_TP_DISTANCE_ATR -> 1.25
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-039
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-31: Dynamic TP maximum distance

```yaml
AXIS_ID: AX-31
MECHANISM: Dynamic TP maximum distance
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_parameter_bindings.MAX_TP_DISTANCE_ATR -> 3.00
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-040
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-32: Structural reward-to-risk gate

```yaml
AXIS_ID: AX-32
MECHANISM: Structural reward-to-risk gate
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_supported_fields.minimum_risk_reward.enabled -> True
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §39
  SOURCE_LINES: 1332–1366
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-041
- C-048
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-33: Planned net-edge gate

```yaml
AXIS_ID: AX-33
MECHANISM: Planned net-edge gate
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_supported_fields.minimum_net_edge.enabled -> True
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §40
  SOURCE_LINES: 1370–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-042
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-34: Leverage in exact construction

```yaml
AXIS_ID: AX-34
MECHANISM: Leverage in exact construction
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: POSITION_RULES
WHAT_CAN_VARY: methodology_supported_fields.leverage.value -> 2
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §22
  SOURCE_LINES: 837–880
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-043
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-35: Global own-capital cap

```yaml
AXIS_ID: AX-35
MECHANISM: Global own-capital cap
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.max_capital_in_positions_pct -> 40
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-049
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-36: Coin allocation target and cap

```yaml
AXIS_ID: AX-36
MECHANISM: Coin allocation target and cap
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.coins.1.allocation_pct -> 30
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-050
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-37: Global slot pressure

```yaml
AXIS_ID: AX-37
MECHANISM: Global slot pressure
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.max_open_positions -> 3
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-051
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-38: Per-coin slots and grant division

```yaml
AXIS_ID: AX-38
MECHANISM: Per-coin slots and grant division
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.max_positions_per_coin -> 3
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-052
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-39: Minimum tranche capital

```yaml
AXIS_ID: AX-39
MECHANISM: Minimum tranche capital
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.minimum_tranche_capital -> 50
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-053
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-40: Acceptance-based cooldown

```yaml
AXIS_ID: AX-40
MECHANISM: Acceptance-based cooldown
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.cooldown_minutes -> 15
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
INDEPENDENCE_CLASS: CONDITIONALLY_INDEPENDENT
CANDIDATES:
- C-054
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-41: Daily realized-loss latch

```yaml
AXIS_ID: AX-41
MECHANISM: Daily realized-loss latch
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: PORTFOLIO_RULES
WHAT_CAN_VARY: methodology_supported_fields.daily_loss_limit.enabled -> True
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-055
- C-056
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-42: Participation × cooldown interaction

```yaml
AXIS_ID: AX-42
MECHANISM: Participation × cooldown interaction
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- F-002 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: CROSS_LAYER_INTERACTION
WHAT_CAN_VARY: 'Joint factorial contrast: F-002 membership × cooldown_minutes'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-059
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

### AX-43: Displacement threshold × Entry depth

```yaml
AXIS_ID: AX-43
MECHANISM: Displacement threshold × Entry depth
UNDERLYING_METRICS:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- ATR_15m
- ATR_PCT_15m
- ATR_PCT_5m
- ATR_PCT_work
- ATR_work
- A_t_5m
- AggBuyNotional
- AggSellNotional
- BTC_CONTEXT_SCORE
- BTC_MOMENTUM_SCORE
- BTC_RETURN_Z
- BTC_STRUCTURE_SCORE
- BTC_VETO_LONG
- BTC_VETO_SHORT
- DE
- DE_STRENGTH
- DIRECTION_SCORE
- Entry candidate classification
- F-001 trigger_result
- FLOW_EFFECTIVE
- FLOW_RAW
- LOCAL_MOMENTUM_VETO_LONG
- LOCAL_MOMENTUM_VETO_SHORT
- MOMENTUM_EFFECTIVE
- MOMENTUM_SCORE
- PARTICIPATION_STRENGTH
- PREVIOUS_DAY_HIGH
- PREVIOUS_DAY_LOW
- RELATIVE_RETURN_15m
- RELATIVE_SCORE
- RELATIVE_VETO_LONG
- RELATIVE_VETO_SHORT
- RETURN(BTC,15m)
- RETURN(asset,15m)
- RETURN(asset,5m)
- STRUCTURE_15M
- STRUCTURE_1H
- STRUCTURE_SCORE
- SWING_HIGH_15M
- SWING_HIGH_1H
- SWING_LOW_15M
- SWING_LOW_1H
- SWING_SEQUENCE_STATE(BTC,1h)
- SWING_SEQUENCE_STATE(asset,15m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- TR_15m
- VNM_15m
- VNM_5m
- VNM_5m_z
- actual_committed_capital
- actual_committed_capital_exact
- actual_fees_rebates
- actual_order_notional
- age_seconds
- allocated_funding
- buffer_price
- classifier_direction
- coin_allocation_cap[symbol]
- coin_committed_tranches
- committed_coin_capital
- committed_global_capital
- cooldown_until[symbol]
- corroborating_level_ids[]
- current_portfolio_equity
- daily_loss_limit_amount
- daily_loss_status
- daily_loss_used_amount_d
- daily_portfolio_base
- daily_realized_pnl
- direction_classifier.gates.activity.passed
- direction_classifier.gates.data_available.passed
- direction_classifier.gates.directional_efficiency.passed
- direction_classifier.gates.volatility.passed
- direction_classifier.primary_rejection_stage
- distance_atr_15m
- distance_pct
- distance_price
- expected_entry_fee
- expected_sl_exit_fee
- expected_tp_exit_fee
- final_qty
- first_too_far_distance_atr
- free_coin_capital
- free_global_capital
- global_committed_tranches
- global_position_cap
- gross_loss_sl
- gross_profit_tp
- gross_realized_trading_result
- gross_rr
- improvement_atr
- improvement_pct
- improvement_price
- lifecycle_state
- logical_committed_capital[tranche]
- margin_required
- minimum_distance_adjustment_applied
- minimum_distance_price
- momentum_z
- net_edge_pct
- net_loss_sl
- net_profit_tp
- net_realized_result
- net_rr
- other_supported_exchange_costs
- planned_entry_reference
- pre_rounding_risk_atr
- pre_rounding_risk_price
- raw_qty
- relative_position.side
- relative_return_z
- remaining_coin_slots
- remaining_global_slots
- requested_capital_per_tranche
- reward_distance_pct
- reward_distance_price
- risk_distance_pct
- risk_distance_price
- selection_terminated_by_too_far
- set_match_reference_price
- sl_exit_notional
- sl_total_cost
- stop_loss_price
- take_profit_price
- target distance ATR
- target_order_notional
- tick_size
- too_close_skipped_count
- total_pnl
- total_triggertrade_open_notional_for_symbol_side_at_funding_time
- tp_exit_notional
- tp_total_cost
- tranche_open_notional_at_funding_time
- unrealized_pnl
AFFECTED_LAYER: CROSS_LAYER_INTERACTION
WHAT_CAN_VARY: 'Joint factorial contrast: F-001 theta_move_pct × MAX_ENTRY_DEVIATION_ATR'
WHAT_MUST_REMAIN_CONTROLLED: All configuration content outside the named contrast, source/version/cutoff policies,
  selected run interval, data manifests, initial wallet/native-side state, and evidence rules. Endogenous downstream
  effects are not claimed to be held fixed.
DEPENDENCIES:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
INDEPENDENCE_CLASS: COUPLED
CANDIDATES:
- C-060
STATUS: PROVISIONAL_COVERED
QUALIFICATION: Semantic/configuration independence only; not observed PnL independence.
```

## 10. Dependency graph and coupled variables

The inherited F-004/F-005 subgraph applies only to non-BTC subjects. The new BTC subgraph is `actual completed 5m closes → existing RETURN(asset=BTC,5m) → strict side predicate → generic Set branch direction → same MARKET_HANDOFF`. Existing DE/ATR-percentile/TOD floors and pending BTC_CONTEXT_SCORE are separate required predicates. These are common subject contexts, not separate interventions. `ambiguity → unresolved Portfolio state → censored dependent suffix → unavailable full-window comparison` is a research evidence/report dependency, not a canonical trading-state extension.


| From | To | Relation | Implication | Source |
|---|---|---|---|---|
| 1m completed closes | F-001 trigger_result | DIRECT | F-001 theta only; sign not direction | `methodology/SET.md` Part I §8A, lines 617–843 |
| current + 60 prior 1m base volumes | F-002 trigger_result | DIRECT | Fixed R/P; local intermediates not independent outputs | `methodology/SET.md` Part I §8B, lines 847–1078 |
| 15m HLC + authentic history | ATR_work -> ATR_PCT_work -> ATR percentile | DIRECT | ATR export and work state distinct; positive handoff constraint | `methodology/SET.md` Part II §§13–15, lines 2410–2508; `schemas/SET_NUMERIC_POLICY.md` §§1–7, lines 19–110 |
| completed 15m closes | DE -> DE_STRENGTH -> MOMENTUM_EFFECTIVE | COUPLED | Extra DE confirmation is conditional on its existing score role | `methodology/SET.md` Part II §§11–12, lines 2317–2405; `methodology/SET.md` Part II §§16–18, lines 2512–2697 |
| same-clock 5m quote turnover | TOD_REL_TURNOVER -> PARTICIPATION_STRENGTH -> FLOW_EFFECTIVE | COUPLED | Activity gate and score modifier share one input | `methodology/SET.md` Part II §8, lines 2013–2131; `methodology/SET.md` Part II §§21–23, lines 2760–2858 |
| confirmed swing states, momentum, relative, flow, BTC | DIRECTION_SCORE -> F-005 | COUPLED | Fixed five-factor weights; F-005 also consumes gates and vetoes | `methodology/SET.md` Part II §§31–34, lines 3050–3150; `methodology/SET.md` Part II §§34A–37, lines 3155–3435 |
| F-005 and research predicates | Set expression / formation -> MATCHED | PREREQUISITE | Classifier direction alone is not a committed match | `methodology/SET.md` Part II §§34A–37, lines 3155–3435; `methodology/SET.md` Part I §§14–22, lines 1263–1550 |
| MATCHED / canonical references / Set role bindings | frozen MARKET_HANDOFF | PREREQUISITE | No future or replacement reference producer | `methodology/SET.md` Part III §§3–10, lines 3520–3718; `methodology/SET.md` Part III §43.1, lines 4769–4801 |
| frozen MARKET_HANDOFF | Entry -> Stop dispatch and Dynamic TP | COUPLED | TP is computed independently from eligible favorable geometry, not manufactured from Stop/RR | `methodology/POSITION_RULES.md` Part I §14, lines 465–517; `methodology/POSITION_RULES.md` Part II §§3–31, lines 2142–2759; `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974; `methodology/POSITION_RULES.md` Part IV §§3–32, lines 4320–5056 |
| Entry + Stop + TP | gross_rr opportunity gate | DIRECT | Must precede grant, unlike net-edge gate | `methodology/POSITION_RULES.md` Part I §39, lines 1332–1366; `methodology/POSITION_RULES.md` Part I §14, lines 465–517 |
| Portfolio base/caps/slots | requested_capital_per_tranche | COUPLED | Per-coin slots are divisor; global slots are admission-only | `methodology/PORTFOLIO_RULES.md` Part II §§11–17, lines 484–633; `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772 |
| grant + leverage + Entry + quantity grid | final_qty / actual_notional / actual_committed_capital | COUPLED | Exact quantity floor; ceiling liability; hold equals actual committed capital | `methodology/POSITION_RULES.md` Part I §§17–22A, lines 576–908; `schemas/NUMERIC_POLICY.md` §§1–7, lines 8–94 |
| final size + geometry + factual fee rates | net_edge_pct construction gate | COUPLED | Notional denominator; funding excluded; leverage and rounding may matter | `methodology/POSITION_RULES.md` Part I §§23–40, lines 912–1436; `methodology/POSITION_RULES.md` Part I §40, lines 1370–1436 |
| immutable spec + authorization | native acceptance / Lifecycle | PREREQUISITE | No submit from only one authorization half | `methodology/POSITION_RULES.md` Part I §14, lines 465–517; `methodology/ORDER_LIFECYCLE.md` §7, lines 522–595; `api-contracts/NATIVE_FACT_PROFILE.md` §§1–5 and financial conformance, lines 1–41 |
| proven native accepted_at | cooldown_until and ORDER_PLACED monitor activation | COUPLED | Configured delay cannot start at local submit/fill time | `methodology/PORTFOLIO_RULES.md` Part II §§24–27, lines 876–980; `methodology/SET.md` Part IV §§12–12A, lines 4879–5162; `api-contracts/NATIVE_FACT_PROFILE.md` §§1–5 and financial conformance, lines 1–41 |
| original frozen hard conditions | cancel unfilled entry remainder | DIRECT | Not a new Set match or filled-position exit | `methodology/SET.md` Part IV §§12–12A, lines 4879–5162 |
| complete actual execution/cost/funding | FINAL net_realized_result -> immutable accounting day receipt | PREREQUISITE | No estimated fees, FX or premature zero-exposure closure | `methodology/ORDER_LIFECYCLE.md` §§33–34, lines 1343–1377; `methodology/ORDER_LIFECYCLE.md` §32, lines 1208–1339; `SYSTEM_PROTOCOLS.md` P6–P8, lines 114–220 |
| FINAL current-day receipts | daily_realized_pnl -> Daily Loss latch -> future exposure | COUPLED | Cross-trade path dependence, never unrealized summands | `methodology/PORTFOLIO_RULES.md` Part II §23, lines 776–872 |
| separate metric producers F-001 and F-002 | two distinct participation/displacement mechanisms | CONDITIONALLY_INDEPENDENT | Different input constructs; market-return correlation not measured | `methodology/SET.md` Part I §8A, lines 617–843; `methodology/SET.md` Part I §8B, lines 847–1078 |
| global slot limit vs gross R:R configured threshold | different assigned parameters | INDEPENDENT | Configuration-address independence only; outcomes remain coupled through admission | `methodology/PORTFOLIO_RULES.md` Part II §§18–22, lines 638–772; `methodology/POSITION_RULES.md` Part I §39, lines 1332–1366 |
| GENERIC vs TREND_CONTINUATION label under identical no-thesis hierarchy | same baseline selection | REDUNDANT | No information gain from label alone | `methodology/POSITION_RULES.md` Part II §§3–31, lines 2142–2759; `methodology/SET.md` Part III §43.1, lines 4769–4801 |
| corroborating-level distance | same actual Stop with changed diagnostic | REDUNDANT | Not a distinct trading rule | `methodology/POSITION_RULES.md` Part III §§3–30, lines 3316–3974 |

Do not vary Entry depth and Stop/TP parameters together in a nominal one-factor test. Do not vary per-coin slots while artificially fixing grant size. Do not vary leverage while treating notional/quantity/grid effects as independent. Do not change Daily Loss and its accounting clock or add unrealized PnL. Do not change F-002 thresholds while testing membership. Do not change score weights while adding a factor confirmation. A proposed result dependency is not evidence that two assigned parameters were both changed. The two selected cross-layer studies retain four cells each.


## 11. Preserved candidate-generation history; current selection application

The original60 candidate IDs and historical1,770 pair judgments are unchanged. R2 selected C-036 for R-023; that correction remains. The approved subsequent selection now demotes C-049 and C-053 to source-valid historical/conditional reserves and selects existing C-012/C-015 at R-022/R-026. Only57 affected final relationships change overlay;378 retained judgments are preserved. Current final counts:13 Set /11 Position /4 Portfolio /2 cross-layer;387 LOW /48 MEDIUM /0 HIGH /0 NEAR_DUPLICATE. No empirical performance or parameter optimization was used.

## 12. R3 focused application and source dependencies

| Research | Current candidate / original axis | Non-BTC baseline / variant | BTC baseline / variant | Position / Portfolio |
|---|---|---|---|---|
| R-022 | C-012 / AX-08 | SET-R-001-V1 / SET-R-012-V2 | SET-R-BTC-001-V1 / SET-R-BTC-012-V2 | POS-R-001 / PR-R-201, both arms |
| R-026 | C-015 / AX-11 | SET-R-001-V1 / SET-R-015-V2 | SET-R-BTC-001-V1 / SET-R-BTC-015-V2 | POS-R-001 / PR-R-201, both arms |

Both new BTC variants explicitly derive from the unchanged BTC baseline and instantiate the original inclusive CURRENT_STATE predicate under DB-R-BTC-001, never under F-005. No new Trigger ID or canonical metric is required. Existing39 Trigger definitions,36 Set definitions,16 Position and9 corrected Portfolio bodies are preserved; exactly2 Set definitions are added.

**C-012:** BTC_CONTEXT_SCORE >=0 LONG / <=0 SHORT. Preserve SET Part II §§24–27 L2863–2958, weights/veto thresholds and source timing. Zero is compatible; missing context is UNAVAILABLE. BTC subset dependence with R-005 is explicit; nine non-BTC subjects use external BTC context rather than their own1h structure.

**C-015:** VNM_5m_z >=0 LONG / <=0 SHORT. `WEB_RESEARCH_CONFIGURATION_MODEL.md` §5.R3.D pins the complete existing BTC-local5m dependency: completed source closes → RETURN(5m); separate5m true-range/Wilder14 anchor/seed/checkpoint → ATR_PCT_5m → VNM_5m → same-symbol completed-UTC-day population → arithmetic mean/population-ddof0 stddev → centered work-grid z. Frozen source: SET Part II §5 L1804–1832, §§6–7 L1836–2011, §16.2 L2561–2648; SET_NUMERIC_POLICY §§1–7. No15m ATR/raw-return shortcut, skipped later missing days, current-day population, synthetic source or sigma-zero fallback. Zero-mean nonbinding BTC activation is retained as evidence, never repaired by tuning.

**Controls versus current intervention:** global own-capital cap and minimum tranche capital remain canonical/operative Portfolio controls in PR-R-201 and historical variants. They are no longer current first-wave axes. Current Portfolio studies are R-024 global slots, R-025 per-coin slots/grant division, R-027 cooldown and R-028 Daily Loss. No allocation or new Portfolio field is introduced.

**Activation evidence:** retain valid predicate disagreement separately from source unavailability, then Set/Position/Portfolio disposition, dispatch/fill/finality/report membership and completeness. Original non-BTC veto results are retained where produced; BTC never fabricates classifier gate/veto outputs. Context/pullback economics and activation are unmeasured; MEDIUM selection confidence is provenance, not a profitability finding.

**Regressions explicitly excluded:** R-010 remains unchanged/conditional; R-023 remains C-036; the original14 BTC Sets and all other28 mappings remain identical; no synthetic OHLC path, fake FINAL/capital release or resolved-only full-window reporting; research-record export and human-only authority are unchanged.

## 13. Immutable provenance and dependency scope

R3 research revision is separate from preserved R2 execution/report/evidence semantic identities. Existing28 record experimental payloads match R2 exactly after excluding only revision/predecessor/current-overlap metadata. New BTC Set content digests and dependency binding digest use the normalized authority's compact sorted-key UTF-8 JSON rule. All prior R1/R2 packages and five reviews are retained under HISTORICAL_PROVENANCE; historical counts/findings never override R3.
