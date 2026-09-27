# TriggerTrade — Normalized Web Research Configuration Model — Corrected R3

**OPERATIVE_R3 — `RESEARCH_V1_FOCUSED_CORRECTION_R3`. Status: APPROVED — specification-level package correction only.**

Exactly the two approved assignments are applied: **R-022 = C-012, BTC contextual agreement (AX-08)**; **R-026 = C-015, Local-momentum agreement (AX-11)**. The other 28 questions, treatments, Set mappings, Position/Portfolio configurations and BTC applicability are unchanged. R-023 remains C-036; R-010 retains its unchanged definition and conditional first-wave economic-audit qualification.

Current counts: **30 valid hypotheses; 13 Set / 11 Position / 4 Portfolio / 2 cross-layer**. Sixty candidates remain. Ten fixed 10% allocations total exactly 100%; R-006 BTC remains NOT_APPLICABLE without redistribution. The frozen v1.2.15 archive SHA-256 is `3b38c09c6f52daa77d7cc4257a3c420b21d76ac10d039dd708dd205af963b326` and its bytes are unchanged.

Package/research identity is R3. Existing immutable execution-semantic pins (`profile_revision=RESEARCH_V1_FOCUSED_CORRECTION_R2`), `REPORT-R-V1-R2`, `EVIDENCE-R-V1-R2`, and `DEC-R-001`/R2 deliberately remain unchanged contracts. They do **not** select an R2 hypothesis: launch always resolves the R3 research revision separately. Existing Set/Trigger/configuration revisions and digests are not relabeled. The current profile document explains this compatibility explicitly. No old/new hypothesis runs are pooled.

Authority: frozen methodology; unchanged R2 package; focused BTC/intrabar council; R2 economic and pairwise audits; approved replacement selection and pairwise review; current mechanical-correction instruction. Only `operative/` is current configuration. `provenance/` is HISTORICAL_PROVENANCE. No Backtest, Demo, native API, data availability, statistical independence or profitability is certified.

## 1. Ownership and normalization

This is a declarative specification, not source code, a database migration or a claim of deployed Web APIs. The normalization key for a research is `(research_id, research_revision)`; for a run it includes its immutable run/arm/source/profile/configuration identities. A symbol-to-Set map is explicit. Reporting and evidence metadata are joined envelopes outside canonical wires and cannot feed trading decisions.

| Entity | Key | References / scope |
|---|---|---|
| Canonical metric reference | source-qualified existing name | Inventory source/section, type, unit, availability, numeric policy; no new calculation |
| Research trigger definition | trigger_id | Existing metric binding, typed operator/value, horizon and event/current-state role |
| Trigger instance | Set version + predicate reference + symbol | Canonical predicate body unchanged; enclosing direction prerequisite resolved by Set scope |
| Set version | set_version | Direction authority, full expression, formation/reset/context/pending condition, predecessor digest |
| Symbol binding | research revision + arm + symbol | Exact Set version or explicit NOT_APPLICABLE; no implicit F005 fallback |
| Position config | config_id | Original unchanged supported fields/research calibration bindings |
| Portfolio config | config_id | Corrected201–209; each10%, exact100; old1xx historical only |
| Research hypothesis | research_id + revision | Question, axis, assigned contrast, candidate provenance; R022/R026 R3 and historical R023 revision transitions explicit |
| Run | run_id | One of4 run types, arm, full resolved config/source/profile manifest, endpoint/state history |
| Report/Compare | report_id + revision | Run/population/frontier/completeness, fixedcolumnorder, selected ACTIVE snapshot |
| Resolution / ambiguity | resolution_id / frontier_id | Research-only source order/refinement/causal record; no canonical state extension |
| Export | research_id + export_revision | Entire reachable Research-record evidence graph, all runs/revisions, content closure |
| Human decision | decision_record_id | User action, selected references, provenance; no system winner |

## 2. Representation, immutability and direction scope

Exact decimal configuration values are strings. Canonical Boolean/enums remain typed. Required UNAVAILABLE is never numeric zero or FALSE. Reference resolution fails on missing or conflicting IDs rather than guessing. `NOT_APPLICABLE` is research scope metadata, not a canonical lifecycle status. A type-correct launch input is manually bound and captured before run start; missing real historical/native data can make a run unavailable without making the specification undefined.

New corrected configurations include SHA-256 over their declarative object excluding the `content_sha256` member, encoded as compact UTF-8 JSON with sorted object keys, preserved array order and no ASCII escaping. This is content-addressing for evidence, not a trading formula. Original object bodies and IDs remain unchanged; do not overwrite old histories. Profile/Set/Portfolio corrections create new IDs/revisions. No first-wave arm uses PR-R-101…109 or the unselected PR-R-203 alias.

Common TR-R-001…031 predicates preserve their original bodies. Where their original narrative says current F-005 is required at MATCHED, that is the original enclosing governed Set prerequisite. New BTC Set versions explicitly instantiate those same metric/operator/value/freshness predicates under DB-R-BTC-001; their `trigger_instances` record that scope resolution. The canonical metric dependencies are unchanged. No F005 requirement or classifier diagnostics may leak into a BTC instance. The nine non-BTC Set/Trigger definitions are unchanged.

## 3. Canonical metric-reference registry

The full metadata inventory is artifact A §3; the compact normalized lookup below resolves every metric referenced by a trigger or final research result. Qualified instance names are mapped to their exact source sections; no new metric ID is minted.

| Metric reference | Type / unit | Canonical owner | Used by trigger IDs | Source |
|---|---|---|---|---|
| F-001 trigger_result | tri-state; none | Set | TR-R-001, TR-R-002, TR-R-024, TR-R-029, TR-R-030, TR-R-031 | methodology/SET.md Part I §8A L617–843 |
| move_pct_work | signed decimal; percent; 1 means 1% | Set | Result/dependency only | methodology/SET.md Part I §8A L617–843 |
| F-001 sign_evidence | enum UP / DOWN / FLAT; none | Set | Result/dependency only | methodology/SET.md Part I §8A L617–843 |
| F-002 trigger_result | tri-state; none | Set | TR-R-003 | methodology/SET.md Part I §8B L847–1078 |
| F-002.M | decimal; base-coin volume | Set | Result/dependency only | methodology/SET.md Part I §8B L847–1078 |
| F-002.K | integer 0..60; count | Set | Result/dependency only | methodology/SET.md Part I §8B L847–1078 |
| F-002.R | exact ratio; dimensionless | Set | Result/dependency only | methodology/SET.md Part I §8B L847–1078 |
| F-002.P | exact ratio; percent | Set | Result/dependency only | methodology/SET.md Part I §8B L847–1078 |
| TR_15m | nonnegative decimal; price | Set | Result/dependency only | methodology/SET.md Part II §§13–15 L2410–2508; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR_work | nonnegative decimal; price | Set | Result/dependency only | methodology/SET.md Part II §§13–15 L2410–2508; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR_15m | nonnegative decimal; price | Set | Result/dependency only | methodology/SET.md Part II §§13–15 L2410–2508; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR_PCT_work | nonnegative decimal; percent | Set | Result/dependency only | methodology/SET.md Part II §§13–15 L2410–2508; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR_PCT_15m | nonnegative decimal; percent | Set | Result/dependency only | methodology/SET.md Part II §§13–15 L2410–2508; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR percentile | numeric 0..100; percentile rank | Set | TR-R-007, TR-R-008, TR-R-BTC-006, TR-R-BTC-007 | methodology/SET.md Part II §§13–15 L2410–2508; methodology/SET.md Part II §§3–6 L1739–1961 |
| SWING_HIGH_15M | governed level object; price and factual timestamps | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313; methodology/SET.md Part III §§12–22 L3757–4059 |
| SWING_LOW_15M | governed level object; price and factual timestamps | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313; methodology/SET.md Part III §§12–22 L3757–4059 |
| SWING_HIGH_1H | governed level object; price and factual timestamps | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313; methodology/SET.md Part III §§12–22 L3757–4059 |
| SWING_LOW_1H | governed level object; price and factual timestamps | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313; methodology/SET.md Part III §§12–22 L3757–4059 |
| SWING_SEQUENCE_STATE(asset,1h) | enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE; none | Set | TR-R-009, TR-R-010 | methodology/SET.md Part II §§9–10 L2136–2313 |
| SWING_SEQUENCE_STATE(asset,15m) | enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE; none | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313 |
| SWING_SEQUENCE_STATE(BTC,1h) | enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE; none | Set | Result/dependency only | methodology/SET.md Part II §§9–10 L2136–2313 |
| RETURN(asset,15m) | signed decimal; fractional return | Set | Result/dependency only | methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958 |
| RETURN(BTC,15m) | signed decimal; fractional return | Set | Result/dependency only | methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958 |
| RETURN(asset,5m) | signed decimal; fractional return | Set | TR-R-BTC-001, TR-R-BTC-002, TR-R-BTC-003, TR-R-BTC-004 | methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958 |
| DE | numeric 0..1; dimensionless | Set | TR-R-006, TR-R-BTC-005 | methodology/SET.md Part II §§11–12 L2317–2405 |
| DE_STRENGTH | numeric 0..1; dimensionless | Set | Result/dependency only | methodology/SET.md Part II §§11–12 L2317–2405 |
| VNM_15m | decimal; dimensionless | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| momentum_z | decimal; z-score | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| MOMENTUM_SCORE | decimal; bounded -1..1 | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| MOMENTUM_EFFECTIVE | decimal; bounded -1..1 | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| A_t_5m | decimal; price | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| ATR_PCT_5m | decimal; percent | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| VNM_5m | decimal; dimensionless | Set | Result/dependency only | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| VNM_5m_z | decimal; z-score | Set | TR-R-022, TR-R-023 | methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110 |
| RELATIVE_RETURN_15m | signed decimal; fractional return / z / bounded score, respectively | Set | TR-R-011, TR-R-012 | methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§3–6 L1739–1961 |
| relative_return_z | signed decimal; fractional return / z / bounded score, respectively | Set | Result/dependency only | methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§3–6 L1739–1961 |
| RELATIVE_SCORE | signed decimal; fractional return / z / bounded score, respectively | Set | Result/dependency only | methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§3–6 L1739–1961 |
| AggBuyNotional | decimal; quote notional | Set | Result/dependency only | methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46 |
| AggSellNotional | decimal; quote notional | Set | Result/dependency only | methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46 |
| AGGRESSIVE_VOLUME_DELTA_PCT | decimal; percent | Set | TR-R-013, TR-R-014 | methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46 |
| FLOW_RAW | decimal; fraction | Set | Result/dependency only | methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46 |
| FLOW_EFFECTIVE | decimal; bounded score | Set | Result/dependency only | methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46 |
| TOD_REL_TURNOVER | nonnegative numeric; ratio | Set | TR-R-017, TR-R-BTC-008 | methodology/SET.md Part II §8 L2013–2131; methodology/SET.md Part II §§21–23 L2760–2858 |
| PARTICIPATION_STRENGTH | numeric 0..1; dimensionless | Set | Result/dependency only | methodology/SET.md Part II §§21–23 L2760–2858 |
| BTC_STRUCTURE_SCORE | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| BTC_RETURN_Z | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| BTC_MOMENTUM_SCORE | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| BTC_CONTEXT_SCORE | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | TR-R-018, TR-R-019 | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| STRUCTURE_1H | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| STRUCTURE_15M | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| STRUCTURE_SCORE | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | Result/dependency only | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| DIRECTION_SCORE | numeric; z-score for BTC_RETURN_Z; otherwise bounded score | Set | TR-R-020, TR-R-021 | methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435 |
| BTC_VETO_LONG | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| BTC_VETO_SHORT | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| RELATIVE_VETO_LONG | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| RELATIVE_VETO_SHORT | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| LOCAL_MOMENTUM_VETO_LONG | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| LOCAL_MOMENTUM_VETO_SHORT | Boolean with availability; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§16–18 L2512–2697 |
| classifier_direction | enum LONG / SHORT / NONE; none | Set | TR-R-004, TR-R-005, TR-R-015, TR-R-016, TR-R-025, TR-R-026, TR-R-027, TR-R-028 | methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part I §5 L509–530 |
| direction_classifier.gates.data_available.passed | Boolean / reason enum as named; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435 |
| direction_classifier.gates.directional_efficiency.passed | Boolean / reason enum as named; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435 |
| direction_classifier.gates.activity.passed | Boolean / reason enum as named; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435 |
| direction_classifier.gates.volatility.passed | Boolean / reason enum as named; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435 |
| direction_classifier.primary_rejection_stage | Boolean / reason enum as named; none | Set | Result/dependency only | methodology/SET.md Part II §§34A–37 L3155–3435 |
| Set formation state | INACTIVE / ARMED / PARTIALLY_MATCHED / MATCHED / EXPIRED / RESET / UNAVAILABLE; none | Set | Result/dependency only | methodology/SET.md Part I §§14–22 L1263–1550 |
| Pending monitor state | MONITORING_INACTIVE / MONITORING_ACTIVE / INVALIDATED / MONITORING_STOPPED / MONITORING_UNAVAILABLE; none | Set | Result/dependency only | methodology/SET.md Part I §§14–22 L1263–1550 |
| pending_validity | VALID / INVALID / UNAVAILABLE / STOPPED; none | Set | Result/dependency only | methodology/SET.md Part IV §§12–12A L4879–5162 |
| Frozen hard-condition evaluation | TRUE / FALSE / UNAVAILABLE / INVALID_CONDITION; none | Set | Result/dependency only | methodology/SET.md Part IV §§12–12A L4879–5162 |
| set_match_reference_price | decimal / enum / integer as named; price | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| tick_size | decimal / enum / integer as named; price increment | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| PREVIOUS_DAY_HIGH | decimal / enum / integer as named; price | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| PREVIOUS_DAY_LOW | decimal / enum / integer as named; price | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| relative_position.side | decimal / enum / integer as named; enum | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| distance_price | decimal / enum / integer as named; price | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| distance_pct | decimal / enum / integer as named; percent | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| distance_atr_15m | decimal / enum / integer as named; ATR multiple | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| age_seconds | decimal / enum / integer as named; integer seconds | Set | Result/dependency only | methodology/SET.md Part III §§3–10 L3520–3718; methodology/SET.md Part III §§12–22 L3757–4059 |
| handoff_capabilities.reference_price | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.tick_geometry | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.volatility_scale | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.downside_geometry | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.upside_geometry | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.dynamic_sl_base | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| handoff_capabilities.dynamic_tp_base | available Boolean + reason; none | Set | Result/dependency only | methodology/SET.md Part III §§24–28 L4101–4276 |
| planned_entry_reference | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part II §§3–31 L2142–2759 |
| improvement_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part II §§3–31 L2142–2759 |
| improvement_pct | source-defined scalar / enum / collection; percent | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part II §§3–31 L2142–2759 |
| improvement_atr | source-defined scalar / enum / collection; ATR multiple | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part II §§3–31 L2142–2759 |
| Entry candidate classification | source-defined scalar / enum / collection; TOO_SHALLOW / ELIGIBLE / TOO_DEEP | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part II §§3–31 L2142–2759 |
| stop_loss_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§9–10 L274–365 |
| buffer_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| minimum_distance_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| minimum_distance_adjustment_applied | source-defined scalar / enum / collection; Boolean | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| pre_rounding_risk_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| pre_rounding_risk_atr | source-defined scalar / enum / collection; ATR multiple | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| corroborating_level_ids[] | source-defined scalar / enum / collection; reference IDs, diagnostic-only | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part III §§3–30 L3316–3974 |
| take_profit_price | source-defined scalar / enum / collection; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part IV §§3–32 L4320–5056 |
| target distance ATR | source-defined scalar / enum / collection; ATR multiple | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part IV §§3–32 L4320–5056 |
| too_close_skipped_count | source-defined scalar / enum / collection; integer count | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part IV §§3–32 L4320–5056 |
| selection_terminated_by_too_far | source-defined scalar / enum / collection; Boolean | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part IV §§3–32 L4320–5056 |
| first_too_far_distance_atr | source-defined scalar / enum / collection; ATR multiple | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part IV §§3–32 L4320–5056 |
| target_order_notional | exact finite decimal / rational as defined; USDT notional | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| raw_qty | exact finite decimal / rational as defined; base quantity; exact rational | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| final_qty | exact finite decimal / rational as defined; base quantity | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| actual_order_notional | exact finite decimal / rational as defined; USDT notional | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| actual_committed_capital_exact | exact finite decimal / rational as defined; own-capital unit | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| actual_committed_capital | exact finite decimal / rational as defined; own-capital unit | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| margin_required | exact finite decimal / rational as defined; own-capital unit | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§17–22A L576–908; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| risk_distance_price | exact monetary / ratio as named; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| reward_distance_price | exact monetary / ratio as named; price | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| risk_distance_pct | exact monetary / ratio as named; percent | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| reward_distance_pct | exact monetary / ratio as named; percent | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| gross_rr | exact monetary / ratio as named; dimensionless | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| gross_profit_tp | exact monetary / ratio as named; accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| gross_loss_sl | exact monetary / ratio as named; positive gross loss in accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| expected_entry_fee | exact monetary / ratio as named; signed cost in accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| expected_tp_exit_fee | exact monetary / ratio as named; signed cost in accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| expected_sl_exit_fee | exact monetary / ratio as named; signed cost in accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| tp_exit_notional | exact monetary / ratio as named; notional | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| sl_exit_notional | exact monetary / ratio as named; notional | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| tp_total_cost | exact monetary / ratio as named; signed cost | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| sl_total_cost | exact monetary / ratio as named; signed cost | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| net_profit_tp | exact monetary / ratio as named; signed accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| net_edge_pct | exact monetary / ratio as named; percent of actual order notional | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| net_loss_sl | exact monetary / ratio as named; signed accounting currency | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| net_rr | exact monetary / ratio as named; dimensionless or unavailable | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §§23–40 L912–1436; methodology/POSITION_RULES.md Part I §14 L465–517; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| minimum_rr_result | state enum; none | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §14 L465–517; methodology/POSITION_RULES.md Part I §§23–40 L912–1436 |
| minimum_net_edge | state enum; none | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §14 L465–517; methodology/POSITION_RULES.md Part I §§23–40 L912–1436 |
| OPPORTUNITY_DECISION | state enum; none | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §14 L465–517; methodology/POSITION_RULES.md Part I §§23–40 L912–1436 |
| CONSTRUCTION_RESULT | state enum; none | Position Rules | Result/dependency only | methodology/POSITION_RULES.md Part I §14 L465–517; methodology/POSITION_RULES.md Part I §§23–40 L912–1436 |
| daily_portfolio_base | exact amount / integer / timestamp; own-capital currency | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§2–4 L98–247; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| current_portfolio_equity | exact amount / integer / timestamp; API factual equity | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§2–4 L98–247; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| daily_realized_pnl | exact amount / integer / timestamp; signed accounting currency | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §23 L776–872; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| unrealized_pnl | exact amount / integer / timestamp; factual signed accounting currency | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§2–4 L98–247; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| total_pnl | exact amount / integer / timestamp; signed accounting currency | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§2–4 L98–247; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| global_position_cap | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§6–8 L288–358; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| coin_allocation_cap[symbol] | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part I §§6–8 L288–358; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| committed_global_capital | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| committed_coin_capital | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| logical_committed_capital[tranche] | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| free_global_capital | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| free_coin_capital | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| remaining_global_slots | exact amount / integer / timestamp; integer slots | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| remaining_coin_slots | exact amount / integer / timestamp; integer slots | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| global_committed_tranches | exact amount / integer / timestamp; integer tranches | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| coin_committed_tranches | exact amount / integer / timestamp; integer tranches | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| requested_capital_per_tranche | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| daily_loss_limit_amount | exact amount / integer / timestamp; exact own-capital threshold | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §23 L776–872; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| daily_loss_used_amount_d | exact amount / integer / timestamp; own capital | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §23 L776–872; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| cooldown_until[symbol] | exact amount / integer / timestamp; timestamp | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§24–27 L876–980; schemas/NUMERIC_POLICY.md §§1–7 L8–94; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |
| Portfolio health | LIVE / RECONCILING / STALE; none | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633 |
| daily_loss_status | DISABLED / LATCHED / UNAVAILABLE_OR_FAIL_CLOSED / LIMIT_REACHED / OK; none | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §23 L776–872 |
| daily_loss_blocks_new_exposure | Boolean; none | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §23 L776–872 |
| Coins status | OPEN / CLOSE; none | Portfolio Rules | Result/dependency only | methodology/PORTFOLIO_RULES.md Part II §§11–17 L484–633 |
| gross_realized_trading_result | exact monetary amount; signed accounting currency | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §§33–34 L1343–1377; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| actual_fees_rebates | exact monetary amount; cost-effect signed accounting currency | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §§33–34 L1343–1377; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| allocated_funding | exact monetary amount; wallet-effect signed accounting currency | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §32 L1208–1339; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| other_supported_exchange_costs | exact monetary amount; cost-effect signed accounting currency | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §§33–34 L1343–1377; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| net_realized_result | exact monetary amount; signed accounting currency | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §§33–34 L1343–1377; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| tranche_open_notional_at_funding_time | exact monetary amount; notional | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §32 L1208–1339; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| total_triggertrade_open_notional_for_symbol_side_at_funding_time | exact monetary amount; notional | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §32 L1208–1339; SYSTEM_PROTOCOLS.md P6–P8 L114–220; schemas/NUMERIC_POLICY.md §§1–7 L8–94 |
| lifecycle_state | enum; none | Order Lifecycle | Result/dependency only | methodology/ORDER_LIFECYCLE.md §7 L522–595; SYSTEM_PROTOCOLS.md P6–P8 L114–220 |


