# Research V1 Trigger Web Semantic Audit

Audit date: 2026-09-27

Scope: read-only audit of the 31 imported Research V1 trigger definitions visible in the web dashboard. No production rows were changed. No application code was changed.

## Evidence Read

- Authoritative Research source: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` and `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/RESEARCH_HYPOTHESES_FINAL_30.md`.
- Canonical trigger catalog: `docs/research-import/triggers/RESEARCH_V1_TRIGGERS.json`.
- Web import artifact: `docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`.
- Production import evidence: `docs/research-import/triggers/RESEARCH_V1_TRIGGER_PRODUCTION_IMPORT_REPORT.md`.
- Runtime parser/evaluator: `src/triggertrade/triggers/declarative_metric_predicate.py`.
- Web API projection: `src/triggertrade/dashboard/research_triggers.py`.
- Dashboard rendering: `src/triggertrade/dashboard/product_ui.py`.

Direct live production SQL was attempted read-only against the `.env` DSN with `SET TRANSACTION READ ONLY`, but authentication failed for the configured user. The production row representation below is therefore traced from the production import report, which states the imported package was `RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`, imported through `PostgresTriggerRegistry.sync_trigger_registry()`, created 31 rows, verified 31/31 digest matches, and had a direct read-only SQL Research trigger row count of 31 at import time.

## BTC Output Trace

Authoritative intended BTC semantics are explicit in the Research source: the BTC return branch map assigns `TR-R-BTC-001` to `LONG` and `TR-R-BTC-002` to `SHORT`; the BTC Set direction text says positive 5m return maps to LONG, negative 5m return maps to SHORT, zero qualifies neither, and required unavailable produces no direction-qualified match. The same source identity pattern applies to `TR-R-BTC-003` and `TR-R-BTC-004` for the R-008/SET-R-BTC-016 event variants.

| Trigger | Intended output semantics | Canonical artifact | Web-import representation | Production row representation | Runtime-parsed behavior | API projection | Rendered UI | Semantic loss | Presentation loss | Classification |
|---|---|---|---|---|---|---|---|---|---|---|
| `TR-R-BTC-001` | `RETURN(asset,5m) > 0 -> LONG`; `= 0 -> ZERO`; unavailable -> `UNAVAILABLE` | condition `RETURN(asset,5m) > 0`; `direction_output.direction_applicability=LONG`; `direction_output.output_states=[ZERO, UNAVAILABLE]`; missing-data text says `> 0 yields LONG` | rule `TR-R-BTC-001@1.0.0`; `operator=GT`; `threshold=0`; `direction_applicability=LONG`; `output_states=[ZERO, UNAVAILABLE]`; digest `6dc6f17d305375d38b8bb34380f0d40fca4bd5057d0c61590c07d6ab58077a70` | Production report says the web-import package was inserted through `PostgresTriggerRegistry` with digest match 31/31; therefore expected stored definition matches web-import. Live SQL could not be re-read due auth failure. | Current runtime with this definition emits `TRUE` for positive match, `ZERO` for zero, `UNAVAILABLE` for unavailable. It does not emit `LONG`. | `output="ZERO, UNAVAILABLE"`, `scope` contains `LONG; coins: BTC` | `Output` column shows `ZERO, UNAVAILABLE` | YES | YES | `IMPORT_ARTIFACT_DEFECT` |
| `TR-R-BTC-002` | `RETURN(asset,5m) < 0 -> SHORT`; `= 0 -> ZERO`; unavailable -> `UNAVAILABLE` | condition `RETURN(asset,5m) < 0`; `direction_output.direction_applicability=SHORT`; `direction_output.output_states=[ZERO, UNAVAILABLE]`; missing-data text says `< 0 yields SHORT` | rule `TR-R-BTC-002@1.0.0`; `operator=LT`; `threshold=0`; `direction_applicability=SHORT`; `output_states=[ZERO, UNAVAILABLE]`; digest `aeceda135415bc45605abd4c1159a4a15187008b2da5a785dfc62e8ef00c9d83` | Same import path and digest-match evidence as above. Expected stored definition matches web-import. Live SQL could not be re-read due auth failure. | Current runtime emits `TRUE` for negative match, `ZERO` for zero, `UNAVAILABLE` for unavailable. It does not emit `SHORT`. | `output="ZERO, UNAVAILABLE"`, `scope` contains `SHORT; coins: BTC` | `Output` column shows `ZERO, UNAVAILABLE` | YES | YES | `IMPORT_ARTIFACT_DEFECT` |
| `TR-R-BTC-003` | R-008 event variant: positive 5m BTC return branch -> `LONG`; zero -> `ZERO`; unavailable -> `UNAVAILABLE` | condition `RETURN(asset,5m) > 0`; `direction_output.direction_applicability=LONG`; `direction_output.output_states=[ZERO, UNAVAILABLE]`; freshness is event-based | rule `TR-R-BTC-003@1.0.0`; `operator=GT`; `threshold=0`; `direction_applicability=LONG`; `output_states=[ZERO, UNAVAILABLE]`; digest `ce143b4e8c7f1ad06e3fee43df34e762ab3c54e59043b1240baf517ebba4f22f` | Same import path and digest-match evidence as above. Expected stored definition matches web-import. Live SQL could not be re-read due auth failure. | Current runtime emits `TRUE` for positive match, `ZERO` for zero, `UNAVAILABLE` for unavailable. It does not emit `LONG`. | `output="ZERO, UNAVAILABLE"`, `scope` contains `LONG; coins: BTC` | `Output` column shows `ZERO, UNAVAILABLE` | YES | YES | `IMPORT_ARTIFACT_DEFECT` |
| `TR-R-BTC-004` | R-008 event variant: negative 5m BTC return branch -> `SHORT`; zero -> `ZERO`; unavailable -> `UNAVAILABLE` | condition `RETURN(asset,5m) < 0`; `direction_output.direction_applicability=SHORT`; `direction_output.output_states=[ZERO, UNAVAILABLE]`; freshness is event-based | rule `TR-R-BTC-004@1.0.0`; `operator=LT`; `threshold=0`; `direction_applicability=SHORT`; `output_states=[ZERO, UNAVAILABLE]`; digest `02cbf7b76bdbb05e00d97e508bfd60e5062a5e678343a1c8f40c97e454a75e90` | Same import path and digest-match evidence as above. Expected stored definition matches web-import. Live SQL could not be re-read due auth failure. | Current runtime emits `TRUE` for negative match, `ZERO` for zero, `UNAVAILABLE` for unavailable. It does not emit `SHORT`. | `output="ZERO, UNAVAILABLE"`, `scope` contains `SHORT; coins: BTC` | `Output` column shows `ZERO, UNAVAILABLE` | YES | YES | `IMPORT_ARTIFACT_DEFECT` |

Conclusion: this is not only a web presentation issue. The authoritative source prose intends LONG/SHORT branches, but both `RESEARCH_V1_TRIGGERS.json` and `RESEARCH_V1_TRIGGERS_WEB_IMPORT.json` encode BTC branch `output_states` as only `ZERO` and `UNAVAILABLE`. The runtime uses `output_states` for emitted state; `direction_applicability` is parsed but is not used to emit LONG/SHORT. With the imported-style records, the runtime emits `TRUE` on matched BTC direction branches.

## Apparent Duplicate Pairs

No accidental duplicate identities were found. The pairs either differ semantically in fields not visible in the list, or intentionally preserve distinct Research identities/provenance over equivalent visible predicates.

| Pair | Source-supported comparison | Classification |
|---|---|---|
| `TR-R-001` vs `TR-R-002` | Both are `F-001 trigger_result = TRUE`, but `TR-R-001` has `theta_move_pct=0.50`, broad hypotheses R-001..R-030, and broad Set usage; `TR-R-002` has `theta_move_pct=1.00`, hypotheses R-001 and R-030, and only `SET-R-001-V2`/`SET-R-BTC-001-V2`. Digests differ: `330f...042e` vs `d04d...2b26`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |
| `TR-R-004` vs `TR-R-015` | Both are `classifier_direction = LONG`, non-BTC, but `TR-R-004` is current-state direction over the broad Research hypothesis/Set population, while `TR-R-015` is the R-008/`SET-R-016-V2` event variant with `FRESH_EVENT` freshness. Digests differ: `8c34...4971` vs `bc7f...6b73`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |
| `TR-R-005` vs `TR-R-016` | Both are `classifier_direction = SHORT`, non-BTC, but `TR-R-005` is current-state direction over the broad Research hypothesis/Set population, while `TR-R-016` is the R-008/`SET-R-016-V2` event variant with `FRESH_EVENT` freshness. Digests differ: `f553...8b8e` vs `1e5f...5b99`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |
| `TR-R-029` vs `TR-R-030` | Both are `F-001 trigger_result = FALSE`, but `TR-R-029` has `theta_move_pct=0.50`, broad hypotheses/Sets, and `TR-R-030` has `theta_move_pct=1.00`, hypotheses R-001/R-030 and only the V2 SET-R-001/BTC-001 identities. Digests differ: `a0ed...3b87` vs `e320...c8d8`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |
| `TR-R-BTC-001` vs `TR-R-BTC-003` | Both are positive BTC 5m return LONG branch predicates with metric `RETURN(asset,5m)`, formula `F-004`, `GT 0`, BTC-only applicability, and current encoded output states `[ZERO, UNAVAILABLE]`. They differ by provenance and freshness: `TR-R-BTC-001` is the broad current-state branch for many BTC Sets; `TR-R-BTC-003` is the R-008/`SET-R-BTC-016-V2` event variant with `FRESH_EVENT` ancestry rules. Digests differ: `6dc6...7a70` vs `ce14...f22f`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |
| `TR-R-BTC-002` vs `TR-R-BTC-004` | Both are negative BTC 5m return SHORT branch predicates with metric `RETURN(asset,5m)`, formula `F-004`, `LT 0`, BTC-only applicability, and current encoded output states `[ZERO, UNAVAILABLE]`. They differ by provenance and freshness: `TR-R-BTC-002` is the broad current-state branch for many BTC Sets; `TR-R-BTC-004` is the R-008/`SET-R-BTC-016-V2` event variant with `FRESH_EVENT` ancestry rules. Digests differ: `aece...c9d83` vs `02cb...5e90`. | `DISTINCT_SEMANTICS_NOT_VISIBLE_IN_LIST` |

Because all six pairs have source-supported semantic differences, none should be deduplicated based on the visible list text.

## Metric(s) Column

The web API builds `metric_refs` by combining `definition.metric_ref` with `definition.current_metric_ids`. The UI renders this joined value in one `Metric(s)` column.

Examples:

- `DE, F-004` combines canonical metric/state dependency `DE` with current metric/formula object `F-004`.
- `ATR percentile, F-004` combines a named Research metric dependency with current implementation/formula object `F-004`.
- `classifier_direction, F-005` combines state dependency with classifier formula object.
- `F-001 trigger_result, F-001` combines trigger-result state dependency with formula identity.

This is semantically useful because it preserves both the Research dependency and the current metric/formula mapping, and `metric_links` are created only for `current_metric_ids` that exist in the Metrics Library. It is presentation-confusing because the column name implies one concept while it displays multiple concepts.

Recommendation: `SPLIT_METRIC_AND_FORMULA_COLUMNS`. This is clearer than a rename because both fields are distinct and useful: canonical metric/state dependency should stay visible separately from current formula/metric object linkage.

## DRAFT Status

`DRAFT` is the `RuleStatus` stored in the web-import `RuleDefinition` records. In this path it is lifecycle/read-model metadata, not an execution gate.

Findings:

- `PostgresTriggerRegistry.list_rules()` and `list_trigger_versions()` return all stored rule definitions without a status filter.
- Dashboard Research trigger payloads expose `rule.status.value` and do not filter out `DRAFT`.
- `TriggerSetStore.resolve_trigger_version()` requires exact membership, trigger type, and semantic hash integrity. It does not reject `RuleStatus.DRAFT`.
- Backtest and futures runtime declarative trigger paths call `resolve_trigger_version()` and then `evaluate_declarative_metric_predicate()` for declarative trigger definitions; there is no `RuleStatus.DRAFT` check in that path.
- Set runtime activation is gated by Set status elsewhere; this audit found no RuleDefinition status gate that prevents Set reference or Research execution.

Therefore:

- `DRAFT_BLOCKS_RUNTIME: NO`
- `DRAFT_BLOCKS_SET_REFERENCE: NO`
- `DRAFT_BLOCKS_RESEARCH_EXECUTION: NO`

## Confirmed Defect

Confirmed defect: BTC branch output states are incomplete in the import artifacts. The source prose says positive return maps to LONG and negative return maps to SHORT, but the canonical/imported declarative `output_states` omit LONG and SHORT for `TR-R-BTC-001..004`. The current runtime consequently emits `TRUE` for matched BTC direction branches rather than `LONG` or `SHORT`.

This should be corrected before proceeding to Sets, because Sets will bind these trigger identities and would inherit the wrong runtime output behavior. No correction was made in this audit.

## Recommended Next Action

Open a separate correction task to repair the BTC trigger artifacts and production rows under explicit approval. The correction should preserve trigger identities unless the project decides the immutable version contract requires a new version, then re-run registry idempotency, runtime resolution, web projection, and a live production read-only verification.

