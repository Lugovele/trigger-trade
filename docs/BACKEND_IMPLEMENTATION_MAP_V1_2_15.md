# TriggerTrade — Final Candidate Backend Implementation Map

**Methodology:** frozen v1.2.15
**Planning revision:** 20 September 2026; R6 focused correction of FA-R5-01 (AUD-ENTRY-REPORT and AUD-TP-REPORT) from the supplied fresh clean-room R5 audit
**Artifact:** `BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R6.md`
**Planning disposition:** ready for independent re-audit of this R6 correction; not implementation-approved. CLOSED in §16 is the correction author’s planning assessment, not independent certification. Independent acceptance remains required before starting an implementation batch.

This document replaces `BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R5.md` in full. Substantive R6 edits address only FA-R5-01: map the two already-frozen required Entry/TP research reports, retain their exact source/cohort/path evidence, define diagnostic-only analytical conventions where the frozen reporting lists leave them open, and assign local tests/reviews and subsequent integrated verification. NR-153 and NR-154 receive no historical R alias. All existing canonical formulas, thresholds, business edges, 39 logical-state families, 26 transaction mechanisms, 19-checkpoint order and native/finality gates remain in place. No backend implementation, automatic optimization, Research migration or new trading authority is performed or approved.

## 1. Authority, evidence and interpretation

### 1.1 Controlling sources

For this focused R6 correction, authority is: frozen methodology v1.2.15 → actual supplied current backend source snapshot → FA-R5-01 in `BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15_R5.md` → supplied R5 map. The supplied R5 requirement review, source-evidence annex and JSON summary locate/support the finding; they do not override original source. R5 self-checks are not evidence. The unchanged 152-row core is carried from the fresh full audit and protected by exact comparison; this correction is not a second full independent certification.

The actual supplied ZIPs are `trading-methodology(20260920-114741).zip` and `triggertrade-backend-source-snapshot-v1.2.15(6).zip`. The former contains `trading-methodology/`; repository-relative normative locators keep `docs/trading-methodology/`. The freeze commit `e3aaa67fe5cf06e1d018291ee4d49f335fc5ea56` is recorded provenance, not newly verified git history. The latter ZIP is the complete source snapshot for this correction, not a live deployment or database.

Focused original-source inspection covers POSITION_RULES Part II §§21–22/47/50–51 and Part IV selection/traversal/output/§§47–48, Set reference age/type/context, and existing Lifecycle execution/terminal evidence. Current ResearchService, ResearchStore, research pin helpers, analytics, historical data/cache and actual storage roles are inspected for the additions in §6.4. The two required reporting lists are normative; report denominators, observation horizons and path resolution not fixed there are explicitly identified as pinned diagnostic implementation definitions, never new trading semantics. Changed repository surfaces must be rechecked at implementation.

### 1.2 Evidence convention and preserved inputs

`E01`–`E76`, source inventories and all earlier audit references embedded in preserved R5 text are historical traceability, not additional evidence consulted for R6. R6 cites the actual original source paths and one-based physical lines below; the supplied R5 annex’s CR-* labels are subordinate locators. Do not conflate evidence namespaces.

Exactly these seven inputs were used for R6; SHA-256 values identify their actual supplied bytes:

| R6 input, actual filename | SHA-256 |
| --- | --- |
| `trading-methodology(20260920-114741).zip` | `4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373` |
| `triggertrade-backend-source-snapshot-v1.2.15(6).zip` | `67bc1d12ae0c85c9548bc418f2d58cc6b838705d5615d2619d9e1a305f7d2754` |
| `BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R5(2).md` | `0abfe85d22edbb3dfa779ac24982b6a89f3903cb78512a8cf626ac0d260b5d71` |
| `BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15_R5.md` | `00ce11f91b24e2924d722cb11cf281918ebae8cf270cb30b2615431f3db2571b` |
| `R5_CLEAN_ROOM_REQUIREMENT_REVIEW.md` | `b21be2a0a7dbe4af1aefb3c04d38949483bcbc220572af341d27a765f2894267` |
| `R5_CLEAN_ROOM_SOURCE_EVIDENCE.md` | `18dc199e9eb45e75d27f7d845a8bd12a8f82781926b5cc6aa65db0afd226ece9` |
| `R5_CLEAN_ROOM_AUDIT_SUMMARY.json` | `f6e63897ca4d15fd5297799163ce228c4f83c4f9bb789f845a3bcb85018d4810` |

Verification for this revision comprises original-source inspection, explicit coverage/dataflow/availability analysis, independent exact fixture arithmetic, source-symbol/storage checks, R5-to-R6 structural diff, protected-content comparisons, checkpoint/review-list synchronization and rehashing the seven inputs. It is not execution of backend, PostgreSQL, ResearchStore, adapter or native acceptance suites. Planned tests below must be implemented and independently reviewed at their assigned checkpoints. The sole deliverable is this complete R6 Markdown map.

**Historical R5 input table, retained as provenance only; none of these older aliases adds an input:**

| Historical R5 input | Original recorded SHA-256 |
| --- | --- |
| trading-methodology(10).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| triggertrade-backend-source-snapshot-v1.2.15(5).zip | 67bc1d12ae0c85c9548bc418f2d58cc6b838705d5615d2619d9e1a305f7d2754 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R4(2).md | 2e9ac2bbafe02f4bd769843bb92172d6f698efe7c9438d9c75dc5339f5c42469 |
| BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15_R4.md | 599aef42ef11f31c5b21bbd063f724ef12546d5079defa0dfa6618f889d7a38d |
| SOURCE_EVIDENCE_R4.md | a9357c4642a1093e1c59c0be8a830ce69e7187c6a1e88d9174efdc5141d40de4 |
| REQUIREMENT_REVIEW_R4.md | e926c80c24d69b651db6d7cae94266550ea1f29e6b5f1531f211a4ab3aba1d9a |

**Historical input tables retained from R4 follow.** “Current attachment” inside those tables refers to the historical revision only.

| Historical revision input / task definition (preserved provenance only) | SHA-256 (original bytes) |
| --- | --- |
| trading-methodology(4).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15(1).md | d8309d3b625fb6e93e7c0e4e90c6e99c6067e58502b49da5cb7cd934061f3d46 |
| BACKEND_IMPLEMENTATION_PLAN_CERTIFICATION_V1_2_15.md | 8196e282d63cc9d11c2742c4411e0781040c6dec1cb7633c146c96cb6cf17db7 |
| BACKEND_IMPLEMENTATION_MAP_REVISION_BRIEF_V1_2_15.md | 8179e94ebe2b49776c90d3a07f4ffd6fbace8c332d150f2ab65e31f7021e23e6 |
| BACKEND_IMPLEMENTATION_PLAN_AUDIT_EVIDENCE_V1_2_15.zip | aab6b0e2d070a6800d2146b4b109f46fd8690b79e1edeca76bf992900713b661 |
| Вставленный текст(20260916-182600).txt | f77491da0c7c300c85b9a96d588cf11582e099156e25558e26d5366117ec2c7e |

**Prior RA-01 / RA-02 correction inputs (historical provenance only):**

| Current attachment | SHA-256 |
| --- | --- |
| trading-methodology(6).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15_REVISED (1).md | 38818e375e1204b037d542ce59108f6396280bd3f436ae8e7d2d33b3db93fed0 |
| BACKEND_IMPLEMENTATION_PLAN_REAUDIT_V1_2_15.md | 6e950e93cf9e529967628b9aeb91e95b221966904290eb4b33c85f5bed7bb583 |
| REAUDIT_SOURCE_EVIDENCE_V1_2_15.md | 549a936ad59fb3d77936c62c6b7a0ad2cf14a12713d0bfe84074b51400e7ef33 |
| BACKEND_IMPLEMENTATION_PLAN_REAUDIT_SUMMARY_V1_2_15.json | b61fa828e5768109883b1e287056d24254104aba02e341faf5689b9502453f65 |

**Prior R2 correction inputs (historical provenance only):**

| Current attachment | SHA-256 |
| --- | --- |
| trading-methodology(7).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| triggertrade-backend-source-snapshot-v1.2.15(2).zip | 67bc1d12ae0c85c9548bc418f2d58cc6b838705d5615d2619d9e1a305f7d2754 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE(2).md | d5357ae828a7c02748eef0a734f8c985fde7d26598a078340ec808c40fb8fb37 |
| BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15.md | 0f18701815fc418267825e3bb568e0ce8b627488f8f2517bbd101a566707c160 |
| SOURCE_EVIDENCE.md | 5e07d7a41916dadf18b7820512aeea1538acf84fb97ac33d7b57a38240786c9a |

**Prior R3 correction inputs (historical provenance only):**

| Current attachment | SHA-256 |
| --- | --- |
| trading-methodology(8).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| triggertrade-backend-source-snapshot-v1.2.15(3).zip | 67bc1d12ae0c85c9548bc418f2d58cc6b838705d5615d2619d9e1a305f7d2754 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R2(2).md | c8e443ac90d86b2e17146d8ca3041935d495628d1d2d9699aa99ffbffb39641c |
| BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15_R2.md | 8d3ba34b0acd195f3eb01ae73533fd01d089cd312557592eb1cce73e2fa0d920 |

**Prior R4 correction inputs (historical original bytes):**

| Current attachment | SHA-256 |
| --- | --- |
| trading-methodology(9).zip | 4ad009663c3256577cbb4670b736dda968f2a93d9bbc796af32059753f885373 |
| triggertrade-backend-source-snapshot-v1.2.15(4).zip | 67bc1d12ae0c85c9548bc418f2d58cc6b838705d5615d2619d9e1a305f7d2754 |
| BACKEND_IMPLEMENTATION_MAP_V1_2_15_FINAL_CANDIDATE_R3(2).md | 52b064737dec9b0a5990ca437f7d49bb17eda7fc16f026ed35a22d840404072a |
| BACKEND_IMPLEMENTATION_PLAN_FINAL_AUDIT_V1_2_15_R3.md | b7daeb370e61984f411d96f8e4ed981af2b962714d2d3f67e31aaf777accadd4 |
| R3_AUDIT_EVIDENCE.md | d01c41cdeb343930d67b51759de8e03544b913ebec304b5ca0ce5fac7c972512 |

The preceding historical tables are not R6 source inputs or readiness evidence. The operative supplied fresh R5 audit remains `REVISION_REQUIRED` with one NON_BLOCKING FA-R5-01 covering two incompletely mapped reporting groups. The R6 correction neither amends that audit nor constitutes independent approval.

### 1.3 Strategy and completion semantics

**Existing backend foundation + certified formula/state-rule layer = one v1.2.15-conformant backend.** Reuse, extend, adapt or fence the existing implementation. Do not introduce a second grant ledger, construction/spec/auth store, Set state machine, Lifecycle, close authority, placement-return mechanism, serializer, outbox/inbox, accounting authority or canonical worker.

A logical record marked NEW means the evidence shows a missing canonical obligation. It does **not** prescribe one table per record or authorize duplicate infrastructure. Its owning checkpoint must choose an extension of a compatible existing representation where possible; a genuinely new record/table/helper requires an explicit gap, uniqueness/transaction specification and review. Proposed paths are implementation organization, not new owners.

The normative register contains obligation groups, not a percentage-complete estimate. Every subordinate rule in a cited algorithm/contract remains binding; named acceptance scenarios are required minima, not permission to omit other source-defined branches. Technical mechanisms, file choices and reviewer assignments are implementation planning choices that realize those obligations; they do not acquire authority over frozen behavior.

For a requirement with several checkpoints, early work establishes only the indicated kernel/interface/state capability. Its integrated closure requires **all** listed checkpoints, the actual downstream producer/consumer integration and final verification. B6 fixture-based placement intake, B8A Daily Loss fixtures and B4 structural builders do not prove an operational native/financial/owner flow.

## 2. Existing foundation preservation and file/symbol grounding

### 2.1 Protected components

Every component in this table is protected against wholesale replacement unless a concrete defect is demonstrated and a separately reviewed change is necessary. `FN.*` references used later resolve to this table. Existing methods and class paths are taken from the attached source-symbol inventory, not guessed from planning labels.

| Foundation ID | Component | Existing surface | Action | Required preservation/extension | Evidence |
| --- | --- | --- | --- | --- | --- |
| FN.JSON | Canonical JSON/digest | src/triggertrade/canonical_json.py | REUSE_AS_IS | One serializer/digest and float rejection; owner wrappers call it unchanged unless an actual defect is proved. | E30 |
| FN.UOW | PostgresUnitOfWork | `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94) | REUSE_AS_IS | Compose existing connection-bound stores; no nested auto-commit or cross-database pseudo-transaction. | E31 |
| FN.CAS | OwnerStateStore | `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128) | EXTEND | Reuse put_if_absent/CAS; add only needed domain-independent composition. Owner-specific records arrive later. | E31 |
| FN.MSG | DurableMessageStore | `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62) | EXTEND | Keep append/claim/inbox conflict rules; add same-edge scoped frontier and transaction composition. No second transport. | E32 |
| FN.CONTRACT | Registry/generated schema/parser | src/triggertrade/contracts/registry.py; src/triggertrade/contracts/_approved_wire_schema.py; src/triggertrade/contracts/schema_validator.py | ADAPT | B0 minimum current schema constructs/whitelist; B4 binding reuse. No alternate serializer or business producer layer. | E26–E29 |
| FN.SCOPE | CoinsScopeStore | `src/triggertrade/persistence/coins_scope_store.py::CoinsScopeStore` (inventory L48) | EXTEND | Portfolio scope publication/Set application; retain existing revision/epoch representation. | E59 |
| FN.EPOCH | SetFormationEpoch / SetConfigurationBinding | `src/triggertrade/set_scope.py::SetFormationEpoch` (inventory L88); `src/triggertrade/set_scope.py::SetConfigurationBinding` (inventory L17) | EXTEND | Extend actual scope model with trigger/evaluation/result state rather than a second Set model. | E58 |
| FN.PIN | Position configuration-pin capability | `src/triggertrade/persistence/position_config_pin_store.py::PositionConfigPinStore` (inventory L32); src/triggertrade/position_config_pins.py | EXTEND | Preserve existing initial pin; join retained decision and post-grant evidence. The audit’s longer PositionConfigurationPinStore name is descriptive, not an existing literal symbol. | source_symbol_inventory.json; audit §8 |
| FN.GRANT | CapitalGrantStore / grant builder | `src/triggertrade/persistence/capital_grant_store.py::CapitalGrantStore` (inventory L32); `src/triggertrade/capital_grants.py::build_capital_and_limits_grant` (inventory L15) | EXTEND | Add owner calculations/current checks; reuse issue and initial-APPROVE binding. No second grant ledger. | E35–E36 |
| FN.CONSTRUCT | PositionConstructionStore | `src/triggertrade/persistence/position_construction_store.py::PositionConstructionStore` (inventory L36); src/triggertrade/position_construction.py | EXTEND | Add certified F-011/F-012 and join the existing spec store and two outboxes under one UoW. | E37–E38 |
| FN.SPEC | OrderSpecStore | `src/triggertrade/persistence/order_spec_store.py::OrderSpecStore` (inventory L37); src/triggertrade/order_specs.py | EXTEND | Immutable spec/digest from successful construction; no parallel spec store. | E39 |
| FN.AUTH | SubmitAuthorizationStore | `src/triggertrade/persistence/submit_authorization_store.py::SubmitAuthorizationStore` (inventory L35); src/triggertrade/submit_authorizations.py | EXTEND | Book current exact H/slot/config/frontier with authorization/outbox; no second authorization store. | E40 |
| FN.PORT | Portfolio state/buckets | `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py | EXTEND | Preserve current health/buckets; add missing owner scope/day/hold/receipt transitions. | E47; inventory |
| FN.COOLDOWN | Portfolio cooldown pins | `src/triggertrade/persistence/portfolio_cooldown_store.py::PortfolioCooldownStore` (inventory L33); src/triggertrade/portfolio_cooldown.py | EXTEND | Authoritative first acceptance, attempt-pinned duration and unresolved integrity history. | inventory; audit §§8,15 |
| FN.START | Lifecycle start gate | `src/triggertrade/persistence/lifecycle_start_gate_store.py::LifecycleStartGateStore` (inventory L46); src/triggertrade/lifecycle_start_gate.py | EXTEND | Exact immutable spec+authorization join; no native authority from grant/spec alone. | inventory; audit §8 |
| FN.SUBMIT | LifecycleSubmissionStore | `src/triggertrade/persistence/lifecycle_submission_store.py::LifecycleSubmissionStore` (inventory L61); src/triggertrade/lifecycle_submission.py | EXTEND | Existing durable-before-side-effect intent and client identity, ambiguous-create query/retry. | E45–E46 |
| FN.SYNC | LifecycleSetSyncStore | `src/triggertrade/persistence/lifecycle_set_sync_store.py::LifecycleSetSyncStore` (inventory L46); src/triggertrade/lifecycle_set_sync.py | EXTEND | Already publishes placement and terminal return to Set; bind it to actual B6 monitor. Never duplicate. | E41–E42 |
| FN.CLOSE | LifecycleCloseAuthorityStore | `src/triggertrade/persistence/lifecycle_close_authority_store.py::LifecycleCloseAuthorityStore` (inventory L74); src/triggertrade/lifecycle_close_authority.py | EXTEND | Reuse acquire_or_join/causes/children; add revision/current-proof guards and quantity budget. | E43–E44,E60 |
| FN.RECON | Lifecycle reconciliation/events | `src/triggertrade/persistence/lifecycle_reconciliation_store.py::LifecycleReconciliationStore` (inventory L63); `src/triggertrade/persistence/lifecycle_order_event_store.py::LifecycleOrderEventStore` (inventory L38) | EXTEND | Preserve accepted evidence/tombstones; add source partition/receipts/current factual proof. | inventory; audit §8 |
| FN.FACT | Existing factual stores | `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38) | EXTEND | Retain exact accepted request/page/response bindings; add required raw preflight histories/quarantine and owner composition. | E34; inventory |
| FN.API | Factual API normalization | src/triggertrade/api_adapter_gateway/market_data.py; src/triggertrade/api_adapter_gateway/portfolio_data.py; src/triggertrade/api_adapter_gateway/order_management.py | EXTEND | Keep all three bidirectional technical boundaries and current binary item helper; add accepted provenance/preflight. | E33–E34; inventory |
| FN.NATIVE | Native factual profile boundary | src/triggertrade/api_adapter_gateway/native_profile.py | EXTEND | No profile certification inferred from shape tests; gate actual exposure separately and retain raw field authority. | E56–E57 |
| FN.RUNTIME | Launcher/one worker/process roles | src/triggertrade/services/runtime.py; src/triggertrade/services/trading_worker.py; src/triggertrade/services/process_roles.py | EXTEND | Preserve startup paper/spot rejection and one TargetTradingWorker; replace blocking only at B12 under §11. | E23–E25 |
| FN.RESEARCH | Research pins/isolation/governance | `src/triggertrade/research_pins.py::research_pin_payload` (existing helper, REUSE); `src/triggertrade/persistence/research_store.py::ResearchStore` (existing SQLite research persistence); `src/triggertrade/persistence/operator_state_store.py::OperatorStateStore` (existing SQLite operator-state persistence); `src/triggertrade/persistence/research_promotion_governance.py::ResearchPromotionGovernanceStore` (existing PostgreSQL promotion-request / outbox governance only) | ADAPT | B0 new v1.2.15 defaults only. R6 additionally extends existing ResearchService/analytics and the same SQLite ResearchStore with the required NR-153/154 immutable diagnostic datasets/reports: B3 archival/import capability, B7A/B9/B10 authoritative source retention, B12 read-only assembly, B13 verification (§6.4). Reuse research_pin_payload/research_run_pin_payload and existing historical-data/cache organization; snapshot limitations and missing interfaces are explicit in §6.4.1. Preserve historical pins, narrow PostgreSQL promotion-request governance and S-005 isolation. No Research/operator migration, replacement store, simulator fallback or new canonical authority. | Supplied source: research_pins.py L22–L47; research_store.py L132–L137, L638–L641; operator_state_store.py L44–L55, L231–L234; research_promotion_governance.py L9–L87; final audit FA-02 |
| FN.LEGACC | Legacy accounting and bridge | src/triggertrade/accounting/futures.py; src/triggertrade/persistence/futures_accounting_store.py; src/triggertrade/services/futures_accounting_bridge.py | FENCE | SQLite legacy stays nonauthoritative. Compatible pure helpers only after independent semantic proof; new canonical missing records remain Lifecycle-owned PostgreSQL. | E48–E49 |
| FN.LEGDAY | Legacy DailyLossEvaluator/DailyLossStore | src/triggertrade/services/daily_loss.py; src/triggertrade/persistence/daily_loss_store.py | FENCE | Do not promote legacy UTC day/latch/SQLite storage into A-009 or bridge through dual writes. | E50–E51 |
| FN.LEGACY | Legacy triggers/demo precision/spot/paper/S-005 | src/triggertrade/triggers/percentage_price_move.py; src/triggertrade/triggers/volume_confirmation.py; src/triggertrade/execution/precision.py; src/triggertrade/execution/paper.py; src/triggertrade/execution/bybit.py; src/triggertrade/strategies/futures_directional.py; src/triggertrade/market_data/regime.py | FENCE | Keep useful research/demo behavior separate; no canonical fallback, second formula engine or assumed precision equivalence. | inventory; audit §31 |
| FN.TEST | Existing tests and PostgreSQL fixtures | Existing tests/contract and tests/unit entries in source_symbol_inventory.json | EXTEND | Preserve compatible foundation regression; add independent frozen-clause expectations, actual PG transaction evidence and native-profile scope limits. | test_plan; focused logs are historical only |

### 2.2 Grounding policy and explicit corrections

`EXISTING` is established by attached source evidence; `NEW_PROPOSED` is justified missing implementation organization; `CONDITIONAL_NEW` requires checking for an equivalent before creation; `LEGACY_ONLY` remains isolated; `WRONG_SURFACE` must not be targeted as the claimed canonical implementation. No proposed filename is asserted to exist.

The requirement to preserve the configuration-pin capability is implemented by preserving the **actual `PositionConfigPinStore`**. The longer `PositionConfigurationPinStore` spelling in the audit/request is a descriptive alias, not a separate class to add or rename. This resolves the literal-symbol discrepancy without changing ownership or pin semantics.

| Mentioned target | Classification | Correct action |
| --- | --- | --- |
| build_capital_and_limits_grant | EXISTING | Reuse in capital_grants.py; replace the old map’s non-existent build_capital_grant target. |
| research_pin_payload | EXISTING | Reuse in research_pins.py; replace the non-existent ResearchPinPayload target. |
| PositionConfigPinStore | EXISTING | Reuse persistence/position_config_pin_store.py and existing PositionConfigPin helpers. |
| build_capital_grant / ResearchPinPayload / PositionConfigurationPinStore as literal existing symbols | WRONG_SURFACE | Do not create these merely to satisfy the old planning spelling. |
| FuturesAccountingStore / DailyLossStore | LEGACY_ONLY | SQLite records are not canonical PostgreSQL FINAL/receipt/A-009 state. |
| TriggerSetStore as the new canonical Set formation model | WRONG_SURFACE | Reuse CoinsScopeStore/SetFormationEpoch; preserve legacy config/demo behavior only. |
| src/triggertrade/numeric_policy.py | NEW_PROPOSED | Exact generic missing primitives; no owner equations or duplicate serializer. |
| src/triggertrade/identifier_lineage.py | CONDITIONAL_NEW | Only missing shared binding helpers, not a second identifier generator. |
| src/triggertrade/set_engine/{formulas,handler,cancellation}.py | NEW_PROPOSED | Missing canonical Set implementations inside the existing owner/worker architecture. |
| src/triggertrade/position_rules/{formulas,sizing,economics,handler}.py | NEW_PROPOSED | Missing canonical Position computations, extending existing pin/construction/spec state. |
| src/triggertrade/portfolio_rules/{handler,capital}.py | NEW_PROPOSED | Portfolio owner implementations; reuse existing grants/holds/buckets. |
| src/triggertrade/order_lifecycle/handler.py | NEW_PROPOSED | Existing Lifecycle owner handler, not a new Lifecycle service. |
| src/triggertrade/accounting/finality.py and funding/source helpers | NEW_PROPOSED | Internal Lifecycle-owned canonical financial operations; no fifth owner or dual ledger. |
| src/triggertrade/services/owner_dispatch.py | CONDITIONAL_NEW | Only a thin registration wrapper within the existing worker if needed; no alternative runnable worker. |
| New owner-state stores or migrations | CONDITIONAL_NEW | Owner checkpoint first proves absence/incompatibility; prefer extension. Next unused migration revision is discovered then, not guessed now. |
| New test filenames in checkpoint scopes | CONDITIONAL_NEW | Extend an equivalent existing suite first; added cases must test source semantics independently. |

| Exact preservation path | Classification | Use |
| --- | --- | --- |
| src/triggertrade/accounting/futures.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/api_adapter_gateway/market_data.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/api_adapter_gateway/native_profile.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/api_adapter_gateway/order_management.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/api_adapter_gateway/portfolio_data.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/canonical_json.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/capital_grants.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/contracts/_approved_wire_schema.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/contracts/registry.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/contracts/schema_validator.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/execution/bybit.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/execution/paper.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/execution/precision.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/lifecycle_close_authority.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/lifecycle_set_sync.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/lifecycle_start_gate.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/lifecycle_submission.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/market_data/regime.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/order_specs.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/capital_grant_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/coins_scope_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/daily_loss_store.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/durable_messages.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/futures_accounting_store.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_close_authority_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_order_event_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_reconciliation_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_set_sync_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_start_gate_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/lifecycle_submission_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/market_data_fact_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/order_spec_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/portfolio_cooldown_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/portfolio_data_facts.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/portfolio_state_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/position_config_pin_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/position_construction_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/postgres.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/persistence/submit_authorization_store.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/portfolio_cooldown.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/portfolio_state.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/position_config_pins.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/position_construction.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/research_pins.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/services/daily_loss.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/services/futures_accounting_bridge.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/services/process_roles.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/services/runtime.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/services/trading_worker.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/set_scope.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/strategies/futures_directional.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/submit_authorizations.py | EXISTING | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/triggers/percentage_price_move.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |
| src/triggertrade/triggers/volume_confirmation.py | LEGACY_ONLY | Preserve/extend only under the FN component and checkpoint assigned above; legacy classification never authorizes canonical use. |

## 3. Normalized frozen-clause requirement register

### 3.1 Authoritative planning register

The former R001–R060 numbers were reconstructed by the earlier map, not an original numbered normative register in the conformance audit. They now have only the status `HISTORICAL_TRACEABILITY_ALIAS`. The NR register below is the source-based implementation mapping; frozen clauses override every summary. R6 contains exactly NR-001–NR-154. The existing NR-001–NR-152 rows remain unchanged. NR-153 and NR-154 explicitly map the two frozen Position research-reporting obligations identified by FA-R5-01; like NR-151/NR-152, they receive no historical R alias. Analytical report conventions in §6.4 are diagnostic implementation definitions, not additional trading obligations or certified objects.

`ST.*` and `TX.*` resolve to §§6–7. `AT-NR-xxx` names the row’s independently source-derived acceptance requirement. `G-Bx` resolves to the complete independent gate list in §10. Tests and reviews are part of the implementation checkpoint that creates the behavior; all NR groups also participate in B13 integrated verification and B14 independent re-audit.

| Normalized ID | Frozen source path / exact section / lines | Normative behavioral obligation | Owner | Evidence-supported current condition | Implementation checkpoint(s) | Persistence impact | Transaction impact | Required acceptance test | Independent review | Historical alias(es) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NR-001 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L45 | Preserve four business owners and staged decision/grant/construction/authorization flow. API is a factual boundary; internal financial work remains Lifecycle-owned, not a fifth owner. | All four owners | PARTIAL: existing structural/binding builders; owner production not completed by them [E26–E29,E35–E42]. | B4, B12, B13 | ST.transport | TX.owner | AT-NR-001: Reject every extra decision/API edge and cross-owner recomputation; verify the exact graph in §4. | G-B4; G-B12; G-B13 | R006, R017 |
| NR-002 | `docs/trading-methodology/schemas/CONTRACT_REGISTRY.json` — **JSON document / definitions**, L1–L135 | Align active package to v1.2.15 and all twelve registry/schema definitions without changing the frozen family versions. | Technical contract boundary | CONFLICTING current package/branch enforcement; reusable registry and parser [E26–E29; schema_probe.json]. | B0 | NONE | NONE | AT-NR-002: Compare generated definitions and root whitelists with every frozen registry family; reject unknown family/version. | G-B0 | R010, R052, R053 |
| NR-003 | `docs/trading-methodology/schemas/wire.schema.json` — **JSON document / definitions**, L2653–L2813<br>`docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md` — **Payload**, L16–L71<br>`docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md` — **Shared schema and replay boundary**, L281–L286 | Public parser enforces both cause branches, required/forbidden fields, enum and all constructs actually used by the frozen schema; schema substitution alone is not conformance. | Technical contract boundary | CONFLICTING current package/branch enforcement; reusable registry and parser [E26–E29; schema_probe.json]. | B0 | NONE | NONE | AT-NR-003: Run all eight parser branch cases in §9.1 through parse_contract, not only a schema helper. | G-B0 | R011, R012, R055 |
| NR-004 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` — **F08 batched symbol sections (contract v5)**, L572–L576 | instrument_metadata and fee_rates item status is binary AVAILABLE/UNAVAILABLE; PARTIAL belongs only to aggregates. Enforce requested-symbol row cardinality. | API; Portfolio consumption | CORRECT adapter binary helper; current public source-schema enforcement still requires alignment [E33,E26–E29]. | B0, B3 | ST.facts | TX.facts | AT-NR-004: Reject per-item PARTIAL for both sections; accept mixed binary items with aggregate PARTIAL and exact requested rows. | G-B0; G-B3 | R005 |
| NR-005 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` — **Identifier lineage — v1.2.15**, L10–L15<br>`docs/trading-methodology/README.md` — **TriggerTrade — Active Specification Documentation v1.2.15**, L1–L26 | New configuration/research evidence uses the correct frozen package binding; retained configuration/version/content digest remains immutable through replay. Do not rewrite historical evidence to appear newly pinned. | Configuration-owning owners; Research | CONFLICTING current package/branch enforcement; reusable registry and parser [E26–E29; schema_probe.json]. | B0, B4 | ST.config | TX.owner | AT-NR-005: Update only active expectations/defaults; preserve archive-negative fixtures and old immutable records. | G-B0; G-B4 | R014, R029, R054, R056 |
| NR-006 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **6. Canonical serialization and replay**, L82–L94 | Use one canonical JSON/digest path; exact canonical scalar encoding and complete immutable envelope digests, no display feedback or alternate serializer. | All owners / shared utility | REUSE_AS_IS: canonical JSON and digest utility is supported by source evidence [E30]. | B1 | ST.transport | TX.owner | AT-NR-006: Equivalent canonical values serialize identically; floats/nonfinite/exponent outputs fail; full envelope/version mutation changes digest. | G-B1 | R001 |
| NR-007 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **1. Arithmetic model and operation order**, L8–L30 | Parse finite decimal text exactly into scaled integers/rationals. Addition/multiplication/comparison and intermediate division must not acquire finite-context rounding. Resource failure is explicit, not silent quantization. | Shared numeric utility | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1 | NONE | NONE | AT-NR-007: Independent integer/rational oracle for large scales, nonterminating quotients, signed comparisons and explicit resource rejection. | G-B1 | R015 |
| NR-008 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **2. Output classes**, L16–L30<br>`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **2. Working arithmetic and operation order**, L33–L68 | Expose HALF_EVEN, floor, ceil, truncation toward zero and directional tick/step primitives; use only the output policy selected by the owning formula. | Shared numeric utility | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1 | NONE | NONE | AT-NR-008: Positive/negative ties and adjacent values around each grid; zero/invalid quantum and forbidden implicit conversion. | G-B1 | R015 |
| NR-009 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **2. Working arithmetic and operation order**, L33–L94 | Keep Q36 WORKING values distinct from Q18 WIRE exports; exact intervening arithmetic and named HALF_EVEN points only. No reconstructing working precision from exports. | Set / shared numeric utility | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B5A | ST.setcalc | TX.setcalc | AT-NR-009: Near-threshold work/export disagreement retains working decision; Q18 rounded-to-zero required ATR prevents a handoff. | G-B1; G-B5A | R015, R035, R036 |
| NR-010 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **4. Population standard deviation and sqrt**, L61–L66 | Provide exact integer midpoint square root on the work grid for population standard deviation; compare squared integer midpoint and HALF_EVEN ties, no float/libm approximation. | Shared utility; Set consumer | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B5A | ST.setcalc | TX.setcalc | AT-NR-010: Perfect square, exact midpoint, both sides, huge rational variance and zero population variance. | G-B1; G-B5A | R015, R036 |
| NR-011 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **3. Portfolio grant and atomic capacity gates**, L45–L61 | Spendable/grant Qcapital is floor at 1e-12; liability is ceil. Keep exact mathematical F-011 A distinct from quantized H; Portfolio copies H without another quantizer. | Portfolio; Position owns construction | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B7B, B8B, B8C | ST.grants; ST.construction; ST.holds | TX.grant; TX.construction; TX.hold | AT-NR-011: Nonterminating N/leverage, exact A<=C and H<=C, H not C and zero extra hold for unused grant. | G-B1; G-B7B; G-B8B; G-B8C | R019, R043 |
| NR-012 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **2. Output classes**, L16–L30<br>`docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **4. Position final construction and proof of no overcommit**, L53–L61 | Qratio floor at 1e-18 is REPORT_ONLY where specified. Initial gross and post-grant economics gates compare exact values before reporting. | Position | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B7A, B7B | ST.position; ST.construction | TX.opportunity; TX.construction | AT-NR-012: Values just below/equal/above thresholds that serialize to the same ratio must retain distinct exact outcomes. | G-B1; G-B7A; G-B7B | R020, R042 |
| NR-013 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` — **Identifier lineage — v1.2.15**, L1–L82 | One creator per opaque persisted identity; exact immutable binding and replay reuse, not blanket deterministic re-derivation. No latest/symbol-only/nearest-time association. | All owners | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B4 | ST.config; ST.transport | TX.owner | AT-NR-013: Same semantic identity reuses accepted bytes; wrong lineage/content conflicts; a new unrelated ID cannot acquire an old binding. | G-B1; G-B4 | R013 |
| NR-014 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L45 | Each required owner transition and its mandatory publications share the specified atomic commit. No durable partial decision, construction/spec or authorization may escape the P1 boundary. | Each owning business block | REUSE_AS_IS UoW; EXTEND owner composition, not a second transaction layer [E31–E32]. | B2 | ST.transport | TX.owner | AT-NR-014: Injected rollback between every store/outbox step leaves no partial owner effect. | G-B2 | R030 |
| NR-015 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **S01 — Current finality evidence and terminal quarantine**, L373–L382<br>`docs/trading-methodology/IDENTIFIER_LINEAGE.md` — **Identifier lineage — v1.2.15**, L5–L82 | Retain durable publication, delivery identity, inbox conflict detection and terminal-safe idempotency; owner outcomes are committed with publication before acknowledgement. | Technical transport; each owner | Existing append/claim/inbox primitives are reusable; full business composition remains partial [E31–E32]. | B2 | ST.transport | TX.owner | AT-NR-015: Same ID/content is inert; changed content conflicts; lost ack and concurrent delivery do not duplicate owner effect. | G-B2 | R002, R003, R004 |
| NR-016 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T01 — Separate terminal result and post-final integrity incident**, L459–L503 | Provide a scoped serializable committed-prefix frontier on the existing Lifecycle→Portfolio edge; publication order and Portfolio eligibility/receipt decisions share real fencing, not generic dedupe. | Technical transport; Lifecycle and Portfolio each own local effect | PARTIAL: existing PostgreSQL UoW/CAS/outbox/inbox; domain and frontier composition not proven [E31–E32; audit §17]. | B2, B8C, B10 | ST.frontier; ST.incidents | TX.frontier | AT-NR-016: Two concurrent commits, missing prefix gap, cached head, crash/retry and independent scopes; no first release across prior committed incident. | G-B2; G-B8C; G-B10 | R030, R043 |
| NR-017 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` — **Identifier lineage — v1.2.15**, L1–L82 | Persisted immutable identities, accepted content/configuration and provenance history remain recoverable and unchanged across storage/hydration changes; no representation change authorizes remint or loss of binding history. | Each state owner | Existing PostgreSQL migration/UoW foundations recorded; actual deployed schema not inspected [E31; audit §16]. | B2 | ST.transport | TX.owner | AT-NR-017: Migration/upgrade/hydration preserves identities/digests and owner histories; rollback disables runtime rather than deleting trading evidence. | G-B2 | R030 |
| NR-018 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P14 — Exact construction confirmation and multi-symbol factual cardinality**, L302–L312 | Shared contract layer validates structure, full identity/digest/scalar equality and stage shapes; actual business production/consumption stays in owner checkpoints. | Technical binding helpers; owner validators | PARTIAL: existing structural/binding builders; owner production not completed by them [E26–E29,E35–E42]. | B4 | NONE | NONE | AT-NR-018: Wrong stage, scalar mismatch despite supplied digest, unknown field and forbidden owner edge fail; helper does not mint a business decision. | G-B4 | R012, R024, R025 |
| NR-019 | `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md` — **1. Evidence, not outbound intent**, L5–L62 | Evidence normalization is not native profile certification. Exposure-changing execution requires the applicable native profile proof and current factual authority; uncertified paths stay blocked. | API factual evidence; Lifecycle execution gate | Native-profile helper/tests exist but supplied certification evidence does not certify profiles [E56–E57]. | B3, B9, B12 | ST.nativefacts; ST.protection | TX.facts; TX.native | AT-NR-019: Correctly shaped facts with uncertified profile still deny exposure; missing field authority/provenance cannot become accepted proof. | G-B3; G-B9; G-B12 | R017, R048 |
| NR-020 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Research isolation — S-005 diagnostic-only boundary**, L887–L897 | S-005 and research/demo diagnostics never supply canonical direction, construction, authorization or execution decisions; preserve authorized evidence/promotion boundaries and isolate legacy paths. | Research / all canonical owner import boundaries | Existing research/launcher fences reusable; complete owner-runtime isolation still needs integrated proof [E24,E52; audit §31]. | B13, B12 | ST.research | NONE | AT-NR-020: Canonical import/dispatch cannot reach demo triggers, S-005 regime decisions, paper/spot runtime or SQLite authoritative ledger. | G-B13; G-B12 | R029, R046, R057, R058, R059, R060 |
| NR-021 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` — **Purpose and authority**, L6–L33 | Portfolio requests account/venue facts and consumes API response; permitted frozen facts reach Position only through the grant. API makes no capital or trade decision. | Portfolio; API technical boundary | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B8A, B8B | ST.facts | TX.facts; TX.grant | AT-NR-021: Bidirectional exact request/response/symbol binding; refuse direct Position API call or response consumer. | G-B3; G-B8A; G-B8B | R016, R017, R048 |
| NR-022 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` — **1. Authority and version**, L6–L44 | Set owns pinned selections/requests; API returns factual selected datasets/pages. Enforce completed-data/as-of, coverage, cardinality and factual unavailability without analytic decisions. | Set; API technical boundary | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B5B | ST.facts; ST.setcalc | TX.facts | AT-NR-022: Missing/extra selection, noncontiguous page, wrong request echo, incomplete coverage and stale response cannot silently substitute latest facts. | G-B3; G-B5B | R027, R048 |
| NR-023 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` — **Consumer assembly consistency (wire version unchanged)**, L228–L247 | Persist exact selected request/page/snapshot ownership and assembly. Known historical page conflicts are checked before request/selection echo validation or stale suppression. | Set; factual intake | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B5B | ST.facts | TX.preflight; TX.facts | AT-NR-023: Known page with wrong/missing request or selection echo still retains contradiction; both echoes checked independently. | G-B3; G-B5B | R027, R013 |
| NR-024 | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` — **Existing boundary, complete factual input**, L6–L54 | Lifecycle alone requests governed native operations, current hard facts, open/history/executions and financial facts; API responses return only to Lifecycle. | Lifecycle; API technical boundary | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B9, B10 | ST.nativefacts | TX.facts; TX.native | AT-NR-024: All operation request/response modes route on the sole permitted edge; unsupported/unavailable evidence never becomes success. | G-B3; G-B9; G-B10 | R017, R048 |
| NR-025 | `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md` — **3. Proven acceptance profile**, L25–L62 | Retain accepted-at, authoritative source/effective time, endpoint/record/field/profile identity and field-specific provenance; no receipt-time or source-status guess substitutes authoritative facts. | API; consuming owner accepts | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B9 | ST.facts; ST.nativefacts | TX.preflight; TX.facts | AT-NR-025: Equal-time field enrichment only when allowed; contradictory authoritative facts quarantine; malformed source metadata cannot be synthesized. | G-B3; G-B9 | R016, R048 |
| NR-026 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **U05 — Raw magnitude/direction validation precedes normalization**, L680–L695 | Validate raw magnitude/direction and normalized signed source/quantum before normalization erases information. Preserve signed zero and credit/debit rules; invalid pairs cannot substantiate COMPLETE/FINAL. | API normalization; Lifecycle financial acceptance | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B10 | ST.financial | TX.preflight; TX.facts | AT-NR-026: Full U05 sign truth table; contradictory nonzero magnitude+ZERO never becomes 0; later complete certificate cannot clear unresolved sign conflict. | G-B3; G-B10 | R015, R047 |
| NR-027 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Preventive synchronization — canonical evidence-ingestion invariant**, L872–L885 | For recognizable accepted evidence, resolve persisted identity/ownership from raw exact anchors, compare complete canonical content including presence/null, durably retain challenges before ordinary parsing/stale/terminal/routing rejection. | Every evidence-accepting owner | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B5B, B9, B10 | ST.facts; ST.nativefacts; ST.financial; ST.incidents | TX.preflight | AT-NR-027: Known contradiction plus unrelated malformed companion retains incident and no ordinary partial update; unrecognizable malformed input only rejects. | G-B3; G-B5B; G-B9; G-B10 | R016, R027, R031, R047 |
| NR-028 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **X03 — Durable known-evidence preflight before mixed-batch rejection (normative)**, L808–L823 | Use a durable preflight checkpoint independent of later ordinary-batch rollback across financial, acceptance, native and current-protection intake. A true crash before commit commits neither; redelivery reprocesses raw evidence. | Accepting owner | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B9, B10 | ST.incidents; ST.facts | TX.preflight | AT-NR-028: Failure after preflight commit retains challenge; modeled precommit crash retains neither and retry recreates one identical challenge. | G-B3; G-B9; G-B10 | R030, R044 |
| NR-029 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **V05 — Known historical identity before semantic rejection**, L738–L789 | Restore full monotonic accepted revision/content history and source aliases; check known historical ownership and canonical alias identity before stale/new-echo filtering. No latest-only history reconstruction. | Set; Lifecycle; Portfolio projections | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B5B, B9, B10 | ST.facts; ST.nativefacts; ST.financial | TX.preflight | AT-NR-029: Changed older accepted revision conflicts after newer resolution; identical history replay does not clear later block; unrelated scope cannot refresh proof. | G-B3; G-B5B; G-B9; G-B10 | R013, R027, R031 |
| NR-030 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **U03 — Canonical acceptance resolution before tombstone suppression**, L664–L670 | Accepted entry resolution binds original entry_accepted_at, provenance, covered evidence, resolution ID/revision and proof. Tombstone cannot suppress changed historical content or restart cooldown origin. | Lifecycle producer; Portfolio consumer | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B8C | ST.acceptance; ST.cooldown | TX.acceptance | AT-NR-030: Same historical resolution choosing a new timestamp restores block without moving original origin; identical replay never clears a later incident. | G-B9; G-B8C | R043, R044 |
| NR-031 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Y02 — Recognizable accepted financial coverage before parsing**, L848–L870 | Persist owner-local overall/component financial coverage certificate keys from request_id/response_id/operation/kind/component, monotonic accepted revision, full binding, raw provenance, digest and source-member set. | Lifecycle | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B10 | ST.coverage | TX.preflight; TX.facts | AT-NR-031: Reused key changed content/omission/null conflicts; exact unique fallback indexes recover known owner, ambiguity quarantines, no new wire ID. | G-B3; G-B10 | R047 |
| NR-032 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **U02 — Complete immutable financial source core and post-FINAL producer coverage**, L652–L663 | Persist complete immutable financial_record core and every proven representation/alias. API-proven aliases enrich provenance only; different content, unproven replacement or alias collision cannot duplicate or rewrite economics. | Lifecycle | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B10 | ST.financial; ST.incidents | TX.preflight; TX.facts | AT-NR-032: Same source represented twice posts once; primary-provenance changes require proven alias; mutation of every bound core field is detected. | G-B3; G-B10 | R047 |
| NR-033 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **V01 — Known financial identity before pre-FINAL routing**, L706–L737 | Resolve known financial identity and factual execution evidence before routing/stale/terminal suppression; accept complete revisionless bindings, and invalidate current protection atomically with challenging facts. | Lifecycle; Portfolio logical consumer | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B10 | ST.nativefacts; ST.financial; ST.protection | TX.preflight; TX.protection | AT-NR-033: Late recognizable raw challenge under invalid route persists; rejection does not delete execution; no revisionless content shortcut. | G-B9; G-B10 | R031, R044, R047 |
| NR-034 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Y01 — Immutable accepted native-observation identity**, L840–L847 | Accepted native_observation_id binds original scope revision, quantity and supplied provenance. Changed lower revision is changed replay, not stale; preserve tombstones/receipts and block scope without quantity reversal. | Lifecycle; Portfolio projection | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B10 | ST.attribution; ST.incidents | TX.preflight; TX.partition | AT-NR-034: Same observation lower revision conflicts; resolved replay inert; provisional observation acquires only its first authoritative quantity, not fabricated history. | G-B9; G-B10 | R031, R044 |
| NR-035 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **3. Daily accounting boundary**, L130–L154; **4. Daily portfolio base and live P&L state**, L158–L247; **Appendix B — Daily rollover recovery and metric scopes (v1.1.0)**, L1847–L1883<br>`docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P8 — Economic time, operational time and accounting day**, L193–L220 | Use one ACCOUNTING_DAY_V1 accounting day in Asia/Jerusalem, with persisted accounting_day_id and resolved half-open local-midnight boundary instants. At rollover establish one fixed daily_portfolio_base = strategy_wallet_capital_at_rollover_excluding_unrealized_pnl from verified wallet-own-capital boundary evidence; realized cash already in that wallet value is included once, never added again. Only the frozen complete deterministic reconstruction from authoritative cashflow history spanning the boundary may replace unavailable direct boundary evidence. Without either proof, rollover_state = RECONCILING and new exposure is blocked; a later arbitrary snapshot, current equity/unrealized P&L, first post-startup observation, estimate or prior-day base is not a substitute. Keep the established base immutable throughout its accounting day and retain prior day/base/history for exactly-once historical FINAL posting. Track live current_portfolio_equity, daily_realized_pnl, unrealized_pnl and total_pnl separately; floating P&L and external capital flows do not intraday-rebase the denominator. No selectable daily-base policy or unsupported equity formula is introduced. B8A below specifies the same obligation in full. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A | ST.day; ST.portfolio | TX.day for canonical accounting-day/base/latch establishment and recovery (accounting_day_id, resolved civil-midnight boundary instants, fixed daily_portfolio_base, authoritative boundary evidence or complete deterministic reconstruction, rollover_state, day/latch history and restart/hydration), serialized against historical receipt/day effects where applicable; TX.scope only for consequential scope publication or new-exposure eligibility resulting from Portfolio health/day state | AT-NR-035: All fourteen source-derived cases in B8A’s AT-NR-035 matrix are mandatory: boundary proof; unrealized exclusion; no realized-cash double-add; fixed base with changing live equity/capital flows; no floating-P&L rebase; rejection of substitute snapshots/estimates/prior-day bases; complete reconstruction; incomplete reconstruction fail-closed; new-day rollover with prior base preserved; historical FINAL isolation; separate equity; separate unrealized; restart; DST/local-midnight boundaries. Use frozen-source expectations; B8A fixtures do not replace actual B10 receipt integration. | G-B8A | R018, R045 |
| NR-036 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **5. User Portfolio Rules configuration** through **8. Coin allocation sum semantics**, L251–L358; **19. Global capacity gate** through **22. Coin allocation gate**, L700–L771; **41.1 Atomic hold transaction**, L1361–L1363 | Pin Portfolio configuration and validate each coin's configured allocation percentage/cap under its own frozen constraints, with the global position cap preserved independently. Aggregate coin allocation targets MAY exceed the global position cap; their sum alone does not make configuration invalid. Do not add a configuration-sum ceiling or normalize targets to fit the global cap. Actual simultaneous committed own capital must satisfy the runtime global hard cap and each coin's independent hard cap, under the unchanged grant/current H-booking, slot and capacity gates; no replacement allocator or market strategy. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8B, B8C | ST.config; ST.portfolio | TX.scope; TX.grant; TX.hold | AT-NR-036: All four explicit cases in B8A's allocation-sum/runtime-capacity matrix are mandatory: 60% global with SOL/ETH/DOGE/BTC each 20% (80% targets) is CONFIGURATION_VALID; runtime booking above the current global cap is BOOKING_REJECTED; exceeding the individual coin cap is BOOKING_REJECTED; exact global-cap equality passes the inclusive capacity gate when all other prerequisites pass. B8A verifies configuration/capacity fixtures, B8B preserves the valid configuration and non-reserving grant, and B8C verifies actual H booking. Retain unknown-coin configuration rejection and tests that current configuration changes never rewrite pinned attempt history. | G-B8A; G-B8B; G-B8C | R018, R020, R043 |
| NR-037 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **9. Portfolio Rules-owned state**, L364–L429 | Retain canonical Portfolio state/buckets and health, including LIVE/RECONCILING/STALE restrictions; no missing factual state inferred as free capacity. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8C | ST.portfolio | TX.scope; TX.hold | AT-NR-037: Reconciliation/stale/missing evidence blocks new authority; factual liabilities remain even if apparent free capital is negative. | G-B8A; G-B8C | R018 |
| NR-038 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **10. Refresh triggers**, L430–L520 | Evaluate governed Portfolio triggers and health-dependent scope; unavailable current account/day facts fail closed without a Set or Lifecycle decision shortcut. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A | ST.portfolio; ST.scope | TX.scope | AT-NR-038: Missing inputs preserve block; restored facts do not erase unrelated unresolved incidents. | G-B8A | R018, R026 |
| NR-039 | `docs/trading-methodology/business-contracts/COINS.md` — **Purpose**, L6–L80 | Portfolio publishes persistent monotonic OPEN/CLOSE scope revisions with pinned configuration; Set consumes exact scope and maintains its own epoch. CLOSE affects unfinished formation, not accepted pending monitoring. | Portfolio produces; Set consumes | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B5B | ST.scope; ST.transport | TX.scope; TX.set | AT-NR-039: Same revision different content conflicts; stale identical replay inert; newer scope ends only unfinished older epoch. | G-B8A; G-B5B | R026 |
| NR-040 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **13. Submission hold and reservation start**, L521–L601 | Keep held, remaining-reserved, filled and closing-retained capital mutually exclusive; free capacity deducts all required commitments and slots include unresolved attempts. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8C, B9 | ST.portfolio; ST.holds | TX.hold; TX.acceptance; TX.closeretention | AT-NR-040: Each transition conserves exact total; held H not C; unresolved/closing exposure cannot make a slot or capital disappear. | G-B8A; G-B8C; G-B9 | R018, R019, R043 |
| NR-041 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **17. Dynamic tranche sizing**, L602–L699<br>`docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **3. Portfolio grant and atomic capacity gates**, L45–L51 | Portfolio computes dynamic grant from governed current free capacity and positive remaining slots, respecting minimum capital and exact floor sequence; grant is non-reserving. | Portfolio | PARTIAL: grant issue/binding store exists; canonical owner gates incomplete [E35–E36,E47]. | B8B | ST.grants | TX.grant | AT-NR-041: Zero slots/nonpositive capacity/minimum capital failure creates no grant; repeated or concurrent non-reserving grants do not book capital. | G-B8B | R043 |
| NR-042 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **19. Global capacity gate**, L700–L775 | Apply global allocation, total concurrent slots, per-coin slots and per-coin allocation gates separately from Position economics. Current hold rechecks exact inclusive limits. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8B, B8C | ST.portfolio; ST.holds | TX.grant; TX.hold | AT-NR-042: Boundary equality passes where defined; one-quantum excess and concurrent last-slot requests cannot both book. | G-B8A; G-B8B; G-B8C | R020, R043 |
| NR-043 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **23. Daily Loss Limit**, L776–L874 | A-009 consumes once-received immutable FINAL net results on the bound economic day. Ordered disabled / retained latch / missing state / exact inclusive threshold / OK branches; no unrealized summand. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8C, B10 | ST.day; ST.receipts | TX.day; TX.receipt; TX.hold | AT-NR-043: Exact R_day<=-base*pct/100 including equality; disabled/re-enabled retained latch, empty known day vs missing state, no report-quantized gate. | G-B8A; G-B8C; G-B10 | R018, R020, R043, R045 |
| NR-044 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **24. Cooldown**, L876–L962 | Cooldown starts from authoritative accepted entry time and attempt-pinned duration, not grant/create/callback time. Preserve ambiguity/reconciliation, no grant/order TTL or newer-opportunity cancellation. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B8C, B9 | ST.cooldown; ST.acceptance; ST.config | TX.hold; TX.acceptance | AT-NR-044: Late accepted evidence keeps original origin/duration; changed current config cannot restart cooldown; unresolved origin blocks rather than guesses. | G-B8A; G-B8C; G-B9 | R043 |
| NR-045 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **27. Pending LIMIT orders after cooldown**, L962–L1072<br>`docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **5. Pre-close partial-entry apportionment and residue owner**, L63–L80 | On pending/partial/full/zero-fill and terminal remainder transitions apply exact approved-capital apportionment before close only; retain filled liability, release only proven terminal unused remainder once. | Portfolio consumes Lifecycle facts | PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. | B8C, B9 | ST.portfolio; ST.holds; ST.acceptance | TX.acceptance | AT-NR-045: Partial fill then terminal cancel uses ceiling retained total and residue policy; delayed rejection with execution cannot erase liability. | G-B8C; G-B9 | R043 |
| NR-046 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P6 — CLOSED is one unified predicate composed of six required conditions and explicit retained commitment**, L114–L136 | At close acquisition transfer full then-committed capital/slot into closing_retained; freeze accepted quantity basis and hold through zero exposure and cleanup until canonical terminal receipt. | Portfolio projection; Lifecycle close evidence | PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. | B8C, B9, B10 | ST.holds; ST.close; ST.receipts | TX.closeretention; TX.receipt | AT-NR-046: Partial exit or flat observation alone releases nothing; already released pre-close cancelled remainder is excluded from frozen basis. | G-B8C; G-B9; G-B10 | R043, R047 |
| NR-047 | `docs/trading-methodology/business-contracts/CAPITAL_AND_LIMITS.md` — **Issue timing and binding**, L6–L58 | Issue one immutable non-reserving grant only after exact initial Position APPROVE; bind cycle/result/decision, permitted venue/accounting/profile/fee facts and grant amount. No fabricated initial approval. | Portfolio | PARTIAL: grant issue/binding store exists; canonical owner gates incomplete [E35–E36,E47]. | B8B | ST.grants; ST.config | TX.grant | AT-NR-047: Duplicate APPROVE returns same grant/outbox; wrong stage, decision or content conflicts; grant neither creates H hold nor plan/spec. | G-B8B | R019, R043 |
| NR-048 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **41. Initial APPROVE and post-grant construction**, L1293–L1396 | On successful construction verify exact result/spec/digest/scalars, current capacity/slots/limits/cooldown/day/incident frontier and H; atomically consume grant, book H and slot, pin attempt config and publish SUBMIT_AUTHORIZED. | Portfolio | PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. | B8C | ST.holds; ST.portfolio; ST.config; ST.frontier | TX.hold; TX.frontier | AT-NR-048: First bookable constructed transaction wins; exact H, duplicate auth inert, scalar mismatch fails despite digest; current incident defeats stale grant. | G-B8C | R019, R020, R023, R043 |
| NR-049 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **43. Order Event**, L1397–L1539 | Consume governed logical/native/acceptance/clearance events under separate identity/revision domains; no inference of tranche from aggregate native scope or silent clearing of unresolved evidence. | Portfolio | PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. | B8C, B9, B10 | ST.attribution; ST.portfolio; ST.acceptance | TX.partition; TX.acceptance; TX.receipt | AT-NR-049: Native manifest and logical allocations are not double effects; provisional unresolved scopes and terminal tombstones survive reorder/restart. | G-B8C; G-B9; G-B10 | R021, R043 |
| NR-050 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **54. Daily rollover event contract**, L1593–L1660 | Rollover creates the next governed accounting day/base while preserving unresolved commitments, immutable historical results and prior latch history; leverage/price changes do not repair allocations. | Portfolio | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B10 | ST.day; ST.holds | TX.day; TX.receipt | AT-NR-050: Boundary/DST instants, concurrent result and rollover, restored commitments and late historical first receipt leave current-day base/latch unmodified. | G-B8A; G-B10 | R018, R045 |
| NR-051 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P8 — Economic time, operational time and accounting day**, L193–L221 | Portfolio creates its own first durable delivered_at receipt, unique by result_id and tranche_id, with economic-day posting, A-009 application and once-only capital/slot release in one transaction under the committed-prefix gate. | Portfolio | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.receipts; ST.day; ST.portfolio; ST.frontier | TX.receipt; TX.frontier | AT-NR-051: Receipt-before/after incident, duplicate/conflicting result, historical late result, crash before/after commit; no wallet/equity double-credit. | G-B10 | R043, R047 |
| NR-052 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — **59. Set boundary**, L1679–L1740 | Portfolio verifies Position outputs and current own gates but never recomputes Entry/SL/TP/F-011/F-012; funding never triggers an exit. | Portfolio | PARTIAL: grant issue/binding store exists; canonical owner gates incomplete [E35–E36,E47]. | B8B, B8C, B13 | NONE | TX.grant; TX.hold | AT-NR-052: Replace a Position formula dependency with a trap in Portfolio tests; verify only supplied immutable construction evidence is consumed. | G-B8B; G-B8C; G-B13 | R019, R020 |
| NR-053 | `docs/trading-methodology/methodology/SET.md` — **TriggerTrade — Set Methodology**, L1–L616, especially **5. Direction belongs to Set**, L509–L530; `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P17 — Immutable configuration binding for started cycles and attempts**, L359–L365 | Use the frozen Trigger/Core Set configuration model, typed nodes, configured references and source requirements. Set owns all final direction. For F-005-governed Sets, final direction is resolved only by F-005; fixed-direction and matched-branch labels cannot bypass, override or reverse it, and F-001/F-002/F-003 do not independently decide final direction. Outside that scope, existing generic deterministic Set definitions may fix direction or determine it explicitly from the matched branch. Conflicting LONG/SHORT branches at the same canonical timestamp require declared deterministic conflict resolution in the frozen Set definition; without it the configuration is invalid and no directional handoff is eligible. Within F-005 scope, arbitration of eligible Core Sets must also be deterministic, Set-owned and consistent with F-005; missing/conflicting arbitration is ineligible. No API, Portfolio, Position, Research/S-005, human-readable name, first-arrival, lexical, strongest-score or other undeclared mechanism may determine direction. Bind the governing scope, fixed/branch rule and any declared conflict rule to the immutable Set configuration/epoch and retained result; no latest-configuration reinterpretation or retry remint. This is the same Set owner, not a new formula/service or a new scope switch. No generic legacy percentage/volume trigger is promoted into canonical evaluation. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A, B5B | ST.config; ST.setcalc | TX.setcalc; TX.set | AT-NR-053: Each configured node/source type follows its frozen availability and grouping rules; missing or invalid configuration cannot become an empty successful Set. B5B's cases A–H explicitly cover governed F-005 positives and bypass negatives, generic fixed/explicit matched-branch positives without an F-005 prerequisite, unresolved generic conflict rejection, declared deterministic conflict resolution, cross-owner negatives and configuration/scope/branch/result replay integrity. B5A tests the applicable pure configuration/kernel boundary; B5B tests durable dispatch and identical original handoff/IDs; V03/V04/V15/V17 and B13 verify the same expectations through the integrated path. | G-B5A; G-B5B | R033, R034, R035 |
| NR-054 | `docs/trading-methodology/methodology/SET.md` — **8A. F-001 — Signed 1m endpoint price displacement**, L617–L846 | F-001 is signed 1m endpoint percentage displacement with its specified completed endpoints, current-state semantics, exact operation order and threshold logic. It is not ATR-normalized momentum or final direction. F-001 is a configured formation trigger only: its TRUE/FALSE/UNAVAILABLE and signed work evidence may affect formation but are neither numerical operands nor availability prerequisites of F-004. Final direction is not its output. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A kernels; B5B integration | ST.setcalc; ST.setevents (formation); ST.setresults (eligible final resolution) | TX.setcalc; TX.set | AT-NR-054: Both signs, equality, nonpositive denominator, exact required endpoint/coverage and no interpolation; distinguish F-001 from normalized momentum. Mandatory classifier/formation discriminator AT-NR-068-CF A–D in §5.3, through actual B5A/B5B paths. | G-B5A; G-B5B | R033 |
| NR-055 | `docs/trading-methodology/methodology/SET.md` — **8B. F-002 — Futures relative participation confirmation**, L847–L1081 | F-002 is 1m relative participation/volume confirmation with its own governed baseline population and completed-data requirements. It has no LONG/SHORT ownership. F-002 is a configured formation participation trigger only. Its base-volume/trigger-local population remains distinct from F-004 quote-turnover and normalization populations, and neither its result nor its availability is an F-004 classifier operand or gate. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A kernels; B5B integration | ST.setcalc; ST.setevents (formation); ST.setresults (eligible final resolution) | TX.setcalc; TX.set | AT-NR-055: Missing/zero baseline, exact membership and threshold equality; own trigger population is not replaced by F-004 normalization population. Mandatory classifier/formation discriminator AT-NR-068-CF A–D in §5.3, through actual B5A/B5B paths. | G-B5A; G-B5B | R034 |
| NR-056 | `docs/trading-methodology/methodology/SET.md` — **9. Boolean logic**, L1082–L1393 | Preserve Boolean/sequence/N-of-M, satisfaction-window and maintained/invalidation semantics exactly; distinguish CURRENT_STATE and FRESH_EVENT rather than synthesizing fresh occurrences from persisted TRUE state. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A, B5B | ST.setcalc; ST.setevents | TX.setcalc; TX.set | AT-NR-056: Cold-start TRUE, FALSE→TRUE, interrupted unavailable sequence, duplicate source, expired original window and repeated state never counterfeit a fresh event. | G-B5A; G-B5B | R035, R036 |
| NR-057 | `docs/trading-methodology/methodology/SET.md` — **15. Set lifecycle**, L1394–L1604 | Unfinished formation persists original evaluation/event/deadline and consumption per OPEN epoch. Reset/rearm, interruption, multi-timeframe completion and identity rules survive restart; no old-epoch event joins a new epoch. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.scope; ST.setevents | TX.set | AT-NR-057: OPEN/CLOSE/reopen, crash mid-sequence and same event replay reproduce original deadlines/consumption; no clock renewal on retry. | G-B5B | R026, R035 |
| NR-058 | `docs/trading-methodology/methodology/SET.md` — **25. No trade-construction or order-management Rules inside Set**, L1605–L1738 | Set alone evaluates market predicates; retained audit evidence binds configured nodes and source identities. Other owners cannot reconstruct or override a matched thesis. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.config; ST.setevents; ST.setresults | TX.set | AT-NR-058: Cross-owner request to recalculate/replace thesis fails; exact source/config changes under same identity conflict. | G-B5B | R006, R028 |
| NR-059 | `docs/trading-methodology/methodology/SET.md` — **3. Canonical time hierarchy**, L1739–L1910<br>`docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **1. Source identity, order and completeness**, L19–L38 | Use all prescribed timeframes and cadence, completed candles, ordinary UTC analytical calendars, lookback and minimum complete populations. Ordinary normalization is not the canonical ATR seed anchor. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc | TX.setcalc | AT-NR-059: UTC day-boundary and incomplete current-day exclusions; insufficient full days is unavailable; no arbitrary rolling-24-hour replacement. | G-B5A | R036 |
| NR-060 | `docs/trading-methodology/methodology/SET.md` — **Observation membership and preserved temporal rules**, L1911–L2135 | Bind complete normalization membership, z-score and time-of-day turnover/volume populations; fixed accepted members, work values and source coverage are retained separately from wire exports. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc; ST.facts | TX.setcalc | AT-NR-060: Population membership reorder gives same result; missing required member, duplicate member or zero denominator follows the exact frozen branch. | G-B5A | R036 |
| NR-061 | `docs/trading-methodology/methodology/SET.md` — **9. Swing Point specification**, L2136–L2367 | Derive confirmed swing structures, sequences and efficiency from prescribed completed evidence and fixed reference identities. No future/unconfirmed bars or downstream thesis replacement. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc; ST.references | TX.setcalc | AT-NR-061: Confirmation boundary, equal extrema/ties, missing historical predecessor, flat path and side-symmetric reference identity cases. | G-B5A | R036, R028 |
| NR-062 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **3. Wilder ATR(14) seed and recursive state**, L39–L60 | F-003 maintains canonical 15m TR/Wilder ATR14 and ATR_PCT ancestry: authoritative earliest seed, preceding close, exact TR, Q36 seed/recurrence and deterministic accepted-source order. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.atr15 | TX.setcalc | AT-NR-062: First valid seed needs 14 eligible TR values and authoritative preceding close; no arbitrary first-fetched seed; replay from checkpoints equals full history. | G-B5A | R035 |
| NR-063 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` — **3. Wilder ATR(14) seed and recursive state**, L39–L60<br>`docs/trading-methodology/methodology/SET.md` — **10. ATR semantics**, L3698–L3756 | F-003 required malformed/missing candles are unavailable, not skipped/reseeded. Valid zero close advances TR/ATR exactly once but ATR_PCT is unavailable; a price gap is not a missing interval. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.atr15 | TX.setcalc | AT-NR-063: Nonfinite/negative/inconsistent OHLC rejected; zero-close progression and next predecessor=0 preserved; zero ATR state distinguished from unavailable. | G-B5A | R035 |
| NR-064 | `docs/trading-methodology/methodology/SET.md` — **12. Directional Efficiency hard gate**, L2368–L2511 | F-004 uses prescribed efficiency and volatility/ATR-percentile populations and hard gates; source/dataset insufficiency is explicit and not a neutral score. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc; ST.atr15 | TX.setcalc | AT-NR-064: Each threshold equality and unavailable percentile/population case; optional context does not repair missing required gate data. | G-B5A | R036 |
| NR-065 | `docs/trading-methodology/methodology/SET.md` — **16. VOLATILITY_NORMALIZED_MOMENTUM specification**, L2512–L2676 | F-004 normalized momentum and independent local 5m calculation/state use their own timeframe/seed/populations. Never feed F-003 15m state into the local 5m path or substitute F-001 displacement. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.local5; ST.setcalc | TX.setcalc | AT-NR-065: Distinct 5m/15m histories produce independent checkpoints; mismatch/replay/threshold tests expose accidental shared ATR state. | G-B5A | R036 |
| NR-066 | `docs/trading-methodology/methodology/SET.md` — **18. Local momentum veto**, L2677–L2862 | Implement prescribed candidate-side local/relative-strength vetoes and the distinct non-veto aggressive delta/flow and activity factors, with their exact data dependencies and unavailable rules. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc | TX.setcalc | AT-NR-066: LONG/SHORT veto pairs, conflicting flow, missing required inputs and signed boundary vectors preserve source-defined outcomes. | G-B5A | R036 |
| NR-067 | `docs/trading-methodology/methodology/SET.md` — **24. BTC structure specification**, L2863–L3049 | Keep prescribed BTC structure/momentum/context/side veto and derivatives/other context roles; diagnostic or optional context cannot gain unapproved final-direction authority. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A | ST.setcalc | TX.setcalc | AT-NR-067: BTC pair and required context failures; changing an explicitly diagnostic-only input cannot change canonical output. | G-B5A | R036, R060 |
| NR-068 | `docs/trading-methodology/methodology/SET.md` — **31. Top-level weights**, L3050–L3226, especially §34A L3189–L3197 and §35 L3203–L3217 | F-004 computes the frozen factors, weights and Q36 score. F-005 requires all eleven inputs and derived diagnostics, inclusive hard gates and both sides of veto evidence; score >= +0.35 selects LONG, <= -0.35 selects SHORT, and the open interval is NONE. Only that candidate's BTC, relative and local-momentum vetoes can block it; opposite-side vetoes never block or reverse it. Raw aggressive-flow, undefined strong-HTF-structure, OI, funding and premium vetoes remain disabled. Classifier success is not yet a committed Set MATCHED. F-004/F-005 use only the exact frozen classifier input set, prescribed populations, F-003 context and separate local-5m evidence. No F-001/F-002 trigger output, sign/work value or trigger-local population is injected as a classifier operand or availability prerequisite. Classifier validity is independently evaluable from configured formation validity; the branches join only at B5B final resolution under SET §34A. All other formation and handoff gates remain mandatory. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A kernels; B5B integration | ST.setcalc; ST.setevents (formation); ST.setresults (eligible final resolution) | TX.setcalc; TX.set | AT-NR-068: Independent score vectors covering all eleven prescribed inputs, the three active candidate-side veto families (BTC, relative and local momentum), threshold equality and both candidate outcomes; disabled vetoes and an opposite-side veto cannot block or reverse the candidate. Mandatory classifier/formation discriminator AT-NR-068-CF A–D in §5.3, through actual B5A/B5B paths. | G-B5A; G-B5B | R036, R037 |
| NR-069 | `docs/trading-methodology/methodology/SET.md` — **35. Required-data gate**, L3201–L3495 | Respect required versus diagnostic inputs, typed result/failure evidence and frozen configuration. Score reporting/classification bands are not substitute final gates. | Set | MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. | B5A, B5B | ST.setcalc; ST.setresults | TX.setcalc; TX.set | AT-NR-069: Required-unavailable prevents valid directional handoff; diagnostic absence follows specified branch without invented neutral values. | G-B5A; G-B5B | R036, R037 |
| NR-070 | `docs/trading-methodology/methodology/SET.md` — **Part III — Market Handoff Methodology**, L3496–L3863 | Handoff is one immutable completed snapshot with Set-owned final direction, exact IDs, reference/market metadata, canonical integer freshness and positive required ATR exports. Do not add undeclared wire fields. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.setresults; ST.references | TX.set | AT-NR-070: Mutated snapshot/scalars, unusable required export or stale mandatory field refuses handoff; exact retry returns original bytes. | G-B5B | R028, R037 |
| NR-071 | `docs/trading-methodology/methodology/SET.md` — **16. Approved baseline level types**, L3864–L4066 | Resolve concrete producer-owned swing/day/range/neutral reference identities and roles from the matched configuration/evidence. Position validates these bindings rather than choosing a new thesis. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.references; ST.setresults | TX.set | AT-NR-071: Ambiguous/unresolved producer reference prevents usable handoff; equal-price distinct references do not collapse identities. | G-B5B | R028, R013 |
| NR-072 | `docs/trading-methodology/methodology/SET.md` — **23. Direction-aware interpretation belongs downstream**, L4067–L4768 | Emit only the approved reference/capability/context payload under P4; uphold optional-field gates, exclusions, ownership, no circular dependencies and strict wire synchronization. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.references; ST.setresults | TX.set | AT-NR-072: Unsupported capability, omitted required role, forbidden context field and downstream repair attempts fail. | G-B5B | R028, R037 |
| NR-073 | `docs/trading-methodology/methodology/SET.md` — **Part IV — Pending Order Market Validity**, L4837–L4934 | At final MATCHED freeze the F-013 condition record and original predicate/configuration/source bindings; condition_record_id and frozen_condition_record_id refer to the same record. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.frozen; ST.setresults | TX.set | AT-NR-073: Record absence/content mismatch rolls back MATCHED/handoff; configuration changes cannot alter an existing frozen condition. | G-B5B | R028, R051 |
| NR-074 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L17 | Commit final MATCHED, consumed trigger events, decision_cycle_id, set_result_id, producer references, frozen record and MARKET_HANDOFF/outbox together. No opportunity cycle is fabricated before MATCHED. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B | ST.setevents; ST.setresults; ST.frozen; ST.transport | TX.set | AT-NR-074: Crash at every write leaves all or none; duplicate input gives same cycle/result/record/handoff; conflicting content is retained. | G-B5B | R028, R035, R037 |
| NR-075 | `docs/trading-methodology/methodology/SET.md` — **15. Fresh formation versus pending-order monitoring**, L5220–L5400 | Govern pending signal lifetime, scope changes, outages, zero/partial/full fill and no-repricing through the frozen lifecycle boundaries; scope CLOSE and a new opportunity do not invalidate accepted pending entries. | Set | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B, B6 | ST.setevents; ST.monitor | TX.set; TX.monitor | AT-NR-075: Outage/recovery and scope CLOSE stop unfinished formation as defined but retain original accepted-entry monitor until terminal evidence. | G-B5B; G-B6 | R051 |
| NR-076 | `docs/trading-methodology/methodology/SET.md` — **12A. Canonical pending-validity reducer — F-013**, L4935–L5008 | F-013 activates only from authoritative ORDER_PLACED return with exact cycle/result/tranche/original accepted client/native entry and frozen record. Use existing LifecycleSetSyncStore, no second return mechanism. | Set consumes Lifecycle return | MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. | B6, B9 | ST.sync; ST.monitor; ST.frozen | TX.placement; TX.monitor | AT-NR-076: Handoff/grant/spec/create intent alone cannot activate; delayed placement cannot resurrect terminal monitor; wrong original entry is quarantined. | G-B6; G-B9 | R022, R051 |
| NR-077 | `docs/trading-methodology/methodology/SET.md` — **Canonical outcome precedence**, L5009–L5077 | Evaluate frozen numeric predicates with their pinned policy and full four-outcome reducer: terminal first; invalid activation/record unavailable; valid TRUE precedes another unavailable predicate; required unavailable/invalid condition follows; all FALSE means VALID. | Set | MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. | B6 | ST.monitor; ST.frozen | TX.monitor | AT-NR-077: Every outcome and pairwise precedence, especially TRUE+unavailable, terminal+TRUE, invalid activation+TRUE and FALSE vs missing evidence. | G-B6 | R051 |
| NR-078 | `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md` — **INVALIDATION: existing factual semantics**, L91–L141 | INVALIDATION retains exact frozen record/condition/evidence_digest and authoritative original TRUE effective invalidated_at, not callback time; it requests only original unfilled remainder reconciliation. | Set | MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. | B6 | ST.monitor; ST.cancel | TX.monitor | AT-NR-078: Same evaluation reuses signal; changing reason/time/condition/content conflicts; no signal from full-Set rematch, TTL, new opportunity or filled exposure. | G-B6 | R051, R055 |
| NR-079 | `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md` — **Requirement identity and atomic persistence**, L142–L187 | Acquire-or-join sticky unavailable requirement by original accepted-entry semantic key; unavailable_requirement_id equals signal_id. Preserve first time/reason/content and optional trustworthy record presence. | Set | MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. | B6 | ST.monitor; ST.cancel | TX.monitor | AT-NR-079: Partial-fill quantity/revision changes, further failures and recovery retain same ID/first primary reason/time; no remint/reclassification/withdrawal. | G-B6 | R051, R055 |
| NR-080 | `docs/trading-methodology/methodology/SET.md` — **Signal and unavailable handling**, L5078–L5165 | Persist unresolved original source/event transition before exact target binding, never guess a target. Later authoritative linkage preserves initial transition/time; terminal evidence ends applicability, not market recovery or signal ack. | Set | MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. | B6 | ST.monitor; ST.cancel | TX.monitor | AT-NR-080: Restart unbound requirement, two potentially matching entries, delayed exact linkage and terminal race; no guessed envelope. | G-B6 | R051 |
| NR-081 | `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md` — **Reconcile-first receipt and execution**, L188–L269 | Lifecycle receives both causes as conditional reconcile-first requests; only current positive unfilled remainder proof authorizes native cancel. Both causes join the same existing original-entry cancel intent. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.cancel; ST.reconcile; ST.sync | TX.cancel | AT-NR-081: Partial fill/cancel race, unavailable state, already terminal, duplicate causes and positive remainder; never cancel/close filled exposure. | G-B9 | R044, R051 |
| NR-082 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L45 | First evaluation pins one immutable MARKET_HANDOFF and Position configuration with initial position_decision_id; the later grant cannot select a newer handoff/configuration or recreate the initial decision. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.config; ST.position | TX.opportunity | AT-NR-082: Concurrent/restarted initial evaluations reuse exact pin/decision; same cycle changed handoff or config conflicts. | G-B7A | R014, R025, R038 |
| NR-083 | `docs/trading-methodology/business-contracts/APPROVE_REJECT.md` — **Two-stage meaning on one existing boundary**, L6–L44 | Initial OPPORTUNITY_DECISION performs Entry/SL/TP feasibility/geometry and enabled gross R:R. Post-grant construction gates remain NOT_YET_EVALUATED; initial APPROVE creates no grant/plan/tranche/spec. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-083: Initial APPROVE and REJECT exact stage shapes; no successful IDs, completed net edge or economics PASS on initial stage. | G-B7A | R025, R038, R039, R040, R041 |
| NR-084 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **1B. Position Rules configuration selection and immutable binding**, L75–L241 | Validate owner boundaries, frozen configuration, received venue/market identities and typed missing/invalid facts. Position has no API edge and no native order, close or Portfolio allocation authority. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A, B7B | ST.config; ST.position | TX.opportunity; TX.construction | AT-NR-084: No direct API fallback, missing config/market fields fail closed, wrong identity precedes unavailable substitute. | G-B7A; G-B7B | R017, R024, R025 |
| NR-085 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **Part II — Dynamic Entry Methodology**, L2072–L2674 | F-008 selects Entry from producer-bound eligible references using exact family/role/hierarchy, side, ties, ATR distance and unavailable rules. Retain selected reference and raw selection evidence. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position; ST.config | TX.opportunity | AT-NR-085: Both sides, equal-price distinct IDs, tie ranking, preferred/required/none cases, too shallow/deep and missing ATR/reference preflight. | G-B7A | R038 |
| NR-086 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **30. Tick rounding**, L2675–L3247 | Apply F-008 directional tick rounding and post-round eligibility exactly; preserve LIMIT+POST_ONLY mechanics. No chase, fallback market order, arbitrary offset, repricing or downstream reference reselection. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-086: Tick boundary changes distance/geometry outcome; reject failed post-round case rather than repair; grant replay keeps original Entry. | G-B7A | R038 |
| NR-087 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **Part III — Dynamic Stop Loss Methodology**, L3248–L4252 | F-006 LONG dynamic stop uses the same selected Entry, frozen references/configuration/ATR, prescribed candidate and buffer/risk sequence and directional rounding. F-007 is the separate SHORT mirror, not a side flip heuristic. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-087: Independent LONG/SHORT oracle vectors across ties, missing anchors/ATR, risk bounds and rounding; retain failure precedence without trying a new candidate. | G-B7A | R039 |
| NR-088 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **9. Fixed Stop Loss semantics**, L274–L368<br>`docs/trading-methodology/methodology/POSITION_RULES.md` — **14. Deterministic dependency order**, L465–L548 | F-009 dispatches FIXED versus DYNAMIC stop exactly; FIXED follows its own formula/rounding, DYNAMIC consumes the already selected usable F-006/F-007 branch unchanged. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-088: Both modes/sides, invalid mode, unavailable selected branch and geometry failure; no mode fallback or hidden second dynamic evaluation. | G-B7A | R040 |
| NR-089 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **Part IV — Dynamic Take Profit Methodology**, L4253–L4953 | F-010 Dynamic Take Profit follows the full frozen favorable-reference hierarchy and sequential candidate traversal with fixed ties/distances/failure rules; no TP derived by repairing an SL/risk-reward failure. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-089: Candidate sequence including too-close/too-far/missing input and next-candidate rules; both sides and required-reference precedence. | G-B7A | R041 |
| NR-090 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **29. Tick rounding**, L4954–L5489 | Apply TP directional rounding and post-round minimum/maximum/geometry checks; planned economics remains separate. No strategic partial TP, chase or invented fallback reference. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A | ST.position | TX.opportunity | AT-NR-090: Exactly-on-tick and just-off-tick bounds, crossed Entry/Stop/TP and failure after rounding; no later economic gate changes TP. | G-B7A | R041 |
| NR-091 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **23. Gross risk distance**, L912–L1037 | Initial geometry/risk/reward/gross R:R use the frozen LONG/SHORT definitions and exact selected prices; signed planned profit and distance denominators are validated before enabled gross gate. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A, B7B | ST.position; ST.construction | TX.opportunity; TX.construction | AT-NR-091: Zero/wrong-side distance, exact threshold equality, disabled gate with still-required geometry, and report-only ratio collision. | G-B7A; G-B7B | R020, R042 |
| NR-092 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L18–L45 | Post-grant construction consumes the exact original approved opportunity and immutable grant/facts. Only successful final construction creates plan/tranche/spec; failure retains an immutable unsuccessful outcome without those IDs. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.grants; ST.position; ST.construction | TX.construction | AT-NR-092: Grant before approval, wrong grant/decision, duplicate grant, reject outcome and restart after initial decision with changed active settings. | G-B7B | R019, R024, R025 |
| NR-093 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **17. Requested capital per tranche**, L576–L836<br>`docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **4. Position final construction and proof of no overcommit**, L53–L61 | F-011 retains prescribed C→T→Q→N→A→H sequence, step floor and final exchange minimum/maximum gates. Exact A is not quantized H; no reprice/resize/clamp to turn failure into success. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.construction; ST.spec | TX.construction | AT-NR-093: Smallest step/minimum notional/maximum qty, nonterminating N/leverage, Q=0, A<=C and H<=C independent checks. | G-B7B | R019 |
| NR-094 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **22. Leverage**, L837–L911 | Leverage/product and governed accounting/settlement currency admissibility are explicit construction dependencies; no implicit FX or substitution of instrument constraints. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.construction; ST.spec | TX.construction | AT-NR-094: Invalid leverage/product, missing applicable metadata or foreign accounting currency reject without constructing a trade. | G-B7B | R019, R042 |
| NR-095 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **28. Fee facts**, L1038–L1141 | F-012 uses signed factual fractional maker/taker rates with frozen schedule/effective/source applicability. Entry fee uses N; TP/SL fees use respective exit price×Q, preserving zero/rebates. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.construction | TX.construction | AT-NR-095: Negative/zero rates, wrong units, provenance mismatch, missing rates and incorrect Entry-notional reuse at TP/SL fail appropriate local branch. | G-B7B | R020, R042 |
| NR-096 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **32. Funding**, L1142–L1370 | F-012 excludes future funding and unapproved simulated costs from baseline planned edge. Additional baseline TP cost set is empty; an asserted applicable undefined cost is COST_POLICY_UNAVAILABLE, not zero. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.construction | TX.construction | AT-NR-096: Funding/spread/slippage cannot enter baseline gate; asserted extra applicable cost blocks; net edge denominator is actual N, never C/H/T. | G-B7B | R020, R042 |
| NR-097 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **39. Minimum Risk / Reward hard gate**, L1332–L1632 | Apply exact enabled minimum gross R:R and minimum net edge with certified status/reason precedence, dependency and no-repair rules; report fields cannot determine a gate. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A, B7B | ST.position; ST.construction | TX.opportunity; TX.construction | AT-NR-097: All enable/disable combinations, threshold equality, simultaneous identity/missing/malformed failures and no geometry repair. | G-B7A; G-B7B | R020, R042 |
| NR-098 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L18–L45 | Successful construction result, immutable ORDER_SPEC and two outboxes—CONSTRUCTED on APPROVE_REJECT to Portfolio and ORDER_SPEC to Lifecycle—commit in one existing PostgreSQL UoW. | Position | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B | ST.construction; ST.spec; ST.transport | TX.construction | AT-NR-098: Failure at either record or either outbox rolls back all success state; duplicate outcome returns original full envelope. | G-B7B | R019, R024, R025 |
| NR-099 | `docs/trading-methodology/business-contracts/ORDER_SPEC.md` — **Immutable post-grant construction**, L6–L101<br>`docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P14 — Exact construction confirmation and multi-symbol factual cardinality**, L302–L312 | ORDER_SPEC is immutable with versioned full-envelope digest, pinned configuration and exact construction values. Duplicate scalar equality is independently verified; no self-referential digest or caller-supplied replacement economics. | Position producer; Lifecycle validates | MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. | B7B, B9 | ST.spec; ST.authorization | TX.construction; TX.native | AT-NR-099: Change any ID, Entry/Q/N/leverage/H/gate scalar with a supplied digest; confirm independent equality check rejects. | G-B7B; G-B9 | R024 |
| NR-100 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **2. Core lifecycle identity**, L172–L306 | Lifecycle starts only by exact ORDER_SPEC+SUBMIT_AUTHORIZED join with all IDs/digest and held H, independent of delivery order. No grant-only, spec-only or expired-age inference gives native authority. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.spec; ST.authorization; ST.submission | TX.native | AT-NR-100: Spec first/auth first/duplicate, wrong construction or digest and missing hold; no call before complete authoritative join. | G-B9 | R023, R031, R044 |
| NR-101 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P2 — Immutable grants and current hard execution compatibility**, L46–L62 | Before native create obtain current coherent non-market hard execution facts; compare immutable spec against current product/profile/tick/step/minimum/maximum/leverage/mode restrictions. Revision age alone is not incompatibility; fee refresh is not hard re-economics. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.nativefacts; ST.submission | TX.native | AT-NR-101: Compatible newer opaque revision passes; incompatible definitive no-create differs from unavailable RECONCILING; no repricing or lexical revision ordering. | G-B9 | R031, R044 |
| NR-102 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **4. Technical submission boundary**, L307–L419 | Persist native intent and stable client order identity before external create; use same identity through retries and bind request/profile evidence. External call is outside—not pseudo-atomic with—the database transaction. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.submission; ST.nativefacts | TX.native | AT-NR-102: Crash before call, after call before ack, request retry and duplicate dispatcher claim cannot create a second native order. | G-B9 | R022, R031, R044 |
| NR-103 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **6.1 ACCEPTED**, L420–L521 | Persist authoritative placement/rejection/ambiguous-create facts and accepted-time provenance. Lost ack means reconcile exact client/native IDs, not mint new create; selected acceptance time remains immutable under explicit resolution. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.submission; ST.acceptance; ST.reconcile | TX.acceptance; TX.placement | AT-NR-103: Lost ack, reordered acceptance evidence, duplicate order and contradictory accepted time; no callback timestamp used as accepted origin. | G-B9 | R022, R044 |
| NR-104 | `docs/trading-methodology/business-contracts/ORDER_PLACED.md` — **Purpose**, L7–L135 | Publish actual ORDER_PLACED and governed ENTRY_LIFECYCLE_EVENT return variants to Set using existing LifecycleSetSyncStore, with original cycle/result/tranche/client/native lineage and terminal revision/timestamps. | Lifecycle produces; Set consumes | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B6 | ST.sync; ST.monitor | TX.placement; TX.monitor | AT-NR-104: Actual placement activates exact frozen monitor; terminal-first replay never reactivates; all return variants reach Set, not Lifecycle as consumer. | G-B9; G-B6 | R022, R051 |
| NR-105 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **7. Canonical lifecycle states**, L522–L702 | Implement pending/partial/full exposure states and protection duties from factual executions, not exchange status text alone. Filled quantity does not itself establish financial CLOSED. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.submission; ST.reconcile; ST.protection | TX.acceptance; TX.protection | AT-NR-105: Partial and full fill before/after status, duplicate execution and absent ack converge without repeated quantity/economic effect. | G-B9 | R031, R044 |
| NR-106 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **11. Cancel inputs**, L703–L876 | Native cancel operates on current authoritative remainder proof; cancel/fill race reconciles executions and terminality. Zero-fill/partial-fill terminal outcomes remain distinct, no fill erasure or new-entry retry shortcut. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.cancel; ST.reconcile; ST.sync | TX.cancel; TX.acceptance | AT-NR-106: Cancel accepted but racing fill, ambiguous cancel and terminal remainder; retain/protect filled exposure and signal proper return to Set. | G-B9 | R031, R044, R051 |
| NR-107 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **15. No replace / no reprice baseline**, L877–L902 | Lifecycle never reprices/reselects Entry/SL/TP, replaces planned execution mechanics or applies hidden strategy. Validity of original immutable spec is checked, not repaired. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.spec; ST.submission | TX.native | AT-NR-107: Post-only reject or changed hard fact never causes market fallback/chase or replacement spec; only governed no-create/reconcile outcome. | G-B9 | R044 |
| NR-108 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **16. Attached TP / SL protection**, L903–L982 | Install/track owned native protection for actual fill quantities using approved mechanics and child provenance. Separate historical child identity from current proof that live protection exists. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.protection; ST.close; ST.nativefacts | TX.protection | AT-NR-108: Partial-fill protection quantities, missing child/provenance and competing child authority; native profile remains independently gated. | G-B9 | R031, R044 |
| NR-109 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T03 — Current live-protection proof is a separate derived object**, L543–L569 | Current protection proof binds exact query/native scope, source generation/as-of/completeness and expected owned children. New COMPLETE omission invalidates live verification atomically; historical mappings remain. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.protection; ST.nativefacts | TX.preflight; TX.protection | AT-NR-109: New complete empty query, omitted TP/SL, older replay, same-generation conflicting membership and partial response; no blind replacement/cancel from absence. | G-B9 | R031, R044 |
| NR-110 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P5 — Atomic acquire-or-join and reduction authority**, L83–L113 | Reuse one acquire-or-join close intent per tranche, persisted revision/CAS, cause records and stable child identity. Reconcile competing/remainder authorities; allocate current exact residual reduction budget before native child effect. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.close; ST.reconcile; ST.nativefacts | TX.close; TX.native | AT-NR-110: Simultaneous TP/SL/manual causes, lost ack child, racing fill and retry join same intent; negative residual is incident, not clamp. | G-B9 | R031, R044 |
| NR-111 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **19. Close conditions**, L983–L1092 | Implement existing close/current-proof states, event idempotency and ordering; one active child authority and authoritative executions determine exit classification, not first cause or transport arrival. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.close; ST.reconcile | TX.close | AT-NR-111: Concurrent causes and uncertain child cannot authorize overlapping reduction; exact source chronology controls final classification. | G-B9 | R031, R044 |
| NR-112 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **26. Reconciliation**, L1093–L1207 | Restart/reconciliation restores accepted facts, intents, revisions, tombstones and current authority before processing new deliveries; outage cannot reset identities or allow stale source inference. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.reconcile; ST.close; ST.submission | TX.owner | AT-NR-112: Hydrate each active/terminal/ambiguous state; same IDs retained across process crash and factual backfill with reordered source delivery. | G-B9 | R031, R044 |
| NR-113 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **U04 — Rejection is not authority to erase execution**, L672–L678 | Zero-fill rejection/no-create release requires bound terminal proof, no actual executions and no ambiguous authority. Confirmed execution dominates contradictory rejection; later execution after proven zero-fill is factual liability/reconciliation, not resubmission. | Lifecycle; Portfolio receives factual consequence | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B8C | ST.submission; ST.reconcile; ST.portfolio | TX.acceptance | AT-NR-113: Reject without proof retains resources; eventual complete no-execution proof releases once; later attributable fill restores liability/slot without reopening CREATE. | G-B9; G-B8C | R043, R044 |
| NR-114 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P9 — Native observation and complete attribution resolution**, L222–L242 | Unattributed native observations stay native-scoped with separate revisions/tombstones; explicit complete attribution manifest governs logical projection, not symbol/time inference or debit to an arbitrary tranche. | Lifecycle attribution; Portfolio projection | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.attribution; ST.portfolio | TX.partition | AT-NR-114: Observation/manifest/allocation permutations, unresolved native scope and provisional tombstone; manifest is not a second quantity effect. | G-B9 | R021, R031, R044 |
| NR-115 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T04 — Prove source conservation before native quantity mutation**, L570–L622 | Stage pre-manifest allocations with zero effect. Lifecycle proves positive disjoint gap-free half-open source slices and exact source/observed total conservation before applying named allocations; receipts globally bind source/membership/digest. | Lifecycle; Portfolio separately verifies manifest projection | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.attribution; ST.reconcile | TX.partition | AT-NR-115: Overlapping/duplicate-source claims, missing member, aliases outside manifest, source overconsumption, crash between quantity and receipt, manifest-first/allocation-first convergence. | G-B9 | R031, R044 |
| NR-116 | `docs/trading-methodology/business-contracts/ORDER_EVENT.md` — **Semantic synchronization (contract version unchanged)**, L386–L425 | Logical lifecycle, native scope, attribution resolution and incident revisions are separate histories. Same-known revision content is checked before stale/terminal suppression; no global high-watermark shortcuts. | Lifecycle producer; Portfolio consumer | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B10 | ST.attribution; ST.incidents; ST.acceptance | TX.preflight; TX.partition; TX.incident | AT-NR-116: Older previously accepted conflicting revision blocks; unseen older evidence follows own scope; identical replay never reopens a terminal effect. | G-B9; G-B10 | R021, R031 |
| NR-117 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **30. Dedicated trading account / subaccount baseline**, L1186–L1207 | Preserve dedicated managed-account assumptions and explicit external/native reconciliation authority; no unlinked native fact is assigned to a strategy tranche or repaired by a compensating trade. | Lifecycle; Portfolio scope | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.attribution; ST.portfolio | TX.partition | AT-NR-117: Unattributed/manual external change creates governed blocked scope/reconciliation; no fabricated lineage, order or accounting result. | G-B9 | R031, R044 |
| NR-118 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P7 — Complete Lifecycle financial evidence**, L137–L192 | Lifecycle fetches factual financial components directly. Complete source coverage requires intervals, no missing ranges, exhausted pagination, watermark/cutoff and source finality or proven non-applicability; empty/zero is not proof. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.financial; ST.coverage | TX.facts; TX.final | AT-NR-118: Missing fee/funding/cost component, partial pages, inadequate watermark, unsupported empty certificate and timeout cannot finalize. | G-B10 | R047 |
| NR-119 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` — **2A. One governed accounting unit; unsupported currency blocks FINAL**, L31–L44 | Required source currency must equal the inherited governed accounting/settlement currency. Retain foreign native evidence and block finality; never convert, net away, omit or relabel foreign sources. | Portfolio pins; Position/Lifecycle enforce | PARTIAL: grant issue/binding store exists; canonical owner gates incomplete [E35–E36,E47]. | B8B, B7B, B10 | ST.grants; ST.spec; ST.financial | TX.grant; TX.construction; TX.final | AT-NR-119: Foreign debit/credit even net-zero blocks; settlement mark used for funding weights is not FX authority. | G-B8B; G-B7B; G-B10 | R045, R047 |
| NR-120 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **32. Funding attribution**, L1208–L1338 | A-004 uses complete unique signed source, effective-time eligible tranches/quantities, common settlement basis, exact rational weights, q=1e-18 toward-zero bases and entire signed residue to largest absolute raw allocation, lexical tranche-ID tie. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.funding; ST.financial; ST.coverage | TX.funding | AT-NR-120: Positive/negative/zero sources, quantum representability, lexical ties and largest-raw vs largest-fractional distinction; exact signed conservation. | G-B10 | R047 |
| NR-121 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **32. Funding attribution**, L1232–L1338 | Funding eligibility/weights bind authoritative effective-time execution/cashflow order and persisted basis; ambiguous material ties/unmatched amount remain RECONCILING. Restore source/coverage history and algorithm version on restart. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.funding; ST.coverage | TX.funding | AT-NR-121: Current-position substitution, missing basis, same-time material tie, duplicate alias and changed source cannot create allocation; immutable replay same bytes. | G-B10 | R047 |
| NR-122 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P12 — Proven execution lineage, then non-funding cashflow allocation**, L267–L291 | Non-funding EXEC_CASHFLOW_ALLOC_V1 uses its factual source_amount_quantum and proven execution-quantity×price weights, not funding q18. Truncate toward zero and assign full signed residue by frozen largest-raw/tie rule. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.financial; ST.attribution | TX.cashflow | AT-NR-122: Source quantum other than q18, negative rebates, multi-execution missing decomposition, signed conservation and no source-rounding. | G-B10 | R047 |
| NR-123 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **U01 — Current accepted applicable financial source set**, L640–L651 | Finality uses the current complete accepted applicable source set, source revision, attribution and component coverage; accepted additional applicable source cannot be excluded to force totals to reconcile. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.financial; ST.coverage | TX.cashflow; TX.final | AT-NR-123: New source after earlier allocation blocks incomplete finality; both orders converge after complete allocations; same-revision changed source proof conflicts. | G-B10 | R047 |
| NR-124 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P13 — Economic execution chronology and permanent zero**, L292–L301 | A-002 accounting_effective_at is the permanent final closing execution on authoritative chronology, not receipt order or temporary zero exposure. Complete accepted execution prefix must not be negative. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.reconcile; ST.final | TX.final | AT-NR-124: Temporary flat-then-refill, simultaneous executions with material unresolved order, callback reorder and contradictory late execution; no lexical-ID chronology. | G-B10 | R047 |
| NR-125 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **33. Fee attribution**, L1343–L1380 | A-002 assembles one canonical immutable FINAL from complete factual executions, signed fees/rebates, A-004 funding and permitted costs in governed currency; planned Entry/rates are not factual final amounts. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.final; ST.financial; ST.funding | TX.final | AT-NR-125: Exact factual net with rebates/funding, incomplete component, duplicate cashflow and fake planned-rate result; no mutable replacement FINAL. | G-B10 | R047 |
| NR-126 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T02 — Revision-bound financial FINAL on every active path**, L504–L542 | Freeze FINAL proof with current execution, source-set, coverage and allocation revisions/digests and economic-day basis at commit. Component FINAL is not full-tranche FINAL; explicit durable parent links govern later incidents. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.final; ST.coverage; ST.financial | TX.final; TX.incident | AT-NR-126: Concurrent source/coverage/attribution change before commit blocks stale proof; later corroboration does not replace committed basis; linked component challenge emits parent incident. | G-B10 | R047 |
| NR-127 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P6 — CLOSED is one unified predicate composed of six required conditions and explicit retained commitment**, L114–L136 | S-004 CLOSED requires all six predicates: zero logical exposure; terminal entry remainder; all owned protective/exit children terminal/disabled; resolved close intent; complete financial finality; no competing execution authority. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.final; ST.close; ST.protection; ST.reconcile | TX.final | AT-NR-127: Individually falsify each predicate while others pass; physical flatness/closed_at alone and partial-close legacy result cannot close. | G-B10 | R047 |
| NR-128 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P8 — Economic time, operational time and accounting day**, L193–L221 | In one Lifecycle terminal transaction freeze immutable FINAL, resolve close intent, establish CLOSED/terminalized_at and append final ORDER_EVENT. Portfolio receipt is a different transaction/owner. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.final; ST.close; ST.transport | TX.final | AT-NR-128: Crash after each terminal write/outbox attempt commits all or none; one immutable result per tranche and no direct Portfolio receipt creation. | G-B10 | R047 |
| NR-129 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P8 — Economic time, operational time and accounting day**, L193–L221 | Persist distinct accounting_effective_at, operational closed_at, financial finalized_at, terminalized_at and Portfolio first delivered_at. ACCOUNTING_DAY_V1 uses Asia/Jerusalem half-open local-day boundaries, not ordinary Set UTC calendars. | Lifecycle timestamps; Portfolio receipt/day | PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. | B8A, B10 | ST.day; ST.final; ST.receipts | TX.day; TX.final; TX.receipt | AT-NR-129: DST-length day, exact midnight and late cleanup/receipt do not move historical economic day; no timezone reconstructed from current settings. | G-B8A; G-B10 | R045, R047 |
| NR-130 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T01 — Separate terminal result and post-final integrity incident**, L432–L503 | After FINAL retain challenges/quarantine and publish separate parent-linked POST_FINAL_INTEGRITY incident identities/revisions on ORDER_EVENT; never mutate FINAL/day/closed proof or erase already applied money. | Lifecycle publishes; Portfolio blocks eligibility | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.incidents; ST.final; ST.frontier | TX.incident; TX.frontier | AT-NR-130: New source, changed content, source-set/coverage challenge and both receipt orders; no replacement result or inverse financial posting. | G-B10 | R047 |
| NR-131 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **POST_FINAL_INTEGRITY incident_class taxonomy**, L824–L835 | Use frozen POST_FINAL_INTEGRITY classes and correct factual-execution versus proof/ownership challenge classification; retain truthful nullable scope/provenance rather than manufactured lineage. | Lifecycle; Portfolio consumer | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.incidents | TX.incident | AT-NR-131: Each prescribed incident class, missing truthful lineage, resolved/historical contradiction and raw-only challenge produce correct independent incident dedupe. | G-B10 | R047 |
| NR-132 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T01 — Separate terminal result and post-final integrity incident**, L459–L503 | Portfolio receipt and every current exposure eligibility decision merge all committed existing-edge messages through the head observed under the same scoped serializable fence. Gaps/known unresolved incidents withhold first application. | Portfolio; same-edge transport | PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. | B8C, B10 | ST.frontier; ST.receipts; ST.incidents | TX.frontier; TX.receipt; TX.hold | AT-NR-132: Incident commits first: no receipt/release; receipt first: immutable once-only posting, block future eligibility; test stale/same-conflict revisions, crash/retry. | G-B8C; G-B10 | R043, R047 |
| NR-133 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **13.1 Zero-fill cancellation**, L782–L852 | Keep zero-fill terminal cancellation and definitive no-create terminal resource release separate from filled-tranche A-002/S-004. No fabricated FINAL for an attempt with no execution. | Lifecycle; Portfolio release consumer | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B10 | ST.submission; ST.portfolio; ST.acceptance | TX.acceptance | AT-NR-133: Proven no-create/zero-fill releases only its resources once; missing proof retains; nonzero fee/cashflow challenge follows governed reconciliation rather than invented filled result. | G-B9; G-B10 | R043, R047 |
| NR-134 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T02 — Revision-bound financial FINAL on every active path**, L504–L542 | Full-tranche immutable revision-bound FINAL and the fenced Portfolio receipt cannot be replaced by mutable financial state, component or partial-close results, or unqualified day totals. The required finality and receipt predicates remain authoritative regardless of storage representation. | Lifecycle; Portfolio | LEGACY_ONLY: FuturesAccountingStore and DailyLossStore are SQLite; canonical equivalents not established [E48–E51]. | B10, B13 | ST.legacy; ST.final; ST.receipts | TX.final; TX.receipt | AT-NR-134: No SQLite+PostgreSQL dual authority or pseudo-atomic writes; any reused pure calculation passes independent full semantic equivalence tests. | G-B10; G-B13 | R045, R046, R047 |
| NR-135 | `docs/trading-methodology/IDENTIFIER_LINEAGE.md` — **Identifier lineage — v1.2.15**, L1–L82 | Every behavior checkpoint commits stable immutable identities/configuration/evidence with effects and outboxes; duplicate, conflict, crash/restart and terminal dominance are local acceptance obligations, not deferred hardening. | All owners | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B, B6, B7A, B8B, B7B, B8C, B9, B10 | ST.transport; all owner state | TX.owner | AT-NR-135: Execute RP-LOCAL suite against each owner with real PostgreSQL transactions and pinned historical inputs, including outbox rollback cutpoints. | G-B5B; G-B6; G-B7A; G-B8B; G-B7B; G-B8C; G-B9; G-B10 | R013, R043, R044 |
| NR-136 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T01 — Separate terminal result and post-final integrity incident**, L432–L622 | Integrated replay must preserve same owner outcomes, exact money/source quantities, finality and frontier ordering across interleaved delivery and process restart; existing local correctness is prerequisite. | All owners | Infrastructure tests exist; full owner replay not proven by supplied evidence [E23,E31–E32; audit §§28,32]. | B11 | All canonical state | All TX boundaries | AT-NR-136: Deterministic full replay plus adversarial hold/cancel/fill/finality/incident schedules; reopen faulty owner checkpoint, do not weaken expected outcomes. | G-B11 | R049 |
| NR-137 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L45 | Route each business message only to its governed owner and enforce stage/evidence prerequisites. A technical dispatcher cannot create an unapproved business effect or bypass owner/contract rules; unknown or incomplete paths remain fail-closed. | Technical runtime / four owners | Canonical worker intentionally blocks owner messages; launcher fences already exist [E23–E25]. | B12 | ST.transport | TX.owner | AT-NR-137: Unknown consumer/type, missing handler/readiness, transaction failure and poisoned envelope leave safe state; approved routes preserve owner boundaries. | G-B12 | R007, R008, R032, R050 |
| NR-138 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — **Order Spec gate-state validation**, L1920–L1953 | Native side effects require independently proven current hard/native profile and execution invariants in addition to complete owner dispatch. Dispatcher readiness alone is not permission to create exposure. | Lifecycle; runtime gate | Canonical worker intentionally blocks owner messages; launcher fences already exist [E23–E25]. | B12 | ST.nativefacts; ST.transport | TX.native | AT-NR-138: All planned/local gates pass but native profile absent: dispatcher may diagnose/reconcile while exposure creation stays disabled. | G-B12 | R007, R032, R050 |
| NR-139 | `docs/trading-methodology/methodology/SET.md` — **16. Validation frequency**, L5250–L5312 | Process scheduling may deliver only frozen evaluation/reconciliation duties and original freshness/deadline behavior; it must not invent trading expiry, periodic cancellation or a second canonical worker. | Technical runtime; owner evaluates | Canonical worker intentionally blocks owner messages; launcher fences already exist [E23–E25]. | B12 | ST.transport; ST.setevents | TX.owner | AT-NR-139: Clock/restart fixtures preserve original evaluation schedules; no order/grant TTL or auto-close from scheduler role. | G-B12 | R008, R009 |
| NR-140 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P1 — Topology and approval/construction sequence**, L6–L45<br>`docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T01 — Separate terminal result and post-final integrity incident**, L432–L897 | The integrated production/consumption paths preserve the exact four-owner protocol and its governed evidence/terminal controls across normal, unavailable, replay and conflict paths; downstream bypass cannot alter the accepted owner outcome. | All owners / independent test review | Existing isolation/tests reusable; full canonical execution not proven [E23–E25,E52; audit §§31–34]. | B13 | All canonical state | All TX boundaries | AT-NR-140: Run V-FULL suite in §12 with all local requirements and actual dispatcher; each missing runtime/native/DB evidence remains explicitly non-passing. | G-B13 | R049 |
| NR-141 | `docs/trading-methodology/methodology/POSITION_RULES.md` — **8. User Position Rules configuration**, L242–L548 | Preserve source-defined user switches, FIXED/DYNAMIC stop/take modes and trade-construction operation order. Supporting fixed-mode rules are not additional certified objects and cannot be dropped merely because the object list names Dynamic TP. | Position | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A, B7B | ST.position; ST.construction | TX.opportunity; TX.construction | AT-NR-141: Every supported mode combination and disabled-gate branch follows frozen geometry/dependency rules; unsupported mode cannot select a fallback. | G-B7A; G-B7B | R038, R039, R040, R041, R042 |
| NR-142 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P3 — POST_ONLY belongs to the exchange**, L63–L82 | Exchange owns actual POST_ONLY admissibility. Position fixes intended mechanics and producer-bound thesis references; Lifecycle submits immutable approved spec or reconciles authoritative refusal, without synthetic market analysis. | Position; Lifecycle | MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. | B7A, B9 | ST.spec; ST.submission | TX.opportunity; TX.native | AT-NR-142: Marketable-at-exchange reject never causes replacement Entry/type; downstream cannot silently rebind a configured thesis role. | G-B7A; G-B9 | R038, R044 |
| NR-143 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Monotonic native facts and acceptance integrity — P10**, L321–L328<br>`docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **S02 — Proven mutable enrichment is field-specific**, L383–L394 | Native field merges retain proven immutable identity and independently ordered mutable fields. Unknown/unproven fields may receive same-time authoritative enrichment; another field update cannot advance this field’s source version. | Lifecycle factual acceptance | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B9 | ST.nativefacts; ST.acceptance | TX.preflight; TX.facts | AT-NR-143: Proven/unproven same-time enrichment, equal-version contradiction, cumulative-fill regression and terminal resurrection; acceptance-integrity block independent of timestamp. | G-B3; G-B9 | R031, R044 |
| NR-144 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P15 — Native-scope no-reduction observation and clearance**, L343–L352 | Native-scope observations without reduction use the governed explicit observation/clearance path and durable tombstones; no fabricated allocation, execution, cashflow or tranche is necessary to clear a proven non-reduction condition. | Lifecycle; Portfolio scope consumer | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.attribution; ST.portfolio | TX.partition | AT-NR-144: No-reduction observation/resolution before/after arrival, known content conflict after clearance and unrelated unresolved scope; no invented quantity effect. | G-B9 | R021, R031 |
| NR-145 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **S04 — Historical assembly is evidence-bound eligibility**, L395–L402 | Current Set analytical eligibility binds one immutable selection/snapshot/complete-page manifest/source-finality proof. Contradictory page/manifest/native record invalidates current eligibility but never rewrites already frozen handoff. | Set | PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. | B3, B5B | ST.facts; ST.setcalc; ST.setresults | TX.preflight; TX.facts; TX.set | AT-NR-145: Page outside manifest, incompatible complete manifests or mixed fixed snapshots block new analysis; original frozen handoff replay stays immutable. | G-B3; G-B5B | R027, R028 |
| NR-146 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **S05 — Global native quantity allocation identity**, L403–L410 | Native quantity allocation identity is global in its account/environment namespace with immutable observation/resolution/source/tranche/quantity binding; a fresh alias ID cannot move a bound source to another observation. | Lifecycle; Portfolio projection | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9 | ST.attribution | TX.partition | AT-NR-146: Same ID under different observation and new ID reusing prior source both quarantine; valid independent members still reconcile with safety block retained. | G-B9 | R031, R044 |
| NR-147 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **S06 — Factual execution-derived gross result**, L411–L418 | A-002 gross derives exact sums of attributable factual execution quantity×actual price for entries/exits and direction. A cost-basis checkpoint proves covered IDs/revision/cost and is reconstructible, never a planned-Entry synthetic fill. | Lifecycle | PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. | B10 | ST.financial; ST.reconcile; ST.final | TX.facts; TX.final | AT-NR-147: Later entry fills at different prices, checkpoint+incremental overlap, missing actual price and changed checkpoint digest; every execution contributes once. | G-B10 | R047 |
| NR-148 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **Revision-bound closure proof — P6 / P8 / P13**, L329–L342 | Current closure/permanent-zero/accounting-day proof binds execution, remainder/authority, children, coverage, close-intent and financial revisions with source certificates. Any relevant change invalidates dependent proof before terminal commit. | Lifecycle | PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. | B9, B10 | ST.close; ST.protection; ST.coverage; ST.final | TX.protection; TX.close; TX.final | AT-NR-148: Change each vector member between proof and commit; no cached bool or old COMPLETE certificate authorizes CLOSED; post-FINAL challenge becomes separate incident. | G-B9; G-B10 | R031, R047 |
| NR-149 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **P17 — Immutable configuration binding for started cycles and attempts**, L359–L368 | Started Set epochs, Position cycles and Portfolio authorized attempts retain owner-specific configuration identity/version/content digests; Portfolio attempt pins cooldown duration and late acceptance cannot read current settings. | Set; Position; Portfolio | MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. | B5B, B7A, B8C | ST.config; ST.scope; ST.holds | TX.set; TX.opportunity; TX.hold | AT-NR-149: Change live config between every stage/restart; started records retain original contents while genuinely new scope/attempt gets correct new binding. | G-B5B; G-B7A; G-B8C | R014, R043 |
| NR-150 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` — **T05 — Internal Set normalization is not an export operation**, L623–L635 | Set normalize_working and any normalize compatibility alias retain Q36 working semantics; serialization is a distinct allowed-wire export operation. Demo precision is not accepted canonical arithmetic without proof. | Set; shared numeric binding | PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. | B1, B5A | ST.setcalc | TX.setcalc | AT-NR-150: Equivalent calls return work values; serializer not used inside factor/score/veto; low-magnitude/near-threshold vectors detect accidental Q18 feedback. | G-B1; G-B5A | R015, R036 |
| NR-151 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` — §§51–53 L1540–L1591; §63 L1741–L1777; existing interpretation boundaries §§37–45 L1214–L1480 and NUMERIC_POLICY §§4–5/7 L53–L80/L90–L92 | Retain Portfolio internal ALLOWED/BLOCKED/UNAVAILABLE decisions, complete source-defined gate_result fields and every actually evaluated reason, including denials/unavailable outcomes; cover every §63 observation by the classified immutable record/history mapping in §6.2. Capture missing owner-local facts at their producing transition, distinguish C/H/never-held surplus from actual release, retain lifecycle-linked consumed/closed/reconciliation history, and derive exact read-only frequencies/utilization from retained evidence. No new gate, default reason precedence, reservation, owner, Research producer or duplicate capital ledger. | Portfolio; other owners retain only their already-owned authoritative inputs | PARTIAL: PortfolioStateStore revision history, CapitalGrantStore immutable issue payload and SubmitAuthorizationStore exist; complete denied/multi-reason and transition observation histories are absent. Exact existing/proposed separation in §6.2.1; source snapshot, not R4 self-check. | B8A foundation; B8B grant outcomes; B8C booking outcomes; B9 factual-return/Portfolio projections; B10 terminal/receipt/release integration; B11/B13 verification only; B14 independent audit | ST.portfolio; ST.grants; ST.holds; ST.authorization; ST.scope; ST.day; ST.cooldown; ST.receipts; ST.transport; ST.config; ST.facts; existing immutable construction work referenced by read-only audit view only | TX.scope; TX.day; TX.grant; TX.hold; TX.acceptance; TX.closeretention; TX.receipt; TX.facts; TX.partition only for an existing Portfolio event projection; TX.owner for owner-local recovery/capture; TX.frontier only when already required by the underlying event; exact membership §7.6 | AT-NR-151: all observations P01–P33 in §6.2.3 and cases 01–12 in §6.2.4; retain every evaluated reason, distinct unavailable/blocked, denials across restart, exact C/H/rounding evidence, duplicate/crash atomicity and history-derived utilization; real owner paths, not B12 infrastructure counters | G-B8A; G-B8B; G-B8C; G-B9; G-B10; G-B11/G-B13 verification; G-B14 audit; explicit local responsibilities §10.4 | NONE — newly mapped frozen obligation; audit-only AUD-P-01, not an R001–R060 alias |
| NR-152 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` — §43 L1774–L1830; §40 L1666–L1693; existing idempotency/order/reconciliation §§24–28 L1046–L1185 | Retain the complete Lifecycle §43 operational/audit observation history and support §40 visibility from authoritative owner records. Map every item by §6.3, including duplicate/out-of-order/recovery/manual observations, distinct authorization and terminal-publication cutpoints, sibling cleanup, close/fill races and factual monetary evidence. Economic idempotency is separate from once-per-captured-arrival diagnostic retention; retries reuse captured observation identity and never repeat economics or counts. No Research owner, new wire family, native authority or trading behavior. | Lifecycle; Portfolio projections remain separately owned under NR-151 | PARTIAL: LifecycleSubmissionStore retains selected latest cutpoints/counter, LifecycleSetSyncStore sync/outbox, LifecycleReconciliationStore history, LifecycleCloseAuthorityStore causes/children and LifecycleOrderEventStore events exist. Full observation history and some cutpoints are missing; §6.3.1 identifies extensions rather than fabricated existing fields. | B9 native/recovery/cancel/close observations; B10 financial/finality observations; B11/B13 verification only; B14 independent audit | ST.submission; ST.authorization; ST.sync; ST.nativefacts; ST.acceptance; ST.reconcile; ST.protection; ST.cancel; ST.close; ST.attribution; ST.financial; ST.coverage; ST.funding; ST.final; ST.incidents; ST.transport; no additional state family | TX.owner; TX.native; TX.acceptance; TX.placement; TX.protection; TX.cancel; TX.close; TX.facts; TX.cashflow; TX.funding; TX.final; existing TX.preflight/TX.partition/TX.incident when the accepted fact/challenge already requires them; exact membership §7.6 | AT-NR-152: all L01–L40 observations and §40 visibility in §6.3, cases 01–12, actual owner paths, immutable arrival identity/counting, exact cutpoints/quantities/factual finance and all crash/retry boundaries | G-B9; G-B10; G-B11/G-B13 verification; G-B14 audit; explicit local responsibilities §10.4 | NONE — newly mapped frozen obligation; audit-only AUD-L-01, not an R001–R060 alias |
| NR-153 | `docs/trading-methodology/methodology/POSITION_RULES.md` Part II §51 L3220–L3243; §50 L3205–L3216; original F-008 fields §47 L2960–L3025 and improvement §§21–22 L2473–L2507; `methodology/SET.md` reference age §§14–15 L3805–L3861 | Implement all 19 required Entry research-reporting items in §6.4.8, with exact owner lineage, explicit diagnostic cohorts/denominators, original raw/rounded improvement and canonical reference age, actual native/fill outcomes, FINAL-based distance-band expectancy and complete post-fill path evidence. Preserve explicit unavailability and pin every reporting convention not fixed by the source. Read-only output, no Entry/live threshold change or optimization. | Position owns Entry decision evidence; Set owns original context/reference family; Lifecycle owns native/execution/FINAL facts; Research owns only diagnostic dataset/report assembly, never those business facts | PARTIAL primitives, complete reports absent: existing F-008 source fields and R5 source retention; ResearchService, SQLite ResearchStore, research pins and limited historical cache exist; aggregate analytics is insufficient (§6.4.1) | B3 diagnostic evidence archival/import; B7A Position source capture; B9 Lifecycle source capture; B10 FINAL basis; B12 report assembly; B11 source-history stress only; B13 integrated verification; B14 audit | ST.position/ST.config/ST.references/ST.setresults; ST.submission/ST.acceptance/ST.nativefacts/ST.reconcile/ST.close/ST.final; ST.facts; ST.research EXTEND within existing SQLite for immutable dataset/member/report records and retained cache objects; no new state family | Source facts in existing TX.opportunity, TX.native, TX.acceptance, TX.facts, TX.cancel, TX.close, TX.partition or TX.final only where the original transition requires them; generic source intake preserves TX.preflight; independent Research-local SQLite writes/read-only assembly are NONE in the canonical transaction taxonomy (§7.7) | AT-NR-153 = ENTRY-RPT-01–15, all E01–E19 source rows, shared dataset/pinning/availability checks in §6.4; actual producer tests before B12; full B12 report tests and V20/B13 verification | G-B3; G-B7A; G-B9; G-B10; G-B12; G-B11 source-only/G-B13 verification; G-B14 audit; exact existing-category local scopes §10.5 | NONE — AUD-ENTRY-REPORT is an audit locator only, not R001–R060 |
| NR-154 | `docs/trading-methodology/methodology/POSITION_RULES.md` Part IV §48 L5464–L5485; §47 L5449–L5460; original F-010 fields §44 L5222–L5299 and source selection/traversal/rounding §§4–30 L4331–L5013 | Implement all 17 required TP research-reporting items in §6.4.9: original target/thesis/traversal/failure evidence, explicit frequency cohorts, exact original ATR distance, post-fill factual target-hit/time/excursion path, original previous-day/1h target grouping and explicitly pinned one-axis min/max research sensitivity. Counterfactual diagnostics cannot replace F-010 output, fabricate hypothetical FINAL or promote parameters. | Position owns F-010 selection/reasons; Set original TP family/reference context; Lifecycle factual executions/close/FINAL; Research only read-only reporting and explicitly isolated diagnostic sensitivity | PARTIAL raw fields/pins/cache/Research storage exist; full target-path/cohort/comparative/sensitivity reporting absent (§6.4.1); source does not prescribe universal report sweep defaults | B3 diagnostic evidence archival/import; B7A Position source capture; B9 Lifecycle source capture; B10 final horizon/outcome; B12 reporting/sensitivity assembly; B11 source-history stress only; B13 verification; B14 audit | Same existing families as NR-153; complete frozen candidate collection/unvisited identities in ST.position/reference lineage; path manifests and immutable diagnostic sensitivity/report members in existing ST.research, not a new canonical store | Original owner source transitions use existing TX.opportunity/TX.native/TX.acceptance/TX.facts/TX.close/TX.partition/TX.final as applicable; Research local persistence is not a canonical TX or cross-owner transaction (§7.7) | AT-NR-154 = TP-RPT-01–17, T01–T17 and shared source/path/retention checks §6.4; actual B7A/B9/B10 source tests; B12 complete report/sensitivity tests; V21/B13 verification | G-B3; G-B7A; G-B9; G-B10; G-B12; G-B11 source-only/G-B13 verification; G-B14 audit; local scopes §10.5 | NONE — AUD-TP-REPORT is an audit locator only, not R001–R060 |


### 3.2 Historical R001–R060 crosswalk

Every row below is a `HISTORICAL_TRACEABILITY_ALIAS`, not an audit-issued requirement number. It carries no independent severity/completion percentage or normative authority. Original meanings are corrected by the NR mapping, including the already-corrected certified object identities. R045 is governed Portfolio opening/economic-day factual base; R046 is removed as a live canonical drawdown target and retained only for research/display isolation. No A-005/A-006 certified object is introduced.

| Historical R alias | Status | Earlier planning label (not normative) | Normalized requirement(s) | Correct checkpoint coverage | Disposition |
| --- | --- | --- | --- | --- | --- |
| R001 | HISTORICAL_TRACEABILITY_ALIAS | canonical JSON deterministic identity | NR-006 | B1 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R002 | HISTORICAL_TRACEABILITY_ALIAS | outbox append idempotency | NR-015 | B2 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R003 | HISTORICAL_TRACEABILITY_ALIAS | outbox claim concurrency | NR-015 | B2 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R004 | HISTORICAL_TRACEABILITY_ALIAS | inbox dedupe/conflict | NR-015 | B2 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R005 | HISTORICAL_TRACEABILITY_ALIAS | TT-FINAL-001 adapter helper | NR-004 | B0, B3 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R006 | HISTORICAL_TRACEABILITY_ALIAS | no fifth business block | NR-001, NR-058 | B4, B5B, B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R007 | HISTORICAL_TRACEABILITY_ALIAS | canonical launcher fence | NR-137, NR-138 | B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R008 | HISTORICAL_TRACEABILITY_ALIAS | process role topology | NR-137, NR-139 | B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R009 | HISTORICAL_TRACEABILITY_ALIAS | scheduler duties | NR-139 | B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R010 | HISTORICAL_TRACEABILITY_ALIAS | contract registry coverage | NR-002 | B0 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R011 | HISTORICAL_TRACEABILITY_ALIAS | schema validator subset | NR-003 | B0 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R012 | HISTORICAL_TRACEABILITY_ALIAS | strict target contract validation | NR-003, NR-018 | B0, B4 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R013 | HISTORICAL_TRACEABILITY_ALIAS | identifier lineage | NR-013, NR-023, NR-029, NR-071, NR-135 | B1, B3, B4, B5B, B6, B7A, B8B, B7B, B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R014 | HISTORICAL_TRACEABILITY_ALIAS | configuration pinning | NR-005, NR-082, NR-149 | B0, B4, B5B, B7A, B8C | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R015 | HISTORICAL_TRACEABILITY_ALIAS | numeric policy enforcement | NR-007, NR-008, NR-009, NR-010, NR-026, NR-150 | B1, B3, B5A, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R016 | HISTORICAL_TRACEABILITY_ALIAS | PORTFOLIO_DATA runtime use | NR-021, NR-025, NR-027 | B3, B8A, B5B, B8B, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R017 | HISTORICAL_TRACEABILITY_ALIAS | API boundary exclusivity | NR-001, NR-019, NR-021, NR-024, NR-084 | B3, B4, B8A, B7A, B8B, B7B, B9, B10, B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R018 | HISTORICAL_TRACEABILITY_ALIAS | Portfolio state health | NR-035, NR-036, NR-037, NR-038, NR-040, NR-043, NR-050 | B8A, B8B, B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R019 | HISTORICAL_TRACEABILITY_ALIAS | Position construction/sizing F-011; Portfolio consumes H output | NR-011, NR-040, NR-047, NR-048, NR-052, NR-092, NR-093, NR-094, NR-098 | B1, B8A, B8B, B7B, B8C, B9, B13 | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R020 | HISTORICAL_TRACEABILITY_ALIAS | Position planned economics F-012; Portfolio verifies limits separately | NR-012, NR-036, NR-042, NR-043, NR-048, NR-052, NR-091, NR-095, NR-096, NR-097 | B1, B8A, B7A, B8B, B7B, B8C, B10, B13 | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R021 | HISTORICAL_TRACEABILITY_ALIAS | ORDER_EVENT structural support | NR-049, NR-114, NR-116, NR-144 | B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R022 | HISTORICAL_TRACEABILITY_ALIAS | ORDER_PLACED structural support | NR-076, NR-102, NR-103, NR-104 | B6, B9 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R023 | HISTORICAL_TRACEABILITY_ALIAS | SUBMIT_AUTHORIZED structural support | NR-048, NR-100 | B8C, B9 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R024 | HISTORICAL_TRACEABILITY_ALIAS | ORDER_SPEC structural support | NR-018, NR-084, NR-092, NR-098, NR-099 | B4, B7A, B7B, B9 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R025 | HISTORICAL_TRACEABILITY_ALIAS | APPROVE_REJECT structural support | NR-018, NR-082, NR-083, NR-084, NR-092, NR-098 | B4, B7A, B7B | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R026 | HISTORICAL_TRACEABILITY_ALIAS | COINS structural support | NR-038, NR-039, NR-057 | B8A, B5B | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R027 | HISTORICAL_TRACEABILITY_ALIAS | MARKET_DATA_REQUEST structural support | NR-022, NR-023, NR-027, NR-029, NR-145 | B3, B5B, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R028 | HISTORICAL_TRACEABILITY_ALIAS | MARKET_HANDOFF structural support | NR-058, NR-061, NR-070, NR-071, NR-072, NR-073, NR-074, NR-145 | B3, B5A, B5B | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R029 | HISTORICAL_TRACEABILITY_ALIAS | research isolation | NR-005, NR-020 | B0, B4, B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R030 | HISTORICAL_TRACEABILITY_ALIAS | migration/store foundation | NR-014, NR-016, NR-017, NR-028 | B2, B3, B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R031 | HISTORICAL_TRACEABILITY_ALIAS | lifecycle stores | NR-027, NR-029, NR-033, NR-034, NR-100, NR-101, NR-102, NR-105, NR-106, NR-108, NR-109, NR-110, NR-111, NR-112, NR-114, NR-115, NR-116, NR-117, NR-143, NR-144, NR-146, NR-148 | B3, B5B, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R032 | HISTORICAL_TRACEABILITY_ALIAS | canonical worker owner handlers | NR-137, NR-138 | B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R033 | HISTORICAL_TRACEABILITY_ALIAS | Set F-001 | NR-053, NR-054 | B5A, B5B | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R034 | HISTORICAL_TRACEABILITY_ALIAS | Set F-002 | NR-053, NR-055 | B5A, B5B | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R035 | HISTORICAL_TRACEABILITY_ALIAS | Set F-003 true range / Wilder ATR / ATR_PCT state | NR-009, NR-053, NR-056, NR-057, NR-062, NR-063, NR-074 | B1, B5A, B5B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R036 | HISTORICAL_TRACEABILITY_ALIAS | Set F-004 normalization/scoring/veto layer | NR-009, NR-010, NR-056, NR-059, NR-060, NR-061, NR-064, NR-065, NR-066, NR-067, NR-068, NR-069, NR-150 | B1, B5A, B5B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R037 | HISTORICAL_TRACEABILITY_ALIAS | Set F-005 final Set LONG/SHORT/NONE ownership | NR-068, NR-069, NR-070, NR-072, NR-074 | B5A, B5B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R038 | HISTORICAL_TRACEABILITY_ALIAS | Position F-008 Entry selection | NR-082, NR-083, NR-085, NR-086, NR-141, NR-142 | B7A, B7B, B9 | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R039 | HISTORICAL_TRACEABILITY_ALIAS | Position F-006/F-007 dynamic stop formulas | NR-083, NR-087, NR-141 | B7A, B7B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R040 | HISTORICAL_TRACEABILITY_ALIAS | Position F-009 stop dispatch | NR-083, NR-088, NR-141 | B7A, B7B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R041 | HISTORICAL_TRACEABILITY_ALIAS | Position F-010 Dynamic Take Profit selection | NR-083, NR-089, NR-090, NR-141 | B7A, B7B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R042 | HISTORICAL_TRACEABILITY_ALIAS | Position F-012 planned economics / minimum net edge | NR-012, NR-091, NR-094, NR-095, NR-096, NR-097, NR-141 | B1, B7A, B7B | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R043 | HISTORICAL_TRACEABILITY_ALIAS | Portfolio grant/release lifecycle | NR-011, NR-016, NR-030, NR-036, NR-040, NR-041, NR-042, NR-043, NR-044, NR-045, NR-046, NR-047, NR-048, NR-049, NR-051, NR-113, NR-132, NR-133, NR-135, NR-149 | B1, B2, B8A, B5B, B6, B7A, B8B, B7B, B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R044 | HISTORICAL_TRACEABILITY_ALIAS | Order Lifecycle owner handlers | NR-028, NR-030, NR-033, NR-034, NR-081, NR-100, NR-101, NR-102, NR-103, NR-105, NR-106, NR-107, NR-108, NR-109, NR-110, NR-111, NR-112, NR-113, NR-114, NR-115, NR-117, NR-135, NR-142, NR-143, NR-146 | B3, B5B, B6, B7A, B8B, B7B, B8C, B9, B10 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R045 | HISTORICAL_TRACEABILITY_ALIAS | Accounting equity | NR-035, NR-043, NR-050, NR-119, NR-129, NR-134 | B8A, B8B, B7B, B8C, B10, B13 | RESCOPED: governed Portfolio opening-base/economic-day evidence and proper receipt accounting; no canonical equity formula. |
| R046 | HISTORICAL_TRACEABILITY_ALIAS | Accounting drawdown | NR-020, NR-134 | B10, B12, B13 | RETIRED_CANONICAL_TARGET: no live drawdown formula; retain only research/display and legacy isolation. No A-006 object. |
| R047 | HISTORICAL_TRACEABILITY_ALIAS | FINAL/CLOSED once-only result | NR-026, NR-027, NR-031, NR-032, NR-033, NR-046, NR-051, NR-118, NR-119, NR-120, NR-121, NR-122, NR-123, NR-124, NR-125, NR-126, NR-127, NR-128, NR-129, NR-130, NR-131, NR-132, NR-133, NR-134, NR-147, NR-148 | B3, B8A, B5B, B8B, B7B, B8C, B9, B10, B13 | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |
| R048 | HISTORICAL_TRACEABILITY_ALIAS | API-to-owner flow | NR-019, NR-021, NR-022, NR-024, NR-025 | B3, B8A, B5B, B8B, B9, B10, B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R049 | HISTORICAL_TRACEABILITY_ALIAS | full canonical E2E tests | NR-136, NR-140 | B11, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R050 | HISTORICAL_TRACEABILITY_ALIAS | canonical active routing | NR-137, NR-138 | B12 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R051 | HISTORICAL_TRACEABILITY_ALIAS | ORDER_CANCEL_SIGNAL runtime production | NR-073, NR-075, NR-076, NR-077, NR-078, NR-079, NR-080, NR-081, NR-104, NR-106 | B5B, B6, B9 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R052 | HISTORICAL_TRACEABILITY_ALIAS | package revision v1.2.14 | NR-002 | B0 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R053 | HISTORICAL_TRACEABILITY_ALIAS | generated schema v1.2.14 id/title | NR-002 | B0 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R054 | HISTORICAL_TRACEABILITY_ALIAS | stale tests assert v1.2.14 | NR-005 | B0, B4 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R055 | HISTORICAL_TRACEABILITY_ALIAS | ORDER_CANCEL_SIGNAL source mismatch | NR-003, NR-078, NR-079 | B0, B6 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R056 | HISTORICAL_TRACEABILITY_ALIAS | research pins stale revision | NR-005 | B0, B4 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R057 | HISTORICAL_TRACEABILITY_ALIAS | legacy paper runtime | NR-020 | B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R058 | HISTORICAL_TRACEABILITY_ALIAS | legacy paper/spot adapters | NR-020 | B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R059 | HISTORICAL_TRACEABILITY_ALIAS | legacy trigger formulas | NR-020 | B12, B13 | Trace only; implement/review the linked NR obligations, not the old classification or batch assignment. |
| R060 | HISTORICAL_TRACEABILITY_ALIAS | demo strategy/regime S-005 | NR-020, NR-067 | B5A, B12, B13 | SEMANTIC_LABEL_CORRECTION: exact current object/owner/stage is defined by §5 and linked frozen clauses; overlapping old rows do not add objects. |

### 3.3 Historical finding crosswalk

These BCA labels are retained only to connect the certification evidence to the revised planning mechanisms. They do not reinstate the original audit’s mislabeled formula/equity/drawdown meanings.

| Historical finding | Corrected planning scope | Checkpoint(s) | Closure mechanism |
| --- | --- | --- | --- |
| BCA-001 | Missing canonical handlers/dispatch | B5B/B6/B7A/B8B/B7B/B8C/B9/B10; gated B12 | All owner-local gates, then one worker; no early routing |
| BCA-002 | Active source package/schema mismatch | B0 | Frozen metadata plus actual schema/whitelist/branch conformance |
| BCA-003 | Active baseline test expectations | B0 | Correct current assertions, preserve historical negative fixtures |
| BCA-004 | F-013 branch and monitor integration | B0/B6/B9 | Public parser + actual reducer + original-entry native reconciliation |
| BCA-005 | Missing canonical Set computation/handler | B5A/B5B | Complete populations/state and atomic result/handoff |
| BCA-006 | Missing canonical Position computations | B7A/B7B | Interleaved grant dependency, exact complete construction |
| BCA-007 | Portfolio atomic scope/grant/hold/release | B8A/B8B/B8C/B10 | Non-reserving grant, H booking, day/receipt/frontier |
| BCA-008 | Lifecycle/finality incomplete | B9/B10 | Reuse native/sync/close foundation, source proofs and terminal transaction |
| BCA-009 | Validator construct coverage | B0 minimum; B1 regression; B4 bindings | No ignored currently used oneOf/not/other frozen constructs |
| BCA-010 | Pin default/version and isolation | B0/B4/B5B/B7A/B8C/B13 | New defaults only; immutable started/historical pins |
| BCA-011 | Full business replay incomplete | Every B5–B10 owner checkpoint; B11 hardening | Local correctness before integrated stress |
| BCA-012 | Process/scheduler integration | B12 | Only frozen duties, no new trading TTL or second worker |
| BCA-013 | Legacy/demo authority boundary | Every adjacent checkpoint; B12/B13 | No canonical fallback; useful isolated code retained |
| BCA-014 | Canonical financial/finality obligations | B10 plus Portfolio day foundation B8A | Factual result/funding/CLOSED/receipt; unsupported equity/drawdown labels removed |
| BCA-015 | Identity/lineage integration | B1/B4 and every owner checkpoint | Single creator, immutable full history, exact binding |
| BCA-016 | Exclusive factual API integration | B3 then B5B/B8A/B8B/B9/B10 | Three bidirectional families; no Position/API edge |
| BCA-017 | Exact certified numerical implementations | B1/B5A/B7A/B7B/B8A/B8B/B8C/B10 | Exact work/wire/report and source-specific allocation |
| BCA-018 | End-to-end conformance evidence | Local owner tests; B11/B12/B13/B14 | Real applicable runtime/DB evidence; no historic green-count shortcut |

## 4. Exact contract graph and family matrix

The four business owners are **Portfolio, Set, Position and Lifecycle**. “Accounting” denotes Lifecycle-internal implementation organization, not a fifth owner. API is factual/technical; Research is isolated diagnostic/governance evidence, not a canonical decision owner.

```text
Portfolio --COINS v2--> Set
Set --MARKET_HANDOFF v4--> Position
Position --APPROVE_REJECT v5 (initial)--> Portfolio
Portfolio --CAPITAL_AND_LIMITS v5 (non-reserving grant)--> Position
Position --APPROVE_REJECT v5 (construction result)--> Portfolio
Position --ORDER_SPEC v5--> Lifecycle
Portfolio --SUBMIT_AUTHORIZED v5 (current H hold)--> Lifecycle
Lifecycle --ORDER_PLACED v3 (placement/terminal return)--> Set
Set --ORDER_CANCEL_SIGNAL v2--> Lifecycle
Lifecycle --ORDER_EVENT v7 (native/logical/final/incident variants)--> Portfolio
Portfolio <--PORTFOLIO_DATA_REQUEST v5 request/response--> API
Set <--MARKET_DATA_REQUEST v3 request/response--> API
Lifecycle <--ORDER_MANAGEMENT v4 request/response--> API
```

There are **twelve families**, not a separate family for each variant or each API direction. CAPITAL_AND_LIMITS has only Position as consumer. Portfolio-data responses have only Portfolio as consumer. ORDER_PLACED returns to Set. A Lifecycle final ORDER_EVENT is not a Portfolio-created receipt.

For every family: B0 enforces the complete frozen structural schema at the public parser; B4 adds/reuses identity/content/scalar binding checks; each actual owner then verifies its current behavioral preconditions. These three layers cannot substitute for one another. The matrix’s production/consumption assignments—not a generic B4 producer layer—are authoritative.

| Contract | Version | Producer | Consumer | Structural validation | Semantic validation / identity binding | Production checkpoint | Consumption checkpoint | Existing implementation reused | Persistent state | Transaction point | Replay/idempotency | Frozen source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COINS | v2 | Portfolio | Set | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: scope_revision, symbol, exact configured Set binding; OPEN/CLOSE content | B8A | B5B | FN.SCOPE/FN.EPOCH/FN.MSG | ST.scope | TX.scope/TX.set | Same revision/content inert; changed known content conflict; unfinished epoch only | `docs/trading-methodology/business-contracts/COINS.md`; registry/wire schema |
| MARKET_HANDOFF | v4 | Set | Position | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: decision_cycle_id, set_result_id, frozen snapshot/config, exact producer role/level bindings | B5B | B7A | FN.FACT/FN.EPOCH/FN.CONTRACT/FN.MSG | ST.setresults/ST.frozen/ST.references | TX.set/TX.opportunity | Immutable handoff replay; no newer snapshot/config/reference lookup | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`; registry/wire schema |
| APPROVE_REJECT | v5 | Position | Portfolio | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: Initial position_decision_id/cycle; post-grant construction_result_id/grant and exact spec scalars/digest | B7A initial; B7B construction | B8B initial; B8C construction | FN.PIN/FN.CONSTRUCT/FN.GRANT/FN.AUTH | ST.position/ST.construction/ST.grants | TX.opportunity/TX.construction/TX.grant/TX.hold | Stage-correct outcome identity; no successful plan/spec on initial or failed construction | `docs/trading-methodology/business-contracts/APPROVE_REJECT.md`; registry/wire schema |
| CAPITAL_AND_LIMITS | v5 | Portfolio | Position | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: Immutable capital_grant_id and exact initial decision/cycle/result, allowed venue/profile/fee/accounting facts | B8B | B7B | FN.GRANT | ST.grants | TX.grant/TX.construction | Duplicate initial APPROVE same non-reserving grant; no expiry/supersession or Lifecycle consumer | `docs/trading-methodology/business-contracts/CAPITAL_AND_LIMITS.md`; registry/wire schema |
| ORDER_SPEC | v5 | Position | Lifecycle | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: grant/construction/plan/tranche/spec/version/full-envelope digest and exact constructed economics | B7B | B9 | FN.SPEC/FN.CONSTRUCT/FN.START | ST.spec | TX.construction/TX.native | Successful result+spec+two outboxes; delayed matching auth permitted; no reprice | `docs/trading-methodology/business-contracts/ORDER_SPEC.md`; registry/wire schema |
| SUBMIT_AUTHORIZED | v5 | Portfolio | Lifecycle | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: authorization_id, all construction/spec lineage/digest and exact H | B8C | B9 | FN.AUTH/FN.START | ST.authorization/ST.holds | TX.hold/TX.native | One current hold/slot; immutable auth, consumed CREATE and terminal dominance | `docs/trading-methodology/business-contracts/SUBMIT_AUTHORIZED.md`; registry/wire schema |
| ORDER_EVENT | v7 | Lifecycle | Portfolio | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: Variant-correct logical/native revisions; accepted source/allocation; immutable result_id/tranche; separate incident ID/revision | B9 native/logical; B10 FINAL/integrity | B8C/B9 logical projections; B10 receipt/incident | FN.RECON/FN.MSG/FN.PORT | ST.attribution/ST.final/ST.receipts/ST.incidents/ST.frontier | TX.acceptance/TX.partition/TX.final/TX.incident/TX.receipt/TX.frontier | Independent variant histories/dedupe; complete source proof; no FINAL dedupe erasing incident | `docs/trading-methodology/business-contracts/ORDER_EVENT.md`; registry/wire schema |
| ORDER_PLACED | v3 | Lifecycle | Set | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: cycle/result/plan/tranche, original accepted client/native entry, placement/terminal revision and authoritative times | B9 | B6 typed consumer; B9 real integration | FN.SYNC | ST.sync/ST.monitor | TX.placement/TX.monitor | Existing placement and ENTRY_LIFECYCLE_EVENT return only; terminal replay cannot reactivate | `docs/trading-methodology/business-contracts/ORDER_PLACED.md`; registry/wire schema |
| ORDER_CANCEL_SIGNAL | v2 | Set | Lifecycle | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: INVALIDATION record/condition/evidence OR sticky unavailable key/first time/reason, same original accepted entry | B6 | B9 | FN.CONTRACT/FN.SYNC/FN.RECON/FN.MSG | ST.monitor/ST.cancel | TX.monitor/TX.cancel | Cause-specific immutable content; no target guessing; both causes same native remainder cancel intent | `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md`; registry/wire schema |
| PORTFOLIO_DATA_REQUEST | v5 | Portfolio (request); API (response) | API (request); Portfolio (response) | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: request_id/response_id, requested unique symbol set, exact source/as-of/profile and binary per-item statuses | B8A/B8B requests; B3 factual responses | B3 requests; B8A/B8B responses | FN.API/FN.FACT | ST.facts | TX.facts/TX.scope/TX.grant | Both directions one family; exact row/request binding; no Position response edge | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`; registry/wire schema |
| MARKET_DATA_REQUEST | v3 | Set (request); API (response) | API (request); Set (response) | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: selection_id/request_id; exact fixed snapshot/page/manifest/coverage and accepted ownership | B5B requests; B3 factual responses | B3 requests; B5B responses (B5A kernels use accepted data) | FN.API/FN.FACT/FN.EPOCH | ST.facts/ST.setcalc | TX.preflight/TX.facts/TX.set | Immutable history before echo/stale checks; no page revision or latest-page substitution | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`; registry/wire schema |
| ORDER_MANAGEMENT | v4 | Lifecycle (request); API (response) | API (request); Lifecycle (response) | B0 public parser; B4 structure/version regression | B4 binding + actual owner checks: operation/request/response, native/client/source/profile scope; accepted proof/coverage and exact queried interval | B9 execution/hard requests; B10 financial requests; B3 responses | B3 requests; B9 native/hard responses; B10 financial responses | FN.API/FN.NATIVE/FN.SUBMIT/FN.RECON | ST.nativefacts/ST.coverage/ST.financial | TX.preflight/TX.facts/TX.native/TX.cancel/TX.final | Factual request/response only; raw known evidence before malformed/stale/terminal filters | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`; registry/wire schema |

No owner reads another owner’s mutable business table to bypass an edge. The common committed-prefix mechanism is technical delivery ordering on the existing Lifecycle→Portfolio transport, not a Portfolio read of Lifecycle quarantine or a new business edge. Position’s permitted venue/fee/accounting facts are frozen in CAPITAL_AND_LIMITS; it never directly obtains a Portfolio-data response.

## 5. Certified object to contract, formula and state integration

Exactly eighteen identities are retained. Supporting protocol/fee/coverage/quantity obligations are not fabricated additional A/S certified objects. Numeric kernels without their state, producer/consumer and transaction integration do not complete an object assignment. S-005’s complete assignment is isolation, not canonical implementation.

| Object | Exact canonical meaning | Owner | Inputs / contracts | Existing infrastructure reused | New/extended persistent state | Output / contracts | Downstream state / consumer | Correct checkpoint(s) | Normalized anchor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | signed 1m endpoint percentage displacement | Set | Completed 1m endpoint facts through MARKET_DATA_REQUEST; pinned CURRENT_STATE trigger | FN.FACT/FN.EPOCH; B1 exact primitives | ST.setcalc/ST.setevents: endpoint/source/trigger evidence, no separate formula table | Internal trigger satisfaction and exact work value; not final direction | Set formation; never ATR-normalized momentum substitution Formation consumer only; never an F-004 operand, normalization input or classifier availability gate. | B5A kernels; B5B consumption | NR-054 |
| F-002 | 1m relative participation / volume confirmation | Set | Completed 1m volume plus own complete trigger population | FN.FACT/FN.EPOCH; B1 exact primitives | ST.setcalc/ST.setevents: volume members/coverage/config | Internal participation trigger; no LONG/SHORT authority | Set formation; population distinct from F-004 analytical windows Formation consumer only; no F-004 numerical/availability edge or base-volume-to-quote-turnover substitution. | B5A/B5B | NR-055 |
| F-003 | true range / Wilder ATR / ATR_PCT state | Set | Authoritative completed 15m candles, preceding close, seed/accepted ancestry | FN.FACT/FN.CAS | ST.atr15: Q36 recurrence/seed and source checkpoint, invalid/zero-close state | Internal work ATR/PCT; only prescribed Q18 MARKET_HANDOFF exports | F-004 required context and Position exact received values; no local 5m substitution | B5A/B5B | NR-062 |
| F-004 | Set normalization / scoring / veto | Set | Full prescribed factor/dependency populations through Set factual intake; independent local 5m and canonical 15m context Only its own frozen input set: no F-001/F-002 result, trigger work/sign or trigger-local population/availability gate. | FN.FACT/FN.EPOCH/FN.CAS | ST.setcalc/ST.local5: exact membership/work scores and candidate-side veto evidence | Internal Q36 normalization/score/veto; permitted diagnostics only | F-005 final ownership; never API/research or wire report authority | B5A/B5B | NR-068 |
| F-005 | final Set LONG / SHORT / NONE resolver for F-005-governed Sets | Set | Classifier: canonical Q36 F-004 score plus all eleven prescribed inputs, derived diagnostics, inclusive hard gates and both sides' veto evidence. Final Set resolution: independently eligible configured formation and common handoff prerequisites join the classifier criterion; these are not classifier operands. Current immutable governed scope | FN.EPOCH/FN.SCOPE/FN.MSG | ST.setresults/ST.references/ST.frozen + event consumption | MARKET_HANDOFF v4 only for valid committed MATCHED directional outcome | Position initial opportunity; frozen record later activates F-013 only on placement | B5A classifier; B5B transaction | NR-074 |
| F-006 | LONG dynamic stop | Position | Same F-008 Entry, immutable LONG handoff, producer references, received ATR/tick, pinned config | FN.PIN; structural construction/spec helpers | ST.position: same retained initial geometry/evidence | Internal exact selected/rounded LONG stop and failure reason | F-009 DYNAMIC stop branch; retained Stop for later joint TP/SL feasibility and unchanged opportunity/post-grant geometry/economics | B7A | NR-087 |
| F-007 | SHORT dynamic stop | Position | Same F-008 Entry, immutable SHORT handoff, producer references, received ATR/tick, pinned config | FN.PIN; structural construction/spec helpers | ST.position: same retained initial geometry/evidence | Internal exact selected/rounded SHORT stop and failure reason | F-009 DYNAMIC stop branch; retained Stop for later joint TP/SL feasibility and unchanged opportunity/post-grant geometry/economics | B7A | NR-087 |
| F-008 | Entry selection | Position | Immutable MARKET_HANDOFF producer bindings and pinned policies/tick | FN.PIN/FN.CONTRACT | ST.position: selected reference, raw/rounded Entry, pinned initial decision | Internal Entry; initial APPROVE_REJECT v5 geometry decision | Stop/TP and unchanged post-grant sizing operand; no later reselection | B7A | NR-085 |
| F-009 | FIXED versus DYNAMIC stop dispatch | Position | Same Entry, configured mode/tick and applicable F-006/F-007 outcome | FN.PIN/FN.CONSTRUCT | ST.position: chosen mode and exact selected branch/reason | FIXED result or unchanged applicable dynamic output | TP feasibility/geometry and later F-011/F-012 | B7A | NR-088 |
| F-010 | Dynamic Take Profit | Position | Immutable MARKET_HANDOFF/direction, matched_at/market_snapshot_at; same-bound AVAILABLE F-008 Entry; frozen TP references and tp_context; received ATR_15m and tick; pinned Position configuration and DYNAMIC TP mode; required instrument/cycle/result/handoff-digest/metadata/tick-provenance bindings. No Stop operand or availability prerequisite | FN.PIN/FN.CONSTRUCT | ST.position: sequential traversal/selection, rounding and reason | Internal independently selected/rounded TP result with its own Entry/TP geometry checks | Retained post-grant construction/economics, no SL-derived repair | B7A | NR-089 |
| F-011 | Position construction/sizing C, T, Q, N, A, H | Position | Exact CAPITAL_AND_LIMITS grant and original approved geometry/leverage/instrument facts | FN.GRANT/FN.CONSTRUCT/FN.SPEC/FN.UOW | ST.construction/ST.spec: exact intermediates and quantized H, outcome/spec linked | CONSTRUCTION_RESULT on APPROVE_REJECT v5 plus ORDER_SPEC v5 in success transaction | Portfolio verifies/books H; Lifecycle consumes immutable spec; neither recomputes sizing | B7B; downstream B8C/B9 | NR-093 |
| F-012 | planned geometry/economics, factual fees/rebates, minimum R:R, minimum net edge | Position | Same geometry, successful F-011 actual N/Q, signed frozen fee facts and enabled gates | FN.CONSTRUCT/FN.SPEC/FN.PIN | ST.construction: exact gate evidence; report-only ratios; same joined success state | CONSTRUCTED or failed construction; approved economics in existing outputs | Portfolio current own gates then authorization; Lifecycle unchanged approved economics | B7A gross feasibility only; B7B complete economics | NR-097 |
| F-013 | frozen pending-entry monitoring and cancellation | Set | B5B frozen record + authoritative ORDER_PLACED original entry return + allowed frozen-predicate current evidence | FN.SYNC/FN.EPOCH/FN.MSG/FN.RECON | ST.monitor/ST.cancel: activation, four-outcome reducer, sticky/deferred key/first time/reason | ORDER_CANCEL_SIGNAL v2 INVALIDATION or MONITORING_UNAVAILABLE, otherwise specified no-message outcome | Lifecycle B9 reconcile-first exact unfilled remainder; terminal return ends applicability | B6 monitor; B9 actual return/cancel integration | NR-079 |
| A-002 | canonical immutable FINAL result | Lifecycle | Complete unique factual execution/fee/rebate/funding/other-cost evidence, current currency/coverage/attribution/day proof | FN.RECON/FN.CLOSE/FN.UOW/FN.MSG; only proven compatible pure financial helpers | ST.final/ST.financial/ST.coverage: immutable result and full revision-bound basis | Final ORDER_EVENT v7; NOT a Portfolio receipt | Portfolio creates own receipt/day/A-009/release once through frontier | B10 Lifecycle producer and Portfolio integration | NR-125 |
| A-004 | funding allocation | Lifecycle | Unique funding source/aliases/complete coverage; effective-time eligible quantities and common settlement basis | FN.API/FN.RECON/FN.UOW; B1 exact primitives | ST.funding: signed source, q18 raw/base/residue, deterministic recipient and once-only allocations | Internal allocated funding component with unchanged algorithm version | A-002 factual funding contribution only; never close authority | B10 | NR-120 |
| A-009 | Portfolio Daily Loss / economic accounting-day aggregation and latch | Portfolio | Once-received immutable FINAL, ACCOUNTING_DAY_V1 day/base/config/recovered latch; no unrealized or arrival-day substitution | FN.PORT/FN.CAS/FN.MSG; legacy day service fenced | ST.day/ST.receipts: exact historical sum/base/latch and unique result receipts | Current scope/grant/hold allowed/blocked state; no exit/cancel message | B8A/B8B/B8C current Portfolio gates; B10 real FINAL receipt integration | B8A state/gates; B8C hold check; B10 completion | NR-043 |
| S-004 | canonical CLOSED / six-predicate finality | Lifecycle | Current exposure/remainder/owned children/close intent/financial completeness/competing authority vector | FN.CLOSE/FN.RECON/FN.SUBMIT/FN.UOW | ST.final/ST.close: six source-backed predicates and immutable terminalized_at | CLOSED with immutable FINAL/outbox in Lifecycle terminal transaction | Portfolio fenced receipt may release exactly once; physical flatness is insufficient | B10, using B9 current proofs | NR-127 |
| S-005 | research/demo diagnostic only | Research | Explicitly isolated research/demo inputs | FN.RESEARCH/FN.LEGACY | ST.research only; no NEW canonical state/table | Research/display diagnostics only, no canonical trading contract | No canonical decision consumer; isolation is the complete integration assignment | B13 fence (preserved from earlier touched checkpoints) | NR-020 |

**F-005 scope:** The F-005 row and F-004→F-005 final-resolution references describe F-005-governed Sets only. Generic non-F-005 fixed-direction or explicit matched-branch resolution remains Set-owned under NR-053 and frozen SET §5. It is not another certified object or an alternate owner. The historical R037 label has no independent authority to broaden that scope. F-005 inputs, arithmetic, thresholds, vetoes, state, checkpoints and governed MARKET_HANDOFF behavior remain unchanged; §5.2 makes the two scope-bound routes explicit.

### 5.1 Position evaluation schedule versus operand dependencies — FA-01

The OPPORTUNITY-stage schedule remains:

```text
configuration + Market Handoff
→ immutable direction
→ F-008 Entry
→ Stop evaluation / F-009 selection
→ F-010 Take Profit evaluation (when DYNAMIC TP is selected)
→ joint Entry / Stop / TP feasibility
→ gross structural risk/reward and enabled Minimum R:R
→ initial APPROVE / REJECT
```

**evaluation order != operand dependency.** Evaluating Stop first does not make a Stop result, Stop price, Stop distance or Stop availability an F-010 input. The existing FIXED-mode rules remain supported and unchanged.

For the DYNAMIC branches, the operand graph is `bound F-008 Entry + frozen Stop inputs → applicable F-006/F-007 → F-009 DYNAMIC Stop`, and separately `bound F-008 Entry + frozen F-010 TP inputs → F-010 TP`. These branches meet only afterward at joint TP/SL feasibility and Entry/SL/TP geometry. Neither directional Stop formula nor F-009 supplies an operand, preflight prerequisite, fallback input, selector input or availability dependency to F-010.

F-010 consumes only its own governed handoff/configuration/Entry/reference/ATR/tick/provenance inputs identified in its object row and frozen Part IV §§4/10. Its own post-rounding checks concern Entry and TP, not Stop. When those required inputs are available, F-010 is evaluated even when the required Stop is unusable. It may produce a usable TP, but later joint feasibility still requires a usable Stop and TP. A missing/unusable required Stop therefore keeps the overall initial opportunity **REJECT**; TP availability never authorizes an unprotected trade. Stop and TP are combined only in the later joint geometry/gross checks and subsequent grant-dependent construction/F-012 economics as applicable. No TP is derived from SL distance and no post-grant geometry reselection is introduced.

Frozen basis: `docs/trading-methodology/methodology/POSITION_RULES.md` Part I §14 L465–L519 and §43 L1500–L1508; Part IV §4 L4331–L4352, §10 L4476–L4480, §26 L4896–L4909 and §§29–30 L4954–L5013. The explicit distinguishing acceptance subcase is in B7A under AT-NR-089; it adds no normalized requirement, contract, state store or checkpoint.

### 5.2 Configuration-bound direction routes and separate classifier/formation branches — FA-R3-01 preserved; FA-R4-01 corrected

Set is the sole final-direction owner in both routes. F-005 is not a universal prerequisite for every generic Set. The following is an owner-local dependency/scope description, not a new wire field, user-selectable mode, direction service or contract edge:

```text
F-005-governed Set — two independent owner-local branches:

CLASSIFIER:
F-003 canonical 15m WORKING/context
+ F-004 own prescribed factor/population inputs
+ F-004 separate local-5m state where applicable
→ F-004 normalization / scoring / veto
→ F-005 classifier criterion (LONG / SHORT / NONE)

FORMATION:
immutable configured Trigger/Core Set expression
  (including F-001 / F-002 only where actually configured)
+ Boolean / sequence / N-of-M / event rules
+ active formation epoch and eligible same-epoch events
+ configured source / reference / common Set requirements
→ independently evaluated configured formation eligibility

FINAL SET RESOLUTION:
valid directional classifier criterion
+ independently TRUE / eligible configured formation
+ all mandatory source / reference / MARKET_HANDOFF validation
→ eligible Set-owned final LONG / SHORT
→ same TX.set: MATCHED + consumed events + decision_cycle_id
  + set_result_id + concrete producer references
  + frozen F-013 condition record + MARKET_HANDOFF + outbox

Generic deterministic Set outside F-005-governed scope:
configured fixed direction
OR configured explicit matched-branch direction
→ declared deterministic conflict resolution when required
→ Set-owned final LONG / SHORT only for an otherwise eligible match
```

The classifier consumes neither F-001 trigger result, `move_pct_work` or sign evidence nor F-002 result, trigger-local population or base-volume participation outcome as numerical or availability operands. An underlying factual metric may participate only when F-004 independently prescribes it with its own source, timeframe, population and accepted provenance. Trigger-local populations cannot substitute for classifier populations. F-003's canonical 15m state and F-004's separate local-5m state remain distinct.

The classifier branch retains the frozen eleven inputs, derived diagnostics, work precision, inclusive hard gates, thresholds and candidate-side veto rules. Formation evidence has its own configured dependencies. A required F-001 UNAVAILABLE or F-002 FALSE can prevent formation and final MATCHED while an independently evaluable F-004/F-005 classifier remains unchanged. Classifier success alone is not MATCHED. Under SET §34A, formation failure or mandatory handoff-validation failure produces `matched=false`, final Set `direction=NONE` and its separate resolution reason; it does not overwrite the retained classifier criterion, create committed cycle/result IDs, freeze a successful handoff or authorize downstream work.

Inside governed scope, fixed/matched-branch labels cannot bypass F-005, including NONE/unavailable. Arbitration among eligible Core Sets remains declared, deterministic, configuration-bound, Set-owned and consistent with F-005; missing/conflicting arbitration is ineligible. No independent branch can waive the other applicable branch or common handoff prerequisites.

The second route uses only the existing generic deterministic definition allowed by frozen SET §5. It does not acquire an F-005 or classifier-only data prerequisite merely by being canonical. This does not waive that generic definition's own required data, configured triggers, event/formation eligibility, reference bindings, required positive volatility exports or any mandatory MARKET_HANDOFF validation. Opposing eligible LONG/SHORT branches at the same canonical timestamp require an explicit deterministic conflict rule already declared in the bound definition. Apply that declared rule only as permitted by frozen semantics; otherwise the configuration/outcome is invalid or ineligible, no winner is guessed and no handoff is emitted. No first-arrival, lexical or strongest-score resolver is added.

Both routes converge on the same existing B5B Set result/handoff transaction only when all applicable frozen conditions are satisfied. Scope is determined from the immutable selected Set/Trigger/Core Set definition, not from the Set's name, the currently active configuration, an absent classifier value or a consumer's preference. Missing/invalid governing configuration cannot be reclassified as generic to bypass F-005.

At epoch creation and MATCHED, retain the existing configuration identity/version/content digest and the exact direction-rule, matched-branch/constituent and declared conflict-rule evidence through the assigned Set records. Restart restores those original bindings before new input. It cannot switch scope in either direction, resolve a branch from latest data, reverse an accepted direction, remint cycle/result identity or rewrite a frozen handoff. Same-ID changed configuration, governing scope, branch or direction binding is an integrity conflict. This specializes the unchanged ST.config/TX.set and P17 obligations; no persistence or transaction topology changes.

Frozen basis: `docs/trading-methodology/methodology/SET.md` §5 L509–L530; Part II §§33–37, especially §34A L3155–L3197; `docs/trading-methodology/SYSTEM_PROTOCOLS.md` P17 L359–L365. B5B's AT-NR-053 cases A–H and invariant 1 are the local/integrated acceptance oracles.

### 5.3 Mandatory classifier-versus-formation discriminator — AT-NR-068-CF A–D

This discriminator is shared acceptance coverage for NR-054, NR-055 and NR-068, not a new normalized requirement, certified object, contract or configuration mode. `formation_trigger_evidence` and `classifier_evidence` below describe distinct owner-local evaluation results in ST.setcalc; these names do not add wire fields. B5A must expose the two independently evaluable concepts. B5B consumes them within the same existing Set handler and TX.set.

**Common fixture and oracle.** Start with the complete independent source-derived F-004/F-005 LONG golden vector required by AT-NR-068: all eleven inputs/required diagnostics valid, all hard gates passing, score at or above +0.35 and no selected-candidate veto. Mirror the independence tests for a SHORT vector at or below -0.35. Pin classifier configuration, canonical F-003 work state, local-5m state, complete populations, cutoff and accepted classifier-source bindings. Keep the exact work values, score, veto evidence and `classifier_direction` byte-equivalent in cases A–C. Execute actual F-003/F-004/F-005 kernels, not an injected final score/direction. Use a valid governed Set whose independent configured formation requires the tested trigger and whose other formation, scope, reference and handoff prerequisites pass.

Each contrast uses isolated, source-valid fixture instances with explicit source identities; it must not mutate an accepted record under the same ID. “Fixed classifier evidence” means every classifier operand/population/configuration/provenance input is fixed, not that a real contradiction in a shared factual source is ignored. A trigger-only missing selection or distinct trigger-local population may change without invalidating the separately complete classifier selection. If a changed factual core is genuinely shared by F-004, its existing integrity rules still apply; that is not a valid independence fixture.

| Case | Actual source-derived input/action | B5A required result | Actual B5B required result |
| --- | --- | --- | --- |
| A — F-001 unavailable, classifier fixed | Preserve all classifier evidence. Remove only required selected completed-1m endpoint/coverage evidence from the configured F-001 branch; do not remove classifier candles/populations or mandatory common handoff evidence. SET §8A L645–L670/L699–L712 requires F-001 UNAVAILABLE. | F-001 UNAVAILABLE; F-004 work/score/veto and F-005 classifier unchanged. No F-001 availability preflight in F-004. | Formation UNAVAILABLE prevents MATCHED: `matched=false`, final `direction=NONE`, separate formation-resolution reason. Retain unchanged classifier evidence; no committed cycle/result/frozen-success/handoff/outbox or downstream opportunity. |
| B — F-002 false, classifier fixed | Retain complete consecutive 61-candle F-002 input; current base volume c=1 and all 60 historical volumes=1 give M=1, K=60, R=1, P=100. R>=2 fails, so F-002 FALSE. All classifier inputs remain fixed. | Actual F-002 FALSE with the exact stated M/K/R/P; F-004/F-005 results unchanged. A false formation trigger is not classifier DATA_UNAVAILABLE or a direction veto. | Required formation FALSE prevents MATCHED with the same unmatched/final-NONE boundary and distinct formation reason; no successful lineage or publication. |
| C — trigger-local population only | In one independent fixture c=2 and all 60 historical volumes=1: M=1, K=60, R=2, P=100, TRUE. In the contrasting coherent fixture retain c=2 but historical volumes=2: M=2, K=60, R=1, P=100, FALSE. Keep F-004 quote-turnover, ordinary normalization populations, completed classifier facts and all other classifier operands unchanged. These are distinct accepted fixture worlds, not altered same-ID facts. | F-002 changes TRUE→FALSE under its own exact predicate; F-004 work/score/veto and F-005 classifier do not change. No base-volume substitution for classifier quote-turnover or ordinary population. | With all other requirements satisfied, the TRUE formation fixture may commit its original match; the FALSE fixture cannot. Only the configured formation branch explains the difference. |
| D — genuine classifier operand only | Keep independently source-valid F-001/F-002 formation results TRUE and their bindings fixed. Change only genuine local-5m classifier evidence, using full raw completed/population fixtures whose independent exact oracle gives VNM_5m_z=0 versus VNM_5m_z=-2 for an otherwise eligible LONG candidate. The latter activates the frozen inclusive LONG local-momentum veto. No prefilled z/score/direction may replace the real kernels. | Formation evidence remains TRUE. F-004's own derived local veto changes; F-005 is LONG in the no-veto fixture and NONE in the -2 veto fixture, with the frozen veto reason. Mirror +2 for SHORT. The numeric score need not change for the classifier veto result to change. | The valid no-veto case may MATCH; the veto case has no satisfied classifier criterion and cannot MATCH despite unchanged valid formation. No opposite-direction fallback. |

Frozen basis: `methodology/SET.md` §8A L617–L712; §8B L847–L928/L943–L988/L1078; Part II local-5m population L2561–L2676, local veto L2677–L2697, weights/thresholds L3050–L3150 and §34A/35 L3155–L3226. The numeric F-002 values above follow M=(v30+v31)/2, K=count(v<=c), R=c/M and P=100K/60; no new parameter is selected.

**Execution and negative controls.** B5A independently computes and round-trips both evidence branches; B5B runs A–D through actual configuration/epoch/formation/final-resolution paths and real PostgreSQL transactions. Assert actual classifier output and its complete operand binding even when final matching fails: a handler that skips classification because F-001 is unavailable or F-002 is false must fail the discriminator despite returning the correct final unmatched result. A constant/prefilled classifier fails D. A population-substituting classifier fails C. At every successful Set commit inject failures through consumption/result/references/frozen record/handoff/outbox; failed matches commit no success IDs. Replay restores each fixture's original evidence and separates classifier reason from Set-resolution reason. V03/V04/V15 and B13 verify the already implemented local behavior; B5A still creates no MATCHED or wire handoff.

## 6. Persistence overlay and ownership

The action column is a logical-state plan. Do not equate a row with a new SQL table. Existing compatible records take precedence over new repositories; an extension is preferred whenever it can preserve required uniqueness, immutable fields, current-proof history and transaction composition. New domain state is introduced by its listed owner checkpoint, not pre-created by B2.

For all canonical states: preserve account/environment scope; persist the exact immutable binding and canonical digest/source core where required; enforce semantic uniqueness in addition to delivery dedupe; validate known content before stale suppression; retain raw contradictions separately; hydrate accepted history before processing new deliveries. No field-sized database numeric type may silently round a source-defined exact value.

| State ID | Logical state | Existing representation | Required action | Owner | Checkpoint | Transaction role | Replay role |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ST.transport | Owner-state CAS; inbox/outbox; handler publication Owner-local NR-151/NR-152 capture metadata and required immutable publication/intake history are retained at the producing B8/B9/B10 checkpoint, not pre-created as B2 domain state. | FN.UOW/FN.CAS/FN.MSG | EXTEND | Transport; effects remain one owner | B2; all behavior checkpoints | TX.owner | Existing same-ID canonical equality/conflict; durable consumption only with effect. Same captured arrival/attempt retries retain its original key; economic dedupe does not discard required diagnostic observations (§6.3.2). |
| ST.frontier | Scoped committed-prefix head and applied prefix | FN.MSG; no specific certified frontier in evidence | NEW | Existing-edge technical transport; Lifecycle append/Portfolio consume | B2 primitive; B8C/B10 integration | TX.frontier | Head and append commit together; reconstruct complete prefix, never cached best effort. |
| ST.config | Set/Position/Portfolio attempt and research configuration pins | FN.EPOCH/FN.PIN/FN.COOLDOWN/FN.RESEARCH | EXTEND | Each configuration-owning block | B5B/B7A/B8C; B0 new defaults | TX.set/TX.opportunity/TX.hold | Identity/version/digest and pinned duration immutable; no latest reload for started work. |
| ST.scope | COINS revisions and Set formation epochs | FN.SCOPE/FN.EPOCH | EXTEND | Portfolio revisions; Set epochs | B8A/B5B | TX.scope/TX.set | Known same revision conflict before stale suppression; unfinished epoch closure does not terminate pending monitor. |
| ST.facts | Accepted Portfolio/Market request/response/pages/source history | FN.FACT/FN.API | EXTEND | Requesting/accepting owner; API factual normalization | B3; Set assembly B5B | TX.preflight/TX.facts | Complete accepted identity/content/presence history, exact lookup indexes and raw challenges restored. |
| ST.setcalc | Set populations, work results and current assembly eligibility Keep formation_trigger_evidence and classifier_evidence independently bound/evaluable inside this same Set state; no trigger-to-classifier availability edge. | FN.FACT/FN.CAS; canonical analytical state absent | NEW | Set | B5A kernels/checkpoint format; B5B handler assembly | TX.setcalc/TX.set | Pin all source members/manifests; contradiction blocks new analysis but not rewrite frozen output. AT-NR-068-CF preserves both branches on deterministic replay. |
| ST.atr15 | F-003 authoritative 15m seed/checkpoint ancestry | FN.FACT/FN.CAS; no canonical ATR series ledger | NEW | Set | B5A; B5B input/commit integration | TX.setcalc | Exact work values/accepted source ancestry, original anchor and last processed identity; one progression per candle. |
| ST.local5 | Separate F-004 local 5m state | FN.FACT/FN.CAS; not F-003 15m state | NEW | Set | B5A; B5B integration | TX.setcalc | Independent timeframe/seed/member identity, exact Q36 values; no cross-series substitution. |
| ST.setevents | Trigger evaluations/transitions/windows/consumption | FN.SCOPE/FN.EPOCH plus justified missing records | NEW | Set | B5B | TX.set | Original event order/deadlines/consumption bound to epoch; duplicate source never retriggers. |
| ST.references | Matched producer-side role/binding/level/occurrence evidence | Existing scope/factual/config infrastructure; missing canonical result linkage | NEW | Set | B5B | TX.set | Concrete references only at governed time; Position cannot recreate thesis bindings. |
| ST.setresults | Final MATCHED cycle/result and exact MARKET_HANDOFF | Existing registry/FN.MSG; producer state missing | NEW | Set | B5B | TX.set | Result/frozen record/handoff and consumed events share commit; one immutable result per cycle. |
| ST.frozen | Frozen F-013 condition record | FN.CAS/config/evidence, no canonical record in audit | NEW | Set | B5B creates; B6 reads | TX.set | One condition_record_id also referenced by frozen_condition_record_id; retain configured condition IDs. |
| ST.monitor | F-013 activation, four-state evaluation, sticky/deferred requirement | FN.SYNC reused for placement/terminal; monitor record absent | NEW | Set | B6; actual native integration B9 | TX.monitor | Original entry key; first time/reason/optional presence; no recovery withdrawal or terminal resurrection. |
| ST.cancel | Set immutable signals; Lifecycle conditional receipt/cancel progress NR-152 adds actual Lifecycle request/cause/terminal/race observations, with existing Set signals unchanged. | Set requirement absent; existing Lifecycle submit/reconciliation/close facilities | EXTEND | Set signal record; Lifecycle separately owns receipt/cancel | B6 Set; B9 Lifecycle | TX.monitor/TX.cancel | Cause-specific signal IDs; both causes join same original-entry native intent; exact remainder/tombstone. One native intent can have multiple causes; replay cannot count them as extra native cancels. |
| ST.position | Initial Position opportunity/geometry/config binding; NR-153/154 RPT-ENTRY/RPT-TP full original candidate/selection/reason/raw-rounded metric and report-lineage evidence (§6.4.3) | FN.PIN; initial handler/result extension required | EXTEND | Position | B7A | TX.opportunity | One immutable cycle/decision/geometry; later grant cannot reselection or repin. Preserve complete actually evaluated versus unvisited candidate membership, source pins and original age/metric evidence on success and rejection; reports cannot overwrite it. |
| ST.grants | Immutable non-reserving grant Retain P-GRANT-LIFE consumption/actual-terminal-resolution observations beside, never inside a rewritten immutable grant payload (NR-151). | FN.GRANT | EXTEND | Portfolio | B8B issue; B8C consumption/rejected-construction observations; B9/B10 proven terminal projections | TX.grant/TX.hold/TX.acceptance/TX.receipt (owner-local observation membership only) | Same initial approval returns same grant; no reserve or expiry-based remint. Original consumed/closed operational cutpoints and causes survive; unresolved work gains no invented closure. |
| ST.construction | F-011/F-012 outcome and retained exact work evidence | FN.CONSTRUCT | EXTEND | Position | B7B | TX.construction | Immutable outcome including failure; A rational retained separately from H; no success IDs on reject. |
| ST.spec | Immutable full ORDER_SPEC/digest | FN.SPEC | EXTEND | Position publishes; Lifecycle consumes | B7B/B9 | TX.construction/TX.native | One spec with successful construction+two outboxes, exact binding and immutable bytes. |
| ST.authorization | SUBMIT_AUTHORIZED and consumed grant linkage NR-151 retains first Portfolio authorization/H-booking evidence; NR-152 separately retains Lifecycle receipt/first-native-use timestamps, with no second authority. | FN.AUTH | EXTEND | Portfolio publishes; Lifecycle consumes | B8C/B9 | TX.hold/TX.native/TX.owner (Lifecycle first intake) | One exact H/spec/digest authorization; duplicate cannot hold or create again. Original authorization identity/payload unchanged; receipt and consumption are distinct cuts. |
| ST.holds | H hold, slots, attempt pins and commitment transfer NR-151 P-TRANSITION history retains exact per-tranche before/after buckets, slots, timing and release/never-held-surplus distinctions. | FN.AUTH/FN.PORT/FN.COOLDOWN | EXTEND | Portfolio | B8C; native projection B9; final release B10 | TX.hold/TX.acceptance/TX.closeretention/TX.receipt | Book H once; pre-close residue and fixed closing retention; no release from physical flatness. No duration, utilization or diagnostic delta can authorize a release. |
| ST.portfolio | Account state, capacity and four capital buckets; separate live current_portfolio_equity, daily_realized_pnl, unrealized_pnl and total_pnl NR-151 complete P-DECISION/P-STATE/P-TRANSITION/P-RECON history includes unavailable/denied outcomes, all evaluated gate results/reasons and original basis; read-only counters derive from retained events. | FN.PORT | EXTEND | Portfolio | B8A/B8B/B8C/B9/B10 | TX.scope/TX.hold/TX.acceptance/TX.receipt/TX.grant/TX.day/TX.owner; TX.closeretention/TX.frontier only with underlying effect | Factual liabilities and pending reconciliation not erased by stale status or restart. Live equity/unrealized facts and capital flows remain separate from the fixed ST.day base; daily_realized_pnl retains its A-009 immutable-FINAL day scope. Denials and all secondary reasons restore without forcing a new capital-state revision or double-counting. |
| ST.day | ACCOUNTING_DAY_V1 accounting_day_id, persisted resolved local boundary instants, one fixed daily_portfolio_base, exact boundary evidence or complete reconstruction basis, A-009 daily realized result state, configuration/latch history, receipt/day-posting relationship and rollover_state | FN.PORT/FN.CAS; FN.LEGDAY is incompatible authority | NEW | Portfolio | B8A state/gates; B10 real result integration | TX.day/TX.receipt | Restore the same immutable day identity/boundaries/established base and its exact evidence or reconstruction basis. Preserve receipt/day/latch history; disabled does not clear latch. Missing new-day boundary proof leaves rollover_state=RECONCILING and blocks new exposure, never borrowing the prior base. Rollover creates a separate day; late FINAL posts once only to its immutable historical day without changing either established base. Live metrics are not a second denominator. |
| ST.cooldown | Attempt-pinned duration and accepted origin/integrity Retain NR-151 block observations against the original cooldown evidence/binding in Portfolio history, not only the latest cooldown value. | FN.COOLDOWN/FN.PORT | EXTEND | Portfolio | B8A/B8C; Lifecycle evidence B9 | TX.hold/TX.acceptance | First authoritative origin unchanged; unresolved accepted-time integrity blocks even after apparent duration. No diagnostic observation restarts the cooldown. |
| ST.submission | Joined start, durable create intent/client/native binding NR-152 extends complete L-SUB attempt/cutpoint history and distinct L-AUTH received/consumed observations; mutable last_* fields alone are insufficient. | FN.START/FN.SUBMIT | EXTEND | Lifecycle | B9 | TX.native/TX.acceptance/TX.owner (first intake metadata) | Intent before side effect; ambiguous create uses original ID; no second create after terminal tombstone. Each captured attempt and original consumption cutpoint replays once without native reuse permission. |
| ST.sync | Lifecycle placement and terminal return to Set Retain NR-152 original terminal-return publication event/outbox/timestamp separately from native terminality and Set receipt. | FN.SYNC | EXTEND | Lifecycle producer; Set projection | B6 typed intake; B9 actual publication | TX.placement/TX.monitor | Existing mechanism only; terminal-first placement reorder cannot revive monitor. A later sync/current row cannot replace the original publication record/time. |
| ST.nativefacts | Accepted hard facts/native fields/executions/raw profiles NR-152 links retained L-ARRIVAL classifications to exact factual/source history; raw capture is not accepted native authority. | FN.API/FN.NATIVE/FN.RECON | EXTEND | Lifecycle acceptance | B3 normalized paths; B9 owner records | TX.preflight/TX.facts | Per-field proven source histories; complete raw accepted content and aliases, not latest-row reconstruction. Known-content preflight still precedes ordinary duplicate/stale suppression. |
| ST.acceptance | Entry acceptance-integrity observations/resolutions/tombstones Retain NR-151 Portfolio projection cutpoints separately from NR-152 Lifecycle factual acceptance/fill observation history. | FN.SUBMIT/FN.RECON/FN.COOLDOWN | EXTEND | Lifecycle authority; Portfolio projection | B9; B8C consumer interfaces | TX.preflight/TX.acceptance | All accepted revisions including CLEAR/CONFLICT/RESOLVED; changed older content restores block without moving origin. No consumer timestamp substitutes for original factual accepted_at. |
| ST.reconcile | Order/native reconciliation and terminal tombstones NR-152 retains full episode/failure/recovery-correction and duplicate/out-of-order/manual observation history; NR-151 Portfolio episodes remain in ST.portfolio, not this foreign owner table. | FN.RECON/FN.SUBMIT/FN.SYNC | EXTEND | Lifecycle; each consumer own projection | B9; B10 financial recovery-observation integration only | TX.cancel/TX.close/TX.partition/TX.owner/TX.facts/TX.acceptance; B10 financial observations use their existing owner transaction | Factual executions dominate statuses; tombstone only after known-content check; immutable receipts. Original episodes, capture/classification bases and completed/failure cutpoints hydrate before processing; no count from unchanged restart. |
| ST.protection | Historical children plus separate current live proof NR-152 retains verification checks/failures and separate sibling cancellation start/confirmation per exact child/generation/proof. | FN.CLOSE/FN.RECON/FN.NATIVE | EXTEND | Lifecycle | B9 | TX.protection/TX.native/TX.close for existing child-operation start | New complete omission invalidates current proof; historical mapping survives; old query cannot restore live authority. Diagnostics cannot restore current live proof or infer terminal confirmation. |
| ST.close | One close intent, causes, child budget and proof revision NR-152 preserves actual close/remainder-race observations and post-intent entry-execution membership beside existing intent/child/proof history. | FN.CLOSE | EXTEND | Lifecycle | B9; terminal transition B10 | TX.close/TX.final/TX.acceptance for associated fill observation | CAS/acquire-or-join; stable child identity; all causes retained; no competing reduction authority. Convergence does not erase race/member evidence; diagnostic sums add no reduction authority. |
| ST.attribution | Native observations/manifests/source partitions/quantity receipts | FN.RECON/events; missing complete proof/receipt extensions | EXTEND | Lifecycle quantity authority; Portfolio independent projection | B9 | TX.partition | Zero-effect staging; global source binding/disjoint slices; application+source consumption+receipt atomic. |
| ST.financial | Accepted immutable raw financial core/aliases/component ledgers NR-152 read-only entry/exit fee observations derive from these exact source/components/receipts, not another ledger. | FN.API/FN.RECON; legacy SQLite not canonical | NEW | Lifecycle | B10; B3 normalization interfaces | TX.preflight/TX.facts/TX.cashflow | Complete source and alias histories; exact source-member applicability; no dual authoritative financial ledger. Source alias dedupe/finality remain unchanged. |
| ST.coverage | Accepted coverage/basis/allocation proof revisions and indexes | FN.RECON/FN.CAS; complete financial certificate model missing | NEW | Lifecycle | B10; B3 raw-preflight interfaces | TX.preflight/TX.facts/TX.final | Exact Y02 keys, full content/presence/source-member sets and permitted unique fallback indexes restored. |
| ST.funding | A-004 source/eligibility/weights/raw/base/residue/allocation receipt NR-152 reuses the retained A-004 basis and allocations for funding diagnostics; no new allocation algorithm. | Legacy rows inadequate; canonical owner UoW reused | NEW | Lifecycle | B10 | TX.funding | One signed conserved source and frozen algorithm version; aliases no second funding. Observability never reallocates a source. |
| ST.final | A-002 immutable FINAL, current proof and S-004 CLOSED NR-152 gross/net/funding and final-close diagnostic views reference the same immutable result/proof. | No canonical final ledger; FN.CLOSE/FN.RECON reused | NEW | Lifecycle | B10 | TX.final | One result/tranche with immutable proof/timestamps/outbox; late challenge separate incident, not rewritten result. No diagnostic correction edits FINAL or creates a provisional full-tranche result. |
| ST.receipts | Portfolio result receipt, first delivered_at, day post/release NR-151 terminal release/grant-resolution observations and historical utilization evidence accompany Portfolio's existing receipt effect. | No canonical result receipt ledger; FN.PORT/FN.MSG reused | NEW | Portfolio | B10 | TX.receipt/TX.frontier | Unique result_id and tranche_id; exact content equality; historical posting once, no duplicate wallet credit. Same result/tranche receipt keeps original time and once-only release/diagnostic history. |
| ST.incidents | Raw challenges/quarantine; parent-linked incidents and Portfolio scope blocks NR-151/NR-152 observation links reuse actual required incidents; a benign duplicate observation is not a new incident class. | Schema/owner-state scaffolding; complete incident consumer absent | NEW | Each intake retains challenge; Lifecycle publishes financial/native parent incident; Portfolio owns block projection | B3/B5B/B9/B10 by domain | TX.preflight/TX.incident/TX.frontier | Separate incident/result dedupe; history before stale suppression; no money inversion or automatic incident clear. Separate diagnostic capture cannot suppress a real challenge or clear an existing block. |
| ST.research | Research/demo diagnostics and authorized governance evidence; NR-153/154 immutable report-definition/configuration pins, source/cohort manifests, member/path data, report results and sensitivity evidence | FN.RESEARCH/FN.LEGACY: existing research_pin_payload/research_run_pin_payload; SQLite ResearchStore and OperatorStateStore; existing historical cache organization; separate PostgreSQL ResearchPromotionGovernanceStore for promotion-request state/outbox only. Missing append-only diagnostic datasets/reports extend ResearchStore (§6.4.1); no claimed existing report table | EXTEND within existing ResearchStore; preserve existing records and storage roles | Research diagnostic persistence only; Set/Position/Lifecycle facts keep their original owners | B0 pin defaults; B3 immutable diagnostic archive/import; B12 report assembly; B13 isolation/verification. Source owner retention remains B7A/B9/B10 | NONE in canonical business TX taxonomy; independent SQLite diagnostic transactions and non-authoritative file staging (§7.7), never a PostgreSQL/SQLite distributed commit | Same report definition/query/configuration/source manifest returns identical semantic content and retained identity; new evidence/pins create a new immutable report, old reports stay unchanged; complete source/manifest restoration precedes calculation; no canonical S-005 state or report feedback. |
| ST.legacy | Legacy SQLite accounting/day and paper/demo execution | FN.LEGACC/FN.LEGDAY/FN.LEGACY | FENCE_LEGACY | Legacy/demo only | B1/B5A/B5B/B7A/B7B/B9/B10/B12/B13 as adjacent surfaces | NONE | No canonical read fallback, dual write, pseudo-atomic bridge or relabeling ClosedTradeResult as FINAL. |

### 6.1 Legacy accounting and migration decisions

`FuturesAccountingStore` and `DailyLossStore` are SQLite legacy infrastructure in the supplied evidence. They are not PostgreSQL financial finality, Portfolio receipt or canonical A-009 state. The legacy partial-close result and UTC daily-loss service stay isolated. A compatible pure helper may be reused only after independent tests prove full semantic equivalence for inputs, signs, rounding, status and output—not because its name resembles the required formula.

A canonical source/funding/result ledger missing from the existing PostgreSQL implementation is added within Lifecycle’s existing owner transactions; a missing receipt/day ledger is Portfolio-owned. Neither is dual-written as a second authoritative SQLite ledger. There is no SQLite+PostgreSQL atomic-transaction claim and no legacy “fallback” on recovery failure.

Future schema changes are forward-only extensions after checking the actual current repository/deployment migration chain. Existing applied migrations and immutable trading evidence are protected. Additive backfills preserve original identity/content/provenance; unknown historical data stays explicitly unavailable, not fabricated. Rollback disables the affected runtime/authority and uses a reviewed forward correction rather than deleting accepted trading history.

### 6.2 NR-151 — Portfolio status, gate results and retained diagnostic history

#### 6.2.1 Source boundary, classification and existing-record grounding

Frozen `methodology/PORTFOLIO_RULES.md` §§51–53 L1540–L1591 and §63 L1741–L1777 require this evidence. The list is implemented by the existing Portfolio owner, not B12 infrastructure counters, ResearchStore or a new allocator. This is retention/visibility of source-defined decisions, not new permission to trade, a new metric threshold or a new capital formula.

The classification in §6.2.3 identifies how each obligation is satisfied: **DIRECTLY_PERSISTED** denotes the named retained field; **DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS** requires the full immutable named basis; **DERIVABLE_FROM_EVENT_HISTORY** requires all qualifying event members/order/cutpoints; **ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED** identifies a missing field/event to add inside the existing owner-state/history representation. Derivable does not mean the complete history is already implemented. Every proposed addition below is explicitly a planning extension, not a claimed existing Python symbol, SQL table or wire field.

The following P-* names are documentation aliases for records/views within existing ST/FN families, not additional state families or new stores:

| Record alias / retained basis | Actual snapshot support and required extension | Owner / canonical location |
| --- | --- | --- |
| P-GRANT | Existing `CapitalGrantStore.issue`, `persistence/capital_grant_store.py` L39–L101, persists immutable `payload_json`/digest and `capital_and_limits.capital_grant_id`, decision/cycle/result, `created_at`, `as_of`, `portfolio_state_revision`, `requested_capital_per_tranche` and allowed facts. Reuse these exact fields; never update issue payload to carry later diagnostic timestamps. | Portfolio / ST.grants / FN.GRANT |
| P-AUTH | Existing `SubmitAuthorizationStore.authorize`, `persistence/submit_authorization_store.py` L42–L128, persists immutable authorization payload/digest and grant/construction/spec bindings. Reuse `submit_authorized.authorization_id`, `authorized_at`, `held_committed_capital` and `capital_grant_id`. B8C already must compose this with actual H/slot booking; the current builder alone does not prove that composition. | Portfolio / ST.authorization and ST.holds / FN.AUTH |
| P-STATE | Existing `PortfolioStateStore.record` L32–L92 retains `triggertrade_portfolio_state_revisions` separately from the mutable current pointer. `portfolio_state.py` L90–L127 exposes `portfolio_id`, `revision`, `evidence_id`, `as_of`, `health`, one `reason_code`, global/coin buckets and committed-tranche counts. The existing single reason is not the full gate history. Retain references to the evaluated rules binding, exact caps/slot limits/day/cooldown/fact basis alongside the corresponding historical revision. | Portfolio / ST.portfolio, ST.config, ST.day, ST.cooldown / FN.PORT/FN.CAS |
| P-DECISION | **ADDITIONAL** immutable event content in ST.portfolio history using FN.PORT/FN.CAS and the existing owner UoW: existing scope/decision/construction/input identity, stage, owner evaluation identity, evaluated state revision/configuration/facts, captured operational time, internal decision status, complete gate_results, all evaluated reasons, selected primary reason and computed requested amount when actually available. Include blocked and unavailable outcomes without fabricating grant/authorization IDs. A diagnostic event does not itself advance a capacity revision or reserve anything. | Portfolio / ST.portfolio; branch-specific links in ST.grants/ST.holds |
| P-TRANSITION | **EXTEND** existing Portfolio commitment/authorization/receipt history with the original event/receipt identity, exact tranche/grant/authorization binding, before/after four buckets and slot counts, source-effective time where proven, first Portfolio recorded time, cause/reason, and same-time exact cap/configuration evidence. Retain per-tranche transitions as well as aggregate P-STATE revisions; a current aggregate alone cannot establish historical durations. | Portfolio / ST.holds, ST.portfolio, ST.cooldown, ST.receipts; FN.PORT/FN.AUTH/FN.COOLDOWN |
| P-GRANT-LIFE | **ADDITIONAL** immutable linkage observations in existing ST.grants/ST.portfolio history: grant consumed cutpoint bound to the successful B8C P-AUTH; terminal opportunity/attempt-resolution observation and its reason/cause, if one is actually established. This is not mutation of P-GRANT, a new grant state machine, an expiry or a prerequisite for consuming the frozen grant. | Portfolio / ST.grants with ST.holds/ST.receipts links |
| P-RECON | **ADDITIONAL** complete Portfolio health/reconciliation episode history in ST.portfolio: episode key bound to its first existing causal owner evidence identity, starting state revision/time/reason, each request/response/evidence basis, completion time and failed-attempt reason where applicable. Retries while the same episode is unresolved retain that episode key; failure history and later success coexist. | Portfolio / ST.portfolio; ST.facts/ST.day where the underlying recovery belongs |
| P-CONSTRUCT-VIEW | Reuse the **already required** immutable Position ST.construction F-011 work record (C,T,Q,N,exact A,H; §5/§8/B7B) and its existing `construction_result_id`/grant/spec bindings. Target T is Position-owned and absent from the current Portfolio confirmation's listed scalars. The Portfolio-facing **read-only audit/visibility composition** displays that retained producer value through exact immutable lineage; no Portfolio trading handler reads a foreign mutable table, consumes a new ORDER_SPEC edge or recomputes F-011. No additional Position production, wire field, or new service is required. | Position retains T; the existing diagnostic/audit query composes immutable evidence only. Portfolio's own decisions still use existing messages exclusively. |
| P-TRANSPORT | Existing immutable outbox/inbox payloads and keys in `durable_messages.py` L25–L59/L68–L129; retain required publication/intake cutpoints rather than infer them from a mutable latest status or a pruned queue. Technical metadata is evidence, never a substitute for P-DECISION or P-TRANSITION. | Existing ST.transport, with Portfolio-local references |

For every derivation, retain the identified original records, complete member sets, exact fields, event identities, source/configuration bindings and observation-time basis; restart loads those records, not `get_current()` alone. No purge policy is introduced. A cache/projection may be rebuilt, but must not be the sole retained source. Historical missing evidence remains explicitly unavailable, not backfilled with a current snapshot or guessed timestamp. No diagnostic calculation may alter Portfolio gates, conceal negative free capacity, normalize allocations, rebuild another owner's formula or authorize a release.

#### 6.2.2 Gate, identity, timing and economic semantics

Internal Portfolio decisions remain `ALLOWED`, `BLOCKED`, `UNAVAILABLE`; external COINS and CAPITAL_AND_LIMITS shapes are unchanged. Retain the following complete gate-result content for every gate actually evaluated, preserving applicable presence/nullability and dependency status:

```text
gate_id
status = PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
configured_value
calculated_value
operator
reason_code
dependency_reason
```

A disabled/not-applicable or dependency-unavailable gate is not fabricated PASS. Missing value is not numeric zero. The frozen per-gate algorithm determines status, inputs and applicable reason; this mapping adds no global FAIL-versus-UNAVAILABLE precedence or new reason-code taxonomy. Retain the complete collection of evaluated gate outcomes/reasons even when one primary reason is selected. Primary selection never deletes secondary reasons or forces previously unevaluated gates to execute. Preserve the original primary selection and original ordered/identity-bound result collection on replay.

P-DECISION is uniquely bound to the actual owner evaluation instance: existing causal input identity and stage, original opportunity/construction/scope lineage, accepted Portfolio state/configuration/evidence basis and original persisted evaluation identity. Duplicate processing of that same evaluation reuses its outcome and full reasons; same identity with altered content is conflict. A genuinely new governed refresh/evaluation under new authoritative state can create a new diagnostic evaluation, but cannot rewrite an old denial, mint a replacement for an issued grant, restart a terminal opportunity or turn an already issued grant into a reservation. Waiting or temporarily unissuable grants acquire no TTL.

`capital grant consumed_at` is the first Portfolio **TX.hold** cutpoint that actually consumes the grant and books H with its authorization; the immutable authorization's `authorized_at` plus retained consumption binding supplies it. It is not grant delivery, Position calculation, native dispatch or `entry_accepted_at`. `capital grant closed_at` is retained as a separate operational observation of an **actually established terminal resolution of the linked opportunity/attempt**: a governed construction rejection without consumption, proven terminal no-create/zero-fill path, or filled-tranche terminal Portfolio receipt as applicable. Keep resolution kind, original causal event/effective time and first Portfolio recorded time. Consumption alone does not invent a later terminal fact. A booking denial, unavailable evidence, receipt of no order, elapsed time or merely flat exposure does not manufacture closure; if no terminal resolution exists, closed_at remains absent/unavailable with the unresolved basis. This diagnostic field neither changes grant use semantics nor releases capital.

For `released rounding delta`, the older short §63 label cannot override §44 L1454–L1466, P11 or NUMERIC_POLICY §7 L90–L92. Retain distinct exact observations: requested C, booked H, **never-held surplus C−H**, actual authorized release amount/reason, and the source-defined pre-close apportionment operands/rounded outputs/residue where relevant. There is **zero grant-surplus release at acceptance**: the same H is reclassified. Expose that zero actual release and separately label C−H as never held; never invent a release posting for the surplus or call the whole zero-fill release a rounding adjustment. Any rounding-attributable diagnostic must point to an actual named numeric-policy operation and its retained exact operands/output, not an invented rounding formula. Missing attribution is unavailable, not guessed. During close retention there is no proportional release.

Timing projections explicitly distinguish proven factual effective timestamps from owner operational capture timestamps. Operational hold/reserve/reconciliation durations use paired first committed owner cutpoints for the same episode/interval; factual acceptance/execution time remains separately available. An open interval has an explicit query `as_of` and remains open, not falsely completed. No diagnostic elapsed time becomes a trading TTL or changes cooldown, accounting day or finality.

#### 6.2.3 Complete Portfolio observation map

Each P-number is a subitem of NR-151, not a new normalized requirement. Exact counts are over the selected, explicitly identified reporting scope/window and distinct qualifying **owner events**, never transport retry attempts. A frequency view retains numerator, denominator/exposure-window definition and covered event IDs; source §63 does not prescribe a new default reporting window. Known empty counts can be zero; missing history or a zero ratio denominator is reported explicitly unavailable/not applicable. Store exact numerator/denominator values and apply no new gate quantizer.

| Item / frozen observation | Classification | Exact retained source / deterministic derivation and restart basis | Producing checkpoint / existing transaction |
| --- | --- | --- | --- |
| P01 — canonical internal decision/status | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-DECISION.internal_status is the actual ALLOWED/BLOCKED/UNAVAILABLE result for its stage and basis; replay retains the same outcome including denied stages. | B8A TX.scope/TX.day; B8B TX.grant; B8C TX.hold |
| P02 — complete gate_result fields | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-DECISION.gate_results contains all seven fields above with source-defined presence/dependency semantics, exact configured/calculated values and retained input bindings. | B8A/B8B/B8C in the gate's same existing transaction |
| P03 — all evaluated reasons and primary reason | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-DECISION complete gate-result/reason collection plus primary selection; single current PortfolioState.reason_code is insufficient. Do not collapse multi-reason history into one string. | B8A/B8B/B8C; TX.scope/TX.day/TX.grant/TX.hold |
| P04 — Coins OPEN / CLOSE transitions | DERIVABLE_FROM_EVENT_HISTORY | P-STATE and retained COINS payload symbol/scope_revision/action/configuration plus original P-TRANSPORT publication. Count real action transitions against preceding retained action; idempotent resend is not another transition. | B8A TX.scope |
| P05 — Capital and Limits grants / blocks | DERIVABLE_FROM_EVENT_HISTORY | Distinct P-DECISION grant-stage outcomes; issued grants join P-GRANT by actual initial decision/cycle. BLOCKED and UNAVAILABLE remain distinct; no grant ID is fabricated for a denial. | B8B TX.grant |
| P06 — gate failure frequencies | DERIVABLE_FROM_EVENT_HISTORY | Count qualifying P-DECISION `(evaluation,gate_id,FAIL)` members once, grouped by gate and actual reason; retain evaluated/status population for the selected denominator. UNAVAILABLE is not silently FAIL. | B8A/B8B/B8C; corresponding gate transaction |
| P07 — cooldown block frequency | DERIVABLE_FROM_EVENT_HISTORY | P-DECISION reason COIN_COOLDOWN_ACTIVE and its exact retained ST.cooldown origin/duration/boundary basis; count distinct blocked owner evaluations in the explicit cohort. | B8A TX.scope; B8B TX.grant; B8C TX.hold |
| P08 — daily loss block frequency | DERIVABLE_FROM_EVENT_HISTORY | P-DECISION reason DAILY_LOSS_LIMIT_REACHED and original ST.day/base/latch/configuration references; count blocked evaluations, not FINAL delivery retries. | B8A TX.scope/TX.day; B8B TX.grant; B8C TX.hold; actual day/receipt facts B10 |
| P09 — global cap block frequency | DERIVABLE_FROM_EVENT_HISTORY | P-DECISION actual global-cap failure and exact free/cap/requested-or-booked H basis; count once per failed evaluated gate. Retain INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE or actual applicable frozen reason. | B8A/B8B/B8C; TX.scope/TX.grant/TX.hold |
| P10 — coin cap block frequency | DERIVABLE_FROM_EVENT_HISTORY | P-DECISION per-coin gate result, exact coin commitment/cap and source-defined reason; distinguish exhausted free-coin capital from a later H that exceeds remaining coin capacity. | B8A/B8B/B8C; TX.scope/TX.grant/TX.hold |
| P11 — slot utilization | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-STATE.global/coin committed_tranches and the exact historical rules max_open_positions/max_positions_per_coin. Expose count and limit, or their exact ratio, per retained revision; all unresolved holds/closing-retained slots remain included. | B8A TX.scope; B8C TX.hold; B9 TX.acceptance/TX.closeretention; B10 TX.receipt |
| P12 — capital utilization | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Sum P-STATE global held+reserved+filled+closing_retained once; pair with that revision's governed global_position_cap. Preserve negative free/excess observations rather than clamp; no equity/base substitution. | Same Portfolio state-producing transactions as P11 |
| P13 — coin allocation utilization | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Same four-bucket sum for the exact coin and retained coin_allocation_cap/configuration at that revision; global cap and per-coin targets remain independent. | Same Portfolio state-producing transactions as P11 |
| P14 — submission hold duration | DERIVABLE_FROM_EVENT_HISTORY | P-TRANSITION first actual H booking operational time to first actual hold exit/reclassification/proven terminal release for that authorization; keep both cutpoints/cause and fact-effective times. Missing endpoint remains open. | B8C TX.hold; B9 Portfolio TX.acceptance; B10 TX.receipt if applicable |
| P15 — reserved capital duration | DERIVABLE_FROM_EVENT_HISTORY | Retained P-TRANSITION intervals in the reserved bucket, including quantity/amount changes and actual exits to filled/closing-retained/release. Restore every interval, not latest RESERVED state. No duration-based release. | B9 Portfolio TX.acceptance/TX.closeretention; B10 TX.receipt |
| P16 — requested tranche capital | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-GRANT.requested_capital_per_tranche for issued grants; P-DECISION exact evaluated candidate C for denied evaluations where computed. Absent computation remains unavailable; never synthesize a grant. | B8B TX.grant; retained scope candidate at B8A TX.scope |
| P17 — actual committed capital | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-AUTH.held_committed_capital and accepted confirmation approved_actual_committed_capital identify approved H; P-TRANSITION/P-STATE give later current four-bucket commitment. Label these distinct, never exchange margin or mathematical F-011 A. | B8C TX.hold; B9/B10 Portfolio projections |
| P18 — target order notional | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-CONSTRUCT-VIEW displays the exact already retained Position T from ST.construction, joined by immutable construction/grant/spec identity. The Portfolio decision path must not calculate C×leverage or import a Position kernel to supply this diagnostic. An unsuccessful construction without T is explicitly unavailable. | Existing B7B TX.construction retains T; B8C read-only audit composition verified locally, B13 integrated |
| P19 — actual order notional | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Portfolio's retained CONSTRUCTION_RESULT.approved_economics.approved_actual_order_notional, bound to construction/grant/spec digest; copy exact N, not an Entry/quantity recomputation. Factual executed notional is separately Lifecycle-owned. | B8C TX.hold/retained construction intake |
| P20 — reconciliation count / frequency | DERIVABLE_FROM_EVENT_HISTORY | Distinct P-RECON episode starts with original scope/reason and selected reporting interval. Repeated request/delivery within the same episode does not create another episode. Preserve failed attempts as separate observations, not completed episodes. | B8A TX.scope/TX.day/TX.owner; B9/B10 Portfolio local reconciliation transitions |
| P21 — concurrency conflicts | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-DECISION or retained attempt failure keyed to the original competing evaluation/attempt, state revision/lock outcome and CONCURRENT_CAPACITY_CONFLICT where source-applicable. Logical capacity denial is distinct from a transient database retry; §7.6 preserves captured technical failures without any partial booking. | B8C TX.hold; existing TX.owner capture only after an aborted technical attempt if necessary |
| P22 — missed opportunities due to capacity | DERIVABLE_FROM_EVENT_HISTORY | P-DECISION blocked capacity result linked to original position_decision_id/decision_cycle_id and, when present, construction_result_id. Query distinct opportunity IDs plus all denial evaluations/reasons; a repeatedly denied same opportunity is not several unique missed opportunities. | B8B TX.grant; B8C TX.hold |
| P23 — capital grant created_at | DIRECTLY_PERSISTED | Existing immutable P-GRANT.capital_and_limits.created_at; retained issue payload/digest. Do not replace with replay or observation time. | B8B TX.grant |
| P24 — capital grant amount | DIRECTLY_PERSISTED | Existing P-GRANT.requested_capital_per_tranche (C), exactly once under capital_grant_id. It is not held capital. | B8B TX.grant |
| P25 — capital grant consumed_at | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-AUTH.authorized_at plus P-GRANT-LIFE grant-consumption binding to the successful TX.hold event, as defined in §6.2.2. Absent successful hold means not consumed; native acceptance is not the cutpoint. | B8C TX.hold |
| P26 — capital grant closed_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-GRANT-LIFE first actual terminal-resolution observation, source/cause/effective time and Portfolio recorded time; preserve rejection/no-create/zero-fill/filled-terminal branch identity separately. No guessed closure for unavailable/denied/unresolved work. | B8C existing rejected-construction TX.hold outcome; B9 Portfolio TX.acceptance for proven zero-fill/no-create; B10 TX.receipt for filled terminal outcome |
| P27 — hold created_at | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-AUTH.authorized_at and matching committed H/slot P-TRANSITION establish first booking, not the earlier non-reserving grant time. | B8C TX.hold |
| P28 — hold amount | DIRECTLY_PERSISTED | Existing P-AUTH.held_committed_capital, composed with actual ST.holds amount in B8C. Exact copied H; do not add C−H. | B8C TX.hold |
| P29 — actual reserved capital | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | P-TRANSITION/P-STATE reserved_committed_capital for the actual post-acceptance/remainder state and original H basis. Full-fill-before-acceptance may leave no reserved remainder; preserve the factual branch. | B9 Portfolio TX.acceptance |
| P30 — released rounding delta | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | Retain C/H/never-held C−H, actual release event/amount, and exact named apportionment operands/output/residue per §6.2.2. Acceptance reclassifies H and releases **0** grant surplus. Show never-held surplus separately; do not invent a monetary release or a rounding rule. | B8C TX.hold; B9 Portfolio TX.acceptance; B10 TX.receipt only for the actual terminal release, not a new rounding action |
| P31 — reconciliation started_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-RECON first captured RECONCILING episode transition plus original causal factual/operational basis; repeated restarts cannot reset it. | B8A TX.scope/TX.day/TX.owner; B9/B10 Portfolio local projection/recovery transaction |
| P32 — reconciliation completed_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-RECON actual consistency-restored transition with complete evidence and operational time; no completion timestamp from timeout or partial refresh. | Same existing Portfolio transaction that establishes recovery |
| P33 — reconciliation failure reason | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | P-RECON immutable failed-attempt reason/content and evidence/response links, preserving earlier failures after eventual completion. No invented clear on valid-but-unrelated data. | Same existing Portfolio recovery/fact acceptance transaction, or TX.owner retained failure outcome |

P01–P03 derive from §§51–53; P04–P33 cover every §63 list item. The P-CONSTRUCT-VIEW exception is deliberately not a new Portfolio formula consumer: the immutable Position-produced T already exists in required construction evidence. Diagnostic composition never feeds that field back into a Portfolio gate or bypasses the existing business graph. The view must be read-only, must prove exact lineage, and must expose unavailable evidence rather than a guessed value.

#### 6.2.4 AT-NR-151 — mandatory owner-local acceptance cases

All cases run through the actual producing owner handler/store composition; tests derive outcomes from frozen predicates and retained event identities, not from a mutable dashboard snapshot. B8A fixtures cover only the foundational portions; B8B/B8C/B9/B10 implement their own producers before B11/B13 integration. Every case also checks the appropriate P01–P33 rows and full evidence round-trip.

| Case | Source-derived fixture/action | Required persisted/replay assertion | Local producer / review |
| --- | --- | --- | --- |
| 01 — multi-reason blocked grant | Valid initial APPROVE; free coin=100, remaining coin slots=2, hence C=50 under §17. Minimum tranche=100 and free global=40; both independently evaluable §18/§19 predicates fail. Other prerequisites permit evaluating both. | BLOCKED; retain MINIMUM_TRANCHE_CAPITAL_NOT_MET and INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE with complete exact gate results, one selected primary that is a retained evaluated reason, and no grant/hold/auth. Source does not require a new primary priority. Replay the same evaluation twice: one outcome, one contribution to each qualifying gate frequency, unchanged full reasons. | B8B; implementation/numeric/trading/persistence/replay/test |
| 02 — unavailable distinct from blocked | Required coherent Portfolio state/fact basis unavailable; no fabricated free-capital value. | UNAVAILABLE and actual dependency reason retained, not BLOCKED/FAIL or ALLOWED. No grant; repeated evaluation identity remains one unavailable outcome. A new governed recovered-state evaluation is separately retained without rewriting the first. | B8A/B8B |
| 03 — grant creation, consumption and terminal history | Source-valid grant and successful Position construction; later successful current H booking, then a source-proven terminal path. Exercise filled FINAL/Portfolio receipt and the separate zero-fill/no-create branch. | Original created_at/C, B8C consumed_at and separately proven closed_at/cause persist across restart; no acceptance-time substitution for consumption. Grant remains non-reserving before booking. Missing final proof leaves closed_at unresolved and preserves resources. | B8B creation; B8C consumption; B9/B10 terminal projections |
| 04 — global-cap missed opportunity | Reuse AT-NR-036 case 02: valid 80/60 configuration, global 590, H=20, cap600 and independently valid original grant. | Current booking denied since610>600; exact opportunity/construction/state/cap/H evidence retained after restart. No partial H/slot/auth/success outbox. No new unique missed opportunity from redelivery; all evaluated reasons remain available. | B8C |
| 05 — per-coin capacity | Reuse AT-NR-036 case03: global500→520<=600, SOL190→210>200, H20. Also test exhausted free coin under §22. | Distinct exact per-coin block evidence and appropriate frozen reason/status survive, independently of passing global gate; no resize/normalization. | B8A/B8B gate fixtures; B8C actual booking |
| 06 — cooldown block | Proven original accepted_at and pinned duration; evaluate strictly before the existing cooldown end, then use a genuinely new governed evaluation after the source boundary. | First COIN_COOLDOWN_ACTIVE block and original duration/evidence retained; duplicate does not count twice. Later eligibility never edits the blocked history or origin. | B8A/B8B/B8C as applicable |
| 07 — Daily Loss block | Proven day/base=1000, configured limit5%, eligible once-received FINAL total R_d=-50; exact inclusive A-009 boundary. | DAILY_LOSS_LIMIT_REACHED block/latch basis and day identity retained; historical result redelivery cannot inflate block counts or rebase the day. Use B8A fixture then actual B10 receipt in integration. | B8A/B8C; B10 factual receipt |
| 08 — concurrency | Two otherwise valid constructed attempts contend for the last currently available slot/capacity. Use real PostgreSQL serialization and retained attempt identities. | One books; the other retains the actual CONCURRENT_CAPACITY_CONFLICT or applicable current-capacity denial and evaluated basis, without partial success. Retrying the same captured conflict does not increment it again; a technical aborted attempt is not falsely counted as a second logical denial. | B8C; §7.6 aborted-attempt rules |
| 09 — rounding/never-held surplus | Source example C100, H90.666666666667, surplus9.333333333333. Accept the actual entry; separately use NUMERIC_POLICY §5 example H1,Q3,F1,R2 and terminal remainder cancellation. | Booking holdsH only; acceptance release from grant surplus=0, surplus remains distinctly never held. Pre-close filled0.333333333333/reserved0.666666666667; after terminal remainder, retained0.333333333334, reserved0, cumulative released_unfilled0.666666666666. Retain original exact operands/residue/cause; do not reuse apportionment to release during close. | B8C/B9; numeric review; B10 release/finality regression |
| 10 — reconciliation episode | Capture start t0, failed factual refresh with reason at t1, restored consistency at t2 under the same episode; repeat/restart between each event. | One episode, original started_at, completed_at only at t2, retained t1 failure and exact request/response links; operational duration=t2−t0; no inferred completion or loss of failed history. | B8A/B9/B10 Portfolio paths |
| 11 — utilization and immutable construction visibility | Retained historical revision has held20,reserved30,filled40,closing10, global cap200 and two slots occupied of four; next revision changes. Exact Position construction T is already retained under matched grant/construction/spec lineage. | Historical total100/cap200 and2/4 remain exactly reconstructible after restart/current changes; coin ratios use their own retained caps. Read-only audit displays producer T and confirmation N unchanged, with a trap against Portfolio F-011 invocation/recomputation or foreign mutable-state lookup. All four buckets counted once. | B8A/B8C/B9/B10 production; B13 integrated |
| 12 — PostgreSQL crash and identity | Fail before/after P-DECISION, history, authoritative state, required outbox and inbox writes on success and denial branches; retry captured input/evaluation identity and test changed-content conflict. | Precommit failure commits neither that owner outcome nor its observations. Postcommit retry restores identical status/reasons/times and counts once. A committed denial may contain diagnostic history but no success grant/H/slot/auth. Existing separately committed preflight challenges remain intact. All P01–P33 histories hydrate before new processing. | Every affected Portfolio checkpoint; B11/B13 verify, not first produce |

### 6.3 NR-152 — Lifecycle operational observations and audit visibility

#### 6.3.1 Existing support and complete retained bases

Frozen `methodology/ORDER_LIFECYCLE.md` §43 L1774–L1830 is the observation obligation; §40 L1666–L1693 supplies its visibility scope. Capture belongs to Lifecycle at B9/B10. “Research and diagnostics” in the chapter title does not transfer ownership to Research, SQLite, S-005, a new accounting block or a dispatcher.

The same four classification meanings and complete-history retention conditions in §6.2.1 apply. The L-* aliases below name projections/fields within existing logical states, not additional states, transaction mechanisms or Python classes. New fields/child-history entries are proposed additions, not claims that the snapshot already contains them.

| Retained basis alias | Actual snapshot support and precisely required extension | Owner / existing states |
| --- | --- | --- |
| L-SUB | `LifecycleSubmissionRecord`, `persistence/lifecycle_submission_store.py` L31–L58, already retains intent/auth/grant/spec/tranche/client identity, payload/digest, dispatch_attempts and selected **last** cutpoints. `_mark_dispatch` L286–L339 updates that latest state. Extend the same submission history to retain **every** stable dispatch_cutpoint_id/attempt, operation, original submitted/started time, definite/uncertain dispatch outcome and native response/provenance. Latest fields/counter alone cannot reconstruct latency or reason history. | Lifecycle / ST.submission / FN.SUBMIT |
| L-EVENT | Existing append-only `LifecycleOrderEventStore.append` L44–L104 and `list_for_tranche` retain event_id, variant/type, occurred_at, lifecycle_revision, tranche/lineage, exact payload/digest. Reuse this full history and the factual native/execution history already required by B9; no extra ORDER_EVENT fields are added for diagnostics. | Lifecycle / ST.acceptance, ST.nativefacts, ST.reconcile / FN.RECON |
| L-ARRIVAL | **ADDITIONAL** owner-local captured intake/observation metadata in existing ST.transport/ST.nativefacts/ST.reconcile history: durable arrival instance key, original raw input digest/reference, received/observed time, exact semantic evidence/message identity when recognizable, original classification basis and flags. Duplicate/out-of-order flags are retained per captured arrival, not inferred later from an economic inbox no-op. §6.3.2 defines identity and ordering. | Lifecycle-owned intake observation; existing technical transport carries metadata only |
| L-AUTH | Reuse exact accepted SUBMIT_AUTHORIZED payload and existing `InboxMessageRecord.received_at` (`durable_messages.py` L48–L59) for first durable Lifecycle intake. Add immutable first native-use or definitive terminal-no-create consumption cutpoint and its kind/proof. Actual native use requires the complete spec/auth/current hard/profile join; a proven terminal no-create consumption creates no native-use authority. Preserve original auth receipt even when spec arrives later. | Lifecycle / ST.submission, ST.authorization, ST.transport; Portfolio authorization unchanged |
| L-SYNC | Existing `LifecycleSetSyncStore.publish_from_order_event` L53–L105 joins sync state and exact Set-addressed outbox. Preserve original terminal event ID/revision, causal ORDER_EVENT identity and **first producer publication timestamp** from that outbox's immutable created_at. Latest sync state alone is insufficient after later events. Preserve separate dispatch/consumption cutpoints if present; none is an exchange terminal timestamp. | Lifecycle / ST.sync and ST.transport / FN.SYNC/FN.MSG |
| L-PROTECTION | Extend B9's existing historical owned-child/current-proof state with immutable verification failure observations (query/proof identity and failed predicate/reason), and each sibling cancellation's durable start plus separately proven terminal confirmation, with child/generation/intent/request/proof links. Do not replace current proof with diagnostics. | Lifecycle / ST.protection, ST.nativefacts, ST.cancel, ST.close |
| L-CANCEL | Retain existing original-entry conditional receipt/intent and all actual causes, requests, response proofs, racing executions and terminal remainder outcome. Set invalidation and monitoring-unavailable may join one native cancel intent; category views must not double-count it as two native cancels. | Lifecycle / ST.cancel, ST.reconcile, ST.acceptance |
| L-CLOSE | Existing `LifecycleCloseAuthorityStore` L30–L64/L80–L212 retains intent/causes/children and acquired/resolved times. Extend its required history with exact close-race observations, cause/evidence IDs, and individually attributed additional entry executions after the close-intent boundary. Keep pre/post proof vectors, not only the converged final residual. | Lifecycle / ST.close, ST.reconcile, ST.nativefacts, ST.attribution |
| L-RECON | Existing `LifecycleReconciliationRecord` L24–L37 retains evidence identity/kind/scope/revision/content/accepted status/time. Add complete operational episode start/completion/failure and restart-correction history to that owner domain, with exact previous/resulting state revisions and authoritative proof. Already-resolved tombstone or unchanged rehydration is not a new correction. | Lifecycle / ST.reconcile, with source/incident links |
| L-MANUAL | **ADDITIONAL** retained actual operator action or independently proven external/manual intervention observation, original command/source identity, truthful scope, observed time/reason and resulting reconciliation/action link. Keep manual cancellation, Manual Close and unrelated external intervention distinguishable. An unattributed external fact remains native-scoped. | Lifecycle / ST.reconcile, ST.cancel, ST.close, ST.incidents as applicable |
| L-FIN | Reuse the canonical B10 ST.financial/ST.coverage/ST.funding/ST.final records already required by §§7–8: unique accepted sources/aliases, actual fee/rebate attribution, A-004 basis/allocations, exact executed gross, current proof and immutable FINAL. These canonical records are planned, not present merely because legacy SQLite accounting exists. | Lifecycle / existing B10 state families; no second financial ledger |

For every history-derived metric, retain the exact event members, original field content, source/profile/chronology/configuration binding, operational-versus-factual time basis and reporting cohort/window. No latest-row reconstruction, changed historical payload, guessed absent endpoint or lossy count-only summary can replace the retained basis. Metric/report values remain read-only. Monetary/quantity calculations use the existing exact policy; view ratios retain exact numerator/denominator and never alter gates or introduce another quantizer.

#### 6.3.2 Economic idempotency, arrival identity and operational cutpoints

**ECONOMIC_IDEMPOTENCY** uses the unchanged business/source IDs and domain receipt/terminal rules: no duplicate fill, fee, grant, native effect, close reduction, FINAL or Portfolio receipt. **DIAGNOSTIC_OBSERVATION_RETENTION** records what was actually observed at intake/recovery/verification without granting another effect.

For a new physical intake instance, Lifecycle acquires a durable owner-local **arrival observation key** through the existing input/owner-state history, before discarding a delivery as an ordinary duplicate or out-of-order no-op. Reuse a trustworthy already-persisted transport intake-instance key when available; otherwise persist one opaque capture key and its exact raw payload digest/reference, path/scope and first observed time in the existing owner/transport namespace. This is not `native_observation_id`, not a new wire ID, and not a business identity owner. Once captured, every retry of its preflight/classification/processing receives that same capture key. A genuinely new delivery of the same business event has a distinct arrival key; a repeated worker/database attempt on the same captured arrival does not.

Raw capture carries no acceptance, freshness, quantity or execution authority. The unchanged known-evidence preflight still recognizes accepted identity/owner, compares complete content and commits contradictions before ordinary parsing/stale/terminal/duplicate suppression. A changed-content replay is not downgraded to a benign duplicate metric. Classification is retained as an immutable observation keyed by `(arrival capture key, observation kind)` with the exact original accepted-state/order basis; its processing retries neither remint identity nor increment again. Pending captured intake hydrates before new input. A true precommit capture crash has not created a durable observation; an unobserved delivery is never fabricated. An after-capture crash resumes that captured record rather than treating worker retry as another physical arrival.

A first valid economic event may apply once; later same-content arrival instances apply zero economics and each contribute once to a required duplicate-arrival count. Replaying a **fixed captured-arrival history** reproduces both economics and diagnostic counts. Two schedules containing genuinely different numbers of physical redeliveries can have identical economics but different, truthful arrival counts; an integrated test must not require those diagnostic counts to be identical. Counters may be deterministic read-only projections of immutable observations, or atomically updated with a unique observation receipt; a naked increment before/after dedupe is insufficient.

Out-of-order classification retains the original incoming source/order/revision evidence and the accepted comparable history as it stood at capture/classification, within the correct domain. It uses proven source chronology/field ordering, not arrival as execution order, a global revision watermark, symbol/time identity inference or lexical ID ranking. An incomparable or unproven order remains explicitly unknown; do not invent an ordering event. A stale-but-identical observation never reverses cumulative quantity; changed historical content still reaches preflight. Reprocessing the same captured observation uses its retained classification basis, not today's latest state.

Recovery corrections are keyed to the retained recovery episode, causal proof and actual before/after state revisions; unchanged startup hydration is not a correction. Protection verification failures are keyed to the actual check/query/proof event, and manual intervention observations to the actual command or proven external event. Repeated processing of those same captured checks/actions does not increment again; genuinely new checks/actions remain separately observable. Neither category creates a new trading trigger, expiry, native operation or release right.

Cutpoints remain distinct:
- `authorization_received_at` is Lifecycle's original durable intake time for the exact authorization; `authorization_consumed_at` is its first irreversible use under the existing Lifecycle protocol: binding to the governed durable native-use intent, or an explicitly proven definitive terminal-no-create resolution. Retain the consumption kind and proof; do not fabricate an intent/native call for the no-create branch. This is not Portfolio's earlier grant consumption. Reusing the existing intent for a governed retry does not consume authorization again.
- `entry_terminal_event_sent_to_set_at` denotes the **producer's first committed publication to the existing Set-addressed outbox** for that terminal return, using L-SYNC/P-TRANSPORT immutable publication evidence. It is not the exchange's terminal effective time, Set's receipt time, or a claim of completed delivery. Actual dispatch/receipt metadata, where observed, remains separately labeled. This makes the local message-boundary cutpoint precise without database/external atomicity claims.
- `sibling_protection_cancel_started_at` records the durable cancellation-start operation for the exact owned child/generation; `...confirmed_at` records the separately accepted authoritative terminal/disabled proof. A cancel intent, acknowledgement alone, absence in a partial query or timeout does not fabricate confirmation.
- `close_remainder_race_detected` retains the actual race observation and source identities even after convergence. `additional_fill_after_close_intent_qty` uses distinct proven entry execution members ordered after the retained intent boundary, not quantities that merely arrived later. A late older fill is not silently “after intent”; material ambiguous order is retained as unresolved. No new source chronology, competing child or residual rule is introduced.

Operational durations use the explicitly paired original operational cutpoints; factual execution/acceptance timing uses authoritative timestamps with provenance. Mixed-clock latency reports identify both bases and cannot certify elapsed exchange time when comparability is unproven. An unresolved endpoint remains absent/open/unknown, not zero, a guessed current time, a backdated success or a trading deadline.

#### 6.3.3 Complete Lifecycle observation map

L01–L40 are NR-152 subitems. Frequencies have explicit record scope, reporting interval/cohort and qualifying event IDs; no new universal default denominator/window is prescribed by the frozen list. Keep attempt/request/confirmed-result populations distinguishable. Source-complete empty counts are zero; incomplete evidence and undefined zero-denominator ratios are explicitly unavailable. No count is a native-safety or finality predicate.

| Item / frozen observation | Classification | Exact retained source / deterministic derivation and restart basis | Producer / existing transaction |
| --- | --- | --- | --- |
| L01 — submission attempts | DERIVABLE_FROM_EVENT_HISTORY | Count distinct retained L-SUB dispatch_cutpoint_id/attempt entries for the same durable intent. Preserve prepared, dispatch-observed and uncertain states; a persisted intent alone is not proof that an external request reached the venue. Current last-cutpoint/counter fields alone are insufficient. | B9 TX.native |
| L02 — submission acceptance rate | DERIVABLE_FROM_EVENT_HISTORY | Distinct actual accepted original entry identities from L-EVENT/L-SUB divided by the explicitly selected submitted-entry cohort, with accepted/rejected/ambiguous/unresolved member sets separately retained. Do not mix retry-attempt counts with unique-order acceptance without labeling the cohort. | B9 TX.native/TX.acceptance |
| L03 — submission rejection reasons | DERIVABLE_FROM_EVENT_HISTORY | Retained factual L-SUB/L-EVENT rejected outcomes and exact normalized/native reason with raw provenance; technical no-create refusal and actual venue rejection remain separate. Latest last_error_code does not replace history. | B9 TX.native/TX.acceptance |
| L04 — ambiguous submission frequency | DERIVABLE_FROM_EVENT_HISTORY | Distinct observed ambiguous outcome events/cutpoints in L-SUB with request/client/intent identity; count per explicit attempt or original-order cohort. Later resolution does not erase ambiguity history. | B9 TX.native/TX.acceptance/TX.owner recovery |
| L05 — native POST_ONLY rejection/cancellation observations | DERIVABLE_FROM_EVENT_HISTORY | L-SUB/L-EVENT actual venue refusal/cancellation reason and bound order/profile/source proof. No best-bid/ask prediction or local marketability check is a qualifying native observation. | B9 TX.acceptance/TX.cancel |
| L06 — time from submit to acceptance | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Original L-SUB.submitted_at for the retained intent/attempt and authoritative L-EVENT.entry_accepted_at/provenance; exact difference only with explicit compatible time bases, otherwise unavailable with endpoints retained. Never callback time as acceptance. | B9 TX.native/TX.acceptance |
| L07 — time to first fill | DERIVABLE_FROM_EVENT_HISTORY | Original submit cutpoint and first attributable positive execution in authoritative chronology, with execution_id/effective time/quantity. Retain full execution history so backfill changes an unfinalized observation honestly without mutating a prior accepted source. | B9 TX.acceptance/TX.partition as applicable |
| L08 — time to full fill | DERIVABLE_FROM_EVENT_HISTORY | Original submit and earliest proven cumulative entry execution prefix reaching the immutable approved Q, with all member IDs. A terminal partially filled cancel is not full fill; missing/materially ambiguous chronology remains unavailable. | B9 TX.acceptance/TX.partition |
| L09 — partial-fill frequency | DERIVABLE_FROM_EVENT_HISTORY | Distinct original entries with a proven historical 0<F<Q state in L-EVENT/execution history, including entries later fully filled. Count entries or transitions only as explicitly labeled; duplicate fills do not add economic or qualifying entry members. | B9 TX.acceptance |
| L10 — fill ratio | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Exact attributable cumulative entry quantity F and immutable approved Q at a named history revision, ratio F/Q. Retain member IDs and Q source; do not clamp overfill or substitute native aggregate quantity. | B9 TX.acceptance/TX.partition |
| L11 — cancel frequency | DERIVABLE_FROM_EVENT_HISTORY | L-CANCEL unique original-entry cancel intent/request and separately proven terminal-cancel outcomes. State whether the query counts requests or confirmations; retain the underlying exact sets. Two F-013 causes joining one intent do not create two native cancels. | B9 TX.cancel/TX.acceptance |
| L12 — cancel/fill race frequency | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-CANCEL actual race observation keyed to cancel intent, racing execution and native terminal/proof history; preserve even when final state converges. Never infer from latest CANCELLED text alone. | B9 TX.cancel/TX.acceptance |
| L13 — Set-driven cancel frequency | DERIVABLE_FROM_EVENT_HISTORY | L-CANCEL exact original ORDER_CANCEL_SIGNAL receipt/cause IDs joined to the single conditional intent; count distinct qualifying intents with Set causation and distinguish signal count from native cancel count. | B9 TX.cancel |
| L14 — manual cancel frequency | DERIVABLE_FROM_EVENT_HISTORY | L-MANUAL actual manual-cancel command/event identity and L-CANCEL linkage; no guessed human cause from endpoint/source name. | B9 TX.cancel |
| L15 — zero-fill cancel frequency | DERIVABLE_FROM_EVENT_HISTORY | L-CANCEL terminal original-entry cancel plus authoritative zero-execution proof. Explicit no-create failures are a separate cohort, not invented cancel or financial FINAL. | B9 TX.cancel/TX.acceptance |
| L16 — partial-fill remainder cancel frequency | DERIVABLE_FROM_EVENT_HISTORY | Proven terminal remainder cancellation with prior positive attributable entry fills, exact F and cancelled remainder proof; filled exposure persists under unchanged rules. | B9 TX.cancel/TX.acceptance |
| L17 — TP close frequency | DERIVABLE_FROM_EVENT_HISTORY | Distinct terminal tranche/result with authoritative TAKE_PROFIT final classification and current CLOSED evidence in L-EVENT/ST.final. A TP cause/request before full finality is not a completed close. | B9 TX.close captures cause; B10 TX.final confirms |
| L18 — SL close frequency | DERIVABLE_FROM_EVENT_HISTORY | Same retained terminal evidence with STOP_LOSS classification, never first-arrival cause inference. | B9 TX.close; B10 TX.final |
| L19 — Manual Close frequency | DERIVABLE_FROM_EVENT_HISTORY | Same terminal evidence with MANUAL_CLOSE classification; retain manual request and actual final outcome separately in races. | B9 TX.close; B10 TX.final |
| L20 — reconciliation frequency | DERIVABLE_FROM_EVENT_HISTORY | Distinct L-RECON episode starts under original causal identity and selected reporting scope. Restoring one unfinished episode is not another start; new source-defined episodes remain distinct. | B9 TX.owner or actual native/fact/close transition; B10 financial episode transitions |
| L21 — reconciliation duration | DERIVABLE_FROM_EVENT_HISTORY | Original L-RECON first operational started_at and actual consistency-restored completed_at; failed attempts/uncertain endpoint retained. Open episodes are right-censored at explicit report as_of, not falsely complete. | Same owner transactions as L20 |
| L22 — restart recovery corrections | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-RECON actual correction with episode/cause-proof/before-after state revisions and captured correction time/reason. No event from unchanged hydration; replay of same correction contributes once. | B9 TX.owner with recovery transition; B10 own financial recovery where applicable |
| L23 — duplicate event count | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-ARRIVAL immutable duplicate classification per captured arrival key and actual accepted semantic evidence identity. Count distinct qualifying arrival observations, not economic effects or repeated classification retries. | B9 existing TX.owner intake/classification; B10 applies same rule to financial intake |
| L24 — out-of-order event count | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-ARRIVAL original ordering basis/flag using comparable authoritative per-domain history; retain incoming/counterpart IDs, source order and captured time. No global high watermark or invented temporal association. | B9 TX.owner/TX.facts/TX.acceptance; B10 corresponding financial intake |
| L25 — protection verification failures | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-PROTECTION check/query/proof identity, actual failed/unknown prerequisite, reason, expected child set and source evidence; repeated same check processing counts once, new checks are separate. | B9 TX.protection, after applicable TX.preflight |
| L26 — manual intervention count | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-MANUAL distinct actual command/proven external event, truthful scope and observed health/action consequence; unresolved attribution has no fabricated tranche or execution authority. | B9 TX.owner/TX.cancel/TX.close/TX.partition as the actual event requires |
| L27 — authorization_id | DIRECTLY_PERSISTED | Existing L-SUB.authorization_id plus exact accepted authorization payload/digest and start-gate binding. No new authorization identity. | B9 TX.native; original receipt TX.owner |
| L28 — authorization_received_at | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | First retained Lifecycle InboxMessageRecord.received_at for exact accepted SUBMIT_AUTHORIZED message/authorization, with original digest/binding; retain in L-AUTH if transport history is compacted, without substituting a new time. | B9 existing TX.owner intake |
| L29 — authorization_consumed_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-AUTH first native-use consumption bound to L-SUB and verified spec/auth/current facts, or the existing proven definitive terminal-no-create consumption with its terminal proof/kind. Distinct from receipt and Portfolio grant consumption; no intent is fabricated for no-create and retries do not consume again. | B9 TX.native; TX.acceptance for existing terminal no-create |
| L30 — entry_terminal_event_sent_to_set_at | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | L-SYNC terminal return event ID/revision and original Set-addressed OutboxMessageRecord.created_at, retained as first producer publication under §6.3.2. Not terminal effective time or consumer delivery acknowledgement. | B9 TX.placement |
| L31 — sibling_protection_cancel_started_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-PROTECTION exact owned child/generation, close/cancel intent, stable request and first durable cancellation-start time. Keep all child generations and attempts, not one overwritten timestamp. | B9 TX.protection/TX.close; durable native intent uses existing TX.native |
| L32 — sibling_protection_cancel_confirmed_at | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | Separate L-PROTECTION accepted terminal/disabled confirmation and its authoritative effective time/provenance plus first owner capture; link to the same original child/start operation. | B9 TX.protection |
| L33 — close_remainder_race_detected | ADDITIONAL_OWNER_LOCAL_OBSERVATION_REQUIRED | L-CLOSE retained detection event/cause/entry remainder/cancel/fill evidence and proof vector; once established it remains in history after residual converges. Not a new trading close cause. | B9 TX.close/TX.cancel/TX.acceptance as facts arrive |
| L34 — additional_fill_after_close_intent_qty | DERIVABLE_FROM_EVENT_HISTORY | Sum exact distinct attributable **entry** execution quantities proven after L-CLOSE's original intent boundary using retained authoritative ordering/basis. Keep member IDs and uncertainty; a delayed pre-intent execution is not an additional post-intent fill. No clamp, speculative attribution or quantity mutation from the metric. | B9 TX.acceptance/TX.close/TX.partition |
| L35 — funding_allocation_basis | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | ST.funding unique source, effective-time eligible tranche/member quantities, settlement basis/provenance, exact weights, algorithm version and allocation receipts. Reuse actual A-004 evidence; never current-position weights. | B10 TX.funding |
| L36 — realized entry fees | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | ST.financial accepted entry-execution-linked fee/rebate components and exact non-funding allocation receipts/source aliases, with component coverage/applicability/currency. Sum distinct qualifying signed cost-effect allocations, not planned maker rates. | B10 TX.facts/TX.cashflow; FINAL qualification TX.final |
| L37 — realized exit fees | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Same actual source/receipt basis restricted to proven exit executions; do not reuse entry notional or classify by arrival. Components lacking complete evidence remain explicitly non-FINAL. | B10 TX.facts/TX.cashflow/TX.final |
| L38 — realized funding | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Exact once-allocated ST.funding amounts; immutable financial_result.allocated_funding when FINAL. Retain source identity and sign; no future funding or implicit FX. | B10 TX.funding/TX.final |
| L39 — gross realized P&L | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | ST.final financial_result.gross_realized_trading_result and its actual execution/cost-basis proof; before FINAL expose only clearly scoped existing factual components, not a provisional full-tranche result. | B10 TX.final |
| L40 — net realized P&L | DERIVABLE_FROM_IMMUTABLE_RETAINED_RECORDS | Immutable ST.final financial_result.net_realized_result with actual fees/rebates/funding/other costs, currency, current evidence vector and accounting_effective_at/day. Query by exact result_id/tranche; no duplicate source aliases or planned substitute. | B10 TX.final; Portfolio own receipt remains separate |

#### 6.3.4 Frozen §40 visibility support

The existing read-only user/audit layer must retain the seven source labels **Pending, Partially Filled, Open, Cancel Pending, Closed, Failed, Reconciling**, with finer internal states available as diagnostics. This is a projection of the frozen lifecycle states, not another state machine. In particular Closed requires the actual S-004 terminal state; physical flatness or cleanup without finality remains nonterminal/reconciling. Failed does not erase confirmed fills or uncertain authority.

| Required question from §40 | Retained evidence supplying the answer |
| --- | --- |
| Was the order submitted? Was it accepted? | L-SUB original durable/observed submission cutpoints and separately proven L-EVENT acceptance; distinguish intent, uncertain dispatch and venue acceptance. |
| How much filled? How much remains pending? | Exact attributable execution members/cumulative quantity and current original-entry remainder/terminal proof; not an aggregate exchange-position guess. |
| Is TP/SL protection confirmed? | Current L-PROTECTION source-complete proof and owned children, distinct from historical mappings or past successful checks. |
| Was cancellation requested? Why did it cancel? | L-CANCEL/L-MANUAL original intent and all actual causes, then separately proven terminal cancellation reason/outcome. |
| Is the tranche open or closed? What was the close reason? | Actual lifecycle/close state, authoritative final classification and all six predicates/ST.final; no first cause or dashboard label as authority. |
| What are realized fees/funding/P&L? | L-FIN actual components with completeness status and immutable FINAL when available, source and currency binding; no fabricated provisional result. |
| Is the system reconciling uncertainty? | Current unresolved L-RECON/protection/close/source/incident state plus complete episode/reason history. A historical successful query cannot clear a newer incident. |

No new trading API contract is added. Existing diagnostic query/view composition reads retained evidence; it never becomes a producer of missing historical facts or a control path.

#### 6.3.5 AT-NR-152 — mandatory owner-local acceptance cases

Every case checks the related L01–L40 rows and §40 questions through actual owner paths, with explicit retained factual proofs and independent expected values. B9 implements operational capture; B10 implements its own financial portion. B11/B13 stress/integrate those completed producers, not reconstruct missing history after the fact.

| Case | Input/sequence | Required source-derived assertion | Producer / gate |
| --- | --- | --- | --- |
| 01 — duplicate economics versus arrivals | Apply a factual execution once as capture a1. Receive identical business content as new capture a2; retry processing a2 before/after commit. | One economic execution/quantity/fee effect; a2 supplies exactly one duplicate observation and no extra effect. Processing a2 again keeps count1. A genuinely new a3 increases duplicate observation count to2 but economics remain unchanged. Same a2 with changed content conflicts. | B9 intake/acceptance; B10 analogous financial case |
| 02 — out-of-order arrival | Proven later cumulative entry observation F=2 arrives before a valid older F=1 observation in the same ordered domain; retain distinct captures and original source proof. | Current F stays2; original older-arrival classification retained once. No global high-watermark identity shortcut; changed known historical content still triggers preflight. Replay classifications use retained basis. | B9 TX.owner/TX.acceptance |
| 03 — restart recovery correction | Hydrate an unresolved episode, accept missing authoritative fact and commit one actual state correction under one retained proof/revision binding; restart again without new evidence. | One correction history/count, original episode/time/evidence; second unchanged hydration adds no correction. A new independently justified correction is separate, not a duplicate of startup. | B9 TX.owner; B10 financial recovery analog |
| 04 — authorization cutpoints | Authorization is durably received at t0; matching spec/current proofs become available later; first native-use intent commits at t1>t0. Repeat auth, spec and intent processing; separately exercise a proven definitive terminal-no-create resolution without a native call. | Original received_at=t0 and consumed_at=t1 retained separately and once; the no-create branch retains its actual terminal-consumption proof/time and cannot reopen CREATE; no native authority before complete join; Portfolio grant consumed_at remains its own earlier B8C cutpoint. | B9 TX.owner/TX.native |
| 05 — terminal return publication | Authoritative terminal event effective time t0 arrives later; existing LifecycleSetSyncStore publishes the return to Set at t1; delivery occurs at t2. | `entry_terminal_event_sent_to_set_at` is original producer publication t1 under §6.3.2, not t0 or t2. Retain exact terminal event/outbox identity; retry preserves t1, terminal-first monitor dominance unchanged. | B9 TX.placement |
| 06 — sibling cancellation | Durable owned-sibling cancel start at t0; acknowledgement without terminal proof at t1; authoritative child-terminal/disabled confirmation at t2. | Started=t0; no confirmed timestamp at t1; separate proven confirmation at t2 retained. Uncertainty keeps existing child/close authority restrictions; no inferred cleanup success. | B9 TX.protection/TX.close/native intent |
| 07 — close/fill race | Acquire one close intent; then two uniquely attributable entry fills of0.2 and0.3 are authoritatively ordered after the intent boundary while remainder cancel races. Also deliver a0.1 fill proven before intent only afterward. | Retain race=true and members for exact post-intent sum0.5; late0.1 is not counted as post-intent. Factual exposure still includes every real fill under unchanged P5/P9. Replay never adds0.2/0.3 twice; ambiguous ordering stays unresolved, not guessed. | B9 TX.close/TX.acceptance/TX.partition |
| 08 — manual intervention | Actual manual action or proven external intervention has stable original identity; repeat delivery. Include unattributed native change. | One observation per captured action; truthful native scope for unlinked change. No invented tranche, release, FINAL, close reason or native permission. Existing governed manual cancel/close commands retain their own authority checks. | B9 owner/cancel/close/partition |
| 09 — native POST_ONLY refusal | Native factual refusal/cancel record names original authorized order and actual venue reason; also supply a merely locally predicted marketability case. | Retain/count actual refusal once with raw provenance; the local prediction cannot be a venue observation, new gate, reprice or MARKET fallback. | B9 TX.acceptance/TX.cancel |
| 10 — reconciliation and timing | One episode starts t0, has failed and ambiguous attempts, and completes only at proven consistency t3; replay source events and restart in between. | Episode count1, exact operational duration t3−t0 with original bases, all failures retained; unfinished episode exposes absent completion. First/full-fill and acceptance latencies retain their own independently proven endpoint types, not episode times. | B9/B10 owner transitions |
| 11 — factual financial observations | Retain complete source-proven LONG entries quantity2 at100 and exits quantity2 at110: gross20; actual entry fee cost1; exit rebate cost−0.2; allocated funding−0.3; other costs0, all one governed unit. Include complete allocation/coverage and each source once. | Gross20; actual fee/rebate cost total0.8; funding−0.3; net18.9. Show entry/exit components and A-004 basis by source/receipt; source aliases/retries do not change totals. Any missing/foreign/materially conflicting required source blocks full FINAL rather than synthetic planned economics. These are factual fixture values, not trading parameters. | B10 TX.facts/TX.cashflow/TX.funding/TX.final; accounting/numeric review |
| 12 — crash, history completeness and visibility | Inject before/after capture, preflight, classification, operational state/outbox, protection/close and financial commits; restore all histories and query every L01–L40/§40 item. | Precommit current transaction commits neither its observation nor effect; existing preflight/capture commits remain as defined. After commit, retry same capture/cutpoint uses original content/count/times. Recovery never fabricates unobserved physical events or overwrites FINAL. Check fixed-arrival replay equality separately from schedules with genuinely extra arrivals. | B9/B10 local PG tests; B11/B13 integration |

### 6.4 NR-153 / NR-154 — required Entry and TP research reporting (FA-R5-01)

#### 6.4.1 Authority, applicability and actual implementation surfaces

**Controlling obligation:** POSITION_RULES Part II §51 L3220–L3243 requires the 19 Entry items; Part IV §48 L5464–L5485 requires the 17 TP items. The adjacent research sections provide versioned baseline candidates and prohibit unrestricted combinatorial optimization. The frozen F-008/F-010 selection, failure, distance and output semantics remain authoritative. They do not specify a universal research denominator, observation-price sampling frequency, expectancy unit/band sweep or counterfactual experiment grid for every reporting label.

**Explicit diagnostic definitions, not alleged frozen formulas:** This subsection fixes the narrow reporting interpretation used by the implementation, identifies it as `ENTRY_REPORT_V1` / `TP_REPORT_V1`, and requires its full definition to be pinned in each report. Definitions of cohorts, as-of rates, first-fill excursion anchor, target-touch windows and outcome aggregation below are analytical implementation choices permitted by the reporting obligation; they are not claimed to be prescribed trading rules. Where an experiment needs parameter values, bands or a data-resolution profile not fixed by frozen source, the request must supply an explicit versioned Research configuration. There is no invisible default parameter sweep or later implementer choice between competing denominators. Changing a report definition produces a differently pinned report, never reinterpretation of a canonical record.

Applicability is independently **DYNAMIC Entry** and **DYNAMIC TP**. An F-010 result independently computed even when Stop fails remains in the TP evaluation cohort; an overall Position REJECT must not erase usable Entry/TP evidence. A fixed-mode result is retained under its original mode but is NOT_APPLICABLE to the corresponding dynamic-selection report. This does not make either dynamic mode mandatory, create an F-010 Stop prerequisite, or alter the existing fixed-mode obligations. Diagnostic results never become Position inputs.

| Actual current surface | Existing capability inspected in the supplied snapshot | Focused extension / limit |
| --- | --- | --- |
| `src/triggertrade/services/research.py::ResearchService` L80–L105, `run_backtest` L140–L233 | Existing Research orchestration accepts explicitly supplied `HistoricalCandle` tuples, run pins and existing ResearchStore; reporting is not presently complete. | Add read-only dataset import/report assembly entry points inside this existing service. New method names are implementation proposals, not claims of existing methods. Do not route this task through `run_backtest` or the legacy simulator to invent canonical observations. Existing `request_make_active`/promotion methods are not invoked by a report. |
| `src/triggertrade/research_pins.py::research_pin_payload` L22–L47; `research_run_pin_payload` L50–L66 | Existing configuration/source/profile/assumption pins and canonical digest helpers. | Reuse them to carry report-definition/query/band/path/sweep and source-manifest pins. An existing generic pin does not already prove those fields were captured. Preserve old pin contents and schema meaning; report additions are explicit nested diagnostic run inputs. |
| `src/triggertrade/persistence/research_store.py::ResearchStore` L132–L137; run records L214–L381; schema L526–L636; SQLite connection L638–L641 | Research entities, backtest/demo runs, JSON metric payloads and pin digests; no full immutable required-report/dataset store interface. | Extend the same ResearchStore with append-only diagnostic dataset/member/report records and exact pin/content comparison. Dedicated child tables **inside the same SQLite database/store** are justified if existing generic records cannot represent an immutable report without falsely labeling it a backtest/demo success. No new repository/service and no PostgreSQL migration. Existing generic `metrics_json` is reused where its semantics fit, not forced to act as a canonical execution ledger. |
| `src/triggertrade/backtest/data.py::HistoricalKlineCache` L83–L141; `validate_historical_candles` L32–L80 | Historical cache files/metadata, exact decimal candle values, symbol/category/timeframe/interval checks and content hashes. Current cache paths are range-based and writes are not a proven immutable publication protocol. | Reuse this ingestion/cache organization. B3 adds diagnostic source manifest, full provenance/coverage, immutable content-addressed retained copies, conflict checks and crash-safe publication described below. Reusing the validator requires added OHLC consistency/source completeness checks for reports, not a claim that current checks certify all evidence. Never overwrite a dataset already referenced by a report. |
| `src/triggertrade/backtest/data.py::BybitHistoricalDataSource.load` L152–L165; `HistoricalCandle`, `backtest/models.py` L37–L49 | Current public downloader is explicitly **linear BTCUSDT, 1m only**. A candle has OHLC and interval times but not individual intra-bar trade ordering. | Do not claim multi-coin downloads, tick histories or exact intra-bar target time already exist. The same diagnostic ingestion boundary accepts explicitly supplied, provenance-complete immutable factual datasets for other instruments and finer source records; this is an extension, not a new canonical API requester. Unsupported acquisition returns UNAVAILABLE. Historical candles alone cannot resolve arbitrary intra-bar chronology. No new venue endpoint or permission is assumed. |
| `src/triggertrade/analytics/futures.py::TradePerformanceFact` L9–L24; `FuturesPerformanceMetrics` L35–L60; `compute_futures_performance` L82–L156 | Closed-trade/direction-split aggregate performance. | Extend the existing analytics package with these report functions, using exact source-bound members. Reuse a helper only where its actual numerical/unit/cohort semantics match; do not feed legacy `ClosedTradeResult`/SQLite trade rows into canonical-outcome reports. Aggregate P&L is not fill, missed-entry, target-touch or excursion evidence. |
| FN.PIN/FN.CONSTRUCT/FN.RECON/FN.SUBMIT/FN.FACT and R5’s existing owner histories | Planned canonical original Position work, native/source history, and immutable FINAL already have assigned owners/transactions. | Add the missing local retained fields/complete child collections at their original producers; read-only Research import sees committed immutable rows only. Existing owner facts remain authoritative and are never rewritten by the diagnostic copy. |
| `OperatorStateStore`; `ResearchPromotionGovernanceStore` | Existing SQLite operator state and separate PostgreSQL promotion-request/outbox governance. | **No scope or storage change.** Report assembly does not select an active run, promote a candidate, invoke operator commands or update live configuration. |

`ENTRY_REPORT_V1`, `TP_REPORT_V1`, the E-/T-/RPT-* aliases and fields in this subsection are internal diagnostic definitions. They add neither certified F/A/S objects nor business wire fields. No extra contract family is needed to compose already-retained immutable evidence in a read-only query.

#### 6.4.2 Producer/consumer dataflow and first implementation checkpoints

```text
Set original result/context/reference evidence ─┐
Position original F-008/F-010 evidence ─────────┼─> committed immutable owner history
Lifecycle native/execution/close/FINAL facts ──┘                 │
                                                               ├─> exact-lineage read-only dataset import
Existing retained market facts / explicit public Research       │
historical-data input -> immutable diagnostic source archive ───┘
    -> existing ResearchService + analytics report assembly
    -> append-only diagnostic dataset/report in existing SQLite ResearchStore
    -> existing read-only research/diagnostic presentation
```

There is no Research→Set/Position/Portfolio/Lifecycle decision edge. No owner waits for a report or reads a report value to determine its result. Source integrity rules remain with the original owner; read-only reporting neither clears nor creates native/release authority.

| Checkpoint | First-time responsibility | Completion and non-dependency boundary |
| --- | --- | --- |
| B3 | Extend the existing diagnostic historical/factual dataset ingestion/cache and same ResearchStore with immutable source/coverage manifests, exact import identity, source-object retention and unavailable/conflict handling. Test this generic documentary persistence with typed factual datasets, including boundary-resolution limits. | No Position result, F-010 counterfactual, report metric, native operation or future owner state is created here. This is documentary acquisition/retention through existing factual/Research inputs, not a fourth API contract or Research subscription to the trading bus. |
| B7A | Retain complete original Entry/TP decision-source collections, evaluated and unevaluated candidate distinctions, raw/rounded metrics, warning/primary reason, selected/thesis bindings, age and immutable lineage in ST.position/configuration/reference evidence. | Same TX.opportunity as initial decision/pin/outbox, including rejected opportunities. Local evidence tests do not wait for grants, native execution, FINAL or B12 reports. |
| B9 | Retain actual immutable submission, current-hard-refusal, venue POST_ONLY outcome, acceptance/fill/time/source and close-proof inputs using existing Lifecycle histories and transactions. Register no future synthetic outcome. | Private execution evidence is Lifecycle-owned. Public price-path import/archival remains the B3-established isolated diagnostic input, not a new Lifecycle market strategy or a new Research native call. B9 tests join-ready factual data and chronology without requiring B10 FINAL. |
| B10 | Supply actual immutable FINAL/result/tranche/currency/net and permanent closing-execution chronology, plus existing final close cause and retained proof. | TX.final remains Lifecycle-only; Portfolio receipt/release remains its own transaction. Research outcome projection copies the original result and never recomputes Entry/TP or produces a FINAL. |
| B11 | Stress the already implemented source/manifest capture, immutable member lineage, cross-owner read-only import retries and source retention. | Verification only. Full report assembly is not a B11 prerequisite and is not first implemented here. Test source data and diagnostic dataset persistence, not an as-yet-unimplemented B12 metric function. |
| B12 | Extend the existing **technical diagnostics/ResearchService/analytics** responsibility to assemble both complete reports and isolated min/max sensitivity from pinned committed evidence; persist them in the same ResearchStore. Implement all remaining ENTRY-RPT/TP-RPT report assertions locally. | This runs outside the canonical dispatcher’s decision logic, with read-only access to business evidence and no canonical writer/native/promotion capability. No second worker. The existing dispatch portion remains after B0–B11; reporting uses those completed sources and introduces no reverse checkpoint dependency. |
| B13 / B14 | V20/V21 full integrated report/isolation verification; then independent implemented-backend review. | Neither is a first producer, first archive of a lost path, or first implementation of report calculations. |

A report may be requested before its factual horizon is complete; it must accurately expose INCOMPLETE/UNAVAILABLE data. The existence of that diagnostic status never gates live trading. Plan-completion tests can require that the reporting capability and its correct unavailable branches are implemented, but cannot require future live fills or a future FINAL before permitting a current legitimate trade.

#### 6.4.3 Exact retained bases, source capture and lineage

The following documentary aliases extend **existing** state families, not additional canonical state families:

| Basis | Exact retained contents and producing location | Persistence / uniqueness |
| --- | --- | --- |
| RPT-SET | Original immutable handoff/result bytes and digest; Set configuration ID/version/content; `decision_cycle_id`, `set_result_id`, matched/market-snapshot times, symbol/direction, exact `entry_context.set_family` and `tp_context.set_family`; concrete reference IDs/types/prices/timeframes/available_at and producer role/occurrence bindings. Context-specific families are not assumed equal. | Existing ST.setresults/ST.references/ST.config under TX.set; no new wire fields. Research copies/reference-links exact committed content. |
| RPT-POS | Original `position_decision_id`, initial status and source basis, Position configuration ID/version/content digest and mode, matching handoff digest; full frozen relevant reference collection, per-stage evaluated/not-evaluated status, original F-008 and F-010 local output fields below, plus source references proving the actual chosen thesis/default path. | B7A ST.position under TX.opportunity. Unique decision+stage and candidate `(position_decision_id, stage, original level_id)` inside original account/environment; each visited outcome retained once. A rejected opportunity retains its real decision, never fictional grant/tranche/spec. |
| RPT-ENTRY | `dynamic_entry.reference_selection`: original before-selection/ineligible/shallow/deep/eligible ID collections, selected ID/type/price/timeframe/available_at/age/priority; exact raw and rounded improvement price/pct/ATR; M=`set_match_reference_price`, received ATR_15m and its source/handoff binding, tick, raw/rounded Entry; usable/reason/warnings. Explicitly retain which improving candidates actually received a depth classification and whether the selected reference reached the rounding check. | B7A, same ST.position work record. Original selected-reference metrics and failed diagnostics are non-actionable; unavailable values are not zeros. Raw/rounded values are labeled separately. |
| RPT-TP | `dynamic_tp` full snapshot/thesis context, reference collection status, directional/basic/traversable member sets, actual visited order and per-visit reason, skipped too-close IDs, first too-far and termination, unvisited IDs, selected ID/type/price/timeframe/priority, original raw/rounded distance and ATR/tick/min/max; usable/reason/warnings. Retain whether a thesis actually selected, versus default traversal/fallback warning, with exact original thesis ID/policy/binding. | B7A ST.position; complete frozen collection is retained for explicit diagnostic alternative traversal, but unvisited candidates are never misrepresented as actually visited by the primary selector. Position-only diagnostic additions to §44; no extra MARKET_HANDOFF/ORDER_SPEC fields. |
| RPT-CHAIN | Exact existing immutable links: initial decision → actual capital_grant_id → construction_result_id → successful plan/tranche/order_spec_id/digest → authorization_id → original durable client_order_link_id and proven exchange order identity; later close_intent_id, exact cause/result and result_id. | Reuse existing ST.grants/ST.construction/ST.spec/ST.authorization/ST.submission/ST.close/ST.final bindings, read-only. Each link has accepted content/revision proof. Uncreated/unknown links remain absent with a reason, not inferred by symbol/price/time. No additional grant/spec/auth producer is required. |
| RPT-LIFE | Original actual dispatch observations/uncertainty, exact complete spec/auth/current-hard-check identity and result, native POST_ONLY rejection versus cancellation with raw reason/provenance, native accepted_at and origin proof, distinct attributed entry/exit execution IDs/quantities/prices/effective time/order, original approved Q and entry-remainder terminal proof, final close classification. | B9 existing ST.submission/ST.nativefacts/ST.acceptance/ST.reconcile/ST.close/ST.attribution and L-SUB/L-EVENT/L-CANCEL bases. Existing TX.native/TX.acceptance/TX.facts/TX.cancel/TX.close/TX.partition as actually applicable; no report-induced business event. |
| RPT-FINAL | Same canonical full-tranche immutable A-002 result_id/tranche_id/content digest, actual net/gross/component proof, governed currency, permanent final closing-execution ID/order/time=`accounting_effective_at`, and S-004 status/proof. | B10 ST.final and original factual proof in TX.final. No new financial ledger, wallet posting, fee estimation or Portfolio-created result. A component result or legacy closed trade is not eligible. |
| RPT-PATH | Immutable source dataset ID/digest, exact venue/product/market symbol/price kind/source-profile version, raw source records and provenance, interval bounds, source-effective time/order/resolution, page/member manifest, coverage/missing ranges/watermark/finality, capture/import metadata and content comparison. Record event prices where available or exact completed OHLC intervals with all extrema and resolution limits; preserve boundary subrecords when required. | Existing ST.facts source records where already retained, or immutable diagnostic raw objects in the existing historical-cache organization plus ST.research manifest/member records. B3 establishes capture; Research ingestion persists before releasing/overwriting the input. No prediction, mark-price substitution, chart reconstruction or creation of a native source ID. |
| RPT-RUN | Complete report-definition/configuration/query pins, source snapshot/manifest and per-owner revisions, exact member/cohort/numerator/denominator sets, path and outcome availability, exact results, immutable report identity/content and first generated_at metadata. | B12 same SQLite ResearchStore, append-only. The same manifest/pins reproduce the same report. B3 already provides dataset persistence. Reports cannot be selected/promoted by this code path. |

**Reference age is already defined by source, not a new report convention.** Copy/verify the selected producer reference’s `available_at`, exact `market_snapshot_at`, and `age_seconds = ceil(market_snapshot_at − available_at)` in seconds under SET §§14–15 L3805–L3861. Keep the exact delta and original integer age. It is **not** time since pivot, not time since report generation and not age at a later Position retry. RPT-POS also retains `entry_decision_effective_at` as the original analytical decision’s handoff-bound effective basis (`matched_at`), labeled separately from first Position operational evaluation time; neither substitutes for `market_snapshot_at` in canonical reference age.

**Lineage completeness:** Report members include all fields above plus separate owner-specific configuration namespaces. A single ambiguous `configuration_id` cannot silently stand for Set, Position and Research pins. For Entry, `selected_entry_reference_id/type/price` map exactly to F-008 `selected_level_id/type/reference_price`; for TP, target reference/type/raw price and actionable rounded TP are separately labeled. Every later association is a validated existing ID/digest binding, not “latest trade for coin”. Path dataset matching uses an explicitly pinned factual instrument/source plus proven execution interval **after** business lineage is established; symbol/interval alone never establishes which trade a record belongs to.

**Internal report-member schema aliases (not new wire fields):** Both reports retain `decision_cycle_id`, `set_result_id`, `position_decision_id`, `symbol`, `direction` and the exact account/environment/product namespace. `configuration_id`, `configuration_version`, `configuration_content_digest` explicitly denote the original **Position** pin; separate `set_configuration` and `research_configuration` objects carry their own ID/version/content digests. Entry `set_family` means the original entry context; TP `set_family` means the original TP context.

Entry members additionally retain `selected_entry_reference_id`, `selected_entry_reference_type`, `selected_entry_reference_price` (raw), `entry_price` (usable rounded Entry only), `entry_decision_effective_at` (the explicitly labeled matched-at analytical basis above), `reference_available_at`, original `market_snapshot_at`, exact reference-age delta and canonical integer age. TP members retain the same original Entry link, `selected_target_reference_id`, `selected_target_type`, `selected_target_reference_price` (raw), `target_price` (usable rounded actionable TP), separately labeled raw/rounded `target_distance_atr`, complete actual `traversal_evidence`/candidate sequence and `tp_failure_reason`. Failed diagnostic prices remain separate non-actionable fields, not fabricated usable prices.

Both retain the exact later `capital_grant_id`, `construction_result_id`, `tranche_id`, `order_spec_id`/digest, `authorization_id`, `client_order_link_id`, proven native entry identity and actual execution IDs **only when those records exist and exact immutable links are proven**. TP/outcome members additionally retain `close_intent_id`, authoritative final close cause and immutable `result_id` when present. Every absent link distinguishes NOT_YET_CREATED, NOT_APPLICABLE or unresolved provenance in report-only metadata; the report does not create those business records. All member/source field names are documentary projection aliases over the original owner records, not additions to the frozen contract schemas.

**Capture before loss:** B3 must publish raw diagnostic source objects durably and immutably before publishing a manifest that references them. Reusing a mutable range-named cache file is insufficient: use canonical source content/digest-qualified immutable objects; write/flush/atomic-publish the object first, then commit the SQLite manifest/member references. This is ordered publication, **not** filesystem/SQLite atomicity. A pre-manifest orphan is non-authoritative and resumable; a published manifest cannot refer to an incomplete/unflushed object. Existing accepted raw facts must remain retained while any required report dataset references them; diagnostic source copies can be reused only after exact digest/provenance verification. This introduces no purge policy.

Owner-local RPT-POS and RPT-LIFE/RPT-FINAL source fields commit with their original owner effects, before acknowledgment. Research copies them afterward independently; a failed SQLite import cannot roll back or block an unrelated canonical transition. Its read position advances only with its complete imported manifest/member transaction, so restart retries the same source identities. Owner history remains the recovery basis until archival proof exists. Public path facts are archived at the existing factual/Research ingestion boundary as received, not reconstructed for the first time at B13. A historical import is permitted only when its source archive proves the full requested period and source identity. A later incomplete chart or a recomputed series is not accepted as that proof. The current snapshot has no universal event-resolution feed; absence of a suitable supplied/retained source must be explicit, not falsely certified.

#### 6.4.4 Pinned cohorts, rate definitions and availability

A report request pins a half-open **opportunity window** `[window_start,window_end)` using the original RPT-POS analytical `matched_at`, plus a separate `evidence_as_of` and exact immutable source manifest. Follow-up native/path/FINAL facts may occur after the opportunity window but must be inside the report’s explicitly selected evidence horizon. Generated time is not an analytical cutoff. Account/environment/product/currency scopes and source class (canonical factual versus explicitly isolated diagnostic input) remain separate. No legacy/demo backtest execution is relabeled canonical.

The manifest proves the full opportunity enumeration and per-stage memberships for the selected scope; storing only successful trades cannot prove any selection denominator. Include source-complete empty cohorts as well as missing-member/unknown-scope indicators. Every rate exposes exact numerator/denominator counts and reconstructible member IDs, plus excluded/not-applicable/unresolved membership and its reason. Ratios are exact rationals; any display formatting remains report-only. A frequency may have a finite exact count when its requested denominator is undefined; never report the undefined ratio as zero.

| Cohort | Deterministic diagnostic definition / exact member basis |
| --- | --- |
| E-evaluated | Distinct RPT-POS initial decisions where DYNAMIC Entry actually ran with valid frozen source/configuration sufficient to perform its relevant selection operation. Stage/prerequisite failures are retained separately, never silently counted as depth failures. A later Stop, TP, gross, Portfolio or construction rejection does not remove an already evaluated Entry. |
| E-depth | Actual improving candidate classification members `(decision, original reference ID)` in RPT-ENTRY; only candidates for which the source’s depth classification actually executed. Wrong-side/type/unavailable references are explicitly excluded. |
| E-rounded | E-evaluated members whose selected reference reached the actual F-008 rounding/post-round checks, including post-round failures. |
| E-selected | E-evaluated members with a usable immutable selected Entry; original selected reference and rounded Entry are retained. An overall rejected opportunity can be E-selected but cannot acquire downstream authority from this report. |
| E-authorized-check | E-selected members that reached Lifecycle’s exact complete spec/authorization join and an actually evaluated current hard-compatibility check; definitive no-create and passing outcomes both retained, unavailable checks separately identified. |
| E-submitted | Distinct E-selected original entry identities proven to have entered actual native submission after exact authorization: retained actual dispatch observation, or authoritative acceptance/execution proving that submission happened. A durable prepared intent alone is not dispatch. Ambiguous dispatch membership is unresolved, not assumed submitted or silently omitted. A later proof can resolve a new report’s membership without rewriting an old report. |
| E-accepted | E-submitted original entries with authoritative venue acceptance evidence. An attributable execution can prove acceptance occurred, but does not fabricate a missing accepted_at timestamp. Keep proof and timing availability separately. |
| E-filled | E-submitted entries with at least one positive, uniquely attributable native entry execution. Keep all source IDs and sums; retries are not members. Execution price/quantity/identity must be factual. |
| E-fully-filled | E-filled entries with a complete authoritative cumulative execution prefix reaching approved Q exactly and full-fill proof. Partial terminal cancellation is not full fill. Overfill/ambiguous quantity follows existing integrity rules, not a clamp. |
| E-terminal-accepted | E-accepted members whose original entry remainder is authoritatively terminal and whose attributable entry-execution history is complete through that terminal boundary. Filled exposure may still be open; entry terminality is not S-004 CLOSED. |
| E-missed | **Narrow diagnostic missed-entry definition:** E-terminal-accepted members with proven total entry fill quantity zero. Denominator E-terminal-accepted. Pending accepted entries are censored, not missed. Pre-submit capital denial, hard no-create, unaccepted native rejection, parser failure and presumed profitable moves are excluded and separately visible. No profitability/hindsight counterfactual or new cancellation/TTL is introduced. |
| T-evaluated | Distinct RPT-POS decisions where DYNAMIC TP actually evaluated its own prerequisites/selector using usable same-bound F-008 and sufficient frozen F-010 source evidence. Stop availability is not membership input. Preserve blocked preflight records separately from classified failures. |
| T-policy | T-evaluated members whose valid REQUIRED/PREFERRED/NONE thesis policy resolution actually executed, including valid-bound unavailable/ineligible thesis fallback evidence where the frozen selector permits it. |
| T-distance | Actual visited target candidates, keyed `(decision, original target ID)`, for which exact distance classification was evaluated. Do not include unvisited candidates just because they exist in the frozen collection. |
| T-selected | T-evaluated members with independently usable final selected TP. Preserve selected raw reference price and rounded actionable TP separately. |
| T-filled | T-selected members that later bind exactly to E-filled through the same initial decision/construction/tranche/native chain. Pre-entry target touches do not enter its post-fill path. |
| T-resolved-path | T-filled members with proven final observation horizon and full comparable path/ordering evidence sufficient to decide hit or no-hit under §6.4.6. Incomplete cases remain visible as unresolved, not quietly removed from the target-hit rate population. |

**Entry fill rate:** `ENTRY_FILL_RATE_SUBMITTED_ASOF_V1 = |E-filled| / |E-submitted|`, at the pinned evidence horizon. This is the one default for this report, not a ratio over selected or accepted entries and not an eventual-fill prediction. Open but source-proven zero-fill submitted entries may contribute to the as-of denominator; label them open. Unknown dispatch or incomplete execution coverage makes the full requested rate INCOMPLETE; retain known numerator/denominator and unresolved IDs without advertising the known subset as the full rate. Zero complete denominator is NOT_APPLICABLE.

**Entry time to fill:** For each E-filled member, use its original proven first actual submission cutpoint from RPT-LIFE/L-SUB and first attributable positive fill in authoritative execution chronology, consistent with the existing L07 submitted-origin observation. Store both raw time bases/provenance and `first_fill_effective_at − original_submitted_at` only when clocks/order are demonstrably comparable. No acknowledgment/receipt/generated timestamp substitutes for either endpoint. A missing original dispatch time despite later acceptance/fill proof is UNAVAILABLE for duration. No fills means no completed duration: still pending = INCOMPLETE/right-censored; proven terminal zero-fill = NOT_APPLICABLE. Retries do not restart the timer. A negative or materially ambiguous delta is not clamped to zero.

**Selection frequencies:** Entry TOO_SHALLOW and TOO_DEEP each use their exact classified E-depth member set as numerator and E-depth as denominator; expose affected opportunity IDs but do not merge candidates into a different default rate. ENTRY_TOO_DEEP_AFTER_ROUNDING uses exact primary F-008 reason on E-rounded divided by E-rounded, not the pre-round TOO_DEEP set. Native POST_ONLY rejection and cancellation have **separate numerator sets** over E-submitted; a combined view is their union, not a double-counted sum. A venue event must explicitly prove that reason. Current-hard technical incompatibility uses actual definitive incompatible members of E-authorized-check divided by E-authorized-check, with exact checked predicate and factual refusal retained; unknown facts are not hard incompatibility. Position geometry, Portfolio capital, unrelated parser failures and generic unavailability do not migrate into these classes.

**TP frequencies:** Thesis override is the actual successful thesis-selected branch on T-policy divided by T-policy; a PREFERRED fallback warning is separately retained and is not a successful override. NO_REACHABLE_TARGET is the exact primary F-010 reason among T-evaluated divided by T-evaluated, not all unsuccessful Position decisions. TOO_CLOSE and TOO_FAR are separate actual T-distance member sets divided by T-distance. Keep selected-target post-round `TARGET_TOO_CLOSE_AFTER_ROUNDING` and terminal `TARGET_TOO_FAR` reason separately alongside those candidate classes; do not count an unavailable input, unvisited target, later gross/net failure or post-round rounding error as a visited pre-round distance classification.

**Availability schema is diagnostic only:** AVAILABLE means the precise metric has a complete valid basis for its pinned horizon; INCOMPLETE means its relevant cohort/path/outcome is open or partially covered; UNAVAILABLE means required identity/source/timing/definition is missing, unsupported or conflicting; NOT_APPLICABLE means the explicit mode/cohort predicate excludes the metric or its complete denominator is zero. Each item retains its own status/reason/covered and unresolved member sets. A report with 18 available Entry items and one unavailable path item is not wholly complete. Zero members with proven enumeration differs from absent enumeration. There is no newly introduced trading enum, gate or fail-closed live rule. Correctly exposed analytical unavailability does not erase original owner facts.

#### 6.4.5 Original distances, age and eventual expectancy

Entry source values remain exactly those retained by F-008: raw selected-reference improvement `abs(M − r)`, percent `100 × abs(M − r)/M`, ATR units `abs(M − r)/received_ATR_15m`; rounded improvement substitutes the original rounded Entry for r. Publish **raw and rounded columns**, not an unlabeled replacement. Original Q18 received ATR is consumed exactly as it was, with no recovered hidden Set precision or latest-ATR lookup. A failed rounding diagnostic price never becomes selected Entry. Canonical age uses §6.4.3, not these distance formulas.

TP raw distance is `abs(selected_target_reference_price − original_Entry)` and rounded distance uses original rounded TP; both divide by the original received ATR_15m. Retain original direction, raw target type, tick, min/max configuration and work result. Equality/band/tick behavior belongs only to unchanged F-010. Reporting comparisons and displays cannot enter a gate.

For `eventual expectancy by entry-distance band`, require an explicit versioned band configuration with ordered nonoverlapping exact intervals, endpoint inclusion flags and `distance_basis = dynamic_entry.distance.raw_improvement.atr_units` for ENTRY_REPORT_V1. There is no invented production band grid. Bands partition the requested eligible distance scope; retain explicit out-of-band membership rather than dropping it. A different distance basis or grid requires a new report-definition/configuration pin. Set/Position configuration, direction, coin, context family and governed accounting currency stay in the grouping key; do not average different currencies or enable FX.

For each band, primary expectancy is the exact arithmetic mean of **net_realized_result in the governed accounting unit per actually filled tranche** with a canonical full-tranche FINAL. The denominator and numerator members are exact result_id+tranche_id pairs linked to original E-selected/E-filled membership, not delivery counts. Unfilled or unsubmitted selected opportunities are not zero-P&L trades. If any filled eligible member lacks FINAL, retain its ID and INCOMPLETE eventual cohort status; a clearly labeled completed-subset mean may be shown with separate denominator, never labeled full eventual expectancy. A complete band with no filled trades is NOT_APPLICABLE; missing bands/configuration or unknown lineage is UNAVAILABLE. Original FINAL values are copied from Lifecycle, not recalculated by Research; fees/funding remain included through that immutable net. The report never updates an Entry threshold or chooses a winning band for live use.

#### 6.4.6 Factual post-fill paths, target touch and excursions

The report request must pin an explicit **factual last-traded-price path profile**: venue/product/instrument, source and source-profile version, record kind (`ordered trade events` or `completed last-trade OHLC intervals`), resolution/timeframe and proof of coverage/order. These are source capabilities, not a fabricated venue API. Do not mix mark/index/bid/ask data with last-trade extrema or silently switch source/granularity. Source does not prescribe a universal timeframe; the chosen profile is part of the diagnostic report definition, is visible, and must be supplied rather than defaulted from today’s chart. Current BTCUSDT/1m cache support does not imply event-resolution or another instrument’s support.

**Window and anchor:** One original entry/tranche member begins at its first positive attributable entry execution in authoritative chronology, `t0`, with that actual execution price `p0`. The analytical anchor is explicitly the first-fill price, **not** planned Entry, a mutable later VWAP or accounting cost basis. Additional entry fills do not restart the path, reset p0 or create another member. Partial fill followed by terminal remainder cancellation still has one filled exposure path. If a material same-time ordering affects which execution is first, retain unresolved rather than choose lexical execution IDs. No fill means path metrics NOT_APPLICABLE.

The completed full path ends at the permanent last factual closing execution `t1 = FINAL.accounting_effective_at`, including only source-proven events at the boundary. Operational cleanup, financial finalization time and Portfolio receipt do not extend it. Temporary flatness in B9 cannot declare a completed report horizon. Before a full immutable FINAL/current accepted chronology exists, observed-to-`evidence_as_of` excursions may be displayed as **INCOMPLETE**, with open/censored horizon, not final-trade metrics. An additional post-intent fill remains ordinary factual exposure inside the same path; the report creates no close/reduction authority. B10 supplies the permanent horizon, not a new source subscription.

For exact path membership, use proven event order relative to t0/t1. Include a same-time event only when its position within the boundary is established, or when all permissible orderings provably give the same requested metric; otherwise that metric is unresolved. Never include an entire bar spanning t0 or t1 without sufficient finer boundary evidence. Factual execution prices can be retained as separately proven endpoint observations of the same traded-price kind, but cannot stand in for the missing intervening path.

Let `d=+1` for LONG and `d=−1` for SHORT. For a complete eligible path, including its first-fill anchor:

```text
signed_favorable_move(p) = d × (p − p0)
favorable_excursion = max(0, maximum signed_favorable_move over the path)
adverse_excursion  = max(0, maximum of −signed_favorable_move over the path)
```

These are exact **nonnegative price-unit magnitudes** with an explicit original instrument/unit and anchor, not new P&L or mark-to-market accounting. SHORT signs are not copied from LONG. Full-horizon MFE in the TP report uses the same favorable excursion; Entry adverse/favorable reports use the same full exposure horizon. No additional-fill VWAP reset, quantity weighting or hypothetical profit is silently added.

**Selected target:** Primary TP hit refers to the original **rounded actionable TP** in RPT-TP/ORDER_SPEC, with the raw selected reference price/type retained alongside it. LONG touch is `p >= rounded_TP`; SHORT touch is `p <= rounded_TP`. This is a diagnostic market-path touch, not proof of actual TP execution or TAKE_PROFIT close cause. Raw-level touch is not substituted for rounded-order touch. A touch before t0 is excluded. A complete path closing by SL/manual before any qualifying touch is no-hit through t1; prices after t1 are excluded. A partial entry uses t0 of its first actual fill and the same approved target.

**Time-to-target:** Earliest qualifying source-proven touch `thit` within the completed or observed post-fill interval; duration `thit − t0` uses comparable factual time/order only. A known post-entry hit can have an AVAILABLE hit flag before terminal close, but full-trade hit-rate/horizon completeness remains separately labeled. A full completed path with no hit has `hit=false`, duration NOT_APPLICABLE, and explicit terminal cause/horizon. Open or incomplete no-touch evidence is INCOMPLETE, not false.

**OHLC honesty:** Full, source-complete bars lying wholly within the interval can prove extrema and sometimes existence of touch. Their timestamp is an interval, not the exact first touch instant. Retain earliest-hit interval `[bar_open,bar_close)` and mark exact time-to-target UNAVAILABLE with reason `INTRABAR_TIME_UNRESOLVED` unless finer authoritative records establish thit. High/low order in the hit bar is not known: MAE before target remains UNAVAILABLE if whether an adverse extreme preceded the touch can affect the answer. Report an explicitly labeled bound/interval only as supplementary evidence, never substitute it for an exact metric. A coarse bar intersecting the entry/exit boundary with unknown sub-bar path makes affected extrema/hit evidence INCOMPLETE. Do not interpolate a plausible path from OHLC or count a pre-entry high as a hit. Complete finer supplied data can resolve a **new** report without editing the old one.

**MAE before target:** Same p0/d anchor; take adverse excursion from t0 through the first proven touch, inclusive. If the complete terminal path never hit, use t0→t1 with `censored_at_terminal_without_target=true`; keep this cohort separate from target-hit MAE rather than pretending a hit occurred. With unresolved touch ordering/boundary/path, MAE-before-target is unavailable/incomplete even when full-horizon MFE is knowable. If still open, any partial observed extrema are labeled censored/incomplete. Exact TP MFE uses t0→t1, not automatically stopping at target touch; no assumed actual exit merely because market touched.

**Target hit rate:** Primary full-horizon rate is `count(T-filled members with proven post-fill touch) / count(T-filled members)` for the pinned opportunity cohort. AVAILABLE requires terminal horizons and sufficient complete evidence to classify every member; source-complete no-hits remain in denominator. An unresolved/open member makes the full requested rate INCOMPLETE; expose known hits/known no-hits/unresolved IDs and optional bounds, not a misleading resolved-only success rate. Zero complete denominator is NOT_APPLICABLE. This is independent from Lifecycle TP-close frequency and does not fabricate executions.

#### 6.4.7 Target-family comparison and bounded diagnostic sensitivity

Use original F-010 selected types, not price proximity: LONG `PREVIOUS_DAY_HIGH` / SHORT `PREVIOUS_DAY_LOW` form the previous-day category; LONG `SWING_HIGH_1H` / SHORT `SWING_LOW_1H` form the 1h category. Preserve the exact original type/ID and traversal rank. Other permitted 15m/range types remain explicit separate categories, not dropped or relabeled as 1h/day. Compare target-touch rate, time-to-target, MAE/MFE and source availability using the same pinned opportunity/horizon definitions and direction/coin/TP-context-family/configuration partitions. A category with no eligible members is NOT_APPLICABLE, not missing evidence or zero performance.

`MIN_DISTANCE_SENSITIVITY` and `MAX_DISTANCE_SENSITIVITY` are two separately labeled diagnostic analyses, not automatic parameter selection. Pin the original F-010 baseline configuration and its exact MIN=0.75/MAX=4.00 evidence, complete original frozen reference/candidate inputs, original Entry/ATR/tick, family/hierarchy/thesis policy and original primary traversal. Require explicit alternative finite positive parameter values and research-config version/digest; each requested pair must satisfy min<=max. No unspecified sweep, arbitrary generated range, strongest-result selection or unrestricted Cartesian optimization is permitted. If the request has no alternative values, the sensitivity items are UNAVAILABLE (`RESEARCH_PARAMETER_SET_REQUIRED`), not claimed complete by a baseline-only report. This does not block live trading.

Minimum-distance sensitivity varies **only** the explicitly supplied research minimum, keeping the source baseline maximum and every other input fixed. Maximum-distance sensitivity varies **only** the explicit maximum, keeping the baseline minimum and all other inputs fixed. Preserve complete member comparability; report the original baseline candidate IDs/outcomes alongside each diagnostic alternative and its exact changed membership/selected target/reason/distance. All unvisited baseline references remain marked unvisited in the canonical record even when a diagnostic alternative visits them.

Implement diagnostic alternative evaluation by reusing the **same reviewed pure selection/traversal arithmetic**, not by replacing a canonical F-010 output or adding a parallel formula runtime. Canonical entry points always bind the frozen thresholds/configuration and retain their existing authority/type boundaries. An isolated report-only invocation can bind the explicitly versioned research candidate parameter in that pure calculation; its output type has no business IDs, decision publication, state writer, native handle or active-configuration writer. It is not accepted as MARKET_HANDOFF, APPROVE_REJECT, ORDER_SPEC, a successful started cycle or FINAL. Any refactoring necessary to share pure code must prove byte-/value-identical canonical behavior and keep existing F-010 tests unchanged. No live threshold, schema or supported mode is changed by this plan.

Where comparing an alternative target against the observed market path, label it **conditional target-touch on the original factual exposure window**, not a simulated alternative execution/fee/net result. The original Entry, fills and close horizon stay fixed for comparability; do not reuse actual FINAL as the counterfactual trade’s profit. No simulator, slippage assumption, synthetic fill, future target/reference, target-family retuning or new trading strategy is introduced. Alternative results cannot modify original references, source selections, price geometry, Set direction, grant capital or native intent. Promotion, should it ever be separately requested, continues through existing governed configuration/promotion procedures; the reporting path has no permission to call them.

#### 6.4.8 Entry source-completeness table — all 19 required items

Each E-number is a subitem of NR-153, not another normalized requirement. `Entry §51 Lnnnn` below means the exact list line in `docs/trading-methodology/methodology/POSITION_RULES.md`; calculation/output support is in §§21–22/47, and age support is the exact Set clause identified above. Cohort/window/denominator/path conventions reference §§6.4.4–6.4.7 and are explicitly diagnostic definitions. Review abbreviations in these two tables are **local scope references**, not new gate tokens: POS=B7A’s implementation/numeric/trading/persistence/replay/test reviews; LIFE=B9’s implementation/provenance/numeric/persistence/replay/test reviews; FINAL=B10’s accounting/numeric/persistence/replay/test reviews; REPORT=B12’s implementation/numeric/trading/persistence/replay/test reviews; ARCH=B13’s existing architecture/test/trading/numeric reviews. B3 provenance/persistence/replay/test review covers every imported path dataset. See §10.5 for full token names and assignments.

| Item | Frozen source | Producer | Retained basis | Consumer/report | Availability | Replay | Test | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E01 — LONG separately | Entry §51 L3225 | Set → Position; B7A | RPT-SET.direction=LONG and RPT-POS decision/mode/config/handoff digest; exact member IDs | Entry LONG partition of each applicable cohort; never netted with SHORT | AVAILABLE only with original direction binding; missing direction UNAVAILABLE | Original direction/partition fixed by pins | ENTRY-RPT-01; ENTRY-RPT-15 | POS; REPORT; ARCH |
| E02 — SHORT separately | Entry §51 L3226 | Set → Position; B7A | RPT-SET.direction=SHORT and same exact RPT-POS bindings; do not infer side from P&L | Separate SHORT partition, including direction-aware paths | Same original-binding rule; NONE not a successful directional member | No replay reversal or inferred side | ENTRY-RPT-01; ENTRY-RPT-15 | POS; REPORT; ARCH |
| E03 — coin | Entry §51 L3227 | Set/Position identity; B7A | Original symbol plus venue/product/account/environment namespace in RPT-SET/POS/CHAIN | Coin dimension on numerator and denominator members | Missing exact instrument identity UNAVAILABLE; never guess symbol | Same symbol text in another product/environment is distinct | ENTRY-RPT-02; ENTRY-RPT-15 | POS; REPORT; ARCH |
| E04 — Set family | Entry §51 L3228 | Set context; Position copies at B7A | Original entry_context.set_family plus Set ID/version/digest in RPT-SET and RPT-ENTRY | Entry-family partition; retain Set configuration separately | Missing context UNAVAILABLE; no name-based family inference | Original entry family, not current configuration or TP family | ENTRY-RPT-02; ENTRY-RPT-15 | POS; REPORT; ARCH |
| E05 — selected entry reference type | Entry §51 L3229 | Position; B7A | RPT-ENTRY.selected_level_id/type/reference_price/timeframe/producer binding and actual selection branch | Type dimension for E-selected; unsuccessful rows retain reason/no chosen reference | No usable selected reference: NOT_APPLICABLE for successful-type metric, not invented type | Equal prices never collapse different IDs/types | ENTRY-RPT-03; ENTRY-RPT-15 | POS; REPORT |
| E06 — entry improvement ATR | Entry §51 L3230 | Position; B7A | Original M, raw selected reference, rounded Entry, received ATR_15m and immutable handoff source; RPT-ENTRY raw/rounded atr_units | Raw and rounded improvement columns, exact original operands | Valid corresponding selection/calculation required; missing ATR UNAVAILABLE | No latest ATR/high-precision reconstruction; exact rational round-trip | ENTRY-RPT-04; ENTRY-RPT-15 | POS; REPORT |
| E07 — entry improvement percent | Entry §51 L3231 | Position; B7A | RPT-ENTRY raw/rounded improvement.price and original M; 100×improvement/M, original calculation result | Raw and rounded percent columns, no percent/fraction-unit confusion | M positive and valid original values required; absent is not zero | Same source operands and diagnostic basis retained | ENTRY-RPT-04; ENTRY-RPT-15 | POS; REPORT |
| E08 — fill rate | Entry §51 L3232 | Lifecycle facts B9; Research B12 | RPT-CHAIN, unique actual E-submitted IDs, E-filled execution IDs, approved Q and source coverage/cutoff; unresolved dispatch IDs | ENTRY_FILL_RATE_SUBMITTED_ASOF_V1 = filled/submitted; explicit known/open/unresolved sets | Full rate AVAILABLE only when cohort and status coverage complete; empty denominator NOT_APPLICABLE | Business-member count once despite retries/new duplicate arrivals | ENTRY-RPT-05; ENTRY-RPT-15 | LIFE; REPORT |
| E09 — time to fill | Entry §51 L3233 | Lifecycle; B9 | RPT-LIFE original proven submitted_at cutpoint, first positive execution ID/effective time and comparable clock/order proof | Per filled entry first_fill_effective_at−submitted_at; submit-origin label | Missing/comparability failure UNAVAILABLE; pending INCOMPLETE; terminal zero-fill NOT_APPLICABLE | Same original endpoints; retry never restarts timer | ENTRY-RPT-06; ENTRY-RPT-15 | LIFE; REPORT |
| E10 — missed-trade rate | Entry §51 L3234 | Lifecycle; B9; diagnostic definition B12 | Complete E-terminal-accepted IDs, exact terminal remainder proofs and entry execution member sets; E-missed zero-fill IDs | E-missed/E-terminal-accepted; report definition explicitly terminal accepted zero-fill, no hindsight profit | Incomplete execution/terminal proof INCOMPLETE; pending excluded as censored; empty denominator NOT_APPLICABLE | No count from a later profitable price move or repeated cancel message | ENTRY-RPT-07; ENTRY-RPT-15 | LIFE; REPORT; ARCH |
| E11 — TOO_SHALLOW skip frequency | Entry §51 L3235 | Position; B7A | RPT-ENTRY actual classified E-depth candidate IDs and too_shallow_level_ids, exact raw improvement/ATR, source reason | Distinct TOO_SHALLOW candidate members / E-depth; opportunity IDs retained alongside | Only actually classified candidates; input failures/unvisited not shallow | Same decision+level+stage once; no reason inferred from overall REJECT | ENTRY-RPT-08; ENTRY-RPT-15 | POS; REPORT |
| E12 — too-deep candidate frequency | Entry §51 L3236 | Position; B7A | RPT-ENTRY E-depth and too_deep_level_ids/count; actual raw classification TOO_DEEP | TOO_DEEP members / E-depth; distinct from post-round failure | Prerequisite absence not too deep; complete classified member set required | No merge with ENTRY_TOO_DEEP_AFTER_ROUNDING | ENTRY-RPT-09; ENTRY-RPT-15 | POS; REPORT |
| E13 — ENTRY_TOO_DEEP_AFTER_ROUNDING frequency | Entry §51 L3237 | Position; B7A | RPT-ENTRY E-rounded IDs, exact primary reason and selected raw/rounded values/tick/ATR | Matching post-round decision members / E-rounded | Rounding stage not reached => NOT_APPLICABLE; never infer from raw TOO_DEEP | Original selected reference/failure fixed; no retry another reference | ENTRY-RPT-09; ENTRY-RPT-15 | POS; REPORT |
| E14 — native POST_ONLY rejection/cancellation frequency | Entry §51 L3238 | Lifecycle; B9 | RPT-LIFE raw venue reason/event/provenance bound to original native/client/spec/auth identity; E-submitted | Separate rejection and cancellation numerator sets; each / E-submitted; union if combined | Local marketability prediction excluded; unproven reason UNAVAILABLE | Each original entry once per class; union not sum; unchanged economics | ENTRY-RPT-10; ENTRY-RPT-15 | LIFE; REPORT |
| E15 — hard non-market technical incompatibility frequency | Entry §51 L3239 | Lifecycle; B9 | RPT-LIFE exact spec/auth/current-hard-check outcome/predicate and current factual profile/metadata evidence; E-authorized-check | Definitive incompatible original entry members / actually evaluated hard-check cohort | Unavailable facts/ambiguous create not incompatible; parser/geometry/capital failures separate | Replay original check basis, not latest restrictions | ENTRY-RPT-11; ENTRY-RPT-15 | LIFE; REPORT |
| E16 — entry-reference age | Entry §51 L3240 | Set derives; Position retains B7A | Selected reference available_at, original market_snapshot_at, exact delta and copied age_seconds from RPT-SET/ENTRY | Canonical ceil(delta seconds), plus exact original basis | No selected reference NOT_APPLICABLE; missing basis UNAVAILABLE | Never report-time/decision-retry age; source timestamps unchanged | ENTRY-RPT-12; ENTRY-RPT-15 | POS; REPORT |
| E17 — eventual expectancy by entry-distance band | Entry §51 L3241 | Position B7A; Lifecycle B10; Research B12 | RPT-ENTRY raw atr_units, pinned band interval config; exact E-filled→tranche→FINAL result IDs/net/currency; unresolved IDs | Exact mean FINAL net per filled tranche by original distance band and direction/coin/entry family/config/currency | Missing FINAL makes eventual cohort INCOMPLETE; no filled members NOT_APPLICABLE; missing band definition UNAVAILABLE | No rebanding using current ATR/config; immutable FINAL never replaced | ENTRY-RPT-13; ENTRY-RPT-15 | POS; FINAL; REPORT; ARCH |
| E18 — adverse excursion after fill | Entry §51 L3242 | Lifecycle first/last fills B9/B10; factual archive B3; Research B12 | RPT-LIFE first-fill t0/p0/direction; RPT-FINAL permanent t1; RPT-PATH complete bounded last-trade members and extrema/order proof | max(0,max[−d×(p−p0)]) in price units over full factual exposure interval | Partial boundary/gap INCOMPLETE; unsupported path UNAVAILABLE; no fill NOT_APPLICABLE | Same pinned path/anchor; later fill does not reset, FINAL P&L not a proxy | ENTRY-RPT-14; ENTRY-RPT-15 | LIFE; FINAL; REPORT; ARCH |
| E19 — favorable excursion after fill | Entry §51 L3243 | Same original factual producers; Research B12 | Same RPT-LIFE/RPT-FINAL/RPT-PATH member set and original first-fill anchor; no substituted latest prices | max(0,max[d×(p−p0)]) over same full exposure interval, separate from adverse metric | Same completeness; known flat complete path can be zero, missing path cannot | Canonical data unchanged; no future information in live decisions | ENTRY-RPT-14; ENTRY-RPT-15 | LIFE; FINAL; REPORT; ARCH |

#### 6.4.9 TP source-completeness table — all 17 required items

Each T-number is a subitem of NR-154. `TP §48 Lnnnn` means the exact list line in `docs/trading-methodology/methodology/POSITION_RULES.md`; raw fields/selection semantics remain Part IV §44 and the unchanged F-010 sections. The same explicit diagnostic-definition and review-scope distinction applies.

| Item | Frozen source | Producer | Retained basis | Consumer/report | Availability | Replay | Test | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 — LONG separately | TP §48 L5469 | Set → Position; B7A | RPT-SET.direction=LONG, original RPT-TP snapshot and exact decision/config pins | Separate LONG TP cohorts; inclusive favorable touch uses >= | Original valid direction required | No mixed/opposite-direction regrouping | TP-RPT-01; TP-RPT-17 | POS; REPORT; ARCH |
| T02 — SHORT separately | TP §48 L5470 | Set → Position; B7A | RPT-SET.direction=SHORT, original RPT-TP snapshot and exact decision/config pins | Separate SHORT TP cohorts; touch uses <= and mirrored excursion sign | Original valid direction required | No direction inferred from return or later target price | TP-RPT-01; TP-RPT-17 | POS; REPORT; ARCH |
| T03 — coin | TP §48 L5471 | Set/Position; B7A | Exact original symbol/product/venue/account/environment in RPT-SET/POS/CHAIN | Coin partitions for candidate and target-path cohorts | Unknown identity UNAVAILABLE, not nearest symbol | All original namespaces retained | TP-RPT-02; TP-RPT-17 | POS; REPORT; ARCH |
| T04 — Set family | TP §48 L5472 | Set TP context; Position B7A | RPT-TP.thesis_context.set_family copied from tp_context.set_family, exact Set configuration and handoff digest | TP-context-family partitions; do not substitute Entry family | Missing/invalid context UNAVAILABLE | No lookup from current Set name/configuration | TP-RPT-02; TP-RPT-17 | POS; REPORT; ARCH |
| T05 — selected target type | TP §48 L5473 | Position; B7A | RPT-TP selected original level ID/type/price/timeframe/priority and exact producer binding | Selected-type dimension on T-selected/T-filled; failed selections retain no target | No usable target => NOT_APPLICABLE for selected-type item | Equal-price references retain independent IDs/types | TP-RPT-03; TP-RPT-17 | POS; REPORT |
| T06 — thesis override frequency | TP §48 L5474 | Position; B7A | RPT-TP actual thesis-selected branch, exact REQUIRED/PREFERRED/NONE policy and bound thesis ID; fallback warning separately | Successful thesis-selected T-policy members / T-policy | Policy/preflight not evaluated excluded and visible; invalid binding not override | No inference solely from selected ID equaling a possible thesis | TP-RPT-04; TP-RPT-17 | POS; REPORT |
| T07 — NO_REACHABLE_TARGET frequency | TP §48 L5475 | Position; B7A | RPT-TP exact primary reason, T-evaluated set, original traversal/pool evidence | NO_REACHABLE_TARGET decisions / T-evaluated | Missing input/economic/Stop reject is not this reason | Original reason preserved across report/replay | TP-RPT-05; TP-RPT-17 | POS; REPORT |
| T08 — too-close frequency | TP §48 L5476 | Position; B7A | RPT-TP actually visited T-distance IDs/classification TOO_CLOSE and exact original distance | TOO_CLOSE candidates / T-distance; post-round too-close status separate | Unvisited/missing prerequisite excluded; no invented evaluation | Candidate once per original decision; no merging failure classes | TP-RPT-06; TP-RPT-17 | POS; REPORT |
| T09 — too-far frequency | TP §48 L5477 | Position; B7A | RPT-TP actual first TOO_FAR/termination, visited candidate distance and unvisited IDs | TOO_FAR candidates / T-distance; TARGET_TOO_FAR primary reason retained | Source termination stops actual traversal; later candidates not counted | No optional diagnostic traversal counted as original traversal | TP-RPT-06; TP-RPT-17 | POS; REPORT |
| T10 — target distance ATR | TP §48 L5478 | Position; B7A | Original Entry, raw target and rounded TP, received ATR_15m, tick/config and RPT-TP raw/rounded atr_units | Separate raw/rounded favorable distance ATR columns | Valid corresponding original calculation required; missing ATR not zero | No latest ATR or Stop-distance-derived TP | TP-RPT-07; TP-RPT-17 | POS; REPORT |
| T11 — time-to-target | TP §48 L5479 | Lifecycle first fill/final horizon; B3 path archive; Research B12 | RPT-LIFE t0 and RPT-PATH earliest qualifying rounded-target touch/time/order; RPT-TP target/direction | Exact thit−t0 when event-resolved; retain hit interval if only bars | Never-hit terminal => NOT_APPLICABLE duration; intra-bar exact time UNAVAILABLE; pre-entry touch excluded | Original path/start/target fixed; no TP-close timestamp substitution | TP-RPT-08, TP-RPT-09; TP-RPT-17 | LIFE; FINAL; REPORT |
| T12 — MAE before target | TP §48 L5480 | Same factual sources; Research B12 | RPT-PATH prefix through first proven post-fill target touch; t0/p0/d; t1 and censor flag for terminal no-hit | Adverse magnitude before hit; censored no-hit MAE separately labeled | Hit-bar adverse-order ambiguity UNAVAILABLE; open/incomplete path INCOMPLETE | Do not move adverse extrema from after-hit into before-hit period | TP-RPT-10; TP-RPT-17 | LIFE; FINAL; REPORT |
| T13 — MFE | TP §48 L5481 | Same factual sources; Research B12 | Complete RPT-PATH t0→permanent t1 and original first-fill p0/d; selected target lineage | Full-horizon favorable price-unit magnitude, not final P&L or clipped target gain | No fill NOT_APPLICABLE; absent/full-horizon gap not zero | Same anchor despite later partial fills or target touch | TP-RPT-11; TP-RPT-17 | LIFE; FINAL; REPORT |
| T14 — target hit rate | TP §48 L5482 | Lifecycle factual horizon; B3 path; Research B12 | All T-filled IDs, rounded target/direction, proven hits/no-hits and unresolved path member sets | Proven hit count / T-filled; full rate requires all members resolved | Zero complete denominator NOT_APPLICABLE; unresolved member INCOMPLETE, not false or dropped | No rate change from duplicate executions or report retries | TP-RPT-12; TP-RPT-17 | LIFE; FINAL; REPORT |
| T15 — previous-day vs 1h target behavior | TP §48 L5483 | Position original type; actual outcomes/path; Research B12 | RPT-TP original PREVIOUS_DAY_HIGH/LOW versus SWING_HIGH_1H/LOW_1H types, ID/traversal rank; same hit/time/excursion members | Compare source-defined type families, split direction/coin/TP Set family/config; other families retained separately | Empty known family NOT_APPLICABLE; unresolved types not assigned by price | Original type survives chart/config changes | TP-RPT-13; TP-RPT-17 | POS; LIFE; FINAL; REPORT |
| T16 — minimum-distance sensitivity | TP §48 L5484 | Position frozen evidence B7A; Research-only B12 | Original baseline MIN/MAX/config/candidate collection, Entry/ATR/tick/family/thesis; explicit alternate-min list/version; same pinned cohort/path | One-axis diagnostic min alternatives with baseline max unchanged; record selection/reason/conditional touch only | No explicit alternatives UNAVAILABLE; incomplete immutable candidate inputs not substituted | Each alternative pinned; no canonical record/threshold/FINAL modification | TP-RPT-14, TP-RPT-16; TP-RPT-17 | POS; REPORT; ARCH |
| T17 — maximum-distance sensitivity | TP §48 L5485 | Position frozen evidence B7A; Research-only B12 | Same original complete input manifest; explicit alternate-max list/version and baseline min fixed | Separate one-axis max alternatives; never merge with min sweep or optimize a combined grid | No explicit alternatives UNAVAILABLE; unknown chronology preserves affected path availability | Same baseline/cohort under rerun; new parameter set new diagnostic report | TP-RPT-15, TP-RPT-16; TP-RPT-17 | POS; REPORT; ARCH |

#### 6.4.10 Pinning, immutable report publication and restart

Use the existing research pin helpers with explicit methodology v1.2.15 and unchanged contract-version/numeric-policy pins. Each diagnostic report additionally binds: report definition/name/version/content digest; opportunity window and evidence horizon; cohort and denominator definitions; account/environment/product/currency and direction/coin/context-family keys; exact Set and Position configuration IDs/versions/content digests; Research configuration/version/digest; original distance-band basis/intervals; path kind/profile/source/granularity/completeness policy; explicit alternative min/max lists and fixed other parameters; and the complete accepted source/member/revision/manifest/digest set. A source-count aggregate without reconstructible member IDs is insufficient.

Derive or acquire a **report-local** semantic identity from that complete canonical pin+source-manifest binding using the existing canonical digest helper and Research namespace. This is not a replacement for any opaque business identifier. First successful report publication atomically stores report semantic identity, pins, complete output/member references, availability/reasons and first generated_at in the existing SQLite ResearchStore. Generated_at is metadata excluded from semantic calculation; an exact rerun returns the original report identity/content/first generated_at rather than generating a different value only because the clock moved. A separately requested execution attempt can retain its own diagnostic attempt metadata without modifying the semantic report.

All exact numerical results persist as finite canonical decimals when exact, or reduced integer numerator/positive denominator for nonterminating rationals; no binary float/SQLite REAL or context-rounded gate value is accepted. Display precision is explicit metadata and never changes exact stored membership or values. Foreign currencies cannot be silently averaged. Report source and output JSON use the existing canonical helpers, not a second serializer. Preserve every copied original source-prescribed scalar quantization unchanged. Exact rational provenance is an additional retained basis, not permission to replace a required serialized scalar with another numeric policy. Where a report scalar falls under TT_NUMERIC_V1 §2 economic ratio/percentage output, apply the existing Qratio=1e−18 floor for that serialization only; retain the exact pre-report numerator/denominator and use it for band membership and arithmetic. Do not apply Qratio to money, native price, quantity, timestamps or an otherwise unspecified diagnostic field. For the ENTRY-RPT-04 percent oracle, exact work is100/51 and its Qratio scalar is1.960784313725490196; neither representation feeds a canonical decision.

Read-only import takes explicit immutable source revisions/manifests for each owner. It does **not** claim a simultaneous cross-owner database snapshot. Validate every exact link and retain missing downstream links as not-yet-created/unknown; never chase a mutable latest pointer until a convenient successful chain appears. Complete member enumeration/coverage and record digests become the pinned dataset. Reading a later FINAL or additional path history yields a new dataset/report pin, not a rewritten old report. Import/retry cannot mint grant/tranche/execution/result IDs.

Same known accepted business/source identity with changed content uses the existing owner integrity rules; Research marks its dataset UNAVAILABLE/conflicting and retains the contradictory copies plus exact original links. It does not directly write an owner’s incident/health table, downgrade a native conflict to a report update, send a new business message, or fabricate reconciliation authority. Existing canonical incidents, when present in retained evidence, are referenced read-only and remain under their original owner. A proven alternate representation is usable only with the original authority’s alias proof, not a report-generated alias.

On restart restore original Research/configuration/source manifest, exact candidate/member sets and availability before rebuilding a report. No latest Position settings, current chart types, wall-clock age or near-time fill association. Missing archived bytes/digest mismatch is explicit unavailable data, not a request to silently regenerate history from a different source. A report commit is all-or-none locally: before commit it has no published report; after commit retry returns the same record. Source objects staged before a failed manifest/report commit may remain unreferenced, but never appear as committed cohort members. Committed original source facts survive any failed read-only report import and can be retried. No diagnostic database commit is atomic with a foreign business effect.

**Additional reporting invariant (specialization of existing global invariant 6, not invariant 21):**

```text
RESEARCH_REPORTING_HAS_NO_CANONICAL_DECISION_AUTHORITY
```

No automatic threshold update, Entry-distance change, TP min/max change, target-family choice, Set update, capital change or native execution change. Report code has read-only canonical access and no promotion writer. A changed report/sensitivity result cannot change an already-started or future canonical decision through an implicit feedback route; only the existing separately authorized configuration path can change future configuration. Missing report data cannot block a canonical trade unless an independent existing live rule already requires that same factual evidence.

#### 6.4.11 AT-NR-153 — ENTRY-RPT-01–15 local acceptance matrix

These are **planned** source/definition-derived tests, not a claim that backend tests ran during R6 editing. All wire/owner fixtures must be otherwise source-valid and exercise the actual producing owner path, not hand-built expected report rows. Position tests begin B7A, Lifecycle sources B9, outcome proof B10, generic archival B3. B12 executes the complete read-only report path with real existing SQLite ResearchStore extensions and actual retained-source manifests. B13 verifies the same behavior, not first implements it. Each case asserts all relevant source-list rows and exact local membership/content/replay, alongside existing canonical acceptance tests.

| Test | Source/explicit-report-definition fixture | Required retained/report assertion | First local execution scope |
| --- | --- | --- | --- |
| ENTRY-RPT-01 — LONG/SHORT split | Mirror source-valid original decisions, source values and factual paths across the two directions; retain otherwise equal grouping metadata. | Two separate direction/member sets. Exact mirrored excursion magnitudes match without pooling LONG and SHORT, changing Set direction or inferring direction from profit. | B7A original identity; B12 report |
| ENTRY-RPT-02 — coin / Set family | Provide two valid instruments and two original entry_context families with equal numerical metrics; include an independently different tp_context family. | Neither coin nor Entry family cohorts merge; the Entry report reads entry_context, not TP family or current Set name. Source importer distinguishes venue/product/environment as well as symbol. | B3 import; B7A evidence; B12 |
| ENTRY-RPT-03 — reference type / equal price | Two producer-proven reference IDs/types share a price; exercise actual valid F-008 ranking/selection in separate fixture worlds. | Report uses the actual chosen ID/type/priority/binding. Equal price cannot pick a different reference, invent a type or collapse candidate history. | B7A; B12 |
| ENTRY-RPT-04 — improvement ATR / percent | Use the existing source-valid LONG M=102, received ATR=10, selected reference=100, tick=0.1 fixture; actual F-008 Entry=100. Change later active ATR/configuration only. | Raw and rounded improvement price=2, ATR=1/5, percent=100/51 exactly (100×2/102); report serialization preserves the rational. Later ATR=20 cannot change either metric. The overall Stop-unavailable REJECT fixture may retain this usable Entry and independent TP without success authority. | B7A actual selector; B12 exact report |
| ENTRY-RPT-05 — fill rate with exact cohort | Four source-proven submitted original entries: one fully filled, one accepted terminal zero-fill, one accepted/open with proven zero fills at cutoff, one actual unaccepted venue rejection. Add a definitive pre-submit no-create and a selected/no-authority opportunity. | Submitted=4, filled=1, as-of fill rate=1/4. The two non-submitted examples do not enter this denominator; open/unaccepted/accepted categories remain visible. Duplicate arrival/restart keeps exact member sets. Remove a required execution-coverage proof: full rate becomes INCOMPLETE, not unchanged AVAILABLE. | B9 source facts; B12 SQLite/report |
| ENTRY-RPT-06 — authoritative time to fill | Actual comparable submitted_at=t0, first positive execution=t0+3 seconds; receive the execution much later, then replay it. Contrast missing original dispatch timing and incompatible clock proof. | Exact completed duration=3 seconds, unaffected by receipt time. Missing comparable endpoints => UNAVAILABLE, no fill while open => INCOMPLETE, terminal zero-fill => NOT_APPLICABLE; no zero fabrication or timer reset. | B9; B12 |
| ENTRY-RPT-07 — missed-trade rate without hindsight | Use accepted terminal entry cohort with one fully filled original order and one proven terminal zero-fill order; another accepted order is pending. Add unaccepted POST_ONLY rejection/capital denial and later price rally. | E-terminal-accepted=2, E-missed=1, rate=1/2. Pending member is censored; unaccepted rejection/capital denial and price rally do not create missed-entry members. Incomplete zero-execution proof cannot count as a miss. | B9; B12; no-feedback assertion |
| ENTRY-RPT-08 — TOO_SHALLOW classification | Actual F-008 depth pool at M102/ATR10 contains valid improving LOW references 101.5,100,85 with truthful producer identities; valid family/policy makes these depth-classified candidates. | Raw ATR distances 0.05,0.2,1.7; shallow ID count1 / depth count3. Keep the original candidate TOO_SHALLOW evidence even if an eligible reference selects and overall opportunity later rejects. A wrong-side or missing-input record adds no shallow member. | B7A; B12 |
| ENTRY-RPT-09 — pre-round and post-round too-deep | Use actual TOO_DEEP candidate above and a separate source-valid selected-reference post-round failure: LONG M100/ATR1, raw reference98.75, tick0.1 gives raw distance1.25 and rounded Entry98.7 with distance1.3. Include exact valid tick/reference provenance. | First remains candidate TOO_DEEP; second is original primary ENTRY_TOO_DEEP_AFTER_ROUNDING, in E-rounded but not a pre-round TOO_DEEP candidate. No successful Entry from the failed diagnostic rounded price; no next-reference repair. | B7A numeric/reason producer; B12 |
| ENTRY-RPT-10 — actual native POST_ONLY event | Source-proven POST_ONLY reject and cancel facts name original authorized entries; separately provide a locally predicted crossing, generic reject and two causes for one original entry. | Only actual venue-proven POST_ONLY members enter corresponding reject/cancel sets. Keep separate subcounts, union once when combined. No prediction, capital block or duplicate delivery becomes native refusal. | B9; B12 |
| ENTRY-RPT-11 — hard non-market technical incompatibility | Actual complete spec/auth join with a definitive current tick/step/profile incompatibility; contrast mere newer compatible revision, unavailable facts, Position geometry rejection and a Portfolio denial. | Only definitive actually evaluated hard incompatibility is numerator over E-authorized-check; all other classes remain distinct. No marketability pre-check, reprice, current-config overwrite or native operation from reporting. | B9; B12 |
| ENTRY-RPT-12 — original reference age | Original market_snapshot_at−selected.available_at is 60.750000 seconds; preserve producer integer age61, then restart/generate report much later. | Exact delta60.75 and canonical ceiling61 persist. Neither matched_at/evaluation receipt nor current wall-clock replaces market_snapshot_at; no use of pivot timestamp. | B7A; B12 |
| ENTRY-RPT-13 — expectancy by pinned distance band | Explicit test-only band [0.10,0.50) over original raw Entry ATR distance; two filled member tranches have immutable same-currency FINAL net18.9 and −8.9. Add another filled member without FINAL; later alter active ATR/band settings. | Completed subset sum10/count2 => mean5. With missing third FINAL, full eventual cohort is INCOMPLETE and unresolved ID visible, not full mean5 or zero imputation. In a separate complete two-member report mean5 is AVAILABLE. Original band/config/result IDs persist; no currency mixing or live feedback. | B7A band source; B10 actual FINAL; B12 |
| ENTRY-RPT-14 — exact post-fill excursions | Proven LONG first fill100; complete ordered post-fill path100,98,105,110,112,109 through permanent closing execution; pre-fill price120 and post-close130 excluded. Mirror SHORT100,102,95,90,88,91. Include later partial fill without changing anchor. | Both directions adverse2/favorable12 price units; first-fill anchor retained across partial fills. Missing interval or boundary-crossing OHLC with unknown subperiod makes affected metric INCOMPLETE; FINAL P&L alone is insufficient. No hindsight path reaches any live decision input. | B3 archival; B9/B10 horizon; B12 |
| ENTRY-RPT-15 — crash / replay / incomplete dataset | Inject faults at actual TX.opportunity/source capture, Lifecycle fact capture, source-object publication, SQLite manifest/report commit; rerun exact pins/source manifest after restart. | Precommit source fact does not create a report member; committed owner source survives failed Research import. Pre-manifest orphan is not membership; after-report-commit retry returns same content/ID/first generated_at. Known ID changed content quarantines diagnostic copy and preserves original owner integrity, with no cross-owner write. | B3/B7A/B9/B10 local sources; B12 full report; B11 source-only stress |

#### 6.4.12 AT-NR-154 — TP-RPT-01–17 local acceptance matrix

Use the same source-valid fixture and local-production discipline. Tests must exercise actual F-010 result retention, not a prefilled selected target; independently source-derived baseline outcomes remain unchanged. Alternative min/max values below are **test-only explicit Research configurations**, not production defaults or permission to tune live thresholds.

| Test | Source/explicit-report-definition fixture | Required retained/report assertion | First local execution scope |
| --- | --- | --- | --- |
| TP-RPT-01 — LONG/SHORT split | Mirror original usable LONG/SHORT TP selections and post-fill paths with the same absolute distance. | Separate direction cohorts; LONG touch>=target and SHORT touch<=target, exact mirrored signs; no Set-direction feedback. | B7A; B12 |
| TP-RPT-02 — coin / Set family | Identical numerical target inputs for different symbols and original TP context families; Entry family may differ. | Group by original instrument and tp_context.set_family/configuration, never infer family or use Entry family as default. | B3/B7A; B12 |
| TP-RPT-03 — exact selected target type | Equal-price producer targets have distinct IDs/types; actual F-010 traversal selects one with exact family/rank. | Retain selected ID/type/raw reference and rounded actionable TP. Equal prices/current chart cannot reclassify the selected family. | B7A; B12 |
| TP-RPT-04 — thesis override frequency | Four valid policy-evaluated decisions: actual eligible thesis selects in one; NONE/default in another; valid PREFERRED fallback with warning in another; valid-bound REQUIRED calculation failure in another. | Actual successful thesis-selected count1/T-policy4 =1/4. Fallback warning remains distinct. No override inferred merely from a matching price or selected ID. Preflight identity-invalid record is not a policy evaluation. | B7A; B12 |
| TP-RPT-05 — NO_REACHABLE_TARGET | E100/ATR10/tick0.1, complete valid default target pool has only a favorable allowed HIGH at105; actual traversal records TOO_CLOSE then exhausts. Contrast a missing ATR, wrong-side pool and later F-012 rejection. | Actual primary NO_REACHABLE_TARGET counts once in T-evaluated; TOO_CLOSE candidate remains separately countable. Missing prerequisite or another failure class is not relabeled. | B7A actual F-010; B12 |
| TP-RPT-06 — too-close / too-far distinct | Under a valid family/default policy use same-type HIGH targets with proven available_at ordering:105 first,145 second,150 third, E100/ATR10/tick0.1. | Visited105 has distance0.5/TOO_CLOSE;145 distance4.5/TOO_FAR terminates;150 remains unvisited. Each class numerator1/visited-distance denominator2. Optional diagnostic traversal cannot add150 to canonical candidate frequency. Post-round failure remains separate. | B7A; B12 |
| TP-RPT-07 — original target distance | Actual valid selected raw/rounded TP110, Entry100, received ATR10, tick0.1; change only later active ATR/configuration. | Raw and rounded distance10/10=1; original target/ATR pins persist. Stop unavailable does not suppress the independently evaluable TP or its report record. No output from a Stop-distance proxy. | B7A; B12 |
| TP-RPT-08 — time-to-target and pre-entry touch | Using exact ordered LONG post-fill path from ENTRY-RPT-14, t0=0s, price110 first occurs at3s; include pre-fill touch120. Mirror SHORT target90. | First post-fill hit at3s, time-to-target3s. Pre-fill touch excluded. Replace events by a hit-containing complete bar: retain hit interval, exact time UNAVAILABLE unless independently proven. Boundary-spanning bar cannot invent a post-fill hit. | B3/B9/B10 sources; B12 |
| TP-RPT-09 — target never hit / early close | Complete post-fill LONG path ends at factual SL/manual close below rounded TP with no prior touch. Add a touch strictly after permanent close; contrast an open/incomplete path with no observed touch. | Completed member hit=false, no time-to-target, terminal no-hit censor reason; post-close touch excluded. Incomplete/open member hit unresolved, not false. TAKE_PROFIT/SL text alone cannot prove the price-path answer. | B9/B10; B12 |
| TP-RPT-10 — MAE before target | LONG first fill100, then98,110(first hit),95,112 before terminal close; exact source event ordering. Contrast OHLC hit bar whose low timing is unknown. | Before-target MAE=2, not5; full-horizon adverse=5 remains separately knowable. Unknown hit-bar adverse ordering => MAE-before-target UNAVAILABLE even when full-horizon extrema are available. Terminal no-hit case uses labeled censored t1 endpoint. | B3/B9/B10; B12 |
| TP-RPT-11 — MFE | Full complete factual LONG path100,98,110,112,109 with target110 and later permanent close; partial fill arrives after original first fill. | Full-horizon MFE12, not clipped target-distance10 or final gain9. Original first-fill anchor unchanged by partial fills; no inference from immutable FINAL alone. | B3/B9/B10; B12 |
| TP-RPT-12 — exact target hit-rate cohort | Two T-filled members have complete terminal paths, one hit and one no-hit. Then a third filled member has an unresolved path. Retry all source/report deliveries. | Complete two-member rate1/2. Three-member requested full rate INCOMPLETE with known hit/no-hit/unresolved IDs, not resolved-only1/2 as full rate nor treating unresolved as false. Repeat reports do not duplicate denominator. Empty complete cohort NOT_APPLICABLE. | B9/B10 source; B12 SQLite/report |
| TP-RPT-13 — previous-day versus 1h | Original selected PREVIOUS_DAY_HIGH/LOW and SWING_HIGH_1H/LOW_1H references include equal-price examples; add 15m and range targets. | Retain exact original families/ranks; compare hit/time/excursion on same pinned cohorts, split direction/coin/TP family. Other types stay separate, not reclassified by price or current day boundary. | B7A; B12 |
| TP-RPT-14 — minimum-distance sensitivity | Same frozen inputs E100/ATR10 with eligible same-type110 then115 in source order, valid NONE policy and baseline min0.75/max4.00. Explicit test Research alternative minimum1.25 only. | Canonical baseline still selects110. Diagnostic minimum1.25 skips distance1 and can select115 at1.5; max stays4.00 and all source/Entry/config lineage fixed. Original primary traversal not rewritten; no auto-promotion, hypothetical fill or replacement FINAL. | B7A original full input; B12 report-only selector reuse |
| TP-RPT-15 — maximum-distance sensitivity | Original valid single target135, E100/ATR10, baseline0.75/4.00; explicit test-only alternative maximum3.00 with min unchanged. | Baseline selects135 at3.5. Diagnostic max3.00 produces TARGET_TOO_FAR; min remains0.75. Record both versioned results and same cohort; no inferred alternative profit. Missing explicit alternatives => UNAVAILABLE rather than invented sweep. | B7A; B12 |
| TP-RPT-16 — no live feedback / authority | Vary saved report metrics, selected bands and sensitivity outputs; make ResearchStore unavailable; trap active-config writes, owner writers, native calls and promotion calls. Replay existing canonical inputs. | Canonical F-010/Entry/Set/Portfolio/Lifecycle outputs remain unchanged for original and independently started cycles absent separately authorized config change. Report code cannot invoke promotion or persist business success IDs. Report unavailability is not an added trading block. | B12 actual report path; B13 existing dispatcher/import isolation |
| TP-RPT-17 — restart / replay / partial source history | Restart between source archival, dataset-manifest and full report commits; activate different live config and submit a new separately pinned Research sweep. | Old pins/member order/type/path/hit/availability/report identity/content preserved. New sweep/source manifest yields new immutable report only. No latest/nearest-time/price association, duplicate result member, overwritten report or canonical source repair. | B3/B7A/B9/B10 source tests; B12 report; B11 source stress |

#### 6.4.13 Shared documentary ingestion and full-report completion checks

In addition to all named cases, B3/B12 must test: wrong instrument/profile/price kind, unsupported acquisition (including non-BTC input to the current BTC-only downloader), missing pages/ranges/watermark, duplicate raw source ID same content, same ID changed content, data imported after original observation under a complete archival proof, stale mutable cache replacement, filesystem-before-manifest crashes, missing object referenced by a manifest, and ambiguous boundary bar chronology. A valid explicit supplied dataset for another symbol must remain a distinct dataset even when its prices/times match BTC; it cannot be claimed fetched by the restricted downloader.

Verify mode-specific NOT_APPLICABLE; an independently usable F-010 result retained despite unavailable Stop; incomplete fill/target/FINAL outcomes; no denominator from successful trades alone; no legacy accounting fallback; and a report-only source gap that leaves a separately valid canonical decision unchanged. Read-only credentials/interfaces must reject writes and have no promotion/native command dependency. Same source report input under reordered delivery produces identical semantic records; extra physical diagnostic arrivals may retain truthful separate observations under NR-152 without changing these business-member rate denominators.

A complete implementation satisfies **19/19 Entry mappings and 17/17 TP mappings**, all 32 named cases and the shared matrix, including correct unavailable behavior where a particular supplied historical dataset lacks necessary resolution. This is capability/test-plan completeness, not a false assertion that every historical market path, current native profile or unimplemented report is already AVAILABLE. Unresolved source limitations are visible report outcomes, never lost requirements or fabricated numbers.


## 7. Transaction matrix and required mechanisms

`TX.*` below defines a semantic atomic boundary, not necessarily a new transaction helper or one transaction spanning business owners. All store composition uses the existing PostgreSQL UoW and connection-bound stores. Native external calls occur **after** their durable intent transaction; native ambiguity is reconciled by the retained intent, never hidden inside a database atomicity claim.

| Transaction ID | Boundary | Existing support | Required extension/mechanism | Owner / checkpoint | Acceptance tests |
| --- | --- | --- | --- | --- | --- |
| TX.owner | Generic owner state+required outboxes+inbox consumption | FN.UOW/FN.CAS/FN.MSG | One connection/transaction; owner conditional writes, canonical conflict checks and durable completion. Delivery claim is not committed business success. NR-151/NR-152 use the existing owner intake/recovery transaction for immutable captured-arrival/attempt metadata and actual recovery/failure observations (§7.6); not a 27th mechanism. Same captured instance has one classification receipt, distinct from economic dedupe. | B2 primitive; each behavior owner | Fault after every write; state/outboxes/consumption all-or-none; same input once; changed input conflict. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.preflight | Known-evidence recognition and contradiction capture | Existing accepted factual stores/UoW; parse-first path needs extension | Resolve raw exact anchors and compare full accepted binding before ordinary parsing. Commit known challenge+quarantine+required incident/outbox in a separate owner checkpoint that later ordinary-batch rejection cannot roll back. | B3 intake; Set B5B; Lifecycle B9/B10; consuming Portfolio | Known altered item plus malformed companion; omission vs null; precommit crash neither, post-preflight ordinary rollback keeps challenge, retry one identity. |
| TX.facts | Ordinary accepted factual response/history+required owner delivery | FN.FACT/FN.RECON/FN.MSG | Validate complete ordinary batch after preflight, accept immutable facts and provenance and compose required outbox under one UoW; no partial ordinary batch. At the receiving owner, capture NR-151/NR-152 factual observation references with the accepted facts/history; preserve the ordinary batch and earlier preflight separation. | B3 technical normalization; receiving owners B5B/B8A/B9/B10 | Invalid companion leaves no partial ordinary facts; previously committed challenge preserved; source aliases and same-ID conflicts. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.scope | Portfolio scope/state+COINS revision publication | FN.PORT/FN.SCOPE/FN.MSG | Current governed account/day/capacity/health/incident checks; persistent monotonic scope revision and COINS outbox commit together. Include NR-151 scope/gate outcome, complete evaluated reasons and state/configuration/capacity observation history in this same commit, including source-defined blocked/unavailable scope outcomes. | Portfolio B8A | Scope row/outbox rollback; concurrent updates; stale/changed revision; no initial grant or approval fabricated. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.day | Governed day/base/latch transition | FN.PORT/FN.CAS; canonical day records to add | Persist exact boundary instants/base evidence/config and existing latch history; rollover serialized with receipt/day posting; no wallet double-credit. Include NR-151 day/base/latch/recovery observation and its exact basis in the same day transaction, without changing base or A-009 semantics. | Portfolio B8A/B10 | Midnight/DST, reconstruction unavailable, disabled/re-enabled latch, historical receipt concurrent with rollover. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.setcalc | Set analytical/indicator checkpoint acceptance | FN.FACT/FN.CAS | Persist accepted series/population ancestry and exact work state without publishing a MATCHED decision; same source identity progresses once. B5B composes this into actual owner event processing. Retain independently bound formation-trigger and classifier evidence; AT-NR-068-CF A–D excludes trigger-to-classifier numeric/availability edges. | Set B5A kernels/checkpoint tests; B5B durable consumption | Full replay vs checkpoint, duplicate candle, malformed/zero close, changed membership and crash before checkpoint commit. AT-NR-068-CF A–D. |
| TX.set | Trigger/event evaluation+final MATCHED+frozen record+handoff | FN.SCOPE/FN.EPOCH/FN.FACT/FN.MSG | In one Set UoW commit required trigger consumption, result/cycle and reference bindings, frozen record, exact MARKET_HANDOFF and outbox. No visible partial match. Join independent eligible formation and applicable classifier/generic direction plus common handoff gates only here (§5.2); failure retains its separate unmatched reason without success IDs/outbox. | Set B5B | Fail each of record/event/handoff/outbox writes; restart retries same IDs/deadlines; CLOSE/reopen race; changed input conflict. AT-NR-068-CF A–D. |
| TX.monitor | F-013 activation/reducer/sticky requirement+signal | FN.SYNC/FN.CAS/FN.MSG | Acquire original-entry requirement key and freeze first reason/time/content; write state+signal/outbox atomically when exact binding exists. Unbound raw transition retained without guessed envelope. | Set B6 | TRUE/unavailable/terminal precedence; acquire race; partial-fill/recovery no remint; record-present vs absent retry; terminal dominance. |
| TX.opportunity | Initial Position decision+configuration/geometry pin+APPROVE_REJECT | FN.PIN/FN.MSG | First handoff evaluation pins configuration and retained geometry; one initial decision and outbox, no successful construction IDs or completed construction gates. | Position B7A | Concurrent evaluation/crash, config refresh between retries, initial REJECT no downstream grant authority. |
| TX.grant | Non-reserving Portfolio grant issue+CAPITAL_AND_LIMITS | FN.GRANT/FN.MSG/FN.PORT | Exact persisted initial APPROVE binding, current grant gates/facts, unique grant/outbox; does not reserve slot or capital. Include NR-151 full actual gate outcome/reasons and issue or blocked/unavailable history. Successful issue has its existing grant/outbox; a denial retains evidence with no fabricated grant/reservation or success publication. | Portfolio B8B | Duplicate APPROVE same grant; changed initial decision conflict; capacity unavailable; no side effect on commitment buckets. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.construction | Successful construction+ORDER_SPEC+TWO outboxes | FN.CONSTRUCT/FN.SPEC/FN.UOW/FN.MSG | Use one outer UoW/connection for existing construction result store and spec store plus CONSTRUCTED→Portfolio and ORDER_SPEC→Lifecycle outboxes. Store-local writes may not independently commit. Failed outcome has own failure result/outbox, no success spec. | Position B7B | Fail any of four writes and inbox completion: no partial success; both output arrival orders; duplicated scalar/digest equality; no success IDs on failure. |
| TX.hold | Current H/slot booking+config pin+authorization+outbox | FN.AUTH/FN.PORT/FN.COOLDOWN/FN.MSG | Under same scoped frontier/current Portfolio serialization, verify exact constructed values and current limits/day/cooldown, consume grant, book H+slot, pin attempt, store SUBMIT_AUTHORIZED and outbox. Include NR-151 current gate/denial evidence, successful grant consumed_at/H/slot/auth cutpoint and original configuration/cap basis. A denied outcome may retain observations but no success hold/slot/auth/outbox. Captured technical aborts follow §7.6, not partial booking. | Portfolio B8C | Two last-slot constructions, no H=C shortcut, stale grant, concurrent incident, rollback after hold/before outbox; first bookable wins. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.native | Durable native intent before external side effect | FN.START/FN.SUBMIT/FN.CLOSE | Complete exact spec/auth/current hard/profile join; persist intent/client ID/authorized quantity then commit before external API call. Reconcile ambiguous outcome by the same persisted identity. Include NR-152 first actual authorization-use consumption and immutable attempt/cutpoint history with the existing intent; proven definitive no-create consumption remains its existing terminal path, not a fabricated native intent. External calls stay outside the database transaction. | Lifecycle B9 | Crash pre-call, exchange accepted+lost ack, retry uncertain request, no new create ID or exposure from uncommitted intent. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.acceptance | Accepted native execution/entry-time integrity+logical event/projection | FN.SUBMIT/FN.RECON/FN.COOLDOWN/FN.PORT | Lifecycle source/effect/event in own UoW; Portfolio separately applies accepted event to capital/cooldown once. Known acceptance conflicts persist before tombstone suppression. Retain NR-152 accepted/rejected/fill/race evidence with Lifecycle's fact/event; Portfolio separately captures NR-151 bucket/cooldown/hold-exit/proven terminal observations with its own projection. | Lifecycle B9; Portfolio B8C/B9 | Late/reordered fill/reject, immutable accepted time, per-field same-version conflicts and pre-close capital residue; no cross-owner pseudo-transaction. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.placement | Actual accepted entry/terminal return publication | FN.SYNC/FN.SUBMIT/FN.MSG | Append existing ORDER_PLACED/entry-lifecycle return with exact native/client lineage and terminal revision; Set separately commits activation/stop. Retain NR-152 first exact terminal-return publication timestamp/outbox identity in existing LifecycleSetSync history, distinct from terminal effective time and Set receipt. | Lifecycle B9; Set B6 consumer | Placement before/after terminal, lost ack+query proof, duplicate publication; exactly one existing sync pathway. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.protection | Current protection evidence dependency transition | FN.CLOSE/FN.RECON/FN.NATIVE | Accept current field-aware query proof and atomically invalidate dependent live verification on complete omission/contradiction, preserving historical children. Retain NR-152 verification failure and actual child cancellation confirmation observations with their own authoritative proof transition; start markers follow the already-existing durable child-operation intent boundary. | Lifecycle B9 | New empty complete set, same-generation changed membership, partial/older query, crash on invalidation; no blind replacement. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.cancel | Reconciled entry remainder proof+cancel intent/receipt | FN.SUBMIT/FN.RECON/FN.SYNC | Conditional F-013 receipt joins original-entry cancel intent only after positive current unfilled remainder proof; persist intent before cancel call and reconcile terminal/fill evidence afterward. Retain NR-152 all actual causes, manual/Set request links and cancellation/racing-fill/terminal observation history; multiple causes still join one native intent. | Lifecycle B9 | Both causes one intent; partial fill race, terminal before receipt, unavailable native facts; filled quantity never targeted. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.close | Acquire-or-join close authority+current reduction budget | FN.CLOSE/FN.RECON | Atomic current revision/CAS, reconcile competing children/remainder, retain all causes and bound actual residual; one child authority/ID with uncertain outstanding budget counted. Retain NR-152 actual race detection and source-linked post-intent entry-fill member evidence with the existing close/proof transition; no diagnostic quantity grants another child. | Lifecycle B9 | Concurrent close causes, residual changed by racing fill, ambiguous child ack; no double reduction or negative clamp. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.closeretention | Logical close evidence and Portfolio retained-capital projection | FN.CLOSE/FN.PORT/FN.MSG | Lifecycle publishes governed close fact; Portfolio separately transfers current full committed amount to closing_retained and retains slot once. No release due to cancellation/partial exit during close. Portfolio's separate projection includes NR-151 original retained-capital/slot timing and exact before/after history; no premature release. | Lifecycle B9; Portfolio B8C/B9 | Frozen then-committed basis, repeated close events, partial exits and cancelled remainder; only later canonical receipt releases. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.partition | Native source partition+quantity application+global receipt | FN.RECON/FN.MSG; proof/receipt extension | Stage until complete proven disjoint source slices/manifest; then atomically apply named quantity, per-source consumed amount and global receipt. Portfolio separate manifest/projection verifies members once, not source slices reconstruction. NR-152 source-linked quantity observations and NR-151 Portfolio projection observations accompany their separate already-required owner effects; do not create another source-quantity posting. | Lifecycle B9; Portfolio projection B9 | Allocation-first/manifest-first, overlap/gap/source alias, member outside manifest, crash each write; source conservation and persistent incident independent of valid reconciliation. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.cashflow | Non-funding source allocation+component receipt | Canonical Lifecycle financial records over FN.UOW | Validate complete current execution attribution/accepted source set; use exact source quantum algorithm; commit full conserved allocation proof/component receipts before component finality. NR-152 entry/exit fee diagnostics reference the same conserved source/member/receipt evidence; no separate financial posting. | Lifecycle B10 | Non-q18 quantum, duplicate aliases, changed attribution/source member set, multi-execution unproven decomposition; no partial financial effect. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.funding | A-004 funding source+all allocations+once-only receipts | Canonical Lifecycle source/coverage records over FN.UOW | Freeze effective-time eligible set/weights, signed source, q18 raw/base/residue/recipient and exact conserved allocations under unique source identity, unchanged algorithm version. NR-152 funding/basis visibility reuses this exact retained A-004 record; no second source or allocation. | Lifecycle B10 | Signed conservation, lexical raw-allocation tie, source not representable, zero/empty coverage, crash with multi-recipient allocation. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.final | Lifecycle FINAL+close resolution+CLOSED+terminal outbox | FN.CLOSE/FN.RECON/FN.MSG plus missing canonical final ledger | Re-read current revision vector and all six predicates under serialization; freeze factual result/basis/economic time, resolve close intent, commit CLOSED/terminalized_at and final ORDER_EVENT together. NR-152 full-tranche monetary/close diagnostics reference this immutable terminal result and original factual proof; no provisional replacement or Portfolio receipt. | Lifecycle B10 | Each predicate false, source arrives during commit, post-final repeat and fault after each write; no Portfolio receipt created here. Applicable AT-NR-151/152 owner-observation cases; no duplicate economic or diagnostic application. |
| TX.incident | Post-final raw challenge/quarantine+incident+publication | FN.UOW/FN.MSG plus owner incident/parent links | Persist immutable accepted FINAL unchanged and separate parent-linked incident ID/revision/raw evidence, with scoped transport append/head update; no money adjustment. | Lifecycle B10; native/financial intake B9/B10 | Same incident revision content conflict, later valid evidence cannot auto-clear incident, multiple affected parent links, no result dedupe suppression. |
| TX.receipt | Portfolio first receipt+economic day+A-009+release | FN.PORT/FN.MSG plus canonical receipt/day records | Within scoped frontier serialization verify immutable FINAL/result+tranche uniqueness and current incident block; create first delivered_at receipt, post correct day, latch as governed and release capital/slot once. NR-151 retains original actual release, historical-day/recovery and linked terminal grant-resolution observations with this same Portfolio receipt; no extra wallet credit or release. | Portfolio B10 | Historical late first result, duplicate/conflict, incident ordering, missing day history and all write cutpoints; no wallet addition or second release. Applicable AT-NR-151 history/duplicate/crash cases. |
| TX.frontier | Lifecycle append vs Portfolio receipt/current eligibility | FN.MSG/FN.UOW; new scoped internal head/applied-prefix state | Concrete same-PostgreSQL design: serialize relevant append/head and Portfolio prefix merge+gate/effect on the same scope row/lock in fixed order. Head is read inside transaction; merge complete committed prefix, block gaps. No new wire family or direct business-state read. When a NR-151 underlying decision/receipt requires this fence, its observation records retain the same applied-prefix basis within that existing owner transaction. Diagnostics neither append a new business edge nor bypass the prefix. | B2 primitive; Lifecycle B9/B10 publication; Portfolio B8C/B10 decisions | Incident-before/after receipt, concurrent hold/append, omitted delivery, cache-head negative control, same-revision conflicts, stale messages, crash/retry and independent scopes. Applicable AT-NR-151 history/duplicate/crash cases. |

### 7.1 Durable known-evidence preflight

The intake sequence is explicit: resolve an already accepted identity/owner using a raw, exact recognizable anchor; compare its complete accepted canonical binding, including omitted versus present-null fields; durably retain any challenge/quarantine and required owner publication; only then perform ordinary required-field parsing, normalization, stale/covered/terminal/routing suppression and business-batch validation.

For mixed deliveries, scan every recognizable accepted member before an unrelated malformed companion can abort ordinary processing. Contradiction capture has a committed owner-local checkpoint independent of later ordinary-batch rollback. Ordinary valid updates remain atomic under their existing transaction. A modeled crash **before any commit** commits neither incident nor ordinary updates and requires redelivery; a normal parse failure **after** the preflight commit cannot erase that incident. Same raw challenge/accepted binding is deduplicated under the retained incident identity.

This applies to historical market selection/request/page/snapshot ownership; native observations/manifests/attribution/clearance; financial source/aliases/source-set/coverage/allocation proofs; entry-acceptance histories/resolutions; native-scope/close/day authority proofs; and current-protection query/proof envelopes. Factual execution/quantity contradictions remain execution facts; a lineage/clearance-only contradiction does not fabricate quantity. Unknown unrelated malformed input is rejected normally. Ambiguous owner recognition quarantines rather than guessing.

Y02 financial coverage recognition uses only existing envelope identity fields. Its overall key is `(request_id, response_id, GET_FINANCIAL_FACTS, OVERALL)`; its component key adds `COMPONENT, component`. The internal accepted revision is scoped to request/kind/component. Persist full nested coverage/applicability fields, exact accepted source-member set, raw provenance and basis digest; retain all accepted history and permitted exact lookup indexes. A missing echo can be recovered only by an actually present uniquely bound allowed anchor; not symbol, nearest time, endpoint similarity or current response. No new wire coverage identifier is added.

### 7.2 Concrete existing-edge committed-prefix fence

The selected implementation mechanism is a scoped transport head/applied-prefix extension in the existing canonical PostgreSQL transport. The key is the governed account/environment/native eligibility domain for the affected decisions; it is not a new business identifier or wire field. The future implementation must resolve that scope from accepted governance/native identities, never a guessed symbol-only join.

Lifecycle’s relevant publication transaction locks the scope’s transport head in a fixed documented order, appends the existing ORDER_EVENT message and advances the committed head atomically with its owner outcome/incident. Portfolio’s current eligibility/hold or first-receipt transaction acquires the same serialization fence, observes the head **inside that transaction**, merges all relevant committed existing-edge messages through that head into its own histories/projections, verifies no prefix gaps or unresolved blocking incident, and commits its own effect plus applied prefix. It reads transport records, not another owner’s mutable quarantine tables. Concurrent append and decision therefore have one actual serializable order. Retry retains immutable message/incident/result identities.

An incident committed before the receipt/hold linearization is part of the required prefix even when ordinary delivery has not reached the consumer; Portfolio withholds first receipt/release/current exposure authority. A receipt committed before the incident remains once-only and is never reversed, re-added or released again; the new incident blocks future eligibility. Missing gap/head/fence proof fails closed. A cached earlier head, broker ordering, poll interval, inbox dedupe, SKIP LOCKED claim or eventual projection alone is insufficient.

Tests must interleave both commit orders, undelivered committed incidents, same-revision conflicting content, stale history, concurrent receipt/hold, crashes/retries and unrelated scopes. A future alternative transport implementation must prove exactly the same ordering under independent persistence/architecture review; it may not weaken the behavior or add an owner/edge.

### 7.3 Quantity, current proof and close authority

Lifecycle owns factual attribution and validates half-open exact source slices `[start_quantity,end_quantity)` within each source total. Complete membership must be positive, disjoint, gap-free and conserving both each source and the observed reduction. Pre-manifest allocations are staged with **zero** quantity effect. A valid member applies quantity, per-source consumption and global receipt atomically. Outside-manifest aliases or reused-source claims are quarantined; independently valid reconciliation can still complete, but the incident block remains. A complete manifest itself is not a second quantity application.

Portfolio does not reconstruct slices, execution prices or attribution. It stages strict messages, verifies the complete Lifecycle manifest’s identity/member bindings/conserved observed total and applies each named logical projection once. Its projection is separate from Lifecycle’s source quantity effect. Resolution/manifest-first and allocation-first delivery converge without fabricated observation history or clearing an unrelated incident.

Historical native child mappings are separate from current live-protection proof. Before terminal FINAL/CLOSED commitment, a newer COMPLETE same-scope query omitting an expected child invalidates current verification immediately, preserves historical mapping and enters reconciliation. After terminal FINAL/CLOSED commitment, relevant contradictory evidence follows the separate post-final incident path; it does not revert immutable CLOSED to ordinary mutable RECONCILING. Absence proves neither fill, cancel, terminality nor replacement authority. Older/partial queries cannot restore current complete protection; equal-time enrichment is field-specific and only authoritative where the pinned profile proves it.

The existing single close intent is acquired or joined under current revision/CAS with all causes retained. Current residual uses unique factual entry/exit quantities and outstanding uncertain reduction authority, not cached flatness. Reconcile entry remainder and competing children before allocating the next child budget. Negative residual is an integrity condition, never a clamp. Stable intent/child IDs survive lost acknowledgement and restart. No second close authority or strategic partial-close logic is added.

### 7.4 Finality and receipt are separate owner-local transactions

Lifecycle’s terminal transaction rechecks the complete current evidence revision vector and source certificates. At its committed state it establishes all six S-004 predicates: logical exposure zero; original entry remainder terminal; every owned protective/exit child terminal or authoritatively disabled; close intent resolved; complete financial finality; no competing execution authority. It coherently freezes A-002 FINAL, its proof and economic-time basis, resolves the existing close intent, writes CLOSED/terminalized_at and appends final ORDER_EVENT. Intermediate A-004/component-FINAL work alone is not a full-tranche terminal result.

Portfolio then performs its own fenced receipt transaction: validate unchanged FINAL by **both result_id and tranche_id**; apply the committed-prefix incident gate; record its own first delivered_at; post the result on its bound historical economic day; apply A-009; release the appropriate capital/slot exactly once. Lifecycle publishes a result; **Portfolio creates the receipt**. No transaction claims to atomically mutate both owners’ business records.

`accounting_effective_at` follows the permanent final factual closing execution, not an earlier temporary zero, operational closed_at, finalized_at, terminalized_at or delivery time. ACCOUNTING_DAY_V1 uses persisted Asia/Jerusalem half-open local-midnight boundaries. A late first historical result posts to that historical day without changing the current base/latch or crediting the factual wallet again. New contradictory post-final facts are retained under separate parent-linked incidents, never a replacement FINAL or automated inverse adjustment.

Proven zero-fill cancellation and definitive no-create terminal release remain their separate governed paths, not fabricated filled-tranche FINAL/CLOSED. Missing no-create/zero-execution proof retains resources during reconciliation. Confirmed execution dominates contradictory rejection; a later attributable execution after prior proven zero-fill is factual liability/occupied slot and integrity reconciliation, not permission to reopen consumed CREATE or issue a compensating trade.

### 7.5 Authoritative lineage graph

Opaque identity encoding is an implementation detail unless constrained by the native API. Semantic creation ownership, immutable binding, reuse and conflict behavior are not optional. Names below that describe an internal technical record do not create new wire fields or contract families.

```text
Portfolio scope_revision -> Set formation_epoch / pinned selection/request evidence
  -> committed MATCHED: decision_cycle_id + set_result_id + frozen condition_record_id
  -> Position position_decision_id + immutable configuration/geometry
  -> Portfolio capital_grant_id
  -> Position construction_result_id -> successful position_plan_id / tranche_id / order_spec_id
  -> Portfolio authorization_id + exact H/slot + pinned attempt config
  -> Lifecycle durable intent / original client_order_link_id -> exchange_order_id
  -> factual execution/source identities -> close_intent_id / current proof
  -> exact source allocations -> immutable result_id / CLOSED
  -> Portfolio own receipt / first delivered_at / economic-day post / once-only release

Original frozen record + original accepted placement -> Set condition/evidence OR sticky unavailable requirement
  -> immutable signal_id -> Lifecycle exact-remainder reconcile/cancel -> terminal return to Set

Lifecycle incident_id/revision -> same-edge committed prefix -> Portfolio separate block/receipt eligibility
```

The same-symbol, same-price or same-time appearance of two records never makes them the same opportunity, native source, result or incident. Every known-content check precedes stale/covered/terminal suppression where the source requires it.

| Identity / lineage node | Single creation authority | Creation checkpoint | Immutable binding | Reuse / restart rule | Conflict rule |
| --- | --- | --- | --- | --- | --- |
| scope_revision | Portfolio | B8A | Exact symbol/configured OPEN/CLOSE content within governed scope | Republish original revision/content; newer effective scope advances unfinished formation only | Known revision changed content conflicts before stale check |
| formation_epoch | Set | B5B | Existing SetFormationEpoch: symbol + effective OPEN scope_revision + config/version/digest | Restore unfinished evaluation history; never import old epoch events | Same epoch different binding or attempt to revive closed epoch reconciles |
| selection_id | Set | B5B (B3 contract) | Immutable complete historical selection and scope/config/source parameters | Pagination requests retain same selection; one accepted snapshot/manifests | Incoming echo cannot rebind accepted page owner |
| request_id | Requesting owner: Portfolio, Set or Lifecycle | B8A/B8B; B5B; B9/B10 | Exact existing API family/operation/scope/selection/interval/intent | Retry same logical request as governed; paginate under retained selection and explicit request identities | Known ID different request content quarantines; never symbol/time lookup |
| response_id / snapshot_id / page_id | API factual producer, owner accepts | B3; B5B/B8A/B9/B10 acceptance | Exact parent request/source/profile/raw fact and fixed snapshot/page content | Restore complete accepted records/indexes; no fabricated page revision | Known content/omission/echo conflict retained before rejection |
| Trigger evaluation / transition-event identity | Set | B5B | Configured trigger/version, epoch, exact FALSE/TRUE/source evaluations and authoritative effective time | Original continuity, deadline and consumption survive restart | Unavailability interrupts; duplicate source cannot create fresh event |
| trigger_occurrence_id / core_set_constituent_id / role_id / binding_id / level_id | Configuration owns slots/roles; Set persists concrete matched bindings | B5B | P4 exact matched trigger/core-set occurrence to concrete reference; configured role namespace retained | Concrete MATCHED occurrence replay reuses IDs | No downstream recreation/ranking or equal-price identity collapse |
| decision_cycle_id | Set at final MATCHED | B5B | Exact symbol, matched set/config/version/digest and frozen contexts | Same committed MATCHED returns original cycle | No pre-match/Portfolio cycle minting or new cycle for replay |
| set_result_id | Set with immutable MATCHED result | B5B | Exact decision_cycle_id, result evidence and handoff | One immutable result for cycle | Different result/handoff under ID is conflict, not newer replacement |
| condition_record_id / frozen_condition_record_id | Set at matched frozen-record transaction | B5B | Same single record ID; cycle/result/config/family/direction/snapshot/typed predicates | Restore original record bytes/digest | No new record from current settings, no divergent duplicate reference |
| condition_id | Set configuration producer; copied at MATCHED | Before/at B5B | Typed predicate definition/threshold/reference/horizon/freshness/selector inside frozen record | Copy configured ID unchanged; same record/condition on evaluation | Never mint replacement predicate or reinterpret threshold |
| position_decision_id / initial event_id | Position | B7A | One exact handoff/cycle with initial config and opportunity outcome | Decision semantic identity and delivery identity both retained | Same cycle altered decision/pin conflicts; no completed construction fields |
| capital_grant_id | Portfolio after initial APPROVE | B8B | Initial decision/cycle/result, non-reserving amount, allowed pinned factual/config basis | Duplicate initial APPROVE yields original grant | No new grant due to age/revision/retry; bound facts immutable |
| construction_result_id | Position post-grant | B7B | Exact grant, initial retained geometry/config and success/failure outcome | One persisted outcome; failed result stays failed without success fields | Different outcome under same grant identity conflicts |
| position_plan_id / tranche_id / order_spec_id | Position successful construction only | B7B | Grant/decision/construction plus immutable final approved spec/actual economics | Result/spec/two outboxes commit and replay together | No initial or failed construction fabrication; no reuse across trades |
| order_spec_digest | Position via existing canonical serializer | B7B | Full exact immutable spec envelope/version; no self-reference | Consumer validates same digest AND duplicated scalar equality | Digest alone never excuses scalar/lineage mismatch |
| authorization_id | Portfolio with current H/slot hold | B8C | Grant/cycle/decision/construction/plan/tranche/spec/digest/H + attempt pin | One hold and consumed grant; reuse original authorization through delayed spec | Different H/spec/config binding conflicts; no no-create resurrection |
| client_order_link_id (client_order_id / client order ID semantic label) / durable intent identity | Lifecycle before external side effect | B9 | Exact authorized tranche/spec/native operation and stable native-client encoding | Ambiguous create reconciles original ID, never fresh create | Conflicting native mapping/attempt quarantines |
| exchange_order_id (native_order_id / native order ID semantic label) | Venue assigns; API transports; Lifecycle accepts | B9 | Exact proven original client/native pair and account/environment/product/scope | Replay preserves native alias/mapping | No synthetic/nearest-time/symbol association |
| execution_id / native source execution identity | Venue factual identity; API normalization; Lifecycle accepts | B9 | Native account/scope/order/source/effective chronology, quantity and actual price | Each accepted factual execution contributes once | Same ID changed core/provenance quantity or linkage conflicts |
| entry_acceptance_integrity revision / resolution_id | Lifecycle authoritative resolution | B9; Portfolio B8C/B9 consumer | Original accepted time/provenance/covered evidence, all accepted CLEAR/CONFLICT/RESOLVED content | Restore complete history and terminal resolution; retain original cooldown origin | Known older revision changed selection/content blocks without origin rewrite |
| native_observation_id / native_scope_revision | Lifecycle accepted factual native-scope observation | B9 | Original scope, authoritative quantity if known, source content/provenance; independent of lifecycle revision | Resolved or provisional observation history retained | Same ID lower changed revision is conflict; no global watermark shortcut |
| attribution_resolution_id / allocation_id / allocation application receipt | Lifecycle factual attribution owner | B9 | Global account/environment allocation→observation/resolution/source/revision/tranche/exact slices/quantity | Complete proof first; named effect/source consumed amount/receipt once | New alias cannot move reused source; changed ID binding/overlap quarantines with zero extra effect |
| close_intent_id / child sequence / cause identity | Lifecycle acquire_or_join | B9 | One active intent per tranche, durable revision, all causes, exact child budget/operation | Retry/concurrent causes join same intent and stable child | No second intent/child for ambiguous authority; closed/resolved forbids new authority |
| cashflow_id / proven source aliases | Factual source/API proof; Lifecycle canonical acceptance | B10 (B3 normalization) | Complete immutable U02 core and proven equivalence representations within exact source scope | One economic source, supplemental aliases without second effect | Changed core/unproven alias/ownership mismatch preserves raw contradiction |
| Non-funding financial allocation identity/receipt | Lifecycle | B10 | Unique source/component, accepted execution attribution, source_amount_quantum, algorithm/members/amounts | One complete conserved component posting under unchanged algorithm | No funding q18 substitution, changed members or amount rebinding |
| Funding allocation identity/receipt | Lifecycle | B10 | Unique signed source/effective-time eligible set/basis/q18 algorithm/recipient/allocations | One source full signed conservation, alias/retry inert | Changed eligibility/order/source quantum blocks rather than rounding/reallocating |
| Accepted coverage certificate key / accepted_certificate_revision | Lifecycle first accepted proof; internal only | B10; B3 preflight interface | Y02 existing-field tuple (request_id,response_id,GET_FINANCIAL_FACTS,OVERALL) or (...,COMPONENT,component), complete content/raw proof/source set | Immutable history/indexes and monotonic request/kind/component revision; no wire extension | Reused key/revision changed content/presence conflicts; exact unique fallback or quarantine |
| Factual-basis/source-set and allocation proof revision | Lifecycle | B9/B10 | Current exact accepted members/executions/coverage/allocation proof and parent-result links | Historical revision content retained, current dependent proof invalidated on change | Known changed same revision before stale suppression; no source exclusion to force finality |
| result_id / terminal result-tranche binding | Lifecycle canonical terminal transaction | B10 | One immutable factual FINAL for tranche, current basis proof, accounting_effective_at/day, terminalized_at | Identical terminal replay no-op; no replacement result stream | New contradictory source is separate parent-linked incident, not result edit |
| Portfolio receipt / first delivered_at | Portfolio | B10 | Unique result_id AND tranche_id, same FINAL content/day, receipt commit time and once-only application | Retry returns first accepted receipt/time; late result stays historical | Duplicate different content/tranche mapping conflicts; no second posting/release |
| incident_id / incident_revision | Lifecycle for governed published incident; receiving Portfolio projection | B9/B10 | Exact parent-result link where present, native eligibility scope, frozen incident class/raw evidence/status history | Independent from result dedupe; accepted history before stale filtering | Same revision different content blocks; only valid explicit resolution clears, never automatic money inversion |
| evidence_digest | Set | B6 condition evaluation; source frozen by B5B | Actual retained selected evidence plus record/condition/cycle/result/original linked entry | TRUE invalidation retains original authoritative effective time and same digest | Unavailable branch never fabricates TRUE evidence/digest |
| unavailable_requirement_id = signal_id (unavailable cause) | Set acquire-or-join | B6 | (F013_MONITORING_UNAVAILABLE,decision_cycle_id,set_result_id,tranche_id,original entry client_order_link_id) in existing account/environment | First transition/time/reason/optional record presence immutable; same key returns same ID | Different content/second ID same key conflicts; no quantity/revision/recovery-based remint |
| signal_id (INVALIDATION cause) | Set first logical TRUE signal | B6 | Frozen record/condition/evidence and exact original accepted entry remainder lineage | Replayed same logical TRUE event returns original signal/time | No cause mutation, TTL/new opportunity invalidation or guessed target |
| Deferred F-013 source/event transition binding | Set existing exact event/incident namespace | B6 | Original identifiable source/event, first effective transition/order until target is independently resolved | Later exact linkage preserves time; no targetless wire envelope | Multiple/unresolved candidate matches quarantine; terminal proof prevents resurrection |
| Committed-prefix technical scope/head/applied sequence | Existing-edge technical transport; not a wire ID or owner | B2 primitive; B8C/B10 integration | Governed account/environment/native eligibility domain and ordered committed existing-edge publication | Head/append and prefix application are serialized; replay restores committed history | Gaps/unavailable fence block; cached or out-of-scope head cannot license eligibility |

### 7.6 Observation capture uses existing transactions — NR-151 / NR-152

This subsection specifies membership in the existing **26** mechanisms, not another transaction topology. P-/L-record labels are the documentary aliases in §§6.2–6.3. Missing observation fields/events are added at the same owner checkpoint and to the same existing connection/UoW as their authoritative basis. Read-only aggregates/caches are not another canonical posting.

| Existing owner event | Same existing transaction(s) and required observation membership | Atomicity / replay constraint |
| --- | --- | --- |
| Portfolio scope, configuration/capacity gate and COINS transition | B8A TX.scope: P-DECISION full status/gates/reasons and P-STATE/configuration/cap basis with scope revision/outbox. No effective status change can still have an actually evaluated diagnostic outcome. | Do not invent another scope transition, grant or capital-state revision merely to count an evaluation. |
| Portfolio accounting-day/base/latch and recovery | B8A TX.day; B10 TX.receipt/day integration: exact day/base/latch/recovery observations with the existing authoritative day transition. TX.scope only its consequential scope effect. | One fixed base, original historical receipt and latch branch order are unchanged; a diagnostic record never establishes a missing base. |
| Portfolio grant issue, unavailable or blocked grant evaluation | B8B TX.grant: P-DECISION and computed candidate amount/reasons, successful P-GRANT/outbox if permitted; denied outcomes have no grant/hold/slot/auth. | Return/publish success only after the complete commit. A committed denial retains its original evidence; same evaluation retry cannot double-count. |
| Portfolio construction intake/current H booking | B8C TX.hold under existing frontier where required: P-DECISION, accepted original construction confirmation, exact H/slot/auth and grant-consumption history on success, or complete denial history with no success effect. | A failed **business outcome** may be committed with diagnostic evidence while containing zero successful holds/slots/auth/outbox. A failed **database transaction** commits none of its staged outcome/history. Never repair the spec. |
| Portfolio reception of native acceptance/remainder/close evidence | B9 Portfolio-local TX.acceptance/TX.closeretention (and actual TX.partition projection where applicable): P-TRANSITION/P-RECON/cooldown/proven-terminal history alongside the accepted event's local effect. | Lifecycle first commits its own factual event/outbox. Portfolio separately consumes it on the existing ORDER_EVENT edge; no distributed transaction or direct Lifecycle mutable-state read. |
| Portfolio first FINAL receipt and actual release | B10 TX.receipt with existing TX.frontier/day serialization: P-TRANSITION and linked proven terminal grant-resolution evidence with the same receipt/day/A-009/release. | Exactly once by result and tranche; original recorded/delivered time retained. No observation authorizes release, adds wallet P&L or rewrites a historical base. |
| Lifecycle input capture and first authorization receipt | B9 existing TX.owner intake, using ST.transport/native/reconciliation history; B10 reuses the same mechanism for its domain. Retain capture key/raw reference/first observation time; first authorization receipt keeps existing inbox key/time. | This is durable ingress metadata, not accepted native/financial authority. Resume pending captured inputs on restart. No new worker or transport; no new wire identity. |
| Known evidence challenge and ordinary classification | Unchanged TX.preflight commits recognized contradiction as already specified. Ordinary accepted facts/outcomes and their L-ARRIVAL classification use the existing accepting TX.facts/TX.acceptance/TX.owner boundary. | Capturing a diagnostic arrival never suppresses or rolls back the independently committed challenge. A benign duplicate needs an observation receipt but zero new economic effect. Same captured key/kind/content returns the original classification. |
| Lifecycle native-use intent and observed outcome | B9 TX.native: original L-SUB attempt/cutpoint and first actual L-AUTH native-use consumption; TX.acceptance for accepted/rejected facts and the existing definitive no-create terminal-consumption branch. | Durable intent precedes external side effect. No-create consumes terminally without a fabricated native request. A crash between external call and observation is uncertain, not proof of acceptance/failure. Retain original native identity. |
| Lifecycle placement/terminal return | B9 TX.placement: existing L-SYNC record and Set-addressed outbox plus its first producer publication evidence. | Producer publication time differs from venue effective time and Set receipt; publication does not claim delivery or terminality of another child. |
| Lifecycle protection and sibling cleanup | B9 TX.protection records actual verification/confirmation; existing TX.close/TX.native durable child-operation transaction captures its start and intent, using the same owner/UoW where combined. | An uncommitted start cannot authorize a call. Confirmation requires separate authoritative proof; diagnostics do not replace current-protection predicates. |
| Lifecycle entry cancel and close/racing fill | B9 TX.cancel/TX.close/TX.acceptance and TX.partition where attribution is actually required: L-CANCEL/L-CLOSE cause, race and exact execution-member observations with original effect/proof. | Original single intent/child/source receipts remain authoritative. Additional-fill diagnostic is a projection, not another quantity effect or another close cause. |
| Lifecycle reconciliation, restart correction or manual intervention | Existing TX.owner or the actual TX.facts/TX.cancel/TX.close/TX.partition transition: L-RECON/L-MANUAL original episode/check/cause/before-after evidence. | Unchanged hydration creates no correction; repeated capture/check reuses observation identity. A manual diagnostic alone cannot create execution, allocate a tranche or clear an incident. |
| Lifecycle financial source/allocation/finality | B10 TX.facts/TX.cashflow/TX.funding/TX.final retain L-FIN source/component/receipt/funding basis/final observations in the already authoritative records. Existing TX.incident handles real post-final contradictions. | No extra financial posting or diagnostic FINAL; raw capture does not bypass coverage/currency/current-revision gates; immutable FINAL never changes. |

**Definitive denial versus transient failure.** Current-capacity conflicts discovered under the B8C lock/serialization can commit the correct denied P-DECISION and its complete evidence in TX.hold with zero success effect. A transient SQL serialization/deadlock rollback cannot retain a counter from inside the aborted transaction and is not automatically a business BLOCKED outcome. Keep the original durable intake/attempt identity. If a technical failure observation has actually been captured, persist it once through the already-existing TX.owner failure/recovery outcome before acknowledging that captured attempt, with no grant/hold/auth effect. A retried transaction uses the same captured failure identity for that failure; its later actual decision has its own retained evaluated basis. A crash before failure capture/commit provides no proof of an exact unrecorded failure reason; retain uncertainty/recovery and do not fabricate one. All committed diagnostic observations, denials and incomplete captured work remain recoverable. This does not add a new business outcome, 27th mechanism or trading retry policy.

For each producing checkpoint, test a crash before every state/history/observation/outbox/inbox commit step and redelivery after commit. Where an observation is derivable, test retention of its complete basis rather than introducing another duplicate value ledger. Same-ID altered status/reasons/source/core/arrival metadata is a conflict, never a correction in place. Existing preflight, terminal dominance, grant non-reservation, immutable FINAL and committed-prefix rules continue to govern independently of diagnostic visibility.

### 7.7 NR-153 / NR-154 — source retention and diagnostic persistence membership

The existing 26 canonical transaction mechanisms and their owners/atomicity are unchanged. Reporting adds retained fields/child evidence to the original source transition, never a second business effect or a 27th transaction family:

| Source or diagnostic operation | Existing boundary | Required membership / failure rule |
| --- | --- | --- |
| B7A Entry/TP work and initial outcome | TX.opportunity | Complete RPT-POS/RPT-ENTRY/RPT-TP work, exact candidate/visit/reason/age/configuration binding commit with the original pin/decision/outbox, including rejected outcomes. Crash before commit produces no source member; after commit duplicate reuses original work. No grant/success spec is invented. |
| B9 actual dispatch/current hard checks | TX.native and actual TX.facts/accepted outcome as already applicable | RPT-LIFE original observed dispatch or uncertainty, definitive hard-compatibility proof and exact joined lineage remain with the existing intent/fact history. No report instruction makes an external call atomic with the database. |
| B9 acceptance/fills/POST_ONLY refusal/terminal remainder/close | TX.acceptance/TX.facts/TX.cancel/TX.close and TX.partition only when the original fact requires attribution | Retain source IDs, quantities/prices/times/chronology/coverage and actual reasons in the existing owner histories. Report-derived counts/touches add no native, quantity or cancel authority. Existing TX.preflight still handles recognized changed evidence before ordinary acceptance. |
| B10 final factual outcome/horizon | TX.final | Existing immutable full-tranche FINAL, result/tranche binding, actual net/currency and permanent closing-execution chronology provide the reporting outcome. No geometry recomputation, Research write or Portfolio receipt is joined into this transaction. |
| B3 diagnostic market-path ingestion and exact immutable owner-history import | NONE in the canonical TX taxonomy | Reuse retained ST.facts after its original owner commit, or the existing isolated Research/public historical input boundary. Raw immutable objects publish before their SQLite dataset manifest (§6.4.3); archive/import cannot issue business messages or grant accepted native authority. Same ResearchStore local transaction retains source/member manifest and import progress once. |
| B12 report assembly/publication | NONE in the canonical TX taxonomy | Read-only canonical evidence consumption; same ResearchStore SQLite transaction publishes report pins, semantic identity, complete member/output references and status atomically. A diagnostic rollback commits no report and cannot roll back business history. No PostgreSQL/SQLite/filesystem distributed atomicity claim. |

Existing ST.transport/ST.nativefacts/ST.position/ST.final identities remain business/source authority. Report/dataset identities are internal documentary keys only. Original source retention enables idempotent import after a report failure; loss or conflict is explicitly unavailable data, never a fabricated canonical correction. No Research failure is inserted into a live trading gate. The existing separate PostgreSQL promotion-request/outbox transaction is not changed or invoked by report generation.


## 8. Exact numeric policy and end-to-end dataflow

### 8.1 Generic arithmetic boundary: B1

B1 provides exact finite-decimal parsing and canonical output validation, scaled integers and exact rational intermediates, exact comparisons/cross-multiplication without unintended finite-context division, signed HALF_EVEN/floor/ceil/truncation, directional tick/step primitives and exact integer-midpoint square root. A sufficiently large but finite Decimal context is not a proof of exactness. A resource limit must return an explicit error, never silently select a different value. Generic helpers implement mathematical primitives, not F-001/F-002, Entry/SL/TP, grant sizing, F-011/F-012 or source-allocation equations.

The three value classes are explicit. **WORKING** is the exact or source-prescribed Q36 owner calculation state. **WIRE** is the exact field value selected by its own frozen export/monetary/tick policy. **REPORT_ONLY** is a display/diagnostic ratio that cannot determine a gate where the source excludes it. Do not reconstruct working inputs from a rounded export or display string. Native raw representations remain retained as provenance even when a separately canonicalized value is equivalent.

### 8.2 Numeric interface matrix

| Value/operation | Owner/checkpoint | Exact working rule | Export/persistence rule | Downstream prohibition / tests |
| --- | --- | --- | --- | --- |
| Canonical source decimals | API intake/B3; every owner | Exact finite value, original raw magnitude/sign and provenance retained | Canonical output text only at governed boundary; no binary floats/nonfinite/exponents | Missing is not zero; raw sign truth table and canonical equivalence tests |
| Set source/ordinary populations | Set B5A/B5B | All prescribed accepted members and completed UTC windows, not an arbitrary recent subset | Membership/source identities and Q36 working state retained | No rounded handoff or incomplete current day used as population |
| F-001 and F-002 | Set B5A | Frozen equation and named operation/quantization order using their own trigger inputs | Persist exact trigger evidence and source-prescribed working output | F-001 is not ATR-normalized momentum; F-002 population not substituted by F-004 Formation-only results; no F-004 operand or availability edge in either direction. |
| F-003 TR/Wilder ATR/ATR_PCT | Set B5A/B5B | Exact TR; authoritative seed14; named Q36 HALF_EVEN seed/recurrence/PCT; valid zero-close advances ATR only | Q36 checkpoint/ancestry; Q18 HALF_EVEN allowed ATR/PCT wire exports independently from work | No reseed/skip malformed candle; positive work rounded to unusable required zero wire does not get clamped |
| F-004 normalization/stddev/score | Set B5A/B5B | Exact population variance (ddof=0), exact integer midpoint sqrt on Q36 grid, frozen factor order; only candidate-side BTC, relative and local-momentum vetoes are active | normalize_working/normalize compatibility returns WORKING Q36; export serializer separate | Q18 never used inside score/veto; separate local5m and canonical15m state Own classifier populations/context only; no F-001/F-002 trigger work/result/sign or trigger-local availability prerequisite. |
| MARKET_HANDOFF numeric fields | Set B5B; Position B7A | Set finishes work decisions before export; factual references/tick remain exact as specified | Only existing schema-permitted fields, Q18 where required; canonical integer freshness policy | Position consumes received values exactly, no inferred hidden digits or additional ATR-percentile requirement |
| Entry/SL/TP | Position B7A | Frozen reference selection, exact operations, directional tick rules and post-round geometry/distance checks. F-010 uses only its own bound Entry/TP inputs (§5.1), independently of Stop availability; chosen Stop and TP join only in later joint feasibility/geometry | Retain raw selection/evidence and chosen immutable final prices for later grant | No fee/tick refresh or downstream repair/reselection |
| Portfolio grant | Portfolio B8B | Exact governed free capacity; floor_Qcapital(Cfree); divide positive remaining slots exactly then floor_Qcapital grant | Qcapital=1e-12 spendable floor; grant remains non-reserving | No upward allocation, final-recipient residue redistribution or stale grant as current capacity |
| F-011 C,T,Q,N,A,H | Position B7B | T=C×leverage; Q follows exact raw quantity and step floor; N=Q×Entry; mathematical A=N/leverage; H=ceil_Qcapital(A) | Retain exact intermediate evidence (rational where needed); spec/confirmation hold value is H; exact N | Require A<=C and H<=C; do not clamp/resize; H copied without another rounding step |
| F-012 fees/edge/R:R | Position B7A gross; B7B full | Exact geometry and signed factual fractional fee rates; entry cost uses N, exit fees respective exit price×Q; net-edge denominator N | Qratio=1e-18 floor only for prescribed reports; gates use exact unrounded values | Funding excluded from planned edge; baseline extra TP-cost set empty, asserted undefined applicable cost blocks |
| Portfolio H hold | Portfolio B8C | Compare supplied immutable H/scalars/digest and current exact own constraints | Copy exact H into hold/spec confirmation/auth; unused C−H stays free | No F-011/F-012 recomputation and no hold of C or unquantized mathematical A |
| Pre-close entry apportionment | Portfolio B9 projection | NUMERIC_POLICY §5 local approved-capital variable is the already quantum-aligned approved liability, i.e. F-011 H—not F-011 mathematical A; compute ratios exactly | Ceiling retained total, floor filled while remainder exists, reserved gets residue; terminal remainder leaves ceiling filled total | Never reuse pre-close formula for proportional release during closing_retained |
| A-004 funding | Lifecycle B10 | Exact signed source and effective-time eligible settlement-notional weights; q=1e-18 toward-zero bases | Full signed residue to greatest absolute unrounded allocation; tie Unicode code-point tranche_id ascending; exact conservation | Not largest fractional remainder, not current position weights, not source rounding or currency conversion |
| Non-funding source allocation | Lifecycle B10 | EXEC_CASHFLOW_ALLOC_V1 source_amount_quantum with proven execution quantity×actual-price weights | Own source quantum toward-zero bases, full signed residue per frozen rule and once-only receipt | Do not call the funding allocator as a generic substitute; validate quantum and source multiple |
| A-002 factual final result | Lifecycle B10 | Exact unique factual entry/exit cost sums and frozen component signs; signed fees/rebates/funding/other supported costs | One exact immutable result/current proof in governed currency, no arbitrary cents or ratio quantizer | No planned Entry/rates, double source alias, component FINAL mistaken for full tranche or implicit FX |
| A-009 Daily Loss | Portfolio B8A/B10 | Exact eligible historical R_day; exact loss bound base×pct/100; compare inclusively before reporting. The base operand is the single fixed accounting-day value established/recovered under NR-035, not current equity or unrealized P&L. | Persist day/base/config/latch and once-only result receipts; retain exact NR-035 boundary evidence/reconstruction basis; no Qcapital/Qratio gate rounding | Disabled preserves latch, missing recovery not empty day, historical late result not current-day sum |

### 8.3 Allocation algorithms remain separate

A-004’s frozen version is `FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL`. The signed source must be exactly representable at q18. Eligible tranches and attributable quantities are those at the funding effective event, with authoritative ordering or proof that a tie is immaterial to the funding weights; this does not waive independent permanent-closing chronology. Persist source/aliases, coverage, effective event, eligible set, settlement basis/provenance, exact weights, raw/base allocations, full signed residue, recipient and final allocations. A nonzero unmatched source, unsupported currency, unknown basis/eligibility or incomplete coverage stays RECONCILING/finality-blocked.

Non-funding `EXEC_CASHFLOW_ALLOC_V1` first requires proven execution attribution and exact applicable source decomposition. Its own factual `source_amount_quantum` is not assumed q18. Weights use absolute attributable execution quantity×factual price; bases truncate toward zero, with complete signed residue according to its frozen deterministic rule. The source must already be exactly representable at its quantum; do not round or omit it to force conservation. Complete current source sets and their once-only receipts are mandatory for component finality.

Both algorithms conserve the entire signed source exactly, but this common invariant does not make them one generic business allocator. B1 can share exact rational/truncation primitives only. Source applicability, effective-time membership, weights, quantum and algorithm identity belong to Lifecycle’s distinct B10 functions.

### 8.4 No hidden cross-owner recomputation

Set owns work calculations and final direction. Position consumes exact permitted handoff values and owns Entry/Stop/TP/construction/economics. Portfolio verifies immutable Position scalars/digest and its own current allocation/day/incident gates; it does not rerun Position formulas. Lifecycle consumes authorized immutable order values and current factual execution restrictions; it does not select a new trade. Its financial result uses actual accepted executions and cashflows, not reconstructed planned economics. Research/display values never feed any canonical gate.


**NR-151/NR-152 observation projections:** Retain exact source-selected monetary/quantity values and paired timestamp bases under this existing policy. Diagnostic ratios may retain exact numerator/denominator with explicit availability; no new Qcapital/Qratio/output rule is introduced for an unspecified display metric. Never feed a display, duration, count, utilization, unused-grant surplus or race quantity projection into a trading gate or source allocation. Position's already-retained T is displayed from its immutable work evidence, not recalculated by Portfolio. Money/source conservation and the two distinct allocation algorithms remain unchanged.

### 8.5 NR-153 / NR-154 report-only exact arithmetic

§6.4 retains original F-008/F-010 raw/rounded operands and canonical age without changing them. Report-only ratios, band comparisons, means, price-unit excursions and time deltas use exact finite-decimal/rational arithmetic and proven timestamp resolution. Persist exact numerator/denominator when a decimal would not terminate. No SQLite REAL, binary float, hidden finite-context rounding, new gate quantizer, implicit FX, latest ATR or rounding feedback is introduced. The same first-fill anchor and complete path member set determine direction-aware extrema. OHLC intervals do not create an exact intra-bar timestamp/order. Test-only research parameter alternatives remain exclusively in the isolated diagnostic invocation specified by §6.4.7; the canonical F-010 inputs, thresholds, reason precedence and numeric policy are unchanged.


## 9. Strict branch conformance and complete F-013 state

### 9.1 B0 public-parser acceptance matrix

Every case runs through the actual exported `parse_contract` boundary and existing builder/registry path. A direct schema-only validator test is supplementary, not a replacement. Frozen schema constructs currently used by any family must be enforced before B0 claims alignment.

| Case | Required public-parser result | Additional semantic boundary |
| --- | --- | --- |
| VALID INVALIDATION with all required original record/condition/evidence/time/entry fields | ACCEPT | B6/B9 still verify trustworthy evidence, exact lineage and remainder applicability |
| VALID MONITORING_UNAVAILABLE with required requirement/time/reason and signal_id equality | ACCEPT | B6 still proves original sticky key/time/reason; no TRUE evidence is inferred |
| INVALIDATION missing any required cause-specific field | REJECT | No generic root-required list may accidentally waive branch fields |
| MONITORING_UNAVAILABLE missing any required cause-specific field | REJECT | Regenerated schema plus a validator ignoring oneOf/not is insufficient |
| INVALIDATION carrying unavailable-only fields | REJECT | Branches are mutually exclusive, not an additive union |
| MONITORING_UNAVAILABLE carrying forbidden invalidation-only fields | REJECT | No fabricated condition/evidence/invalidated_at on unavailable branch |
| MONITORING_UNAVAILABLE with optional condition_record_id permitted by frozen schema | ACCEPT structurally | B6 permits presence only when actually trustworthy; absence/presence/content stays frozen |
| Unknown cause | REJECT | No fallback branch or legacy cause inference |
| instrument_metadata item with status PARTIAL | REJECT | Mixed valid binary rows may make aggregate PARTIAL |
| fee_rates item with status PARTIAL | REJECT | Same binary item rule, exact requested-symbol coverage |
| Unknown field/version or unsupported used schema construct | REJECT / B0 incomplete until enforcement exists | No silent validation skip; family versions remain frozen |

### 9.2 Monitor activation and exact reducer

B5B freezes the original condition record at MATCHED, but that alone does not activate pending-entry monitoring. B6 accepts authoritative ORDER_PLACED return from the existing LifecycleSetSyncStore path for the exact cycle/result/tranche and original accepted client/native entry. Terminal entry-lifecycle evidence has precedence, including when delivered before delayed placement. Scope CLOSE/new opportunity does not stop an already accepted entry monitor.

For a valid activation and resolvable frozen record, evaluate each required typed predicate as TRUE, FALSE, UNAVAILABLE or INVALID_CONDITION using its frozen definition, selector and numerical/freshness policy. The complete effective reducer is:

| Priority / condition | Reducer outcome | Owner action |
| --- | --- | --- |
| 1. Authoritative original entry remainder already terminal | STOPPED / NO_MARKET_SIGNAL | Retain terminal tombstone; no pending-entry market signal or reactivation |
| 2. Activation identity invalid or original frozen record invalid/unresolved | UNAVAILABLE / FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING | Retain exact source/event integrity condition; sticky unavailable requirement only for a trustworthy original target |
| 3. With valid activation/record, at least one required frozen predicate TRUE | INVALID / EMIT_ORDER_CANCEL_SIGNAL | Emit immutable INVALIDATION from actual selected TRUE evidence; TRUE takes precedence over another unavailable predicate |
| 4. No TRUE; a required predicate UNAVAILABLE or INVALID_CONDITION | UNAVAILABLE / FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING | Acquire/join immutable sticky unavailable requirement |
| 5. All required predicates are FALSE | VALID / NO_MESSAGE | No new signal; an already persisted unavailable requirement is not withdrawn or reclassified |

“TRUE” means the frozen invalidation predicate is true; it is not “the trade remains valid.” Missing evidence is not FALSE. A TRUE precedence rule does not override terminal remainder or invalid activation/frozen-record integrity. B6 evaluates numeric predicates rather than merely constructing an envelope.

### 9.3 Sticky unavailable identity, reason and deferred binding

The unique semantic key is `(F013_MONITORING_UNAVAILABLE, decision_cycle_id, set_result_id, tranche_id, original entry client_order_link_id)` inside the retained account/environment lineage. One acquire-or-join mapping assigns `unavailable_requirement_id`; `signal_id` is that same ID. Partial fill quantity, lifecycle revision, retries, new observations, additional failed conditions and market recovery are **not** a new semantic key.

On the first durable unavailable transition, persist original transition/source identity and order, effective unavailable_at, all known failure diagnostics, and the first primary reason in this order: `ACTIVATION_IDENTITY_INVALID` → `FROZEN_RECORD_INVALID_OR_UNRESOLVED` → `INVALID_CONDITION` → `REQUIRED_EVIDENCE_UNAVAILABLE`. This selection happens only after the reducer selects UNAVAILABLE; it does not change terminal or TRUE precedence. Freeze primary time/reason and optional condition_record_id presence/value. Repeated key returns original content; a second ID or changed content is a conflict.

When original target lineage is not trustworthy, retain the original exact source/event transition and integrity/reconciliation state, but send no guessed-target envelope. Later authoritative linkage to **that original accepted entry** permits acquire-or-join while preserving original effective transition time/order. Recovery arrival order, symbol matching or a newer opportunity never selects the target.

No recovery withdrawal, remint or reclassification is allowed. A later valid evaluation does not erase the prior conditional reconcile-first requirement. An independent later TRUE invalidation keeps its own original cause/evidence while both messages join the same Lifecycle original-entry cancel intent. No arbitrary TTL, full-Set rematch, newer opportunity, repricing/chasing or filled-exposure cancellation is introduced.

### 9.4 Lifecycle consequence and completion boundary

Lifecycle B9 persists the conditional receipt, reconciles authoritative current original-entry state, and only a proven positive active unfilled remainder can authorize native cancel. Unknown/conflicting native state retains reconciliation; terminal remainder makes the request no longer applicable and returns through the existing placement/entry-lifecycle mechanism. Filled exposure is protected/managed under its normal Lifecycle rules, never cancelled or closed by F-013. A signal delivery acknowledgement is not terminal proof or capital-release authority.

B6 local typed-return fixtures validate monitor behavior. B9 must additionally prove actual authoritative placement→Set activation, cancel/remainder reconciliation and terminal→Set stop through the existing infrastructure before F-013 integration is treated as complete.

## 10. Dependency checkpoints and mandatory independent review

### 10.1 Dependency graph

The display sequence below is a safe topological order, **not** the former blanket numeric B0→B14 dependency chain. B8A and B5A can be developed/reviewed independently after B0–B4, but B5B needs both. B6 and B7A have independent consumers after B5B. Any parallel work must avoid unreviewed shared-file/schema edits and cannot relax the true dependency gates. Checkpoint splits are review/transaction boundaries inside existing owners, not new owners/services.

| Checkpoint | Scope | Direct prerequisites | Reason for order |
| --- | --- | --- | --- |
| B0 | Frozen source alignment | Frozen attached package and accepted revised plan | Fixed predecessor capability and evidence required before downstream owner work. |
| B1 | Exact numeric and binding foundation | B0 | Fixed predecessor capability and evidence required before downstream owner work. |
| B2 | Shared durable foundation | B0, B1 | Fixed predecessor capability and evidence required before downstream owner work. |
| B3 | Factual adapters and accepted-evidence intake | B0, B1, B2 | Fixed predecessor capability and evidence required before downstream owner work. |
| B4 | Contract structure and semantic binding layer | B0, B1, B2, B3 | Fixed predecessor capability and evidence required before downstream owner work. |
| B8A | Portfolio scope, account state and economic-day foundation | B0, B1, B2, B3, B4 | Actual upstream scope before Set; no grant/initial decision fabricated. |
| B5A | Set numeric dependencies and indicator state | B0, B1, B2, B3, B4 | Independent numeric/population kernels; consumes typed factual data, not premature MATCHED state. |
| B5B | Set durable handler, MATCHED and handoff | B8A, B5A | Both real scope and kernels before final event/result transaction. |
| B6 | Frozen pending-entry monitor and two-cause signal production | B0, B1, B2, B3, B4, B5B | Original frozen record exists; real native placement producer arrives in B9. |
| B7A | Initial Position opportunity | B0, B1, B2, B3, B4, B5B | Initial approved opportunity must precede its exact Portfolio grant. |
| B8B | Portfolio non-reserving grant | B8A, B7A | Grant binds real initial approval, not a completed post-grant result. |
| B7B | Post-grant Position construction and economics | B7A, B8B | Exact immutable grant and retained geometry precede final sizing/economics. |
| B8C | Current Portfolio hold and authorization | B8A, B7B | Current constructed H, not grant/request age, can be booked. |
| B9 | Lifecycle native flow, protection and factual reconciliation | B8C, B6, B3 | Exact spec/current authorization and monitor intake exist before native owner integration. |
| B10 | Financial finality and separate Portfolio receipt integration | B9, B8A, B8C, B2 | Current native/quantity proof exists before financial finality and actual Portfolio receipt integration. |
| B11 | Integrated replay, restart and concurrency hardening | B5B, B6, B7A, B8B, B7B, B8C, B9, B10 | Hardens already-correct local owners. |
| B12 | Canonical dispatch, independently gated native authority and separate read-only Research report assembly | B0, B1, B2, B3, B4, B8A, B5A, B5B, B6, B7A, B8B, B7B, B8C, B9, B10, B11 | Only one dispatcher; all prior implementation gates and applicable native authority proofs required. NR-153/154 assembly is separate read-only technical diagnostics over completed sources, not formula logic in dispatch; no reverse dependency. |
| B13 | Full integrated verification and isolation | B12 | Full integrated dispatcher verification, not first local correctness tests. |
| B14 | Independent full backend conformance re-audit | B13 | Independent assessment of actual implemented source/evidence, not map banners. |

For multi-checkpoint interfaces, fixtures permit early local verification only. B8A can test A-009 state using immutable fixture results, but actual receipt/producer integration closes in B10. B7A must not evaluate completed post-grant economics. B9 may model closable/current-proof states without manufacturing financial FINAL before B10. B11 may invoke actual owner interfaces in tests while the production dispatcher remains gated; this is not a second production orchestration path.

### 10.2 Independent gates

Gates occur **after implementation and applicable tests, before that future checkpoint is committed/pushed**. This revision performs none of those repository actions. Each review records scope, exact source/test evidence, changed surfaces and unresolved findings. A BLOCKER or an unexecuted required database/native acceptance case is not a passed gate. Fixes discovered later reopen the affected owner checkpoint and its applicable reviews. Additional security/architecture review is required when the actual changed authority/import/transport surface warrants it; this table is the minimum.

| Gate group | Checkpoint | Mandatory independent reviews / acceptance |
| --- | --- | --- |
| G-B0 | B0 | IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B1 | B1 | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B2 | B2 | IMPLEMENTATION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; ARCHITECTURE_CONFORMANCE_REVIEW |
| G-B3 | B3 | IMPLEMENTATION_REVIEW; API_PROVENANCE_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW |
| G-B4 | B4 | IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B8A | B8A | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW; ACCOUNTING_FINALITY_REVIEW |
| G-B5A | B5A | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW |
| G-B5B | B5B | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW |
| G-B6 | B6 | IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; NUMERIC_PRECISION_REVIEW |
| G-B7A | B7A | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW |
| G-B8B | B8B | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B7B | B7B | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW |
| G-B8C | B8C | IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B9 | B9 | IMPLEMENTATION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; ADVERSARIAL_TRADING_REVIEW; API_PROVENANCE_REVIEW; CONTRACT_REVIEW; TEST_REVIEW; NUMERIC_PRECISION_REVIEW |
| G-B10 | B10 | IMPLEMENTATION_REVIEW; ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW |
| G-B11 | B11 | IMPLEMENTATION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; TEST_REVIEW |
| G-B12 | B12 | IMPLEMENTATION_REVIEW; ARCHITECTURE_CONFORMANCE_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; E2E; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW |
| G-B13 | B13 | ARCHITECTURE_CONFORMANCE_REVIEW; TEST_REVIEW; ADVERSARIAL_TRADING_REVIEW; ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW |
| G-B14 | B14 | FULL_BACKEND_CONFORMANCE_REAUDIT; ARCHITECTURE_CONFORMANCE_REVIEW; ACCOUNTING_FINALITY_REVIEW; ADVERSARIAL_TRADING_REVIEW |

### 10.3 Owner-local replay/test policy

Every behavior checkpoint B5A/B5B/B6/B7A/B8A/B8B/B7B/B8C/B9/B10 includes **RP-LOCAL**, proportionate to its changed state. For a pure kernel the replay check is exact deterministic input/output and checkpoint round trip; for a durable handler it must use actual PostgreSQL owner transactions. RP-LOCAL requires: identical duplicate is inert; known changed content is retained as conflict before stale filtering; original semantic/delivery IDs, config and evidence remain pinned; injected failures at each state/outbox/receipt cutpoint are atomic; after-commit redelivery reuses accepted state; terminal/epoch/resolution dominance prevents resurrection; raw accepted histories hydrate before new input. An early typed-interface fixture never substitutes for the later real producer/consumer integration.

Independent test oracles come from frozen equations, branch tables, source-membership/identity sets and invariants. Expected values cannot simply be captured from the implementation under test. Native stubs must supply explicit acceptance/execution/coverage/provenance evidence; action names such as “cancelled” or “rejected” are not proof of zero execution or source finality. Source/profile conformance is a separate factual certificate, not inferred from a green mock test.

### 10.4 Focused observation review assignments — existing categories only

The R5 observation-specific review assignments below remain unchanged in scope. The **19 central and detailed mandatory-review lists remain synchronized**. For R6, B12 additionally applies three existing categories (numeric, adversarial trading and persistence) to its newly explicit diagnostic report implementation, as §10.5 specifies. No new reviewer category, business owner or checkpoint is added.

| Checkpoint | Requirement / local responsibility under its existing review categories |
| --- | --- |
| B5A | NR-054/055/068: implementation/numeric/trading/test review independently checks full classifier input authority and AT-NR-068-CF A–D. Existing persistence/replay reviews verify the separately bound work histories; contract review rejects new wire fields. |
| B5B | Same requirements: actual independent-branch final join, unmatched reasons, no partial success IDs and exact TX.set persistence/replay through A–D. Existing AT-NR-053 A–H and generic direction scope remain separate mandatory coverage. |
| B8A | NR-151: implementation/test review of full status/gate/reason and scope/day/capacity observations; persistence/replay of complete historical basis; numeric utilization/cap values; adversarial capacity/disabled/unavailable cases; existing accounting-finality review of day/base/latch and Portfolio recovery history. |
| B8B | NR-151: implementation/test of all actual grant outcomes, denials and evaluated reasons; persistence/replay of issue versus denial and original timestamps; numeric candidate/grant amounts; adversarial capacity-missed opportunities; contract review of unchanged non-reserving outputs. No terminal accounting is implemented here. |
| B8C | NR-151: implementation/test/persistence/replay of current gate/denial/H/slot/auth history, grant consumption and concurrency; numeric exact H/never-held surplus/utilization; adversarial capacity/hold races; contract review of immutable confirmation and audit-only producer T. Original day/latch logic is already reviewed at its B8A producer; actual terminal receipt/release remains B10. |
| B9 | NR-152 and Portfolio NR-151 factual projections: implementation/test of every operational history/§40 visibility item; persistence/replay of captured arrivals, all cutpoints, race/episode/verification/manual evidence; API-provenance review of actual sources/times/chronology; adversarial native ambiguity/cleanup/manual/cancel/close behavior; numeric quantities/pre-close Portfolio H basis and report-only derivations; contract review of no new edge/field. |
| B10 | NR-151/152: existing accounting-finality and numeric reviews of factual component/basis/FINAL visibility and separate Portfolio day/receipt/release history; persistence/replay of source/observation/receipt uniqueness and retention; implementation/test/contract review of complete coverage without new financial authority. |
| B11 | Verification only: existing implementation/persistence/replay/test reviews stress already-captured owner histories and distinguish fixed captured-arrival replay from new physical redeliveries; a missing producer reopens the original checkpoint. |
| B13 | Verification only: existing architecture/test/trading/accounting/numeric reviews cover all 154 requirements and V18/V19; no metric/import/view becomes a new canonical decision path, and no missing history is first fabricated here. |
| B14 | Independent implemented-backend audit includes all 154 groups and every observation basis/case. Candidate self-checks are not implementation evidence. |

Within RP-LOCAL, “identical duplicate is inert” continues to mean no repeated business/economic/native effect. Reprocessing the same captured diagnostic observation is also inert. A genuinely distinct duplicate **arrival instance** may require a separately retained diagnostic observation under NR-152, without becoming a second economic effect. Tests must supply fixed capture IDs/bases when asserting identical observation histories; see §6.3.2. There is no change to native retry authority, grant identity, financial finality or transport graph.

### 10.5 FA-R5-01 local reporting reviews — existing categories only

Each responsibility below is part of the producing checkpoint’s local review before commit/push. B13 architecture/isolation review verifies earlier implementation; it is not the first quantitative or persistence review. The two added NR rows have no unassigned reporting review scope.

| Checkpoint | Mandatory local scope using existing review categories |
| --- | --- |
| B3 | IMPLEMENTATION_REVIEW/TEST_REVIEW verify the extended existing Research ingestion/cache/SQLite manifest capability, source publication order and truthful current downloader limits. API_PROVENANCE_REVIEW checks raw factual price kind/instrument/profile, coverage/chronology and no fabricated intra-bar evidence; PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW verify immutable objects/manifests, same-content reuse, conflicts, retention and failed-import recovery. CONTRACT_REVIEW verifies the three unchanged canonical API edges; Research documentary input is not another trading requester or wire family. No report metric or owner business rule is implemented here. |
| B7A | IMPLEMENTATION_REVIEW/TEST_REVIEW check every E/T Position-source item and candidate/traversal/classification field in actual initial outcomes, including rejected opportunities. NUMERIC_PRECISION_REVIEW verifies original raw/rounded distance operands, exact age and no latest ATR; ADVERSARIAL_TRADING_REVIEW checks distinct failure cohorts, unvisited candidates, independent F-010 despite Stop unavailability and no report gating. PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW check same TX.opportunity retention, exact pins and duplicate/crash behavior. Existing CONTRACT_REVIEW confirms no extra handoff/spec wire field; all additional report fields are owner-local diagnostics. |
| B9 | IMPLEMENTATION_REVIEW/TEST_REVIEW check actual submit/native POST_ONLY/current-hard-refusal/acceptance/fill/close factual source records and exact report lineage. API_PROVENANCE_REVIEW verifies real source/effective time/order/coverage, not prediction or receipt-time inference; NUMERIC_PRECISION_REVIEW verifies exact quantities/prices/time-basis projections. PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW verify source capture under original transactions, duplicate business-member identity and recovery. Existing adversarial/contract reviews forbid new native authority, extra API edge or foreign mutable-state lookup. Public Research path acquisition stays in the B3-established documentary boundary. |
| B10 | ACCOUNTING_FINALITY_REVIEW/NUMERIC_PRECISION_REVIEW verify that expectancy consumes original full-tranche immutable net/currency and path completion uses permanent factual closing chronology, not component FINAL/cleanup/receipt or a recalculated P&L. IMPLEMENTATION_REVIEW/TEST_REVIEW and PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW check once-only result/source links and failed-copy recovery. Existing CONTRACT_REVIEW confirms no new result/receipt field or owner. B9/B3 source-provenance review remains prerequisite; B10 does not newly acquire a public price feed. |
| B11 | Existing IMPLEMENTATION_REVIEW, PERSISTENCE_TRANSACTION_REVIEW, REPLAY_IDEMPOTENCY_REVIEW and TEST_REVIEW stress **source/manifest retention only**. Full report assembly remains B12; no reverse completion gate or new B11 producer. |
| B12 | IMPLEMENTATION_REVIEW/TEST_REVIEW verify all 19 Entry items, 17 TP items, 32 named cases and shared unavailable/zero-cohort/source-resolution cases through actual ResearchService/analytics/SQLite report persistence. NUMERIC_PRECISION_REVIEW covers exact ratios/means/bands/timing/extrema and explicitly pinned diagnostic sensitivity. ADVERSARIAL_TRADING_REVIEW proves no live feedback, no simulator/canonical substitution and no automated optimization/promotion. PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW cover immutable report publication/manifest membership and restart, explicitly without cross-database atomicity. Existing ARCHITECTURE_CONFORMANCE_REVIEW checks read-only source access, one worker, unchanged storage and no new business edge; E2E includes the existing read-only presentation path as well as unchanged dispatcher tests. The three added tokens use existing categories and are present in both the central and detailed B12 lists. |
| B13 | Existing ARCHITECTURE_CONFORMANCE_REVIEW/TEST_REVIEW/ADVERSARIAL_TRADING_REVIEW/NUMERIC_PRECISION_REVIEW verify V20/V21 source-to-report integration, Research isolation, exact cohort/path pins and zero feedback. Existing ACCOUNTING_FINALITY_REVIEW verifies that reported realized outcomes are copies of actual FINAL, not another ledger. No report is implemented for the first time here. |
| B14 | Existing independent full conformance scope covers all 154 groups, required report evidence and implementation/test/review records, without accepting candidate self-checks as runtime proof. |


## 11. Canonical worker activation gate

B12 may enable a registered canonical dispatch route only after the revised plan has passed independent certification and all applicable prerequisites below have implementation evidence. Planning-level CLOSED labels alone satisfy none of the implementation conditions.

| Gate | Required evidence before activation |
| --- | --- |
| Planning correction gate | Independent acceptance of this revised R6 plan, including FA-R5-01 required-report closure and the protected-core comparison in §16. Candidate closure labels and historical §14–15 statements alone do not satisfy this gate. |
| Frozen contract gate | B0 actual parser/schema/whitelist aligned; all twelve families and both F-013 branches, binary per-item statuses and used schema constructs tested. |
| Numeric/binding/durability gate | B1/B2 complete with exact arithmetic and real PostgreSQL UoW/outbox/inbox/frontier evidence; no duplicate infrastructure. |
| Factual boundary gate | B3/B4 and actual owner integrations complete; three bidirectional API paths; accepted provenance/preflight; no Position/API or generic business helper bypass. |
| Set/Position/Portfolio owner gate | B8A/B5A/B5B/B6/B7A/B8B/B7B/B8C local and integration gates passed; exact real staged owner flow. |
| Lifecycle/native evidence gate | B9 complete, including actual placement/terminal return to Set, hard facts, stable native intent, current protection, source partition/receipts and close authority. |
| Financial/receipt gate | B10 complete: source/coverage/currency, both allocation algorithms, immutable FINAL/six-predicate CLOSED and Portfolio own receipt/day/A-009/release. |
| Incident/ordering gate | Committed-prefix scope/head/publication and Portfolio current eligibility/receipt tested in both commit orders; no cached-head/dedupe substitute. |
| Local and integrated recovery gate | All owner RP-LOCAL and B11 stress gates passed with actual applicable database evidence; no skipped required suite counted green. |
| Invariant/blocker gate | All twenty invariants have actual implementation+test+review evidence; every BLOCKER implementation finding closed, not just mapped. |
| Legacy isolation gate | One existing canonical worker/launcher; no demo/paper/spot/SQLite/legacy formula fallback for unknown or incomplete paths. |
| Separate native exposure gate | Where exposure-changing operations are enabled, applicable native profile certification, current hard/protection/quantity facts and existing operator/runtime authority are satisfied. Dispatch readiness alone is insufficient. |

Unknown consumer/message/version, incomplete handler, unresolved integrity, missing required current facts, unavailable financial proof or uncertified native operation stays fail-closed. Diagnostic and governed reconciliation capability may be available without granting exposure-changing authority. No new trading expiry/timer or scheduler strategy is introduced. B13 integrated verification and B14 independent backend audit still follow; enabling a testable dispatcher is not a statement of live-trading or profitability readiness.

**R6 reporting completion qualification:** B12 also implements/reviews the separate technical report capability from NR-153/154 using completed B3/B7A/B9/B10 sources. It is not a new runtime input to dispatch/native gates. A particular report’s missing path/FINAL, unavailable source or absent optional experiment configuration must remain correctly unavailable without blocking otherwise valid canonical trading. B13/B14 still verify the complete implemented capability and its isolation.


## 12. Verification plan and global invariant closure

### 12.1 V-FULL: required B13 integrated scenarios

| Case | Integrated scope | Required assertions |
| --- | --- | --- |
| V01 | Full applicable existing regression | Foundation JSON/durability/contracts/state/gateway/runtime/research tests preserved; old-schema tests updated only at proper source boundary. |
| V02 | All twelve contract families | Both API directions, all governed variants, strict parser+owner semantic binding and exact graph; no extra edge. |
| V03 | All eighteen certified objects | Source-derived numerical/state expectations, all supporting populations and compound unavailable/failure branches; S-005 tested as isolation only. Include AT-NR-053 A/E for F-005-governed authority without widening its scope; generic direction positives are separately exercised under V04, not counted as extra certified objects. Include AT-NR-068-CF A–D: genuine classifier computations independent of trigger availability/populations, with real classifier-veto sensitivity. |
| V04 | Complete staged owner flow | COINS→Set MATCHED→initial Position→grant→Position result/spec+two outboxes→current Portfolio H/auth→Lifecycle exact join. Exercise both Set direction scopes through AT-NR-053 A–F and cross-owner negatives G, without forcing generic Sets through F-005. Include AT-NR-036 01–04: valid 80%-targets/60%-global configuration, runtime global/per-coin rejection and exact allowed capacity boundary under current H booking. Join classifier and configured formation only at final Set resolution; a valid classifier with FALSE/UNAVAILABLE formation has no success IDs/handoff. NR-151/152 observation capture accompanies the same existing owner paths. |
| V05 | Placement and F-013 return loop | Actual Lifecycle ORDER_PLACED→Set activation; INVALIDATION and MONITORING_UNAVAILABLE; exact remainder/native reconcile; terminal return and sticky replay. |
| V06 | Fail-closed factual paths | Missing/stale/malformed/foreign/uncertified facts, required population gaps, optional vs required inputs and durable known-conflict capture before ordinary rejection. |
| V07 | Native create ambiguity | Persisted intent before side effect, lost ack, retry same client ID, current hard/profile refusal, no unauthorized replacement trade. |
| V08 | Partial fill/cancel/rejection races | Factual execution precedence, original remainder only, filled exposure retained/protected, zero-fill/no-create terminal paths separate. |
| V09 | Current protection and single close authority | Query omission invalidates current proof; no historical union or blind replacement; concurrent causes/uncertain child use one current residual budget. |
| V10 | Native source partition and receipts | Pre-manifest zero effect, disjoint gap-free exact slices, global binding/aliases, all orderings, correct separate Portfolio projection. |
| V11 | Financial sources and allocations | Full immutable raw core/aliases/coverage/applicability/currency; A-004 signed q18 conservation and distinct non-funding source quantum conservation. |
| V12 | A-002 and S-004 | Actual execution-derived cost, permanent final chronology, current revision proof and all six predicates; immutable FINAL/CLOSED/outbox transaction. |
| V13 | Portfolio receipt and A-009 | Own first delivered_at, result/tranche uniqueness, economic-day post/latch/release, late historical first result, DST/rollover, no wallet double-credit. |
| V14 | Committed-prefix incidents | Both receipt/incident linearization orders, undelivered committed incident, stale/same-conflict revision, gaps, crash/retry and future eligibility block. |
| V15 | Complete replay/restart/concurrency | Every owner and native cutpoint, immutable evidence/config history, current proof invalidation, once-only money/quantity and terminal dominance. AT-NR-053 H explicitly retains original governing scope, matched-branch/configuration/direction binding and cycle/result/handoff identity through configuration changes and restart. Apply NR-151/152 fixed-captured-history replay to full denied/reason/cutpoint/race evidence; distinguish extra real arrival observations from repeated economic effects. Retain complete source basis, not mutable latest counters. |
| V16 | No legacy/research canonical reachability | Actual dispatcher/import/runtime paths cannot choose SQLite/demo/paper/spot/S-005 authority; no second worker or formula-only pipeline. |
| V17 | All twenty invariants | Each row below has traceable implementation, independent test and review evidence; a skip or unresolved BLOCKER prevents a passing integrated scope. |
| V18 | Portfolio owner status/diagnostic history — NR-151 | Actual B8A/B8B/B8C/B9/B10 producers retain every P01–P33 observation, allowed/blocked/unavailable status, complete evaluated reasons and original grant/hold/day/reconciliation/release basis. AT-NR-151 cases01–12; no B12/Research producer, duplicate count, fake surplus release, Position formula recomputation or latest-state reconstruction. |
| V19 | Lifecycle operational/financial observation history — NR-152 | Actual B9/B10 producers satisfy L01–L40 and §40 visibility, full AT-NR-152 cases01–12, immutable arrival identity, auth/publication/cleanup cutpoints, race quantities and factual financial basis. Economic idempotency and captured-arrival retention are separately verified; no new native/finality authority. |
| V20 | Required Entry report — NR-153 | Actual B7A original Entry/reason/configuration evidence, B9 actual native/fill facts, B10 immutable outcomes and B3 diagnostic path archive feed the already implemented B12 read-only Research report. Verify all E01–E19/ENTRY-RPT-01–15, exact cohort/denominator/band/age/path/member pins, SQLite persistence/restart and explicit incompleteness; no current-state or P&L-only proxy, synthetic missed trade or feedback. |
| V21 | Required TP report — NR-154 | Actual F-010 original target/thesis/traversal evidence plus factual executions/horizon/path feed the completed B12 report. Verify T01–T17/TP-RPT-01–17, distinct reasons, target touch versus actual TP exit, exact or explicitly unresolved timing, MAE/MFE, original day/1h types and pinned one-axis sensitivity. No legacy simulator, automatic promotion, new canonical edge or changed F-010 output. |

The reporting invariant `RESEARCH_REPORTING_HAS_NO_CANONICAL_DECISION_AUTHORITY` in §6.4.10 specializes existing global invariant 6. It does not add a twenty-first global invariant, change its owner or authorize a reporting-to-trading feedback path.


### 12.2 All twenty invariants — planned implementation, test and review

Every row is **PLANNED**, not an execution PASS. The assigned owner/checkpoint, test and review are explicit; none is left PLAN_INCOMPLETE. For row 9, canonical filled-tranche finality is not confused with the separately proven zero-fill/no-create terminal resource paths described in §7.4.

| # | Invariant | Implementation checkpoint(s) | Normative anchor | Required test | Review gate | Planning status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Set alone owns final market direction | B5A/B5B | NR-053; NR-068 | AT-NR-053 A–H: F-005 alone resolves direction in governed scope and fixed/branch labels cannot bypass it; valid generic fixed-direction and explicit matched-branch Sets outside that scope resolve within Set without spuriously requiring F-005; opposing generic branches use only their valid declared deterministic conflict rule, otherwise no valid outcome/handoff; API, Portfolio, Position (including reversal) and Research/S-005 cannot set direction. Replay retains original scope/configuration/branch/direction and identities. This is Set ownership, not universal F-005 execution. | CONTRACT_REVIEW; ADVERSARIAL_TRADING_REVIEW | PLANNED |
| 2 | Position alone owns trade construction | B7A/B7B | NR-098 | Only Position emits initial/construction decisions and ORDER_SPEC from exact pinned chain. | CONTRACT_REVIEW; ADVERSARIAL_TRADING_REVIEW | PLANNED |
| 3 | Portfolio alone owns capital/holds/limits | B8A/B8B/B8C | NR-048 | Only current Portfolio transaction books H/slot and emits authorization. | PERSISTENCE_TRANSACTION_REVIEW; CONTRACT_REVIEW | PLANNED |
| 4 | Lifecycle alone owns native side effects | B9/B12 | NR-102 | No other owner/helper/dispatcher can call exposure-changing native operations. | API_PROVENANCE_REVIEW; ARCHITECTURE_CONFORMANCE_REVIEW | PLANNED |
| 5 | API is factual only | B3/B4/B13 | NR-024 | Bidirectional technical requests/responses never choose strategy/allocation; no Position API edge. | API_PROVENANCE_REVIEW; CONTRACT_REVIEW | PLANNED |
| 6 | Research cannot affect canonical decisions | B0/B12/B13 | NR-020 | S-005/legacy import and dispatch traps; historical pins not re-certified by default update. | ARCHITECTURE_CONFORMANCE_REVIEW; TEST_REVIEW | PLANNED |
| 7 | No duplicate economic effect | B2/B5B/B6/B7A/B8B/B7B/B8C/B9/B10/B11 | NR-135 | Duplicate/conflicting delivery at every owner and financial/quantity receipt boundary. | REPLAY_IDEMPOTENCY_REVIEW; PERSISTENCE_TRANSACTION_REVIEW | PLANNED |
| 8 | Immutable evidence/configuration binding | B1/B3/B4/B5B/B7A/B8C/B9/B10 | NR-149 | Active config changes and malformed old evidence cannot rebind accepted history. | CONTRACT_REVIEW; REPLAY_IDEMPOTENCY_REVIEW | PLANNED |
| 9 | No premature capital release | B8C/B9/B10 | NR-046 | Partial exit/flatness/cleanup without six-predicate FINAL and clear fenced receipt retains closing capital/slot; explicit proven zero-fill/no-create paths separate. | ACCOUNTING_FINALITY_REVIEW; PERSISTENCE_TRANSACTION_REVIEW | PLANNED |
| 10 | Flatness alone is not CLOSED | B9/B10 | NR-127 | Set each of six predicates false in isolation; zero exposure alone cannot terminalize. | ACCOUNTING_FINALITY_REVIEW; ADVERSARIAL_TRADING_REVIEW | PLANNED |
| 11 | F-013 never cancels filled exposure | B6/B9 | NR-081 | Full fill/partial fill/cancel races prove target is only authoritative original unfilled remainder. | ADVERSARIAL_TRADING_REVIEW; API_PROVENANCE_REVIEW | PLANNED |
| 12 | Portfolio holds H, not C | B7B/B8C | NR-048 | C>H unused capacity stays free; authorization/spec/confirmation/hold carry same H. | NUMERIC_PRECISION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW | PLANNED |
| 13 | A and H remain distinct | B1/B7B/B8C | NR-011 | Nonterminating exact A and ceiling H differ; equal numerical grid case does not erase type/semantic distinction. | NUMERIC_PRECISION_REVIEW | PLANNED |
| 14 | FINAL immutable and once-only | B10 | NR-126 | All same/changed source/coverage/attribution postfinal paths retain result and use separate incident. | ACCOUNTING_FINALITY_REVIEW; REPLAY_IDEMPOTENCY_REVIEW | PLANNED |
| 15 | Funding fully conserved | B10 | NR-120 | Signed source exactly equals all persisted allocations; deterministic raw-largest/lexical residue both signs. | ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW | PLANNED |
| 16 | Daily Loss consumes immutable FINAL on economic day | B8A/B10 | NR-043 | Once-only historical day sum, retained latch, late first result and DST/rollover cases. | ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW | PLANNED |
| 17 | No implicit FX | B8B/B7B/B10 | NR-119 | Foreign required sources block even if net zero; funding mark is weight only. | ACCOUNTING_FINALITY_REVIEW; CONTRACT_REVIEW | PLANNED |
| 18 | No hidden cross-owner formula recomputation | B3/B4/B7B/B8C/B9 | NR-052 | Consumer validates exact output/binding without importing another owner’s kernels or rebuilding geometry. | ARCHITECTURE_CONFORMANCE_REVIEW; CONTRACT_REVIEW | PLANNED |
| 19 | No latest/symbol/nearest-time identity inference | B1/B3/B4/B5B/B6/B7A/B9/B10 | NR-013 | Adversarial equal-symbol/time but different accepted identity; only exact permitted historical indexes resolve owner. | REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW | PLANNED |
| 20 | No canonical legacy/demo fallback | B1/B5A/B5B/B7A/B7B/B9/B10/B12/B13 | NR-134 | Unready canonical owner stays blocked rather than routes to legacy formula/runtime/SQLite or second worker. | ARCHITECTURE_CONFORMANCE_REVIEW; TEST_REVIEW | PLANNED |

### 12.3 Current evidence limitations and future acceptance discipline

The attached source evidence establishes reusable infrastructure and missing canonical integrations; it does not establish a newly run PostgreSQL deployment or a certified exchange profile. Historical focused/broad test logs are not run results of this revision. A future required suite unavailable because its dependency/database/native environment is missing is reported as **NOT EXECUTED**, with its affected gate incomplete; it is never silently counted green.

B13 verifies already-correct locally reviewed behavior through the actual dispatcher. B14 independently rechecks then-current source, actual applicable execution evidence and this source-clause register; it must not certify from old audit counts, prior approval banners or implementation-map DONE flags. A failed re-audit starts a separate bounded remediation/review cycle, not a silent edit to the frozen methodology.

## 13. Complete checkpoint specifications

Every checkpoint below is future implementation/review scope. `FILES/SURFACES_EXPECTED_TO_EXTEND` resolves to the exact classified FN inventory in §2. `NEW_SURFACES_IF_REQUIRED` names only explicit proposals, not existing files. Original methodology and source evidence are protected throughout; new tests and migrations described here are not created by this planning revision.

## B0 — Frozen source alignment

**PRIORITY:**

P0

**PURPOSE:**

Make the existing public contract boundary conform to the attached frozen v1.2.15 package, not just its metadata.

**NORMATIVE_REQUIREMENTS:**

NR-002, NR-003, NR-004, NR-005

**HISTORICAL_TRACEABILITY_ALIASES:**

R005, R010, R011, R012, R014, R029, R052, R053, R054, R055, R056

**EXISTING_FOUNDATION_REUSED:**

FN.CONTRACT, FN.RESEARCH, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

CONFLICTING current package/branch enforcement; reusable registry and parser [E26–E29; schema_probe.json]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Frozen v1.2.15 public parser/schema/whitelist and active defaults align; family versions unchanged; worker remains blocked.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.CONTRACT: Registry/generated schema/parser — src/triggertrade/contracts/registry.py; src/triggertrade/contracts/_approved_wire_schema.py; src/triggertrade/contracts/schema_validator.py; ADAPT under §2 classification.

FN.RESEARCH: Research pins/isolation/governance — `src/triggertrade/research_pins.py::research_pin_payload` (existing helper, REUSE); `src/triggertrade/persistence/research_store.py::ResearchStore` (existing SQLite research persistence); `src/triggertrade/persistence/operator_state_store.py::OperatorStateStore` (existing SQLite operator-state persistence); `src/triggertrade/persistence/research_promotion_governance.py::ResearchPromotionGovernanceStore` (existing PostgreSQL promotion-request / outbox governance only); ADAPT under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

None expected in production; CONDITIONAL_NEW parser differential fixtures only if existing contract suites cannot express them.

**LEGACY_SURFACES_TO_FENCE:**

Preserve archive-negative fixtures and historical pins; no legacy runtime promotion.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

No business transaction introduced; later owners retain §7 atomicity.

**CONTRACTS_TOUCHED:**

All 12: public parser/registry/schema alignment only.

**IDENTITY_BINDINGS:**

Existing package/family/configuration/content bindings as applicable; no premature business IDs.

**NUMERIC_REQUIREMENTS:**

Preserve decimal wire patterns and canonical serializer; no business formula calculation.

**IMPLEMENTATION_SCOPE:**

Regenerate the existing embedded schema from frozen wire.schema.json; align package revision, root required/optional whitelists and definitions; inventory all constructs used by this exact schema and implement the minimum missing enforcement in the existing validator now (including oneOf/not). Preserve all twelve family versions. Update only active package/default/test expectations; historical facts remain unchanged.

**TESTS_REQUIRED:**

Public parse_contract tests for all twelve families, exact current branch positives/negatives, per-item PARTIAL rejection for instrument_metadata AND fee_rates, aggregate mixed status, requested-row cardinality, metadata/schema equality and existing JSON/research integrity regressions. Required schema keywords cannot be silently ignored.

Existing regression examples (non-exhaustive): `tests/contract/test_canonical_json_contract.py` (EXISTING), `tests/contract/test_target_contract_registry.py` (EXISTING), `tests/unit/test_canonical_json.py` (EXISTING), `tests/unit/test_methodology_integrity.py` (EXISTING), `tests/unit/test_research_backend.py` (EXISTING), `tests/unit/test_target_contracts.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-002, AT-NR-003, AT-NR-004, AT-NR-005.

**NEGATIVE_BOUNDARY_TESTS:**

Eight ORDER_CANCEL_SIGNAL cases in §9.1, unknown field/version/cause, both causes with wrong cross-branch content, missing fields, optional record reference. Include schema-only refresh as a negative control demonstrating that unsupported oneOf/not is not enough.

**REPLAY_RESTART_TESTS:**

Repeated parse/serialize of each valid envelope is canonical and inert; existing immutable research evidence is not rewritten. No persistence/runtime behavior is introduced.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**UPSTREAM_DEPENDENCIES:**

Attached frozen package; independent acceptance of the revised plan before implementation.

**DOWNSTREAM_DEPENDENTS:**

B1, B2, B3, B4, B8A, B5A, B6, B7A, B12

**DEFINITION_OF_DONE:**

Actual public parser, whitelist and embedded schema agree with the frozen package on valid and invalid cases; applicable implementation/contract/test reviews pass. Owner production remains unimplemented and worker remains blocked.

**RISKS:**

A green schema generation test can hide a parser branch defect; blanket v1.2.14 search/replace can corrupt history.

**DO_NOT:**

Do not defer currently required schema semantics to B1, bump family versions, implement owner behavior, modify frozen files or activate dispatch.

## B1 — Exact numeric and binding foundation

**PRIORITY:**

P0

**PURPOSE:**

Supply one reusable exact arithmetic/identity toolkit without embedding owner formulas or duplicating canonical JSON.

**NORMATIVE_REQUIREMENTS:**

NR-006, NR-007, NR-008, NR-009, NR-010, NR-011, NR-012, NR-013, NR-150

**HISTORICAL_TRACEABILITY_ALIASES:**

R001, R013, R015, R019, R020, R035, R036, R042, R043

**EXISTING_FOUNDATION_REUSED:**

FN.JSON, FN.CONTRACT, FN.PIN, FN.RESEARCH, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: canonical serialization exists; required exact calculation layer not established [E30,E37; audit §19]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

One exact generic numeric/binding foundation supports owner kernels without a second serializer or formula subsystem.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.CONTRACT: Registry/generated schema/parser — src/triggertrade/contracts/registry.py; src/triggertrade/contracts/_approved_wire_schema.py; src/triggertrade/contracts/schema_validator.py; ADAPT under §2 classification.

FN.PIN: Position configuration-pin capability — `src/triggertrade/persistence/position_config_pin_store.py::PositionConfigPinStore` (inventory L32); src/triggertrade/position_config_pins.py; EXTEND under §2 classification.

FN.RESEARCH: Research pins/isolation/governance — `src/triggertrade/research_pins.py::research_pin_payload` (existing helper, REUSE); `src/triggertrade/persistence/research_store.py::ResearchStore` (existing SQLite research persistence); `src/triggertrade/persistence/operator_state_store.py::OperatorStateStore` (existing SQLite operator-state persistence); `src/triggertrade/persistence/research_promotion_governance.py::ResearchPromotionGovernanceStore` (existing PostgreSQL promotion-request / outbox governance only); ADAPT under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/numeric_policy.py for proven missing exact primitives. CONDITIONAL_NEW src/triggertrade/identifier_lineage.py only for genuinely shared missing binding functions; extend existing helpers first.

**LEGACY_SURFACES_TO_FENCE:**

FN.LEGACY execution/precision.py remains demo-only without independent semantic equivalence.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

No business transaction introduced; later owners retain §7 atomicity.

**CONTRACTS_TOUCHED:**

All 12 indirectly for exact numeric/binding utilities; no business producer or wire shape changes.

**IDENTITY_BINDINGS:**

Existing package/family/configuration/content bindings as applicable; no premature business IDs.

**NUMERIC_REQUIREMENTS:**

§8 is mandatory: exact rational intermediates, Q36 and Q18 HALF_EVEN, Qcapital 1e-12 directional policy, Qratio 1e-18 floor report-only, exact A distinct from H.

**IMPLEMENTATION_SCOPE:**

Implement exact finite decimal parsing, scaled integer/rational representation and arithmetic/comparison; explicit finite resource failure. Provide named quantizers, signed rounding, directional tick/step and exact integer-midpoint sqrt. Separate WORKING/WIRE/REPORT_ONLY types or validated boundaries. Keep opaque persisted ID semantics and existing digests; no universal remint-by-hash scheme. B0 branch conformance remains a regression gate, not deferred work.

**TESTS_REQUIRED:**

Independent rational/scaled-integer oracle, signed floor/ceil/truncation and HALF_EVEN ties, Q36/Q18/export boundaries, Qcapital spendable/liability, report-only Qratio, tick/step and exact midpoint sqrt. Serialize/deserialize same exact result.

Existing regression examples (non-exhaustive): `tests/contract/test_canonical_json_contract.py` (EXISTING), `tests/contract/test_target_contract_registry.py` (EXISTING), `tests/unit/test_canonical_json.py` (EXISTING), `tests/unit/test_position_config_pin_store.py` (EXISTING), `tests/unit/test_position_config_pins.py` (EXISTING), `tests/unit/test_research_backend.py` (EXISTING), `tests/unit/test_target_contracts.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-006, AT-NR-007, AT-NR-008, AT-NR-009, AT-NR-010, AT-NR-011, AT-NR-012, AT-NR-013, AT-NR-150.

**NEGATIVE_BOUNDARY_TESTS:**

Binary float/nonfinite/exponent/canonical-output errors, zero denominator/invalid quantum, context precision exhaustion, near-threshold ratio collisions and accidental reuse of report values as work values.

**REPLAY_RESTART_TESTS:**

Pure functions deterministic for identical accepted operands; resource errors explicit. Replay cannot turn rounded wire data into an invented high-precision value.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**UPSTREAM_DEPENDENCIES:**

B0

**DOWNSTREAM_DEPENDENTS:**

B2, B3, B4, B8A, B5A, B6, B7A, B12

**DEFINITION_OF_DONE:**

Exact primitive behavior and canonical boundaries are independently reviewed/tested. No owner equation, trade decision, funding allocation or new persistence has entered the shared layer.

**RISKS:**

Decimal division under a finite context may look exact while moving a gate; one generic allocator could silently merge two different policies.

**DO_NOT:**

Do not implement F-001/F-002/Entry/Stop/TP/sizing/economics/allocation equations here; do not replace canonical_json.py merely to reorganize.

## B2 — Shared durable foundation

**PRIORITY:**

P0

**PURPOSE:**

Prove composition of the already-existing PostgreSQL UoW/stores/transport and the required scoped existing-edge frontier, without designing every future domain table.

**NORMATIVE_REQUIREMENTS:**

NR-014, NR-015, NR-016, NR-017

**HISTORICAL_TRACEABILITY_ALIASES:**

R002, R003, R004, R030, R043

**EXISTING_FOUNDATION_REUSED:**

FN.UOW, FN.CAS, FN.MSG, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: existing PostgreSQL UoW/CAS/outbox/inbox; domain and frontier composition not proven [E31–E32; audit §17]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Shared PostgreSQL owner composition and scoped frontier are proved; future domain storage remains assigned to its owners.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.CAS: OwnerStateStore — `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128); EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW domain-independent transport frontier helper/forward migration only after existing store inventory proves the missing capability. No new outbox/inbox/worker/ledger.

**LEGACY_SURFACES_TO_FENCE:**

SQLite stores are not eligible for canonical transaction composition.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.transport, ST.frontier. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row. B2 introduces only shared transport/CAS/frontier capability, never incident, result, day or other owner-domain records.

**TRANSACTION_BOUNDARIES:**

TX.owner, TX.frontier; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

Existing owner transport envelopes only; no new family/field/version. Technical frontier is internal.

**IDENTITY_BINDINGS:**

Committed-prefix technical scope/head/applied sequence

**NUMERIC_REQUIREMENTS:**

Store exact canonical text/rational components where required; persistence cannot impose hidden database rounding. B2 chooses no formula quantizer.

**IMPLEMENTATION_SCOPE:**

Inventory current connection ownership and commit behavior of reused stores; expose safe outer-UoW composition and compatible CAS. Implement only generic state+outbox+inbox atomicity and same-edge scoped head/prefix serialization. Use a fixed lock acquisition order and retry policy. Plan forward-only migration/upgrade tests against the actual next unused repository revision when implemented. Leave Set/monitor/Position/Portfolio/native/financial entities to their owning checkpoints.

**TESTS_REQUIRED:**

Actual isolated PostgreSQL transactions, rollback at every store/outbox step, durable duplicate/conflict handling, concurrent claim behavior and scoped append/receipt-frontier serialization with a technical stub consumer. Preserve all existing message tests.

Existing regression examples (non-exhaustive): `tests/unit/test_durable_messages.py` (EXISTING), `tests/unit/test_postgres_persistence_foundation.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-014, AT-NR-015, AT-NR-016, AT-NR-017.

**NEGATIVE_BOUNDARY_TESTS:**

Nested store auto-commit, cross-connection pseudo-atomic writes, cached-head receipt, missing prefix gap, deadlock/retry and same-ID different content. Verify independent scopes do not falsely share eligibility.

**REPLAY_RESTART_TESTS:**

Hydrate committed head/prefix and CAS revisions; crash before/after commit, lost claim lease and repeated acknowledgement never duplicate committed owner effect.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; ARCHITECTURE_CONFORMANCE_REVIEW

**UPSTREAM_DEPENDENCIES:**

B0, B1

**DOWNSTREAM_DEPENDENTS:**

B3, B4, B8A, B5A, B6, B7A, B10, B12

**DEFINITION_OF_DONE:**

Generic durability/frontier capability and extension/reuse inventory are reviewed and transaction-tested. No complete future owner-state claim and no domain schema pre-creation.

**RISKS:**

Premature B2 ledgers duplicate existing stores or force later migrations; SKIP LOCKED/dedupe is not a serializable receipt frontier.

**DO_NOT:**

Do not pre-create ATR, Set results, monitor requirements, construction/grants, day/latch, native protection, funding, FINAL/CLOSED or Portfolio receipt models here. Do not rewrite applied migrations.

## B3 — Factual adapters and accepted-evidence intake

**PRIORITY:**

P1

**PURPOSE:**

Extend the three existing bidirectional API families with complete factual provenance and contradiction-preserving intake interfaces.

**NORMATIVE_REQUIREMENTS:**

NR-004, NR-019, NR-021, NR-022, NR-023, NR-024, NR-025, NR-026, NR-027, NR-028, NR-029, NR-031, NR-032, NR-143, NR-145, NR-153, NR-154

**HISTORICAL_TRACEABILITY_ALIASES:**

R005, R013, R015, R016, R017, R027, R028, R030, R031, R044, R047, R048

**EXISTING_FOUNDATION_REUSED:**

FN.API, FN.FACT, FN.NATIVE, FN.RECON, FN.UOW, FN.MSG, FN.TEST; see §2 for exact components and preservation action.

R6 documentary evidence scope additionally reuses FN.RESEARCH and the existing `backtest/data.py` historical input/cache organization (§6.4.1). No new canonical factual owner or API requester.

**CURRENT_STATE:**

PARTIAL: factual normalization/stores exist; accepted-content and owner integration incomplete [E33–E34,E56–E57; audit §§11,17]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Three strictly factual bidirectional API paths preserve accepted provenance and known conflicts; owner integrations remain explicit downstream work.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.API: Factual API normalization — src/triggertrade/api_adapter_gateway/market_data.py; src/triggertrade/api_adapter_gateway/portfolio_data.py; src/triggertrade/api_adapter_gateway/order_management.py; EXTEND under §2 classification.

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.NATIVE: Native factual profile boundary — src/triggertrade/api_adapter_gateway/native_profile.py; EXTEND under §2 classification.

FN.RECON: Lifecycle reconciliation/events — `src/triggertrade/persistence/lifecycle_reconciliation_store.py::LifecycleReconciliationStore` (inventory L63); `src/triggertrade/persistence/lifecycle_order_event_store.py::LifecycleOrderEventStore` (inventory L38); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

R6 NR-153/154: actual `src/triggertrade/backtest/data.py`, `services/research.py`, `persistence/research_store.py` and `research_pins.py` for the existing isolated diagnostic input/archive and SQLite manifest capability. No new method/table is asserted to exist; additional records are explicitly scoped in §6.4.1.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW accepted-evidence/preflight helpers or raw challenge indexes only inside existing factual intake/owner infrastructure; no separate factual decision service.

**LEGACY_SURFACES_TO_FENCE:**

No paper/spot/demo factual fallback; native adapter profile remains uncertified until its separate evidence gate passes.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.facts. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row. Domain-specific native/financial certificates/incidents are integrated and persisted by B9/B10; B3 supplies factual preflight and acceptance interfaces without parallel ledgers.

NR-153/154 additionally extend existing ST.research with immutable diagnostic source objects/manifests/member references, retaining the actual SQLite role. Existing ST.facts remains owner-authoritative; Research imports committed evidence read-only. No future Position/native/financial domain state is pre-created.

**TRANSACTION_BOUNDARIES:**

TX.facts, TX.native, TX.grant, TX.preflight, TX.set; exact mechanism and tests in §7.

NR-153/154 diagnostic source archival/import uses independent ResearchStore SQLite transactions and ordered file-before-manifest publication (§7.7), not another canonical TX, business outbox or PostgreSQL/SQLite atomic operation.

**CONTRACTS_TOUCHED:**

PORTFOLIO_DATA_REQUEST v5; MARKET_DATA_REQUEST v3; ORDER_MANAGEMENT v4, each in both directions.

**IDENTITY_BINDINGS:**

selection_id; response_id / snapshot_id / page_id; cashflow_id / proven source aliases; Accepted coverage certificate key / accepted_certificate_revision

**NUMERIC_REQUIREMENTS:**

Exact factual decimal/raw sign preservation; no business rounding, implicit FX or zero substitution for unavailable facts.

**IMPLEMENTATION_SCOPE:**

Implement request/response binding for Portfolio↔API, Set↔API and Lifecycle↔API. Retain raw source/profile/field/accepted-at/effective identity. Add generic intake interface for owner-local known-evidence preflight and ordinary-batch atomic acceptance. Preserve TT-FINAL-001 binary item helper and validate full requested symbol coverage. Support exact historical selection/page and financial coverage recognition contracts; domain-specific canonical financial records are introduced in B10, not prematurely duplicated here.

R6 documentary extension: implement §6.4.1–6.4.3 raw source/coverage/provenance import, immutable cache-object and same-ResearchStore manifest publication before data can be overwritten/lost. Accept explicitly supplied provenance-complete datasets at the existing Research input boundary; keep the current downloader’s BTCUSDT/1m restriction explicit and unsupported acquisition unavailable. Preserve exact event data when supplied and OHLC resolution limits otherwise. No F-008/F-010 calculations, metric assembly, new venue endpoint, business producer or Research→API trading contract is introduced here.

**TESTS_REQUIRED:**

Existing gateway/fact/native-profile tests; all request and response modes, cardinality, page manifests, raw magnitude/direction truth table, source applicability, exact accepted anchor recovery and mixed malformed companion tests. Typed owner request fixtures prove the technical boundary, not integrated owner execution.

Existing regression examples (non-exhaustive): `tests/contract/test_market_data_gateway_contracts.py` (EXISTING), `tests/contract/test_native_profile_conformance.py` (EXISTING), `tests/contract/test_order_management_gateway_contracts.py` (EXISTING), `tests/contract/test_portfolio_data_gateway_contracts.py` (EXISTING), `tests/unit/test_market_data_fact_store.py` (EXISTING), `tests/unit/test_market_data_gateway.py` (EXISTING), `tests/unit/test_order_management_gateway.py` (EXISTING), `tests/unit/test_portfolio_data_gateway.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-004, AT-NR-019, AT-NR-021, AT-NR-022, AT-NR-023, AT-NR-024, AT-NR-025, AT-NR-026, AT-NR-027, AT-NR-028, AT-NR-029, AT-NR-031, AT-NR-032, AT-NR-143, AT-NR-145.

R6 source-archival portions of AT-NR-153/154 and §6.4.13: immutable object/manifest/capture identity, complete versus missing coverage, OHLC consistency, absent boundary subrecords, source conflicts, wrong product/symbol/profile, restricted downloader, valid explicitly supplied other-symbol dataset, before/after publication crash and same-source restart. ENTRY-RPT-14/15 and TP-RPT-08/10/17 start with this factual documentary capability; full metrics remain B12.

**NEGATIVE_BOUNDARY_TESTS:**

Direct Position/API edge; absent source/profile/field authority; guessed timestamps/currencies; source negative magnitude or inconsistent ZERO; known conflict suppressed by routing/stale/schema error; no or ambiguous accepted owner anchor.

**REPLAY_RESTART_TESTS:**

Accepted history/raw challenges retained across restart; same fact identity inert, changed historical core conflicts before suppression; preflight commit survives later ordinary rollback. Actual owner integrations complete in B5B/B8A/B9/B10.

Restore original diagnostic source objects/manifests and ingest keys from existing ResearchStore before re-importing; same source reused, changed known content conflicted, no manifest referencing incomplete bytes and no regenerated latest chart. RPT-POS/LIFE source producers remain later checkpoints.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; API_PROVENANCE_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW

**R6 local report-source scope:** Existing implementation, provenance, persistence, replay, contract and test reviews cover §10.5’s B3 documentary responsibilities. No additional review category or business authority.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2

**DOWNSTREAM_DEPENDENTS:**

B4, B8A, B5A, B6, B7A, B9, B12

**DEFINITION_OF_DONE:**

Technical factual endpoints/intake APIs and contracts pass independent provenance/transaction/replay/contract tests. No business production claim or native exposure permission arises from this checkpoint.

R6 diagnostic source archival/import and its local retention/provenance/crash tests pass as part of the existing Research path. Later owner-source capture and B12 report calculations are not certified by these typed-dataset tests.

**RISKS:**

Parse-first rejection can erase integrity evidence; a normalized number without raw source facts cannot substantiate finality.

**DO_NOT:**

Do not compute Set/Position/Portfolio decisions, invent provenance or native certification, forward Portfolio responses directly to Position, or let API create business grants/receipts.

## B4 — Contract structure and semantic binding layer

**PRIORITY:**

P1

**PURPOSE:**

Inventory and extend existing builders/validators for strict shapes and immutable cross-contract identity/scalar binding only.

**NORMATIVE_REQUIREMENTS:**

NR-001, NR-005, NR-013, NR-018

**HISTORICAL_TRACEABILITY_ALIASES:**

R006, R012, R013, R014, R017, R024, R025, R029, R054, R056

**EXISTING_FOUNDATION_REUSED:**

FN.CONTRACT, FN.GRANT, FN.CONSTRUCT, FN.SPEC, FN.AUTH, FN.SYNC, FN.PIN, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: existing structural/binding builders; owner production not completed by them [E26–E29,E35–E42]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Strict structural/semantic binding over existing builders, not generic business production.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.CONTRACT: Registry/generated schema/parser — src/triggertrade/contracts/registry.py; src/triggertrade/contracts/_approved_wire_schema.py; src/triggertrade/contracts/schema_validator.py; ADAPT under §2 classification.

FN.GRANT: CapitalGrantStore / grant builder — `src/triggertrade/persistence/capital_grant_store.py::CapitalGrantStore` (inventory L32); `src/triggertrade/capital_grants.py::build_capital_and_limits_grant` (inventory L15); EXTEND under §2 classification.

FN.CONSTRUCT: PositionConstructionStore — `src/triggertrade/persistence/position_construction_store.py::PositionConstructionStore` (inventory L36); src/triggertrade/position_construction.py; EXTEND under §2 classification.

FN.SPEC: OrderSpecStore — `src/triggertrade/persistence/order_spec_store.py::OrderSpecStore` (inventory L37); src/triggertrade/order_specs.py; EXTEND under §2 classification.

FN.AUTH: SubmitAuthorizationStore — `src/triggertrade/persistence/submit_authorization_store.py::SubmitAuthorizationStore` (inventory L35); src/triggertrade/submit_authorizations.py; EXTEND under §2 classification.

FN.SYNC: LifecycleSetSyncStore — `src/triggertrade/persistence/lifecycle_set_sync_store.py::LifecycleSetSyncStore` (inventory L46); src/triggertrade/lifecycle_set_sync.py; EXTEND under §2 classification.

FN.PIN: Position configuration-pin capability — `src/triggertrade/persistence/position_config_pin_store.py::PositionConfigPinStore` (inventory L32); src/triggertrade/position_config_pins.py; EXTEND under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW minimal wrapper only after a named existing builder lacks a required binding check. No all-family generic business producer package.

**LEGACY_SURFACES_TO_FENCE:**

Do not wrap legacy payloads into canonical success contracts.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

No business transaction introduced; later owners retain §7 atomicity.

**CONTRACTS_TOUCHED:**

All 12 structural/semantic binding surfaces; business production remains §4 owner checkpoints.

**IDENTITY_BINDINGS:**

Existing package/family/configuration/content bindings as applicable; no premature business IDs.

**NUMERIC_REQUIREMENTS:**

Compare exact canonical values under owning numeric policy; never recompute another owner’s formula to validate a binding.

**IMPLEMENTATION_SCOPE:**

Implement strict version/field/stage and exact identity/content/digest/scalar checks for all twelve families, preserving existing builders. Use build_capital_and_limits_grant and research_pin_payload; use actual PositionConfigPinStore capability. Map every business producer/consumer to §4 and its owning later checkpoint. Shared validation may validate supplied owner outcomes, never decide them.

**TESTS_REQUIRED:**

All existing contract/binding tests and independently invalid producer/consumer envelopes, initial vs construction stage semantics, no self-referential spec digest, exact duplicated scalar equality and missing mandatory branch content.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_order_specs_contracts.py` (EXISTING), `tests/contract/test_position_construction_contracts.py` (EXISTING), `tests/contract/test_submit_authorizations_contracts.py` (EXISTING), `tests/contract/test_target_contract_registry.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_order_spec_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-001, AT-NR-005, AT-NR-013, AT-NR-018.

**NEGATIVE_BOUNDARY_TESTS:**

Correct-looking digest with wrong H/Entry/Q/tranche, invalid stage with successful IDs, unknown root fields, wrong consumer, API response sent to Position, or caller-supplied result bypassing owner computation.

**REPLAY_RESTART_TESTS:**

Pure binding validation byte-stable; owner transactions later enforce durable semantic uniqueness. Same envelope cannot mean different stages on replay.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3

**DOWNSTREAM_DEPENDENTS:**

B8A, B5A, B6, B7A, B12

**DEFINITION_OF_DONE:**

Validation/binding responsibilities complete and independently reviewed; business production/consumption remains explicitly uncompleted until owner checkpoints. No duplicate serializer/state machine added.

**RISKS:**

Calling a builder a producer can mask missing owner logic; clean new helper packages can become parallel authority.

**DO_NOT:**

Do not mint decisions, grants, MATCHED, native operations, FINAL or Portfolio receipts in generic contract helpers.

## B8A — Portfolio scope, account state and economic-day foundation

**PRIORITY:**

P1

**PURPOSE:**

Establish governed upstream account/day/base/latch/capacity/cooldown and COINS production before actual Set formation.

**NORMATIVE_REQUIREMENTS:**

NR-021, NR-035, NR-036, NR-037, NR-038, NR-039, NR-040, NR-042, NR-043, NR-044, NR-050, NR-129, NR-151

**HISTORICAL_TRACEABILITY_ALIASES:**

R016, R017, R018, R019, R020, R026, R043, R045, R047, R048

**EXISTING_FOUNDATION_REUSED:**

FN.PORT, FN.SCOPE, FN.COOLDOWN, FN.CAS, FN.FACT, FN.MSG, FN.UOW, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: Portfolio state/scope infrastructure; canonical owner execution and day integration incomplete [E23,E47,E50–E51,E59]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

NR-151 additionally requires full gate/multi-reason and reconciliation observation history; current PortfolioStateStore's single reason/current pointer is not that history (§6.2.1).

**TARGET_STATE:**

Actual governed Portfolio scope/day/latch/capacity/cooldown state and COINS producer, with one fixed accounting-day base and separately tracked live Portfolio metrics; no premature grant.

Source-defined internal statuses, complete evaluated gate evidence and history-backed scope/day/capacity diagnostics are retained locally; no first-time history capture deferred to B12/B13.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.PORT: Portfolio state/buckets — `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py; EXTEND under §2 classification.

FN.SCOPE: CoinsScopeStore — `src/triggertrade/persistence/coins_scope_store.py::CoinsScopeStore` (inventory L48); EXTEND under §2 classification.

FN.COOLDOWN: Portfolio cooldown pins — `src/triggertrade/persistence/portfolio_cooldown_store.py::PortfolioCooldownStore` (inventory L33); src/triggertrade/portfolio_cooldown.py; EXTEND under §2 classification.

FN.CAS: OwnerStateStore — `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128); EXTEND under §2 classification.

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED Portfolio owner functions in src/triggertrade/portfolio_rules/handler.py and capital.py where canonical handlers are absent. CONDITIONAL_NEW canonical day/base/latch representation within existing PostgreSQL owner infrastructure, not SQLite.

**LEGACY_SURFACES_TO_FENCE:**

FN.LEGDAY remains isolated; no unsupported canonical equity/drawdown object.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.portfolio, ST.scope, ST.day, ST.cooldown, ST.config. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

NR-151 uses ST.portfolio history, existing ST.scope/ST.day/ST.cooldown/configuration/fact bindings and retained transport publications for P01–P04/P06–P13/P16/P20/P31–P33 as applicable. Add only missing immutable P-DECISION/P-RECON fields/events; no diagnostic state family or second state pointer/allocator.

**TRANSACTION_BOUNDARIES:**

TX.facts, TX.grant, TX.scope, TX.hold, TX.set, TX.acceptance, TX.closeretention, TX.day, TX.receipt, TX.final; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

COINS v2 production; PORTFOLIO_DATA_REQUEST v5 request/response. ORDER_EVENT FINAL fixtures test day logic only; actual receipt integrates B10.

**IDENTITY_BINDINGS:**

scope_revision; request_id; response_id / snapshot_id / page_id

**NUMERIC_REQUIREMENTS:**

Exact Portfolio capacity/base and A-009 threshold arithmetic; governed day timezone separate from Set UTC populations. The base is the single fixed NR-035 boundary wallet-own-capital value, excluding unrealized P&L and without re-adding realized cash already reflected in that value; live equity is not its denominator.

**IMPLEMENTATION_SCOPE:**

Consume factual Portfolio responses; recover governed account health and all commitments, opening-base evidence, ACCOUNTING_DAY_V1 boundary history and A-009 latch. Implement one governed fixed accounting-day base plus separate live Portfolio metrics, as required by NR-035.

At each Asia/Jerusalem accounting-day rollover, resolve the ACCOUNTING_DAY_V1 half-open interval `[local 00:00, next local 00:00)` and persist its accounting_day_id and boundary instants. Establish the new day’s base from the verified strategy-wallet own-capital value at the resolved boundary, excluding unrealized P&L. Realized P&L already reflected in wallet capital is included in that value and is never added a second time:

```text
daily_portfolio_base
=
strategy_wallet_capital_at_rollover_excluding_unrealized_pnl
```

When direct authoritative boundary evidence is unavailable, use only the frozen deterministic reconstruction based on complete authoritative cashflow history spanning that boundary. Retain the exact supporting evidence or reconstruction basis. If neither the boundary snapshot nor that complete governed reconstruction proves the value, persist `rollover_state = RECONCILING` and block new exposure. Do not substitute a later arbitrary snapshot, current equity, current unrealized P&L, the first observed account state after startup, an estimate, or the previous day’s base for the missing new-day value. The previous established base remains historical evidence, not permission to trade on an unproven new day.

Keep the established daily_portfolio_base immutable for its entire accounting day. The next rollover establishes a new day’s value without mutating the previous day’s base, boundaries or historical result/receipt/latch record. Retain the prior day for exactly-once late FINAL posting under the unchanged B10 receipt protocol.

Track and expose `current_portfolio_equity`, `daily_realized_pnl`, `unrealized_pnl` and `total_pnl` separately from the fixed base. Current equity is the authoritative API account-equity fact including unrealized P&L; current unrealized P&L is the authoritative floating-account fact. daily_realized_pnl remains A-009’s eligible immutable-FINAL logical net total for its bound accounting day, not a replacement cash-period metric. The frozen display/diagnostic relationship remains `total_pnl = daily_realized_pnl + unrealized_pnl`; `daily_portfolio_base + daily_realized_pnl + unrealized_pnl` is not an exchange-equity identity. Unrealized P&L is visible, stored and reflected in live equity/total P&L, but does not rebase percentage Portfolio Rules. Record external deposits/withdrawals immediately as live capital flows, not trading P&L; they do not change the current accounting day’s percentage denominator before the next rollover. There is no selectable daily-base policy, second live-equity denominator, intraday rebasing authority or future policy switch in this map.

Compute only Portfolio scope/capacity/cooldown gates and publish persistent COINS OPEN/CLOSE with config pins. Add day/rollover and latch reducer tests using immutable FINAL-shaped fixtures; actual producer/receipt integration waits for B10. Do not fabricate an initial Position decision or grant. A-009’s formula, disabled-first ordering, retained latch, unavailable branch, inclusive comparison and current/historical receipt semantics are unchanged. A disabled Daily Loss gate does not waive the independent rollover/recovery block on an unproven day.

Frozen basis for this base prerequisite: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` §§3–4 (L130–L247), Appendix B (L1847–L1883), and §23 (L776–L874); `docs/trading-methodology/SYSTEM_PROTOCOLS.md` P8 (L193–L220).

Implement NR-151's complete gate-result/status/all-evaluated-reason capture for actual scope/day/configuration/capacity evaluations, and original Portfolio reconciliation episode/failure history. Preserve the original evaluated rules/facts/caps and exact state revision for historical utilization. This records the existing gates; it neither changes their ordering/status branches nor selects a new base or allocation rule.

**TESTS_REQUIRED:**

Current account health, one governed fixed accounting-day base, separate live Portfolio metrics and all AT-NR-035 boundary/reconstruction/immutability cases below; four bucket/slot recovery, COINS revision transaction and A-009 ordered branch fixtures (disabled, retained latch, missing data, exact threshold, OK). Preserve scope/state/cooldown regressions. Also run AT-NR-036's configuration and pure current-capacity cases below. These B8A fixtures do not book H, reserve slots or issue grants; actual non-reserving grant and H-booking integration remain B8B and B8C respectively.

**AT-NR-035 — source-derived fixed-base acceptance matrix (all fourteen cases required):**

In the source column, `PORTFOLIO_RULES` means `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`; `P8` means `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, **P8 — Economic time, operational time and accounting day**. These are subcases of the existing AT-NR-035, not new normalized requirements. Expected values and outcomes must be derived independently from the frozen clauses and authoritative fixture evidence, never captured from the implementation under test. B8A tests the day/recovery/latch behavior locally; cases involving FINAL receipt use immutable fixtures here and the unchanged actual B10 producer/consumer and transaction tests for integrated closure.

| AT-NR-035 case | Scenario | Required source-derived expectation | Frozen source |
| --- | --- | --- | --- |
| 01 | Verified exact-boundary wallet snapshot | A verified strategy-wallet own-capital snapshot at the resolved boundary establishes exactly that day’s daily_portfolio_base and persists its accounting_day_id, boundary instants and evidence binding. | PORTFOLIO_RULES §§3–4 L130–L180; Appendix B L1847–L1855; P8 L197 |
| 02 | Unrealized P&L excluded | Keep the boundary own-capital amount as the base even when exposure has nonzero unrealized P&L. The floating amount is stored separately and contributes neither to the new base nor an alternative denominator. | PORTFOLIO_RULES §4 L170–L194; Appendix B L1855 |
| 03 | Realized cash already in wallet | Use wallet capital once. In the frozen example, prior base 1,000 with realized cash +80 already reflected in the next boundary wallet establishes 1,080, not 1,160; do not add an arriving logical result again. | PORTFOLIO_RULES §4 L182–L192; Appendix B L1883; P8 L218–L220 |
| 04 | Intraday live equity and external capital flows | Change authoritative current equity and record deposits/withdrawals in live Portfolio state; the established daily base and percentage denominator remain unchanged throughout that day. External capital flows are not trading P&L. | PORTFOLIO_RULES §4 L196–L247 |
| 05 | Intraday unrealized P&L changes | Vary current floating P&L, including its sign, and update its separate live value and applicable display/diagnostic metrics. The daily base and percentage denominator remain exactly the persisted values. | PORTFOLIO_RULES §4 L196–L243 |
| 06 | Forbidden substitutes for missing boundary proof | A later arbitrary wallet/equity snapshot, current unrealized P&L, first post-startup observation, estimate or previous day’s base cannot establish the missing new-day value. Without a verified boundary snapshot or the complete governed reconstruction, remain RECONCILING and block new exposure. | PORTFOLIO_RULES Appendix B L1849–L1865; P8 L220 |
| 07 | Complete deterministic boundary reconstruction | When the direct boundary snapshot is unavailable but complete authoritative cashflow history spanning the boundary proves the own-capital value, the frozen deterministic reconstruction may establish that exact base. Retain its complete basis; do not introduce another reconstruction policy. | PORTFOLIO_RULES Appendix B L1855; §23 L846–L849; P8 L220 |
| 08 | Incomplete reconstruction or unavailable boundary value | Missing material history or an otherwise unproven boundary value leaves rollover_state=RECONCILING and new exposure blocked. A previous historical base remains immutable but cannot be reused as the new-day base; a disabled Daily Loss switch does not waive this independent recovery gate. | PORTFOLIO_RULES Appendix B L1857–L1865; §23 L858–L860; P8 L220 |
| 09 | Next rollover preserves the previous day | Establish the next day’s distinct base from its own proven boundary value. Preserve the previous accounting_day_id, boundaries, base, historical result/receipt records and latch history; only the new day follows the existing rollover reset rules. | PORTFOLIO_RULES §3 L141–L154; Appendix B L1849–L1863; P8 L216–L220 |
| 10 | Late historical first FINAL | Post an eligible immutable FINAL once under result_id and tranche_id to its bound historical day. Change only that day’s logical realized total as governed; neither historical/current established base, today’s sum/latch nor API-authoritative wallet capital is rewritten or credited again. | PORTFOLIO_RULES §23 L787–L789; P8 L216–L220 |
| 11 | Separate authoritative live equity | Retain and expose current_portfolio_equity from the authoritative API account-equity field, including unrealized P&L. Do not derive it from base plus logical realized plus unrealized, and never use it as a substitute daily-base operand. | PORTFOLIO_RULES §4 L196–L229; Appendix B L1873–L1883 |
| 12 | Separate authoritative current unrealized P&L | Retain and expose the current floating-account fact independently of the base and A-009’s immutable-FINAL total. Preserve total_pnl = daily_realized_pnl + unrealized_pnl for display/diagnostics only; unrealized is not an A-009 summand. | PORTFOLIO_RULES §4 L198–L243; Appendix B L1867–L1883; §23 L850–L856 |
| 13 | Accounting-day restart | Hydrate the same persisted accounting_day_id, boundary instants, fixed base, base-evidence/reconstruction binding, receipt/day/latch and historical late-posting state before new results. Restart or a fresh account snapshot cannot re-establish an already fixed base. | PORTFOLIO_RULES Appendix B L1849–L1883; P8 L197, L216–L220 |
| 14 | DST and exact local midnight | Resolve the half-open Asia/Jerusalem civil-midnight boundaries required by ACCOUNTING_DAY_V1, persist the actual instants and restore them unchanged. An instant at the next boundary belongs to the next day; do not impose a fixed 24-hour UTC interval or substitute receipt time. | PORTFOLIO_RULES Appendix B L1849–L1855; P8 L195–L220 |

**AT-NR-036 — source-derived allocation-sum and runtime-capacity acceptance matrix (all four cases required):**

These are subcases of the existing AT-NR-036. `PORTFOLIO_RULES` means `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`. The frozen example configures `max_capital_in_positions_pct = 60` and enabled SOL, ETH, DOGE and BTC at `allocation_pct = 20` each. The summed targets are 80%; the configuration is valid. Preserve those percentages exactly; no rescaling, normalization or configuration-level sum ceiling is allowed.

For explicit exact-money fixtures, a proven fixed daily_portfolio_base of 1,000 governed accounting units gives a global_position_cap of 600 and a coin_allocation_cap of 200 for each coin under the unchanged §6/§7 equations. This is a test input, not a change to any production configuration, threshold, daily-base rule or unit/FX policy. Committed amounts include all four mutually exclusive capital buckets. The booking cases use an independently valid previously issued immutable grant and successfully constructed result with `C = H = 20`, exact spec/scalar/digest binding and a still-unconsumed grant. They isolate the specified current capacity gate; all other required state/day/latch/cooldown/scope/slot/frontier and construction checks pass. Because the earlier grant did not reserve capital, other legitimate commitments may change current capacity before B8C; the fixture must prove valid grant issuance at its own original time rather than mint a grant in the already failing state.

`CONFIGURATION_VALID`, `BOOKING_REJECTED` and `BOOKING_ALLOWED` below name test expectations, not new wire enums or business outcomes.

| AT-NR-036 case | Scenario | Required source-derived expectation | Frozen source / stage |
| --- | --- | --- | --- |
| 01 — valid target sum above global cap | Global cap percentage 60%; SOL/ETH/DOGE/BTC each 20%; summed targets 80%. Provide otherwise valid Portfolio configuration. At the fixture base the target caps sum to 800 while the global cap is 600. | CONFIGURATION_VALID. Retain all four 20% allocations and the independent 60% global cap; do not normalize them or reject configuration merely because 80% > 60%. This is not permission to commit all 80% simultaneously. | PORTFOLIO_RULES §§5–8 L251–L358; B8A configuration validation, preserved through B8B/B8C |
| 02 — runtime global cap excess | Same valid configuration. Current aggregate committed capital 590 and current SOL committed capital 150; an otherwise valid SOL construction requires H=20. Proposed totals are 610 globally and 170 for SOL. | BOOKING_REJECTED by the existing current global capacity gate: 610 > 600 (equivalently free global 10 < the fixture's C=H=20). Configuration remains valid and the coin cap is not the failing gate. No H/slot/authorization/outbox success is committed; do not shrink the tranche, resize the spec or normalize configured targets. | PORTFOLIO_RULES §§14–15 L541–L570, §19 L700–L717 and §41.1 L1361–L1363; B8A capacity fixture, actual B8C hold transaction |
| 03 — runtime per-coin cap excess | Same valid configuration. Current aggregate committed capital 500 and SOL committed capital 190; the otherwise valid H=20 SOL construction would give 520 globally and 210 for SOL. | BOOKING_REJECTED by the existing current per-coin capacity check: 210 > 200 even though 520 <= 600. A previous non-reserving grant does not waive this current check. No H/slot/authorization/outbox success is committed; neither cap nor trade is repaired. | PORTFOLIO_RULES §7 L305–L329, §§14–15 L541–L570, §22 L759–L771 and §41.1 L1361–L1363; B8A capacity fixture, actual B8C hold transaction |
| 04 — exact allowed global boundary | Same valid configuration. Current aggregate committed capital 580 and SOL committed capital 150; H=20 gives exactly 600 globally and 170 for SOL. All other gate prerequisites, including a remaining global and coin slot, pass. | BOOKING_ALLOWED under the existing inclusive capacity semantics: free global capital equals C=H=20, so equality does not fail the global gate. B8C books the unchanged exact H and one slot with authorization/outbox once in its existing transaction. The cap permits equality, not any excess; another gate failure would still reject. | PORTFOLIO_RULES §19 L700–L717, §§20–22 L721–L771 and §41.1 L1361–L1363; B8A capacity fixture, actual B8C hold transaction |

Retain AT-NR-036's existing unknown-coin configuration rejection and immutable attempt-history tests. Newly selected/current configuration checks cannot rewrite an already pinned grant or authorized attempt. B8B must accept case 01's valid configuration, derive grants only by its unchanged current gates/floor/slot rules and prove that issuing them reserves neither capital nor slots. B8C must execute cases 02–04 through the actual current H-booking transaction with the same valid configured target sum, including rollback/duplicate checks already required there. V04/V17 and B13 carry this configuration-versus-runtime distinction into integrated verification. No configuration-sum ceiling, automatic percentage normalization, grant-size override or new Portfolio mechanism is added.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_coins_scope_contracts.py` (EXISTING), `tests/contract/test_portfolio_state_contracts.py` (EXISTING), `tests/contract/test_submit_authorizations_contracts.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_coins_scope.py` (EXISTING), `tests/unit/test_coins_scope_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-021, AT-NR-035, AT-NR-036, AT-NR-037, AT-NR-038, AT-NR-039, AT-NR-040, AT-NR-042, AT-NR-043, AT-NR-044, AT-NR-050, AT-NR-129, AT-NR-151.

AT-NR-151 foundational portions (§6.2.4) verify all fields/reasons, scope transition versus resend, unavailable versus blocked, cooldown/day/capacity observation bases, complete reconciliation episodes and historical utilization. Actual grant/hold/native-return/receipt observations remain assigned to B8B/B8C/B9/B10; B8A fixtures cannot close those integrations.

**NEGATIVE_BOUNDARY_TESTS:**

Later arbitrary snapshot, current equity/unrealized P&L, first post-startup account observation, estimate or prior-day base as the missing new-day opening base; realized cash double-added; floating P&L or external capital flows changing the established denominator; missing recovery mistaken for empty day, stale state as free capital, current config replacing old day/attempt pin, scope revision conflict and any grant before initial APPROVE.

**REPLAY_RESTART_TESTS:**

Day/base/latch/config/scope revisions restore before new events, including the same accounting_day_id, resolved boundary instants and immutable base with its exact evidence/reconstruction basis. New account observations cannot rebase a restored day. Duplicate COINS has no extra epoch; rollover never discards unresolved commitments or historical latch.

Hydrate P-DECISION/P-STATE/P-RECON histories and original gate reason collections. Duplicates do not create another scope transition, count or episode; newer current state cannot erase an old denial.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW; ACCOUNTING_FINALITY_REVIEW

**Local ACCOUNTING_FINALITY_REVIEW scope:** Review B8A's ACCOUNTING_DAY_V1 foundation: Asia/Jerusalem civil-midnight boundaries and persisted actual instants; authoritative boundary evidence or complete deterministic reconstruction; RECONCILING fail-closed behavior while the new-day base is unproven; one immutable daily_portfolio_base; preservation of historical days; restart/hydration of the same day/base/evidence; day/base/latch state and A-009 prerequisites; no intraday rebase; late historical FINAL isolation and no wallet double-credit. This is the local day/base foundation review, using B8A's existing fixture and recovery scope. Actual FINAL receipt implementation remains in B10; A-002 and S-004 remain Lifecycle-owned. No financial-finality behavior or receipt authority moves into B8A.

**NR-151 local review responsibilities:** Existing IMPLEMENTATION_REVIEW and TEST_REVIEW cover P01–P04 and all applicable source §63 rows; PERSISTENCE_TRANSACTION_REVIEW and REPLAY_IDEMPOTENCY_REVIEW prove atomic status/reasons/history and dedupe/recovery; NUMERIC_PRECISION_REVIEW covers exact historical caps/buckets/utilization; ADVERSARIAL_TRADING_REVIEW covers capacity/cooldown/day denial visibility. Existing ACCOUNTING_FINALITY_REVIEW covers original day/base/latch and Portfolio reconciliation history, without moving B10 receipt/finality into B8A.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3, B4

**DOWNSTREAM_DEPENDENTS:**

B5B, B8B, B8C, B10, B12

**DEFINITION_OF_DONE:**

Actual Portfolio scope producer and recoverable upstream state pass local gates; Set can consume governed scope. Grants/holds and actual FINAL receipt integration are not declared complete here.

NR-151's B8A producers and history-based views pass their local source-derived observation tests and existing reviews; later producers remain explicitly incomplete.

**RISKS:**

Early A-009 fixtures can be mistaken for a fully integrated financial feed; scope CLOSE must not stop an existing pending monitor.

**DO_NOT:**

Do not issue CAPITAL_AND_LIMITS before B7A APPROVE, reserve capital, compute Position formulas, use UTC legacy day logic, or create A-005/A-006 objects.

## B5A — Set numeric dependencies and indicator state

**PRIORITY:**

P1

**PURPOSE:**

Implement all certified Set kernels and complete factual populations/series dependencies before wiring durable MATCHED production. Preserve applicability by frozen Set configuration: the F-005 kernel is required for governed Sets, not a universal direction prerequisite for generic deterministic Sets.

**NORMATIVE_REQUIREMENTS:**

NR-009, NR-010, NR-053, NR-054, NR-055, NR-056, NR-059, NR-060, NR-061, NR-062, NR-063, NR-064, NR-065, NR-066, NR-067, NR-068, NR-069, NR-150

**HISTORICAL_TRACEABILITY_ALIASES:**

R015, R028, R033, R034, R035, R036, R037, R060

**EXISTING_FOUNDATION_REUSED:**

FN.FACT, FN.EPOCH, FN.CAS, FN.UOW, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

MISSING canonical kernels; factual/scope infrastructure reusable [E23,E34,E58–E59; audit §9]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Complete exact Set kernels/populations and separate indicator state interfaces, no MATCHED publication yet. Configuration validation preserves both NR-053 direction scopes for the same later B5B handler.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.EPOCH: SetFormationEpoch / SetConfigurationBinding — `src/triggertrade/set_scope.py::SetFormationEpoch` (inventory L88); `src/triggertrade/set_scope.py::SetConfigurationBinding` (inventory L17); EXTEND under §2 classification.

FN.CAS: OwnerStateStore — `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/set_engine/formulas.py and package initializer. CONDITIONAL_NEW Set-owned checkpoint/population records only where existing owner/fact storage cannot represent the required history.

**LEGACY_SURFACES_TO_FENCE:**

Legacy percentage/volume triggers, demo strategy/regime and demo precision remain fenced.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.setcalc, ST.atr15, ST.local5. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

**TRANSACTION_BOUNDARIES:**

TX.setcalc, TX.set; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

MARKET_DATA_REQUEST v3 accepted inputs and MARKET_HANDOFF v4 numeric export interfaces; no actual handoff producer until B5B.

**IDENTITY_BINDINGS:**

Existing package/family/configuration/content bindings as applicable; no premature business IDs.

**NUMERIC_REQUIREMENTS:**

TT_SET_NUMERIC_V1 Q36 exact named quantization, exact variance/midpoint sqrt, Q18 only at allowed export; no hidden ratio rounding or wire-based working reconstruction.

**IMPLEMENTATION_SCOPE:**

Implement F-001/F-002 current-state kernels with their own populations; F-003 15m TR/Wilder ATR/PCT including source/seed/candle/zero-close rules; F-004 full populations, ordinary UTC calendar, exact normalization/stddev, separate local5m state, required factors/weights and side-specific vetoes; F-005 classifier. Persist/checkpoint only Set-owned analytical state with exact ancestry where introduced. No concrete MATCHED cycle or MARKET_HANDOFF is produced until B5B. Apply these kernels according to the immutable frozen Set definition. F-005 remains the sole final resolver inside its governed scope, with unchanged inputs/arithmetic/thresholds/vetoes; outside it, preserve the existing generic fixed-direction or explicit matched-branch configuration semantics and declared deterministic conflict requirements in NR-053/§5.2. Do not require a generic Set to execute F-005 or supply classifier-only inputs. This applicability check is within the same Set configuration/kernel boundary; B5B performs durable scope dispatch, not a second direction owner or service.

Keep `formation_trigger_evidence` (F-001/F-002 only where configured) distinct from `classifier_evidence` (F-003 work context, F-004's own factor/population/local-5m inputs and F-005 classifier). These are internal evidence concepts, not wire fields. Classifier evaluation never takes F-001 result/move_pct_work/sign or F-002 result/base-volume/population/availability as a prerequisite. A separately prescribed shared underlying factual metric must use F-004's own accepted source/population semantics. Kernels expose independently evaluable results; the final formation/classifier/handoff join is B5B only (§5.2).

**TESTS_REQUIRED:**

Independent golden and boundary vectors for all five objects, complete population membership, CURRENT_STATE/FRESH_EVENT dependency distinctions, confirmed bars/swings, zero/missing denominators, ATR full replay vs checkpoint and local5m independence. Persisted checkpoint round trips and source conflict tests are local. Add the pure configuration/kernel portions of AT-NR-053 A–H: governed F-005 outcomes and bypass rejection, valid generic fixed/branch definitions without classifier invocation, declared/unresolved conflicts, cross-owner rejection and deterministic configuration round trips. Generic positives must still satisfy their own required inputs. Actual epoch/result/handoff and crash atomicity remain B5B tests.

Existing regression examples (non-exhaustive): `tests/contract/test_canonical_json_contract.py` (EXISTING), `tests/contract/test_coins_scope_contracts.py` (EXISTING), `tests/unit/test_canonical_json.py` (EXISTING), `tests/unit/test_coins_scope.py` (EXISTING), `tests/unit/test_coins_scope_store.py` (EXISTING), `tests/unit/test_market_data_fact_store.py` (EXISTING), `tests/unit/test_set_scope.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-009, AT-NR-010, AT-NR-053, AT-NR-054, AT-NR-055, AT-NR-056, AT-NR-059, AT-NR-060, AT-NR-061, AT-NR-062, AT-NR-063, AT-NR-064, AT-NR-065, AT-NR-066, AT-NR-067, AT-NR-068, AT-NR-069, AT-NR-150.

AT-NR-068-CF A–D (§5.3) is mandatory at the real kernel/configuration boundary: full source-derived classifier inputs fixed across trigger-unavailable/false/population contrasts, plus a genuine local-5m classifier-veto change with formation fixed. Assert actual work/score/veto/direction evidence; no constant/stubbed classifier. B5B separately proves the final unmatched/matched transaction consequences.

**NEGATIVE_BOUNDARY_TESTS:**

Malformed required candle, valid zero-close with advancing ATR but unavailable PCT, arbitrary fetched-window seed, missing full days, current incomplete bar, F-001 mistaken for normalized momentum, Q18 feedback into work score, diagnostic data repairing required gate. Reject universal F-005 enforcement on a valid non-F-005 generic definition, generic fallback from missing/invalid governed configuration, and fixed/branch labels overriding an in-scope F-005 outcome.

Reject an F-001/F-002 result, sign/work value, trigger-local volume population or availability check wired into F-004. A correct final NONE is insufficient if the implementation wrongly skipped or modified an independently evaluable classifier.

**REPLAY_RESTART_TESTS:**

Same accepted series produces identical work state across restart; duplicate candle does not advance twice; changed accepted source invalidates current derivations, not a frozen historical handoff. Persist original seed ancestry. Pure configuration replay also retains the original direction-resolution scope, fixed/branch rule and declared conflict rule; round-trip loading cannot reinterpret scope. B5B proves the corresponding durable epoch/result binding.

Round-trip the separate original classifier and formation evidence bindings. AT-NR-068-CF must remain reproducible without re-reading latest populations, confusing fixture worlds or ignoring a real shared-source contradiction.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW

**Local FA-R4-01 review scope:** The existing implementation, numeric, trading, contract, persistence, replay and test reviews explicitly inspect the separated operand graph and AT-NR-068-CF A–D. No reviewer token, owner, schema or MATCHED producer is added.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3, B4

**DOWNSTREAM_DEPENDENTS:**

B5B, B12

**DEFINITION_OF_DONE:**

Kernels, required population/state interfaces and every exact boundary have local independent numeric/trading/persistence/replay/contract/test review. B5B remains responsible for actual scope/event handler and MATCHED atomicity. NR-053 applicability/configuration tests prove that supporting F-005-governed Sets has not made F-005 mandatory outside its scope.

The kernel separation and all A–D evidence discriminators pass locally. No F-001/F-002-to-F-004 numerical/availability edge remains; no MATCHED is produced here.

**RISKS:**

A five-formula checklist can miss ordinary populations, separate indicator series and work/export precision; legacy code can appear numerically similar but have different semantics.

**DO_NOT:**

Do not tune thresholds/weights, infer missing population members, share 5m state with canonical15m ATR, promote S-005, or create a parallel Set state machine.

## B5B — Set durable handler, MATCHED and handoff

**PRIORITY:**

P1

**PURPOSE:**

Integrate the tested Set kernels with existing COINS scope/epochs, factual assembly and one atomic final-result producer.

**NORMATIVE_REQUIREMENTS:**

NR-022, NR-023, NR-027, NR-029, NR-039, NR-053, NR-056, NR-057, NR-058, NR-069, NR-070, NR-071, NR-072, NR-073, NR-074, NR-075, NR-135, NR-145, NR-149, NR-054, NR-055, NR-068

**HISTORICAL_TRACEABILITY_ALIASES:**

R006, R013, R014, R016, R026, R027, R028, R031, R033, R034, R035, R036, R037, R043, R044, R047, R048, R051

**EXISTING_FOUNDATION_REUSED:**

FN.SCOPE, FN.EPOCH, FN.FACT, FN.CAS, FN.MSG, FN.UOW, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

MISSING canonical evaluation handler; scope/epochs already exist [E23,E34,E58–E59]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Single Set handler atomically creates MATCHED/refs/frozen record/handoff and event consumption over existing epochs.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.SCOPE: CoinsScopeStore — `src/triggertrade/persistence/coins_scope_store.py::CoinsScopeStore` (inventory L48); EXTEND under §2 classification.

FN.EPOCH: SetFormationEpoch / SetConfigurationBinding — `src/triggertrade/set_scope.py::SetFormationEpoch` (inventory L88); `src/triggertrade/set_scope.py::SetConfigurationBinding` (inventory L17); EXTEND under §2 classification.

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.CAS: OwnerStateStore — `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128); EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/set_engine/handler.py. CONDITIONAL_NEW Set result/event/frozen-record storage only for justified missing logical records, preferably extending existing owner-state/epoch infrastructure.

**LEGACY_SURFACES_TO_FENCE:**

Legacy TriggerSetStore/config/demo trigger paths are not the canonical formation-state replacement.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.scope, ST.facts, ST.setcalc, ST.atr15, ST.local5, ST.setevents, ST.references, ST.setresults, ST.frozen, ST.config. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

**TRANSACTION_BOUNDARIES:**

TX.facts, TX.preflight, TX.scope, TX.set, TX.setcalc, TX.monitor, TX.owner, TX.opportunity, TX.hold; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

COINS v2 consumption; MARKET_DATA_REQUEST v3 request/response; MARKET_HANDOFF v4 production.

**IDENTITY_BINDINGS:**

formation_epoch; selection_id; request_id; response_id / snapshot_id / page_id; Trigger evaluation / transition-event identity; trigger_occurrence_id / core_set_constituent_id / role_id / binding_id / level_id; decision_cycle_id; set_result_id; condition_record_id / frozen_condition_record_id; condition_id; evidence_digest

**NUMERIC_REQUIREMENTS:**

Consume B5A work values; serialize only allowed Q18 fields, retain factual reference prices/tick unchanged and canonical integer freshness under frozen policy.

**IMPLEMENTATION_SCOPE:**

Consume actual COINS and exact factual pages, track current analytical eligibility and trigger/event continuity/consumption per pinned epoch. Preserve authoritative original deadlines and rearm semantics. Resolve direction inside this same handler from the Set/Trigger/Core Set configuration immutably bound to the current formation epoch. For an F-005-governed Set, use the unchanged F-005 classifier and final-resolution path; no fixed or matched-branch label may bypass, override or reverse its outcome. Required in-scope Core Set arbitration must be declared, deterministic, Set-owned and consistent with F-005; missing/conflicting arbitration is ineligible. Outside F-005-governed scope, use the existing generic definition's configured fixed direction or its explicit matched-branch direction without requiring F-005. If eligible generic branches can produce LONG and SHORT at the same canonical timestamp, apply only a valid deterministic conflict rule already declared in that bound definition; absent or unresolved conflict resolution makes the configuration/outcome invalid or ineligible and prevents a handoff. No first-arrival, lexical, strongest-score, latest-result or human-readable Set-name inference is permitted. An unavailable/invalid F-005 result or unknown configuration scope cannot trigger generic fallback. All routes remain Set-owned and retain the same frozen formation, source/reference, handoff validation and atomicity requirements.

Resolve producer-owned thesis references, then atomically persist final MATCHED/cycle/result, frozen condition record, handoff and required outbox with consumption. A NONE/unavailable result follows frozen behavior and never counterfeits a directional handoff.

Consume the two independently bound B5A evidence branches (§5.2). Evaluate the immutable configured Trigger/Core Set expression, including F-001/F-002 only where configured, with its original epoch/events and Boolean/sequence/N-of-M requirements. In governed scope, combine an independently valid F-005 classifier criterion with independently TRUE/eligible formation and all source/reference/handoff gates; `classifier criterion != formation eligibility`. Retain classifier evidence even when formation fails. Formation or mandatory handoff-validation failure produces the frozen unmatched/final-NONE outcome and distinct reason, with no committed success IDs/frozen-success/handoff/outbox. Only the complete eligible join enters the existing one TX.set. The already specified generic fixed/matched-branch/conflict-rule route and AT-NR-053 A–H are unchanged.

**TESTS_REQUIRED:**

Real scope→API facts→kernels→MATCHED→Position handoff with current source assembly; all event grouping/window/interruption fixtures; required/optional references and exact handoff contract. Fault-inject each record/outbox step in PostgreSQL. Exercise both NR-053 direction scopes and all cases A–H below through the actual same Set handler. F-005 is invoked for the governed path and is not invoked as a direction prerequisite on valid generic fixed/branch paths.

**AT-NR-053 — source-derived direction-scope acceptance matrix (A–H):**

These are subcases of the existing AT-NR-053, not new normalized requirements or certified objects. `SET` below means `docs/trading-methodology/methodology/SET.md`; `P17` means `docs/trading-methodology/SYSTEM_PROTOCOLS.md` P17. Each positive fixture includes a complete valid immutable Set/Trigger/Core Set definition, its original formation epoch, required source/evaluation evidence and all otherwise-required handoff fields/validations. A direction result alone does not waive any other gate. Expectations come from the frozen definition and retained fixture evidence, not from the implementation's output.

For governed positives, reuse the independently source-derived full F-004/F-005 vectors required by AT-NR-068: all eleven inputs and their diagnostics valid, hard gates passing and no veto against the selected candidate, with exact score at/above +0.35 for LONG or at/below -0.35 for SHORT. The actual kernels must produce the expected direction; a prefilled classifier result is not evidence. Generic positives instead use a valid definition explicitly outside that governing scope; omit classifier-only dependencies and trap any spurious F-005 invocation, while providing every input that the generic definition and the common handoff actually require.

| AT-NR-053 case | Source-derived fixture / action | Required expectation | Frozen source |
| --- | --- | --- | --- |
| A — governed positive | Valid F-005-governed LONG and SHORT fixtures with complete valid F-004 inputs and all other eligibility satisfied. Also exercise a conflicting fixed/branch direction label as an attempted override, without changing the authoritative classifier evidence. | PASS / valid Set-owned direction equal to F-005's final resolution. A conflicting label cannot change the result or select the opposite side. Only the otherwise eligible outcome enters the existing MATCHED/handoff transaction. | SET §5 L509–L530; Part II §§33–35 L3094–L3226, especially §34A L3155–L3197 |
| B — generic fixed positive | Valid generic definition outside F-005 scope explicitly fixes LONG; mirror with SHORT. All its own predicates and mandatory handoff requirements pass; classifier-only data is absent and F-005 invocation is trapped. | The configured fixed direction is accepted within Set; F-005 is not required or invoked to resolve it. Persist the original configuration and the same canonical result/handoff lineage. | SET §5 L517–L528; P17 L359–L365 |
| C — generic matched-branch positive | Valid generic definition outside F-005 scope explicitly binds the satisfied branch to LONG; mirror with SHORT. One deterministic branch is eligible at the canonical timestamp, with exact retained branch/constituent evidence. | Direction equals that branch's declared direction without an F-005 prerequisite. Retain the exact matched branch, evidence and immutable configuration binding; no latest-branch lookup. | SET §5 L517–L530; P17 L359–L365 |
| D — generic unresolved conflict negative | Two eligible generic branches can resolve LONG and SHORT at the same canonical timestamp, with no declared deterministic conflict rule. Vary delivery order, labels and lexical order. | Invalid/ineligible configuration or Set outcome; no arbitrary winner, successful MATCHED or handoff. Reordering cannot cure the missing rule. | SET §5 L526–L530 |
| E — governed bypass negative | Under an F-005-governed definition, attempt to substitute an opposing fixed or matched-branch direction for the computed F-005 result. Also try a directional label when F-005 is NONE/unavailable or its required evidence is missing. | Reject the bypass, not F-005's authority: the valid governed result remains authoritative, and NONE/unavailable cannot become a directional match. No generic fallback, opposite-side handoff or cross-owner override. | SET §5 L524–L526; Part II §34A L3155–L3197; §35 L3201–L3226 |
| F — generic declared conflict positive | Use a complete source-permitted generic definition whose deterministic conflict rule is explicitly declared in the pinned configuration and yields one independently specified expected direction for the fixture's simultaneous opposite branches. Retain the rule's full content and exact branch/evidence inputs; vary delivery order. | Apply that declared rule only; final direction equals its unique source/configuration-derived expectation in every ordering. A missing, contradictory or unresolved rule returns to case D; the backend must not invent a priority, lexical, arrival or strongest-score resolver. | SET §5 L526–L530; P17 L359–L365 |
| G — cross-owner negatives | On both valid scopes, attempt to supply/set/override direction from API, Portfolio, Position (including reversal), Research/S-005, or a human-readable name. | No attempted route gains direction authority or changes the accepted Set result. Factual API data may affect the Set's own governed evaluation but is not a direction decision; other owners only consume the permitted result. | SET §5 L511–L528; SYSTEM_PROTOCOLS P1 L6–L45 and Research isolation L887–L897 |
| H — scope/branch replay integrity | Start each scope under configuration v1, then activate a different configuration while replaying/restarting that original epoch or MATCHED cycle. Try both scope switches, a different branch/direction under the same bound identity, changed configuration content under the same ID/version, and retries before/after the Set commit. | Hydrate and reuse the original configuration/scope/branch/direction and existing IDs/bytes. No generic↔F-005 reinterpretation, latest-data branch resolution, reminted cycle/result or rewritten handoff. Same-ID changed binding is an integrity conflict. Precommit failure leaves no partial success; postcommit retry republishes the original result/handoff. | SET §5 L524–L530; §34A L3193–L3197; P17 L359–L365; existing NR-074/NR-135 atomicity |

B5A performs the applicable pure validation/kernel/configuration tests. B5B must perform all A–H cases with its actual owner-local scope dispatch, configured branch evidence and PostgreSQL transaction/replay boundaries; pure or mocked direction results cannot replace these tests. V03/V04/V15/V17 and B13 repeat the relevant assertions through the existing integrated dispatcher. No new wire fields, direction runtime, persistence ledger, owner or native permission is introduced.

Existing regression examples (non-exhaustive): `tests/contract/test_canonical_json_contract.py` (EXISTING), `tests/contract/test_coins_scope_contracts.py` (EXISTING), `tests/unit/test_canonical_json.py` (EXISTING), `tests/unit/test_coins_scope.py` (EXISTING), `tests/unit/test_coins_scope_store.py` (EXISTING), `tests/unit/test_market_data_fact_store.py` (EXISTING), `tests/unit/test_set_scope.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-022, AT-NR-023, AT-NR-027, AT-NR-029, AT-NR-039, AT-NR-053, AT-NR-056, AT-NR-057, AT-NR-058, AT-NR-069, AT-NR-070, AT-NR-071, AT-NR-072, AT-NR-073, AT-NR-074, AT-NR-075, AT-NR-135, AT-NR-145, AT-NR-149, AT-NR-054, AT-NR-055, AT-NR-068.

Execute all AT-NR-068-CF A–D through the actual same Set handler and PostgreSQL boundary, not prefilled direction outputs. Verify unchanged computed classifier for A–C, genuine source-derived veto behavior for D, exact branch-specific failure reasons, no failed-match success IDs/publication, and original successful match/frozen record/outbox atomicity. These tests supplement, never replace, AT-NR-053 A–H.

**NEGATIVE_BOUNDARY_TESTS:**

CLOSE/reopen old events, cold-start TRUE treated as fresh transition, contradictory complete page manifests, unresolved producer roles, rounded-to-zero required ATR export and partial MATCHED write. Include undeclared opposing generic branches, spurious F-005 requirements on generic definitions, generic fallback from an invalid governed scope, fixed/branch bypass of F-005, and name/latest/arrival/lexical/strongest-score direction inference.

Classifier success cannot bypass FALSE/UNAVAILABLE formation or mandatory handoff failure; formation TRUE cannot bypass classifier NONE. A correct unmatched outcome with a wrongly skipped classifier fails A–C; no new resolver, transaction or wire field is allowed.

**REPLAY_RESTART_TESTS:**

RP-LOCAL: duplicate/conflicting input, crash at every write, replay pinned configuration/evidence, terminal/epoch dominance and immutable handoff bytes. Contradicted source blocks new analysis without rewriting prior frozen results. Apply AT-NR-053 H to both scopes: the existing immutable configuration/epoch binding includes the governing direction-resolution semantics, exact matched branch and any declared conflict rule. No newer configuration may switch scope in either direction, re-resolve a branch using latest data or remint cycle/result identity. Same-ID changed configuration/scope/branch/direction binding is an integrity conflict; the original accepted handoff remains immutable.

Retain separate classifier and final-resolution evidence/reasons across replay; do not overwrite the former with final NONE or reinterpret formation after active configuration changes.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW

**Local FA-R4-01 review scope:** Existing reviews verify the actual branch join, source-only classifier dependencies and all A–D transaction/replay discriminators in addition to unchanged AT-NR-053 scope tests.

**UPSTREAM_DEPENDENCIES:**

B8A, B5A

**DOWNSTREAM_DEPENDENTS:**

B6, B7A, B11, B12

**DEFINITION_OF_DONE:**

Canonical Set handler/handoff runs through existing stores and publishes one correct immutable result atomically; local replay and independent reviews pass. Native monitoring activation remains later authoritative placement, not handoff. Both frozen direction scopes and the invariant-1 oracle are covered by AT-NR-053 A–H; successful generic directions do not depend on F-005, and governed directions cannot bypass it.

Both independent branches and common prerequisites are joined only at final Set resolution; all AT-NR-068-CF owner-path cases pass without a second state machine or reminted lineage.

**RISKS:**

Creating cycle/result too early or persisting frozen record after publication breaks deterministic replay and F-013 lineage.

**DO_NOT:**

Do not rewrite existing scope/epoch infrastructure, remint on retry, invent references, make native calls or activate production worker.

## B6 — Frozen pending-entry monitor and two-cause signal production

**PRIORITY:**

P1

**PURPOSE:**

Implement complete Set-owned F-013 state and immutable sticky requirements, using existing placement/terminal intake.

**NORMATIVE_REQUIREMENTS:**

NR-075, NR-076, NR-077, NR-078, NR-079, NR-080, NR-104, NR-135

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R022, R043, R044, R051, R055

**EXISTING_FOUNDATION_REUSED:**

FN.SYNC, FN.EPOCH, FN.CAS, FN.MSG, FN.UOW, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

MISSING canonical monitor; actual placement/terminal sync infrastructure exists [E23,E41–E42; audit §22]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Complete frozen monitor/reducer and both immutable cause branches; actual native return/reconciliation integrates in B9.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.SYNC: LifecycleSetSyncStore — `src/triggertrade/persistence/lifecycle_set_sync_store.py::LifecycleSetSyncStore` (inventory L46); src/triggertrade/lifecycle_set_sync.py; EXTEND under §2 classification.

FN.EPOCH: SetFormationEpoch / SetConfigurationBinding — `src/triggertrade/set_scope.py::SetFormationEpoch` (inventory L88); `src/triggertrade/set_scope.py::SetConfigurationBinding` (inventory L17); EXTEND under §2 classification.

FN.CAS: OwnerStateStore — `src/triggertrade/persistence/postgres.py::OwnerStateStore` (inventory L128); EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/set_engine/cancellation.py. CONDITIONAL_NEW monitor/requirement representation in Set-owned PostgreSQL state; no second Lifecycle sync or cancellation engine.

**LEGACY_SURFACES_TO_FENCE:**

No generic TTL/new-opportunity/rematch cancellation hook; no legacy pending-order timeout.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.monitor, ST.cancel, ST.sync. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

**TRANSACTION_BOUNDARIES:**

TX.set, TX.monitor, TX.placement, TX.owner; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

ORDER_PLACED v3 return consumption; ORDER_CANCEL_SIGNAL v2 production. Set has no native ORDER_MANAGEMENT authority.

**IDENTITY_BINDINGS:**

evidence_digest; unavailable_requirement_id = signal_id (unavailable cause); signal_id (INVALIDATION cause); Deferred F-013 source/event transition binding

**NUMERIC_REQUIREMENTS:**

Frozen predicates use their exact Set numeric/evidence selector policies; this is not identity-only logic. Timestamp uses original authoritative TRUE/effective transition semantics.

**IMPLEMENTATION_SCOPE:**

Consume exact authoritative placement/terminal return. Apply §9.2 reducer and frozen numeric predicates. Persist INVALIDATION from actual TRUE evidence or sticky MONITORING_UNAVAILABLE using original-entry semantic key, first transition/time/primary reason and optional trustworthy record presence. If exact target is unresolved, retain original source/event transition without guessed wire message. Both causes remain immutable and later join B9 existing native cancel intent; only terminal remainder evidence ends applicability.

**TESTS_REQUIRED:**

Every four-outcome case, terminal/activation/TRUE/unavailable precedence, first-reason priority, optional-record truth, unbound/deferred binding, partial-fill coalescing, no recovery withdrawal and signal/outbox transaction. Existing LifecycleSetSync tests stay green; typed authoritative return fixtures test local semantics.

Existing regression examples (non-exhaustive): `tests/contract/test_target_contract_registry.py` (EXISTING), `tests/unit/test_lifecycle_set_sync.py` (EXISTING), `tests/unit/test_lifecycle_set_sync_store.py` (EXISTING), `tests/unit/test_target_contracts.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-075, AT-NR-076, AT-NR-077, AT-NR-078, AT-NR-079, AT-NR-080, AT-NR-104, AT-NR-135.

**NEGATIVE_BOUNDARY_TESTS:**

Handoff/create intent instead of ORDER_PLACED, wrong entry/client/native lineage, fabricated TRUE digest/time, newer opportunity/full rematch/TTL cause, filled quantity target, missing recovered requirement treated as absent.

**REPLAY_RESTART_TESTS:**

RP-LOCAL plus acquire-or-join race, terminal-before-placement, restart unbound incident, signal lost ack, recovery before/after publication, duplicate cause and changed content under same key. Market recovery never changes first reason/time.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; CONTRACT_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; NUMERIC_PRECISION_REVIEW

**Local NUMERIC_PRECISION_REVIEW scope:** Review B6's exact frozen F-013 numeric predicates and TT_SET_NUMERIC_V1 use for Set-derived dependencies, including the prescribed working-value boundaries and exact comparisons with no epsilon. Verify correct availability/unavailability branching and unchanged TRUE/FALSE/UNAVAILABLE/INVALID_CONDITION outcomes; reject implicit quantization, hidden precision recovery or any numeric shortcut that changes those outcomes. Review the already-specified predicate evaluator and reducer without changing F-013 semantics, moving implementation out of B6 or duplicating Set formula ownership.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3, B4, B5B

**DOWNSTREAM_DEPENDENTS:**

B9, B11, B12

**DEFINITION_OF_DONE:**

Set monitor and both strict causes are locally correct, durable and reviewed. Actual native producer/consumer return and remainder-cancel integration must still pass B9; intake fixtures are not native conformance evidence.

**RISKS:**

Envelope-only implementation omits the reducer and numeric predicates; reminting on partial fill or recovery can create contradictory cancellation authority.

**DO_NOT:**

Do not cancel natively from Set, target filled exposure, withdraw/reclassify sticky requirements, guess target or add a second placement/terminal channel.

## B7A — Initial Position opportunity

**PRIORITY:**

P1

**PURPOSE:**

Pin immutable handoff/configuration and compute only the initial Entry/Stop/Take opportunity before any grant.

**NORMATIVE_REQUIREMENTS:**

NR-012, NR-082, NR-083, NR-084, NR-085, NR-086, NR-087, NR-088, NR-089, NR-090, NR-091, NR-097, NR-135, NR-141, NR-142, NR-149, NR-153, NR-154

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R014, R017, R020, R024, R025, R038, R039, R040, R041, R042, R043, R044

**EXISTING_FOUNDATION_REUSED:**

FN.PIN, FN.CONSTRUCT, FN.CONTRACT, FN.MSG, FN.UOW, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

MISSING canonical opportunity calculations; pin and structural helpers exist [E23,E37; audit §23]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

One pinned initial Position opportunity and retained geometry, with post-grant gates NOT_YET_EVALUATED.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.PIN: Position configuration-pin capability — `src/triggertrade/persistence/position_config_pin_store.py::PositionConfigPinStore` (inventory L32); src/triggertrade/position_config_pins.py; EXTEND under §2 classification.

FN.CONSTRUCT: PositionConstructionStore — `src/triggertrade/persistence/position_construction_store.py::PositionConstructionStore` (inventory L36); src/triggertrade/position_construction.py; EXTEND under §2 classification.

FN.CONTRACT: Registry/generated schema/parser — src/triggertrade/contracts/registry.py; src/triggertrade/contracts/_approved_wire_schema.py; src/triggertrade/contracts/schema_validator.py; ADAPT under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/position_rules/formulas.py and handler.py for missing canonical kernels/owner flow; preserve existing pin and construction helpers.

**LEGACY_SURFACES_TO_FENCE:**

Legacy futures strategy/position lifecycle calculations do not supply canonical decisions.

**PERSISTENCE_ACTION:**

EXTEND

**PERSISTENCE_DETAILS:**

Logical records: ST.position, ST.config. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

NR-153/154: extend the same ST.position work record with complete RPT-POS/RPT-ENTRY/RPT-TP fields and exact Set/config/reference lineage in §6.4.3, including actual visited/unvisited candidates, raw/rounded distances, original canonical age, actual thesis branch and all stage-specific reasons on rejected outcomes. Additional report fields are owner-local, not new wire fields or another canonical store.

**TRANSACTION_BOUNDARIES:**

TX.opportunity, TX.construction, TX.owner, TX.native, TX.set, TX.hold; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

MARKET_HANDOFF v4 consumption; initial APPROVE_REJECT v5 production.

**IDENTITY_BINDINGS:**

position_decision_id / initial event_id

**NUMERIC_REQUIREMENTS:**

Use received Q18 handoff values exactly, not recovered high precision; exact geometry/ratios and source-defined directional tick rounding. Report precision cannot decide gross gate.

**IMPLEMENTATION_SCOPE:**

Validate one handoff and atomically pin Position configuration. Compute F-008 Entry, F-006 LONG/F-007 SHORT stop, F-009 stop dispatch, F-010 Dynamic TP and source-defined fixed-mode support; preserve references, failure precedence, rounding and geometry. Preserve the evaluation schedule and separate operand graph in §5.1: Stop evaluation may precede F-010, but F-010 is evaluated whenever its own required inputs are valid, with no Stop value/status dependency. Join the independently evaluated results only afterward for joint Entry/Stop/TP feasibility and geometry; an unavailable required Stop still forces overall initial REJECT even when TP is usable. Apply enabled initial gross R:R only from its valid required geometry; emit one initial APPROVE_REJECT with construction gates NOT_YET_EVALUATED. Persist retained geometry for the exact subsequent grant.

R6 source retention: implement the Position portions of §6.4 alongside the actual F-008/F-010 evaluation in the existing TX.opportunity. Retain the complete frozen input collection for later diagnostic comparison but never mark an unvisited target as evaluated. Capture original family/type/policy/reference/time/ATR/tick/metric/failure evidence before publication, including independently usable TP despite unavailable Stop and usable Entry despite later rejection. No Research calculation, report result, future fill or sensitivity parameter may affect this opportunity.

**TESTS_REQUIRED:**

Independent LONG/SHORT and mode vectors, role/reference preflight, Entry hierarchy, dynamic-stop candidate/risk sequence, TP sequential traversal, tick-boundary postchecks, initial gross threshold and stage contracts.

R6 required source acceptance: AT-NR-153 ENTRY-RPT-01–04/08–09/12 and Position-source portions of 13–15; AT-NR-154 TP-RPT-01–07/13 and original-input portions of 14–17 (§6.4). Actual selectors generate the retained fields; tests inspect durable source records, not manually fabricated report inputs. Full path/outcome/SQLite report tests remain at their later source/assembly checkpoints. All existing AT-NR-089 assertions remain mandatory and unchanged.

**AT-NR-089 — F-010 independent evaluation with an unavailable required dynamic Stop (FA-01):**

This is a required subcase of the existing AT-NR-089, with the existing AT-NR-083/087/088/090/097 opportunity, Stop, rounding and aggregation obligations; it adds no NR row. Exercise the actual B7A owner path and its F-010 evaluator, not a stub that returns the expected TP. All remaining handoff/configuration fields must be independently source-valid; the projection below is not a shortened wire envelope.

**Given:** one schema-valid, immutable LONG Market Handoff with matching instrument/cycle/result/digest, valid `matched_at`/`market_snapshot_at`, metadata revision and tick/source provenance; one pinned valid Position configuration with DYNAMIC Stop and DYNAMIC TP. Use `set_match_reference_price = 102`, received `ATR_15m = 10` and `tick_size = 0.1`, all exact. The frozen, complete relevant level collection contains one producer-proven `SWING_LOW_15M` at `100` and one producer-proven `SWING_HIGH_15M` at `110`, with unique original IDs and valid type/timeframe/provenance/availability evidence (`available_at <= matched_at`); there are no other candidates. Entry, SL and TP contexts use `GENERIC` and valid `NONE` policy, with each thesis ID and its origin binding null as required. The handoff and its F-008 result retain the same immutable identity/configuration bindings throughout; no source, Stop or TP value is synthesized.

The independently derived oracle is:

```text
F-008 Entry:
improvement = 102 - 100 = 2
improvement_atr = 2 / 10 = 0.2, within [0.10, 1.25]
rounded_entry = floor(100 / 0.1) * 0.1 = 100
E = 100, AVAILABLE / usable

Required LONG dynamic Stop:
the only permitted LOW reference is 100
strict adverse-side test: 100 < E - tick = 99.9 is false
the HIGH reference at 110 is not an allowed LONG Stop type
no eligible adverse-side reference -> unusable / NO_ELIGIBLE_REFERENCE
F-009 DYNAMIC retains the unusable directional Stop outcome; no fallback

F-010 TP, evaluated independently from its own valid inputs:
110 > E + tick = 100.1
distance_price = 110 - 100 = 10
distance_atr = 10 / 10 = 1, within [0.75, 4.00]
rounded_tp = floor(110 / 0.1) * 0.1 = 110
110 > E, 110 <= selected_target_price, 110 / 0.1 = 1100
4 * rounded_distance_price = 40 >= 3 * ATR_15m = 30
rounded_distance_price = 10 <= 4 * ATR_15m = 40
selected target = original SWING_HIGH_15M reference
usable = true; reason = AVAILABLE; rounded_tp = 110
```

**Then:** retain the independently evaluated TP result/traversal evidence even though the Stop is unusable. No Stop price, distance or availability result is passed to or read by F-010 as a calculation/preflight dependency. The later joint TP/SL feasibility cannot pass because the required Stop is unavailable; dependency-blocked checks are not fabricated PASS results. Aggregate the initial opportunity as **REJECT**, not APPROVE. Construction-stage gates remain `NOT_YET_EVALUATED`; no grant, successful plan, tranche, spec, authorization or native side effect follows from this opportunity. An absent Stop is not zero and must not be repaired.

**Discriminating negative control:** an implementation that skips F-010 solely because Stop is unavailable must fail this test even if it returns the expected overall REJECT. Assert the actual independently derived `110` TP and selected original reference/traversal evidence on the B7A path, as well as the rejected opportunity and absence of downstream authority. A Stop-dependent selector, SL-distance-derived TP, synthetic Stop, forced TP unavailability or prefilled/stubbed TP result must not satisfy the case. This is acceptance coverage to implement at B7A and include in existing V03/V04/V06 integrated coverage, not a claim of a backend test executed during R2.

**Frozen derivation:** `docs/trading-methodology/methodology/POSITION_RULES.md` Part II §§8–10 L2206–L2262, §12 L2311–L2325, §§21–22 L2473–L2507 and §§29–31 L2661–L2748 establish the Entry projection; Part III §§6–10 L3365–L3487 and §26 L3844–L3858 establish the missing usable Stop without a fallback; Part IV §§4/10 L4331–L4352 and L4476–L4480, §§14–15 L4555–L4581, §§19–21 L4633–L4702, §26 L4896–L4909 and §§29–30 L4954–L5013 establish independent TP selection/rounding. Part I §14 L465–L519 and §43 L1500–L1508 require independent current-stage evaluation, overall REJECT for required unavailability and no grant-dependent gate before grant. These exact calculations are source-derived fixture expectations, not outputs copied from an implementation under test.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_order_specs_contracts.py` (EXISTING), `tests/contract/test_position_construction_contracts.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_order_spec_store.py` (EXISTING), `tests/unit/test_order_specs.py` (EXISTING), `tests/unit/test_position_config_pin_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-012, AT-NR-082, AT-NR-083, AT-NR-084, AT-NR-085, AT-NR-086, AT-NR-087, AT-NR-088, AT-NR-089, AT-NR-090, AT-NR-091, AT-NR-097, AT-NR-135, AT-NR-141, AT-NR-142, AT-NR-149.

**NEGATIVE_BOUNDARY_TESTS:**

Missing/unavailable/identity-conflicting handoff, attempt to fetch latest Set or direct API facts, downstream repair/reselection, initial PASS net economics or fabricated grant/plan/tranche/spec. Also reject a Stop operand/preflight/availability dependency in F-010, skipping its independently evaluable TP solely because Stop is unavailable, or deriving TP from SL distance. The independent usable TP must not turn the missing-Stop opportunity into APPROVE.

NR-153/154 reject reason-class merging, candidate counts synthesized from overall REJECT, absent Stop suppressing independently evaluated TP evidence, current ATR/reference-age substitution and report-created future success IDs. Additional report capture cannot become a new selection gate or live feedback input.

**REPLAY_RESTART_TESTS:**

RP-LOCAL with simultaneous first evaluation, changed active config after pin, duplicate handoff and crash between pin/decision/outbox. Later retries retain original geometry and initial decision.

RPT-POS/ENTRY/TP source evidence commits with the original decision/pin/outbox and restores exactly: same candidate IDs/order/status, warning/primary reason, raw/rounded metric and original age/time/configuration. Source-only tests need no later grant, FINAL or report. Research copy failure cannot roll back this owner commit.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW

**R6 NR-153/154 local scope:** Apply the existing IMPLEMENTATION_REVIEW, NUMERIC_PRECISION_REVIEW, ADVERSARIAL_TRADING_REVIEW, PERSISTENCE_TRANSACTION_REVIEW, REPLAY_IDEMPOTENCY_REVIEW and TEST_REVIEW to the Position reporting-source matrix (§10.5). Existing CONTRACT_REVIEW confirms owner-local additions do not change any wire boundary. No duplicated tokens or new categories.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3, B4, B5B

**DOWNSTREAM_DEPENDENTS:**

B8B, B7B, B11, B12

**DEFINITION_OF_DONE:**

Initial opportunity and immutable pin/outbox are locally correct and reviewed; actual grant consumption, F-011 and completed F-012 remain B7B. Initial REJECT has no grant authority.

All original Entry/TP report-source fields and initial-stage tests in §6.4 are durably complete and locally reviewed; no report-generated geometry, later native outcome or missing historical field is deferred to B13.

**RISKS:**

Computing full economics before grant creates dependency cycle and unsupported facts; post-grant tick/fee changes cannot trigger hidden selection.

**DO_NOT:**

Do not issue a Portfolio grant, create a spec, place orders or compute successful post-grant construction in this checkpoint.

## B8B — Portfolio non-reserving grant

**PRIORITY:**

P1

**PURPOSE:**

Issue a uniquely bound immutable grant only after the actual B7A initial APPROVE.

**NORMATIVE_REQUIREMENTS:**

NR-011, NR-021, NR-036, NR-041, NR-042, NR-047, NR-052, NR-119, NR-135, NR-151

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R016, R017, R018, R019, R020, R043, R044, R045, R047, R048

**EXISTING_FOUNDATION_REUSED:**

FN.GRANT, FN.PORT, FN.FACT, FN.COOLDOWN, FN.MSG, FN.UOW, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: grant issue/binding store exists; canonical owner gates incomplete [E35–E36,E47]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

CapitalGrantStore already retains successful immutable issue payloads; denied/unavailable evaluations and full multi-reason histories still require the NR-151 extension.

**TARGET_STATE:**

One non-reserving immutable Portfolio grant bound to real initial APPROVE.

The original non-reserving grant path also durably retains ALLOWED/BLOCKED/UNAVAILABLE grant evaluations and all evaluated reasons, including denied opportunities with no grant ID.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.GRANT: CapitalGrantStore / grant builder — `src/triggertrade/persistence/capital_grant_store.py::CapitalGrantStore` (inventory L32); `src/triggertrade/capital_grants.py::build_capital_and_limits_grant` (inventory L15); EXTEND under §2 classification.

FN.PORT: Portfolio state/buckets — `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py; EXTEND under §2 classification.

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.COOLDOWN: Portfolio cooldown pins — `src/triggertrade/persistence/portfolio_cooldown_store.py::PortfolioCooldownStore` (inventory L33); src/triggertrade/portfolio_cooldown.py; EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

Extend NEW_PROPOSED Portfolio owner module from B8A; no new grant store. Additional helper only for a demonstrably missing owner gate.

**LEGACY_SURFACES_TO_FENCE:**

No legacy allocator or accounting service supplies a grant.

**PERSISTENCE_ACTION:**

EXTEND

**PERSISTENCE_DETAILS:**

Logical records: ST.grants. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

Extend ST.portfolio P-DECISION history alongside ST.grants; retain original initial APPROVE identity, evaluated state/configuration/facts, complete gate results/primary and secondary reasons, candidate C when available, and existing issue created_at/amount. A denial has no fabricated grant/hold/authorization.

**TRANSACTION_BOUNDARIES:**

TX.grant, TX.construction, TX.hold, TX.facts, TX.scope, TX.final, TX.owner; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

Initial APPROVE_REJECT v5 consumption; CAPITAL_AND_LIMITS v5 production; permitted Portfolio factual request/response as needed.

**IDENTITY_BINDINGS:**

request_id; capital_grant_id

**NUMERIC_REQUIREMENTS:**

Exact free capacity then floor_Qcapital; division by positive remaining slots then floor_Qcapital again. Grant residue remains free; no final-recipient redistribution.

**IMPLEMENTATION_SCOPE:**

Consume exact initial decision/cycle/result, reject unsuccessful/wrong-stage inputs, evaluate governed current grant gates and capture permitted applicable instrument/native-profile/fee/accounting facts. Use build_capital_and_limits_grant and CapitalGrantStore.issue under outer UoW with outbox. Grant is non-reserving, immutable, without TTL; all true holds wait for B8C.

Capture the actual grant decision and complete P-DECISION evidence in TX.grant, atomically with successful grant/outbox or the denied/unavailable owner outcome. Retain capacity-missed opportunity lineage even when no grant can issue. Existing temporary-unavailability/new-governed-refresh behavior is unchanged; replay of a captured evaluation returns its original reasons, while an issued grant remains immutable/non-reserving.

**TESTS_REQUIRED:**

Actual initial APPROVE→grant flow, Cfree/remaining-slot floor sequence, minimum capital and exact limits, currency/profile/fee applicability, immutable grant payload and no capital/slot mutation. Under AT-NR-036 case 01, retain the valid 80%-targets/60%-global configuration without rejecting or normalizing its sum. Apply the existing grant-time global/per-coin/slot gates and sizing sequence; issuance remains non-reserving. Cases 02–04 verify subsequent actual booking at B8C, not a new B8B hold.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_coins_scope_contracts.py` (EXISTING), `tests/contract/test_portfolio_state_contracts.py` (EXISTING), `tests/contract/test_submit_authorizations_contracts.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_coins_scope.py` (EXISTING), `tests/unit/test_coins_scope_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-011, AT-NR-021, AT-NR-036, AT-NR-041, AT-NR-042, AT-NR-047, AT-NR-052, AT-NR-119, AT-NR-135, AT-NR-151.

AT-NR-151 cases01/02/03-creation/04 grant-time analog/05–07/12: source-valid multiple evaluated failures, distinct unavailable, successful issue history, denied-capacity/cooldown/day cases, exact candidate/C values, duplicate count once, original issue bytes and all no-reservation assertions. The full later consumed/closed test completes at B8C/B9/B10.

**NEGATIVE_BOUNDARY_TESTS:**

Grant before persisted approval, stale or wrong initial ID, missing required factual row, zero slots, nonpositive grant and user-supplied arbitrary amount. Same approved decision with changed content conflicts.

A blocked or unavailable gate cannot disappear from history because no grant exists; a selected primary reason cannot erase another evaluated reason. Diagnostic capture may not manufacture a grant, reserve surplus, permanently expire temporarily unissuable work or replay a terminal opportunity.

**REPLAY_RESTART_TESTS:**

RP-LOCAL: duplicate APPROVE returns original grant/outbox; crash during issue publishes nothing partial; changed current facts cannot rewrite an already issued grant.

Same owner evaluation, success or denial, reuses the original outcome, reason collection and first times. Same captured identity with changed contents conflicts. Crash before TX.grant commits neither its outcome nor observations; after commit duplicate does not reissue/count.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**NR-151 local review responsibilities:** Existing IMPLEMENTATION_REVIEW/TEST_REVIEW cover the complete allowed/blocked/unavailable grant outcome and all evaluated reasons; PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW cover atomic issue/denial history and count-once behavior; NUMERIC_PRECISION_REVIEW covers candidate C/grant amounts/cap diagnostics; ADVERSARIAL_TRADING_REVIEW covers missed opportunities and competing evaluations. CONTRACT_REVIEW confirms no new message fields or denied-outcome grant authority. No B10 financial-finality behavior is implemented here.

**UPSTREAM_DEPENDENCIES:**

B8A, B7A

**DOWNSTREAM_DEPENDENTS:**

B7B, B11, B12

**DEFINITION_OF_DONE:**

Real initial producer and grant consumer/producer are integrated and reviewed; exact grant can feed B7B. No reservation, authorization, plan or native order is implied.

NR-151 grant issue/denial/unavailable observations and local tests/reviews pass with the non-reserving grant path; immutable issue timestamps are not later consumption or terminal times.

**RISKS:**

Confusing a grant with hold overbooks concurrent opportunities; fetching missing facts directly from Position adds a forbidden edge.

**DO_NOT:**

Do not reserve H/slot, create plan/tranche/spec, recalculate Position geometry/economics or invent A-005/A-006.

## B7B — Post-grant Position construction and economics

**PRIORITY:**

P1

**PURPOSE:**

Complete F-011/F-012 from the exact grant and retained initial geometry, producing one immutable success/failure with correct atomic output.

**NORMATIVE_REQUIREMENTS:**

NR-011, NR-012, NR-084, NR-091, NR-092, NR-093, NR-094, NR-095, NR-096, NR-097, NR-098, NR-099, NR-119, NR-135, NR-141

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R017, R019, R020, R024, R025, R038, R039, R040, R041, R042, R043, R044, R045, R047

**EXISTING_FOUNDATION_REUSED:**

FN.PIN, FN.GRANT, FN.CONSTRUCT, FN.SPEC, FN.MSG, FN.UOW, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

MISSING certified calculation; existing construction/spec stores not yet joined as complete owner flow [E37–E39]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Exact post-grant F-011/F-012 result plus success spec and two outboxes in one UoW, or valid immutable failure.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.PIN: Position configuration-pin capability — `src/triggertrade/persistence/position_config_pin_store.py::PositionConfigPinStore` (inventory L32); src/triggertrade/position_config_pins.py; EXTEND under §2 classification.

FN.GRANT: CapitalGrantStore / grant builder — `src/triggertrade/persistence/capital_grant_store.py::CapitalGrantStore` (inventory L32); `src/triggertrade/capital_grants.py::build_capital_and_limits_grant` (inventory L15); EXTEND under §2 classification.

FN.CONSTRUCT: PositionConstructionStore — `src/triggertrade/persistence/position_construction_store.py::PositionConstructionStore` (inventory L36); src/triggertrade/position_construction.py; EXTEND under §2 classification.

FN.SPEC: OrderSpecStore — `src/triggertrade/persistence/order_spec_store.py::OrderSpecStore` (inventory L37); src/triggertrade/order_specs.py; EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/position_rules/sizing.py and economics.py; extend existing result/spec stores, not new ledgers.

**LEGACY_SURFACES_TO_FENCE:**

Demo sizing/economics and precision remain noncanonical without independent proof.

**PERSISTENCE_ACTION:**

EXTEND

**PERSISTENCE_DETAILS:**

Logical records: ST.construction, ST.spec. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

**TRANSACTION_BOUNDARIES:**

TX.grant, TX.construction, TX.hold, TX.opportunity, TX.native, TX.final, TX.owner; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

CAPITAL_AND_LIMITS v5 consumption; construction APPROVE_REJECT v5 and ORDER_SPEC v5 production.

**IDENTITY_BINDINGS:**

construction_result_id; position_plan_id / tranche_id / order_spec_id; order_spec_digest

**NUMERIC_REQUIREMENTS:**

Exact products/rationals; Q step floor; mathematical A=N/leverage retained; H=ceil_Qcapital(A); test both <=C. N exact. Qratio report-only; signed rate and rebate semantics preserved.

**IMPLEMENTATION_SCOPE:**

Consume the exact grant/initial pin, preserving original Entry/SL/TP. Compute C,T,Q,N, exact A and ceiling H with fixed constraints; evaluate signed factual fees/rebates and exact enabled F-012 gates. Apply no-repair and reason precedence. On success use one connection/UoW for construction result, ORDER_SPEC and both outboxes; failure creates outcome/decision only with no success plan/tranche/spec.

**TESTS_REQUIRED:**

Independent sizing/economics vectors, min/max/step/tick boundaries, exact A/H and scalar equality, signed rates, denominator N, empty baseline additional costs, future funding excluded, both output contracts and PostgreSQL four-write atomicity.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_order_specs_contracts.py` (EXISTING), `tests/contract/test_position_construction_contracts.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_order_spec_store.py` (EXISTING), `tests/unit/test_order_specs.py` (EXISTING), `tests/unit/test_position_config_pin_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-011, AT-NR-012, AT-NR-084, AT-NR-091, AT-NR-092, AT-NR-093, AT-NR-094, AT-NR-095, AT-NR-096, AT-NR-097, AT-NR-098, AT-NR-099, AT-NR-119, AT-NR-135, AT-NR-141.

**NEGATIVE_BOUNDARY_TESTS:**

Wrong grant/cycle/config, Q=0, A>C or H>C, malformed/missing fee provenance, extra asserted undefined cost, min-gate rounded report collision and any reprice/resize/repair.

**REPLAY_RESTART_TESTS:**

RP-LOCAL: both downstream arrival orders, duplicate grant, conflict outcome, failure replay without success IDs, restart with newer active settings and every result/spec/two-outbox cutpoint.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; CONTRACT_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW

**UPSTREAM_DEPENDENCIES:**

B7A, B8B

**DOWNSTREAM_DEPENDENTS:**

B8C, B11, B12

**DEFINITION_OF_DONE:**

Exact successful result/spec and both outboxes commit together under reused stores, or a valid immutable failure is emitted. Independent numeric/trading/contract/transaction/replay/test reviews pass.

**RISKS:**

Separate store-local commits create orphan success/spec; treating A as H or planned fee reports as exact gate values alters money.

**DO_NOT:**

Do not make Portfolio compute F-011/F-012, use C/H/T as net-edge denominator, pull direct API facts or change frozen geometry.

## B8C — Current Portfolio hold and authorization

**PRIORITY:**

P1

**PURPOSE:**

Book only currently admissible constructed capital H and the required slot, then publish authorization atomically.

**NORMATIVE_REQUIREMENTS:**

NR-011, NR-016, NR-030, NR-036, NR-037, NR-040, NR-042, NR-043, NR-044, NR-045, NR-046, NR-048, NR-049, NR-052, NR-113, NR-132, NR-135, NR-149, NR-151

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R014, R018, R019, R020, R021, R023, R030, R043, R044, R045, R047

**EXISTING_FOUNDATION_REUSED:**

FN.AUTH, FN.PORT, FN.COOLDOWN, FN.GRANT, FN.MSG, FN.UOW, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: authorization/Portfolio stores exist; complete current atomic hold/frontier not established [E40,E47]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Current exact H/slot/config/frontier booking and authorization in one Portfolio transaction.

Current gate/booking success and denial histories include exact original H/cap/slot/configuration/frontier basis and the actual grant-consumption cutpoint; no observation becomes authority.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.AUTH: SubmitAuthorizationStore — `src/triggertrade/persistence/submit_authorization_store.py::SubmitAuthorizationStore` (inventory L35); src/triggertrade/submit_authorizations.py; EXTEND under §2 classification.

FN.PORT: Portfolio state/buckets — `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py; EXTEND under §2 classification.

FN.COOLDOWN: Portfolio cooldown pins — `src/triggertrade/persistence/portfolio_cooldown_store.py::PortfolioCooldownStore` (inventory L33); src/triggertrade/portfolio_cooldown.py; EXTEND under §2 classification.

FN.GRANT: CapitalGrantStore / grant builder — `src/triggertrade/persistence/capital_grant_store.py::CapitalGrantStore` (inventory L32); `src/triggertrade/capital_grants.py::build_capital_and_limits_grant` (inventory L15); EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

Extend Portfolio owner functions/current booking state; CONDITIONAL_NEW fields only for missing canonical attempt/day/frontier linkage. No second allocator or authorization store.

**LEGACY_SURFACES_TO_FENCE:**

Legacy day/allocator paths remain excluded.

**PERSISTENCE_ACTION:**

EXTEND

**PERSISTENCE_DETAILS:**

Logical records: ST.holds, ST.authorization, ST.portfolio, ST.config, ST.cooldown, ST.day, ST.frontier. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

NR-151 additionally links existing ST.grants issue history to consumption/actual terminal-resolution observations, retained ST.portfolio P-DECISION/P-TRANSITION records and immutable original construction confirmations/transport evidence. Do not mutate frozen grant/auth payloads or create another canonical ledger.

**TRANSACTION_BOUNDARIES:**

TX.grant, TX.construction, TX.hold, TX.frontier, TX.acceptance, TX.scope, TX.closeretention, TX.day, TX.receipt, TX.partition, TX.owner, TX.set, TX.opportunity; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

Construction APPROVE_REJECT v5 consumption and SUBMIT_AUTHORIZED v5 production. Immutable spec binding is verified; Portfolio is not a new ORDER_SPEC message consumer. ORDER_EVENT projections integrate in B9/B10.

**IDENTITY_BINDINGS:**

authorization_id; entry_acceptance_integrity revision / resolution_id; Committed-prefix technical scope/head/applied sequence

**NUMERIC_REQUIREMENTS:**

Copy exactly the already canonical H. Four capital buckets/conservation and inclusive comparisons remain exact; no re-quantized liability or grant-surplus reservation.

**IMPLEMENTATION_SCOPE:**

Consume successful construction and its exact spec binding, independently compare duplicated scalars/digest, and recheck current capital, slots, limits, cooldown, A-009 and incident frontier. Under one serialized UoW consume grant, hold exact H, reserve slot, pin Portfolio attempt config/duration, create SUBMIT_AUTHORIZED and append outbox. Add typed Lifecycle event/receipt consumer interfaces for subsequent B9/B10 integration; Portfolio never recomputes Position formulas.

In the existing TX.hold, retain all actually evaluated current gate outcomes/reasons and original cap/slot/day/cooldown/prefix basis. Successful booking retains first grant-consumed/hold-created time and exact H; definitive denied outcome retains full evidence with zero success hold/slot/auth/outbox. Preserve actual rejected-construction resolution evidence without inventing closure for unresolved work. Provide read-only diagnostics from §6.2, including original producer-owned T visibility by immutable construction lineage, without importing/recomputing Position formulas.

**TESTS_REQUIRED:**

Last-slot/last-capital concurrency, exact inclusive limits, H<C, duplicated scalar mismatch, current day/latch/cooldown and incident-before-hold. Verify first bookable constructed transaction, not request arrival or stale grant, wins. Run AT-NR-036 cases 01–04 using the unchanged valid 80%-targets/60%-global configuration: no config-sum rejection/normalization, global and individual-coin excess each reject current booking, and exact allowed global equality passes when all other gates pass. Use valid immutable original grants and independently constructed H/scalars; verify rejected bookings commit no partial hold/slot/authorization/outbox and the equality case books H only once under TX.hold.

Existing regression examples (non-exhaustive): `tests/contract/test_capital_grants_contracts.py` (EXISTING), `tests/contract/test_coins_scope_contracts.py` (EXISTING), `tests/contract/test_portfolio_state_contracts.py` (EXISTING), `tests/contract/test_submit_authorizations_contracts.py` (EXISTING), `tests/unit/test_capital_grant_store.py` (EXISTING), `tests/unit/test_capital_grants.py` (EXISTING), `tests/unit/test_coins_scope.py` (EXISTING), `tests/unit/test_coins_scope_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-011, AT-NR-016, AT-NR-030, AT-NR-036, AT-NR-037, AT-NR-040, AT-NR-042, AT-NR-043, AT-NR-044, AT-NR-045, AT-NR-046, AT-NR-048, AT-NR-049, AT-NR-052, AT-NR-113, AT-NR-132, AT-NR-135, AT-NR-149, AT-NR-151.

AT-NR-151 cases03-consumption/04/05/06/07/08/09-booking/11/12, with full current capacity and last-slot conflicts. Source-valid T remains displayed from Position's retained work record only; a trap forbids Portfolio F-011 recomputation. Denial history survives independently of absent success records; case12 distinguishes business denial from database rollback.

**NEGATIVE_BOUNDARY_TESTS:**

Hold C or exact unquantized A instead of H, already consumed grant/auth, current incident unseen because only inbox dedupe checked, stale grant assumed capacity, missing recovered day treated as clear.

Do not discard a failed booking's actual reasons, count a retried evaluation twice, equate grant C with H, record C−H as held/released, infer closed_at from elapsed time/no native order, or substitute mutable latest caps for original diagnostic basis.

**REPLAY_RESTART_TESTS:**

RP-LOCAL with hold/slot/auth/outbox rollback, current-scope frontier retry and duplicate construction. Pinned attempt duration survives config changes; later Lifecycle status projection cannot silently free resources.

Original full gate evidence, successful consumed/hold cutpoint and captured concurrency denials survive restart; technical transaction retries reuse captured attempt/failure identity under §7.6. No diagnostic restores a consumed grant or alters the immutable spec.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**NR-151 local review responsibilities:** Existing IMPLEMENTATION_REVIEW/TEST_REVIEW cover complete current-booking reasons and actual consumption/hold/denial observations; PERSISTENCE_TRANSACTION_REVIEW/REPLAY_IDEMPOTENCY_REVIEW cover success/denial atomicity and concurrent/captured-attempt replay; NUMERIC_PRECISION_REVIEW covers H, never-held C−H and exact history-based utilization; ADVERSARIAL_TRADING_REVIEW covers global/coin/slot denials and concurrency. CONTRACT_REVIEW verifies immutable confirmation/authorization binding and audit-only T visibility without a new business edge. Actual day-base/latch producer review remains B8A and terminal receipt/release accounting review remains B10; neither is implemented for the first time here.

**UPSTREAM_DEPENDENCIES:**

B8A, B7B

**DOWNSTREAM_DEPENDENTS:**

B9, B10, B11, B12

**DEFINITION_OF_DONE:**

Current constructed-result→H/slot/auth transaction is complete and locally reviewed with frontier primitive. Actual acceptance/close projections complete B9 and actual FINAL receipt/day/release complete B10 before activation.

NR-151 current-booking and denial histories, consumed/created cutpoints and history-backed views pass local tests/reviews. Actual factual acceptance/proven terminal closure/release observations remain B9/B10 producers.

**RISKS:**

A complete B8A grant state does not imply current booking authority; current incident head must share transaction with hold.

**DO_NOT:**

Do not recompute F-011/F-012, release on order flatness or emit native calls. Do not declare the future receipt path integrated before B10.

## B9 — Lifecycle native flow, protection and factual reconciliation

**PRIORITY:**

P1

**PURPOSE:**

Extend existing Lifecycle start/intent/sync/close/reconciliation machinery into the complete native owner path without duplicating authority.

**NORMATIVE_REQUIREMENTS:**

NR-019, NR-024, NR-025, NR-027, NR-028, NR-029, NR-030, NR-033, NR-034, NR-040, NR-044, NR-045, NR-046, NR-049, NR-076, NR-081, NR-099, NR-100, NR-101, NR-102, NR-103, NR-104, NR-105, NR-106, NR-107, NR-108, NR-109, NR-110, NR-111, NR-112, NR-113, NR-114, NR-115, NR-116, NR-117, NR-133, NR-135, NR-142, NR-143, NR-144, NR-146, NR-148, NR-151, NR-152, NR-153, NR-154

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R016, R017, R018, R019, R021, R022, R023, R024, R027, R030, R031, R038, R043, R044, R047, R048, R051

**EXISTING_FOUNDATION_REUSED:**

FN.START, FN.SUBMIT, FN.SYNC, FN.CLOSE, FN.RECON, FN.NATIVE, FN.API, FN.PORT, FN.COOLDOWN, FN.MSG, FN.UOW, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL: native intent/sync/close/reconciliation foundation; canonical handler/current proofs incomplete [E41–E46,E56–E60; audit §25]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

NR-152 requires full attempt/arrival/recovery/cleanup observation history beyond current latest submission fields and sync rows; NR-151 requires Portfolio's own separately committed factual projection history. Exact existing/proposed representations are in §§6.2.1/6.3.1.

**TARGET_STATE:**

One existing Lifecycle handles native intent/facts/placement/protection/remainder/close/attribution safely; financial terminality remains B10.

The same Lifecycle additionally retains every §43 operational observation and supports §40 visibility, while Portfolio separately records its own acceptance/hold/reserved/reconciliation/proven-terminal observations on existing events.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.START: Lifecycle start gate — `src/triggertrade/persistence/lifecycle_start_gate_store.py::LifecycleStartGateStore` (inventory L46); src/triggertrade/lifecycle_start_gate.py; EXTEND under §2 classification.

FN.SUBMIT: LifecycleSubmissionStore — `src/triggertrade/persistence/lifecycle_submission_store.py::LifecycleSubmissionStore` (inventory L61); src/triggertrade/lifecycle_submission.py; EXTEND under §2 classification.

FN.SYNC: LifecycleSetSyncStore — `src/triggertrade/persistence/lifecycle_set_sync_store.py::LifecycleSetSyncStore` (inventory L46); src/triggertrade/lifecycle_set_sync.py; EXTEND under §2 classification.

FN.CLOSE: LifecycleCloseAuthorityStore — `src/triggertrade/persistence/lifecycle_close_authority_store.py::LifecycleCloseAuthorityStore` (inventory L74); src/triggertrade/lifecycle_close_authority.py; EXTEND under §2 classification.

FN.RECON: Lifecycle reconciliation/events — `src/triggertrade/persistence/lifecycle_reconciliation_store.py::LifecycleReconciliationStore` (inventory L63); `src/triggertrade/persistence/lifecycle_order_event_store.py::LifecycleOrderEventStore` (inventory L38); EXTEND under §2 classification.

FN.NATIVE: Native factual profile boundary — src/triggertrade/api_adapter_gateway/native_profile.py; EXTEND under §2 classification.

FN.API: Factual API normalization — src/triggertrade/api_adapter_gateway/market_data.py; src/triggertrade/api_adapter_gateway/portfolio_data.py; src/triggertrade/api_adapter_gateway/order_management.py; EXTEND under §2 classification.

FN.PORT: Portfolio state/buckets — `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py; EXTEND under §2 classification.

FN.COOLDOWN: Portfolio cooldown pins — `src/triggertrade/persistence/portfolio_cooldown_store.py::PortfolioCooldownStore` (inventory L33); src/triggertrade/portfolio_cooldown.py; EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED src/triggertrade/order_lifecycle/handler.py as existing owner implementation organization. CONDITIONAL_NEW current-proof/source-partition/receipt fields in existing stores; no new Lifecycle or close ledger.

**LEGACY_SURFACES_TO_FENCE:**

Paper/spot/demo side-effect paths and uncertified native profiles remain fenced; tests do not activate production.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.submission, ST.nativefacts, ST.acceptance, ST.sync, ST.reconcile, ST.cancel, ST.close, ST.protection, ST.attribution, ST.portfolio. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row. Financial proof interfaces may remain blocked pending B10; do not create a second financial/finality store in B9.

NR-152 extends existing ST.transport/ST.submission/ST.authorization/ST.sync/ST.nativefacts/ST.acceptance/ST.reconcile/ST.protection/ST.cancel/ST.close histories with the missing L-* observations. NR-151 separately extends Portfolio ST.holds/ST.grants/ST.cooldown/ST.portfolio histories for its existing projections. There is no shared mutable owner ledger, extra state family, duplicate sync or new financial ledger in B9.

NR-153/154 reuse the original owner histories under §6.4.3/§7.7 and expose exact immutable read-only source membership. No second report/financial/quantity ledger is created in this owner. Research archival/assembly remains separately owned SQLite documentary persistence, not a cross-owner commit.

**TRANSACTION_BOUNDARIES:**

TX.facts, TX.native, TX.preflight, TX.acceptance, TX.protection, TX.partition, TX.hold, TX.closeretention, TX.receipt, TX.placement, TX.monitor, TX.cancel, TX.construction, TX.close, TX.owner, TX.incident, TX.opportunity, TX.final; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

ORDER_SPEC v5; SUBMIT_AUTHORIZED v5; ORDER_MANAGEMENT v4; ORDER_PLACED v3; ORDER_CANCEL_SIGNAL v2; ORDER_EVENT v7.

**IDENTITY_BINDINGS:**

request_id; response_id / snapshot_id / page_id; client_order_link_id (client_order_id / client order ID semantic label) / durable intent identity; exchange_order_id (native_order_id / native order ID semantic label); execution_id / native source execution identity; entry_acceptance_integrity revision / resolution_id; native_observation_id / native_scope_revision; attribution_resolution_id / allocation_id / allocation application receipt; close_intent_id / child sequence / cause identity; Factual-basis/source-set and allocation proof revision; incident_id / incident_revision

**NUMERIC_REQUIREMENTS:**

Exact factual quantities/prices/immutable spec values; disjoint half-open source slices and residual budget, no epsilon/clamp. Native effect consumes authorization, not rederived strategy.

**IMPLEMENTATION_SCOPE:**

Join exact spec/auth, check current coherent hard facts/profile, persist stable create intent before external call and reconcile ambiguity/lost ack. Publish actual placement/terminal return through LifecycleSetSyncStore and complete B6 real integration. Apply field-aware native facts, acceptance-time integrity and Portfolio projections, fills/remainder races, protection installation/current proof, cancel reconcile-first, one close intent/current reduction budget. Prove complete disjoint source partition and global receipts before quantity effect; preserve logical/native revision domains and tombstones. Financially incomplete closure remains blocked until B10.

Implement §§6.3.1–6.3.4 and §7.6 operational capture in the actual Lifecycle owner: full submission attempt/cutpoint history; separate authorization receipt/native-use or proven no-create consumption; first terminal publication to Set; verification failures and sibling cleanup cuts; cancel/close races; exact additional-fill members; reconciliation/recovery/manual observations; and stable duplicate/out-of-order captured-arrival classification. These do not change native operations or FINAL gates. In Portfolio's existing separate event consumers, implement NR-151 actual acceptance/reclassification/reserved-duration/reconciliation and proven no-create/zero-fill terminal observation history, including zero acceptance release of never-held C−H. No Lifecycle code writes Portfolio observations directly.

R6 NR-153/154 factual report source: retain actual observed dispatch/uncertainty, exact spec/auth/current-hard compatibility evaluation/refusal, venue POST_ONLY rejection versus cancellation, original comparable submit/acceptance timestamps, attributable fill IDs/quantity/price/authoritative order and complete entry-terminal history in the existing RPT-LIFE/L-* bases. Filled executions can prove dispatch/acceptance occurred without fabricating missing timestamps. Preserve close/exposure chronology for the later B10 permanent horizon. Public market-path acquisition/archival uses the B3-established isolated Research/factual-input boundary; do not add a Lifecycle market strategy, Research native operation or another API requester.

**TESTS_REQUIRED:**

Native stub with explicit factual proofs for ambiguous create, pending/partial/full fills, rejection precedence, acceptance-time resolution, protection omissions, F-013 both causes, single close budget and source-partition orderings. Actual PostgreSQL store/transport/projection transactions and native-profile conformance gate evidence.

Existing regression examples (non-exhaustive): `tests/contract/test_lifecycle_start_gate_contracts.py` (EXISTING), `tests/contract/test_native_profile_conformance.py` (EXISTING), `tests/unit/test_lifecycle_close_authority.py` (EXISTING), `tests/unit/test_lifecycle_close_authority_store.py` (EXISTING), `tests/unit/test_lifecycle_reconciliation.py` (EXISTING), `tests/unit/test_lifecycle_reconciliation_store.py` (EXISTING), `tests/unit/test_lifecycle_set_sync.py` (EXISTING), `tests/unit/test_lifecycle_set_sync_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-019, AT-NR-024, AT-NR-025, AT-NR-027, AT-NR-028, AT-NR-029, AT-NR-030, AT-NR-033, AT-NR-034, AT-NR-040, AT-NR-044, AT-NR-045, AT-NR-046, AT-NR-049, AT-NR-076, AT-NR-081, AT-NR-099, AT-NR-100, AT-NR-101, AT-NR-102, AT-NR-103, AT-NR-104, AT-NR-105, AT-NR-106, AT-NR-107, AT-NR-108, AT-NR-109, AT-NR-110, AT-NR-111, AT-NR-112, AT-NR-113, AT-NR-114, AT-NR-115, AT-NR-116, AT-NR-117, AT-NR-133, AT-NR-135, AT-NR-142, AT-NR-143, AT-NR-144, AT-NR-146, AT-NR-148, AT-NR-151, AT-NR-152.

AT-NR-152 cases01–10/12 and all operational L01–L34 rows/§40 questions run locally through actual source/native fact and PostgreSQL paths; case11 financial evidence remains B10. Run NR-151 B9 portions of cases03/06/08/09/10/11/12 through the separate Portfolio projection. Explicitly test fixed-arrival count-once versus genuinely new duplicate arrivals, post-intent fill versus merely delayed old fill, distinct receipt/consumption/publication/proof cutpoints, and immutable history after convergence.

R6 source portions of ENTRY-RPT-05–07/10–11/14–15 and TP-RPT-08–13/17: exact submitted/accepted/positive/full/terminal-zero-fill membership, hard refusal distinct from capital/geometry/parser/unavailable outcomes, original time comparability, post-fill boundaries and no report authority. Validate actual owner records and retained source proofs; B10 supplies permanent FINAL, B12 assembles reports. The existing NR-151/152 cases remain unchanged.

**NEGATIVE_BOUNDARY_TESTS:**

No auth, incompatible hard spec, missing native profile/current field proof, generic status overwriting proven fill, blind replacement protection, guessed tranche/source slices, allocation before manifest, replay under reused source or simultaneous competing close.

Reject economic dedupe as proof of duplicate-arrival history, latest-cutpoint-only latency history, filled quantity inferred from a count, premature sibling confirmation, terminal-effective-time substituted for publication, terminal no-create fabricated as a native-use intent, and a manual diagnostic used as release/finality authority. No Portfolio or Lifecycle diagnostic may fetch foreign mutable state to bypass a contract.

**REPLAY_RESTART_TESTS:**

RP-LOCAL plus side-effect-before-ack restart, uncertain child authority, terminal placement reorder, stale/historical acceptance conflict, manifest/allocation reorder and native-observation changed lower revision. Same native IDs/intents/receipts retained.

NR-152 replay retains capture/classification identity and original order basis, attempts, auth cuts, terminal publication, sibling cleanup, races, recovery corrections and manual observations. The same captured instance counts once; an actual extra arrival is a separate observation with zero repeated economics. NR-151 Portfolio projection histories restore original events/times/reasons without restarting cooldown or changing retained commitment.

Report-source membership reuses existing business/native execution IDs and original accepted chronology, not physical arrival counts. All actual fill/refusal/terminal evidence survives restart and remains reconstructible for a failed later Research import. No report source omission is repaired by latest status or a fake zero-fill.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; ADVERSARIAL_TRADING_REVIEW; API_PROVENANCE_REVIEW; CONTRACT_REVIEW; TEST_REVIEW; NUMERIC_PRECISION_REVIEW

**R6 NR-153/154 local scope:** Existing implementation/provenance/numeric/persistence/replay/test reviews cover actual execution/refusal/time/coverage and exact report lineage (§10.5); existing adversarial/contract reviews prove unchanged native authority, quantities and API graph. No new token or business action.

**Local NUMERIC_PRECISION_REVIEW scope:** Review exact source partitions, source quantity conservation and allocation slices; residual reduction quantity; confirmed_target_quantity, executed_reduction_quantity, confirmed_residual_quantity and authorized_reduction_quantity; and unresolved/uncertain child authority budgets. Verify exact pre-close liability apportionment where B9 participates in factual transitions, preserving the existing Portfolio-owned projection and the approved H basis in §8.2. Reject negative-residual clamping, binary float, epsilon comparisons and silent quantity repair. This review covers B9's existing native-quantity and factual-transition scope only: B10 financial logic remains in B10, and source partition, single close authority and native execution semantics are unchanged.

**NR-151/NR-152 local review responsibilities:** Existing IMPLEMENTATION_REVIEW and TEST_REVIEW cover every assigned observation/§40 visibility path; PERSISTENCE_TRANSACTION_REVIEW verifies capture/history/state/outbox membership and no cross-owner writes; REPLAY_IDEMPOTENCY_REVIEW distinguishes economic receipts from captured-arrival observations and restores original timestamps/counts/bases; ADVERSARIAL_TRADING_REVIEW checks ambiguity, manual actions, cancellation/close races and denied/proven terminal Portfolio projections; API_PROVENANCE_REVIEW validates actual native/source/time/ordering evidence; NUMERIC_PRECISION_REVIEW covers exact fill ratios/member sums, Portfolio pre-close H apportionment and non-authoritative timing/utilization projections; CONTRACT_REVIEW confirms unchanged messages/directions. Financial component/finality observation review remains with the actual B10 producer. No new reviewer token or accounting owner is created.

**UPSTREAM_DEPENDENCIES:**

B8C, B6, B3

**DOWNSTREAM_DEPENDENTS:**

B10, B11, B12

**DEFINITION_OF_DONE:**

Existing Lifecycle handler and Set/Portfolio return/projection paths satisfy local native/provenance/transaction/replay tests. No native exposure authority from unverified profile and no filled-tranche FINAL/CLOSED until B10 complete.

All applicable NR-151 Portfolio-return and NR-152 operational producers/history/visibility tests are locally complete and reviewed. B10 monetary/FINAL/receipt observability is still future integration, not manufactured in B9.

The Lifecycle factual inputs assigned to both required reports are retained and tested locally before downstream assembly. Completed reporting paths still require B10’s true permanent outcome/horizon and B12’s read-only consumer.

**RISKS:**

Stable ID alone does not prove safe native create; historical child mapping is not current protection; receipt dedupe alone is not source quantity conservation.

**DO_NOT:**

Do not reprice spec, recompute Position formulas, duplicate sync/close/outbox, infer attribution, cancel filled exposure through F-013 or convert zero-fill/no-create into fake FINAL.

## B10 — Financial finality and separate Portfolio receipt integration

**PRIORITY:**

P1

**PURPOSE:**

Implement Lifecycle-owned A-004/A-002/S-004 and the separate Portfolio receipt/economic-day/A-009/release transaction.

**NORMATIVE_REQUIREMENTS:**

NR-016, NR-024, NR-026, NR-027, NR-028, NR-029, NR-031, NR-032, NR-033, NR-034, NR-043, NR-046, NR-049, NR-050, NR-051, NR-116, NR-118, NR-119, NR-120, NR-121, NR-122, NR-123, NR-124, NR-125, NR-126, NR-127, NR-128, NR-129, NR-130, NR-131, NR-132, NR-133, NR-134, NR-135, NR-147, NR-148, NR-151, NR-152, NR-153, NR-154

**HISTORICAL_TRACEABILITY_ALIASES:**

R013, R015, R016, R017, R018, R020, R021, R027, R030, R031, R043, R044, R045, R046, R047, R048

**EXISTING_FOUNDATION_REUSED:**

FN.RECON, FN.CLOSE, FN.PORT, FN.MSG, FN.UOW, FN.FACT, FN.API, FN.JSON, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

PARTIAL evidence infrastructure; canonical FINAL/receipt integration absent; SQLite accounting is legacy [E48–E51; audit §26]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Lifecycle immutable financial terminal result and separate Portfolio own receipt/day/A-009/release are fully integrated and incident-fenced.

NR-151 terminal Portfolio history and NR-152 actual financial/terminal Lifecycle observation projections are completed alongside those separate owner transactions, never as additional financial authorities.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.RECON: Lifecycle reconciliation/events — `src/triggertrade/persistence/lifecycle_reconciliation_store.py::LifecycleReconciliationStore` (inventory L63); `src/triggertrade/persistence/lifecycle_order_event_store.py::LifecycleOrderEventStore` (inventory L38); EXTEND under §2 classification.

FN.CLOSE: LifecycleCloseAuthorityStore — `src/triggertrade/persistence/lifecycle_close_authority_store.py::LifecycleCloseAuthorityStore` (inventory L74); src/triggertrade/lifecycle_close_authority.py; EXTEND under §2 classification.

FN.PORT: Portfolio state/buckets — `src/triggertrade/persistence/portfolio_state_store.py::PortfolioStateStore` (inventory L26); src/triggertrade/portfolio_state.py; EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.FACT: Existing factual stores — `src/triggertrade/persistence/market_data_fact_store.py::MarketDataFactStore` (inventory L35); `src/triggertrade/persistence/portfolio_data_facts.py::PortfolioDataFactStore` (inventory L38); EXTEND under §2 classification.

FN.API: Factual API normalization — src/triggertrade/api_adapter_gateway/market_data.py; src/triggertrade/api_adapter_gateway/portfolio_data.py; src/triggertrade/api_adapter_gateway/order_management.py; EXTEND under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED Lifecycle-owned src/triggertrade/accounting/finality.py and funding/source helpers if absent, plus missing canonical financial/coverage/result and Portfolio receipt records. All under existing PostgreSQL owner transactions, no separate Accounting service.

**LEGACY_SURFACES_TO_FENCE:**

FuturesAccountingStore, DailyLossStore and futures_accounting_bridge stay LEGACY_ONLY where incompatible. Pure helpers require semantic equivalence proof before reuse.

**PERSISTENCE_ACTION:**

MIXED

**PERSISTENCE_DETAILS:**

Logical records: ST.financial, ST.coverage, ST.funding, ST.final, ST.receipts, ST.day, ST.incidents, ST.frontier, ST.close, ST.portfolio. Exact action, uniqueness/history and transaction roles are defined in §6. Reuse compatible existing stores; a NEW logical obligation does not imply one table or a new repository per row.

NR-151 additionally retains Portfolio ST.grants/ST.holds terminal-resolution/release observations and original ST.portfolio episode history with ST.receipts/day evidence. NR-152 reuses the same ST.financial/ST.coverage/ST.funding/ST.final and ST.reconcile/transport capture histories; no separate fee/P&L diagnostic ledger or replacement FINAL.

NR-153/154 reuse the original owner histories under §6.4.3/§7.7 and expose exact immutable read-only source membership. No second report/financial/quantity ledger is created in this owner. Research archival/assembly remains separately owned SQLite documentary persistence, not a cross-owner commit.

**TRANSACTION_BOUNDARIES:**

TX.frontier, TX.facts, TX.native, TX.preflight, TX.protection, TX.partition, TX.day, TX.receipt, TX.hold, TX.closeretention, TX.acceptance, TX.incident, TX.final, TX.grant, TX.construction, TX.funding, TX.cashflow, TX.owner, TX.close; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

ORDER_MANAGEMENT v4 financial factual request/response; ORDER_EVENT v7 FINAL/integrity production and separate Portfolio consumption.

**IDENTITY_BINDINGS:**

request_id; response_id / snapshot_id / page_id; cashflow_id / proven source aliases; Non-funding financial allocation identity/receipt; Funding allocation identity/receipt; Accepted coverage certificate key / accepted_certificate_revision; Factual-basis/source-set and allocation proof revision; result_id / terminal result-tranche binding; Portfolio receipt / first delivered_at; incident_id / incident_revision; Committed-prefix technical scope/head/applied sequence

**NUMERIC_REQUIREMENTS:**

Exact factual execution sums and signed component semantics; source-specific non-funding quantum vs q18 funding with full signed residue; no Qratio gate, arbitrary cents rounding, or economics rebuilt from reports.

**IMPLEMENTATION_SCOPE:**

Retain full raw immutable financial core/aliases, current accepted source sets, Y02 coverage histories/indexes, exact execution-derived gross/cost basis and non-funding source-quantum allocation. A-004 uses effective-time eligibility and its separate q18 signed residue algorithm. Recheck current source/closure revision vector and all six S-004 predicates in Lifecycle terminal UoW; establish resolved close intent, immutable FINAL, CLOSED/terminalized_at and final ORDER_EVENT together. Portfolio separately serializes committed-prefix merge, first result/tranche receipt/delivered_at, historical economic-day post, A-009 state and once-only release. Post-final challenges create independent incident/parent links, never replacement money.

Complete NR-152 L35–L40 and the terminal qualifications for close-frequency/§40 visibility from the actual retained source allocations and immutable FINAL. Apply the same captured-arrival/known-evidence rules to financial intake without weakening preflight. In Portfolio's separate receipt/recovery path, complete NR-151 grant-terminal-resolution, actual once-only release, historical day/latch and reconciliation timing/reason observations. Do not rewrite the immutable grant, native result or prior diagnostic history to mark current success.

R6 NR-153/154 outcome source: expose the same immutable full-tranche FINAL result/tranche identity, governed currency/net and permanent closing-execution ID/order/accounting_effective_at for read-only expectancy and completed path horizons. Research uses exact original links only; it never writes a final result, duplicates financial posting, substitutes a Portfolio receipt time or makes B10 recompute Entry/TP. Report copies can retry after this owner commit without changing FINAL or release.

**TESTS_REQUIRED:**

Actual canonical PG allocation/finality/receipt tests, all currencies/signs/coverage and funding conservation, every six-predicate failure, temporary zero vs final execution chronology, DST/historical late receipt, A-009 threshold/latch, component-parent incidents, preflight malformed companions and both incident/receipt commit orders.

Existing regression examples (non-exhaustive): `tests/contract/test_canonical_json_contract.py` (EXISTING), `tests/contract/test_lifecycle_start_gate_contracts.py` (EXISTING), `tests/integration/test_bybit_demo_futures_lifecycle_smoke.py` (EXISTING), `tests/unit/test_canonical_json.py` (EXISTING), `tests/unit/test_futures_accounting.py` (EXISTING), `tests/unit/test_futures_position_lifecycle.py` (EXISTING), `tests/unit/test_lifecycle_close_authority.py` (EXISTING), `tests/unit/test_lifecycle_close_authority_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-016, AT-NR-024, AT-NR-026, AT-NR-027, AT-NR-028, AT-NR-029, AT-NR-031, AT-NR-032, AT-NR-033, AT-NR-034, AT-NR-043, AT-NR-046, AT-NR-049, AT-NR-050, AT-NR-051, AT-NR-116, AT-NR-118, AT-NR-119, AT-NR-120, AT-NR-121, AT-NR-122, AT-NR-123, AT-NR-124, AT-NR-125, AT-NR-126, AT-NR-127, AT-NR-128, AT-NR-129, AT-NR-130, AT-NR-131, AT-NR-132, AT-NR-133, AT-NR-134, AT-NR-135, AT-NR-147, AT-NR-148, AT-NR-151, AT-NR-152.

AT-NR-152 case11 uses actual signed source components and exact gross20/net18.9 fixture expectations, A-004 basis and complete source/coverage/currency checks; cases01–03/10/12 also cover financial capture/recovery. NR-151 cases03/07/09/10/11/12 verify original first receipt/release/terminal-resolution and day/reconciliation history through real Lifecycle→Portfolio flow. All source-required monetary and close metrics remain unavailable as full FINAL until existing completeness predicates pass.

R6 final-source portions of ENTRY-RPT-13–15 and TP-RPT-08–13/17: actual full-tranche result/currency/chronology binding, temporary flatness versus permanent close, missing FINAL stays incomplete, result alias/retry not duplicate expectancy membership, immutable source after failed Research import. Preserve actual A-002/A-004/A-009/S-004 tests and existing gross20/net18.9 oracle unchanged.

**NEGATIVE_BOUNDARY_TESTS:**

Empty rows without COMPLETE proof, foreign required source even net-zero, source rounding or wrong allocator, planned price/fee as factual, stale proof before commit, physical flatness, Lifecycle-created Portfolio receipt, result_id-exists shortcut release, duplicate wallet credit and SQLite+PG pseudo-transaction.

Do not build entry/exit fee diagnostics from planned rates, substitute a component FINAL for a full-tranche result, treat a diagnostic grant closed_at as release authority, count a replayed result again, label C−H as money released at acceptance, or fill missing history from current wallet/equity.

**REPLAY_RESTART_TESTS:**

RP-LOCAL at source acceptance, all allocation recipients, terminal writes/outbox, receipt/day/release and frontier cutpoints. Restore full accepted proof histories before ingestion; identical FINAL once, changed content separate incident, already applied receipt never reversed/reposted.

Restore the same source/alias/allocation/FINAL basis and Portfolio own first receipt/release/episode history. A repeated captured financial arrival may have one diagnostic duplicate observation but zero new source posting; same capture retry adds neither. An actual post-final challenge remains a separate incident, not a replacement diagnostic economic result.

Old report references continue to resolve the exact original immutable FINAL and permanent chronology after restart or newer evidence. No report backfill edits the original result or supplies a component/legacy result as full-tranche evidence.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; CONTRACT_REVIEW; TEST_REVIEW

**R6 local outcome scope:** Existing ACCOUNTING_FINALITY_REVIEW and NUMERIC_PRECISION_REVIEW verify original FINAL net/currency and permanent path-end chronology for reports; implementation/test/persistence/replay/contract reviews verify immutable read-only lineage and no extra financial/receipt authority (§10.5). Factual acquisition/provenance review remains at the actual B3/B9 producers, not newly introduced public-feed acquisition here.

**NR-151/NR-152 local review responsibilities:** Existing ACCOUNTING_FINALITY_REVIEW checks actual fee/rebate/funding/gross/net observation basis, current source coverage, immutable FINAL, separate historical Portfolio receipt/day/release and grant-terminal-resolution history. NUMERIC_PRECISION_REVIEW checks exact component signs, conserved source allocations, copied H and actual release/never-held-surplus separation without another quantizer. PERSISTENCE_TRANSACTION_REVIEW and REPLAY_IDEMPOTENCY_REVIEW check same-owner capture, immutable history and once-only economics/observations; IMPLEMENTATION_REVIEW and TEST_REVIEW cover every assigned row/case. CONTRACT_REVIEW forbids a new result/receipt/diagnostic wire authority. These are local additions to existing review scope, not duplicate review tokens.

**UPSTREAM_DEPENDENCIES:**

B9, B8A, B8C, B2

**DOWNSTREAM_DEPENDENTS:**

B11, B12

**DEFINITION_OF_DONE:**

Both owner-local transactions and actual A-009 producer→consumer integration pass independent accounting/numeric/contract/transaction/replay/test gates. All applicable current financial/quantity proof is represented; zero-fill/no-create remain separate; no production native authority is implied.

Every NR-151/NR-152 B10 observation has its exact retained owner basis, source-derived acceptance and existing accounting/numeric/persistence/replay/contract/test review. B11/B13 verify these histories; they do not first capture them.

Both reports’ canonical financial-outcome and permanent-horizon source inputs are locally retained/tested with the existing FINAL path. B12 assembles diagnostic means/paths from them; B13 does not first produce the source data.

**RISKS:**

Terminal result, six-predicate closure and Portfolio receipt are three distinct authorities; legacy partial-close/UTC day logic can silently corrupt them.

**DO_NOT:**

Do not introduce a fifth owner, relabel SQLite results, invent equity/drawdown objects, perform FX, use funding allocator for non-funding sources, mutate FINAL or release before clear fenced receipt.

## B11 — Integrated replay, restart and concurrency hardening

**PRIORITY:**

P2

**PURPOSE:**

Stress already-correct owner-local semantics before canonical dispatcher activation.

**NORMATIVE_REQUIREMENTS:**

NR-136, NR-151, NR-152 (NR-151/NR-152 verification only; production remains B8A/B8B/B8C/B9/B10).

NR-153/154 verification of already implemented source capture and B3 diagnostic manifest persistence only; their complete report assembly is B12, not a reverse B11 dependency.

**HISTORICAL_TRACEABILITY_ALIASES:**

R049

**EXISTING_FOUNDATION_REUSED:**

FN.UOW, FN.MSG, FN.TEST; see §2 for exact components and preservation action.

**CURRENT_STATE:**

Infrastructure tests exist; full owner replay not proven by supplied evidence [E23,E31–E32; audit §§28,32]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Already locally correct handlers withstand integrated restart/reorder/concurrency without authority/economic duplication.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW tests/integration/test_canonical_replay_restart.py and test_canonical_concurrency.py if equivalent existing suites cannot be extended. Test orchestration is not a new runtime.

**LEGACY_SURFACES_TO_FENCE:**

No fallback to legacy during stress/recovery.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

TX.owner, TX.preflight, TX.facts, TX.scope, TX.day, TX.setcalc, TX.set, TX.monitor, TX.opportunity, TX.grant, TX.construction, TX.hold, TX.native, TX.acceptance, TX.placement, TX.protection, TX.cancel, TX.close, TX.closeretention, TX.partition, TX.cashflow, TX.funding, TX.final, TX.incident, TX.receipt, TX.frontier; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

All 12 through their actual owner/technical boundaries; no new contracts.

**IDENTITY_BINDINGS:**

Full §7.5 graph, unchanged; no new identity ownership.

**NUMERIC_REQUIREMENTS:**

Exact equality of accepted canonical values and conservation, not floating tolerances or approximate PnL comparisons.

**IMPLEMENTATION_SCOPE:**

Run interleaved actual owner interfaces with real PostgreSQL and deterministic native factual stubs across all transaction boundaries. Exercise reorder, redelivery, crash, concurrent holds/close/cancel/finality/incident publication and process recovery. Any exposed defect reopens its owning implementation checkpoint with the same reviews; B11 is not first implementation of identity/atomicity.

**TESTS_REQUIRED:**

All RP-LOCAL suites remain green; full replay produces identical canonical accepted outcomes/bytes where required, exact conserved quantities/money and same terminal/incident/receipt histories across permitted delivery schedules.

Existing regression examples (non-exhaustive): `tests/contract/test_lifecycle_start_gate_contracts.py` (EXISTING), `tests/integration/test_bybit_demo_futures_lifecycle_smoke.py` (EXISTING), `tests/unit/test_durable_messages.py` (EXISTING), `tests/unit/test_futures_position_lifecycle.py` (EXISTING), `tests/unit/test_lifecycle_close_authority.py` (EXISTING), `tests/unit/test_lifecycle_close_authority_store.py` (EXISTING), `tests/unit/test_lifecycle_order_event_store.py` (EXISTING), `tests/unit/test_lifecycle_order_events.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-136, AT-NR-151, AT-NR-152.

Include AT-NR-068-CF across actual Set paths and full AT-NR-151/152 observation-history stress. Replay the same captured inputs to prove identical retained diagnostic results; when the test deliberately introduces genuinely new physical arrivals, verify the corresponding additional observations while economic effects remain once-only. No missing observation producer may be invented at B11; reopen its original checkpoint.

R6 source-history stress replays B3/B7A/B9/B10 documentary inputs/owner records across failed imports and restarts, checking original RPT-* lineage, manifest members and no fabricated missing data. It does not call not-yet-implemented B12 report assembly or require a report result to close a canonical owner checkpoint.

**NEGATIVE_BOUNDARY_TESTS:**

Fault after native effect before acknowledgement, conflicting older accepted revision, incomplete prefix, last-slot contention, partial-fill/cancel and finality/source change races. Unavailable PG/native evidence is reported, not silently skipped as pass.

**REPLAY_RESTART_TESTS:**

This checkpoint is the integrated RP-STRESS suite; its input and expected invariants are independent of implementation outputs and use original pinned evidence.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; PERSISTENCE_TRANSACTION_REVIEW; TEST_REVIEW

**NR-151/NR-152 verification scope:** Existing persistence/replay/implementation/test reviews verify completed local capture under interleaving, crash and retention/hydration, including denied outcomes, same-capture count-once and truthful different-arrival counts. No new producer or reviewer type.

**UPSTREAM_DEPENDENCIES:**

B5B, B6, B7A, B8B, B7B, B8C, B9, B10

**DOWNSTREAM_DEPENDENTS:**

B12

**DEFINITION_OF_DONE:**

No unreviewed owner replay/transaction defect remains; integrated schedules/cutpoints are recorded, and all applicable local reviews remain valid after fixes.

All assigned history/duration/diagnostic projections remain reconstructible after stress; correct terminal economics with missing required observations is not a passing B11 result.

All R6 report-source and diagnostic dataset evidence is recoverable under stress; complete report-function acceptance is explicitly B12. No new producer or canonical state is added at B11.

**RISKS:**

Stress tests that merely replay generated expected outputs can falsely validate a shared bug.

**DO_NOT:**

Do not weaken frozen expected behavior or add first-time owner semantics here without reopening the original checkpoint.

## B12 — Canonical dispatch and independently gated native authority

**PRIORITY:**

P1

**PURPOSE:**

Wire complete owners through the one existing worker/process path only after all prerequisites and current evidence gates pass.

Additionally complete the existing technical diagnostics/ResearchService read-only Entry/TP report assembly before B13, using already-retained B3/B7A/B9/B10 evidence. This is a separate code path from canonical message dispatch and native authority.

**NORMATIVE_REQUIREMENTS:**

NR-001, NR-019, NR-020, NR-137, NR-138, NR-139, NR-153, NR-154

**HISTORICAL_TRACEABILITY_ALIASES:**

R006, R007, R008, R009, R017, R029, R032, R046, R048, R050, R057, R058, R059, R060

**EXISTING_FOUNDATION_REUSED:**

FN.RUNTIME, FN.MSG, FN.UOW, FN.NATIVE, FN.TEST; see §2 for exact components and preservation action.

R6 adds FN.RESEARCH and existing analytics/historical-evidence interfaces to this technical reporting scope; no new runtime or second Research subsystem.

**CURRENT_STATE:**

Canonical worker intentionally blocks owner messages; launcher fences already exist [E23–E25]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

R6: current ResearchService/analytics/ResearchStore can hold pins and aggregate metrics but lacks complete Entry/TP reports. B3 establishes diagnostic source/archive/manifest persistence; B7A/B9/B10 implement authoritative report-source facts. None of these future checkpoints is claimed executed by this map.

**TARGET_STATE:**

One canonical dispatcher routes only ready owners while unknown/incomplete/native-uncertified paths remain blocked.

Both complete NR-153/154 read-only reports and explicitly pinned diagnostic sensitivity are implemented and locally reviewed in existing ResearchService/analytics, with immutable same-SQLite ResearchStore results and correct unavailability. Canonical dispatch performs no report calculation and consumes no report output.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.RUNTIME: Launcher/one worker/process roles — src/triggertrade/services/runtime.py; src/triggertrade/services/trading_worker.py; src/triggertrade/services/process_roles.py; EXTEND under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.NATIVE: Native factual profile boundary — src/triggertrade/api_adapter_gateway/native_profile.py; EXTEND under §2 classification.

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

R6 actual surfaces: `src/triggertrade/services/research.py`, existing `src/triggertrade/analytics/` package (`futures.py` only for compatible helpers), `src/triggertrade/persistence/research_store.py`, `src/triggertrade/research_pins.py`, and existing read-only dashboard/research presentation. Missing report functions may be organized in a CONDITIONAL_NEW module inside existing analytics after equivalence/absence check; it is not another formula runtime or worker. B3 diagnostic archive interfaces and B7A owner-local retained records are reused, not rewritten.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW src/triggertrade/services/owner_dispatch.py only as registration/wrapper inside existing TargetTradingWorker; never a second worker or formula-only runner.

**LEGACY_SURFACES_TO_FENCE:**

Keep canonical launcher paper/spot rejection and no legacy/demo/accounting fallback.

**PERSISTENCE_ACTION:**

NONE for canonical dispatch. EXTEND/REUSE existing ST.research within the same SQLite ResearchStore for NR-153/154 diagnostic report/member records; no canonical persistence creation, new store or migration to PostgreSQL.

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

R6 diagnostic exception to the preceding canonical-persistence paragraph: implement immutable report result/member publication in the same SQLite ResearchStore (§6.4.10). Reuse B3 manifests and retained source objects. No new canonical state/table/UoW/ledger, no OperatorStateStore migration and no promotion-governance scope change. Report persistence has no business authority.

**TRANSACTION_BOUNDARIES:**

TX.owner, TX.facts, TX.native; exact mechanism and tests in §7.

R6 report generation reads immutable owner evidence and uses independent ResearchStore-local SQLite transactions (§7.7); it is not another canonical TX and is not atomic with source-owner/native effects. Existing dispatch transaction requirements above are unchanged.

**CONTRACTS_TOUCHED:**

All 12 only on the exact graph; dispatch is business-owner routing plus existing factual API boundary, not a fifth decision owner.

R6 report composition adds no business contract, field, version or direction; existing read-only diagnostic presentation consumes immutable report data outside the canonical message graph.

**IDENTITY_BINDINGS:**

Full §7.5 graph, unchanged; no new identity ownership.

R6 internal report/dataset identities bind exact definition/query/configuration/source-manifest content under existing research pin/digest helpers. They never become business/wire identity creators; §7.5 remains unchanged.

**NUMERIC_REQUIREMENTS:**

Dispatcher performs no formula calculation; it delegates exact owner results through existing contracts.

Separate R6 analytics functions (not dispatcher handlers) apply §6.4 exact report arithmetic, canonical age copy, raw/rounded distance preservation, rational cohorts/means, direction-aware path extrema and truthful interval timing. Isolated sensitivity reuses reviewed pure selection with explicit Research-only parameters; it cannot change canonical thresholds or output types.

**IMPLEMENTATION_SCOPE:**

Verify every §11 activation prerequisite, including independent acceptance of this R6 plan and FA-R5-01 correction in §16, including locally complete NR-151/NR-152 observation capture, all B0–B11 checkpoint evidence, twelve strict parser contracts, local replay, current hard/native/financial paths, Portfolio receipt/frontier and twenty invariant implementation evidence. Replace handler_not_certified blocking only for complete registered owner routes. Add readiness/diagnostics/process roles and source-defined scheduling duties. Unknown/incomplete routes stay blocked; actual native exposure remains independently gated by certified profile/current facts and applicable operator/runtime authority.

R6 technical reporting: implement all §6.4 Entry/TP cohort/member/distance/reason/age/outcome/path/type comparisons and separate explicit min/max diagnostic sensitivity in existing ResearchService/analytics. Publish immutable report pins/content/members/availability through the same ResearchStore, with no latest/mutable-owner query shortcut, backtest-simulator fallback or automatic run selection/promotion. Reuse original actual source history; a missing source or experiment parameter remains explicit unavailable/incomplete. Keep report code unable to call native adapters, business writers or promotion methods. Report source completeness is not a new live trading gate; current unknown/incomplete canonical routes remain governed by the original activation conditions.

**TESTS_REQUIRED:**

Existing worker/runtime/roles/diagnostics and module-boundary regressions, actual dispatcher E2E, transaction rollback, unknown/incomplete handler, missing dependency/profile, observation/reconciliation while native creation is disabled.

Existing regression examples (non-exhaustive): `tests/contract/test_module_boundaries.py` (EXISTING), `tests/unit/test_backend_diagnostics.py` (EXISTING), `tests/unit/test_container_runtime.py` (EXISTING), `tests/unit/test_dual_lane_runtime.py` (EXISTING), `tests/unit/test_futures_runtime_integration.py` (EXISTING), `tests/unit/test_paper_runtime.py` (EXISTING), `tests/unit/test_postgres_runtime_store.py` (EXISTING), `tests/unit/test_process_roles.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-001, AT-NR-019, AT-NR-020, AT-NR-137, AT-NR-138, AT-NR-139.

R6 full AT-NR-153 ENTRY-RPT-01–15 and AT-NR-154 TP-RPT-01–17 plus §6.4.13 through actual read-only ResearchService/analytics and real existing SQLite ResearchStore extensions. Verify 19/19 and17/17 source rows, exact cohorts/pins/member IDs, initial reject evidence, immutable source/FINAL linkage, missing path versus zero, OHLC chronology limitations, explicit alternative research parameters, independent rational oracles and no canonical feedback. Existing owner source tests are prerequisites, not replaced by report mocks. E2E includes the existing read-only report presentation; B13 repeats integrated verification.

**NEGATIVE_BOUNDARY_TESTS:**

An all-handlers-loaded flag bypassing native profile/financial gates; dispatch after only B0 metadata update; worker-level formula calculation; silent scheduler TTL or alternate demo route.

R6 report negatives: report/source IDs acquiring trade authority, latest ATR/configuration/type lookup, closed-P&L proxy for path, pre-entry/after-close touch, unvisited candidates counted as visited, denominator made only from successes, native POST_ONLY prediction, report-triggered live block, silent sweep defaults, changed canonical thresholds, automatic promotion, cross-database atomicity or a separate worker.

**REPLAY_RESTART_TESTS:**

Claim/inbox/handler outcome/outbox acknowledgement preserves existing atomic semantics; crash and restart dispatch never duplicates completed owner/native effect.

Same complete report pins/manifest produce the same member sets/values/status/report identity and original generated_at metadata. Fault before/after SQLite report commit and retry source import; restore original archive objects/configs before calculation. New path/FINAL evidence or different sweep has a new report identity only. Physical arrival history may differ under NR-152 without changing business-member metrics.

**MANDATORY_REVIEW_GATES:**

IMPLEMENTATION_REVIEW; ARCHITECTURE_CONFORMANCE_REVIEW; REPLAY_IDEMPOTENCY_REVIEW; TEST_REVIEW; E2E; NUMERIC_PRECISION_REVIEW; ADVERSARIAL_TRADING_REVIEW; PERSISTENCE_TRANSACTION_REVIEW

**R6 local reporting scope:** §10.5 assigns all complete report/source/SQLite/isolation responsibilities. The three added categories are existing reviewer types, applied only to quantitative diagnostic assembly, no-feedback protection and local documentary persistence; dispatcher formula logic is still forbidden. Central G-B12 matches this list without duplicate tokens.

**UPSTREAM_DEPENDENCIES:**

B0, B1, B2, B3, B4, B8A, B5A, B5B, B6, B7A, B8B, B7B, B8C, B9, B10, B11

**DOWNSTREAM_DEPENDENTS:**

B13

**DEFINITION_OF_DONE:**

One gated canonical dispatcher passes E2E and independent implementation/architecture/replay/test review. Readiness explicitly separates dispatch capability from native exposure permission; B13/B14 remain required.

Both complete Entry/TP report capabilities, exact pins/source/member/path availability and explicitly configured sensitivity pass their local quantitative/persistence/replay/isolation tests and independent reviews before B13. A particular report may correctly be unavailable; no future live outcome is required to authorize an otherwise valid trade. No canonical geometry/native authority is produced by report assembly.

**RISKS:**

Removing a single worker blocker can accidentally expose all incomplete/native-uncertified paths.

**DO_NOT:**

Do not equate dispatch readiness with permission for native trading or bypass any blocked unknown/current-proof path.

## B13 — Full integrated verification and isolation

**PRIORITY:**

P2

**PURPOSE:**

Verify the actual integrated dispatch/backend against every source-based requirement, all objects/contracts and global invariants.

**NORMATIVE_REQUIREMENTS:**

All 154 normalized groups NR-001–NR-154; source-specific local obligations remain in §3. NR-151/NR-152 map frozen owner observations; NR-153/NR-154 map required frozen Entry/TP reports with explicit diagnostic definitions in §6.4. No methodology addition is claimed. B13 verifies and B14 independently audits all of them.

**HISTORICAL_TRACEABILITY_ALIASES:**

R001–R060 (all HISTORICAL_TRACEABILITY_ALIAS).

**EXISTING_FOUNDATION_REUSED:**

FN.TEST, FN.RUNTIME, FN.RESEARCH, FN.LEGACY, FN.LEGACC, FN.LEGDAY; see §2 for exact components and preservation action.

**CURRENT_STATE:**

Existing isolation/tests reusable; full canonical execution not proven [E23–E25,E52; audit §§31–34]. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

All required integrated tests/graph/objects/contracts/invariants have explicit current evidence; no hidden skipped scope.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

FN.RUNTIME: Launcher/one worker/process roles — src/triggertrade/services/runtime.py; src/triggertrade/services/trading_worker.py; src/triggertrade/services/process_roles.py; EXTEND under §2 classification.

FN.RESEARCH: Research pins/isolation/governance — `src/triggertrade/research_pins.py::research_pin_payload` (existing helper, REUSE); `src/triggertrade/persistence/research_store.py::ResearchStore` (existing SQLite research persistence); `src/triggertrade/persistence/operator_state_store.py::OperatorStateStore` (existing SQLite operator-state persistence); `src/triggertrade/persistence/research_promotion_governance.py::ResearchPromotionGovernanceStore` (existing PostgreSQL promotion-request / outbox governance only); ADAPT under §2 classification.

FN.LEGACY: Legacy triggers/demo precision/spot/paper/S-005 — src/triggertrade/triggers/percentage_price_move.py; src/triggertrade/triggers/volume_confirmation.py; src/triggertrade/execution/precision.py; src/triggertrade/execution/paper.py; src/triggertrade/execution/bybit.py; src/triggertrade/strategies/futures_directional.py; src/triggertrade/market_data/regime.py; FENCE under §2 classification.

FN.LEGACC: Legacy accounting and bridge — src/triggertrade/accounting/futures.py; src/triggertrade/persistence/futures_accounting_store.py; src/triggertrade/services/futures_accounting_bridge.py; FENCE under §2 classification.

FN.LEGDAY: Legacy DailyLossEvaluator/DailyLossStore — src/triggertrade/services/daily_loss.py; src/triggertrade/persistence/daily_loss_store.py; FENCE under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

CONDITIONAL_NEW tests/e2e/test_v1_2_15_canonical_backend_flow.py and test_v1_2_15_fail_closed.py; extend existing coverage first.

**LEGACY_SURFACES_TO_FENCE:**

Full legacy/demo/S-005 and SQLite-authority reachability tests; retain useful isolated behavior rather than deleting for appearance.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

TX.owner, TX.preflight, TX.facts, TX.scope, TX.day, TX.setcalc, TX.set, TX.monitor, TX.opportunity, TX.grant, TX.construction, TX.hold, TX.native, TX.acceptance, TX.placement, TX.protection, TX.cancel, TX.close, TX.closeretention, TX.partition, TX.cashflow, TX.funding, TX.final, TX.incident, TX.receipt, TX.frontier; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

All 12 and all governed variants/directions, integrated verification only.

**IDENTITY_BINDINGS:**

Full §7.5 graph, unchanged; no new identity ownership.

**NUMERIC_REQUIREMENTS:**

Exact independent formula/accounting outputs; no tolerance or report value substitutes; S-005 diagnostic only.

**IMPLEMENTATION_SCOPE:**

Execute §12 V-FULL with actual dispatcher, real isolated PostgreSQL, complete contract fixtures and source-derived expectations. Review full owner graph, all eighteen objects, numeric exactness, native/profile refusal, source allocation, finality/receipt/day/frontier and twenty invariants. Preserve foundation regressions and report all excluded/unavailable native/deployment evidence explicitly.

**TESTS_REQUIRED:**

Full applicable suite plus Set→Position→Portfolio→Lifecycle and Lifecycle→Set return, both F-013 causes, ambiguous create, partial-fill/cancel, current protection, source partition, both allocation algorithms, immutable FINAL, six predicates, A-009 historical day and incident orderings. Explicitly include AT-NR-053 A–H through the existing Set/dispatcher path for both direction scopes, bypass/conflict negatives and immutable scope replay; include AT-NR-036 01–04 across B8A/B8B/B8C for valid aggregate targets and current global/per-coin/equality booking outcomes. These tests begin locally in their owning checkpoints, not for the first time at B13.

Existing regression examples (non-exhaustive): `tests/contract/test_module_boundaries.py` (EXISTING), `tests/contract/test_smoke_script_boundaries.py` (EXISTING), `tests/unit/test_container_runtime.py` (EXISTING), `tests/unit/test_dashboard_research_api.py` (EXISTING), `tests/unit/test_dual_lane_runtime.py` (EXISTING), `tests/unit/test_futures_runtime_integration.py` (EXISTING), `tests/unit/test_paper_runtime.py` (EXISTING), `tests/unit/test_postgres_runtime_store.py` (EXISTING)

Required source-clause acceptance IDs: AT-NR-001, AT-NR-020, AT-NR-052, AT-NR-134, AT-NR-140. All AT-NR rows and V01–V21 are required at the stated integrated/audit scope, AT-NR-151, AT-NR-152.

Verify all 154 groups, AT-NR-068-CF A–D, all P01–P33/L01–L40 observations, §40 visibility, full AT-NR-151/152 local cases and V18/V19 through actual dispatcher/store/native-fact paths. Historical denied outcomes and all reasons, recorded quantity/time bases, original auth/grant/publication cuts and economic-versus-diagnostic idempotency must already exist from owner checkpoints. Integration cannot reconstruct a lost observation from latest state.

R6 V20/V21 explicitly verify already implemented B12 reports end-to-end: all E01–E19/T01–T17, exact opportunity/fill/missed/target cohorts and paths, all ENTRY-RPT-01–15/TP-RPT-01–17, SQLite manifests/report persistence, restart pins and absence of source loss, live feedback, automatic optimization/promotion or legacy/demo authority. Producers remain B3/B7A/B9/B10 and consumer B12; B13 must reopen the producing checkpoint for a missing behavior, not first implement it here.

**NEGATIVE_BOUNDARY_TESTS:**

Every forbidden owner edge, legacy route, source/identity guess, unsupported native profile, incomplete financial proof and omitted required regression; no basic owner acceptance test begins for the first time here.

**REPLAY_RESTART_TESTS:**

Run complete inter-owner recovery/concurrency scenarios from B11 through actual dispatcher and compare exact accepted histories and once-only effects.

**MANDATORY_REVIEW_GATES:**

ARCHITECTURE_CONFORMANCE_REVIEW; TEST_REVIEW; ADVERSARIAL_TRADING_REVIEW; ACCOUNTING_FINALITY_REVIEW; NUMERIC_PRECISION_REVIEW

**R6 integrated scope:** Existing architecture/test/adversarial/numeric reviews cover full required reporting and no-feedback invariant; accounting review verifies original FINAL-based expectancy without another ledger. B12 quantitative/persistence/replay review is prerequisite, not substituted by B13 integration.

**Focused correction verification scope:** Existing architecture/test/trading/accounting/numeric reviews explicitly verify classifier/formation separation, all 154 requirement mappings and complete NR-151/NR-152 retained-basis/report isolation. B8/B9/B10 local review evidence is prerequisite, not replaced by this integrated review.

**UPSTREAM_DEPENDENCIES:**

B12

**DOWNSTREAM_DEPENDENTS:**

B14

**DEFINITION_OF_DONE:**

Integrated test/evidence matrix has a substantiated result for every requirement/object/contract/invariant. Missing applicable DB/native evidence is not green; independent architecture/test/trading/accounting/numeric reviews complete.

V18/V19 and every new observation subitem/case have source-backed local and integrated evidence. Correct trading economics alone does not close missing mandatory observability.

V20/V21 and every report source/cohort/path/member/test have earlier local implementation and review evidence; complete reporting capability is verified independently of whether a particular historical source supports exact intra-bar metrics. Source limitations must remain visible, never silently filled.

**RISKS:**

Broad green counts can hide skipped required cases or unsupported native certification; all claimed scope must be explicit.

**DO_NOT:**

Do not certify from old logs, rename legacy tests as canonical or silently patch methodology to fit implementation.

## B14 — Independent full backend conformance re-audit

**PRIORITY:**

P2

**PURPOSE:**

Independently assess the actually implemented backend against frozen v1.2.15 and this amended source-clause register.

**NORMATIVE_REQUIREMENTS:**

All 154 normalized groups NR-001–NR-154; source-specific local obligations remain in §3. NR-151/NR-152 map frozen owner observations; NR-153/NR-154 map required frozen Entry/TP reports with explicit diagnostic definitions in §6.4. No methodology addition is claimed. B13 verifies and B14 independently audits all of them.

**HISTORICAL_TRACEABILITY_ALIASES:**

R001–R060 (all HISTORICAL_TRACEABILITY_ALIAS).

**EXISTING_FOUNDATION_REUSED:**

FN.TEST, FN.JSON, FN.UOW, FN.MSG; see §2 for exact components and preservation action.

**CURRENT_STATE:**

Independent implemented-backend evidence must be produced after implementation; none claimed by this plan. These are supplied-evidence observations, not a claim that preceding checkpoints have already run.

**TARGET_STATE:**

Independent actual-backend conformance verdict with complete source/test/evidence traceability and limitations.

**FILES/SURFACES_EXPECTED_TO_EXTEND:**

FN.TEST: Existing tests and PostgreSQL fixtures — Existing tests/contract and tests/unit entries in source_symbol_inventory.json; EXTEND under §2 classification.

FN.JSON: Canonical JSON/digest — src/triggertrade/canonical_json.py; REUSE_AS_IS under §2 classification.

FN.UOW: PostgresUnitOfWork — `src/triggertrade/persistence/postgres.py::PostgresUnitOfWork` (inventory L94); REUSE_AS_IS under §2 classification.

FN.MSG: DurableMessageStore — `src/triggertrade/persistence/durable_messages.py::DurableMessageStore` (inventory L62); EXTEND under §2 classification.

**NEW_SURFACES_IF_REQUIRED:**

NEW_PROPOSED docs/BACKEND_CONFORMANCE_REAUDIT_V1_2_15.md as an audit-only future deliverable, not a file created by this revision task.

**LEGACY_SURFACES_TO_FENCE:**

Review isolation and native-uncertified paths explicitly, not as assumed complete.

**PERSISTENCE_ACTION:**

NONE

**PERSISTENCE_DETAILS:**

No canonical persistence creation in this checkpoint. Reuse/read the previously assigned representations; any newly discovered domain gap returns to its owning implementation checkpoint with review.

**TRANSACTION_BOUNDARIES:**

TX.owner, TX.preflight, TX.facts, TX.scope, TX.day, TX.setcalc, TX.set, TX.monitor, TX.opportunity, TX.grant, TX.construction, TX.hold, TX.native, TX.acceptance, TX.placement, TX.protection, TX.cancel, TX.close, TX.closeretention, TX.partition, TX.cashflow, TX.funding, TX.final, TX.incident, TX.receipt, TX.frontier; exact mechanism and tests in §7.

**CONTRACTS_TOUCHED:**

All 12, audit-only.

**IDENTITY_BINDINGS:**

Full §7.5 graph, unchanged; no new identity ownership.

**NUMERIC_REQUIREMENTS:**

Audit exact source-defined arithmetic/rounding/signs and separate economic/operational/receipt times against actual implementation evidence.

**IMPLEMENTATION_SCOPE:**

Inspect actual then-current source, contracts, owner handlers, store/migration shape, identity history, all applicable tests and execution evidence. Reconcile every NR and historical alias, all objects/contracts/transactions/invariants. Prior approval banners, historical green tests, checkpoint DONE flags and this map’s closure claims are not evidence of implementation conformance. Record remaining defects/limitations without silently remediating.

R6 audit includes explicit NR-153/154 report coverage, analytical-definition pinning versus frozen trading semantics, full source retention/lineage/cohort/path availability, true storage grounding, B12 local review and zero canonical feedback. All 154 groups are in scope; this planning self-check is not implemented-backend evidence.

**TESTS_REQUIRED:**

Reproduce required regression, contract, exact numeric, owner-local and integrated transaction/replay/E2E/finality evidence; distinguish unavailable infrastructure/native certification from tested behavior.

Existing regression examples (non-exhaustive): All applicable existing suites from source_symbol_inventory.json, selected by actual affected source; no historical green result is imported. All AT-NR rows and V01–V21 are required at the stated integrated/audit scope.

**NEGATIVE_BOUNDARY_TESTS:**

Independent challenge of alleged completeness, skipped required suites, alternate canonical path, missing proof/receipt/frontier, wrong current package and fresh source drift.

**REPLAY_RESTART_TESTS:**

Review actual restart/duplicate/conflict/terminal evidence across every owner, not only unit serialization or a historical report.

**MANDATORY_REVIEW_GATES:**

FULL_BACKEND_CONFORMANCE_REAUDIT; ARCHITECTURE_CONFORMANCE_REVIEW; ACCOUNTING_FINALITY_REVIEW; ADVERSARIAL_TRADING_REVIEW

**UPSTREAM_DEPENDENCIES:**

B13

**DOWNSTREAM_DEPENDENTS:**

None; a negative re-audit opens a separately scoped remediation task.

**DEFINITION_OF_DONE:**

Independent full conformance verdict and complete traceability/evidence report issued, with every finding classified. A negative verdict requires a separate bounded remediation task; completion alone is not approval.

**RISKS:**

Self-certification by the implementation team or treating planning closure as runtime proof.

**DO_NOT:**

Do not implement fixes during audit, change the frozen source, accept DONE banners as proof or promise profitability/live readiness.

## 14. Planning-defect closure

All P/N and prior correction records in **§§14.1–14.5 and §15 are historical R5-and-earlier traceability only**. Their old count, CLOSED, readiness, source inventory and protected-diff assertions are not R6 evidence. The supplied fresh clean-room R5 audit identified FA-R5-01 despite those historical self-checks. The active R6 register has 154 rows and its focused correction, actual R5-to-R6 comparison and pending-independent-review status are in §16. No historical banner overrides that disposition.

| Defect | Required correction | Revision made / evidence in revised map | Map section(s) changed | Closure status |
| --- | --- | --- | --- | --- |
| P01 | Normalize reconstructed model; remove unsupported canonical labels | §3 has source-based NR obligations, all sixty historical aliases and explicit R045/R046 dispositions; no old-count completion percentage. §§4–12 add omitted proof/receipt/preflight obligations. RA-01 now corrects NR-035 and its acceptance cases to one fixed boundary base with separate live metrics; no normalized requirement is added or renumbered. | §1.3; §3; §12; every checkpoint NORMATIVE_REQUIREMENTS | CLOSED |
| P02 | Correct twelve-family topology and receipt owner | §4 has exact producers/consumers, API request AND response directions, return to Set, exclusive Position grant consumer; §7.4 separates Lifecycle result and Portfolio receipt. | §4; §5; TX.final/TX.receipt; B6/B9/B10 | CLOSED |
| P03 | B0 actual frozen branch enforcement | B0 includes schema/whitelist/minimum validator constructs and actual public-parser positive/negative branch cases, optional unavailable record, unknown cause and binary per-item statuses. | §9.1; B0; AT-NR-003/AT-NR-004 | CLOSED |
| P04 | Exact arithmetic and work/wire/report dataflow | Generic rational/grid/midpoint primitives separated from owner equations; Q36/Q18/Qcapital/Qratio, exact A vs H, report-only gates and distinct funding/non-funding policies mapped/tested. | §8; B1/B5A/B7A/B7B/B8B/B8C/B10 | CLOSED |
| P05 | Narrow B2; reuse stores; fence SQLite authority | B2 is shared UoW/CAS/transport/frontier only. Domain records assigned by owner. Reuse table and logical overlay prohibit duplicate grants/spec/auth/sync/close/outbox. Legacy accounting isolated. | §2; §6; §7; B2 and all owner persistence fields | CLOSED |
| P06 | Interleave initial decision/grant/construction/current hold | B7A→B8B→B7B→B8C explicit dependencies, B8A upstream scope; successful construction/spec/TWO outboxes share existing UoW. | §4; TX.opportunity/TX.grant/TX.construction/TX.hold; §10.1; B7A/B8B/B7B/B8C | CLOSED |
| P07 | Complete Set dependency/formation state | B5A full populations/work precision/15m ATR/separate local5m; B5B existing epochs, CURRENT_STATE/FRESH_EVENT, event interruption/consumption and MATCHED/frozen/handoff atomicity. | §3 Set rows; §5; ST.setcalc/ST.atr15/ST.local5/ST.setevents; TX.set; B5A/B5B | CLOSED |
| P08 | Complete F-013 monitor instead of envelope-only logic | Full activation/reducer/precedence/frozen predicates; original-entry sticky key, equal requirement/signal ID, first time/reason/optional content, deferred exact target and no recovery withdrawal; real native return in B9. | §9.2–9.4; §7.5; ST.monitor/ST.cancel; TX.monitor/TX.cancel; B6/B9 | CLOSED |
| P09 | Lifecycle native safety and actual return integration | Existing start/intent/sync/close/reconciliation extended with current hard/provenance/profile/protection, complete source partition, one close budget and separate native authority gate. | §7.3; §11; B9/B12; V05/V07–V10 | CLOSED |
| P10 | Canonical financial/finality/economic-day integration | Lifecycle A-004/A-002/S-004 terminal transaction and separate Portfolio first receipt/day/A-009/release; historical day handling, actual factual gross, six predicates, no FX/double wallet credit, distinct zero-fill/no-create. RA-01 corrects only B8A’s upstream base prerequisite; the accepted A-009 equations, sequence and finality/receipt mechanisms remain unchanged. | §5–8; §7.4; B8A/B8C/B9/B10; V11–V14 | CLOSED |
| P11 | Committed-prefix, known-evidence preflight and zero-effect staging | Concrete same-edge scoped serializable head/prefix mechanism, raw accepted-owner preflight with independent durable challenge checkpoint, full history/indexes, source partition/receipt atomicity and both incident orders. | §7.1–7.3; TX.preflight/TX.partition/TX.frontier; B2/B3/B5B/B8C/B9/B10 | CLOSED |
| P12 | Owner-local replay, sufficient review and activation gates | RP-LOCAL tests and full applicable independent reviews inside every owner checkpoint; B11 stress only; B12 requires all corrected implementation blockers/native/current-proof/receipt/invariant evidence; B13 full verification. | §10.2–10.3; §11–12; every checkpoint TESTS/REPLAY/GATES/DoD | CLOSED |
| N01 | B4 is binding inventory, not a second producer layer | Reuse existing builders; only minimal justified wrappers, no business decisions or owner-completion claim. All actual production/consumption assigned to owners. | §2; §4; B4 | CLOSED |
| N02 | Actual paths/symbols and consistent checkpoint crosswalk | Actual build_capital_and_limits_grant/research_pin_payload/PositionConfigPinStore retained; wrong literal names flagged; proposed paths classified; one NR-to-checkpoint relation generates register and checkpoint scopes. | §2.2; §3; §10.1; checkpoint fields | CLOSED |

### 14.1 Prior RA-01 / RA-02 correction record — historical traceability

| Finding | Correction in this candidate | Frozen source / independent finding | Candidate status |
| --- | --- | --- | --- |
| RA-01 | Correct NR-035/AT-NR-035, B8A, ST.day/ST.portfolio and A-009’s numeric base-input description: one fixed boundary wallet-own-capital base, complete governed reconstruction or RECONCILING/block, separate live metrics, and all fourteen source-derived acceptance cases. | PORTFOLIO_RULES §§3–4 L130–L247, Appendix B L1847–L1883; SYSTEM_PROTOCOLS P8 L193–L220; re-audit §29 RA-01. | CLOSED — correction assessment, independent confirmation pending |
| RA-02 | Correct only NR-043’s source heading to **23. Daily Loss Limit** and range to L776–L874; retain every other cell unchanged. | PORTFOLIO_RULES L776–L874; re-audit §29 RA-02. | CLOSED — editorial correction assessment |

**Historical RA input-to-candidate comparison, not the R2 diff:** Focused input-to-candidate checks preserve all 150 normalized IDs and all historical aliases; only NR-035 and NR-043 differ, and NR-043 differs only in its source locator. The entire twelve-family contract section, eighteen-object matrix, twenty-invariant section, all 26 transaction rows and the full preflight/frontier/finality/identifier section are byte-identical to the revised input. All 39 logical-state IDs and their representation/action/owner/checkpoint/transaction columns are unchanged; only ST.day and ST.portfolio descriptive fields are clarified. All eighteen checkpoint bodies other than B8A, including B8C and B10, are byte-identical. B8A retains its original requirement IDs, state/store/transaction assignments, dependencies and review gates. The only numeric-matrix edit clarifies A-009’s fixed base operand and supporting evidence, not its equation or comparison. Candidate metadata and closure/readiness statements identify this focused correction rather than claiming a new independent audit.

**Historical daily-base residual-language check, retained unchanged:** Residual-language review distinguishes prohibited daily-base alternatives from legitimate Portfolio health and Position construction terminology. The operative map contains no requirement to select or test multiple daily bases. Explicit prohibitions on an alternative denominator or intraday rebasing are retained as negative acceptance boundaries. Portfolio health LIVE/RECONCILING/STALE and the unrelated FIXED/DYNAMIC Position modes remain unchanged.

```text
RA-01_STATUS:
CLOSED

RA-02_STATUS:
CLOSED

UNSUPPORTED_DAILY_BASE_MODES_REMAINING:
0

SELECTABLE_BASE_MODE_INTRODUCED:
NO

SINGLE_FIXED_DAILY_BASE_PRESERVED:
YES

LIVE_METRICS_SEPARATE_FROM_BASE:
YES

INTRADAY_REBASE_AUTHORIZED:
NO

A009_SEMANTICS_CHANGED_BEYOND_BASE_PREREQUISITE:
NO

CONTRACT_GRAPH_CHANGED:
NO

CERTIFIED_OBJECT_MEANINGS_CHANGED:
NO

OWNER_MAPPING_CHANGED:
NO

DEPENDENCY_ORDER_CHANGED:
NO

TRANSACTION_TOPOLOGY_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

F013_CHANGED:
NO

FINALITY_RECEIPT_MODEL_CHANGED:
NO

NEW_PRODUCT_DECISION_INTRODUCED:
NO
```

### 14.2 FA-01 / FA-02 — prior R2 focused correction and regression check (historical traceability)

The statements, CLOSED statuses and comparison results in this subsection record the prior R2 correction against its then-supplied evidence; they are not R4 verification results or independent approval for implementation. The prior R3 FA-R2-01 / FA-R2-02 correction is retained separately in §14.3; the current R4 correction is recorded in §14.4.

| Finding | R2 correction | Exact controlling evidence | Focused status |
| --- | --- | --- | --- |
| FA-01 — BLOCKING | Remove F-010 from the F-006/F-007 consumer cells and Stop from F-010 input authority; clarify F-010’s own TP output, preserve the schedule while making operand independence explicit in §5.1, synchronize the §8.2 Entry/SL/TP dataflow and B7A scope, and add the explicit AT-NR-089 discriminator. Missing Stop still rejects the overall opportunity. | POSITION_RULES Part I §14 L465–L519 / §43 L1500–L1508; Part IV §4 L4331–L4352, §10 L4476–L4480, §26 L4896–L4909; complete numerical fixture derivation in B7A; supplied final audit §2 FA-01. | CLOSED — independent re-audit pending |
| FA-02 — NON_BLOCKING | Correct FN.RESEARCH, its repeated B0/B1/B13 descriptions and ST.research’s existing-representation cell: existing helper, SQLite ResearchStore, SQLite OperatorStateStore, separate PostgreSQL promotion-request/outbox governance. Preserve pins/history/isolation and the existing promotion facility; no migration or new store. | Actual src/triggertrade/research_pins.py L22–L47; persistence/research_store.py L132–L137 / L638–L641; persistence/operator_state_store.py L44–L55 / L231–L234; persistence/research_promotion_governance.py L9–L87; SYSTEM_PROTOCOLS L887–L897; supplied final audit §2 FA-02. | CLOSED — independent re-audit pending |

R2’s full-map scan covers the object matrix, operand/dependency summaries, B7A scope/tests, numeric dataflow, all FN.RESEARCH repetitions, ST.research and current closure/readiness text. It leaves no operative Stop-to-F-010 dependency or claim that ResearchStore/OperatorStateStore are PostgreSQL. Source-supported joint TP/SL feasibility and required-Stop rejection remain operative. References to the removed dependency in prohibitions, test negative controls or this correction history are not instructions to implement it.

The input-to-R2 comparison preserves all 150 NR rows and the full historical R001–R060 crosswalk byte-for-byte. The entire twelve-family contract section, all 26 transaction rows and the complete preflight/frontier/finality/identifier section, the F-013 section, checkpoint dependency/review/replay policy, worker activation section and all twenty invariants are byte-identical. All 39 persistence rows preserve their IDs, actions, owners, checkpoints, transaction and replay fields; only ST.research’s existing representation changes. Fifteen certified-object rows are byte-identical; F-006/F-007 change only their consumer cells, and F-010 changes only its input authority and directly dependent own-output clarification, not its meaning, owner, state, checkpoint or frozen formula.

The checkpoint specifications change only B7A’s directly affected scope/tests and the FN.RESEARCH description in B0/B1/B13. All other checkpoint bodies—including B8A and every AT-NR-035 case, B8B, B7B, B8C, B9, B10, B11 and B12—are byte-identical. Every checkpoint’s requirement/alias set, state/transaction assignment, contracts, IDs, upstream/downstream dependencies, reviews and existing replay requirements remain unchanged. The only §8 numeric-row change clarifies independent F-010 dataflow; no arithmetic, threshold or quantization policy changes. Current provenance and closure/readiness statements are synchronized with R2; historical comparisons in §14.1 are explicitly not R2 preservation claims.

ST.research’s unchanged NONE transaction assignment introduces no canonical trading transaction; it does not deny the existing PostgreSQL promotion-request/outbox UoW identified by FN.RESEARCH. Its truthful mixed-storage description grants no SQLite canonical trading authority, migration, new Research runtime or new business/API edge.

#### FA-01 focused self-check

```text
FA-01_STATUS:
CLOSED

F010_STOP_INPUT_PRESENT:
NO

F006_F010_CONSUMER_DEPENDENCY_PRESENT:
NO

F007_F010_CONSUMER_DEPENDENCY_PRESENT:
NO

F010_INDEPENDENT_INPUT_AUTHORITY_CORRECT:
YES

JOINT_TP_SL_FEASIBILITY_PRESERVED:
YES

MISSING_STOP_STILL_REJECTS_OVERALL_OPPORTUNITY:
YES

F010_INDEPENDENCE_ACCEPTANCE_CASE_PRESENT:
YES

POSITION_STAGE_ORDER_CHANGED:
NO
```

#### FA-02 focused self-check

```text
FA-02_STATUS:
CLOSED

RESEARCHSTORE_CLASSIFIED_AS_SQLITE:
YES

OPERATORSTATESTORE_CLASSIFIED_AS_SQLITE:
YES

POSTGRES_PROMOTION_GOVERNANCE_DISTINGUISHED:
YES

NONEXISTENT_POSTGRES_RESEARCH_STORE_CLAIM_REMAINS:
NO

RESEARCH_MIGRATION_INTRODUCED:
NO

S005_ISOLATION_CHANGED:
NO
```

#### Architecture and regression check

```text
CONTRACT_GRAPH_CHANGED:
NO

OWNER_MAPPING_CHANGED:
NO

TRANSACTION_TOPOLOGY_CHANGED:
NO

CHECKPOINT_ORDER_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

NEW_BUSINESS_OWNER:
NO

NEW_PRODUCT_BEHAVIOR:
NO

BACKEND_REDESIGN_REQUIRED:
NO

UNRELATED_PLAN_REGRESSION:
NO

UNRELATED_SUBSTANTIVE_CHANGES:
0

NEW_PRODUCT_DECISION_INTRODUCED:
NO
```

### 14.3 FA-R2-01 / FA-R2-02 — prior R3 focused correction and regression check (historical traceability)

These CLOSED statuses and R2-to-R3 comparison results record the prior focused R3 correction against its then-supplied frozen clauses, source and clean-room R2 findings. They do not amend that audit, independently certify R3 or establish R4 closure. The current FA-R3-01 / FA-R3-02 correction and R3-to-R4 verification are recorded in §14.4.

| Finding | R3 correction | Controlling evidence / original R2 location | Focused status |
| --- | --- | --- | --- |
| FA-R2-01 — NON_BLOCKING | Change only NR-035's transaction-impact cell: TX.day is the principal canonical day/base/latch establishment and recovery mechanism; TX.scope is limited to consequential scope publication or new-exposure eligibility resulting from Portfolio health/day state. ST.day, B8A, TX.day and TX.scope bodies remain unchanged. | Frozen methodology/PORTFOLIO_RULES.md §§3–4 L130–L247 and Appendix B L1847–L1883; SYSTEM_PROTOCOLS.md P8 L193–L221; clean-room R2 audit §28 FA-R2-01 L1079–L1095; original R2 NR-035 L230, ST.day L557, TX.scope/TX.day L593–L594. | CLOSED — independent focused re-audit pending |
| FA-R2-02 — NON_BLOCKING | Add NUMERIC_PRECISION_REVIEW to B6 and B9, and ACCOUNTING_FINALITY_REVIEW to B8A, in both §10.2 and the matching detailed MANDATORY_REVIEW_GATES. Each added review has its local scope directly under that checkpoint's gate list. All other review assignments and implementation boundaries remain unchanged. | Frozen methodology/SET.md L4935–L5008; schemas/SET_NUMERIC_POLICY.md L33–L94; SYSTEM_PROTOCOLS.md P5 L83–L113 and T04 L570–L622; schemas/NUMERIC_POLICY.md §5 L63–L80; methodology/PORTFOLIO_RULES.md §23 L776–L874 and Appendix B L1847–L1883; clean-room R2 audit §28 FA-R2-02 L1098–L1114; original R2 central gates L855/L858/L863 and detailed lists L1697/L2063/L2725. | CLOSED — independent focused re-audit pending |

Frozen paths in this subsection are relative to `docs/trading-methodology/`, the repository location of the supplied frozen package. Backend grounding remains the existing `src/triggertrade/persistence/postgres.py` L94–L125 and `portfolio_state_store.py` L26–L106, together with the existing `lifecycle_close_authority_store.py` L80–L329, `lifecycle_reconciliation_store.py` L63–L148 and `lifecycle_set_sync_store.py` L46–L105. The legacy `daily_loss_store.py` L1–L50 remains SQLite and fenced. These are existing extension surfaces, not proof of implemented canonical behavior or new stores to create. Reviewer categories are local planning gates, not additional business owners or new frozen trading rules.

**Transaction traceability:** NR-035 now resolves to the same principal TX.day mechanism already assigned to ST.day. The retained TX.scope reference concerns only the downstream scope/eligibility consequence of Portfolio health/day state; it cannot replace day/base establishment or recovery. Inspection of all NR-035 references found no other transaction cell requiring correction. Historical alias, daily-base policy, numeric dataflow and acceptance references are retained unchanged; this subsection and §15 synchronize the active closure and transaction-plan assessment.

**R2-to-R3 protected-content verification:**

| Protected surface | Focused comparison result |
| --- | --- |
| Normalized register | All 150 IDs and rows retained; 149 rows byte-identical. NR-035 differs only in its transaction-impact cell; every other cell, including source, obligation, owner, checkpoint, persistence, test, review and aliases, is unchanged. |
| Historical R001–R060 crosswalk | All 60 aliases and the complete crosswalk byte-identical. |
| Certified objects / contract graph | All 18 object rows, F-010 input authority and dependency explanation, and the entire twelve-family contract section byte-identical. |
| Persistence / transactions | All 39 logical-state rows and their surrounding policy unchanged; all 26 transaction mechanism bodies and the entire preflight/frontier/close/finality/identifier section byte-identical. No new mechanism or canonical store. |
| Review assignments | Exactly three checkpoint-specific specialist additions, each reflected once in the central matrix and once in its detailed list. All 19 central and detailed lists match exactly; all other assignments are unchanged. The three required local review scopes do not expand implementation duties. |
| Checkpoint bodies | All 19 checkpoints remain in the original order. Outside the three affected MANDATORY_REVIEW_GATES blocks and their local review scope paragraphs, every checkpoint body is byte-identical; all dependencies, implementation scopes, tests and definitions of done are unchanged. |
| Daily-base / Position acceptance | The complete fourteen-case AT-NR-035 matrix, B8A business policy and A-009 semantics are unchanged. B7A, including the complete AT-NR-089 F-010 discriminator, is byte-identical. |
| Numeric / F-013 / replay / activation / invariants | The complete numeric matrix/dataflow, F-013 section, dependency graph, owner-local replay policy, worker/native activation gates, integrated test plan and twenty global invariants are byte-identical. |
| Other edits | Only current R3 metadata/input provenance, historical-versus-current correction labels and directly dependent closure/readiness wording. No unrelated substantive change. |
| Input preservation / execution scope | Original input SHA-256 values remain unchanged. Verification uses text/field/section comparison and read-only source inspection; no backend code, implementation tests, database, native operation or repository action is executed. |

#### FA-R2-01 focused self-check

```text
FA-R2-01_STATUS:
CLOSED

NR035_TX_DAY_PRESENT:
YES

NR035_TX_SCOPE_ROLE_EXPLICITLY_LIMITED:
YES

NR035_DAY_BASE_TRANSACTION_MAPPING_CORRECT:
YES

TX_DAY_MECHANISM_CHANGED:
NO

TX_SCOPE_MECHANISM_CHANGED:
NO

DAILY_BASE_POLICY_CHANGED:
NO

AT_NR_035_CHANGED:
NO

A009_CHANGED:
NO
```

#### FA-R2-02 focused self-check

```text
FA-R2-02_STATUS:
CLOSED

B6_NUMERIC_PRECISION_REVIEW_PRESENT:
YES

B9_NUMERIC_PRECISION_REVIEW_PRESENT:
YES

B8A_ACCOUNTING_FINALITY_REVIEW_PRESENT:
YES

CENTRAL_REVIEW_MATRIX_SYNCHRONIZED:
YES

DETAILED_CHECKPOINT_GATES_SYNCHRONIZED:
YES

UNRELATED_REVIEW_GATES_ADDED:
0

CHECKPOINT_DEPENDENCIES_CHANGED:
NO
```

#### Architecture and regression verification

```text
CONTRACT_GRAPH_CHANGED:
NO

OWNER_MAPPING_CHANGED:
NO

TRANSACTION_MECHANISM_COUNT_CHANGED:
NO

TRANSACTION_TOPOLOGY_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

CHECKPOINT_ORDER_CHANGED:
NO

CERTIFIED_OBJECT_MEANINGS_CHANGED:
NO

FORMULA_SEMANTICS_CHANGED:
NO

DAILY_BASE_SEMANTICS_CHANGED:
NO

A009_SEMANTICS_CHANGED:
NO

F013_SEMANTICS_CHANGED:
NO

NEW_BUSINESS_OWNER:
NO

NEW_PRODUCT_BEHAVIOR:
NO

BACKEND_REDESIGN_REQUIRED:
NO

FOCUSED_DIFF_BOUNDARY_RESPECTED:
YES

UNRELATED_SUBSTANTIVE_CHANGES:
0

UNRELATED_PLAN_REGRESSION:
NO

NEW_PRODUCT_DECISION_INTRODUCED:
NO
```

### 14.4 FA-R3-01 / FA-R3-02 — R4 focused correction and regression verification

This subsection is the current focused correction record. CLOSED means that the replacement map has been corrected against the supplied frozen source and the two clean-room R3 findings; independent focused re-audit is still required. It does not convert R3's REVISION_REQUIRED verdict into an approval, certify the future implementation or replace any checkpoint's tests/reviews.

| Finding | Focused R4 correction | Direct controlling source / original R3 location | Correction assessment |
| --- | --- | --- | --- |
| FA-R3-01 — BLOCKING | NR-053 explicitly preserves both frozen direction scopes. The F-005 row is qualified to governed Sets; §5.2 distinguishes the two owner-local routes without changing any formula. B5A preserves applicable kernels/configuration semantics; B5B dispatches from the immutable definition, retains generic fixed/branch direction, enforces declared deterministic conflict resolution and rejects F-005 bypass. Invariant 1 is a Set-ownership oracle, with AT-NR-053 A–H and V03/V04/V15/V17/B13 integration/replay coverage. | Frozen SET §5 L509–L530 and Part II §§33–37, especially §34A L3155–L3197; SYSTEM_PROTOCOLS P17 L359–L365 and Research isolation L887–L897. Clean-room R3 audit §3 FA-R3-01 L43–L57; original R3 NR-053 L257, F-005 row L499, invariant 1 L936, B5A L1808 and B5B L1932. | CLOSED — focused correction assessment; independent confirmation pending |
| FA-R3-02 — NON_BLOCKING | NR-036 no longer leaves a configured-sum constraint unidentified. It expressly permits aggregate targets above the global cap without normalization. AT-NR-036 01–04 accepts the frozen 80%-targets/60%-global example, rejects actual global/per-coin overcommit and preserves the inclusive allowed capacity boundary. B8A/B8B/B8C local tests and V04/V17/B13 integration distinguish configuration validity, non-reserving grant and current H booking. | Frozen PORTFOLIO_RULES §§5–8 L251–L358, §§14–15 L541–L570, §§19–22 L700–L771 and §41.1 L1361–L1363. Clean-room R3 audit §3 FA-R3-02 L60–L74; original R3 NR-036 L240 and dependent B8A/B8B/B8C tests. | CLOSED — focused correction assessment; independent confirmation pending |

Frozen paths above are relative to `docs/trading-methodology/`; the archive root is `trading-methodology/`. Source line ranges are physical one-based lines in the original supplied files, not line numbers in this growing replacement map. E01 and E05 in the supplied `R3_AUDIT_EVIDENCE.md` corroborate the direction-scope and allocation-sum extracts; the original files, not that report, control the correction.

**Current-source grounding:** `src/triggertrade/set_scope.py` L17–L120 already represents configuration identity/version/digests and the formation epoch; the correction extends the same Set handler/records rather than creating another owner or a new direction service. `src/triggertrade/services/trading_worker.py` L106–L131 remains fail-closed for uncertified owner handlers; this document does not remove that block. `src/triggertrade/portfolio_state.py` L22–L59 and L89–L145 and `src/triggertrade/persistence/portfolio_state_store.py` L26–L119 remain the reusable commitment/state and persistence foundation, not authority for a new configuration-sum ceiling. No constructor/API, migration, worker route or backend file is changed by R4.

**Source-derived acceptance checks:** Direction cases are grounded in SET §5's explicit two-scope rule, unchanged governed classification/final-resolution clauses and P17 binding. They require future actual local/integrated tests; no current owner-handler execution is claimed. The AT-NR-036 numeric projection was checked independently with exact rational arithmetic: 1,000×60/100=600; 1,000×20/100=200; four targets=800; 590+20=610 (global failure); 190+20=210 (coin failure); 580+20=600 (global equality). Fixture C=H=20 is not a new sizing policy or a user-supplied grant override: the existing source-defined grant/geometry/construction path must independently substantiate it, with all non-target gates satisfied. Configuration validity never implies native permission.

**R3-to-R4 protected-content verification:**

| Protected surface | Comparison result |
| --- | --- |
| Complete replacement / normalized register | The entire map is retained. All 150 NR IDs remain NR-001–NR-150 with unchanged numbering; 148 rows are byte-identical. Only NR-036 and NR-053 change, and only their source locator, behavioral obligation and acceptance-test cells. Owner, current-condition, checkpoints, persistence, transaction, review and alias cells are unchanged for both. |
| Historical aliases / source foundation | All 60 R001–R060 historical-alias rows and the complete crosswalk are byte-identical. The full existing-component/source grounding section is unchanged, including the Research SQLite versus narrow PostgreSQL governance distinction and legacy fences. Historical R037 remains an alias interpreted under the corrected current §5 scope, not a new universal direction obligation. |
| Certified objects | Exactly 18 identities. Seventeen entire rows are byte-identical. F-005 changes only its canonical-meaning cell to qualify its governing scope; every input, owner, state, output, consumer, foundation, checkpoint and normalized-anchor cell remains unchanged. Scope explanation is added adjacent to the matrix and in §5.2, not inside the arithmetic or another object. |
| Contract graph | The entire §4 graph/family matrix is byte-identical: 12 families, exact versions/directions, four business owners, no new business/API edge. |
| Persistence / transactions | The complete §6 persistence section and all 39 state rows are byte-identical. The complete §7 section, including every one of the 26 TX mechanism bodies, preflight, frontier, close/finality separation and identifier graph, is byte-identical. No duplicate authority, record topology or transaction is introduced. |
| Numeric / F-010 / F-013 | The complete §8 numeric policy/dataflow and §9 parser/F-013 section are byte-identical. §5.1 Position schedule/operand distinction, the F-010 row and the entire B7A checkpoint including AT-NR-089 are byte-identical. B6 is unchanged in full. F-005's NR-068 arithmetic/threshold/veto row and all other formula rows are unchanged. |
| Daily base / NR-035 | NR-035 and its principal TX.day/consequential TX.scope mapping are byte-identical. B8A's complete implementation scope, negative boundaries, replay policy and local accounting review are unchanged. The full fourteen-case AT-NR-035 matrix and its derivation are byte-identical. The new separate AT-NR-036 matrix does not change the base, daily totals, A-009 or B10. |
| Checkpoints / stage order | All 19 checkpoints remain in the same order with identical requirement/alias lists, existing/new-surface assignments, persistence/transaction/contract/identity/numeric assignments, dependencies and review blocks. Twelve full checkpoint bodies are byte-identical: B0/B1/B2/B3/B4/B6/B7A/B7B/B9/B10/B11/B14. B5A/B5B changes are direction-scope/acceptance/replay specializations; B8A/B8B/B8C changes are allocation acceptance tests/references; B13 adds those integrated tests; B12 changes only the directly dependent planning-closure reference. |
| Review gates | §10, including the dependency DAG, central mandatory-review matrix and RP-LOCAL policy, is byte-identical. All 19 central/detailed review lists match exactly, and every detailed review block is unchanged. B8A ACCOUNTING_FINALITY_REVIEW and B6/B9 NUMERIC_PRECISION_REVIEW and their local scopes remain unchanged. |
| Native / finality / replay / activation | B9 native safety, B10 finality/Portfolio receipt, B11 replay hardening and all related mechanisms remain byte-identical. §11/B12 only synchronize which current planning correction must be independently accepted; dispatch/native permission prerequisites, operational routing, fail-closed behavior and B13/B14 obligations do not change. |
| Integrated tests / invariants | V03/V04/V15 and B13 add only AT-NR-053/AT-NR-036 scope/configuration acceptance references. All other V-FULL rows are unchanged. Invariant 1 retains Set ownership and the same checkpoint/review assignments, with a corrected anchor/oracle; invariant rows 2–20 are byte-identical. |
| Other edits / input preservation | Other edits are R4 metadata, current input hashes, historical-versus-current labels and directly dependent correction/readiness text. All five original input hashes remain unchanged. The only new deliverable is this complete R4 Markdown file; no backend code, database/native tests, git action or methodology modification is performed. |

#### FA-R3-01 focused self-check

```text
FA-R3-01_STATUS:
CLOSED

F005_SCOPE_QUALIFIED:
YES

GENERIC_FIXED_DIRECTION_PRESERVED:
YES

GENERIC_MATCHED_BRANCH_DIRECTION_PRESERVED:
YES

GENERIC_CONFLICT_RULE_PRESERVED:
YES

F005_BYPASS_BLOCKED_IN_GOVERNED_SCOPE:
YES

SET_REMAINS_SOLE_DIRECTION_OWNER:
YES

NR053_SCOPE_CORRECT:
YES

F005_OBJECT_ROW_SCOPE_CORRECT:
YES

B5A_SCOPE_CORRECT:
YES

B5B_DIRECTION_DISPATCH_CORRECT:
YES

INVARIANT_1_ORACLE_CORRECT:
YES

GENERIC_DIRECTION_ACCEPTANCE_CASES_PRESENT:
YES

F005_ARITHMETIC_CHANGED:
NO

NEW_DIRECTION_OWNER_INTRODUCED:
NO
```

#### FA-R3-02 focused self-check

```text
FA-R3-02_STATUS:
CLOSED

NR036_CONFIG_SUM_AMBIGUITY_REMOVED:
YES

AGGREGATE_COIN_TARGETS_MAY_EXCEED_GLOBAL_CAP:
YES

VALID_80_TARGETS_60_GLOBAL_CASE_PRESENT:
YES

RUNTIME_GLOBAL_CAP_STILL_ENFORCED:
YES

PER_COIN_CAP_STILL_ENFORCED:
YES

NEW_CONFIGURATION_SUM_CEILING_INTRODUCED:
NO

AT_NR_036_SOURCE_SUPPORTED:
YES
```

#### No architecture, formula or product change

```text
CONTRACT_GRAPH_CHANGED:
NO

OWNER_MAPPING_CHANGED:
NO

BUSINESS_OWNER_COUNT_CHANGED:
NO

TRANSACTION_MECHANISM_COUNT_CHANGED:
NO

TRANSACTION_TOPOLOGY_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

CHECKPOINT_ORDER_CHANGED:
NO

F005_ARITHMETIC_CHANGED:
NO

F010_CHANGED:
NO

F013_CHANGED:
NO

DAILY_BASE_CHANGED:
NO

A009_CHANGED:
NO

NEW_DIRECTION_SERVICE:
NO

NEW_PORTFOLIO_CONFIGURATION_CEILING:
NO

NEW_PRODUCT_BEHAVIOR:
NO

BACKEND_REDESIGN_REQUIRED:
NO
```

#### Focused diff and regression verification

```text
FOCUSED_DIFF_BOUNDARY_RESPECTED:
YES

UNRELATED_SUBSTANTIVE_CHANGES:
0

UNRELATED_PLAN_REGRESSION:
NO

NEW_PRODUCT_DECISION_INTRODUCED:
NO

NORMALIZED_REQUIREMENT_COUNT:
150

HISTORICAL_ALIAS_COUNT:
60

CERTIFIED_OBJECT_COUNT:
18

CONTRACT_FAMILY_COUNT:
12

LOGICAL_STATE_COUNT:
39

TRANSACTION_MECHANISM_COUNT:
26

CHECKPOINT_COUNT:
19

UNRELATED_CERTIFIED_OBJECT_CHANGES:
0

CONTRACT_GRAPH_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

TRANSACTION_TOPOLOGY_CHANGED:
NO

DEPENDENCY_ORDER_CHANGED:
NO

ALL_19_REVIEW_LISTS_MATCH:
YES

REVIEW_ASSIGNMENTS_CHANGED:
NO

INPUT_FILES_CHANGED:
NO
```

### 14.5 FA-R4-01 / FA-R4-02 / FA-R4-03 — historical R5 focused correction

The operative basis is the six actual inputs and authority order in §1. The supplied clean-room R4 audit returned one blocking and two non-blocking map-edit findings. Its AUD-P-01 and AUD-L-01 missing groups are now NR-151 and NR-152; they were already frozen obligations. No R4 closure banner was used as evidence, and no historical audit is amended by this correction.

| Finding | Focused correction in R5 | Original-source support and actual source grounding | Corrected map locations | Correction assessment |
| --- | --- | --- | --- | --- |
| FA-R4-01 — BLOCKING | Remove the operative F-001/F-002→F-004 prerequisite graph; separately bind configured formation and F-003/F-004/F-005 classifier evidence, joining only at final Set resolution. Update the three affected NR rows, four dependent object-input/consumer cells, numeric dataflow and B5A/B5B. Add real-path AT-NR-068-CF A–D with exact F-002 and candidate-veto discriminators. | SET §8A L617–L712, §8B L847–L928/L943–L988/L1078, Part II L1739–L1757/L2561–L2697/L3050–L3226. Actual set_scope.py configuration/epoch foundation and fail-closed trading_worker.py support extension, not a fabricated existing classifier. SOURCE_EVIDENCE_R4 E01–E06; audit §3 FA-R4-01. | NR-054/055/068; §5 object matrix/§§5.2–5.3; ST.setcalc; TX.setcalc/TX.set; §8.2; B5A/B5B; V03/V04/V15 | CLOSED — focused correction self-check; independent confirmation pending |
| FA-R4-02 — NON_BLOCKING | Add NR-151 with full gate/status/all-evaluated-reason and P01–P33 diagnostic mapping; distinguish current fields from missing observation history, history derivation from latest state, consumed/terminal timing, and never-held surplus from release. Assign existing owner states/transactions, twelve local tests and explicit local review responsibilities; integrate at B13. | PORTFOLIO_RULES §§51–53 L1540–L1591, §63 L1741–L1777; §§37–46 L1214–L1495; NUMERIC_POLICY §§4–5/7 L53–L80/L90–L92. Actual PortfolioStateStore, CapitalGrantStore, SubmitAuthorizationStore and durable-message records as §6.2.1. SOURCE_EVIDENCE_R4 E07–E11; audit §3 FA-R4-02; REQUIREMENT_REVIEW_R4 AUD-P-01. | NR-151; §6.2; existing ST/TX rows; §7.6; §10.4; B8A/B8B/B8C/B9/B10 local scopes; B11/B13 verification; V18 | CLOSED — focused correction self-check; independent confirmation pending |
| FA-R4-03 — NON_BLOCKING | Add NR-152 with L01–L40 full observation classification and §40 visibility. Retain whole attempt/arrival/recovery/manual/cleanup/race histories and distinct auth/publication cutpoints; distinguish economic idempotency from captured-arrival retention. Reuse factual financial evidence with no new ledger; assign twelve tests and existing reviews at B9/B10 before B11/B13 verification. | ORDER_LIFECYCLE §40 L1666–L1693/§43 L1774–L1830, existing submission/close/idempotency/order/reconciliation paths; ORDER_EVENT financial_result source fields; current LifecycleSubmissionStore, LifecycleSetSyncStore, LifecycleReconciliationStore, LifecycleCloseAuthorityStore, LifecycleOrderEventStore and durable-message support as §6.3.1. SOURCE_EVIDENCE_R4 E12–E15; audit §3 FA-R4-03; REQUIREMENT_REVIEW_R4 AUD-L-01. | NR-152; §6.3; existing ST/TX rows; §7.6; §10.4; B9/B10 local scopes; B11/B13 verification; V19 | CLOSED — focused correction self-check; independent confirmation pending |

#### Actual protected-content comparison against supplied R4

The following sections were compared as exact UTF-8 text ranges against the supplied original R4, not inferred from its historical preservation tables. SHA-256 identifies the preserved section text; these are not hashes of the whole R5 file. New directly dependent observation sections sit outside these protected ranges.

| Preserved range | R4-to-R5 check | SHA-256 of unchanged text |
| --- | --- | --- |
| historical R001–R060 | BYTE_IDENTICAL | `bb0417f71f8a76026c72d856149d071122596e6045c2c0e8b8c9b31de1304bff` |
| contract graph / all twelve | BYTE_IDENTICAL | `402f00ec54fd010c107ae8a244b9dfd0e30b048f497afd41f4529dfb1fdfada4` |
| Position operand graph/F010 | BYTE_IDENTICAL | `6ba3e4ed91fcadbfd0523e1df0ddbe107e5984ad9d4081023d894b3dc72614d9` |
| legacy persistence fence | BYTE_IDENTICAL | `2b843ebe45b164e3a9f6eedf41a2d47847461aaaa6ff683203acc7e57cec6c05` |
| preflight/frontier/quantity/finality/lineage | BYTE_IDENTICAL | `a5b31a7e317d1f9152269ae1b64b8177e7154b0d5061fc026eed4757e01e3a37` |
| numeric primitives | BYTE_IDENTICAL | `61fe32436b4c1c88a8ce6bc3f599a135aae9a038ab095ea2410e0205c178e94e` |
| financial allocation algorithms | BYTE_IDENTICAL | `dc831c98c0d9e08b26d3a14478eb3674b12d8fa3017a3b9cebb71a43ce0ca943` |
| B0 branches / complete F013 | BYTE_IDENTICAL | `0c585b243dc387688ba6aa83276ebab30256ff9b60b598f859c7012ffdfe5d90` |
| checkpoint dependency DAG | BYTE_IDENTICAL | `c34b60219358380a5dd04837cd2acb9595a430330c939ba93da4291f32549526` |
| central review lists | BYTE_IDENTICAL | `0e42ca35fbdc4f2558e62241a64e9c7a9c77e0114229ae1a882f900342e8123c` |
| 20 invariants | BYTE_IDENTICAL | `75d77c2d5e96bad11b36709d35db370f6cacac230f6ec723bba12adbb172ffa6` |

Additional performed comparisons:
- All **147 unaffected existing NR rows** are byte-identical. Only NR-054/NR-055/NR-068 change among NR-001–NR-150. NR-151/NR-152 are the only new contiguous rows. The full R001–R060 crosswalk is unchanged.
- All **18 intrinsic object meaning and owner cells** are unchanged. F-001/F-002 consumer and F-004/F-005 input clarifications close FA-R4-01; F-003 and all Position/F-013/A/S object rows are unchanged in full. There is no arithmetic, threshold, weighting, mode or trading-parameter edit.
- All **39 state IDs, existing-representation, action and owner columns** are unchanged. Only required branch separation or observation-history descriptions/checkpoint/TX/replay membership extend existing families. No new direction, configuration-sum, observation-owner or canonical Research store is created.
- All **26 transaction IDs and owner/checkpoint columns** are unchanged. Necessary observation membership/tests are appended to existing mechanisms; preflight/frontier/finality/receipt/lineage text remains byte-identical. No distributed owner/native transaction is introduced.
- All **19 central mandatory-review lists** and each corresponding detailed token list remain byte-identical and equal. New local review scopes attach to existing categories. All **19 upstream and downstream dependency fields** are unchanged.
- Eight full checkpoint bodies are byte-identical: **B0, B1, B2, B3, B4, B6, B7A, B7B**. Other checkpoint edits are directly required classifier/observation scope, local tests/reviews, 152-group verification or current R5 readiness references.
- The complete **AT-NR-035 fourteen-case matrix, AT-NR-036 four-case matrix, AT-NR-053 A–H matrix and AT-NR-089 discriminator** are byte-identical. NR-035, NR-036 and ST.day are byte-identical. All twenty global invariant rows are unchanged, including invariant1's two direction scopes.
- All six supplied input files retain their original SHA-256 values. ZIPs are read-only evidence; no input member, backend file, methodology/schema, migration, dependency or existing audit was modified. Only one complete R5 Markdown deliverable is created.

#### Source-list and cross-reference verification

The active register contains exactly NR-001–NR-152; both new rows identify source clauses, owner, current evidence/gap, producer checkpoint, existing ST/TX membership, acceptance and review scope. P01–P33 cover all Portfolio §§51–53/63 obligations; L01–L40 plus §6.3.4 cover Lifecycle §43/§40. Each derivable observation names a retained immutable record/history basis; required missing fields/events are explicitly marked as additions inside the existing owner domain.

B8A/B8B/B8C produce their assigned Portfolio observations, B9 produces operational Lifecycle and separate Portfolio-return observations, and B10 produces the financial/receipt portions. B11/B13 verify; B14 independently audits. Denied/unavailable outcomes and duplicate arrivals have explicit persistence/replay rules; no lack of a success grant/order/result is used as an excuse to discard the required history. Source-defined authority and exact numerical policies override short diagnostic labels.

The correction adds no new methodology rule, new certified object, contract field/family, business edge, native authority or product decision. No independently verified runtime result is implied. All tests in the implementation map remain future implementation acceptance requirements; the checks performed here are document/source/diff checks only.

## 15. Historical R5 self-check, readiness and resubmission (not R6 evidence)

**Historical record only.** The following statements describe the prior R5 correction and its then-current inputs/counts. They were superseded for completeness by the supplied fresh R5 audit. R6 operative self-check and status are exclusively §16; none of the old READY/CLOSED/count claims below establishes R6 correctness.

The values below are **focused correction authoring checks**, not independent certification or executed backend test results. They reassess the three supplied R4 findings and their directly affected dimensions, carrying accepted unaffected scope only after the actual protected-content comparisons in §14.5. “Tests complete” means the **implementation acceptance plan** now covers the required source obligations; those tests must still be implemented, executed and independently reviewed at the stated checkpoints. No current runtime, PostgreSQL deployment, native profile, paper/live trading, deployment or profitability approval is implied.

The register now has 152 source-supported obligation groups: the existing 150, with three dependency mappings corrected, plus NR-151 and NR-152 for the two missing frozen owner-observation groups. The source-list item matrices specify retained evidence and exact owner-local production, transaction, replay, acceptance and review responsibilities. They do not amend the methodology.

### 15.1 FA-R4-01 focused self-check

```text
FA-R4-01_STATUS:
CLOSED

F001_F004_DEPENDENCY_PRESENT:
NO

F002_F004_DEPENDENCY_PRESENT:
NO

FORMATION_BRANCH_SEPARATE_FROM_CLASSIFIER:
YES

F004_INPUT_AUTHORITY_CORRECT:
YES

F005_CLASSIFIER_INPUT_AUTHORITY_CORRECT:
YES

CLASSIFIER_CAN_EVALUATE_WITH_F001_UNAVAILABLE:
YES

CLASSIFIER_CAN_EVALUATE_WITH_F002_FALSE:
YES

FINAL_MATCH_CAN_STILL_FAIL_FORMATION:
YES

B5A_DEPENDENCY_GRAPH_CORRECT:
YES

B5B_FINAL_RESOLUTION_GRAPH_CORRECT:
YES

FA_R4_01_DISCRIMINATOR_PRESENT:
YES

FORMULA_ARITHMETIC_CHANGED:
NO
```

### 15.2 FA-R4-02 focused self-check

```text
FA-R4-02_STATUS:
CLOSED

PORTFOLIO_OBSERVABILITY_REQUIREMENT_ID:
NR-151

COMPLETE_GATE_RESULT_FIELDS_MAPPED:
YES

ALL_EVALUATED_REASONS_RETAINED:
YES

DENIED_GRANT_HISTORY_RETAINED:
YES

CAPACITY_MISSED_OPPORTUNITIES_RETAINED:
YES

GRANT_CREATED_CONSUMED_CLOSED_TIMES_MAPPED:
YES

ROUNDING_RELEASE_OBSERVATION_MAPPED:
YES

RECONCILIATION_TIMING_REASON_MAPPED:
YES

PORTFOLIO_DIAGNOSTIC_REPLAY_DEFINED:
YES

PORTFOLIO_DIAGNOSTIC_TESTS_COMPLETE:
YES

PORTFOLIO_REVIEW_SCOPE_ASSIGNED:
YES

NEW_PORTFOLIO_ALLOCATOR_CREATED:
NO
```

### 15.3 FA-R4-03 focused self-check

```text
FA-R4-03_STATUS:
CLOSED

LIFECYCLE_OBSERVABILITY_REQUIREMENT_ID:
NR-152

DUPLICATE_EVENT_OBSERVATION_MAPPED:
YES

OUT_OF_ORDER_OBSERVATION_MAPPED:
YES

RECOVERY_CORRECTION_OBSERVATION_MAPPED:
YES

MANUAL_INTERVENTION_OBSERVATION_MAPPED:
YES

AUTHORIZATION_TIMESTAMPS_MAPPED:
YES

TERMINAL_SEND_TO_SET_TIMESTAMP_MAPPED:
YES

SIBLING_PROTECTION_CANCEL_TIMES_MAPPED:
YES

CLOSE_REMAINDER_RACE_MAPPED:
YES

ADDITIONAL_FILL_AFTER_CLOSE_INTENT_MAPPED:
YES

LIFECYCLE_FINANCIAL_DIAGNOSTICS_MAPPED:
YES

ECONOMIC_IDEMPOTENCY_VS_DIAGNOSTIC_RETENTION_DEFINED:
YES

LIFECYCLE_DIAGNOSTIC_TESTS_COMPLETE:
YES

LIFECYCLE_REVIEW_SCOPE_ASSIGNED:
YES

NEW_LIFECYCLE_CREATED:
NO
```

### 15.4 Regression verification

The protected ranges and actual byte-comparison results are in §14.5. Full original contract/owner topology, Position/F-010/F-013, day/base/NR-036/A-009, preflight/frontier/identifiers, finality/receipt, twenty invariants, separate native gate and Research/legacy isolation remain operative. Observation-only additions to persistence/replay do not change those authorities.

```text
UNRELATED_PLAN_REGRESSION:
NO

UNRELATED_SUBSTANTIVE_CHANGES:
NONE

CONTRACT_GRAPH_CHANGED:
NO

OWNER_MAPPING_CHANGED:
NO

NUMERIC_POLICY_CHANGED:
NO

DEPENDENCY_ORDER_CHANGED:
NO
```

### 15.5 Requirement count and coverage

```text
NORMALIZED_REQUIREMENT_COUNT:
152

NORMALIZED_REQUIREMENTS_ADDED:
2 — NR-151 and NR-152

EXPECTED_NEW_REQUIREMENTS:
2

HISTORICAL_ALIASES_CHANGED:
NO

MISSING_SOURCE_OBLIGATIONS_AFTER_CORRECTION:
0

UNMAPPED_REQUIREMENTS_AFTER_CORRECTION:
0
```

### 15.6 State and transaction preservation

No new logical state or transaction mechanism was necessary. Missing history fields/events use the already-mapped owner representations and existing UoW/transport. An owner-local raw capture or failed-attempt outcome uses the existing TX.owner mechanism, not a 27th transaction class or a second inbox/outbox.

```text
LOGICAL_STATE_COUNT:
39

NEW_LOGICAL_STATES:
NONE

NEW_LOGICAL_STATE_JUSTIFICATIONS:
NOT_APPLICABLE — observation fields/history extend existing owner state families.

TRANSACTION_MECHANISM_COUNT:
26

NEW_TRANSACTION_MECHANISMS:
NONE

TRANSACTION_TOPOLOGY_CHANGED:
NO

PERSISTENCE_TOPOLOGY_CHANGED:
NO

DUPLICATE_CANONICAL_STORE_INTRODUCED:
NO
```

### 15.7 Review and test-plan completeness

```text
ALL_CHECKPOINT_REVIEW_LISTS_SYNCHRONIZED:
YES

ALL_19_REVIEW_LISTS_MATCH:
YES

PORTFOLIO_OBSERVABILITY_REVIEW_SCOPE_COMPLETE:
YES

LIFECYCLE_OBSERVABILITY_REVIEW_SCOPE_COMPLETE:
YES

CLASSIFIER_FORMATION_DISCRIMINATOR_COMPLETE:
YES

OWNER_LOCAL_TESTS_COMPLETE:
YES

INTEGRATED_TESTS_COMPLETE:
YES

TEST_PLAN_COMPLETE:
YES

QUALITY_GATE_PLAN_CORRECT:
YES
```

### 15.8 Direct reassessment of previously failed planning dimensions

These are the correction author's scoped planning assessments; they do not grant implementation approval. Independent re-audit must verify the actual R5 text, original frozen clauses, source-grounded retained-record choices and absence of regression.

```text
NORMALIZED_REQUIREMENT_REGISTER_VALID:
YES

NORMALIZED_REQUIREMENTS_COVERED:
152/152

UNSUPPORTED_REQUIREMENTS:
0

MISSING_NORMATIVE_OBLIGATIONS:
0

DUPLICATIVE_OR_CONFLICTING_REQUIREMENTS:
0

UNMAPPED_REQUIREMENTS:
0

CERTIFIED_OBJECTS_CORRECT:
18/18

SET_DIRECTION_GRAPH_CORRECT:
YES

FORMULA_DEPENDENCY_GRAPH_CORRECT:
YES

NUMERIC_DATAFLOW_CORRECT:
YES

B5A_SCOPE_CORRECT:
YES

PERSISTENCE_PLAN_CORRECT:
YES

TRANSACTION_PLAN_CORRECT:
YES

B8B_SCOPE_CORRECT:
YES

B8C_SCOPE_CORRECT:
YES

B9_SCOPE_CORRECT:
YES

OWNER_LOCAL_REPLAY_PLAN_COMPLETE:
YES

TEST_PLAN_COMPLETE:
YES

QUALITY_GATE_PLAN_CORRECT:
YES

METHODOLOGY_AMBIGUITIES:
0
```

### 15.9 Architecture and authority preservation

```text
BUSINESS_OWNER_COUNT_CHANGED:
NO

CONTRACT_FAMILY_COUNT_CHANGED:
NO

CONTRACT_GRAPH_CHANGED:
NO

NEW_SET_STATE_MACHINE:
NO

NEW_PORTFOLIO_ALLOCATOR:
NO

NEW_LIFECYCLE:
NO

NEW_WORKER:
NO

NEW_ACCOUNTING_OWNER:
NO

NEW_DIRECTION_SERVICE:
NO

NEW_CONFIGURATION_SUM_SERVICE:
NO

RESEARCH_STORAGE_MIGRATION:
NO

FORMULA_ARITHMETIC_CHANGED:
NO

TRADING_BEHAVIOR_CHANGED:
NO

CHECKPOINT_ORDER_CHANGED:
NO

NATIVE_AUTHORITY_CHANGED:
NO
```

### 15.10 Correction-induced defects and readiness

One correction-induced acceptance-oracle error was detected during the final exact-arithmetic check and corrected before issuing this R5 artifact. It is recorded below rather than hidden behind a zero-defect self-check. No unresolved correction-induced finding remains. Independent re-audit must verify both this correction and the original three findings, including classifier/formation discrimination, all owner-observation subitems, their cross-references and protected-content comparison.

**FR5-01 — source-derived financial test-oracle arithmetic**

**SEVERITY:** NON_BLOCKING

**AREA:** NR-152 factual-financial observation acceptance oracle.

**EXACT DEFECT:** The initial R5 drafting of AT-NR-152 case 11 specified LONG quantity 2 bought at 100 and sold at 110 but stated gross 40 and net 38.9. With entry fee cost 1, exit rebate cost -0.2, allocated funding -0.3 and other costs 0, those expected values do not follow the frozen equations.

**FROZEN SOURCE:** `docs/trading-methodology/SYSTEM_PROTOCOLS.md` S06 L411–L418 requires exact attributable execution quantity-times-actual-price gross; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` L1368–L1375 specifies gross minus actual fee/rebate cost plus allocated funding minus other supported costs.

**R5 LOCATION:** §6.3.5 AT-NR-152 case 11 and its B10 TESTS_REQUIRED reference.

**WHY IT MATTERS:** A wrong expected value could reject correct factual accounting or encourage an implementation to match an erroneous test, despite unchanged source formulas.

**REQUIRED CORRECTION:** Keep the factual inputs and frozen arithmetic unchanged; replace both linked expected-value statements with gross 20 and net 18.9.

**CORRECTION APPLIED AND CHECKED:** `gross = 2*110 - 2*100 = 20`; `actual_fees_rebates = 1 + (-0.2) = 0.8`; `net = 20 - 0.8 + (-0.3) - 0 = 18.9`. Exact rational assertions verify both values. Both operative references now agree. No backend implementation, trading parameter, formula arithmetic or source file changed.

**STATUS:** CLOSED_IN_CORRECTION — independent confirmation pending.

The counts below refer to unresolved defects in the issued candidate. The authoring check detected one new non-blocking oracle error, corrected that one error and leaves zero unresolved correction-induced defects.

```text
NEW_R5_CORRECTION_DEFECTS:
FR5-01 — NON_BLOCKING; corrected and exact-arithmetic checked before issue; independent confirmation pending.

NEW_BLOCKING_PLANNING_DEFECTS:
0

NEW_NON_BLOCKING_PLANNING_DEFECTS:
0

READY_FOR_INDEPENDENT_REAUDIT:
YES

IMPLEMENTATION_APPROVAL:
NOT_GRANTED_BY_THIS_CORRECTION

BACKEND_IMPLEMENTATION_OR_RUNTIME_TESTS_EXECUTED:
NO

SUPPLIED_INPUT_FILES_MODIFIED:
NO
```

R5 is ready to be submitted for that independent re-audit only. A CLOSED author assessment does not satisfy the planning approval gate. Every later implementation checkpoint still requires implementation, applicable local tests, independent review and remediation/re-review before commit/push. B12 dispatch, separate native exposure approval, B13 integrated verification and B14 full implemented-backend re-audit remain mandatory. No backend batch is authorized by this artifact.

### 15.11 Required final correction summary

```text
FILES/ARTIFACTS_CREATED:
1

FA-R4-01:
CLOSED

FA-R4-02:
CLOSED

FA-R4-03:
CLOSED

F001_F004_DEPENDENCY_PRESENT:
NO

F002_F004_DEPENDENCY_PRESENT:
NO

FORMATION_BRANCH_SEPARATE_FROM_CLASSIFIER:
YES

F004_INPUT_AUTHORITY_CORRECT:
YES

CLASSIFIER_FORMATION_DISCRIMINATOR_PRESENT:
YES

PORTFOLIO_OBSERVABILITY_REQUIREMENT_PRESENT:
YES

PORTFOLIO_COMPLETE_GATE_RESULT_MAPPED:
YES

PORTFOLIO_ALL_EVALUATED_REASONS_RETAINED:
YES

PORTFOLIO_DIAGNOSTIC_REPLAY_DEFINED:
YES

LIFECYCLE_OBSERVABILITY_REQUIREMENT_PRESENT:
YES

LIFECYCLE_DUPLICATE_AND_OUT_OF_ORDER_OBSERVATIONS_MAPPED:
YES

LIFECYCLE_AUTHORIZATION_AND_TERMINAL_TIMES_MAPPED:
YES

LIFECYCLE_CLOSE_RACE_OBSERVATIONS_MAPPED:
YES

ECONOMIC_IDEMPOTENCY_VS_DIAGNOSTIC_RETENTION_DEFINED:
YES

NORMALIZED_REQUIREMENT_COUNT:
152

TRANSACTION_MECHANISM_COUNT:
26

UNRELATED_PLAN_SEMANTICS_CHANGED:
NO

READY_FOR_INDEPENDENT_REAUDIT:
YES
```

BACKEND_IMPLEMENTATION_MAP_R5_CORRECTION_STATUS:
READY_FOR_REAUDIT


## 16. R6 focused correction assessment and readiness — operative current status

### 16.1 FA-R5-01 correction ledger

**Scope:** This is a focused correction and self-check, not a full independent audit or implementation certification. The supplied fresh R5 audit’s two missing groups remain distinct; they are mapped as NR-153 (AUD-ENTRY-REPORT) and NR-154 (AUD-TP-REPORT), without historical R aliases. The 152 accepted core rows are carried from that audit and compared unchanged. Earlier self-checks in §§14–15 are historical only.

| Finding / obligation | Minimal correction implemented in this map | Original-source and actual-code basis | Assessment |
| --- | --- | --- | --- |
| FA-R5-01 / AUD-ENTRY-REPORT | NR-153; all E01–E19 items, explicit immutable lineage/cohorts/denominators, original raw/rounded metrics and canonical age, actual submit/refusal/fill outcomes, original FINAL-based expectancy and complete path/availability rules. ENTRY-RPT-01–15; source capture B3/B7A/B9/B10, report assembly B12, B11 source-only stress, V20/B13 verification and B14 review. | POSITION_RULES Part II §51 L3220–L3243 and adjacent §50; F-008 fields/algorithms and SET canonical age; actual ResearchService/ResearchStore/pins/analytics/cache gaps in §6.4.1; supplied FA-R5-01 and CR-M15/CR-S12/15/16 locators. | CLOSED — correction author’s planning assessment; independent re-audit required |
| FA-R5-01 / AUD-TP-REPORT | NR-154; all T01–T17 items, exact original type/thesis/traversal/failure lineage, original ATR distance, explicit target-touch/time/MAE/MFE cohorts with path-resolution honesty, original day/1h types and pinned one-axis min/max diagnostic sensitivity. TP-RPT-01–17; same original source checkpoints, B12 reporting, V21/B13 verification. | POSITION_RULES Part IV §48 L5464–L5485 and §47 research candidates; original F-010 output/selection/rounding semantics; actual source surfaces §6.4.1; supplied FA-R5-01 and CR-M16/CR-S12/15/16. | CLOSED — correction author’s planning assessment; independent re-audit required |

The correction does not claim frozen source prescribes every analytical denominator or sampling convention. §6.4 explicitly fixes/pins those diagnostic conventions and requires explicit research experiment values where appropriate. This closes the implementation mapping without silently adding a trading rule or an automatic optimization policy. Source support for required reports is distinct from source availability for a particular historical dataset.

### 16.2 Actual protected-content and structural checks

The comparisons below use the actual supplied R5 UTF-8 content and this R6 candidate, not historical preservation banners. Hashes identify preserved original section text, not the whole replacement file.

| Protected range | R5 → R6 comparison | SHA-256 of unchanged section text |
| --- | --- | --- |
| 12-contract graph | BYTE_IDENTICAL | `402f00ec54fd010c107ae8a244b9dfd0e30b048f497afd41f4529dfb1fdfada4` |
| 18 objects and independent Set/Position discriminators | BYTE_IDENTICAL | `f993833a90f180617cf19378f474b3835ffe779cc6ed9f2b62468e0352918f9d` |
| Portfolio P01–P33 and 12 cases | BYTE_IDENTICAL | `82de5a5cf9bbdc5dab0dc20f62a31907b4e09ff1a5f8900cdc545fe897aed847` |
| Lifecycle L01–L40/visibility/12 cases | BYTE_IDENTICAL | `3a6baf1eeb870879b8716c90051bf6579ab944d6d2884a12074f619f5ee10657` |
| known preflight/frontier/source/close/final/receipt/lineage | BYTE_IDENTICAL | `a5b31a7e317d1f9152269ae1b64b8177e7154b0d5061fc026eed4757e01e3a37` |
| NR151/152 observation transaction membership | BYTE_IDENTICAL | `09a72ca1bb230bfafbdd8b756c2ad25740fc0df51b318491e1feaa7a2ea9c41a` |
| existing exact numeric policy/dataflow | BYTE_IDENTICAL | `f5c9e0a26e894c253b53a779ee09cd443a059168e6315b329f79fe6d2a9410bd` |
| strict parser and F013 | BYTE_IDENTICAL | `0c585b243dc387688ba6aa83276ebab30256ff9b60b598f859c7012ffdfe5d90` |
| 20 global invariants | BYTE_IDENTICAL | `75d77c2d5e96bad11b36709d35db370f6cacac230f6ec723bba12adbb172ffa6` |

The following additional structural checks were performed:

- Exactly NR-001–NR-154 occur as contiguous unique register rows. All 152 pre-existing rows are byte-identical; only NR-153/NR-154 are appended. The two new rows explicitly resolve their producer, read-only consumer, original source, state/transaction membership, acceptance and review scope. The complete R001–R060 crosswalk remains unchanged; neither reporting group gains an alias.
- Exactly 39 existing logical-state IDs remain in the same order. Only the ST.position descriptive report-source extension and ST.research diagnostic scope/action/checkpoint/replay row change in the central state table. The remaining 37 central state rows are byte-identical. Documentary child records/raw objects do not create a 40th canonical state family or duplicate store.
- All 26 original transaction-definition rows are byte-identical. §7.7 explains added source-field membership and independent diagnostic SQLite/file persistence, not a new canonical mechanism. Canonical four-owner native/finality/receipt topology remains unchanged.
- All 19 checkpoint headings, their order and detailed upstream/downstream prerequisite lists are unchanged. Eleven full checkpoint bodies remain byte-identical: B0, B1, B2, B4, B8A, B5A, B5B, B6, B8B, B7B and B8C. Changes in B3/B7A/B9/B10/B11/B12/B13/B14 are directly assigned report retention, local assembly/test/review, current total coverage or integrated/audit scope; B11 remains verification-only and B13 is not a producer.
- All 19 central/detailed mandatory-review lists match exactly with no duplicate tokens. Only B12 adds three already-existing categories for the new explicit report implementation: NUMERIC_PRECISION_REVIEW, ADVERSARIAL_TRADING_REVIEW and PERSISTENCE_TRANSACTION_REVIEW. Other checkpoint review lists remain unchanged; source-specific local responsibilities are assigned in §10.5.
- E01–E19 and T01–T17 are complete unique source-list mappings, with exact original physical list lines. ENTRY-RPT-01–15 and TP-RPT-01–17 are complete unique acceptance rows. V20/V21 are integrated reporting scenarios, not new global invariants. The existing 20-invariant table is byte-identical; the named reporting invariant specializes invariant 6.
- Table-column structure and new section/cross-reference presence were checked; required additions contain no placeholders. Existing source paths and named reusable symbols in §6.4.1 were inspected in the actual snapshot. No report method, tick-data feed or completed report store is falsely labeled already implemented.
- All seven supplied input files were rehashed unchanged against §1.2. The ZIPs and their source bytes were used read-only. Only this full R6 Markdown file is issued as a deliverable; no backend code, frozen methodology, schema, migration, audit report or original R5 file was modified.

Independent exact rational calculations confirm the new fixture values: Entry improvement2/10=1/5, percent100/51, raw shallow0.05/deep1.7; selected raw98.75 floors to98.7 on tick0.1 and has rounded depth1.3 at M100/ATR1; canonical age ceil60.75=61; two full outcomes18.9 and−8.9 have mean5; both directional path fixtures have adverse2/favorable12; TP baseline distance1 and alternative1.5/3.5 have the stated threshold relationships. The protected factual gross20/net18.9 arithmetic remains unchanged. These are arithmetic/source-plan checks, **not executed backend/SQLite/PostgreSQL/native tests**.

### 16.3 Complete Entry reporting self-check

YES below means an explicit planning mapping, source-retention/availability definition and assigned acceptance/review responsibility exist. It does not mean that current backend report code has run or every historical path is available.

```text
ENTRY_REPORT_REQUIREMENT_PRESENT:
YES

ENTRY_REPORT_REQUIRED_ITEMS:
19

ENTRY_REPORT_ITEMS_MAPPED:
19/19

ENTRY_REPORT_LONG_SHORT_SPLIT:
YES

ENTRY_REPORT_COIN_DIMENSION:
YES

ENTRY_REPORT_SET_FAMILY_DIMENSION:
YES

ENTRY_REPORT_REFERENCE_TYPE:
YES

ENTRY_IMPROVEMENT_ATR_MAPPED:
YES

ENTRY_IMPROVEMENT_PCT_MAPPED:
YES

ENTRY_FILL_RATE_MAPPED:
YES

ENTRY_TIME_TO_FILL_MAPPED:
YES

ENTRY_MISSED_TRADE_RATE_MAPPED:
YES

ENTRY_TOO_SHALLOW_FREQUENCY_MAPPED:
YES

ENTRY_TOO_DEEP_FREQUENCY_MAPPED:
YES

ENTRY_POST_ROUND_TOO_DEEP_FREQUENCY_MAPPED:
YES

ENTRY_POST_ONLY_REJECTION_FREQUENCY_MAPPED:
YES

ENTRY_TECHNICAL_INCOMPATIBILITY_FREQUENCY_MAPPED:
YES

ENTRY_REFERENCE_AGE_MAPPED:
YES

ENTRY_EXPECTANCY_BY_DISTANCE_BAND_MAPPED:
YES

ENTRY_ADVERSE_EXCURSION_MAPPED:
YES

ENTRY_FAVORABLE_EXCURSION_MAPPED:
YES

ENTRY_REPORT_COHORTS_EXPLICIT:
YES

ENTRY_REPORT_LINEAGE_EXPLICIT:
YES

ENTRY_REPORT_PATH_EVIDENCE_COMPLETE:
YES

ENTRY_REPORT_REPLAY_DEFINED:
YES

ENTRY_REPORT_LOCAL_TESTS_COMPLETE:
YES

ENTRY_REPORT_REVIEW_SCOPE_COMPLETE:
YES
```

### 16.4 Complete TP reporting self-check

```text
TP_REPORT_REQUIREMENT_PRESENT:
YES

TP_REPORT_REQUIRED_ITEMS:
17

TP_REPORT_ITEMS_MAPPED:
17/17

TP_REPORT_LONG_SHORT_SPLIT:
YES

TP_REPORT_COIN_DIMENSION:
YES

TP_REPORT_SET_FAMILY_DIMENSION:
YES

TP_REPORT_TARGET_TYPE:
YES

TP_THESIS_OVERRIDE_FREQUENCY_MAPPED:
YES

TP_NO_REACHABLE_TARGET_FREQUENCY_MAPPED:
YES

TP_TOO_CLOSE_FREQUENCY_MAPPED:
YES

TP_TOO_FAR_FREQUENCY_MAPPED:
YES

TP_DISTANCE_ATR_MAPPED:
YES

TP_TIME_TO_TARGET_MAPPED:
YES

TP_MAE_BEFORE_TARGET_MAPPED:
YES

TP_MFE_MAPPED:
YES

TP_TARGET_HIT_RATE_MAPPED:
YES

TP_PREVIOUS_DAY_VS_1H_MAPPED:
YES

TP_MIN_DISTANCE_SENSITIVITY_MAPPED:
YES

TP_MAX_DISTANCE_SENSITIVITY_MAPPED:
YES

TP_REPORT_COHORTS_EXPLICIT:
YES

TP_REPORT_LINEAGE_EXPLICIT:
YES

TP_REPORT_PATH_EVIDENCE_COMPLETE:
YES

TP_REPORT_REPLAY_DEFINED:
YES

TP_REPORT_LOCAL_TESTS_COMPLETE:
YES

TP_REPORT_REVIEW_SCOPE_COMPLETE:
YES
```

### 16.5 Research isolation, state and transaction preservation

```text
RESEARCH_REPORTS_READ_ONLY:
YES

RESEARCH_REPORTS_CAN_CHANGE_POSITION:
NO

RESEARCH_REPORTS_CAN_CHANGE_SET:
NO

RESEARCH_REPORTS_CAN_CHANGE_PORTFOLIO:
NO

RESEARCH_REPORTS_CAN_CHANGE_LIFECYCLE:
NO

AUTOMATIC_PARAMETER_OPTIMIZATION_INTRODUCED:
NO

NEW_RESEARCH_PROMOTION_MECHANISM_INTRODUCED:
NO

RESEARCHSTORE_MIGRATION_INTRODUCED:
NO

NEW_CANONICAL_BUSINESS_EDGE_INTRODUCED:
NO

LOGICAL_STATE_COUNT:
39

NEW_LOGICAL_STATE_FAMILIES:
0

NEW_LOGICAL_STATE_JUSTIFICATIONS:
NOT_APPLICABLE — existing ST.research/ST.position and original source histories are extended; diagnostic child records are not another canonical state family

TRANSACTION_MECHANISM_COUNT:
26

NEW_TRANSACTION_MECHANISMS:
0

TRANSACTION_TOPOLOGY_CHANGED:
NO

DUPLICATE_CANONICAL_STORE_INTRODUCED:
NO

RESEARCH_STORAGE_ROLES_CHANGED:
NO
```

ResearchStore and OperatorStateStore remain SQLite; PostgreSQL ResearchPromotionGovernanceStore remains narrowly promotion-request/outbox governance only. Adding immutable diagnostic records to the existing ResearchStore is not migration or a new Research subsystem. No 27th canonical transaction, new financial ledger, business wire field or trading owner is introduced.

### 16.6 Regression protection and directly reassessed failed dimensions

The protected NR-035 row, complete B8A daily-base/AT-NR-035 14-case matrix, NR-036 row and four-case allocation matrix, classifier/formation and AT-NR-068-CF A–D, F-005 scopes/AT-NR-053 A–H, F-010 independence/AT-NR-089, F-013, both complete existing observability tables/cases, A-004/A-009/S-004, financial oracle, preflight/frontier/finality/receipt, native safety and 20-invariant core remain unchanged. B9/B10 additions capture only their own report-source facts; B12 adds separate read-only diagnostic functions, not dispatcher formulas or additional exposure authority. The unchanged 152-row core’s source support is carried from the supplied full audit; this scoped check does not purport to independently re-audit all unrelated clauses anew.

```text
UNRELATED_PLAN_REGRESSION:
NO

UNRELATED_SUBSTANTIVE_CHANGES:
NONE

NORMALIZED_REQUIREMENT_COUNT:
154

NORMALIZED_REQUIREMENTS_RECONSTRUCTED:
154

NORMALIZED_REQUIREMENTS_REVIEWED:
154

NORMALIZED_REQUIREMENTS_COVERED:
154/154

NORMALIZED_REQUIREMENT_REGISTER_VALID:
YES

UNSUPPORTED_REQUIREMENTS:
0

MISSING_NORMATIVE_OBLIGATIONS:
0

DUPLICATIVE_OR_CONFLICTING_REQUIREMENTS:
0

UNMAPPED_REQUIREMENTS:
0

TRANSACTION_MAPPING_ERRORS:
0

REVIEW_ASSIGNMENT_ERRORS:
0

PERSISTENCE_PLAN_CORRECT:
YES

OWNER_LOCAL_REPLAY_PLAN_COMPLETE:
YES

TEST_PLAN_COMPLETE:
YES

OWNER_LOCAL_TESTS_COMPLETE:
YES

INTEGRATED_TESTS_COMPLETE:
YES

QUALITY_GATE_PLAN_CORRECT:
YES

ALL_19_REVIEW_LISTS_MATCH:
YES

MISSING_REQUIRED_REVIEWS:
NONE

METHODOLOGY_AMBIGUITIES:
0
```

Counts are at the full audit’s obligation-group granularity: 152 preserved mapped core groups plus two newly explicit report groups. REVIEWED here means the focused mapping/cross-reference/protected-core assessment, not new full independent certification. Two original required-report scopes and their previously absent evidence/test/review mappings are now explicit; they are not merged away into NR-086/090. Reporting experiment configuration left unspecified by the source is handled through required pinned inputs or explicit unavailability, not a new unresolved trading-policy choice. Test/replay/persistence completeness is a planning assessment: all actual implementation gates and execution evidence remain future requirements.

### 16.7 Correction-induced findings and readiness

```text
NEW_R6_CORRECTION_DEFECTS:
NONE

NEW_BLOCKING_PLANNING_DEFECTS:
0

NEW_NON_BLOCKING_PLANNING_DEFECTS:
0

READY_FOR_INDEPENDENT_REAUDIT:
YES

IMPLEMENTATION_APPROVED_BY_THIS_CORRECTION:
NO
```

No unresolved correction-induced planning defect was found in the scoped checks. Independent re-audit must validate the actual R6 mapping, including the expressly diagnostic cohort/path conventions, truthful acquisition limits, quantitative test oracles, same-store persistence and absence of feedback. This is not APPROVED_FOR_IMPLEMENTATION. No backend batch, PostgreSQL runtime, native exchange integration, deployment or trading readiness is certified. Each later checkpoint still requires implementation, actual tests, independent review, correction/re-review before commit/push; separate B12 dispatch/native gates, B13 integrated verification and B14 implemented-backend audit remain mandatory.

### 16.8 Required R6 final correction summary

```text
FILES/ARTIFACTS_CREATED:
1

FA-R5-01:
CLOSED

ENTRY_REPORT_REQUIREMENT_PRESENT:
YES

ENTRY_REPORT_ITEMS_MAPPED:
19/19

ENTRY_REPORT_COHORTS_EXPLICIT:
YES

ENTRY_REPORT_LINEAGE_EXPLICIT:
YES

ENTRY_REPORT_PATH_EVIDENCE_COMPLETE:
YES

ENTRY_REPORT_REPLAY_DEFINED:
YES

ENTRY_REPORT_LOCAL_TESTS_COMPLETE:
YES

ENTRY_REPORT_REVIEW_SCOPE_COMPLETE:
YES

TP_REPORT_REQUIREMENT_PRESENT:
YES

TP_REPORT_ITEMS_MAPPED:
17/17

TP_REPORT_COHORTS_EXPLICIT:
YES

TP_REPORT_LINEAGE_EXPLICIT:
YES

TP_REPORT_PATH_EVIDENCE_COMPLETE:
YES

TP_REPORT_REPLAY_DEFINED:
YES

TP_REPORT_LOCAL_TESTS_COMPLETE:
YES

TP_REPORT_REVIEW_SCOPE_COMPLETE:
YES

RESEARCH_REPORTS_READ_ONLY:
YES

AUTOMATIC_PARAMETER_OPTIMIZATION_INTRODUCED:
NO

NEW_RESEARCH_PROMOTION_MECHANISM_INTRODUCED:
NO

RESEARCHSTORE_MIGRATION_INTRODUCED:
NO

NEW_CANONICAL_BUSINESS_EDGE_INTRODUCED:
NO

NORMALIZED_REQUIREMENTS_RECONSTRUCTED:
154

NORMALIZED_REQUIREMENTS_COVERED:
154/154

NORMALIZED_REQUIREMENT_REGISTER_VALID:
YES

MISSING_NORMATIVE_OBLIGATIONS:
0

UNMAPPED_REQUIREMENTS:
0

PERSISTENCE_PLAN_CORRECT:
YES

OWNER_LOCAL_REPLAY_PLAN_COMPLETE:
YES

TEST_PLAN_COMPLETE:
YES

QUALITY_GATE_PLAN_CORRECT:
YES

LOGICAL_STATE_COUNT:
39

TRANSACTION_MECHANISM_COUNT:
26

UNRELATED_PLAN_REGRESSION:
NO

READY_FOR_INDEPENDENT_REAUDIT:
YES
```

BACKEND_IMPLEMENTATION_MAP_R6_CORRECTION_STATUS:
READY_FOR_REAUDIT