Per-symbol metric dependencies in §8 take precedence over interpreting this union lookup as universal computation. For BTC, do not generate absent classifier fields or self-relative normalization. Reporting statistics live only in the report registry in §11.

## 4. Research trigger registry

### 4.1 Original predicate bodies — preserved

#### TR-R-001

```yaml
trigger_id: TR-R-001
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'TRUE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '0.50'
```

#### TR-R-002

```yaml
trigger_id: TR-R-002
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'TRUE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '1.00'
```

#### TR-R-003

```yaml
trigger_id: TR-R-003
metric_id: F-002 trigger_result
operator: EQ
threshold/state/value: 'TRUE'
timeframe/context: Current completed 1m slot; 60 preceding consecutive 1m base-volume candles
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
canonical_metric_parameters:
  fixed_R_boundary: '2'
  fixed_P_boundary: '90'
  parameter_mutability: NONE
```

#### TR-R-004

```yaml
trigger_id: TR-R-004
metric_id: classifier_direction
operator: EQ
threshold/state/value: LONG
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
```

#### TR-R-005

```yaml
trigger_id: TR-R-005
metric_id: classifier_direction
operator: EQ
threshold/state/value: SHORT
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
```

#### TR-R-006

```yaml
trigger_id: TR-R-006
metric_id: DE
operator: GTE
threshold/state/value: '0.50'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-007

```yaml
trigger_id: TR-R-007
metric_id: ATR percentile
operator: GTE
threshold/state/value: '30'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-008

```yaml
trigger_id: TR-R-008
metric_id: ATR percentile
operator: LTE
threshold/state/value: '85'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-009

```yaml
trigger_id: TR-R-009
metric_id: SWING_SEQUENCE_STATE(asset,1h)
operator: EQ
threshold/state/value: BULLISH
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-010

```yaml
trigger_id: TR-R-010
metric_id: SWING_SEQUENCE_STATE(asset,1h)
operator: EQ
threshold/state/value: BEARISH
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-011

```yaml
trigger_id: TR-R-011
metric_id: RELATIVE_RETURN_15m
operator: GTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-012

```yaml
trigger_id: TR-R-012
metric_id: RELATIVE_RETURN_15m
operator: LTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-013

```yaml
trigger_id: TR-R-013
metric_id: AGGRESSIVE_VOLUME_DELTA_PCT
operator: GTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-014

```yaml
trigger_id: TR-R-014
metric_id: AGGRESSIVE_VOLUME_DELTA_PCT
operator: LTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-015

```yaml
trigger_id: TR-R-015
metric_id: classifier_direction
operator: EQ
threshold/state/value: LONG
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=0 at formation use; same source identity and authoritative
  cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-016

```yaml
trigger_id: TR-R-016
metric_id: classifier_direction
operator: EQ
threshold/state/value: SHORT
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=0 at formation use; same source identity and authoritative
  cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-017

```yaml
trigger_id: TR-R-017
metric_id: TOD_REL_TURNOVER
operator: GTE
threshold/state/value: '1.00'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-018

```yaml
trigger_id: TR-R-018
metric_id: BTC_CONTEXT_SCORE
operator: GTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-019

```yaml
trigger_id: TR-R-019
metric_id: BTC_CONTEXT_SCORE
operator: LTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-020

```yaml
trigger_id: TR-R-020
metric_id: DIRECTION_SCORE
operator: GTE
threshold/state/value: '0.55'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-021

```yaml
trigger_id: TR-R-021
metric_id: DIRECTION_SCORE
operator: LTE
threshold/state/value: '-0.55'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§31–34
  SOURCE_LINES: 3050–3150
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-022

```yaml
trigger_id: TR-R-022
metric_id: VNM_5m_z
operator: GTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-023

```yaml
trigger_id: TR-R-023
metric_id: VNM_5m_z
operator: LTE
threshold/state/value: '0'
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
```

#### TR-R-024

```yaml
trigger_id: TR-R-024
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'TRUE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '0.75'
```

#### TR-R-025

```yaml
trigger_id: TR-R-025
metric_id: classifier_direction
operator: EQ
threshold/state/value: LONG
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=5 minutes; inclusive authoritative event-time age;
  same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-026

```yaml
trigger_id: TR-R-026
metric_id: classifier_direction
operator: EQ
threshold/state/value: SHORT
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=5 minutes; inclusive authoritative event-time age;
  same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-027

```yaml
trigger_id: TR-R-027
metric_id: classifier_direction
operator: EQ
threshold/state/value: LONG
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=10 minutes; inclusive authoritative event-time age;
  same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: LONG
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-028

```yaml
trigger_id: TR-R-028
metric_id: classifier_direction
operator: EQ
threshold/state/value: SHORT
timeframe/context: completed 5m evaluation; source metric retains its own horizon
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate;
  initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=10 minutes; inclusive authoritative event-time age;
  same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution'
direction_applicability: SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
```

#### TR-R-029

```yaml
trigger_id: TR-R-029
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'FALSE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '0.50'
purpose: Research reset predicate only; never treats UNAVAILABLE as FALSE.
```

#### TR-R-030

```yaml
trigger_id: TR-R-030
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'FALSE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '1.00'
purpose: Research reset predicate only; never treats UNAVAILABLE as FALSE.
```

#### TR-R-031

```yaml
trigger_id: TR-R-031
metric_id: F-001 trigger_result
operator: EQ
threshold/state/value: 'FALSE'
timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
freshness/evaluation_semantics: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates;
  no stale substitution
direction_applicability: LONG and SHORT
prerequisites: All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before
  final MATCHED.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
canonical_metric_parameters:
  theta_move_pct: '0.75'
purpose: Research reset predicate only; never treats UNAVAILABLE as FALSE.
```

### 4.2 Approved BTC predicates — new immutable references

#### TR-R-BTC-001

```yaml
trigger_id: TR-R-BTC-001
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: RETURN(asset,5m)
operator: GT
threshold/state/value: '0'
metric_binding:
  asset: BTC
  canonical_instance: RETURN(asset=BTC,5m)
  return_price: completed-bar close
  horizon: 5m
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: LONG
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: 06a65bb52f4820475005ff24dd38e6e804469b379c29d5926b392dcd3732094c
```

#### TR-R-BTC-002

```yaml
trigger_id: TR-R-BTC-002
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: RETURN(asset,5m)
operator: LT
threshold/state/value: '0'
metric_binding:
  asset: BTC
  canonical_instance: RETURN(asset=BTC,5m)
  return_price: completed-bar close
  horizon: 5m
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: e6a658d3975967c593ca4f434fec94df9fcc129b472a135517fbbc2c65def6eb
```

#### TR-R-BTC-003

```yaml
trigger_id: TR-R-BTC-003
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: RETURN(asset,5m)
operator: GT
threshold/state/value: '0'
metric_binding:
  asset: BTC
  canonical_instance: RETURN(asset=BTC,5m)
  return_price: completed-bar close
  horizon: 5m
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch observed FALSE→TRUE of this existing return-side predicate;
  unconsumed event at the current cutoff only. Initial TRUE and UNAVAILABLE→TRUE are not events; unavailable breaks
  event ancestry. Current side remains required at MATCHED.'
direction_applicability: LONG
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: 3af8dd16cca8bb6b907e7b85d10350ddc2f1147085ec8420c15b42cf7fe77186
```

#### TR-R-BTC-004

```yaml
trigger_id: TR-R-BTC-004
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: RETURN(asset,5m)
operator: LT
threshold/state/value: '0'
metric_binding:
  asset: BTC
  canonical_instance: RETURN(asset=BTC,5m)
  return_price: completed-bar close
  horizon: 5m
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: 'FRESH_EVENT: same-epoch observed FALSE→TRUE of this existing return-side predicate;
  unconsumed event at the current cutoff only. Initial TRUE and UNAVAILABLE→TRUE are not events; unavailable breaks
  event ancestry. Current side remains required at MATCHED.'
direction_applicability: SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: 45406e794fe29037b80a9d052778d829a6eb8d39995862872dbc384726e12f55
```

#### TR-R-BTC-005

```yaml
trigger_id: TR-R-BTC-005
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: DE
operator: GTE
threshold/state/value: '0.30'
metric_binding:
  asset: BTC
  canonical_instance: DE (asset=BTC)
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: LONG and SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–15
  SOURCE_LINES: 2317–2508
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: c01959e932573271a1656dc9a2a017c5050897ebb83fcce933674eee22c5ef13
```

#### TR-R-BTC-006

```yaml
trigger_id: TR-R-BTC-006
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: ATR percentile
operator: GTE
threshold/state/value: '15'
metric_binding:
  asset: BTC
  canonical_instance: ATR percentile (asset=BTC)
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: LONG and SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–15
  SOURCE_LINES: 2317–2508
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: 211a35d7ae677eb88da0b7095af00e557c0ebc5983643146d0adb6306d0ff8b8
```

#### TR-R-BTC-007

```yaml
trigger_id: TR-R-BTC-007
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: ATR percentile
operator: LTE
threshold/state/value: '97'
metric_binding:
  asset: BTC
  canonical_instance: ATR percentile (asset=BTC)
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: LONG and SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–15
  SOURCE_LINES: 2317–2508
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: f12ae078b937c4ef8f991d9d4675ec145c08cb56bb4c786677ca7b2500751981
```

#### TR-R-BTC-008

```yaml
trigger_id: TR-R-BTC-008
identifier_class: RESEARCH_ONLY
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
metric_id: TOD_REL_TURNOVER
operator: GTE
threshold/state/value: '0.70'
metric_binding:
  asset: BTC
  canonical_instance: TOD_REL_TURNOVER (asset=BTC)
timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
freshness/evaluation_semantics: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE
  is never FALSE or zero; no stale substitution.
direction_applicability: LONG and SHORT
prerequisites: Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing
  BTC Set. No classifier object or classifier gate is evaluated for BTC.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§10–12
  SOURCE_LINES: 509–530; 1132–1260
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8; §23
  SOURCE_LINES: 2013–2131; 2823–2858
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.4
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
content_sha256: 057e8e0e42961f23b91195b4de5b9feadd2c48921fe51666f7139ad09f42858d
```

## 5. Research Set-version registry

### 5.1 Original governed Set definitions — unchanged, NON_BTC scope in this campaign

Selected and reserve originals remain distinguishable by final arm membership. Their original F005 behavior is not edited to accommodate BTC.

#### SET-R-001-V1

```yaml
set_id: SET-R-001
set_version: SET-R-001-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
  - AND:
    - TR-R-005
    - TR-R-001
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-001-V2

```yaml
set_id: SET-R-001
set_version: SET-R-001-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-002
- TR-R-004
- TR-R-005
- TR-R-030
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-002
  - AND:
    - TR-R-005
    - TR-R-002
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-030; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-030
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-002-V2

```yaml
set_id: SET-R-002
set_version: SET-R-002-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-004
- TR-R-005
- TR-R-024
- TR-R-031
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-024
  - AND:
    - TR-R-005
    - TR-R-024
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-031; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-031
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-003-V2

```yaml
set_id: SET-R-003
set_version: SET-R-003-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-003
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-003
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-007-V2

```yaml
set_id: SET-R-007
set_version: SET-R-007-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-006
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-006
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-006
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-008-V2

```yaml
set_id: SET-R-008
set_version: SET-R-008-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-007
- TR-R-008
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-007
    - TR-R-008
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-007
    - TR-R-008
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-009-V2

```yaml
set_id: SET-R-009
set_version: SET-R-009-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-009
- TR-R-010
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-009
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-010
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-010-V2

```yaml
set_id: SET-R-010
set_version: SET-R-010-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-011
- TR-R-012
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-011
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-012
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-011-V2

```yaml
set_id: SET-R-011
set_version: SET-R-011-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-013
- TR-R-014
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-013
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-014
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-012-V2

```yaml
set_id: SET-R-012
set_version: SET-R-012-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-018
- TR-R-019
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-018
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-019
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-013-V2

```yaml
set_id: SET-R-013
set_version: SET-R-013-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-017
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-017
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-017
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-014-V2

```yaml
set_id: SET-R-014
set_version: SET-R-014-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-020
- TR-R-021
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-020
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-021
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-015-V2

```yaml
set_id: SET-R-015
set_version: SET-R-015-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-022
- TR-R-023
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-022
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-023
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-016-V2

```yaml
set_id: SET-R-016
set_version: SET-R-016-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-015
- TR-R-016
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-015
    - TR-R-001
    - TR-R-004
  - AND:
    - TR-R-016
    - TR-R-001
    - TR-R-005
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-017-V1

```yaml
set_id: SET-R-017
set_version: SET-R-017-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-025
- TR-R-026
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-025
    - TR-R-001
    - TR-R-004
  - AND:
    - TR-R-026
    - TR-R-001
    - TR-R-005
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-017-V2

```yaml
set_id: SET-R-017
set_version: SET-R-017-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-027
- TR-R-028
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-027
    - TR-R-001
    - TR-R-004
  - AND:
    - TR-R-028
    - TR-R-001
    - TR-R-005
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-019-V1

```yaml
set_id: SET-R-019
set_version: SET-R-019-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - TR-R-003
  - AND:
    - TR-R-005
    - TR-R-001
    - TR-R-003
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-019-V2

```yaml
set_id: SET-R-019
set_version: SET-R-019-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-004
          - TR-R-001
        - AND:
          - TR-R-004
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
  - AND:
    - TR-R-005
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-005
          - TR-R-001
        - AND:
          - TR-R-005
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current F-005 direction is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-020-V1

```yaml
set_id: SET-R-020
set_version: SET-R-020-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-004
          - TR-R-001
        - AND:
          - TR-R-004
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
  - AND:
    - TR-R-005
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-005
          - TR-R-001
        - AND:
          - TR-R-005
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current F-005 direction is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-020-V2

```yaml
set_id: SET-R-020
set_version: SET-R-020-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-004
          - TR-R-001
        - AND:
          - TR-R-004
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
  - AND:
    - TR-R-005
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-005
          - TR-R-001
        - AND:
          - TR-R-005
          - TR-R-003
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: The step-1 classifier direction must remain TRUE at every canonical completed-5m evaluation
    in [tA,tB]. FALSE or UNAVAILABLE resets sequence. This is sampled continuity, not continuous intra-bar truth.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current F-005 direction is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-021-V1

```yaml
set_id: SET-R-021
set_version: SET-R-021-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-017
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - AND:
      - TR-R-003
      - TR-R-017
  - AND:
    - TR-R-005
    - TR-R-001
    - AND:
      - TR-R-003
      - TR-R-017
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

#### SET-R-021-V2

```yaml
set_id: SET-R-021
set_version: SET-R-021-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-017
- TR-R-029
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-004
    - TR-R-001
    - OR:
      - TR-R-003
      - TR-R-017
  - AND:
    - TR-R-005
    - TR-R-001
    - OR:
      - TR-R-003
      - TR-R-017
direction_semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side,
  never F-001 sign or a score-only substitute.
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
reset_trigger_id: TR-R-029
context_note: GENERIC is a Position-context Set family here; it does NOT mean the Set is outside F-005 governed
  direction scope.
```

### 5.2 BTC-specific generic deterministic versions

The following fourteen unchanged R2-carried Set bodies supply direction outside F005; the two R3 additions follow in §5.R3. All sixteen use the already approved generic direction mechanism. These fourteen bodies supply direction outside F005 under frozen SET Part I §5. Direction is Set-owned; RETURN is not promoted to an autonomous classifier. The floor predicates are current-state requirements at formation qualification endpoints, not a new maintained test. Pending BTC_CONTEXT_SCORE invalidation remains Set-owned and only active after ORDER_PLACED.

#### SET-R-BTC-001-V1

```yaml
set_id: SET-R-BTC-001
set_version: SET-R-BTC-001-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-001-V1
  definition_sha256: ab78d55348ab80850cab6bc97948e573fbc2d90a9a9750c7f6771ba558521604
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 3cd5b801098a537139d6030d30ef0c6bc7d48f9a6cc4d837b2de46d94cd0a02d
```

#### SET-R-BTC-001-V2

```yaml
set_id: SET-R-BTC-001
set_version: SET-R-BTC-001-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-002
- TR-R-030
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-002
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-002
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-030; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-030
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-001-V2
  definition_sha256: 739285c23847d0eaf2a464d549a9199f1b4b2af47874cc76f07fb58651f5754e
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-002
  predicate_definition_sha256: e0bddb4fe5d5e224553079682f7004072568cd6818c87c994c33d7a1abaeabf7
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-030
  predicate_definition_sha256: 71150f0d3a7fc5684cf6cb0c4708ad8bf3358752fb977c9dba9e38cce1b68323
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 4a24322fffceb0761de982278f3f886c7ae901331c438e8ec996ae0cc211943d
```

#### SET-R-BTC-003-V2

```yaml
set_id: SET-R-BTC-003
set_version: SET-R-BTC-003-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-003
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-003
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-003-V2
  definition_sha256: 0bc28f9eec02b3266829faf690055d16e0630cea3f3c8e515e2448bbac269fe5
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: f40e17f39b238fe7ce8c56588aaed11cac909c70c12592f76a9ebe712e1d0c17
```

#### SET-R-BTC-007-V2

```yaml
set_id: SET-R-BTC-007
set_version: SET-R-BTC-007-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-006
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-006
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-006
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-007-V2
  definition_sha256: 9601425a4137c64c0d65da47a1b0e1fc2e9ad6537d0d60adaa17988becd4463c
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-006
  predicate_definition_sha256: 5badcb3e6ca10215e1f5459dec571ec0f05acbc72c038b7e04bfefc40763333b
  metric_id: DE
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 02774843e90e81442dbc70c3f0db7d50f8cf7bc8c2b1227306f6d74a6884c6b2
```

#### SET-R-BTC-008-V2

```yaml
set_id: SET-R-BTC-008
set_version: SET-R-BTC-008-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-007
- TR-R-008
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-007
    - TR-R-008
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-007
    - TR-R-008
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-008-V2
  definition_sha256: dd4b471c283340330c67414eb4c473a176f1fc95b9cef4d01e276c57fe28b71c
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-007
  predicate_definition_sha256: dd2721770424f9a10bfe413c9114e91c2a65cbe792cc802764f3bb37a0ca0405
  metric_id: ATR percentile
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-008
  predicate_definition_sha256: c8aeb589e24e31ae67cf190abec11df05de237c0819c3cc36128622bb7e6884b
  metric_id: ATR percentile
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: ba58c6d95f3f965962cfddee99892f934d3c16de6ae12b1c0f2b162dc23488b3
```

#### SET-R-BTC-009-V2

```yaml
set_id: SET-R-BTC-009
set_version: SET-R-BTC-009-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-009
- TR-R-010
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-009
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-010
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-009-V2
  definition_sha256: 4c532913580a75d24fdae68db5e73fd63621e5e68c39172e20b7221dd8c70efd
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-009
  predicate_definition_sha256: 3ef3c90c451a7b697b46ebd87cc020d17096ef3153ab5eee560adf83d2b036eb
  metric_id: SWING_SEQUENCE_STATE(asset,1h)
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-010
  predicate_definition_sha256: 020446b5aa23f5b916ccbc0859e01a7877aef029b7aee10dc78b37511ad4dbe3
  metric_id: SWING_SEQUENCE_STATE(asset,1h)
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 2061690f5f7b4fe598298117c65137e8f9a6f5830ac179dad9038ac0c1218fdb
```

#### SET-R-BTC-011-V2

```yaml
set_id: SET-R-BTC-011
set_version: SET-R-BTC-011-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-013
- TR-R-014
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-013
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-014
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-011-V2
  definition_sha256: 597164584e8cf1550afb8bef4d4c9f599f4ded426ffa89912111800f51471550
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-013
  predicate_definition_sha256: 889ffa86151aae28d11709c5526be4dd23950fb89b1f0e9a4f516f7329f4096c
  metric_id: AGGRESSIVE_VOLUME_DELTA_PCT
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-014
  predicate_definition_sha256: 8279227564738af85869ebb9be15ebc6f880aa4743607b172dbf40fb6e2afe84
  metric_id: AGGRESSIVE_VOLUME_DELTA_PCT
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 6c89c6d62a3d8c430604ca5ce650448eb9081f33676370217a3b673af5c32dd7
```

#### SET-R-BTC-016-V2

```yaml
set_id: SET-R-BTC-016
set_version: SET-R-BTC-016-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-003
- TR-R-BTC-004
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-003
    - TR-R-001
    - TR-R-BTC-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-004
    - TR-R-001
    - TR-R-BTC-002
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-016-V2
  definition_sha256: 22f38f6bbb41050bb24db4149f6f238fa054261cc352657e4ba6f5417b412c27
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 666718e8097a70fa66bd46f93800de22d95f6877483afe9373c7fc8713961820
```

#### SET-R-BTC-019-V1

```yaml
set_id: SET-R-BTC-019
set_version: SET-R-BTC-019-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-003
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-003
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-019-V1
  definition_sha256: 02ed3ea8144ced27397398f195760508c2e3d24790da52d762622a41ad1b7211
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: a7984712cf80bdfbdad06b511ed2f1515c0c542677ca9849feb839be4e60c296
```

#### SET-R-BTC-019-V2

```yaml
set_id: SET-R-BTC-019
set_version: SET-R-BTC-019-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-001
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-001
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-002
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-002
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current BTC return-side qualification is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-019-V2
  definition_sha256: 59f9831a25ee78a4a987699ed608253fe0419347af8390d11bc4b2a833293105
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 4f6bf88e42135bcb2235e527c8fb05e2145d008228e644fec69c7870f7a0c036
```

#### SET-R-BTC-020-V1

```yaml
set_id: SET-R-BTC-020
set_version: SET-R-BTC-020-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-001
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-001
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-002
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-002
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current BTC return-side qualification is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-020-V1
  definition_sha256: 72bf584ff47d618725eef62c92d703e60aa2fffccca403a097384b09d32c656c
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 1c442b11c65e709b47d617186505b3a70977a5fee62128afd73e085dbbcfebc3
```

#### SET-R-BTC-020-V2

```yaml
set_id: SET-R-BTC-020
set_version: SET-R-BTC-020-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-001
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-001
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - SEQUENCE:
        steps:
        - AND:
          - TR-R-BTC-002
          - TR-R-001
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        - AND:
          - TR-R-BTC-002
          - TR-R-003
          - TR-R-BTC-005
          - TR-R-BTC-006
          - TR-R-BTC-007
          - TR-R-BTC-008
        anchor: authoritative qualifying step-1 cutoff tA
        order: tB > tA
        window: tB <= tA + 10 minutes; inclusive endpoint
        first_step_rule: First eligible step-1 evaluation in the active formation; do not restart timer on repeated
          TRUE.
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE/new epoch, required UNAVAILABLE or expired sequence clears accumulated steps. No backfill of missed
    intermediate evaluations.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: The step-1 BTC return-side qualification must remain TRUE at every canonical completed-5m
    evaluation in [tA,tB]. FALSE or UNAVAILABLE resets sequence. This is sampled continuity, not continuous intra-bar
    truth.
  sequence_expiry: Expire accumulated sequence after tA+10 minutes; terminal step at equality eligible; reset before
    arming a fresh sequence on a later cutoff.
  step_evidence: F-001 must be current only at step 1; F-002 must be current at step 2. They remain CURRENT_STATE
    predicates. Current BTC return-side qualification is mandatory at both endpoints and final match.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-020-V2
  definition_sha256: fb6f9618d0cae54347606bb5e13dac5f1043280b2456dc97661535f8b2303f9d
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: fa5cf1fb180515a94a0ecc885a5c996bb3f8f7ae802a5312429b3eab218af9d0
```

#### SET-R-BTC-021-V1

```yaml
set_id: SET-R-BTC-021
set_version: SET-R-BTC-021-V1
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-017
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - AND:
      - TR-R-003
      - TR-R-017
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - AND:
      - TR-R-003
      - TR-R-017
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-021-V1
  definition_sha256: 70d129c4d53261213d32ad52931411c7e461c0bf0346d74bf0b36331996da330
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-017
  predicate_definition_sha256: 9b583f3778c0169854bda3bb9c4df383935750a0831ec964014dec1d47034f2e
  metric_id: TOD_REL_TURNOVER
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 0a1b91626b19d807b19abc1902e9e58d6e806401af0c6855d4f2a2e53a1aabe0
```

#### SET-R-BTC-021-V2

```yaml
set_id: SET-R-BTC-021
set_version: SET-R-BTC-021-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-003
- TR-R-017
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - OR:
      - TR-R-003
      - TR-R-017
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - OR:
      - TR-R-003
      - TR-R-017
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch
  to LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity.
    Do not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker
    match reference remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available
    CURRENT_STATE TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE
    of that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin
    remains OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version
    and required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation;
    do not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from:
  set_version: SET-R-021-V2
  definition_sha256: 07add596db30a217abbd672767a0df3c636c1cbfc1e52357d185b8a4b4c92ddd
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a
  maintained interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the
  return-side predicate only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001;
  the original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-003
  predicate_definition_sha256: 4b5339a578705c5a18b4836b3c49e6ca66f7176feb8c55e4c81c51c4fb06574e
  metric_id: F-002 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-017
  predicate_definition_sha256: 9b583f3778c0169854bda3bb9c4df383935750a0831ec964014dec1d47034f2e
  metric_id: TOD_REL_TURNOVER
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
content_sha256: 5a9f0f2398fbe19af90fa605b794d727580579b148b80cc2e1d6afd39f2781e6
```

### 5.R3 — Two newly materialized immutable BTC Set definitions

These are current definitions, not suggested future versions. `derived_from` points to the unchanged BTC baseline and its content digest; `candidate_instantiation_ref` binds the already-approved non-BTC variant. Only one branch-specific CURRENT_STATE compatibility predicate is added in each branch. All original baseline floors, branch direction, reset/re-arm, reference/context, pending condition and ownership are unchanged. Original non-BTC TR-R narratives remain unchanged; `trigger_instances` explicitly replaces only the enclosing-Set direction prerequisite with DB-R-BTC-001.

#### SET-R-BTC-012-V2

```yaml
set_id: SET-R-BTC-012
set_version: SET-R-BTC-012-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-018
- TR-R-019
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
    - TR-R-018
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
    - TR-R-019
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch to
  LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity. Do
    not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker match reference
    remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available CURRENT_STATE
    TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE of
    that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin remains
    OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version and
    required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation; do
    not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§9–12
  SOURCE_LINES: 509–530; 1082–1260
- SOURCE_DOCUMENT: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md
  SOURCE_SECTION: §§5–6; approved replacement application
- SOURCE_DOCUMENT: RESEARCH_V1_R2_REPLACEMENT_PAIRWISE_CHECKS.md
  SOURCE_SECTION: All 57 affected relationships
- SOURCE_DOCUMENT: Mechanical Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§3–15; §§26–28
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
derived_from:
  set_version: SET-R-BTC-001-V1
  definition_sha256: 3cd5b801098a537139d6030d30ef0c6bc7d48f9a6cc4d837b2de46d94cd0a02d
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a maintained
  interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the return-side predicate
  only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001; the
  original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-018
  predicate_definition_sha256: df84081b38f37f181511ea95e1b7548d63ae907dc61cf491af1af200f1ebfcee
  metric_id: BTC_CONTEXT_SCORE
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Canonical metric source/horizon/numeric/availability dependencies unchanged; F-005 in original
    predicate narrative is NOT an enclosing requirement here. No BTC classifier object is produced.
- predicate_definition_ref: TR-R-019
  predicate_definition_sha256: 0de0f3040440ae33ab0298f497cb1911d9c64593ab2881abacc4c328fbb7e199
  metric_id: BTC_CONTEXT_SCORE
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Canonical metric source/horizon/numeric/availability dependencies unchanged; F-005 in original
    predicate narrative is NOT an enclosing requirement here. No BTC classifier object is produced.
revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
candidate_instantiation_ref:
  candidate_id: C-012
  non_btc_variant: SET-R-012-V2
  non_btc_definition_sha256: e12bca655f8c5362816cc3c8a7717621c8fd22860760dc3327b99c95a26996c1
  selection_authority: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md §6
additional_predicate_interpretation: Inclusive sign compatibility only; valid zero passes the selected side, UNAVAILABLE
  never passes. No direction, veto, reset, maintained-condition, execution or allocation change.
content_sha256: 05a5ddc9d704289f6565c7499259b34af659893dd5927494c862129d071a80e9
```

#### SET-R-BTC-015-V2

```yaml
set_id: SET-R-BTC-015
set_version: SET-R-BTC-015-V2
identifier_class: RESEARCH_ONLY
trigger_membership:
- TR-R-001
- TR-R-022
- TR-R-023
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
trigger_composition_logic:
  OR:
  - AND:
    - TR-R-BTC-001
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
    - TR-R-022
  - AND:
    - TR-R-BTC-002
    - TR-R-001
    - TR-R-BTC-005
    - TR-R-BTC-006
    - TR-R-BTC-007
    - TR-R-BTC-008
    - TR-R-023
direction_semantics: 'NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M: Set maps the matched positive-return branch to
  LONG and negative-return branch to SHORT. Zero qualifies neither; required UNAVAILABLE produces no direction-qualified
  MATCHED. No F-005 execution or classifier override.'
reference/context_requirements:
  position_context_policy:
    set_family: GENERIC
    role_bindings: []
    entry:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    sl:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
    tp:
      thesis_reference_policy: NONE
      thesis_reference_level_role: null
  resolved_context_constraints:
    entry_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    sl_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
    tp_context:
      set_family: GENERIC
      thesis_reference_policy: NONE
      thesis_reference_level_id: null
      origin_binding: null
  geometry: Use canonical confirmed 15m/1h swing and previous completed UTC-day references, with source identity. Do
    not fabricate unspecified range/session/VWAP producer facts. Mandatory positive F-003 exports and ticker match reference
    remain required.
evaluation_policy: At each canonical completed-5m cutoff T, sample only the F-001/F-002 CURRENT_STATE 1m slot ending
  T. Preserve own horizons of other metrics and all fixed normalization calendars.
formation_policy:
  arming: Authoritative symbol OPEN epoch; one active formation per Set/version/symbol/epoch. Initial available CURRENT_STATE
    TRUE is eligible.
  rearm: AFTER_RESET using the specified reset Trigger; after a completed match require a later authoritative FALSE of
    that Set version's F-001 predicate, then re-arm at the next strictly later completed-5m cutoff while Coin remains
    OPEN. This consumes no old event again and does not mutate the committed cycle.
  reset: CLOSE / superseding OPEN epoch or required-evidence unavailability invalidates accumulated formation evidence;
    no cross-epoch carry.
  simultaneous_lifetime: No optional maximum lifetime is configured; no implicit time-based pending cancellation.
  maintained_condition: None beyond predicates evaluated at the final formation cutoff.
  reset_trigger: Reset predicate TR-R-029; FALSE evidence means the canonical F-001 trigger is authoritatively FALSE,
    never unavailable.
pending_frozen_condition:
  owner: Set
  activation: Only authoritative ORDER_PLACED for the committed cycle/result; no pre-acceptance monitoring
  hard_conditions:
  - direction: LONG
    metric: BTC_CONTEXT_SCORE
    operator: LTE
    value: '-0.70'
  - direction: SHORT
    metric: BTC_CONTEXT_SCORE
    operator: GTE
    value: '0.70'
  binding: At match freeze only the condition for the original direction, including canonical metric source/version and
    required current completed-5m semantics.
  unavailable_policy: FAIL_SAFE_CANCEL; any required unavailable evidence remains UNAVAILABLE; sticky cancellation; do
    not exit filled exposure.
  source:
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part II §§24–27
    SOURCE_LINES: 2863–2958
  - SOURCE_DOCUMENT: methodology/SET.md
    SOURCE_SECTION: Part IV §§12–12A
    SOURCE_LINES: 4879–5162
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 509–530
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§3–10
  SOURCE_LINES: 3520–3718
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §§12–22
  SOURCE_LINES: 3757–4059
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§18–20
  SOURCE_LINES: 1470–1514
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §24
  SOURCE_LINES: 1582–1601
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part IV §§12–12A
  SOURCE_LINES: 4879–5162
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§3–6; §16.2
  SOURCE_LINES: 1739–1961; 2561–2587
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§4–7
  SOURCE_LINES: 1766–2011
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §16.2; §18
  SOURCE_LINES: 2561–2648; 2677–2697
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md
  SOURCE_SECTION: §§5–6; approved replacement application
- SOURCE_DOCUMENT: RESEARCH_V1_R2_REPLACEMENT_PAIRWISE_CHECKS.md
  SOURCE_SECTION: All 57 affected relationships
- SOURCE_DOCUMENT: Mechanical Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§3–15; §§26–28
reset_trigger_id: TR-R-029
context_note: Position-context family GENERIC is preserved; the explicitly non-F-005 direction authority is separately
  defined by this version. No classifier or relative-score prerequisite is inherited.
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
derived_from:
  set_version: SET-R-BTC-001-V1
  definition_sha256: 3cd5b801098a537139d6030d30ef0c6bc7d48f9a6cc4d837b2de46d94cd0a02d
direction_binding_ref: DB-R-BTC-001
symbol_scope:
- BTC
branch_direction_map:
  TR-R-BTC-001: LONG
  TR-R-BTC-002: SHORT
conflict_rule: One same-source canonical scalar cannot be both >0 and <0. Conflicting source identities or impossible
  dual truth invalidate evaluation; never pick a priority winner.
common_baseline_predicates:
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
common_floor_timing: Required at every direction-qualified formation endpoint and final match. Not promoted to a maintained
  interval test. Required unavailability retains reset semantics. R-010 maintained variant tests the return-side predicate
  only at each completed 5m evaluation; baseline has no new direction-change reset.
trigger_instance_binding_rule: Reuse each referenced common TR-R predicate with its exact metric/operator/value/horizon/role.
  Its original registry narrative requiring current F-005 before final MATCHED was an enclosing F-005 Set precondition,
  not a metric dependency. This immutable BTC Set version replaces that enclosing precondition with DB-R-BTC-001; the
  original non-BTC trigger/Set definitions stay unchanged.
trigger_instances:
- predicate_definition_ref: TR-R-001
  predicate_definition_sha256: 779a03459a911e2671be942ea59f95e1bf5a91bcc8e52078d09c2fd33cb7773f
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-029
  predicate_definition_sha256: 7ffa705a93381a8ea1e2a94d3abec12e87f24ac43544f487e21a615085d6dc8a
  metric_id: F-001 trigger_result
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Unchanged canonical metric dependencies, source completeness and numeric policy; no F-005
    prerequisite in this non-F-005 instance.
- predicate_definition_ref: TR-R-022
  predicate_definition_sha256: 881142f33c03ee8f3140c3be965205a5ee80c60f4b3f932a1871da82267891a6
  metric_id: VNM_5m_z
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Canonical metric source/horizon/numeric/availability dependencies unchanged; F-005 in original
    predicate narrative is NOT an enclosing requirement here. No BTC classifier object is produced.
  dependency_binding_ref: DEP-R3-BTC-C015-5M-VNM
- predicate_definition_ref: TR-R-023
  predicate_definition_sha256: 5fbf30534eed6308f123d3565e4d0b774e9ea88b2cf6451e3f6fcf0546d49ab8
  metric_id: VNM_5m_z
  scope: BTC
  enclosing_set_direction_requirement: DB-R-BTC-001
  canonical_prerequisites: Canonical metric source/horizon/numeric/availability dependencies unchanged; F-005 in original
    predicate narrative is NOT an enclosing requirement here. No BTC classifier object is produced.
  dependency_binding_ref: DEP-R3-BTC-C015-5M-VNM
revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
candidate_instantiation_ref:
  candidate_id: C-015
  non_btc_variant: SET-R-015-V2
  non_btc_definition_sha256: ca78a348e7ffb111d152e324ca77cefd07f46507e4b717d5e957c8e1c06d1e89
  selection_authority: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md §6
additional_predicate_interpretation: Inclusive sign compatibility only; valid zero passes the selected side, UNAVAILABLE
  never passes. No direction, veto, reset, maintained-condition, execution or allocation change.
dependency_binding_ref: DEP-R3-BTC-C015-5M-VNM
content_sha256: 3638df0372fa0ded320fe6c44875d107a4b742c35113b9f1345fd1ac7502fa16
```

### 5.R3.D — Canonical BTC-local 5m VNM dependency binding

This object binds existing formulas and existing source requirements; it is not a new metric, formula, classifier, wire field or data substitute. Source selectors/native instrument identities are evidence-backed launch inputs, never guessed historical availability. Every dependency and its ancestry/population proof is exportable. Mean/stddev and activation observations are research evidence over canonical values, not new trading inputs.

```yaml
binding_id: DEP-R3-BTC-C015-5M-VNM
identifier_class: RESEARCH_ONLY_CANONICAL_DEPENDENCY_BINDING
revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
symbol_scope: BTC
owner: Set
canonical_output: VNM_5m_z
predicate_consumers:
- TR-R-022
- TR-R-023
direction_authority: DB-R-BTC-001; unchanged raw completed-5m RETURN branch; VNM sign never supplies direction
launch_source_binding:
  instrument_ref: UNIVERSE-CORE-V1.BTC evidence-backed native instrument manifest
  as_of: Same persisted completed-5m analytical cutoff T used by the enclosing Set
  data: Actual completed BTC 5m OHLC, factual immediately preceding close, source revision/series identity, finality,
    complete ordered range/page/snapshot proof
  source_contract: api-contracts/MARKET_DATA_REQUEST.md §§2–6, L8–46
  available_history_only: true
  synthetic_candles_allowed: false
  required_fields:
  - instrument/native product and units
  - dataset/series ID
  - price basis
  - 5m interval boundaries
  - candle and predecessor IDs
  - source revision
  - coverage/page/snapshot/finality proof
  - availability cutoff
canonical_chain:
- stage: completed_price_and_return
  canonical_reference: RETURN(asset=BTC,horizon=5m)
  source: methodology/SET.md Part II §5 L1804–1832; §16.2 L2561–2587
  binding: Close_t / Close_(t-5m) - 1, completed source closes only; original division eligibility; no raw-return substitution
    for VNM
- stage: separate_5m_true_range_and_wilder_atr
  canonical_reference: A_t_5m
  source: methodology/SET.md Part II §16.2 L2587–2648; schemas/SET_NUMERIC_POLICY.md §3 L33–59
  input_timeframe: 5m
  window: 14
  smoothing: Wilder
  ancestry: Separate same-symbol 5m series, anchor, fourteen consecutive eligible true ranges plus factual initial predecessor
    close, ordered seed source manifest and authentic checkpoint. Never reuse the 15m F-003 state.
  eligibility: 0 <= Low <= Close <= High; finite exact nonnegative source prices; completed, final, continuous, ordered,
    contradiction-free inputs with immediate predecessor. No skipped malformed/missing candle, stale carry-forward, later
    reseed or synthetic source.
  source_arithmetic_reference: TR=max(High-Low,abs(High-prevClose),abs(Low-prevClose)); seed Q36(sum first14 TR /14);
    recurrence Q36((13*prior_5m_ATR+TR)/14). These are source restatements, not new research formulas.
  checkpoint: Seed manifest, source/policy IDs, last processed ordered candle, exact prior/current work state and checkpoint
    digest; authentic matching restore plus ordered subsequent replay; source revisions invalidate affected derived state.
- stage: 5m_volatility_percentage
  canonical_reference: ATR_PCT_5m
  source: methodology/SET.md Part II §16.2 L2611–2641
  binding: 'With available A_t_5m and positive current completed5m close: Q36(100*A_t_5m/Close_t_5m), then percent-to-decimal
    division by100 for VNM.'
  zero_close: Otherwise eligible zero-close candle retains TR/ATR ancestry update, but ATR_PCT quotient is not evaluated
    and output is UNAVAILABLE.
- stage: local_vnm
  canonical_reference: VNM_5m
  source: methodology/SET.md Part II §16 L2512–2524; §16.2 L2561–2648
  binding: Existing RETURN(5m) / ATR_PCT_decimal_5m with its original Q36 named-output numeric policy.
  unavailable: Unavailable ATR_PCT or nonpositive denominator makes VNM_5m UNAVAILABLE; raw return and 15m ATR are prohibited
    substitutes.
- stage: completed_utc_day_population
  canonical_reference: same-symbol completed5m VNM ordinary reference population
  source: methodology/SET.md Part II §6 L1836–1961; §16.2 L2576–2587
  lookback: 30 completed UTC calendar days [D-30 days,D), where D is current UTC-day start at evaluation cutoff
  minimum_warmup: 14 eligible completed UTC days, with only the source-proven inception/leading-initialization exception
    permitting14–29 days; not discretionary shortening
  membership: Original completed candle/derived-observation membership and exact half-open boundaries. Current incomplete
    UTC day excluded even if some bars are complete. No later missing/invalid days or observations skipped; no trailing-hours
    or accounting-day substitute.
  ancestry_independence: Recursive5m ATR ancestry continues through the proven initialization prefix; population window
    does not reset or reseed it.
  population_evidence:
  - exact UTC boundaries
  - inception/first-countable-day proof if used
  - ordered included VNM source/work-value IDs
  - countable-day coverage
  - pagination/snapshot/finality
  - missing-day reasons
- stage: normalization
  canonical_reference: VNM_5m_z
  source: methodology/SET.md Part II §7 L1965–2011; schemas/SET_NUMERIC_POLICY.md §§2,4,7
  mean: Arithmetic mean of stored canonical same-symbol5m VNM population values
  stddev: Population standard deviation, ddof=0; exact variance and correctly HALF_EVEN-rounded Q36 sqrt per numeric
    policy
  binding: Existing centered z=(current VNM_5m - population mean)/population stddev, canonical work-grid output
  undefined: Zero work standard deviation or otherwise undefined normalization -> UNAVAILABLE; never zero z-score, winsorization,
    robust-z, epsilon or alternative normalization
- stage: additional_current_state_predicate
  canonical_reference: TR-R-022 / TR-R-023 over VNM_5m_z
  binding: LONG>=0; SHORT<=0, inclusive; valid0 passes the branch-specific compatibility test; UNAVAILABLE is not FALSE/zero/economic
    opposition.
  no_veto_change: The canonical ±2 local contradiction veto and non-BTC F-005 are unchanged. BTC does not invoke that
    classifier or acquire a new veto gate; any unavailable classifier-veto evidence is explicitly not produced.
numeric_policy:
  id: TT_SET_NUMERIC_V1
  work: Q36 HALF_EVEN at named outputs; exact inner arithmetic, no binary floats or display-rounded comparisons
  wire: No new wire field. Existing authorized diagnostic export rounding cannot feed the research Set gate.
unavailable_propagation: Any missing/invalid required price,5m ancestry,VNM population or normalization proof yields
  unavailable dependency/predicate and no qualified variant match; log DATA_UNAVAILABLE separately from valid side disagreement.
zero_mean_qualification: For a valid population mean exactly0 and positive sigma/denominator, the BTC raw-return branch
  may imply the VNM z-sign condition. Preserve zero valid disagreements; no threshold/mean/population change to force
  activation.
formula_semantics_changed: false
new_trading_metric: false
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§4–7
  SOURCE_LINES: 1766–2011
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §16.2; §18
  SOURCE_LINES: 2561–2648; 2677–2697
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
content_sha256: 4615856700cf3b958dca199a4f30cad2c13a20bce1cae0058e74276c1e5a2ddd
```

## 6. Corrected Portfolio configurations

Only201–209 have corrected configuration identities. All contain ten10% weights and exact100% total. PR-R-203 is the required historical-successor alias of103, equal to201 in canonical fields; it is not selected or launch-authorized. Historical predecessor definitions remain byte-exact in the provenance archive. Global cap and slot/minimum/cooldown/DailyLoss fields are independently preserved.

| Predecessor PR config | Corrected immutable config | Current role |
|---|---|---|
| PR-R-101 | PR-R-201 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-102 | PR-R-202 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-103 | PR-R-203 | Unselected historical successor alias; not a hypothesis |
| PR-R-104 | PR-R-204 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-105 | PR-R-205 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-106 | PR-R-206 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-107 | PR-R-207 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-108 | PR-R-208 | Canonical fields preserved except all allocations fixed at 10% |
| PR-R-109 | PR-R-209 | Canonical fields preserved except all allocations fixed at 10% |

### PR-R-201

```yaml
config_id: PR-R-201
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-101
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-101
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 602be6d5e174a4e2ca087ebdb1dc1d69df3d441df52780b5f42b632e7dc47474
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: 0da3ab9175503da2fc56dd29d08ab775c63917ac7c2c1e67d3f1ef885554ce0d
```

### PR-R-202

```yaml
config_id: PR-R-202
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '40'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-102
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-102
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 5671b240bbfedcb7b2af92e6858f1f01890fbbc138649dfa4a1c38f6e01fcbe7
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: a6caed8ef20d30de604c70257396b300789359f7f7b2ef251067d6ff45bd6484
```

### PR-R-203

```yaml
config_id: PR-R-203
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-103
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-103
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 43b426179c8edce8d2d6a7fd074c03760928eebe46faa2d7387c823aef5b9df7
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: HISTORICAL_SUCCESSOR_ALIAS_NOT_SELECTED
alias_note: After mandatory allocation correction this has the same canonical fields as PR-R-201. It is NOT an R-023
  variant, is not launch-authorized, and creates no hypothesis. Old PR-R-103 body remains historical only.
content_sha256: 46665ed26ccc529f74a00883ef81c7cf284158214e69ec568065124a0a802126
```

### PR-R-204

```yaml
config_id: PR-R-204
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 3
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-104
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-104
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 39cc1d638ad429a703d4e14006821281885aad49eea4f800cd7a304ef360b34d
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: f7ede6b817523d42176765c91a1796824467be23c613c012dda4c4e7a61c0fa9
```

### PR-R-205

```yaml
config_id: PR-R-205
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 3
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-105
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-105
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 61e48095d609d0af931e13b2e7530835411ecd10eeb856cce5a619c89c84ebb8
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: 29670dbb8b4d282426af5dc51124ff78b7b0fdbfdfce9197dfb5a3483c62c7b0
```

### PR-R-206

```yaml
config_id: PR-R-206
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '50'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-106
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-106
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 9fb53875e43aeda5be6c3960ffbb01762f8a43b536d4c530670a7ef41695795d
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: cf7d2fd983590d0163123046e1356605d4b6fe83827af658be1fd54380da3abc
```

### PR-R-207

```yaml
config_id: PR-R-207
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: false
    pct: '5'
  cooldown_minutes: 15
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-107
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-107
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: ac12a1350160d1bdda71ea44b0450f2d7b6e7b13873bc384e5e885f3a85b7942
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: 4eb88c80ff422d20407a77e1969282291ef0b1a265081d94eb45e949ff4d8aa4
```

### PR-R-208

```yaml
config_id: PR-R-208
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: true
    pct: '5'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-108
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-108
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 180349f0b973cd2c14a1b8360d9cceae4e610fd0bae35ec0724147f264746493
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: a95d890d7bd802f6a83a2c33ab9f60a1a926443baed831af851187c4b8d97ce7
```

### PR-R-209

```yaml
config_id: PR-R-209
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  max_capital_in_positions_pct: '60'
  max_open_positions: 6
  max_positions_per_coin: 2
  minimum_tranche_capital: '25'
  daily_loss_limit:
    enabled: true
    pct: '3'
  cooldown_minutes: 5
  coins:
  - symbol: BTC
    enabled: true
    allocation_pct: '10'
  - symbol: ETH
    enabled: true
    allocation_pct: '10'
  - symbol: SOL
    enabled: true
    allocation_pct: '10'
  - symbol: XRP
    enabled: true
    allocation_pct: '10'
  - symbol: DOGE
    enabled: true
    allocation_pct: '10'
  - symbol: SUI
    enabled: true
    allocation_pct: '10'
  - symbol: PEPE
    enabled: true
    allocation_pct: '10'
  - symbol: AVAX
    enabled: true
    allocation_pct: '10'
  - symbol: LINK
    enabled: true
    allocation_pct: '10'
  - symbol: BNB
    enabled: true
    allocation_pct: '10'
binding_note: 'Research-only configuration: exactly ten immutable 10% allocations, sum 100%. Global cap is a separate
  own-capital constraint. No reweighting, redistribution, or allocation intervention.'
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§6–8
  SOURCE_LINES: 288–358
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§2–3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §1.2; FCR-ALLOC-01; §7.2
derived_from_research_config_id: PR-R-109
configuration_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
universe_version: UNIVERSE-CORE-V1
derived_from:
  config_id: PR-R-109
  profile_revision: RESEARCH_V1_FINALIZATION_R1
  definition_sha256: 77f92d1227c95abdb734a4746649b60e101fc2b4ae94c60c1a03698ce3a86174
campaign_allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
admission: CAMPAIGN_CONFIGURATION
content_sha256: d744b599b7fc5e457a6a6fede839cca0fcef4b7fb479b71d468944f58c12aa68
```

## 7. Position Rules configurations — unchanged

The existing research binding key `MIN_DISTANCE_ATR` refers to the source parameter written `MIN_DISTANCE = 0.50 ATR` in Part III §39. It changes that research calibration value only; the min/max construction in §23 and the frozen default specification remain unchanged. This is not an added canonical wire field.

C-036 uses the already defined POS-R-007, not a new algorithm. POS-R-001/007 differ only in MIN_DISTANCE_ATR0.50/0.75. The original16 configuration bodies follow without modification.

### POS-R-001

```yaml
config_id: POS-R-001
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-002

```yaml
config_id: POS-R-002
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.25'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-003

```yaml
config_id: POS-R-003
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '2.00'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-004

```yaml
config_id: POS-R-004
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.50'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-005

```yaml
config_id: POS-R-005
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: FIXED
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-006

```yaml
config_id: POS-R-006
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.40'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-007

```yaml
config_id: POS-R-007
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.75'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-008

```yaml
config_id: POS-R-008
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '1.50'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-009

```yaml
config_id: POS-R-009
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.50'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-010

```yaml
config_id: POS-R-010
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '1.25'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-011

```yaml
config_id: POS-R-011
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '3.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-012

```yaml
config_id: POS-R-012
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: true
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-013

```yaml
config_id: POS-R-013
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: true
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-014

```yaml
config_id: POS-R-014
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '2'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-015

```yaml
config_id: POS-R-015
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: true
    value: '2.5'
  minimum_net_edge:
    enabled: false
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '1.25'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

### POS-R-016

```yaml
config_id: POS-R-016
identifier_class: RESEARCH_ONLY_NOT_EXISTING_PROJECT_VERSION
methodology_supported_fields:
  stop_loss:
    mode: DYNAMIC
    fixed_pct: '1'
  take_profit:
    mode: DYNAMIC
    fixed_pct: null
  minimum_risk_reward:
    enabled: false
    value: '2'
  minimum_net_edge:
    enabled: true
    pct: '1'
  leverage:
    value: '1'
methodology_parameter_bindings:
  MIN_ENTRY_IMPROVEMENT_ATR: '0.10'
  MAX_ENTRY_DEVIATION_ATR: '2.00'
  BUFFER_ATR_MULTIPLIER: '0.20'
  MIN_DISTANCE_ATR: '0.50'
  MAX_DISTANCE_ATR: '2.00'
  CORROBORATION_DISTANCE_ATR: '0.25'
  MIN_TP_DISTANCE_ATR: '0.75'
  MAX_TP_DISTANCE_ATR: '4.00'
binding_note: Parameter bindings point to existing versioned methodology research constants; this is not a claim
  that they are native Position user/wire fields. fixed_pct=1 is pinned but ignored while Stop mode is DYNAMIC.
  No Fixed TP substitute is used.
TRACEABILITY:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
```

## 8. Normalized final research and symbol-scoped arm registry

Exactly30 current records. Original question wording is preserved for the nine non-BTC subjects. BTC R008/R010 use the Set direction-qualification instantiation described in the final records and focused council. A missing symbol key is invalid; R006 BTC is explicitly null with NOT_APPLICABLE—not missing, zero-performance, or a request to redistribute allocation.

### R-001 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-001
candidate_id: C-001
title: Displacement magnitude selectivity
primary_question: Does requiring a 1.00% rather than 0.50% canonical 1m displacement improve outcomes conditional on
  the unchanged classifier?
primary_axis: AX-01
primary_changed_variable: 'F-001 theta_move_pct: 0.50 -> 1.00'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-002
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-030
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V2
      ETH: SET-R-001-V2
      SOL: SET-R-001-V2
      XRP: SET-R-001-V2
      DOGE: SET-R-001-V2
      SUI: SET-R-001-V2
      PEPE: SET-R-001-V2
      AVAX: SET-R-001-V2
      LINK: SET-R-001-V2
      BNB: SET-R-001-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-001
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 886d3ff962378a50e1820768587a2ac9b42ca8a08d2a6822955124c1ff1ae537
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-002 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-002
candidate_id: C-003
title: Participation confirmation
primary_question: Does adding the fixed F-002 volume-surge predicate improve selection over displacement plus F-005 alone?
primary_axis: AX-02
primary_changed_variable: 'F-002 membership: absent -> required'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- F-002 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-003-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-003-V2
      ETH: SET-R-003-V2
      SOL: SET-R-003-V2
      XRP: SET-R-003-V2
      DOGE: SET-R-003-V2
      SUI: SET-R-003-V2
      PEPE: SET-R-003-V2
      AVAX: SET-R-003-V2
      LINK: SET-R-003-V2
      BNB: SET-R-003-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - F-002 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-002
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: e2474c5056298d2d5d380c0112f1738d617b0c7537ca89efef1451c3636a04dd
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-003 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-003
candidate_id: C-007
title: Directional efficiency confirmation
primary_question: Does an additional DE>=0.50 confirmation improve selection beyond the unchanged DE>=0.30 hard gate?
primary_axis: AX-03
primary_changed_variable: 'Additional DE confirmation: absent -> DE>=0.50'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-006
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-007-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-007-V2
      ETH: SET-R-007-V2
      SOL: SET-R-007-V2
      XRP: SET-R-007-V2
      DOGE: SET-R-007-V2
      SUI: SET-R-007-V2
      PEPE: SET-R-007-V2
      AVAX: SET-R-007-V2
      LINK: SET-R-007-V2
      BNB: SET-R-007-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§11–12
  SOURCE_LINES: 2317–2405
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-003
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: fed9be76a82d127f1a617723c8064ebe8ba324697d427131e851680081570f17
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-004 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-004
candidate_id: C-008
title: Central volatility band
primary_question: Does adding the preregistered ATR-percentile interval [30,85] improve selection inside the unchanged
  [15,97] gate?
primary_axis: AX-04
primary_changed_variable: 'Additional central-volatility interval predicate: absent -> inclusive [30,85]'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-007
- TR-R-008
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-008-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-008-V2
      ETH: SET-R-008-V2
      SOL: SET-R-008-V2
      XRP: SET-R-008-V2
      DOGE: SET-R-008-V2
      SUI: SET-R-008-V2
      PEPE: SET-R-008-V2
      AVAX: SET-R-008-V2
      LINK: SET-R-008-V2
      BNB: SET-R-008-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§13–15
  SOURCE_LINES: 2410–2508
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-004
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: b2cffbedb4704b324f2a11bd787d4c191fe4051eb60634369dd4a342195fa0c4
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-005 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-005
candidate_id: C-009
title: Higher-timeframe structural agreement
primary_question: Does requiring the 1h swing-sequence state to agree with classifier direction improve selection?
primary_axis: AX-05
primary_changed_variable: 'Side-aligned 1h structural confirmation: absent -> required'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- SWING_SEQUENCE_STATE(asset,1h)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-009
- TR-R-010
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-009-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-009-V2
      ETH: SET-R-009-V2
      SOL: SET-R-009-V2
      XRP: SET-R-009-V2
      DOGE: SET-R-009-V2
      SUI: SET-R-009-V2
      PEPE: SET-R-009-V2
      AVAX: SET-R-009-V2
      LINK: SET-R-009-V2
      BNB: SET-R-009-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§9–10
  SOURCE_LINES: 2136–2313
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §28
  SOURCE_LINES: 2962–2996
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-005
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: e5810bbd1aa32bcba3fff3b8b9f131f8c2bc2b9796b0829aad7db97e17979c47
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-006 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-006
candidate_id: C-010
title: Raw relative-return agreement
primary_question: Does requiring raw 15m asset-versus-BTC relative return to agree with direction improve selection?
primary_axis: AX-06
primary_changed_variable: 'Side-aligned RELATIVE_RETURN_15m sign confirmation: absent -> required'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- BTC_CONTEXT_SCORE
- F-001 trigger_result
- RELATIVE_RETURN_15m
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-011
- TR-R-012
- TR-R-029
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: null
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: NOT_APPLICABLE
        reason: SOURCE_LOGIC_NOT_MEANINGFUL_FOR_BTC
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-010-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: null
      ETH: SET-R-010-V2
      SOL: SET-R-010-V2
      XRP: SET-R-010-V2
      DOGE: SET-R-010-V2
      SUI: SET-R-010-V2
      PEPE: SET-R-010-V2
      AVAX: SET-R-010-V2
      LINK: SET-R-010-V2
      BNB: SET-R-010-V2
    symbol_applicability:
      BTC:
        status: NOT_APPLICABLE
        reason: SOURCE_LOGIC_NOT_MEANINGFUL_FOR_BTC
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§19–20
  SOURCE_LINES: 2701–2755
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: NOT_APPLICABLE
    metric_refs: []
    direction_authority: NONE_FOR_THIS_QUESTION
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-006
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 76a03a70d3da45fe2aa3754ab1d30e2c8a723083363a79f3a5e18bf5476aebee
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-007 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-007
candidate_id: C-011
title: Aggressive-flow agreement
primary_question: Does requiring signed 5m aggressive-volume imbalance to agree with direction improve selection?
primary_axis: AX-07
primary_changed_variable: 'Side-aligned aggressive-flow confirmation: absent -> required'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- AGGRESSIVE_VOLUME_DELTA_PCT
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-013
- TR-R-014
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-011-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-011-V2
      ETH: SET-R-011-V2
      SOL: SET-R-011-V2
      XRP: SET-R-011-V2
      DOGE: SET-R-011-V2
      SUI: SET-R-011-V2
      PEPE: SET-R-011-V2
      AVAX: SET-R-011-V2
      LINK: SET-R-011-V2
      BNB: SET-R-011-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§21–23
  SOURCE_LINES: 2760–2858
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - AGGRESSIVE_VOLUME_DELTA_PCT
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - AggBuyNotional
    - AggSellNotional
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-007
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: dc088b75ba8a85b6dbb8a3c9d10d606c3e8a671d4ba97192c34c1ea6e671e743
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-008 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-008
candidate_id: C-016
title: New classifier episode
primary_question: Does admitting only a newly true classifier-side predicate improve selection versus ongoing current
  qualification?
primary_axis: AX-12
primary_changed_variable: 'Classifier-direction predicate role: CURRENT_STATE -> same-cutoff FRESH_EVENT'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-015
- TR-R-016
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-003
- TR-R-BTC-004
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-016-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-016-V2
      ETH: SET-R-016-V2
      SOL: SET-R-016-V2
      XRP: SET-R-016-V2
      DOGE: SET-R-016-V2
      SUI: SET-R-016-V2
      PEPE: SET-R-016-V2
      AVAX: SET-R-016-V2
      LINK: SET-R-016-V2
      BNB: SET-R-016-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §10
  SOURCE_LINES: 1132–1211
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §17
  SOURCE_LINES: 1448–1466
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-008
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 46a024219f74582dd2fa0a7a437d5a0776115f1e4d8ecae7d1110239354ade08
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-009 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-009
candidate_id: C-019
title: Ordered price then participation
primary_question: Does allowing canonical displacement before participation outperform simultaneous coincidence?
primary_axis: AX-15
primary_changed_variable: 'Trigger composition: simultaneous AND -> strict ordered sequence'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- F-002 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-019-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-019-V1
      ETH: SET-R-019-V1
      SOL: SET-R-019-V1
      XRP: SET-R-019-V1
      DOGE: SET-R-019-V1
      SUI: SET-R-019-V1
      PEPE: SET-R-019-V1
      AVAX: SET-R-019-V1
      LINK: SET-R-019-V1
      BNB: SET-R-019-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-019-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-019-V2
      ETH: SET-R-019-V2
      SOL: SET-R-019-V2
      XRP: SET-R-019-V2
      DOGE: SET-R-019-V2
      SUI: SET-R-019-V2
      PEPE: SET-R-019-V2
      AVAX: SET-R-019-V2
      LINK: SET-R-019-V2
      BNB: SET-R-019-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§11–12
  SOURCE_LINES: 1213–1243
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - F-002 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-009
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 61b1b037b1929739714d5be4994280336b78c4c1c30cf22662c65832005a858e
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-010 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-010
candidate_id: C-020
title: Direction maintained through formation
primary_question: Does requiring the classifier-side predicate to remain true throughout the price-to-volume sequence
  improve selection?
primary_axis: AX-16
primary_changed_variable: 'Maintained classifier direction: endpoint-only -> all intervening completed-5m evaluations'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- F-002 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-020-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-020-V1
      ETH: SET-R-020-V1
      SOL: SET-R-020-V1
      XRP: SET-R-020-V1
      DOGE: SET-R-020-V1
      SUI: SET-R-020-V1
      PEPE: SET-R-020-V1
      AVAX: SET-R-020-V1
      LINK: SET-R-020-V1
      BNB: SET-R-020-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-020-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-020-V2
      ETH: SET-R-020-V2
      SOL: SET-R-020-V2
      XRP: SET-R-020-V2
      DOGE: SET-R-020-V2
      SUI: SET-R-020-V2
      PEPE: SET-R-020-V2
      AVAX: SET-R-020-V2
      LINK: SET-R-020-V2
      BNB: SET-R-020-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §13
  SOURCE_LINES: 1247–1259
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §§11–12
  SOURCE_LINES: 1213–1243
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - F-002 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-010
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 096ecedc191f090542447b62b40dfdb4e9307938d90e64574a266d3bcafa5506
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-011 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-011
candidate_id: C-021
title: Participation conjunction versus disjunction
primary_question: Does requiring both F-002 and TOD confirmation improve selection versus permitting either?
primary_axis: AX-17
primary_changed_variable: 'Participation composition: AND -> OR with identical member predicates'
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- F-002 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-017
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-021-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-021-V1
      ETH: SET-R-021-V1
      SOL: SET-R-021-V1
      XRP: SET-R-021-V1
      DOGE: SET-R-021-V1
      SUI: SET-R-021-V1
      PEPE: SET-R-021-V1
      AVAX: SET-R-021-V1
      LINK: SET-R-021-V1
      BNB: SET-R-021-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-021-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-021-V2
      ETH: SET-R-021-V2
      SOL: SET-R-021-V2
      XRP: SET-R-021-V2
      DOGE: SET-R-021-V2
      SUI: SET-R-021-V2
      PEPE: SET-R-021-V2
      AVAX: SET-R-021-V2
      LINK: SET-R-021-V2
      BNB: SET-R-021-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §9
  SOURCE_LINES: 1082–1128
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §8
  SOURCE_LINES: 2013–2131
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - F-002 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-011
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: ede3c53b568f0e97955df976b6fb086d95775cf83ef670035d5f6343af12e0ca
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-012 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-012
candidate_id: C-031
title: Entry minimum improvement
primary_question: Does a deeper minimum Entry improvement change results?
primary_axis: AX-23
primary_changed_variable: methodology_parameter_bindings.MIN_ENTRY_IMPROVEMENT_ATR -> 0.25
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-002
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-012
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 41f55ad7ffea72b735f39787d2bcf3fba220869802e0beab23b088f0fb34899e
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-013 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-013
candidate_id: C-032
title: Entry maximum deviation
primary_question: Does a wider Entry-deviation allowance improve results?
primary_axis: AX-24
primary_changed_variable: methodology_parameter_bindings.MAX_ENTRY_DEVIATION_ATR -> 2.00
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-003
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-013
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 16ed067b6adf7e5ef55c3f3b29cb882b55b794ce4fd17009fd6589ec9186a6ef
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-014 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-014
candidate_id: C-034
title: Dynamic versus fixed Stop dispatch
primary_question: Does fixed 1% Stop dispatch improve results relative to Dynamic Stop?
primary_axis: AX-25
primary_changed_variable: methodology_supported_fields.stop_loss.mode -> FIXED
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-005
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§9–10
  SOURCE_LINES: 274–365
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-014
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 25285089ead157ab4e8c39358f7a103ea6967c6eb0707a7c44e1698c5188aa5d
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-015 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-015
candidate_id: C-035
title: Dynamic Stop buffer
primary_question: Does a larger structural Stop buffer improve results?
primary_axis: AX-26
primary_changed_variable: methodology_parameter_bindings.BUFFER_ATR_MULTIPLIER -> 0.40
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-006
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-015
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 20bbcbede685e149a0a85d37bea5126aafb3d877b3084d46c37bf40ce8e542f2
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-016 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-016
candidate_id: C-037
title: Dynamic Stop maximum risk
primary_question: Does a tighter maximum Stop-risk limit improve results?
primary_axis: AX-28
primary_changed_variable: methodology_parameter_bindings.MAX_DISTANCE_ATR -> 1.50
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-008
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-016
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 98a0c376b6753719dc48802d179425ffa2a3a75f7493230f0b66012d49422315
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-017 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-017
candidate_id: C-039
title: Dynamic TP minimum distance
primary_question: Does a larger minimum target distance improve results?
primary_axis: AX-30
primary_changed_variable: methodology_parameter_bindings.MIN_TP_DISTANCE_ATR -> 1.25
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-010
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-017
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: c35dec3a48390b59f7034aa33c70fa8f73d6893eb147eb905e9e8a471f33fd0f
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-018 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-018
candidate_id: C-040
title: Dynamic TP maximum distance
primary_question: Does a tighter maximum target distance improve results?
primary_axis: AX-31
primary_changed_variable: methodology_parameter_bindings.MAX_TP_DISTANCE_ATR -> 3.00
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-011
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§3–32
  SOURCE_LINES: 4320–5056
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part IV §§47–48
  SOURCE_LINES: 5449–5486
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-018
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 31deba7cf3f88022db90ed3a81625bf648e37a721e73c4472e93928862aec876
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-019 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-019
candidate_id: C-041
title: Structural reward-to-risk gate
primary_question: Does enabling minimum gross R:R=2 improve selection?
primary_axis: AX-32
primary_changed_variable: methodology_supported_fields.minimum_risk_reward.enabled -> True
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-012
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §39
  SOURCE_LINES: 1332–1366
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §14
  SOURCE_LINES: 465–517
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-019
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 66630f604696d915cac954b84d13948f4a145aeadb433a12fc94ffd7e01a9d30
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-020 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-020
candidate_id: C-042
title: Planned net-edge gate
primary_question: Does enabling minimum planned net edge of 1% of actual notional improve selection?
primary_axis: AX-33
primary_changed_variable: methodology_supported_fields.minimum_net_edge.enabled -> True
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-013
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §40
  SOURCE_LINES: 1370–1436
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-020
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: dfd6dee89d63325174dbe68f5372c4e1a660e04fa2c07b6acce372de640e0e12
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-021 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-021
candidate_id: C-043
title: Leverage in exact construction
primary_question: Does leverage 2 rather than 1 change results under identical own-capital policy?
primary_axis: AX-34
primary_changed_variable: methodology_supported_fields.leverage.value -> 2
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-014
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §22
  SOURCE_LINES: 837–880
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§17–22A
  SOURCE_LINES: 576–908
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §§23–40
  SOURCE_LINES: 912–1436
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-021
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: c8c938ab4550767b51d8ecf21cb707dddc31900ff1013a60ae54d10d9e185093
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-022 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-022
candidate_id: C-012
title: BTC contextual agreement
primary_question: Does stronger positive-side BTC context improve selection beyond non-contradiction?
primary_axis: AX-08
primary_changed_variable: Additional BTC_CONTEXT_SCORE sign confirmation
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-018
- TR-R-019
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-012-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-012-V2
      ETH: SET-R-012-V2
      SOL: SET-R-012-V2
      XRP: SET-R-012-V2
      DOGE: SET-R-012-V2
      SUI: SET-R-012-V2
      PEPE: SET-R-012-V2
      AVAX: SET-R-012-V2
      LINK: SET-R-012-V2
      BNB: SET-R-012-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 2863–2958
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §5; §§9–12
  SOURCE_LINES: 509–530; 1082–1260
- SOURCE_DOCUMENT: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md
  SOURCE_SECTION: §§5–6; approved replacement application
- SOURCE_DOCUMENT: RESEARCH_V1_R2_REPLACEMENT_PAIRWISE_CHECKS.md
  SOURCE_SECTION: All 57 affected relationships
- SOURCE_DOCUMENT: Mechanical Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§3–15; §§26–28
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-022
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 963545280af43ffb649323cc3d022d88fd69463473a1a9ff2c4b78b5e1cb1566
  migration: APPROVED_REPLACEMENT; historical results never relabeled or pooled
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
activation_evidence_requirements:
  evidence_namespace: RESEARCH_ONLY; joins/read-only observations, never trading metric/state/input
  required:
  - research_id+research_revision+run_id+arm+symbol+cutoff
  - direction-qualified evaluation and original authority
  - BTC_CONTEXT_SCORE work value, availability, source/metric version and original inputs
  - TR-R-018/019 side predicate truth
  - 'original BTC contradiction-veto result where actually produced by non-BTC F-005; BTC: NOT_PRODUCED_BY_F005, retain
    source-context and unchanged pending-condition evidence instead'
  - baseline/variant valid predicate disagreement at common source cutoff
  - Set epoch/formation/MATCHED or rejection/unavailability
  - Position decision/construction; Portfolio request/grant/authorization fate
  - dispatch/acceptance/fill/protection/close/finality facts
  - report population membership and revision
  - intrabar frontier, endpoint exposure, completeness
  distinction:
  - valid predicate disagreement
  - actual executable downstream difference
  - finalized economic difference
  missing_evidence_is_economic_rejection: false
  BTC_qualification: 'High/nested dependence with R-005 on BTC: aligned unambiguous1h BTC structure can imply compatible
    context sign. Not independent BTC trend evidence; nine non-BTC subjects compare own structure versus external BTC
    context.'
```

### R-023 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-023
candidate_id: C-036
title: Dynamic Stop minimum risk
primary_question: Does a larger minimum risk-distance floor improve results?
primary_axis: AX-27
primary_changed_variable: methodology_parameter_bindings.MIN_DISTANCE_ATR -> 0.75
class: POSITION_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-007
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §§3–30
  SOURCE_LINES: 3316–3974
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part III §39
  SOURCE_LINES: 4238–4249
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-023
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: d776077dc0ea367c58d0d89f5e7737dd53b5e7bbee2f39732bafa0f3cad88894
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-024 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-024
candidate_id: C-051
title: Global slot pressure
primary_question: Does reducing global slots from six to three improve portfolio results?
primary_axis: AX-37
primary_changed_variable: methodology_supported_fields.max_open_positions -> 3
class: PORTFOLIO_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-204
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-024
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 5ac0ea03a0a6641a8acfc3cef198b4629d59ce990ac2bec4497306ae0138a269
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-025 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-025
candidate_id: C-052
title: Per-coin slots and grant division
primary_question: Does increasing per-coin slots improve results under the coupled sizing rule?
primary_axis: AX-38
primary_changed_variable: methodology_supported_fields.max_positions_per_coin -> 3
class: PORTFOLIO_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-205
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§11–17
  SOURCE_LINES: 484–633
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§18–22
  SOURCE_LINES: 638–772
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-025
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: deeabac1fbdc5e324c173d678fa5921052c64afcc0eda94457cfabd3d8da514d
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-026 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-026
candidate_id: C-015
title: Local-momentum agreement
primary_question: Does requiring the 5m local VNM z-score to agree with direction improve selection?
primary_axis: AX-11
primary_changed_variable: Additional same-side VNM_5m_z sign confirmation
class: SET_LAYER
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- VNM_5m_z
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-022
- TR-R-023
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-015-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-015-V2
      ETH: SET-R-015-V2
      SOL: SET-R-015-V2
      XRP: SET-R-015-V2
      DOGE: SET-R-015-V2
      SUI: SET-R-015-V2
      PEPE: SET-R-015-V2
      AVAX: SET-R-015-V2
      LINK: SET-R-015-V2
      BNB: SET-R-015-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§16–18
  SOURCE_LINES: 2512–2697
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§4–7
  SOURCE_LINES: 1766–2011
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §16.2; §18
  SOURCE_LINES: 2561–2648; 2677–2697
- SOURCE_DOCUMENT: RESEARCH_V1_R2_R022_R026_REPLACEMENT_REVIEW.md
  SOURCE_SECTION: §§5–6; approved replacement application
- SOURCE_DOCUMENT: RESEARCH_V1_R2_REPLACEMENT_PAIRWISE_CHECKS.md
  SOURCE_SECTION: All 57 affected relationships
- SOURCE_DOCUMENT: Mechanical Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§3–15; §§26–28
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_5m
    - ATR_PCT_work
    - ATR_work
    - A_t_5m
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - VNM_5m
    - VNM_5m_z
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
    dependency_binding_ref: DEP-R3-BTC-C015-5M-VNM
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-026
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 19ab1fcf16b2e0d6615334d61a71d72efa7192702fc3e937d9787c524a1f9ec9
  migration: APPROVED_REPLACEMENT; historical results never relabeled or pooled
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
activation_evidence_requirements:
  evidence_namespace: RESEARCH_ONLY; read-only existing evidence/counts, never trading inputs
  required:
  - research_id+research_revision+run_id+arm+symbol+cutoff
  - direction-qualified evaluation and original authority
  - RETURN(asset,5m), A_t_5m, ATR_PCT_5m, VNM_5m, VNM_5m_z work values and availability
  - separate5m ATR anchor/seed/checkpoint/ordered-source ancestry
  - normalization population boundaries/membership/days, arithmetic mean and ddof=0 stddev provenance
  - source completeness/page/snapshot/finality/cutoff proof
  - 'TR-R-022/023 truth; original ±2 local veto state where non-BTC F-005 produces it; BTC: NOT_PRODUCED_BY_F005 rather
    than invented classifier evidence'
  - valid-disagreement versus unavailable-dependency classification
  - baseline/variant Set difference; Position/Portfolio downstream fate
  - dispatch/fill/protection/exit/finality and reporting population
  - censor/frontier/completeness
  BTC_additional:
  - raw-return branch versus valid centered-z sign disagreement
  - z-score validity independent of its sign
  - exact zero reference mean and resulting zero incremental valid-disagreement evidence where nonbinding
  distinction:
  - valid predicate disagreement
  - actual executable downstream difference
  - finalized economic difference
  unavailable_is_opposition: false
  force_activation: false
  dependency_binding_ref: DEP-R3-BTC-C015-5M-VNM
dependency_binding_refs:
- DEP-R3-BTC-C015-5M-VNM
```

### R-027 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-027
candidate_id: C-054
title: Acceptance-based cooldown
primary_question: Does a longer acceptance-based per-symbol cooldown improve results?
primary_axis: AX-40
primary_changed_variable: methodology_supported_fields.cooldown_minutes -> 15
class: PORTFOLIO_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-207
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-027
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 371f866d4a6f6ffeffb1402395913b6c48ab46d724ef239199ca411d7082e35f
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-028 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-028
candidate_id: C-055
title: Daily realized-loss latch
primary_question: Does enabling the 5% daily realized-loss latch improve results?
primary_axis: AX-41
primary_changed_variable: methodology_supported_fields.daily_loss_limit.enabled -> True
class: PORTFOLIO_RULES
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  baseline:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  variant:
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-208
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §23
  SOURCE_LINES: 776–872
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §§2–4
  SOURCE_LINES: 98–247
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-028
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: b4dd26c2310a9aa9577fed585c943b8311e66b1cc92715a591f4b774fa2464f6
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-029 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-029
candidate_id: C-059
title: Participation × cooldown interaction
primary_question: Does the effect of requiring F-002 depend on cooldown being five versus fifteen minutes?
primary_axis: AX-42
primary_changed_variable: 'Joint factorial contrast: F-002 membership × cooldown_minutes'
class: CROSS_LAYER_INTERACTION
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- F-002 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-003
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  '00':
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '10':
    set: SET-R-003-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-003-V2
      ETH: SET-R-003-V2
      SOL: SET-R-003-V2
      XRP: SET-R-003-V2
      DOGE: SET-R-003-V2
      SUI: SET-R-003-V2
      PEPE: SET-R-003-V2
      AVAX: SET-R-003-V2
      LINK: SET-R-003-V2
      BNB: SET-R-003-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '01':
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-207
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '11':
    set: SET-R-003-V2
    position: POS-R-001
    portfolio: PR-R-207
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-003-V2
      ETH: SET-R-003-V2
      SOL: SET-R-003-V2
      XRP: SET-R-003-V2
      DOGE: SET-R-003-V2
      SUI: SET-R-003-V2
      PEPE: SET-R-003-V2
      AVAX: SET-R-003-V2
      LINK: SET-R-003-V2
      BNB: SET-R-003-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8B
  SOURCE_LINES: 847–1078
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part II §§24–27
  SOURCE_LINES: 876–980
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - F-002 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-029
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: 229c9a15fa12fb34628367fd2ced5c27d11753d5bd1822e47ad723f154574225
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

### R-030 / RESEARCH_V1_FOCUSED_CORRECTION_R2

```yaml
research_id: R-030
candidate_id: C-060
title: Displacement threshold × Entry depth
primary_question: Does the effect of extending Entry maximum deviation depend on requiring a 0.50% versus 1.00% canonical
  displacement?
primary_axis: AX-43
primary_changed_variable: 'Joint factorial contrast: F-001 theta_move_pct × MAX_ENTRY_DEVIATION_ATR'
class: CROSS_LAYER_INTERACTION
metric_refs:
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
direct_trigger_and_monitor_metric_refs:
- ATR percentile
- BTC_CONTEXT_SCORE
- DE
- F-001 trigger_result
- RETURN(asset,5m)
- TOD_REL_TURNOVER
- classifier_direction
canonical_stage_dependency_refs:
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
trigger_refs:
- TR-R-001
- TR-R-002
- TR-R-004
- TR-R-005
- TR-R-029
- TR-R-030
- TR-R-BTC-001
- TR-R-BTC-002
- TR-R-BTC-005
- TR-R-BTC-006
- TR-R-BTC-007
- TR-R-BTC-008
arms:
  '00':
    set: SET-R-001-V1
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '10':
    set: SET-R-001-V2
    position: POS-R-001
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V2
      ETH: SET-R-001-V2
      SOL: SET-R-001-V2
      XRP: SET-R-001-V2
      DOGE: SET-R-001-V2
      SUI: SET-R-001-V2
      PEPE: SET-R-001-V2
      AVAX: SET-R-001-V2
      LINK: SET-R-001-V2
      BNB: SET-R-001-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '01':
    set: SET-R-001-V1
    position: POS-R-003
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V1
      ETH: SET-R-001-V1
      SOL: SET-R-001-V1
      XRP: SET-R-001-V1
      DOGE: SET-R-001-V1
      SUI: SET-R-001-V1
      PEPE: SET-R-001-V1
      AVAX: SET-R-001-V1
      LINK: SET-R-001-V1
      BNB: SET-R-001-V1
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
  '11':
    set: SET-R-001-V2
    position: POS-R-003
    portfolio: PR-R-201
    set_reference_scope: NON_BTC_DEFAULT_ONLY; explicit set_by_symbol is authoritative for execution
    set_by_symbol:
      BTC: SET-R-BTC-001-V2
      ETH: SET-R-001-V2
      SOL: SET-R-001-V2
      XRP: SET-R-001-V2
      DOGE: SET-R-001-V2
      SUI: SET-R-001-V2
      PEPE: SET-R-001-V2
      AVAX: SET-R-001-V2
      LINK: SET-R-001-V2
      BNB: SET-R-001-V2
    symbol_applicability:
      BTC:
        status: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING
        reason: NON_F005_GENERIC_BRANCH_OVER_EXISTING_RETURN_5M
        allocation_pct: '10'
        redistribution: false
backtest_ref:
- BACKTEST_90D
- BACKTEST_30D
- BACKTEST_7D
demo_ref: DEMO_7D
result_refs:
- classifier_direction
- direction_classifier.primary_rejection_stage
- planned_entry_reference
- stop_loss_price
- take_profit_price
- gross_rr
- final_qty
- actual_order_notional
- actual_committed_capital
- net_edge_pct
- daily_realized_pnl
- net_realized_result
- lifecycle_state
- daily_loss_status
decision_ref:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
admission: FINAL_RESEARCH_V1
web_research_executability: 'YES'
blocking_findings: []
traceability:
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part I §8A
  SOURCE_LINES: 617–843
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§50–51
  SOURCE_LINES: 3205–3244
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part II §§3–31
  SOURCE_LINES: 2142–2759
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part II §§34A–37
  SOURCE_LINES: 3155–3435
- SOURCE_DOCUMENT: methodology/SET.md
  SOURCE_SECTION: Part III §43.1
  SOURCE_LINES: 4769–4801
- SOURCE_DOCUMENT: methodology/POSITION_RULES.md
  SOURCE_SECTION: Part I §8
  SOURCE_LINES: 242–270
- SOURCE_DOCUMENT: methodology/PORTFOLIO_RULES.md
  SOURCE_SECTION: Part I §5
  SOURCE_LINES: 251–284
- SOURCE_DOCUMENT: schemas/NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 8–94
- SOURCE_DOCUMENT: schemas/SET_NUMERIC_POLICY.md
  SOURCE_SECTION: §§1–7
  SOURCE_LINES: 19–110
- SOURCE_DOCUMENT: api-contracts/NATIVE_FACT_PROFILE.md
  SOURCE_SECTION: §§1–5 and financial conformance
  SOURCE_LINES: 1–41
- SOURCE_DOCUMENT: methodology/ORDER_LIFECYCLE.md
  SOURCE_SECTION: §§33–34
  SOURCE_LINES: 1343–1377
- SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
  SOURCE_SECTION: §§2–20
  SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
- SOURCE_DOCUMENT: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
  SOURCE_SECTION: §§1–11
  SOURCE_AUTHORITY: RESEARCH_V1_OPERATIONAL_SPECIFICATION
- SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
  SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
- SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
  SOURCE_SECTION: §§2–13, 14–25
report_statistic_refs:
- RR-V1-001
- RR-V1-002
- RR-V1-003
- RR-V1-004
- RR-V1-005
- RR-V1-006
- RR-V1-007
- RR-V1-008
- RR-V1-009
- RR-V1-010
- RR-V1-011
reporting_profile_ref: REPORT-R-V1-R2
evidence_profile_ref: EVIDENCE-R-V1-R2
universe_ref: UNIVERSE-CORE-V1
scope_refs:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
execution_reporting_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md
research_revision: RESEARCH_V1_FOCUSED_CORRECTION_R3
metric_applicability:
  NON_BTC:
    metric_refs:
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
    direction_authority: F-005 / TT-METH-014@0.4.1 / ALTCOIN_VS_BTC
  BTC:
    status: APPLICABLE
    metric_refs:
    - ATR percentile
    - ATR_15m
    - ATR_PCT_15m
    - ATR_PCT_work
    - ATR_work
    - BTC_CONTEXT_SCORE
    - BTC_MOMENTUM_SCORE
    - BTC_RETURN_Z
    - BTC_STRUCTURE_SCORE
    - DE
    - DE_STRENGTH
    - Entry candidate classification
    - F-001 trigger_result
    - PARTICIPATION_STRENGTH
    - PREVIOUS_DAY_HIGH
    - PREVIOUS_DAY_LOW
    - RETURN(BTC,15m)
    - RETURN(asset,15m)
    - RETURN(asset,5m)
    - SWING_HIGH_15M
    - SWING_HIGH_1H
    - SWING_LOW_15M
    - SWING_LOW_1H
    - SWING_SEQUENCE_STATE(BTC,1h)
    - SWING_SEQUENCE_STATE(asset,15m)
    - SWING_SEQUENCE_STATE(asset,1h)
    - TOD_REL_TURNOVER
    - TR_15m
    - actual_committed_capital
    - actual_committed_capital_exact
    - actual_fees_rebates
    - actual_order_notional
    - age_seconds
    - allocated_funding
    - buffer_price
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
    direction_authority: DB-R-BTC-001
    classifier_object_produced: false
    dependency_rule: Only canonical dependencies of actually bound BTC predicates, pending condition and reached downstream
      stages. No F-004 aggregate/relative normalization/F-005 gate/veto/diagnostic is required or fabricated; full union
      list is not a universal prerequisite.
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
intrabar_policy_ref: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
export_root: RESEARCH_RECORD
predecessor_ref:
  research_id: R-030
  revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  definition_sha256: e673aabedd4d54290315fbabfaf92c9c8b7871f4c4ee7744a7171db2213b52e7
  migration: UNCHANGED_SEMANTICS_CARRIED_FORWARD
report_completeness_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§4.5, 6.6
allocation_policy_ref: ALLOC-R-V1-FIXED-10X10
dependency_scope_note: Union across NON_BTC/BTC and reached stages; metric_applicability is authoritative per symbol,
  never fabricate classifier fields on BTC.
```

## 9. Forward and reverse normalized mappings — current R3

| Research revision / ID | Candidate | Baseline Set map | Variant Set map | Position | Portfolio |
|---|---|---|---|---|---|
| R3 / R-001 | C-001 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V2, SET-R-BTC-001-V2 | POS-R-001 | PR-R-201 |
| R3 / R-002 | C-003 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-003-V2, SET-R-BTC-003-V2 | POS-R-001 | PR-R-201 |
| R3 / R-003 | C-007 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-007-V2, SET-R-BTC-007-V2 | POS-R-001 | PR-R-201 |
| R3 / R-004 | C-008 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-008-V2, SET-R-BTC-008-V2 | POS-R-001 | PR-R-201 |
| R3 / R-005 | C-009 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-009-V2, SET-R-BTC-009-V2 | POS-R-001 | PR-R-201 |
| R3 / R-006 | C-010 | baseline: None, SET-R-001-V1 | variant: None, SET-R-010-V2 | POS-R-001 | PR-R-201 |
| R3 / R-007 | C-011 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-011-V2, SET-R-BTC-011-V2 | POS-R-001 | PR-R-201 |
| R3 / R-008 | C-016 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-016-V2, SET-R-BTC-016-V2 | POS-R-001 | PR-R-201 |
| R3 / R-009 | C-019 | baseline: SET-R-019-V1, SET-R-BTC-019-V1 | variant: SET-R-019-V2, SET-R-BTC-019-V2 | POS-R-001 | PR-R-201 |
| R3 / R-010 | C-020 | baseline: SET-R-020-V1, SET-R-BTC-020-V1 | variant: SET-R-020-V2, SET-R-BTC-020-V2 | POS-R-001 | PR-R-201 |
| R3 / R-011 | C-021 | baseline: SET-R-021-V1, SET-R-BTC-021-V1 | variant: SET-R-021-V2, SET-R-BTC-021-V2 | POS-R-001 | PR-R-201 |
| R3 / R-012 | C-031 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-002 | PR-R-201 |
| R3 / R-013 | C-032 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-003 | PR-R-201 |
| R3 / R-014 | C-034 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-005 | PR-R-201 |
| R3 / R-015 | C-035 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-006 | PR-R-201 |
| R3 / R-016 | C-037 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-008 | PR-R-201 |
| R3 / R-017 | C-039 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-010 | PR-R-201 |
| R3 / R-018 | C-040 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-011 | PR-R-201 |
| R3 / R-019 | C-041 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-012 | PR-R-201 |
| R3 / R-020 | C-042 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-013 | PR-R-201 |
| R3 / R-021 | C-043 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-014 | PR-R-201 |
| R3 / R-022 | C-012 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-012-V2, SET-R-BTC-012-V2 | POS-R-001 | PR-R-201 |
| R3 / R-023 | C-036 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001, POS-R-007 | PR-R-201 |
| R3 / R-024 | C-051 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001 | PR-R-201, PR-R-204 |
| R3 / R-025 | C-052 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001 | PR-R-201, PR-R-205 |
| R3 / R-026 | C-015 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-015-V2, SET-R-BTC-015-V2 | POS-R-001 | PR-R-201 |
| R3 / R-027 | C-054 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001 | PR-R-201, PR-R-207 |
| R3 / R-028 | C-055 | baseline: SET-R-001-V1, SET-R-BTC-001-V1 | variant: SET-R-001-V1, SET-R-BTC-001-V1 | POS-R-001 | PR-R-201, PR-R-208 |
| R3 / R-029 | C-059 | 00: SET-R-001-V1, SET-R-BTC-001-V1 | 10: SET-R-003-V2, SET-R-BTC-003-V2; 01: SET-R-001-V1, SET-R-BTC-001-V1; 11: SET-R-003-V2, SET-R-BTC-003-V2 | POS-R-001 | PR-R-201, PR-R-207 |
| R3 / R-030 | C-060 | 00: SET-R-001-V1, SET-R-BTC-001-V1 | 10: SET-R-001-V2, SET-R-BTC-001-V2; 01: SET-R-001-V1, SET-R-BTC-001-V1; 11: SET-R-001-V2, SET-R-BTC-001-V2 | POS-R-001, POS-R-003 | PR-R-201 |

| Canonical metric | Trigger | Referencing current Set versions | Current Research IDs |
|---|---|---|---|
| F-001 trigger_result | TR-R-001 | SET-R-001-V1, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-001-V1, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| F-001 trigger_result | TR-R-002 | SET-R-001-V2, SET-R-BTC-001-V2 | R-001, R-030 |
| F-002 trigger_result | TR-R-003 | SET-R-003-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-003-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-002, R-009, R-010, R-011, R-029 |
| classifier_direction | TR-R-004 | SET-R-001-V1, SET-R-001-V2, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2 | R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| classifier_direction | TR-R-005 | SET-R-001-V1, SET-R-001-V2, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2 | R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| DE | TR-R-006 | SET-R-007-V2, SET-R-BTC-007-V2 | R-003 |
| ATR percentile | TR-R-007 | SET-R-008-V2, SET-R-BTC-008-V2 | R-004 |
| ATR percentile | TR-R-008 | SET-R-008-V2, SET-R-BTC-008-V2 | R-004 |
| SWING_SEQUENCE_STATE(asset,1h) | TR-R-009 | SET-R-009-V2, SET-R-BTC-009-V2 | R-005 |
| SWING_SEQUENCE_STATE(asset,1h) | TR-R-010 | SET-R-009-V2, SET-R-BTC-009-V2 | R-005 |
| RELATIVE_RETURN_15m | TR-R-011 | SET-R-010-V2 | R-006 |
| RELATIVE_RETURN_15m | TR-R-012 | SET-R-010-V2 | R-006 |
| AGGRESSIVE_VOLUME_DELTA_PCT | TR-R-013 | SET-R-011-V2, SET-R-BTC-011-V2 | R-007 |
| AGGRESSIVE_VOLUME_DELTA_PCT | TR-R-014 | SET-R-011-V2, SET-R-BTC-011-V2 | R-007 |
| classifier_direction | TR-R-015 | SET-R-016-V2 | R-008 |
| classifier_direction | TR-R-016 | SET-R-016-V2 | R-008 |
| TOD_REL_TURNOVER | TR-R-017 | SET-R-021-V1, SET-R-021-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-011 |
| BTC_CONTEXT_SCORE | TR-R-018 | SET-R-012-V2, SET-R-BTC-012-V2 | R-022 |
| BTC_CONTEXT_SCORE | TR-R-019 | SET-R-012-V2, SET-R-BTC-012-V2 | R-022 |
| VNM_5m_z | TR-R-022 | SET-R-015-V2, SET-R-BTC-015-V2 | R-026 |
| VNM_5m_z | TR-R-023 | SET-R-015-V2, SET-R-BTC-015-V2 | R-026 |
| F-001 trigger_result | TR-R-029 | SET-R-001-V1, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-001-V1, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| F-001 trigger_result | TR-R-030 | SET-R-001-V2, SET-R-BTC-001-V2 | R-001, R-030 |
| RETURN(asset,5m) | TR-R-BTC-001 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| RETURN(asset,5m) | TR-R-BTC-002 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| RETURN(asset,5m) | TR-R-BTC-003 | SET-R-BTC-016-V2 | R-008 |
| RETURN(asset,5m) | TR-R-BTC-004 | SET-R-BTC-016-V2 | R-008 |
| DE | TR-R-BTC-005 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| ATR percentile | TR-R-BTC-006 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| ATR percentile | TR-R-BTC-007 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |
| TOD_REL_TURNOVER | TR-R-BTC-008 | SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2 | R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030 |

This maps current use; unused reserve trigger/Set definitions remain in the registry, not in the current30. No implicit symbol fallback. Metadata scope for canonical metrics is inherited unchanged except the explicit C-015 BTC dependency closure.

## 10. Research-only execution/evidence/completeness entities

The root export is **RESEARCH_RECORD**, not RUN. Every optional or missing record has a reason; a null value never claims a fictitious exchange fact. The execution/reporting profile §§4–6,9 supplies the exact behavioral rules. These fields are research envelopes, not additions to canonical contract schemas.

| Entity | Required fields / relations |
|---|---|
| SymbolSetBinding | research_id, research_revision, arm_id, symbol, applicability, reason, set_version, direction_binding_id, predicate_instance_refs, config digests; fixed allocation10; no redistribution |
| SourceResolutionManifest | manifest_id/revision/digest, instrument/venue/product, required price bases, actual available granularities/ranges, source/page/finality records, ordering domain, common comparison manifest, parent_child_refinement_map; required signal histories separate |
| ExecutionResolution | resolution_id, run_id, cell interval, status FACTUAL_ORDER_RESOLVED / MODEL_ORDER_INVARIANT / UNRESOLVED_INTRABAR; factual source refs, eligible orders, touched levels, causal constraints, acceptance/protection refs, quantity/model basis, price mapping |
| ModelChronology | factual time where supported, uncertainty interval, source ordering domain, model ordinal, MODEL_CELL_END only under approved material-timing guard; source availability and ingestion/report time separately |
| Ambiguity | competing event relations, affected Entry/TP/SL/cancel intents, feasible differing positions/quantities and Portfolio state, refinement attempts, exact missing/equivalent proof; no simulated winner |
| DependencyFrontier | last committed unambiguous shared_portfolio_checkpoint_id, dependent_suffix_start, affected positions/symbols, requested_endpoint, processed_frontier; no fabricated release/FINAL/CLOSED |
| ReportCompleteness | FULL_WINDOW / PREFIX_ONLY / INCOMPLETE, requested interval, actual frontier, finalized population membership, excluded/rejected/unavailable categories, per-statistic coverage, reason; same-window comparison unavailable if required arm incomplete |
| ResearchRecordExport | all hypothesis/config revisions, arms, symbol bindings, all four window types; runs, reruns and failed/unavailable attempts, source/metric/trigger/Set/Position/Portfolio/Lifecycle/fill/protection/exit/financial evidence, populations/reports/Compare revisions/ACTIVE snapshots, endpoints/ambiguities/frontiers/human decisions |
| ExportManifest | cutoff/export_revision, complete included IDs and object digests/counts/ranges, immutable raw source objects or accessible content-addressed companion, missing/redacted parts and completeness; credentials excluded |
| HumanDecision | actor/provenance/time, explicit action, chosen research/config/report revisions, annotations; no automatic KEEP/REJECT/NEED_MORE_DATA or winner/promotion |

## 11. Run, report, decision and universe bindings

The profile revision is new; run-type names remain exactly the same. Current reports reference REPORT-R-V1-R2 and EVIDENCE-R-V1-R2. Research-only statistics and their population/undefined-value definitions are in the execution/reporting profile §§6–7. Full-window incompleteness cannot be repaired by dropping a trade and concatenating downstream outcomes. Nested windows/reruns are independent evidence records, never one additive performance population.

```yaml
run_profiles:
- run_type: BACKTEST_90D
  profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  duration_seconds: 7776000
  execution_model: HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1
  launch_authority: HUMAN_ONLY
  universe_ref: UNIVERSE-CORE-V1
  launch_schema_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §3.1
  execution_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §4
  boundary_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §5
  report_ref: REPORT-R-V1-R2
  evidence_ref: EVIDENCE-R-V1-R2
  intrabar_policy: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
  source_resolution_manifest_required: true
- run_type: BACKTEST_30D
  profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  duration_seconds: 2592000
  execution_model: HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1
  launch_authority: HUMAN_ONLY
  universe_ref: UNIVERSE-CORE-V1
  launch_schema_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §3.1
  execution_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §4
  boundary_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §5
  report_ref: REPORT-R-V1-R2
  evidence_ref: EVIDENCE-R-V1-R2
  intrabar_policy: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
  source_resolution_manifest_required: true
- run_type: BACKTEST_7D
  profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  duration_seconds: 604800
  execution_model: HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1
  launch_authority: HUMAN_ONLY
  universe_ref: UNIVERSE-CORE-V1
  launch_schema_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §3.1
  execution_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §4
  boundary_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §5
  report_ref: REPORT-R-V1-R2
  evidence_ref: EVIDENCE-R-V1-R2
  intrabar_policy: FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1
  source_resolution_manifest_required: true
- run_type: DEMO_7D
  profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
  duration_seconds: 604800
  execution_model: NATIVE_DEMO_LIFECYCLE
  launch_authority: HUMAN_ONLY
  universe_ref: UNIVERSE-CORE-V1
  launch_schema_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §3.1
  execution_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §5
  boundary_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §5
  report_ref: REPORT-R-V1-R2
  evidence_ref: EVIDENCE-R-V1-R2
  intrabar_policy: NOT_USED_NATIVE_DEMO
  source_resolution_manifest_required: false
universe:
  universe_version: UNIVERSE-CORE-V1
  ordered_members:
  - BTC
  - ETH
  - SOL
  - XRP
  - DOGE
  - SUI
  - PEPE
  - AVAX
  - LINK
  - BNB
  segments:
    MAJORS:
    - BTC
    - ETH
    HIGH_VOLATILITY_HIGH_BETA:
    - SOL
    - XRP
    - DOGE
    - SUI
    - PEPE
    - AVAX
    DIVERSIFIERS:
    - LINK
    - BNB
  BTC_trading_applicability: APPLICABLE_WITH_BTC_SPECIFIC_DIRECTION_BINDING except R-006 NOT_APPLICABLE
  fixed_allocations_pct:
    BTC: '10'
    ETH: '10'
    SOL: '10'
    XRP: '10'
    DOGE: '10'
    SUI: '10'
    PEPE: '10'
    AVAX: '10'
    LINK: '10'
    BNB: '10'
  total_allocation_pct: '100'
  segment_allocation_pct:
    MAJORS: '20'
    HIGH_VOLATILITY_HIGH_BETA: '60'
    DIVERSIFIERS: '20'
report_profile: REPORT-R-V1-R2
report_statistic_definitions:
- report_statistic_id: RR-V1-001
  name: Net Realized P/L
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-002
  name: Trades
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-003
  name: Win Rate
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-004
  name: Expectancy
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-005
  name: Profit Factor
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-006
  name: Max Drawdown
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-007
  name: Average Winner
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-008
  name: Average Loser
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-009
  name: Fill Rate
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-010
  name: MAE
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
- report_statistic_id: RR-V1-011
  name: MFE
  definition_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §6
  allowed_trading_consumers: []
supplementary_diagnostics_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §7
evidence_profile: EVIDENCE-R-V1-R2
evidence_spec_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §9
result_scopes:
- OVERALL
- BY_SEGMENT
- BY_COIN
- BY_DIRECTION
compare_column_order:
- ACTIVE
- DEMO_7D
- BACKTEST_7D
- BACKTEST_30D
- BACKTEST_90D
decision_policy:
  decision_id: DEC-R-001
  decision_version: RESEARCH_V1_FOCUSED_CORRECTION_R2
  authority: HUMAN_REVIEW_ONLY
  strategy_disposition_output: null
  automatic_demo_launch: false
  automatic_promotion: false
  manual_comparison: Present factual reporting/coverage for explicitly selected compatible run revisions. User decides
    continuation, Demo, further hypotheses and Active use. No automatic KEEP/REJECT/NEED_MORE_DATA or winning-arm
    rule.
  interaction_review: For a cross-layer interpretation inspect all 00/10/01/11 cells with matched inputs; show 10
    versus 00 and 11 versus 01 plus complementary pairs. No automatic action follows a comparison.
  quality_checks:
  - Same window and immutable controlled input/configuration profiles for paired interpretation.
  - Canonical financial finality and evidence coverage; visible open/pending/zero/unavailable/unbounded cases.
  - No pooling of nested windows or averaging of grouped ratios.
  - BTC generic branch context is reported, not treated as F-005. R-006 BTC is NOT_APPLICABLE with no redistribution;
    absent observed directions are unavailable, not zero performance.
  - Incomplete required arm makes a same-window point comparison unavailable; prefix reporting is descriptive only.
  - Use matching research/configuration/profile revisions; never pool old R-023 allocation runs with the replacement.
  profile_ref: RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md §§6–8
  TRACEABILITY:
  - SOURCE_DOCUMENT: RV1-DECISIONS (current user Focused Finalization prompt)
    SOURCE_SECTION: §§2–20
    SOURCE_AUTHORITY: RESEARCH_LAYER_ONLY
  - SOURCE_DOCUMENT: RESEARCH_V1_FOCUSED_EXPERT_COUNCIL_BTC_AND_INTRABAR.md
    SOURCE_SECTION: §§2.3–2.6; §§4–5; §7.3
  - SOURCE_DOCUMENT: Research V1 Package Correction — user instruction
    SOURCE_SECTION: §§2–13, 14–25
profile_revision: RESEARCH_V1_FOCUSED_CORRECTION_R2
derived_from: RESEARCH_V1_FINALIZATION_R1
export_root: RESEARCH_RECORD
execution_resolution_statuses:
- FACTUAL_ORDER_RESOLVED
- MODEL_ORDER_INVARIANT
- UNRESOLVED_INTRABAR
fixed_synthetic_ohlc_path: null
content_sha256: 4ee56f4fb10ee0f98f9c2f9bcb5f6f4b346126930fb26187a415a955c7205c3c
```
## 12. Launch and comparison requirements

Supply an actual instrument/native/historical source manifest, selected endpoint, initial capital/state and Demo environment where applicable. Do not assume a specific execution timeframe exists. Canonical signal requirements remain immutable, including required real1m/5m/15m/1h sources and warmup. Profile §3 defines the precise time windows; §4 defines actual factual-resolution priority. Accepted pending orders and active protection are never reset at a reporting endpoint. Missing source data or material intrabar order produces a factual run unavailability reason, not a new strategy decision.

A comparison cell includes run_id, arm_id, research_revision, Set-by-symbol manifest, Position/Portfolio IDs, universe/allocation/profile/source/report revisions, actual interval/frontier, completeness and result-population references. ACTIVE is a manually chosen immutable reference snapshot, not an automatically inferred existing project version. Different current/historical revisions can be inspected side by side with compatibility disclosure, but cannot be treated as a controlled same-treatment comparison. R023R1 and R023R2 have different questions and may never be pooled.

Field-level reporting representation remains: exact decimal or exact ratio, explicit numerator/denominator and null reason; profit-factor positive infinity is an explicit unbounded status rather than an arbitrary finite number. Unobserved directions and inapplicable BTC R006 are not zero performance. Reporting values cannot appear in trigger definitions, Position fields, Portfolio fields, or canonical decision payloads.

## 13. Immutable lineage, profile compatibility and activation evidence

The current research manifest revision is R3. Old existing definitions retain their original configuration revisions/digests; the new BTC variants alone use R3 configuration revisions. `REPORT-R-V1-R2`, `EVIDENCE-R-V1-R2`, and the execution/decision R2 semantic pins remain unchanged, supported by the current R3 profile document. They are not hypothesis revision aliases. Launch requires `(research_id, research_revision)` before resolving the arm; an R2 cap/minimum result cannot resolve as an R3 context/momentum result.

| Stable record | R2 historical candidate | R3 candidate | Migration |
|---|---|---|---|
| R-022 | C-049 | C-012 | New hypothesis revision; retain old runs as historical/conditional only |
| R-026 | C-053 | C-015 | New hypothesis revision; retain old runs as historical/conditional only |

The whole Research-record export includes all revisions, arms and symbol maps, all run types/reruns/failures, source manifests and complete metric/Trigger/Set/Position/Portfolio/Lifecycle/financial evidence, report/Compare revisions, ACTIVE snapshots, endpoint/open-state/ambiguity/frontier records, and human provenance. No report statistic or activation count feeds a canonical trading input. New per-hypothesis activation requirements in §8 extend existing evidence contents without changing the immutable common reporting formulas/populations or inventing classifier-veto output for BTC.

Required evidence distinction: **valid predicate disagreement → executable difference → finalized economic difference**. Source/normalization unavailability is not an economic disagreement. Native non-BTC original veto results are retained where actually produced; BTC records `NOT_PRODUCED_BY_F005` plus its genuine source/pending evidence, never a fake classifier gate/veto record.

C-012 BTC is nested/dependent with R-005; non-BTC own structure and external BTC context remain different inputs. C-015 BTC may show zero valid disagreements under a zero normalization mean. Neither case authorizes changing source normalization or adding a new intervention. Replacement confidence remains MEDIUM, pre-backtest. The approved 57 relationship judgments are applied in the overlap artifact; not recomputed from trading outcomes.
