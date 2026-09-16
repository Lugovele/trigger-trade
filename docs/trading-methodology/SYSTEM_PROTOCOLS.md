# TriggerTrade — Canonical Cross-Document Protocols v1.2.15


This document specifies shared invariants used by the four existing business blocks. It is not a new business block, service boundary, trading strategy, or exchange-conformance certificate. Methodology sections and contracts incorporate these named protocols. They must not define competing versions.

## P1 — Topology and approval/construction sequence

The business blocks remain Portfolio Rules (capital), Set (market analysis), Position Rules (trade decision), and Order Lifecycle (order management). API remains a factual/technical interface. The diagram is unchanged. The nine business boundaries and three API boundaries are enumerated in the contract indexes. Position Rules has no direct API dependency. Portfolio sends no capital to Set.

The generic Trigger-result/event contract is fully defined in `methodology/SET.md`, Part I §§10–12 and §17. CURRENT_STATE requires current authoritative TRUE; FRESH_EVENT requires an authoritative FALSE -> TRUE transition in the same active OPEN formation epoch, with no intervening UNAVAILABLE. Its timestamp is the TRUE evaluation's authoritative effective time. Set persists evaluation/event identities, interruptions, consumption and original temporal anchors atomically with dependent formation effects; replay/restart never synthesizes a fresh event from current TRUE or resets its clock. Effective CLOSE/newer OPEN discards unfinished old-epoch Trigger state without changing an existing cycle or pending monitor. P17 configuration binding and P16 evidence eligibility remain prerequisites. There is no external Trigger Contract dependency or additional wire boundary.

The sequence is:

```text
Portfolio → Set: Coins OPEN / CLOSE
Set: analyze; persist concrete MATCHED Core Set + Frozen Condition + exact reference bindings
Set → Position: Market Handoff(decision_cycle_id, set_result_id, direction, contexts)
Position: evaluate the opportunity from frozen market inputs and configured Position rules
Position → Portfolio: OPPORTUNITY_DECISION(APPROVE | REJECT)
REJECT: end this opportunity; no grant, hold, tranche, spec, authorization or native order
APPROVE: Portfolio may now issue Capital and Limits for this exact approved decision
Portfolio → Position: Capital and Limits(capital_grant_id, decision_cycle_id, position_decision_id, facts)
Position: finalize leverage, quantity, notional, committed capital and all planned economics
Position: atomically persist successful construction, immutable Order Spec and both outgoing records
Position → Lifecycle: Order Spec
Position → Portfolio: CONSTRUCTION_RESULT(CONSTRUCTED), on the existing Approve / Reject boundary
Portfolio: atomically recheck current gates/capacity and book SUBMISSION_HOLD
Portfolio → Lifecycle: Submit Authorized / Order Submit
Lifecycle: wait for matching spec + authorization; hard non-market compatibility; exact native submit
```

The construction confirmation is a **post-grant variant on the existing Position → Portfolio boundary**, not a second market decision or a new arrow. It moves the former APPROVE-only final economics to the point where they actually exist. It is needed so Portfolio can bind the exact spec and capital before authorizing it. A construction failure emits `CONSTRUCTION_RESULT(REJECT)` on that same boundary, with the existing gate diagnostics and no fabricated successful plan/spec. No hold follows that failure.

When Position first evaluates a Market Handoff it atomically selects and persists the exact Position Rules configuration binding for that `decision_cycle_id` before producing the initial APPROVE/REJECT. That same pinned binding governs every later post-grant construction calculation for the cycle; a newly activated Position configuration applies only to future Position decision cycles. Initial APPROVE validates the pinned configuration, immutable Set direction, required market inputs/references, Entry/SL/TP feasibility and geometry, and enabled gross Minimum R:R. Those quantities do not require allocated capital. Existing formulas and thresholds are unchanged. Capital, quantity, leverage compatibility, actual notional and fee-aware Minimum Net Edge are evaluated only after the grant. The initial decision records `construction_gates = NOT_YET_EVALUATED`; it does not falsely mark those gates PASS, UNAVAILABLE or NOT_APPLICABLE. The ordinary four-valued rule-result model is used when the post-grant gates actually run. A disabled Minimum Net Edge remains NOT_APPLICABLE; an enabled successful one is PASS. No final spec can contain FAIL/UNAVAILABLE.

Position persists one `position_decision_id` and one initial decision per cycle. The initial decision contains **no** `capital_grant_id`, `position_plan_id`, `tranche_id`, `order_spec_id`, or approved final economics. Portfolio creates `capital_grant_id` only after a persisted initial APPROVE, in the transaction that persists the immutable grant and its outbox message. Grant uniqueness is by the approved decision/cycle: duplicate APPROVE republishes the same grant, never allocates another. A rejection or conflicting decision replay is not a new opportunity.

`position_plan_id`, `tranche_id` and `order_spec_id` are finalized only by successful post-grant construction. `construction_result_id` is Position-owned and identifies that construction outcome. A failed construction may have internal calculation/audit records but no invented successful spec. The spec and its CONSTRUCTED confirmation are published durably together; delivery order is immaterial. Portfolio's hold can be triggered only by this complete confirmation, not by initial APPROVE. If it reaches Portfolio before the spec reaches Lifecycle, the hold remains intact and Lifecycle waits. A spec without authorization has no execution authority.

The exact Order Spec digest and all lineage fields must match between construction confirmation, Portfolio binding and authorization. Position never changes a previously constructed spec to make a failed hold succeed. Portfolio atomically validates LIVE/coherent state, Daily Loss latch, symbol scope/policy, cooldown, coin/global capacity and slots, grant existence and approved-cycle binding, and one-time consumption. Hold uses exactly the canonical constructed `actual_committed_capital`, independently equal to confirmation/spec/authorization values and not greater than the grant. Unused grant capacity was never held; acceptance only reclassifies this same amount under the existing entry allocation rules. First successfully bookable **constructed** approval wins. Failed hold means no authorization or submission, not a new analysis or silent resize.

Grants consume no capital/slots. A delayed or temporarily unissuable grant cannot authorize exposure. Waiting for durable delivery does not create an expiry rule; no pending-order, grant, authorization or proposal age TTL exists. An initial APPROVE is not a guarantee that capital will ultimately be available. Same-symbol opportunities are never joined by symbol or arrival order.



## P2 — Immutable grants and current hard execution compatibility

A grant is one immutable factual/capital snapshot bound to its original `decision_cycle_id`, `set_result_id`, `position_decision_id` and symbol. Portfolio persists the source Portfolio-state revision, instrument metadata revision/provenance, native-profile revision and fee schedule version/effective time. Subsequent facts or grants never mutate it, cause an age expiry, or rebind it to another opportunity. A delayed identical grant is usable only for its own unresolved approved construction. An already completed/rejected/consumed opportunity cannot be restarted by replay. Conflicting content for an existing ID is an integrity failure.

Position uses Market Handoff for frozen market geometry and Capital and Limits for the governed capital/venue inputs. Initial price construction uses the Set-provided frozen tick geometry. Post-grant validation verifies that those exact prices remain technically representable; it does not reprice them on a metadata change. Missing required factual values produce a construction failure, not guesses. No vague age-based “fresh enough” condition is a trading gate.

Before entry submission Lifecycle obtains coherent current **hard non-market execution facts** through its existing Order Management API boundary (`GET_HARD_EXECUTION_FACTS`, or an adapter-equivalent operation with the identical normalized payload). It records the approved and checked revisions and the comparison. The current hard set is instrument support/product/profile, price tick and quantity step, applicable minimum/maximum quantity, applicable minimum limit-order notional calculated from the exact Entry × quantity, maximum leverage, and native-side leverage/mode compatibility. Required unavailable or contradictory hard facts block submission through the technical failure/reconciliation path. A known newer revision can invalidate execution **only if the exact spec violates a hard constraint**. The numerical revision label itself is not a gate. Opaque revision IDs are not lexically ordered; currentness comes from authoritative source provenance/coherent refresh, never arrival order. Conflicting purportedly current revisions remain UNAVAILABLE until reconciled.

```text
old maximum 100; new maximum 80; exact quantity 70 → compatible; submit unchanged
old maximum 100; new maximum 80; exact quantity 90 → incompatible; no entry create
```

A fee-rate revision is factual provenance, not a native hard order-admissibility constraint. It neither reprices nor recomputes the immutable planned economics; actual fees are accounted from complete realized evidence. Set is not rerun, grant age is not tested, and Entry/SL/TP, leverage and quantity are not silently changed. The atomic Portfolio hold separately rechecks current Portfolio gates/capacity; the grant is not a capacity reservation.

Definitive local hard incompatibility before any create intent has been dispatched produces `SUBMISSION_FAILED` with `HARD_EXECUTION_CONSTRAINT_INCOMPATIBLE` and checked-fact provenance. Required facts temporarily unavailable remain RECONCILING with hold retained. Hold/slot release for definitive no-create failure requires durable proof that no create was sent or remained in flight. An ambiguous prior submit is reconciled, never declared failed merely because a later hard constraint changed. Definitive no-create terminalization atomically consumes the authorization/spec and records proof before release; new compatible facts, old authorization delivery and restart cannot reactivate it or rebook its hold (P14).

## P3 — POST_ONLY belongs to the exchange

```text
exact approved LIMIT + POST_ONLY
→ exchange submit
→ exchange acceptance/rejection/cancellation
```

Local validation covers only deterministic non-market schema, identifiers, supported instrument/profile, precision, hard quantity/notional/leverage constraints, request construction and transport readiness. Best bid/ask must not be compared with Entry as a submit gate; no local prediction of native POST_ONLY cancellation, resting-time requirement, Entry movement, chase, reprice or MARKET fallback exists. An accepted order that fills immediately is valid. Native rejection/cancellation follows the existing zero-fill or fill/reconciliation path according to actual executions, not a predicted result.

## P4 — Exact producer-bound thesis references

All reference roles, indicators, timeframes and reference levels are inherited from the exact versioned Trigger/Set configuration and concrete MATCHED Core Set that produced the cycle. Configuration defines a scoped `role_id` (unique nonempty string within a Set version) and an explicit relation to `(core_set_constituent_id, trigger_id, trigger_version, reference_key, indicator_id, timeframe)`. A constituent identifies its configured slot, not a level category. The concrete matched occurrence persists `trigger_occurrence_id` and its reference-key → `level_id` mapping. Set persists the join as `binding_id`, with Core Set, constituent, occurrence and exact level identity.

Neither the role nor the indicator name is a ranking instruction. When two SWING_LOW_15M levels exist, the originating Trigger occurrence already identifies which concrete level participated. Set copies that relation; it does not choose latest/closest/strongest/nearest after MATCHED. Distinct occurrences are distinguished by their persisted constituent/occurrence identity, never by heuristics.

REQUIRED demands one uniquely bound, available-at-match reference in the frozen level array; missing, inconsistent or nonunique binding makes the handoff UNAVAILABLE and emits no valid Market Handoff. PREFERRED uses the exact configured binding when available; a genuinely absent configured reference may be null and use the already-approved Dynamic Entry/SL/TP fallback. A nonunique/conflicting purported binding is an integrity error, not permission to guess. NONE has null thesis ID and null origin binding. Reference identity and origin binding must agree.

Position validates/consumes the binding and cannot reconstruct, replace or infer the thesis reference. The existing Dynamic Entry/SL/TP **default candidate hierarchies and tie-breakers**, used only by the already-approved PREFERRED/NONE fallback rules, are unchanged. They select a calculation candidate, not a replacement Set thesis binding; diagnostic selected-reference output is distinct from the immutable thesis ID. REQUIRED never falls back. Frozen Condition remains solely in Set's persisted cycle; it is not sent to Position. Order Placed activates only the exact cycle's stored condition.

## P5 — Atomic acquire-or-join and reduction authority

Lifecycle provides one atomic durable `acquire_or_join_close_intent(tranche_id, cause_event_id)` operation. In a serializable transaction (or equivalent compare-and-set with a persistent unique active-intent constraint), it locks the tranche identity, checks the active-intent record, and returns the existing ID or persists exactly one new `close_intent_id` with the tranche index and intent ledger. Every TP/SL callback, Manual Close, repeated request, retry, reconnect, restart and duplicate/racing delivery calls this operation. No path may independently mint and publish a second active intent. A completed tranche returns the persisted resolved intent/tombstone and performs no new close. Lost local candidate IDs before commit have no durable existence.

For each `tranche_id`, there is at most one active close intent. Active states are ACQUIRED, RECONCILING_CHILDREN, REDUCTION_AUTHORIZED, REDUCTION_UNCERTAIN, AWAITING_EXECUTIONS and AWAITING_FINALITY. RESOLVED is terminal. State/intent revisions are persistent; worker leases alone are not exclusivity. A stale worker cannot authorize a child after its revision loses the transaction. The intent retains all cause events; callback arrival order does not rewrite factual exit classification. Native executions, rather than the first caller, determine actual close attribution. The final economic closing execution's actual role determines TP/SL/Manual close classification; venue-originated reductions retain their external classification.

The intent ledger stores at least: `close_intent_id`, `tranche_id`, `intent_revision`, state, cause-event IDs, entry IDs, protection child IDs/generations, close child IDs, native side, `confirmed_target_quantity`, `confirmed_residual_quantity`, `authorized_reduction_quantity`, `executed_reduction_quantity`, unresolved requests, exposure/authority revisions and close commitment quantity basis. Child IDs and supported client IDs are persisted before side effects; native order IDs remain null until supplied by the exchange.

`confirmed_target_quantity` is cumulative uniquely attributed entry execution quantity, including fills racing entry cancellation. `executed_reduction_quantity` counts uniquely attributed exit executions exactly once. `confirmed_residual_quantity = confirmed_target_quantity - executed_reduction_quantity`. A negative result is an attribution/execution integrity incident, not a zero clamp. An execution assigned to this tranche cannot simultaneously be assigned to another. `authorized_reduction_quantity` on a child is its immutable requested budget; unresolved unexecuted budget is still live authority until authoritative terminal evidence removes it. Aggregated native reduce-only is not, by itself, proof of logical-tranche isolation.

Canonical execution order:

```text
atomic acquire-or-join by tranche_id
→ persist close state; prevent new entry intent for that tranche
→ cancel/reconcile this tranche's entry remainder
→ reconcile/cancel/disable competing tranche-owned protection and exit children
→ ingest attributed executions and prove all earlier ambiguous requests resolved
→ under the same tranche/authority serialization, calculate confirmed residual
→ atomically authorize at most one next reduction child and persist its outbox request
→ submit that exact quantity-scoped reduce-only child once
→ reconcile execution/terminal evidence before any further child authorization
→ cleanup + financial finality + atomic canonical CLOSED
```

Residual calculation and authorization serialize against entry fills, exit allocations, all protective-child state, every competing child claim and outstanding ambiguous request. Before a **new** reduction child, the entry remainder must be terminal and all other potentially executing reduction children terminal or authoritatively disabled; residual must be strictly positive and no unconsumed previous authorization may remain. Unknown competing authority keeps RECONCILING. A timeout cannot release a child claim or justify a new client ID. Only a confirmed terminal partial child permits a subsequent child for the recalculated residual; it is the same intent, not a strategic partial close.

Executions racing cancellation are applied before residual authorization. A passive TP/SL execution callback joins the same intent, even when the native child executed before callback arrival. Software does not retroactively prevent native double execution: the pinned adapter's conformance gate must establish quantity-scoped protection and competing-child isolation before exposure. If that cannot be established, the relevant exposure-changing profile remains disabled. An actual unexplained native over-reduction is preserved as an unresolved native observation, never assigned to another tranche merely to balance a number.

Restart reloads the unique tranche→intent index, intent/child records, source-execution inbox, outstanding authorization budgets and outboxes before permitting another side effect. Crash before intent commit means no intent/child exists; crash after commit rejoins the same one. Crash around child dispatch leaves an uncertain dispatch record requiring native reconciliation; it never allows blind resubmission. Replaying equivalent cause events is a no-op. These are implementation obligations, not assertions that a backend already implements database transactions.

## P6 — CLOSED is one unified predicate composed of six required conditions and explicit retained commitment

CLOSED requires **all six** authoritatively established predicates:

```text
logical exposure = 0
entry remainder terminal
all tranche-owned protective/exit children terminal or authoritatively disabled
active close intent fully resolved
financial finality established
no unresolved competing execution authority
```

Physical flatness alone is not CLOSED. While any predicate is false the closing tranche remains CLOSE_PENDING or RECONCILING. Manual-intervention escalation is a health/incident condition; it cannot release a closing tranche's capital/slot. TP, SL, Manual Close, external close, Portfolio, Order Event and restart use exactly these predicates. Zero-fill cancellation and definitive no-create failure remain distinct terminal paths; they are not fictitious filled-tranche CLOSED events.

Portfolio explicitly maintains four mutually exclusive allocation components: `held_committed_capital`, `reserved_committed_capital`, `filled_committed_capital`, and `closing_retained_committed_capital`. Their sum is `logical_committed_capital`. Free coin/global capital subtracts **all four**. Slots count every unresolved hold or nonterminal logical tranche, including CLOSE_PENDING, RECONCILING and escalation states with commitments.

At close acquisition, Lifecycle freezes the tranche's current accepted committed quantity basis: cumulative entry quantity plus still-committed live entry remainder. Previously terminally cancelled, already released entry remainder is excluded. Portfolio derives the locked own-capital amount from that quantity basis and the immutable approved capital-per-unit. In one update it transfers the tranche's existing accepted reserved/filled allocation to `closing_retained_committed_capital`; the other accepted components become zero. This is an allocation transfer, **not a fabricated fill** or money release. Entry fills racing cancellation transfer no additional capital out of this retained total; cancellation of a remainder during closing does not release it early. If Portfolio receives closing state before acceptance state, it first reconciles the same spec's accepted commitment against its hold and then performs the transfer atomically, never counting both.

While closing, the frozen retained amount stays constant even when `exposure_qty = 0`. Only canonical CLOSED releases it and the one slot, once. Ordinary pre-close entry remainder cancellation still releases only its unfilled reservation under the existing entry policy; this must not be confused with the no-release close path. Pre-close HOLD→RESERVED rounding reconciliation is unchanged. No partial exit causes a proportional release.

Example: accepted commitment 100; exposure 5. Close starts: filled 0, reserved 0, closing-retained 100, logical commitment 100, exposure 5, slot 1. Exposure later becomes 0 with an unresolved SL: closing-retained remains 100, slot 1. Financial history PARTIAL: still 100 and 1. Only all six predicates true: commitment 0 and slot 0. Real executed quantities remain factual throughout.

## P7 — Complete Lifecycle financial evidence

Lifecycle retrieves financial evidence directly through **its existing Order Management boundary**, `GET_FINANCIAL_FACTS`; Portfolio does not forward it. Shared normalized row/coverage definitions are used independently by both API boundaries. Lifecycle, not Portfolio or API, attributes logical-tranche results. Actual entry/exit executions, fees/rebates, funding and other supported attributable costs are mandatory. An empty funding/cost set is valid only with COMPLETE coverage proving no applicable records, or explicit evidenced non-applicability for the pinned profile; absence of rows is not proof of zero.

The normalized financial payload includes source transaction/cashflow/execution identities, exact currency/amount/quantum, effective and recorded time, native scope, available client/native/parent/child linkage, component classifications, endpoint/record/field provenance, normalization profile, aliases, funding settlement basis, and requested/covered intervals. COMPLETE requires every mandatory component interval covered, no missing ranges, pagination exhausted, a source watermark covering the cutoff and source finality confirmed. PARTIAL means some records or ranges are missing; UNAVAILABLE means the required evidence cannot be established. Neither can finalize. Intervals are half-open `[from,to)` and the cutoff must actually include the final execution and all causally applicable records; equal timestamp ambiguity without native sequencing remains unresolved. COMPLETE describes evidence, not elapsed waiting time. No age threshold substitutes for finality.

### P7.1 — Currency admissibility before logical financial FINAL

`schemas/NUMERIC_POLICY.md` §2A governs the single accounting/settlement unit. Every required monetary source/component contributing to FINAL must already be expressed in the tranche's pinned governed currency, including execution-derived gross result, fees/rebates, funding, supported other costs and attributable credits/debits. `financial_record.currency` always carries the actual native source currency; `financial_result.currency` is the pinned target accounting unit. Currency is validated at source/allocation level before any component sums or net aggregation, so cancellation to zero cannot hide unsupported sources. Funding settlement/mark price supplies the existing allocation weights only; it is not an FX conversion rate.

This baseline supports no cross-currency valuation. A required amount in any different currency is durably retained with native amount/currency/quantum, identity, aliases, provenance, attribution and coverage. Never omit it, zero it, relabel it, treat it as NOT_APPLICABLE merely because its currency is unsupported, add it to a different-currency scalar, or infer a conversion from market/execution price or another heuristic. Its affected component and logical result remain RECONCILING/finality-blocked. COMPLETE evidence can describe a cross-currency source accurately but cannot make that source admissible for FINAL. A profile expecting same-currency settlement must fail closed on contrary facts.

Immediately before publishing FINAL, Lifecycle requires all of the following together:

1. All mandatory financial evidence and current component/overall coverage are complete under the existing proof rules.
2. Every mandatory source has resolved, deterministic attribution and all required source allocations are complete/committed under their existing algorithms.
3. Every monetary component participating in the result, and each required source amount underlying it, is already in the tranche's governed accounting/settlement currency.
4. No unresolved required cross-currency source remains; no supported valuation rule exists in this baseline to bypass that requirement.
5. All other existing finality, source-integrity, execution-chronology, accounting-day and P6 terminal conditions hold.

These are financial-finality requirements inside the existing P6 six-condition CLOSED conjunction, not a seventh terminal state/condition, new release path or new posting stream. Until they hold, `financial_result` remains absent/null and the closing tranche retains its existing RECONCILING/CLOSE_PENDING commitment and slot. Native source allocation/conservation, source signs, accounting-day attribution and once-only result receipt remain unchanged.

Currency admissibility never precedes or suppresses the governed identity/ownership resolution, accepted-content comparison and durable contradiction retention. A foreign-currency or malformed recognizable source/proof must not disappear through currency filtering. Persist the affected source IDs, currency discrepancy and pinned accounting binding with their evidence so restart cannot clear the finality block or choose a new currency. A relevant accepted-source change invalidates dependent current component/parent finality proofs through the existing revision-bound rules. If contrary currency evidence is received after FINAL, use the existing post-final integrity taxonomy and receipt/eligibility fence; never rewrite the frozen result, create a replacement result or duplicate/reverse its applied receipt.

The current result formula and allocation rules below apply only after this single-unit check. Native-profile/runtime confirmation that a product settles all supported components in that unit is a later conformance obligation, not certification by this document.

Canonical `cashflows[].signed_amount` is **wallet effect**: credit positive, debit negative. Sign normalization is component- and source-field-specific; it is not currency conversion:

| Component / source convention | Normalized wallet effect |
|---|---|
| Trading fee, COST_POSITIVE source | negate source amount: charge 0.10 → -0.10; rebate -0.02 → +0.02 |
| Funding, CREDIT_POSITIVE source | preserve: receipt +0.30; payment -0.30 |
| Other supported cost, COST_POSITIVE source | negate: charge 0.05 → -0.05; refund -0.01 → +0.01 |
| CREDIT_POSITIVE wallet cashflow | preserve signed wallet change |
| MAGNITUDE_WITH_DIRECTION source | apply explicit authoritative CREDIT/DEBIT direction; never infer direction from the field name |

The adapter profile fixes which convention applies to each endpoint/field and records that choice. These are normalized contract rules; native mappings still require conformance tests. Missing/unknown mappings are UNAVAILABLE. No single generic sign operation is applied to fees, funding and cashflow together.

A normalized cashflow has one stable adapter-owned identity, bound to authoritative native transaction/record identity or execution-plus-component identity with proven linkage. Duplicate endpoint representations become aliases of that identity, not additional amounts. Same symbol, amount or timestamp is insufficient evidence to merge or allocate records. Conflicting alias values remain RECONCILING. Native aggregate realized P&L is cross-check-only for a shared native side. Gross logical trading result is reconstructed from attributed entry/exit executions; a cashflow containing the same gross/net result is not added again.

The final result retains the existing **cost-effect** convention for fee/cost component totals:

```text
actual_fees_rebates = -sum(attributed TRADING_FEE signed_amount)
other_supported_exchange_costs = -sum(attributed OTHER_EXCHANGE_COST signed_amount)
allocated_funding = sum(signed per-tranche funding allocations)
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

Thus a fee rebate makes `actual_fees_rebates` negative and increases net result. Planned fees never replace actual ones. Funding remains the unchanged decimal-18, toward-zero, largest-absolute-raw-allocation/lexical-ID residue algorithm in Lifecycle §32. Source amount must be exactly representable; no source rounding, double allocation or funding-triggered exit is introduced.

Lifecycle durably persists the source inbox, proven aliases, component coverage, allocation ledger and result identity. After restart it resumes uncovered ranges/cursors and reuses source identities. The transition publishing FINAL requires complete mandatory evidence, deterministic attribution and the P7.1 single-unit currency/finality check against the current accepted source basis. There is no provisional logical-result/correction stream. Persist one result per tranche; `result_id` is allocated once in that finalization transaction and retained across replay, not regenerated when source rows arrive in another order. Conflicting later financial truth is an integrity incident requiring reconciliation, not a second result with a new ID.

## P8 — Economic time, operational time and accounting day

`accounting_effective_at` is the timestamp of the **final economic closing execution**, established after reconciliation as the execution that permanently reduced the logical tranche to zero. A temporary zero while an entry remainder can refill is not eligible. Lifecycle must prove terminal entry/reduction authority and complete execution ordering, then persist `final_closing_execution_id` and its original timestamp. It cannot substitute delivery, cleanup, callback or finalization time.

`accounting_day_id` is the immutable date in the Portfolio policy's named timezone `Asia/Jerusalem`, using the half-open local-midnight day containing that instant. Portfolio supplies the policy in Capital and Limits; Position copies it unchanged into Order Spec; Lifecycle derives/persists the day, and Portfolio validates it on receipt. No additional business edge is required. The policy is `ACCOUNTING_DAY_V1`; historical boundary instants are persisted to avoid a restart reinterpreting them.

The four timestamps have different owners/meanings:

- `accounting_effective_at`: Lifecycle-proven final closing execution time.
- `closed_at`: Lifecycle's operational cleanup-complete marker (entry terminal, exposure zero, no competing child authority); this marker **does not by itself mean lifecycle_state=CLOSED**.
- `finalized_at`: Lifecycle's mandatory financial-evidence finalization time.
- `delivered_at`: Portfolio's first successful durable receipt/application time, stored in its result-receipt ledger; retries may have later transport-attempt times but do not change this receipt or accounting day.

`terminalized_at` additionally records the atomic canonical CLOSED transition, which occurs only after all six predicates. Lifecycle atomically persists the final result, resolves the close intent, sets CLOSED and creates its Order Event outbox after operational and financial prerequisites. The result carries the first three timestamps, terminalized_at, the day/policy and stable result_id. Delivery time is not a producer-controlled financial field.

```text
2026-09-11 23:59:59+03:00: final economic closing execution
2026-09-12 00:00:02+03:00: operational cleanup complete (closed_at)
2026-09-12 00:00:06+03:00: financial finalization; canonical CLOSED transaction
2026-09-12 00:00:08+03:00: Portfolio first receipt (delivered_at)
accounting_day_id = 2026-09-11
```

Portfolio's final-only result ledger is unique by result_id **and tranche_id**. In one transaction it checks immutable content/day, inserts the receipt, posts once to that accounting-day record, applies the terminal release once and persists its downstream state updates. Replayed identical payload is a no-op; conflicting payload under either identity is an integrity error.

For the current day, daily_realized_pnl sums FINAL results bound to that day and can latch the existing Daily Loss gate. For a late historical result, update only its immutable historical day. Do not add it to current-day Daily Loss, do not recompute the current latch as if the result occurred today, do not rebase current daily_portfolio_base, and do not add it again to API-authoritative wallet capital. Closed historical day records remain open to **first exactly-once final posting**, not to trading-policy retroactive execution. A historical total may be filled/corrected by that first final result; already posted final values cannot be silently changed.

Rollover fixes the new base from the authoritative boundary wallet value or complete reconstruction, independent of result delivery. Wallet cash already reflected in that base is not added again by logical P&L posting. Missing boundary evidence blocks new exposure; a later arbitrary snapshot never substitutes for the boundary value. Restart restores accounting-day records, boundary instants, current latch/base, receipt deduplication and historical late-posting state before applying results.

## P9 — Native observation and complete attribution resolution

An unknown native observation never fabricates cycle, grant, plan or tranche lineage. Lifecycle persists one `native_observation_id` for its authoritative source identity and an independent `native_scope_revision` in scope `(account, environment, symbol, native_side, position_idx)`. This revision domain is **not lifecycle_revision and has no decision_cycle_id dependency**. Observations retain their original revision on replay. New distinct observations receive new scope revisions; stale/contradictory snapshots are reconciled by source evidence rather than arrival order.

Portfolio persists an unresolved tombstone keyed by observation ID and blocks affected new exposure. It does not debit an arbitrary tranche to explain a native aggregate change. Logical allocations are created only after evidence establishes exact lineage and quantities.

Lifecycle uses one durable `attribution_resolution_id` per observation and monotonic `resolution_revision` for progress. The resolution record contains the original observation/scope revision, affected native scope, expected allocation IDs, affected tranche IDs, quantities, source executions, evidence, observed total, completeness and resolved_at. A complete revision has a frozen expected set, no duplicate IDs and exact quantity conservation. All expected allocations reference strict known-tranche lineage. Partial revisions may persist evidence progress but cannot declare success or unblock exposure.

The producer transaction persists the complete resolution record, every expected strict logical allocation event and all corresponding outboxes together. Arrival may still be split. Portfolio records each logical allocation once by allocation_id and verifies its membership, quantity, tranche, source executions and resolution identity. A resolution manifest is evidence of the expected set, **not a second quantity application**. A logical allocation received before the complete manifest is staged with **zero quantity effect**. Historical factual rows may be retained, but they do not authorize this allocation's exposure subtraction. Only complete membership plus the disjoint authoritative source-quantity partition described in T04 below permits quantity application. The manifest itself is never another quantity effect.

Clear this observation's block only when both are true:

```text
complete resolution established and validated
all expected logical allocations durably applied exactly once
```

A resolution or strict allocation can arrive before the original observation message. Persist a provisional unresolved tombstone using the supplied observation identity and proven native scope; unknown observation totals remain unknown, not guessed. Stage any incomplete evidence. A validated complete manifest supplies the original native scope/revision and total, so complete resolution plus all expected allocations can establish a resolved tombstone without waiting for another delivery of the original observation. Its later matching observation is replay, not a new block; conflicting content is an integrity incident.

First allocation alone never clears it. Complete manifest alone never clears it while expected events are missing. Clearing one observation does not clear another unresolved observation in the same scope, nor bypass other Portfolio gates. Resolved tombstones retain complete revision, expected/applied allocation sets and content digest across restart. Identical old observation/resolution replay cannot reopen the resolved tombstone or reduce exposure again. Conflicting content is an integrity incident. A previously unseen old-revision observation is **not discarded solely because a higher native scope revision exists**; it must be reconciled/block as needed. Native scope high-watermark is not a substitute for per-observation state.

## Validation scope (informative, not another protocol)

Implementation conformance checks cover schema structure, concrete state-transition traces, exact arithmetic, immutable bindings, replay expectations and document synchronization. Documentation-level checks alone do not execute a TriggerTrade backend or prove distributed database/queue behavior. Native Bybit acceptance, quantity-scoped TP/SL isolation, cancel/fill races, funding/fee normalization and historical-finality coverage remain runtime conformance gates. Approval of this specification baseline is not implementation or runtime certification.

## P10 — Proven native protection and immutable entry acceptance

Lifecycle restores its immutable spec/native-entry registry, then reads actual orders through Order Management. It can recover a protective child's logical owner only from a unique proven native parent/client/group relationship. Two tranches on the same native side do not authorize matching by symbol, side, quantity, trigger price, creation time or request proximity. Recovering an unambiguously linked child does not by itself verify protection: independently compare protective role, current live/conditional status, trigger price/direction/type/source, actual protected quantity, PARTIAL_QUANTITY/FULL_POSITION scope, execution type, reduce-only/close semantics and account/environment/symbol/native side/index/mode against that child's immutable expected protection. Field meaning and linkage must have pinned native provenance under `api-contracts/NATIVE_FACT_PROFILE.md`.

An incomplete, conflicting, ambiguous or geometrically different child remains a native observation/reconciliation item; do not mark protection verified, guess ownership, silently cancel another tranche's order or create replacement protection based only on absence of a local mapping. Commit the recovered mapping only after the proof checks, with unique native-child→logical-role binding and source evidence. Query completeness is separately required; matching two rows in a partial page is not proof that no conflicting live child exists. Crash after native attachment but before local mapping persistence is handled by this factual query-and-proof path, not by repeating attachment blindly. Existing protection-failure/close safety semantics remain unchanged.

`entry_accepted_at` is the immutable factual original exchange acceptance/live timestamp for a particular entry order, with `entry_acceptance_status` and `entry_acceptance_provenance`. PROVEN requires nonnull timestamp and verified provenance; UNAVAILABLE carries nulls; NOT_APPLICABLE is for a non-entry fact or a proven no-acceptance terminal. Native creation, fill, current update, receipt and local processing times are not fallback acceptance values.

Lifecycle persists this fact by native entry/authorization identity before cumulative publication. A later authoritative recovery can enrich null→proven once. Same value is idempotent; a conflicting proved value is an integrity/reconciliation condition and cannot rewrite the first fact. Equivalent instants use the adapter's canonical timestamp representation. Every subsequent logical Order Event repeats the known fact; an unavailable older event cannot erase it. Portfolio merges acceptance evidence independently of lifecycle revision: an older accepted event may supply a missing immutable timestamp but cannot roll back quantities, terminal state or a cleared contribution. Conflicting evidence blocks reconciliation regardless of revision.

Cooldown contribution identity is `(authorization_id, tranche_id)`. In the atomic Portfolio hold/authorization transaction, Portfolio persists the attempt's pinned Portfolio Rules `configuration_id`, `configuration_version`, `configuration_content_digest` and exact `pinned_cooldown_duration`. Its only deadline origin is `entry_accepted_at + pinned_cooldown_duration`. The configuration binding and duration survive restart and are never replaced by a later current Portfolio configuration. Seeing accepted/OPEN exposure with an unresolved original timestamp creates an unresolved contribution, not a guessed deadline or expired cooldown. Any unresolved surviving contribution blocks new same-symbol eligibility; otherwise the symbol deadline is the maximum surviving contribution. Later partial/full fills, duplicate ACCEPTED, reorder and restart do not extend it. Proven zero-fill cancellation removes only that attempt's contribution and retains a tombstone so older events cannot recreate it. Cancellation of an older attempt cannot shorten a newer contribution.

If `entry_accepted_at` is recovered after restart or after Portfolio configuration has changed, Portfolio computes the contribution from the factual recovered timestamp plus the already-persisted `pinned_cooldown_duration`. It never reads current cooldown configuration for that attempt and never recomputes an already-established contribution after a settings edit. Existing unresolved-acceptance, replay, conflict and zero-fill-removal semantics are unchanged.

Order Placed remains the existing Lifecycle→Set lifecycle synchronization. `order_placed_at` is its durable placement-notification timestamp (set once after factual live existence and replayed unchanged), not the Portfolio cooldown origin. A placement notification is possible when current live existence is proven but the original acceptance timestamp remains unavailable; Portfolio's cooldown nevertheless stays unresolved. This technical timestamp definition changes no Frozen Condition or Set monitoring logic.

## P11 — Exact numeric values, then canonical serialization

`schemas/NUMERIC_POLICY.md` defines TT_NUMERIC_V1 for exact rational intermediates, capital floor/ceiling at 12 decimals, input-derived exact finite monetary products, source-quantum non-funding allocations, ratio reporting at 18 decimals and exact gates. Every producer/consumer of duplicated capital/economic values uses that version. Existing formula blocks define exact mathematical expressions; the documented output-class quantizer determines their persisted value. No unspecified “small rounding difference” is acceptable. Existing funding, price/quantity grids, formulas and thresholds are unchanged.

## P12 — Proven execution lineage, then non-funding cashflow allocation

Lifecycle owns both stages. First establish P9-complete native quantity lineage: one stable execution, exact factual quantity/price and a complete proven allocation to logical tranches. An execution-linked fee/rebate/cost does not establish that lineage. Without it, stage the factual cashflow and keep affected results non-FINAL; no equal/proportional guessing. If one source record covers multiple executions without a proven decomposition into execution-linked amounts, it does not qualify for this rule and remains unresolved.

After proof, for each shared supported non-funding source cashflow and execution:

```text
weight_i = abs(proven_allocated_execution_qty_i × factual_execution_price)
raw_i = exact_source_signed_cashflow × weight_i / sum(all proven weights)
base_i = trunc_toward_zero_to_source_amount_quantum(raw_i)
recipient = largest abs(raw_i), then lexical tranche_id ascending
final_recipient = base_recipient + exact_source_signed_cashflow - sum(base_i)
final_other_i = base_i
```

Tranche IDs are compared by Unicode code-point order with no locale/case folding; they are already immutable opaque IDs, never renamed for residue. Quantities and price must be positive, weights complete and sum of attributed quantities equal the authoritative execution quantity. Source amount must be an exact multiple of its positive factual quantum. Preserve source sign (zero allocations allowed), and require `sum(final_i) == exact source amount`. This is an accounting allocation only. Funding retains P7/Lifecycle §32's separate existing algorithm; realized gross P&L views are not double-added as a fee.

The durable allocation algorithm is `EXEC_CASHFLOW_ALLOC_V1`. Canonical source identity is the existing adapter-owned cashflow_id within native account/environment/symbol/side/index scope; endpoint aliases refer to that same source and cannot create a second effect. Reject conflicting source amount/currency/quantum/component/execution or alias identity. P12's internal immutable manifest contains the source, execution, complete quantity-resolution ID/revision, expected sorted tranche/allocation IDs and all exact amounts. A split requires a complete P9 resolution ID/revision. Single-tranche proven direct attribution remains valid without a split manifest; the new result collection may therefore be empty when no shared source exists.

For the exact identity encoding, let `I = ["EXEC_CASHFLOW_ALLOC_V1", native_scope, cashflow_id, execution_id, resolution_id, resolution_revision, 1]`. Hash canonical sorted-key, compact UTF-8 JSON of I. `manifest_id = "CFM-" + SHA256(I)` and `allocation_id_i = "CFA-" + SHA256(I + [tranche_id_i])`. Null resolution fields are legal only for already-proven direct attribution, not a split. Allocation revision 1 is immutable; changing attribution after posting is an integrity event, not a new additive revision. Source-level uniqueness across manifests is additionally mandatory: no revised ID may post the same source again.

Persist the complete manifest and rows before one atomic logical financial posting transaction. Rows may be staged over a crash boundary, but no first-tranche financial effect becomes visible before all expected rows exist and match. The atomic commit verifies coverage, quantities, weights, source conservation, identities and absence of an existing source commit, then posts all recipients and one source-commit tombstone. A crash after staging A but before B leaves **zero** posted allocations; recovery completes B and commits each once. Replay/alias returns the same manifest/effects. Database atomicity is a future runtime obligation, not tested by Python deepcopy.

`financial_result.non_funding_allocations` contains that tranche's committed shared-source rows, including manifest/source/execution/resolution identities, source quantum/amount, proven weight and recipient. Lifecycle refuses FINAL until every mandatory source has a complete deterministic committed allocation, all existing P7/P9 coverage conditions hold, and P7.1 currency admissibility is satisfied. Allocation conserves each native source in its own currency; an allocation commit does not convert it or authorize cross-currency final aggregation. In cost-effect totals, trading fees/rebates contribute `-allocated_signed_amount` to actual_fees_rebates; supported other costs contribute the same sign conversion to other_supported_exchange_costs. Portfolio consumes the FINAL logical result exactly once by existing result identity; it does not allocate source cashflows, re-add native wallet effects or infer trading lineage.

## P13 — Economic execution chronology and permanent zero

Lifecycle persists every attributed execution by stable execution_id within native scope, with factual quantity, direction/role, price, executed_at and available native sequence/domain/subsequence/profile/provenance. Duplicate immutable facts are idempotent; conflicting core facts for an existing identity force reconciliation, not last-writer-wins. Persist complete execution history or an authoritative opening checkpoint containing quantity, timestamp, coverage boundary and evidence, plus every subsequent execution. A local callback-derived checkpoint is not authoritative. Checkpoint overlap or an execution at an unresolved checkpoint boundary must be reconciled.

Reconstruct quantity evolution in ascending factual executed_at order, comparing timezone-aware instants. At equal timestamps use only a verified native ordering profile within the same native sequence domain; numeric sequence order must be supported by that profile. Same sequence requires a supported native subsequence. Opaque/lexical execution IDs, callback order, database insertion order and message revision are not economic tie-breakers. If needed order cannot be proven, financial finality and accounting day remain unresolved. Supported evidence may fill missing sequence fields without modifying immutable core facts; contradictory ordering evidence remains an incident.

Beginning from the authoritative quantity checkpoint, apply each proved ENTRY as plus attributed quantity and each EXIT as minus attributed quantity. Negative intermediate exposure with a supposedly complete prefix is inconsistent and blocks finality. A transition positive→zero is only a candidate final close. Any subsequent entry refill invalidates that candidate; a later positive→zero can become the permanent close. A permanent final closing execution is fixed only after the entry remainder is terminal, execution coverage is complete, final exposure is zero and existing operational/financial terminal predicates hold. No complete zero-closing execution means no fabricated final timestamp.

Set `final_closing_execution_id` and `accounting_effective_at` from that permanent closing execution, not from the last processed exit callback. P8 derives accounting_day_id with the unchanged Asia/Jerusalem policy. Final chronology is immutable; a contradictory later “new” execution against already-certified complete coverage is an integrity incident, never silent repost/rebase. Chronological/reverse delivery, duplicates and restart of the same complete execution set must yield the same final execution/time/day. Temporary zero then remainder refill is not a second trade or a strategic partial-close feature.

## P14 — Exact construction confirmation and multi-symbol factual cardinality

Before atomic spec/confirmation persistence, Position independently compares every duplicated field, not only a digest: decision_cycle_id, set_result_id, position_decision_id, construction_result_id, capital_grant_id, position_plan_id, tranche_id, order_spec_id, symbol, direction and numeric policy. `order_spec_contract_version` targets the exact spec contract version. The approved_economics mapping is approved_entry→entry.price, approved_quantity→entry.quantity, approved_leverage→leverage, approved_actual_order_notional→economics.actual_order_notional and approved_actual_committed_capital→economics.actual_committed_capital. Each is canonical and exactly equal. minimum_net_edge enabled/status/calculated_value must equal spec minimum_net_edge_enabled/result/planned_net_edge_pct; the exact formula decides the configured threshold before report quantization. The full spec digest is an additional check, not a substitute.

Portfolio verifies and binds its received confirmation, grant, values and immutable target digest/version when booking the final hold. Lifecycle verifies the received immutable spec and authorization target IDs/digest/version/policy before submission. Cross-document implementation conformance checks may observe all envelopes, but do not introduce a runtime Portfolio→Lifecycle economics feed or Position↔API edge. The producer's prepublication assertion is mandatory. All currently duplicated fields are enumerated above; a future duplicated field requires explicit equality validation, not an unchecked scalar outside the digest. Instrument is currently represented by symbol; no separate instrument object is duplicated in confirmation.

Spec-first or authorization-first **at Lifecycle** only changes which durable inbox record waits. Authorization still cannot originate before Portfolio's valid confirmation and atomic hold. Confirmed specs are never mutated to repair a mismatch. Duplicate messages cause no second hold or dispatch; stale ID/version/digest/conflicting scalar stays non-submittable with an integrity record. A definitive no-create terminal authorization/spec remains consumed across restart, new compatible metadata and duplicate messages; its released hold/slot cannot be recreated. A future trade needs the existing normal product flow, not resurrection of that authorization.

Portfolio Data Request retains batched symbol scope. If instrument_metadata or fee_rates is requested, filters.symbols must be a nonempty unique explicit list. Each requested symbol-scoped response section contains exactly one item per requested symbol, no duplicates/missing/extra symbols. Each row has symbol, AVAILABLE/UNAVAILABLE status, facts or null, independent as_of and endpoint/record provenance, and a reason for unavailability. The aggregate section status is AVAILABLE if all rows are available, UNAVAILABLE if all unavailable, otherwise PARTIAL. Unrequested symbol-scoped sections are absent. Account-only requests can retain empty-symbol managed-account scope; there is no implicit wildcard instrument/fee batch. The API/caller may fan out technical native queries inside the same boundary, preserving one normalized batch response and per-symbol provenance. A missing symbol is not an empty successful result. Existing partial/incoherent-fact safety prevents new exposure until mandatory evidence is available; no price/POST_ONLY marketability test is added.


## R01–R09 normative synchronization

These technical refinements apply to P1–P14 and all existing producer/consumer contracts; the topology, trading formulas and thresholds are unchanged.

### Exact actual hold — P1 / P11 / P14

A grant is a bound, not a reservation. The Portfolio final atomic gate books exactly `Order_Spec.economics.actual_committed_capital = construction_result.approved_economics.approved_actual_committed_capital = Submit_Authorized.held_committed_capital`, with the same canonical TT_NUMERIC_V1 value independently checked rather than trusting digest alone. Require actual <= grant; otherwise no hold/slot/authorization. Grant surplus stays free before acceptance. One slot is consumed once, and accepted state reclassifies rather than enlarges this allocation. Existing entry-remainder apportionment and full closing-retained commitment remain unchanged.

### Monotonic native facts and acceptance integrity — P10

Lifecycle durably merges individual native fields. Authoritatively proven immutable identity/link/role/geometry cannot change silently; contradictory proven values create a durable integrity incident. Unknown/null fields may be enriched by authoritative evidence. Stale incomplete records cannot erase proven fields or provenance. Mutable status/cumulative fills/remaining quantity/update time use the pinned native profile's factual ordering, not row equality or callback arrival. A profile without authoritative mutable order semantics cannot overwrite an established fact. Equal-source-version conflicting mutable facts, decreasing cumulative fill or resurrected terminal status reconcile. The documented synthetic conformance profile uses authoritative updated_at; this is not a Bybit certification.

The first proven original `entry_accepted_at` remains immutable and auditable. A known timestamp plus contradictory acceptance evidence is not eligibility proof. Logical Order Event v7 carries `entry_acceptance_integrity` independently from the timestamp and Lifecycle revision: state CLEAR/CONFLICT/RESOLVED, integrity revision, stable conflict ID, original/conflicting source evidence and explicit resolution reference. CONFLICT requires acceptance_status CONFLICT. Portfolio durably retains this per-attempt unresolved condition, blocking the affected existing cooldown scope even after the apparent timestamp-plus-cooldown interval expires. PROVEN, UNAVAILABLE, stale events, duplicate fills and zero-fill removal never clear an integrity incident.

Only a newer authoritative resolution for the same incident, retaining evidence and proving the original acceptance value while disproving the conflicting evidence, may set RESOLVED/PROVEN. Preserve its tombstone and covered-evidence identities. Delayed covered records with identical accepted canonical content cannot reopen it. A changed binding at ANY previously accepted integrity revision, including CLEAR or CONFLICT, is a durable new challenge and reblocks eligibility without rewriting the acceptance origin or accepted resolution tombstones (X01). An apparent correction requiring a different first acceptance time is not a normal cooldown rewrite and stays in the existing integrity/reconciliation path. No local clock, first fill or updated_at substitutes for acceptance.

### Revision-bound closure proof — P6 / P8 / P13

Every permanent-zero/final-closing-execution/accounting-day/cleanup/closure-eligibility proof binds to an exact durable vector: execution-ledger revision, entry-remainder/authority revision, protective/exit-child revision, coverage/completeness revision, close-intent revision and financial-evidence revision. Each predicate includes its authoritative source certificate, not merely a cached bool. Any relevant source change invalidates all dependent proof fields before release eligibility can be used. New execution evidence invalidates an earlier execution coverage certificate even if it once said COMPLETE; re-establish complete coverage and reconstruct economic order.

Before publishing FINAL/CLOSED or releasing capital/slot, one atomic transaction verifies the current vector and all canonical CLOSED predicates against current durable evidence: zero logical exposure, terminal entry remainder, terminal/authoritatively disabled children, resolved intent, complete mandatory financial evidence/allocations, and no competing authority. Never finalize from cached chronology_status or cleanup alone. A temporary zero followed by refill invalidates the earlier day; the later permanent exit determines accounting_effective_at/day only after a fresh proof. Replay of an unchanged proof never changes closed_at.

After a valid terminal result has committed, identical evidence/cleanup/result replay has no effect. Contradictory new evidence is durably quarantined with an integrity/reconciliation incident and affected exposure eligibility blocked. It must not silently rewrite terminal timestamps, accounting day, financial result or once-only Portfolio receipts. An explicit integrity correction process is separate from normal final-result replay; no automatic fabricated P&L adjustment is introduced.

### Monotonic financial quantity proof — P9 / P12

The financial consumer durably binds accepted attribution_resolution_id, native source/execution scope, revision, completeness, complete proven allocation content/digest and commit state. Older revisions are stale no-ops; identical same-revision content is idempotent; different same-revision content is an integrity incident. Partial progress may only extend already-proven quantity bindings, never alter them. A complete allocation set is immutable. A later identical complete retransmission does not rebind already-posted allocations to another revision. New conflicting or regressing content reconciles. A stale partial message after complete proof or after commit has no effect and is not a false immutable conflict.

Stage the full P12 cashflow allocation manifest against that accepted complete proof and atomically commit all exact source effects only when manifest completeness and proof binding still hold. Crash during staging cannot publish a first-tranche partial financial result. FINAL still requires complete mandatory source coverage/allocation. Funding keeps its separate algorithm; money allocation never infers quantity lineage.

## P15 — Native-scope no-reduction observation and clearance

Order Event v7 adds `NATIVE_SCOPE_RECONCILIATION_OBSERVED` and `NATIVE_SCOPE_RECONCILIATION_RESOLUTION` on Lifecycle → Portfolio only. These are not reduction events. An unbound live protective child with no execution uses a native-only observation containing stable native_observation_id, per-observation native_scope_revision, account/environment/symbol/side/index scope, observed native order ID/role where known, factual linkage, source provenance, unresolved classification and explicit affected blocking scope. It has quantity_effect NONE and no fabricated cycle/tranche/position IDs.

Lifecycle owns its durable observation identity/journal; the reference identity is a versioned digest of factual native scope and native order ID, never symbol/time lineage inference. Proven links and appropriate scope/field evidence are necessary for adoption; geometry alone is never sufficient. Portfolio persists the native observation and blocks only its affected scope under existing P9 safety rules, without changing capital, slots, execution quantities or P&L merely because a child was observed.

Clearance uses the same observation/native scope, a stable reconciliation_resolution_id and monotonic resolution revision. A partial resolution retains blocking. Complete OWNERSHIP_PROVEN requires the entire declared binding set delivered, exactly one proven logical owner for this single native child, factual linkage evidence, and no unresolved execution authority. Complete AUTHORITATIVELY_TERMINAL requires proven terminal/disabled native child and no unresolved authority, with no invented logical bindings. A native child spanning unresolved multiple owners cannot use a single-owner clearance; remain reconciling until factual execution attribution/authority is fully resolved under P9. There is no quantity allocation or accounting effect in this clearance variant.

Resolution-first delivery creates a provisional native tombstone; complete evidence can settle it before the old observation arrives. Persist observation identity/scope, accepted revisions, content, unresolved/resolved state and integrity flags. Ignore older replay; equal revision/different content is an integrity conflict. Resolved tombstones cannot be regressed by stale observation/progress, and other outstanding observations continue to block. Contradictory new post-clearance facts create integrity blocking rather than silent reassignment. Existing NATIVE_UNATTRIBUTED_REDUCTION and its complete multi-tranche allocation manifest remain unchanged and separate.

## P16 — Set numeric state and historical market selectors

Set-derived computation and Market Handoff v4 use `schemas/SET_NUMERIC_POLICY.md` (TT_SET_NUMERIC_V1). Source ordering, recursive initialization/checkpoints, work precision, exact sqrt rounding, handoff quantization and Position exact comparisons are normative technical rules. No new indicator, threshold, fallback or heuristic is introduced.

Set persists fixed per-dataset selection_id/as_of/interval/count/timeframe/cursor requests on the existing Market Data Request v3 boundary. API only supplies the requested factual range, its snapshot/page identity and explicit coverage, missing ranges, source finality and pagination manifest. It never selects analytical windows. A response cannot silently replace a historical range with current data. Set reassembles the exact same immutable selection after restart, deduplicates complete pages and requires complete selected coverage before affected data become AVAILABLE. Full wire and boundary semantics are in api-contracts/MARKET_DATA_REQUEST.md.

## P17 — Immutable configuration binding for started cycles and attempts

Any user/configuration-controlled rule set selected for an already-started logical cycle or attempt is immutable for that cycle or attempt. Later activation or editing of Set configuration, Trigger/Core Set configuration, Position Rules, Portfolio Rules, cooldown, thresholds, sizing parameters, execution-governed settings, or any other participating rule applies only to a newly created cycle/attempt after that configuration becomes effective. No active cycle may resolve an input by consulting whichever configuration happens to be current at replay, restart, late evidence arrival or later construction.

At the canonical selection boundary the owning block persists an immutable binding containing at least `configuration_id`, `configuration_version`, a canonical `configuration_content_digest`, and the owner-local cycle/attempt identity. The digest is over the complete governed configuration content after canonical serialization; changing content without changing its identity/version is an integrity error. Hydration restores the persisted binding itself; it never reconstructs historical content from the latest configuration table. Later edits do not retroactively alter approved decisions, formation/decision-cycle semantics, attempts, orders, pending monitors, cooldown contributions or financial/accounting state.

Set binds each unfinished formation to the Set/Trigger/Core Set configuration selected when its current OPEN formation epoch is created, and a MATCHED cycle retains that exact binding. Position selects and pins its Position Rules configuration when it first evaluates the Market Handoff for the initial APPROVE/REJECT decision; the same binding governs post-grant construction. Portfolio selects and pins the Portfolio Rules configuration used for an authorized entry attempt in the atomic hold/authorization transaction before authorization is emitted; the pinned cooldown duration from that binding remains the attempt's cooldown duration even if acceptance is proved later. These owner-local bindings require no new business edge. Existing wire provenance fields expose the already-defined version where present; owner-local content digests remain durable implementation state unless a contract explicitly carries them.



## S01–S07 execution-reference synchronization

These are focused corrections of existing P6/P9/P10/P13/P15/P16 semantics. They apply to every active implementation path, including Order Lifecycle-owned close and native-observation processing, as well as accounting-day, financial-allocation and native-scope processing. The four business owners, twelve registered boundaries and trading formulas are unchanged. Historical S01–S07 did not alter wire shapes; the current T01 extension below changes only ORDER_EVENT.

### S01 — Current finality evidence and terminal quarantine

Every close implementation uses the P6 conjunction. A cached COMPLETE flag, cached zero, resolved chronology flag or cleanup callback is not itself a source certificate. The execution ledger, entry authority, protection children, exit children, other competing execution authority, close intent, financial evidence and coverage each have durable revision/evidence identity. A closure proof binds that current vector and the actual accepted certificates. A new relevant execution invalidates prior execution completeness immediately; dependent financial completeness cannot remain usable for the changed ledger. Older source certificates cannot replace a newer accepted revision, and known same-revision different content is an integrity incident.

Before committing FINAL/CLOSED and its outbox, one transaction recomputes current exposure and chronology, validates the terminal entry remainder and each terminal/authoritatively disabled child, excludes all competing authority, verifies complete factual financial evidence and exact allocations, and resolves the single active close intent. It then commits the result/proof/terminal timestamps. Temporary zero followed by a pre-final refill invalidates the earlier permanent-zero/accounting-day candidate. Incomplete reordered quantity evidence is RECONCILING and cannot be used as proven zero or a reduction budget.

After valid final commit, identical execution/cleanup/result replay is idempotent. New contradictory execution or authority evidence is durably retained in a separate integrity quarantine and blocks affected eligibility without normally mutating the committed tranche ledger, result, economic day, timestamps, capital or slot. No automatic adjustment, reopening or second release is implied. An unapplied final receipt is withheld whenever a relevant incident was durably committed before its receipt linearization, including when that incident has not yet been delivered; the T01 committed-prefix fence below enforces this; an already posted receipt is not undone or duplicated. Acquire/authorize/dispatch cannot create new execution authority from CLOSED, an already resolved intent, a committed terminal result or unresolved integrity quarantine.

Implementation/runtime conformance checks verify these actions as atomic durable transactions. A crash before any durable commit rolls back the entire action; after-commit redelivery consumes its existing identity. Coverage/certificate input generation constructs evidence only; it does not generate expected results. JSON serialization and state hydration verify restart semantics, not production storage atomicity.

### S02 — Proven mutable enrichment is field-specific

UNKNOWN, UNAVAILABLE, null and values without authoritative matching field provenance are unproven, even when non-null and even when the enclosing native order has an authoritative timestamp. First authoritative mutable status/fill/remaining/average-price enrichment replaces an unproven value at the same source timestamp without creating an integrity conflict. A later enclosing update for another field does not advance this field's factual version.

Retain each proven mutable field's source version/history independently. Identical proven replay is idempotent; older state cannot erase newer proven state. Different proven content at an already known source version is a durable conflict. Cumulative fill regression, contradictory same-version statuses, terminal resurrection and changes without authoritative ordering remain blocking. These ledger metadata do not add wire fields or a native-profile assumption.

### S03 — Native-scope tombstone content consistency

P15 observation identity, scope and accepted content/digest history survive clearance. Resolve identity first, then compare any already accepted observation revision's canonical content BEFORE applying a covered-revision stale shortcut. Identical content is replay; different content at a known revision is an integrity incident even after complete resolution. Re-establish the affected safety block, retain prior tombstone/history, and make no fabricated ownership, quantity or cashflow effect.

Resolution-first recovery retains its independent resolution content and covered native revision. Where the old observation's content has not actually been received, do not invent its digest from the resolution. Capture the first actual covered observation content for its identity/revision without regressing clearance; any later different content at that captured revision blocks. Other unresolved observations and integrity incidents continue to block. No new in-place incident-clearance message is introduced.

### S04 — Historical assembly is evidence-bound eligibility

Set's assembled history binds the immutable selection, supporting request identity or identities for pagination, source snapshot, complete page manifest, accepted page IDs and content digests, completeness/source-finality certificate, and native record identities/content. Page IDs are immutable content identities in the existing protocol; no unsupported page revision is invented.

Any relevant new page evidence invalidates the current derived eligibility until reassembly from one consistent accepted proof. Two incompatible complete manifests for the same selection/snapshot, a page outside the accepted complete manifest, different immutable content for one page/native record, or mixed fixed snapshots cause durable integrity reconciliation. A stale cache entry cannot imply AVAILABLE. Preserve prior assembled evidence for audit, but exclude it from new analysis and restart reconstruction while contradicted.

An already frozen Market Handoff retains its original evidence/values; replay of its immutable ID does not rewrite it. This does not authorize new analysis from contradicted source data. The current fixed-snapshot protocol does not permit silently replacing an immutable page/snapshot under the same identities; this specification introduces no replacement authority or automatic recovery heuristic.

### S05 — Global native quantity allocation identity

P9's allocation identity is global within its existing account/environment namespace, not local to a received observation. Its immutable binding includes allocation ID, native observation, attribution resolution, native scope/revision, native source execution/evidence identity, source content/revision, target tranche and exact quantity. Lifecycle persists that proof before use. Compact reference delivery actions may reference an already persisted full authoritative proof by its ID; they may not infer absent lineage from price, symbol or time.

Same allocation ID plus the identical full binding is idempotent globally. Different observation/resolution/source/tranche/quantity under that ID creates durable integrity blocking without a second quantity effect. A new allocation ID cannot move an already bound source execution to another observation. Legitimate proven multi-tranche splits of one source remain within their single declared observation and complete resolution.

Commit quantity subtraction and global application receipt atomically; a staged proof without a receipt has no quantity effect. Complete manifests carry their explicit native scope/revision, observed total and attribution-resolution identity, including when they arrive before the observation. A complete manifest establishes attribution completion only after its entire exact allocation set has globally committed receipts. Scope eligibility clears only when there is also no unresolved integrity; an alias incident cannot undo independently proven quantity receipts or attribution completion. Integrity blocks new exposure/clearance, not ingestion of independently proven valid reconciliation quantities. Preserve original bindings and receipts through restart and conflicting rebinding.

### S06 — Factual execution-derived gross result

For a fully closed linear logical tranche, let E be the exact sum of each attributable entry execution quantity times its actual price, and X the equivalent exit sum. The existing direction/sign convention gives LONG gross = X − E and SHORT gross = E − X. Every factual execution identity contributes exactly once. Original planned Entry and an unchanged initial average are not cost evidence for later fills.

A cost-basis checkpoint must identify its covered accepted executions and source revision, prove its boundary quantity and actual signed costs, and be exactly reconstructible from those executions. Its covered identities are excluded from later incremental application; conflicting checkpoint replays quarantine. The reference opening checkpoint includes explicit factual rows and their canonical digest, not a fabricated fill derived from planned Entry. Missing actual price blocks finality. Source coverage binds the combined checkpoint and incremental ledger.

The full-tranche result is not final while quantity is open or factual coverage/authority is incomplete. Partial native executions of the same existing close intent do not introduce a strategic partial close or a new partial-realization method. Final net remains gross factual result minus factual fee/rebate cost plus allocated funding minus supported other realized cost, using the existing normalized signs. Funding allocation itself is unchanged.

### S07 — Active versions

The active Order Event contract is version 7; the active Submit Authorized contract is version 5. Producer and consumer methodologies, contract subsections, registry, schemas and examples must identify these governed versions. Superseded introduction metadata must be explicitly historical rather than an active instruction. Historical S01–S07 alone introduced no wire-version increment. T01 now extends ORDER_EVENT to version 7; every other governed contract version is unchanged.


## T01–T05 normative synchronization

This section corrects only the five targeted defects. It is active producer,
consumer, evidence and persistence guidance, not an implementation approval.
It refines P6/P7/P8/P9/P12/P13/P14/P15 and the S clauses where explicitly stated.
No strategy formulas, limits, thresholds, funding allocation or accounting-day
policy change. The canonical nine business and three API boundaries are intact.

### T01 — Separate terminal result and post-final integrity incident

Order Lifecycle owns the immutable final result and any later contradictory
source evidence. It emits `ORDER_EVENT` version 7, variant
`POST_FINAL_INTEGRITY`, on the existing Lifecycle → Portfolio boundary.
The strict payload is governed by `ORDER_EVENT.integrity`; arbitrary free-form
logical event types or acceptance-specific integrity fields are not substitutes.

The incident has a stable `incident_id`, independently monotonic
`incident_revision`, `OPEN`/`RESOLVED` state, class/reason, known tranche and
nullable genuinely unavailable cycle/authorization lineage, native blocking
scope, protected `terminal_result_id` and canonical result digest, first
`observed_at`, and a durable evidence identity/content digest, nullable native
revision, source, provenance and retained evidence reference. UNKNOWN provenance
is not invented. `observed_at` is captured in the first incident transaction;
identical evidence replay reuses that persisted record, even after restart with
a different receipt clock. New contradictory evidence receives its own identity.

Lifecycle is not the Portfolio receipt owner. Its receipt observation may be
UNKNOWN; PENDING/APPLIED is advisory only with an explicit evidence reference and
as-of, and APPLIED names the actual receipt. Portfolio's own durable receipt
ledger determines whether an economic effect has already committed.

Lifecycle atomically persists the quarantine evidence, incident record and the
actual Order Event outbox/committed transport append. This transaction never
changes the committed result, accepted terminal ledger, day, intent or released
capital. Portfolio consumes the incident into its separate durable inbox and
scope-blocking index. Result deduplication by result_id/tranche_id and incident
deduplication by incident_id/revision are independent; a result replay must not
suppress a later incident. No Portfolio read of Lifecycle-local quarantine flags
is part of this protocol.

**Receipt and current-gate ordering on the existing boundary.** For each affected
account/environment/native eligibility scope, the durable Order Event transport
has a committed-prefix frontier (a technical sequence, not a native or lifecycle
revision). Lifecycle incident append and Portfolio's receipt/final eligibility
check must have one serializable order against that same frontier. Before
applying a first result receipt/release or permitting new exposure in that scope,
Portfolio must have merged every committed message through the frontier observed
**inside the same serializable transaction/fence** as its decision. A fetched or
cached frontier from an earlier transaction is insufficient. A gap, unavailable
fence or undelivered committed incident causes withholding, not optimistic
release. Complete delivery through a prefix does not override any open incident.

This is a technical outbox/inbox/receipt requirement on the existing edge, not a
new business owner, direct state-sharing API, fifth block or a global native
revision domain. A same-database implementation can serialize append and receipt
against the transport head; a distributed implementation must supply equivalent
linearizable fencing. A broker's unordered callbacks or eventual head polling
alone do not satisfy the rule. Implementation conformance checks verify this scoped
atomic fence explicitly; actual storage/transport proof remains a runtime gate.

If incident commit precedes receipt commit, retain the exact pending commitment
and slot and block the receipt. If the receipt committed first, never reverse,
re-add, re-release or silently rewrite it; block future affected eligibility.
Result and incident delivery in either order therefore have the same safe
outcome for the same committed incident/receipt order. Merely reversing a later
incident's *discovery* relative to an already committed receipt is a different
factual history and correctly leaves that receipt intact.

Known same incident revision plus identical canonical content is a no-op.
Different content at that revision is a durable integrity conflict before stale
filtering. Older unknown revisions can be retained as covered history without
regressing a newer accepted state; later conflicting replay of that covered
revision blocks. Immutable incident identity/scope/evidence/protected-result
binding cannot change with revision. RESOLVED requires authoritative referenced
proof that the evidence is reconciled and the original terminal result remains
unchanged. It does not authorize a financial correction, reopened position or
new close. A genuine correction requiring a changed result remains quarantined
outside normal replay. A resolved incident cannot resurrect; new evidence is a
new incident. Other incidents/conflicts independently retain their safety block.

### T02 — Revision-bound financial FINAL on every active path

The terminal financial record is immutable, not an ordinary mutable financial
state with a non-null result ID. Its proof binds the actual execution-ledger
revision/content (or authoritative execution-derived checkpoint), accepted
canonical financial source set and revision, all mandatory fee/rebate/funding/
other-cost coverage revisions and completeness certificates, proven attribution
resolution/allocation revisions, and existing accounting-effective/day basis.
The source set carries identity, amount/sign/currency, effective/source times,
execution links and applicable source provenance from the normalized factual
ledger. Planned fees or Entry never replace factual evidence.

Before FINAL, incomplete proof remains RECONCILING. At FINAL commit, recheck the
current bound proof and persist result, basis and actual terminal outbox together.
After FINAL, already-covered identical facts are no-ops. New cashflows, changed
immutable source content, same-revision conflicting coverage, a higher
contradictory coverage certificate or a changed execution/attribution/day basis
are retained separately in quarantine. They cannot change accepted source rows,
net, day, committed completeness or state back to ordinary mutable RECONCILING.
Known same-revision content equality is checked before stale filtering. Older
non-conflicting evidence cannot regress coverage. Higher unchanged COMPLETE
corroboration can be retained as supplemental history, but never replaces the
committed proof. Its revision/content is also checked on later replay.

Order Lifecycle's financial-finalization, close and accounting-day paths route
every relevant post-final incident through T01. Capital/slot release is the separate Portfolio consumer's fenced
receipt operation, never `result_id exists => release`. A known pre-receipt
financial incident withholds the first release; a post-receipt incident preserves
once-only history and blocks future eligibility.

Order Lifecycle's execution-linked non-funding allocation processing also freezes its committed
component proof, source set, allocation balances and posting keys on component
FINAL. Component FINAL is not a full-tranche result. A later component
contradiction blocks further parent finalization; when actual full terminal
results already reference that component, Lifecycle uses its explicit durable
parent-result links to emit T01 for each affected result. It never manufactures
tranche/result lineage from a cashflow. Funding and fee allocation arithmetic is
unchanged; this guard changes only evidence finality and receipt permission.

### T03 — Current live-protection proof is a separate derived object

Lifecycle persists historical native child mappings independently from current
live-protection eligibility. The current proof binds the original request's
exact native scope, query request/response identity, authoritative as_of/source
generation, completeness proof, expected tranche-owned child identities and
field-proven current live status. Membership in an older complete query is not
current evidence after a newer applicable complete query.

A newer COMPLETE GET_OPEN_ORDERS query for the same scope that omits an expected
TP or SL invalidates current live verification immediately, retains historical
mapping, and enters RECONCILING. A newer complete empty set is the same case for
all missing children. Request authoritative order history/executions/terminal
facts on the existing Lifecycle ↔ API edge. Absence alone proves neither fill,
cancellation, terminal authority nor permission to create replacement protection.
No blind replacement/cancel is introduced. Terminal history may establish a
particular child outcome only with the existing field-aware provenance rules;
it does not by itself finalize the tranche or authorize a replacement.

Older complete query replay cannot restore live eligibility. Same-generation
complete membership contradictions retain a durable integrity condition. Equal
source-time field enrichment that does not change complete membership remains
allowed by S02; this correction must not weaken its true-conflict detection.
Other scopes cannot refresh this scope. New partial evidence cannot claim a
complete live set. Restore the current proof from its evidence journal on restart,
not from the union of all historically observed child rows.

### T04 — Prove source conservation before native quantity mutation

An allocation ID's global immutable binding remains necessary, but is not itself
quantity authority. For each authoritative native source execution/evidence
quantity effect, persist its account/environment/native scope, observation and
resolution identity, source revision/content, original exact source quantity,
complete allocation membership/proof and committed quantity receipts.

The current deterministic choice is **stage pre-manifest allocations with zero
quantity effect**. A complete manifest must be validated against an authoritative
source partition before applying any of its allocations. The internal proof uses
half-open exact quantity slices `[start_quantity,end_quantity)` within each
source execution's `[0,total_quantity)`. Each allocation binds its source slices;
their lengths sum to its exact allocated quantity. Across the complete manifest,
slices must be positive, disjoint, gap-free and exactly conserve every included
source total. Source totals must conserve the observed native reduction total.
The proof is supplied by factual attribution, not inferred from price, time,
symbol or cashflows. No allocation is heuristically chosen as the winner of an
overlapping claim. Invalid/incomplete proof cannot authorize subtraction.

These are Lifecycle-internal attribution proof records; the existing strict
logical allocation/manifest wire retains its governed fields and references the
same source execution and allocation identities. No API strategy logic or new
wire edge is added. The ORDER_EVENT v7 consumer semantics require staging until
complete proof; another contract version is not changed.

Lifecycle is the quantity-attribution owner and validates the disjoint source
partition before issuing resolution_complete=true. The existing allocation_evidence
references identify its retained proof and source records; no new wire field is
needed. Portfolio does not reconstruct slices from native prices/quantities or
become another attribution owner: it stages strict allocation messages, verifies
the complete Lifecycle manifest's identity, exact member bindings and conserved
observed total, and applies each named allocation only once. A missing or
contradictory referenced Lifecycle proof cannot authorize COMPLETE at the producer.
Source-partition validation/application remains owned by Lifecycle; Portfolio's separate logical projection cannot duplicate its source effect.


Freeze complete membership plus each allocation/source-proof digest. Accept a
valid member once, atomically subtracting its proven tranche quantity, advancing
per-source consumed quantity and committing the global application receipt.
Never exceed a source total, reuse an already applied slice, or rebind an ID.
An outside-manifest alias is durably quarantined and has zero effect. Independent
valid manifest members still reconcile; the alias's safety block remains even
when the valid attribution is complete. A manifest is not a second quantity
application. Manifest-first and allocation-first orders converge to the same
accepted receipts/exposures and persistent safety block for contradictory aliases.

A source quantity of four split A=one and B=three remains valid. A source quantity
of one described twice under two IDs cannot cause two units of reduction, even
before a manifest arrives. Quantity proof may be staged across restart; quantity,
source consumption and receipt application must commit atomically. No strategic
partial-close or change to funding/non-funding financial allocation is introduced.

### T05 — Internal Set normalization is not an export operation

The Set-owned working-normalization operation, denoted
`normalize_working(value, baseline)`, returns the canonical TT_SET_NUMERIC_V1
working-grid result. Generic `normalize` has these same internal semantics.
Existing internal comparisons consume that exact result with no epsilon.
The separate Set-owned boundary/diagnostic serialization operation, denoted
`serialize_normalized_for_handoff(value)`, is used only where a governed field or
diagnostic export actually allows it. This operation adds no Market Handoff field.
Serialization cannot mutate working state or a checkpoint, and must happen after
any gate that requires working precision. The policy remains TT_SET_NUMERIC_V1;
no threshold, formula, signal or contract version change is needed.

## U01–U06 — focused clarifications (normative)

These corrections govern the existing owners and factual semantics. They introduce no new boundary, wire version, trading parameter, signal, allocation formula, accounting-day policy or Portfolio limit. ORDER_EVENT remains v7. Existing T01–T05 and P1–P15 requirements continue to apply; the clarifications below govern the U01–U06 implementation paths.

### U01 — Current accepted applicable financial source set

Order Lifecycle maintains, for each financial component scope, a deduplicated `accepted_applicable_source_set`, `accepted_source_set_revision` and canonical content digest. The scope binds native scope, authoritative execution/source identity, component classification and its attribution proof. A new applicable canonical source increments the accepted-set revision. Identical replay or proven alias enrichment does not create a second source or increment the economic set revision. A financial component may accumulate separate component sub-balances for the same source execution; its proof binds all of them.

A new accepted applicable source before FINAL immediately invalidates any previously computed finality eligibility. Allocation receipts already validly committed remain once-only; they do not authorize ignoring the new source. In one atomic check-and-freeze transition, the owner must establish agreement among: the current accepted applicable source records and revision; authoritative complete coverage and its mandatory IDs; completed source-quantity attribution; each committed allocation manifest and current attribution-revision receipt; and the balance/result being frozen. Every accepted applicable source must be in the covered, attributed and committed proof. Per-source signed sums, component balances and once-only posting receipts must agree. An older coverage certificate cannot authorize FINAL over a newer source set, even if allocation happens before or after that certificate arrives.

A certificate's missing ID is not a source deletion or proof of non-applicability. Existing governed component/native-scope/source classification can establish non-applicability using authoritative factual identity; any such exclusion must retain its factual reason, scope, authority/provenance and revision in the final proof. No discretionary exclusion or local `not_applicable` flag is introduced. A positive source already accepted as applicable in the fixed execution/component slice must not be removed merely to reconcile totals. If later evidence challenges that applicability, retain both facts and reconcile their identity/scope before another finality claim. The conformance case for this fixed execution/component slice has no independent source-deletion/exclusion operation; `governed_exclusions` is empty and all accepted sources in that case must be covered. Contradictory accepted source content is quarantine, not an exclusion shortcut.

Coverage history binds canonical certificate content to its revision. Compare a previously observed revision's content before stale suppression; same revision with changed content is an integrity conflict. Genuinely identical replay is inert; a new older revision cannot replace current completeness. Source acceptance, allocation effect plus receipt, and final proof freeze obey the existing durable transaction/cutpoint discipline.

Fixed example: E-SPLIT qty4, A1/B3, CASH-E −0.04, then AUDIT-CASH-NEW −0.08. Neither delivery/allocation order may finalize with only CASH-E covered. Once both are covered and committed under current attribution, A=−0.03, B=−0.09 and signed sum=−0.12. The approved allocation weighting and residue rule are unchanged.

### U02 — Complete immutable financial source core and post-FINAL producer coverage

The canonical immutable core of the current `financial_record` is exactly the following required fields, preserving explicit nulls and exact decimal/raw source representations:

`cashflow_id`, `transaction_id`, `execution_id`, `component_type`, `currency`, `signed_amount`, `amount_quantum`, `effective_at`, `recorded_at`, `symbol`, `native_side`, `position_idx`, `client_order_link_id`, `exchange_order_id`, `parent_exchange_order_id`, `child_id`, `fee_classification`, `funding_classification`, `cost_classification`, `source_endpoint`, `source_record_id`, `source_field`, `source_amount`, `source_sign_convention`, `economic_direction`, `normalization_profile_version`, `settlement_price`, `settlement_price_basis`, `settlement_price_as_of`, `settlement_source_ref`, `pnl_scope`, `period_scope`.

`aliases` is a supplemental, governed equivalence set, not permission to mutate that core. A new representation of an already accepted cashflow may have a different primary (`source_endpoint`, `source_record_id`, `source_field`) only if the normalized factual adapter explicitly links it to an accepted representation through a proven alias and every other immutable field agrees. Every accepted representation's own core is thereafter immutable. Unlinked primary-provenance replacement, an alias bound to another cashflow, or any changed economic/native/time/normalization field is conflict. Alias enrichment records supplemental provenance, never a second economic effect, never a changed accepted-set economic revision, and never rewrites the committed FINAL proof. Order Lifecycle's source-equivalence validation does not discover or guess factual aliases.

At every active financial terminal guard, validate the complete immutable core and raw sign semantics before any duplicate/terminal early return. Same identity/core is idempotent. A different immutable core, new applicable source, or invalid source evidence after FINAL preserves the accepted final result, persists the contradictory evidence and quarantine, and uses existing explicit durable parent-result links to publish T01 POST_FINAL_INTEGRITY. No parent result or tranche is inferred from symbol, price or timestamp. A component with no linked committed parent remains blocked locally and cannot be used in a later parent finality claim; any existing linked parent receives the durable incident.

The existing T01 transport and Portfolio consumer semantics are unchanged: a known committed incident fences a pending first receipt/release; an already-applied receipt is never undone or posted again, while affected future eligibility is blocked. Incident and financial-result deduplication domains remain independent. Source fact plus quarantine/outbox persistence and parent linkage obey existing ownership and durability rules. The financial evidence-ingestion path must likewise persist its complete supplied raw-source core, not only a normalized money projection.

### U03 — Canonical acceptance resolution before tombstone suppression

Persist the accepted resolution binding and its observed content by integrity revision and resolution identity: `resolution_id`, `integrity_revision`, selected `entry_accepted_at`, selected factual provenance, canonical covered evidence set, resolution status and `resolution_evidence_ref`. The existing immutable resolution evidence reference binds the factual resolution proof/reason; no new wire reason field is introduced. Evidence-set order and exact duplicates do not change canonical meaning. Content under a proof reference may not be replaced silently.

Before a resolved tombstone suppresses replay, compare any previously observed or accepted resolution revision/identity with its canonical content. Same revision and same content is idempotent and cannot clear a later conflict. Same accepted revision or reused resolution identity with changed selection/provenance/evidence/proof is durable integrity conflict. Preserve the originally accepted timestamp and historical resolution; restore or retain the Portfolio eligibility block and unresolved cooldown status, without moving or restarting the cooldown origin. This comparison also applies to a previously accepted older revision after a newer resolution. A genuinely older covered factual observation may be a stale no-op only after these content checks; a revision-less content shortcut is not permitted.

Lifecycle's resolution owner and Portfolio's consumer both apply this rule. An invalid/conflicting RESOLVED revision first seen before another same-revision variant must not cause that revision's conflicting content to be forgotten. A new authoritative resolution follows the existing explicit resolution path rather than silently overwriting the tombstone. R03-04's accepted 12:00 remains 12:00 when ACR-A/revision4 is replayed selecting 12:01; conflict/eligibility block is restored.

### U04 — Rejection is not authority to erase execution

An ordinary zero-fill rejection releases submission resources only when authoritative factual evidence establishes cumulative execution quantity zero, no accepted/filled execution, no ambiguous outstanding create/execution authority, and terminality of the same bound entry attempt. Missing proof retains the submission resources while reconciling; later complete zero-execution terminal proof may resolve that missing-proof state and release exactly once. This is not a permanent slot hold for every rejection.

Any confirmed execution takes precedence over a contradictory rejection status. Retain logical filled exposure, its current capital, the position slot and any unresolved remainder authority. A filled OPEN/PARTIALLY_FILLED tranche must not become ordinary zero-fill REJECTED or lose its slot because a delayed rejection arrives. Record the contradiction under existing reconciliation/integrity semantics, with duplicate/restart-safe evidence identity. Partial execution preserves the filled/live-reserved capital decomposition until its remainder is authoritatively terminal.

Conversely, a later attributable execution contradicting an earlier proven zero-fill rejection is factual exposure, not permission to resubmit. Restore its liability/occupied slot, block affected eligibility and reconcile; do not discard execution, clamp liabilities to free capital, reopen the terminal CREATE authorization, or issue a compensating trade. This follows existing factual execution precedence and native reconciliation; no new trading action is introduced. Implementation conformance cases for native fill and rejection carry explicit synthetic execution/terminal proof rather than assuming missing evidence from an action name. These are conformance inputs, not new wire shapes or native profile certifications.

### U05 — Raw magnitude/direction validation precedes normalization

For MAGNITUDE_WITH_DIRECTION, retain and validate raw source magnitude before converting it. The canonical truth table is:

| Raw magnitude | Direction | Meaning |
|---|---|---|
| 0 | ZERO | valid signed zero |
| >0 | CREDIT | valid positive signed amount |
| >0 | DEBIT | valid negative signed amount |
| >0 | ZERO | contradictory; unresolved/invalid, never normalized to zero |
| 0 | CREDIT or DEBIT | contradictory; unresolved/invalid under the existing signed-value direction consistency rule |
| <0 | any | invalid magnitude |

COST_POSITIVE and CREDIT_POSITIVE retain their existing mappings and signed-direction consistency requirements. Strict shape validation alone does not establish semantic validity: the API/owner ingestion checks must validate the raw relationship, normalized signed amount and source quantum. No epsilon, guessed direction or source-value erasure is permitted.

An invalid pair is rejected/quarantined according to the existing evidence policy, with the raw source retained for reconciliation. A COMPLETE certificate listing that invalid source cannot legitimize it or permit FINAL. Collecting other valid evidence does not clear the unresolved sign contradiction. If discovered after FINAL, preserve the committed result and route the existing T01 incident to any linked parent; first pending release is fenced, already-applied posting remains once-only. Corrected authoritative direction requires explicit factual reconciliation, not an inferred CREDIT/DEBIT guess.

### U06 — Active version index

ORDER_EVENT remains contract version 7. POST_FINAL_INTEGRITY and the existing logical, native observation/resolution, acceptance-integrity and no-reduction native-scope semantics retain their current wire shapes. U01–U05 govern producer/consumer behavior and its conformance verification within those payloads and require no wire version or shape change.


## V01–V05 — focused evidence-ingestion synchronization (normative)

These clauses do not add a business owner, boundary, wire variant, trading rule, threshold, selection policy, allocation formula, accounting-day policy or execution fallback. ORDER_EVENT remains v7. P/R/S/T/U requirements remain effective; these clauses require implementation transitions to remain consistent with their evidence-retention invariants.

### V01 — Known financial identity before pre-FINAL routing

For a normalized record naming an already accepted canonical `cashflow_id`, Lifecycle compares the complete U02 immutable core and governed alias representation **before** component classification, execution-lineage or native-scope routing can reject the record. Unchanged content is idempotent; a proven alias may enrich provenance without changing source identity, source-set revision, frozen proof or effects. Changed scope, ownership, classification, exchange-order lineage, economic/effective time, amount or governed provenance is an integrity challenge, even before FINAL.

A known-identity contradiction and its raw record are retained in the same transaction as the eligibility block. The original source is not overwritten or deleted. Derived finality eligibility is cleared; pre-FINAL state is RECONCILING and no old coverage/allocation proof can produce FINAL. Already committed effects remain immutable. Duplicate contradictory delivery is idempotent or monotonic, and restart restores the block. Replaying the original source or old complete proof is not an integrity resolution. Only the existing authoritative integrity-resolution rules can clear the block; the focused allocation slice adds no automatic clear operation. A genuinely unrelated foreign source can still be routed/rejected normally without poisoning this source set. The U02 terminal guard and explicit parent-result linkage are unchanged.

### V02 — Facts before terminal/stale execution gates

Factual evidence ingestion is distinct from granting or mutating execution authority. After CLOSED or a resolved intent, entry-terminal, protection-disable, exit-child-terminal, coverage and other-authority facts still reach known-revision content comparison. Order Lifecycle's accounting-day path also applies this rule to authority facts carried within cleanup actions. Terminal gates continue to prevent acquire/authorize/dispatch/retry/finalize from creating new authority or reopening the tranche; they do not discard contradictions.

For each authority domain/child key and coverage component, persist the accepted revision and complete canonical content, not only the latest record. Known revision + identical content is a no-op. Known revision + changed content is durable quarantine, including replay of revision1 after revision2. Compare this binding before stale suppression and before rejecting changed content at that known revision as an invalid proof. Genuinely older unseen irrelevant evidence follows the existing stale-evidence rule; it is not promoted to current authority. Hydration can seed the current retained fact into history but cannot invent absent historical revisions.

A higher-revision corroborating fact observed after FINAL is retained as supplemental history only. It must not replace the frozen authority/coverage proof, economic result, accounting effective time, terminal time or resolved intent. Later different content at that observed supplemental revision is detectable and quarantined. Raw contradictory evidence is retained before/after FINAL. Pre-FINAL Day proof contradictions prevent closure/finalization; post-FINAL contradictions append the existing parent-linked POST_FINAL_INTEGRITY event in the owning transaction.

The T01 ORDER_EVENT v7 boundary remains unchanged: an incident committed before a pending receipt blocks release through the committed-prefix fence, including an undelivered incident. A receipt already applied stays once-only and immutable; subsequent incident delivery blocks future eligibility. Incident identity and terminal-result identity remain independent. Rollback/redelivery conformance checks verify the specified transitions; they do not establish empirical database/outbox atomicity.

### V03 — Complete revisionless acceptance observation

For native acceptance input without an integrity object, validate the tuple `(entry_acceptance_status, entry_accepted_at, complete entry_acceptance_provenance)` before any covered-provenance shortcut. PROVEN requires the existing governed mapping and agreement of normalized time with `provenance.native_value`; UNAVAILABLE requires absence of accepted time/provenance. Inconsistent status/provenance and unknown raw status combinations cannot become clean accepted observations.

The source identity is the governed endpoint, record identity, source field and mapping profile. The covered factual content includes the selected native value and proof reference as well as the normalized status/time. Reconstruct each valid covered PROVEN observation from the accepted resolution's evidence and compare the entire binding. Only an identical, internally consistent covered observation can be stale; membership of a provenance digest alone is insufficient. A different fact under the same covered source identity reblocks integrity, retains the raw observation and leaves the original accepted timestamp and accepted resolution history immutable. Previously disputed but now explicitly covered identical older evidence remains a no-op.

Lifecycle publishes CONFLICT through the existing acceptance-integrity fields of ORDER_EVENT v7. Portfolio retains the selected 12:00 origin in the witness, sets conflict and cooldown_unresolved, and creates no 12:02 origin. Old resolved events cannot clear the later conflict. Ordinary native order `updated_at`, fill quantity and mutable order status are not themselves acceptance-origin evidence; their legitimate evolution is not a new cooldown origin. No new native timestamp mapping is certified here.

### V04 — Atomic invalidation of current protection dependencies

Current live-protection proof is derived evidence, separate from historical child mapping. Its dependencies include current query scope/generation/completeness, expected entry/child lineage and protection geometry, permitted live statuses and mapping profiles, effective native child facts and per-field authority versions. A child terminality/status change, geometry/quantity/reduce-only/close/linkage contradiction, or a changed effective dependency invalidates the proof in the same ingestion transaction, for GET_ORDER_HISTORY and every other operation that merges native facts—not only GET_OPEN_ORDERS.

The reference proof retains full source digests as its generation-time provenance snapshot and separately binds the effective dependency digests. Effective digests exclude accumulated unused stale callbacks; adding old corroboration cannot advance current field authority or invalidate a still-consistent proof merely by changing a history container. Current field values, proven status and their per-field versions remain bound. Native-field integrity conflicts invalidate current verification even when the accepted value itself is not overwritten. Existing S02 factual enrichment and T03 current-complete-query invalidation remain effective.

Invalidation atomically clears current_live_proof and live_mapping, retains historical_mapping, and sets RECONCILING. No later reconcile call is required to make persisted state safe. Before exposing PROTECTION_VERIFIED on hydration, compare stored dependencies with current persisted native facts, expected configuration and query evidence; missing or mismatched dependencies require reconciliation. New complete authoritative live evidence may rebuild proof under existing rules. Terminal child facts neither authorize blind replacement nor establish tranche CLOSED, and old live callbacks cannot resurrect terminal children.

### V05 — Known historical identity before semantic rejection

Market response ingestion distinguishes unrelated malformed input from a challenge to accepted immutable request/selection/page/source evidence. Before ordinary semantic rejection, inspect enough of the bound request, selection, page, snapshot, final manifest and native-record identity to detect whether accepted evidence is challenged. The preflight does not accept invalid records, select a new range, infer a winner or introduce page revisions.

When a known identity is contradicted—even if payload validation fails such as AVAILABLE with source_finality_confirmed=false—retain the raw response, validation failure and integrity incident and invalidate the affected current assembly in the same durable action. Preserve original pages, source records and every already frozen Market Handoff. State is RECONCILING; new analysis/handoff generation cannot use the old assembly. Correct old page replay, assemble() and restart do not clear that incident. Authoritative reconciliation follows existing immutable selection rules; no silent replacement is permitted. Unrelated malformed selection/request input is rejected normally without poisoning unrelated accepted selections. Existing valid-response S04 contradiction handling remains unchanged.

### Focused reference/validation boundary




## W01–W03 — Identity and known-content checks before suppression

These W rules are current normative ingestion requirements and do not alter business ownership or wire shape.

### W01 — One monotonic accepted-proof history invariant

Every affected proof consumer first resolves the owner-local proof identity, then compares any previously accepted revision's full canonical content, before stale, semantic or terminal suppression. This applies to Lifecycle financial factual basis, Lifecycle financial allocation/attribution resolution, and native-scope clearance resolution consumed on the existing Order Event boundary. Existing Close/Day authority histories, component source coverage and acceptance-resolution histories retain their own already-conforming domains; no ownership is transferred.

For every accepted identity/revision, durably retain the identity, revision, canonical content and its digest, including evidence/member sets, selected factual values, provenance/evidence references and completeness as present in that proof. Accepted incomplete progress and permitted supplemental corroboration count as accepted history. Digests are bindings, not substitutes for retaining the accepted content. Revision keys and journals are scoped by the existing owner/aggregate and proof domain; FINANCIAL_BASIS in the focused Finance slice is owner-local, not a global proof ID.

Known revision plus identical content is idempotent. Known revision plus different content is a durable integrity contradiction even when numerically older than the current revision. Retain the raw challenge, preserve the original history/current proof, and atomically block affected finality/clearance. Only after that comparison may an unseen older revision follow its existing stale/no-authority rule. New valid revisions retain the existing monotonic membership/completeness protocol; this specification grants no new authority.

Post-FINAL corroboration, where already permitted, appends supplemental history without replacing frozen proof, accounting day, economics or committed effects. A later change at the supplemental revision is a contradiction. A native-only completed-clearance tombstone remains immutable; a contradiction restores its existing scope block, retains the tombstone and produces no quantity or financial effect. No financial-result identity is invented for a native-only incident.

Before financial FINAL, a contradiction prevents finality. After FINAL, retain frozen economics and use the existing parent-linked ORDER_EVENT v7 POST_FINAL_INTEGRITY path. An incident committed before an unapplied receipt fences release even before message delivery. An already-applied receipt remains once-only and immutable; the incident blocks future eligibility. Financial allocations already committed to A/B are not recomputed or redistributed.

Hydration restores the actual serialized proof journal. Initial implementation state may be initialized only with the actually supplied current proof and must never infer historical contents from the latest proof. Migrating a persistence store requires retaining or replaying its actual accepted evidence; database atomicity remains a runtime conformance obligation.

### W02 — Accepted historical ownership precedes the incoming selection echo

Before rejecting a response, resolve its claims against retained request/page/selection/snapshot/native-source ownership. A retained request/page binding is authoritative; a page name alone is not. Cross-request lookup additionally requires the scoped symbol, snapshot, dataset and matching accepted selection digest or native-record identity. The incoming selection ID cannot be the sole lookup key.

A known accepted page under a changed selection or request ownership is a contradiction, including when source finality, manifest or immutable native content is also invalid. Retain the raw response and semantic error in the same action as invalidation of the ORIGINAL selection's current assembly. Do not accept the new echo, overwrite accepted page/source facts, infer a page revision, or silently rebind ownership. A semantic exception must not roll back this evidence capture.

Current eligibility is withdrawn and state becomes RECONCILING. Existing frozen handoffs remain immutable audit evidence; NEW analysis/handoffs are denied. Correct old response replay, assemble and restart do not resolve the contradiction. No new in-place recovery operation is introduced; existing authoritative recovery requirements continue to apply. A malformed foreign response that shares merely a common-looking page name without accepted scoped ownership is an ordinary rejection and does not poison unrelated selections.

### W03 — Canonical and native alias ownership precede source routing

Before component/execution/native-scope routing rejection, resolve the incoming financial record through both its canonical source/cashflow ID and every actually accepted native primary/alias provenance identity it claims. Existing alias ownership is persisted alongside immutable source cores and restored across restart; actually retained primary cores can supply an initial index binding without inventing lineage.

Any resolved owner makes the record a known-source challenge. Compare the complete immutable source core and governed representation before ordinary rejection. A changed canonical ID under an already-owned native identity is an ownership conflict, including when execution, scope or component also changes. The established rules do not permit a second canonical cashflow ID to become an alias for an already-owned native identity. Legitimate enrichment remains a proven additional representation of the SAME canonical source under the existing explicit alias linkage.

Retain raw contradictions and the integrity block in the same action, preserving source identity, accepted aliases, source-set history and committed financial amounts. Pre-FINAL cannot finalize cleanly across restart. Post-FINAL uses the existing component-to-parent incident/fence mechanism; parent IDs are explicit existing linkage, not inferred. Truly unrelated sources continue ordinary routing/rejection; a new applicable post-FINAL source remains subject to the existing completeness contradiction rule.

### Required scoped evidence and unchanged boundaries

The processing invariant is IDENTITY RESOLUTION → KNOWN-EVIDENCE CONTENT COMPARISON → DURABLE CONTRADICTION CAPTURE → ONLY THEN stale/routing/terminal suppression. This is a local ordering correction, not a new signal or trading decision. Four business blocks plus factual API, APPROVE-before-grant, exact submission commitment, source conservation, Entry/SL/TP, funding/non-funding allocation arithmetic, accounting day and POST_ONLY execution semantics remain unchanged.

Acceptance tests derived from these rules must cover retained content/raw challenges, frozen-effect immutability, receipt ordering, unrelated-source controls, duplicates, reordered replay and modeled commit/restart cutpoints. Backend and native-exchange conformance remain separate runtime obligations.


## X01 — Full accepted acceptance-integrity history (normative)

Within the existing attempt/entry lineage, Order Lifecycle journals each actual published integrity revision and Portfolio journals each actual accepted revision. `accepted_acceptance_bindings` is local durable state, not a wire field. CLEAR, CONFLICT and RESOLVED are all covered, including an accepted CLEAR snapshot with UNAVAILABLE acceptance and revision zero. Persist actual complete bindings; never reconstruct an older binding from the latest resolution.

The binding contains the integrity revision and state, acceptance status, carried `entry_accepted_at`, acceptance provenance/native selected fact, the complete evidence-identity set, conflict identity, resolution identity and resolution evidence reference when applicable. The existing governed evidence reference binds the factual resolution proof/reason; no separate invented reason field is introduced. Canonicalize evidence as a set (ordering and duplicate representations are not different facts). Transport event IDs, delivery ordering and unrelated lifecycle/fill revisions are not part of acceptance content.

Processing is: resolve existing lineage; look up the incoming accepted revision; compare its complete canonical binding; persist any challenge and integrity block; only then apply covered, stale, terminal or semantic suppression. Identical accepted bindings are idempotent. Changed accepted bindings preserve the original timestamp/provenance and all accepted tombstones, journal the challenge, set/retain the existing acceptance conflict and unresolved cooldown, and block affected Portfolio eligibility. A later resolution covering the evidence set does not attest a changed timestamp, state, provenance or evidence set at an earlier accepted revision. Revision-bearing tuples must also satisfy the same timestamp/provenance consistency as revisionless facts. Existing rules for an unseen older revision and ordinary newer evidence remain in force.

Lifecycle and Portfolio use their existing publication/consumption boundaries, not a direct shared state owner. Hydration restores each owner's actual published/accepted history and retained challenges. Publication that would reuse a known integrity revision with changed content fails closed. Replays never create a second acceptance or reset/extend the cooldown origin.

## X02 — Historical accepted ownership independent of both echo IDs (normative)

Historical Market Data contradiction preflight resolves accepted request/selection/page/snapshot/native-source relationships before trusting incoming `selection_id` OR `page_id`. Neither incoming echo must remain unchanged for accepted evidence to be challenged. Existing durable requests, governed selections/digests, page-request bindings, accepted pages, source records and snapshot bindings form the ownership graph; it is not inferred from the latest incoming response.

An exact retained request-to-governed-selection-digest relationship can identify the original owner despite changed echo IDs. Scoped native-record membership is looked up across accepted pages independently of the incoming page lookup and is anchored by an accepted request plus the exact governed selection relationship (excluding only cursor/selector identity), or by the accepted snapshot and exact selection digest. Symbol/dataset and the governed range/as-of relationship remain scoped. Superficial symbol, price or native-ID similarity alone must not poison another selection.

A challenge journals the raw response, accepted ownership anchors and semantic validation error; preserves original accepted pages/source facts; invalidates the original current assembly; enters existing integrity/reconciliation; and blocks new analysis/handoff creation. Already frozen handoffs remain immutable. Ordinary rejection, including selection echo mismatch, cannot roll this integrity capture back. Do not rebind the page to new incoming IDs or invent a page revision. An unrelated malformed response without accepted relationships is rejected without poisoning another selection. Duplicate challenges are idempotent and restart retains the block. Replaying original evidence alone is not authoritative recovery; this correction adds no recovery policy.

## X03 — Durable known-evidence preflight before mixed-batch rejection (normative)

For authority/cleanup batches, first inspect ALL identifiable proof groups in a deterministic order and compare every known accepted revision/content binding. Collect all contradictions before applying any ordinary new proof update or allowing companion semantic validation to abort the batch. The integrity phase may only retain raw contradictory evidence, quarantine/block state and existing parent-linked incident/outbox state; it must not accept the disputed facts or ordinary updates.

Persist that integrity phase within the existing owner-local ingestion discipline. Then validate the ordinary update batch completely and apply its valid ordinary mutations atomically. If a companion is malformed, reject the ordinary batch with no partial normal proof updates but preserve the integrity checkpoint. Reversal of input proof-group ordering does not change the durable integrity outcome. Identical/older unseen proofs retain their existing rules after known-content comparison.

Before FINAL, a retained challenge denies finalization. After FINAL before receipt, preserve the frozen result and emit/retain existing ORDER_EVENT v7 POST_FINAL_INTEGRITY; the pending receipt fence withholds commitment and slot release. After a receipt is already posted, keep historical posting once-only and block future eligibility through the existing incident consumer. Incident IDs and terminal result IDs remain independent, with no reversal or recomputation of frozen economics.

Distinguish an intentional crash before ANY durable commit from ordinary semantic rejection after a known-evidence challenge. The former restores the original state and requires redelivery; the latter retains the integrity checkpoint. Hydration restores actual histories, incident identities/outbox state and quarantine. This is a normative transaction requirement; documentation-level conformance checks do not certify a production database implementation.

### PREVENTIVE SYNCHRONIZATION — same invariant, no economic change

Apply the same known-content-before-parse/rollback order to the existing compact financial-source path, Close/Day coverage proof paths, multi-child close-authority proofs and protection native-query batches. A malformed value or omitted field on a known source/proof is a challenge, not permission to discard it during normalization. Preflight every identifiable known child/native row before another malformed row can abort the batch. Reject ordinary mutations atomically, retain known contradictions, preserve accepted sources/history and frozen results, and invalidate unsupported current live protection without erasing historical mapping. Unknown unrelated malformed input retains normal rejection. Existing source signs, allocation weights, arithmetic, protection dependency semantics and native field-authority rules remain unchanged.



## POST_FINAL_INTEGRITY incident_class taxonomy

The existing ORDER_EVENT v7 enum has one deterministic semantic classification; classification changes observability only and does not change blocking, receipt or release semantics.

| incident_class | Normative subject | Examples |
|---|---|---|
| `POST_FINAL_EXECUTION_CONTRADICTION` | The contradiction changes factual execution/exposure chronology itself. | Newly discovered fill contradicting terminal exposure; conflicting execution quantity, price, side or source; execution chronology contradiction relevant to the frozen terminal result; native observation contradiction with factual execution/quantity effect. |
| `POST_FINAL_FINANCIAL_CONTRADICTION` | The contradiction changes monetary factual/accounting evidence. | Fees, rebates, funding, supported realized costs, cashflows, financial source-set membership, financial coverage/completeness certificates, immutable financial-source core, or monetary attribution/finality evidence. |
| `POST_FINAL_PROOF_CONTRADICTION` | The contradiction changes only non-monetary control, ownership, authority, reconciliation or terminality proof. | Acceptance proof, protection proof, close/child authority proof, native-scope ownership/clearance proof, lifecycle/reconciliation proof, or lineage-only native observation contradiction. |

Precedence is by subject, not detection path: if the contradiction changes actual execution/fill history, classify EXECUTION; otherwise if it changes monetary accounting evidence, classify FINANCIAL; otherwise classify PROOF. A financial coverage/completeness contradiction is always FINANCIAL. A native observation with a factual execution/quantity effect is EXECUTION, while a lineage/ownership/clearance-only native observation contradiction is PROOF. One incident receives exactly one class from these rules. Mixed raw deliveries may produce separate incidents only when they challenge distinct accepted evidence identities; the same challenged accepted fact is not duplicated across classes.

## Y01–Y02 owner-local evidence retention synchronization

These rules clarify ingestion ordering only. All existing trading, allocation, accounting, close, acceptance-origin and capital rules remain unchanged. No new business owner, edge, wire family or contract version is introduced.

### Y01 — Immutable accepted native-observation identity

For an already accepted native_observation_id, resolve the persisted observation before any stale return or numeric/required-field parsing. Its original native-scope revision is itself part of the binding, not a delivery-order watermark. A lower revision at the same ID is therefore a changed replay even when the other fields match. Compare authoritative source quantity, full native scope (including symbol, side and position identity), and actually supplied source/provenance facts against the saved accepted binding. Canonically equivalent decimal representations remain equal.

A changed or recognizably incomplete replay retains raw evidence and an integrity incident, preserves accepted observation facts, resolution tombstone and every application receipt, and blocks the affected scope. It does not apply or reverse quantities. Later independently valid allocation completion may finish its factual effects but cannot clear the previously retained incident. Identical complete replay is idempotent, including after resolution and reconstructed-state restart.

A genuinely different observation ID is not a replay of the original. Apply existing scope/observation rules; do not invent a global revision watermark for native-observation processing. Allocation-created provisional observations may receive their first authoritative quantity when no quantity was previously bound. Hydration uses persisted accepted binding; initialized owner-local state may include only facts actually present in accepted observation/source proofs, never invent historical provenance or past revisions.

### Y02 — Recognizable accepted financial coverage before parsing

No new wire identifier is introduced. For `GET_FINANCIAL_FACTS`, Lifecycle creates an owner-local accepted coverage-certificate record when it first accepts a coverage proof. The durable primary certificate key is built only from existing envelope fields:

```text
overall certificate key
= (request_id, response_id, GET_FINANCIAL_FACTS, OVERALL)

component certificate key
= (request_id, response_id, GET_FINANCIAL_FACTS, COMPONENT, component)
```

The parent `request_id` is the exact persisted technical request; `response_id` is the accepted factual response identity. `component` is the existing EXECUTIONS / TRADING_FEE / FUNDING / OTHER_EXCHANGE_COST value and therefore distinguishes multiple component proofs in one response. The namespace is Lifecycle's Order Management financial-evidence inbox for one managed account/environment. On acceptance Lifecycle also assigns an owner-local monotonic `accepted_certificate_revision` within `(request_id, certificate-kind, component-or-OVERALL)` and persists the complete immutable binding and lookup indexes. This revision is durable internal state, not a new wire field. Reusing a primary certificate key with different bound content is a contradiction, never a new certificate.

The accepted binding contains: primary certificate key; accepted revision; parent request operation and native scope; requested interval; for component proofs the component, `applicable` and `not_applicable_evidence`; every nested coverage field (`status`, `coverage_from`, `coverage_to`, `missing_ranges`, `pagination_complete`, `next_cursor`, `source_watermark_at`, `source_finality_confirmed`, `source_endpoints`, `reason_code`); the accepted provenance/evidence reference for the raw response; a canonical SHA-256 basis digest over those canonical fields plus the exact accepted source-member identities used to substantiate the certificate; and that exact source-member set. Canonical equality compares the complete binding. Presence is part of canonical content: an omitted field is different from a present field whose value is explicit null, even when strict schema validation will later reject the omission. Decimal/timestamp equivalence follows the owning canonicalization rules; no arrival-order or heuristic similarity is used.

Preflight operates on raw input before required-field parsing. Recognition first tries the complete primary key. If an ordinary owner/revision echo is missing or malformed, the persisted indexes may locate an accepted certificate only by an existing exact anchor that is uniquely bound to one accepted certificate: `response_id`; `request_id + certificate-kind + component-or-OVERALL`; the retained raw-response evidence/provenance reference; or the exact accepted basis digest/source-member identity when that anchor is actually present in the raw adapter evidence. Multiple matches mean unresolved ownership and quarantine; zero matches mean the input is unrelated/unrecognized and ordinary malformed-input rejection applies. Symbol, time proximity, endpoint similarity, arrival order, or partial value similarity are never lookup keys. An incoming echo cannot rebind ownership.

Coverage preflight therefore resolves the accepted certificate and compares complete accepted content before stale filtering, covered-proof suppression, required-field extraction, normalization, semantic validation or terminal routing. A valid unseen proof revision follows existing monotonic acceptance rules and creates its own immutable accepted binding; an existing certificate key/revision can only replay identically. A recognizable omitted bound field, explicit-null change, status change, source-membership change or other canonical-content change is a challenge to accepted evidence. Retain raw input and integrity/quarantine state; never mutate the accepted certificate.

Before FINAL, quarantine denies clean finalization. After FINAL, keep the terminal result immutable and publish the existing parent-linked ORDER_EVENT v7 POST_FINAL_INTEGRITY incident classified as `POST_FINAL_FINANCIAL_CONTRADICTION`. Pending receipt/release is withheld. A previously applied receipt remains once-only with no money reversal, while future eligibility is blocked. Known contradiction capture survives subsequent ordinary semantic rejection. A deliberate modeled crash before any commit is distinct and commits neither ordinary updates nor an incident; redelivery must reprocess the raw challenge.

Restart/hydration restores the immutable certificate history, primary-key index, all permitted fallback indexes, accepted revisions, raw evidence references, basis digests/source-member sets and retained challenges before processing new evidence. It must not reconstruct historical certificate content from the latest response. No backend transaction implementation is supplied or certified by these reference transitions.

### Preventive synchronization — canonical evidence-ingestion invariant

For every governed evidence family that can correspond to already accepted evidence, ingestion order is normative:

1. resolve accepted identity and ownership from raw recognizable anchors before strict parsing;
2. compare the complete canonical accepted content, including presence/omission state for bound nullable or optional fields;
3. durably retain any contradiction and the resulting integrity/quarantine state;
4. only after that checkpoint apply stale or covered-evidence suppression, required-field validation, normalization, routing rejection, semantic rejection, terminal suppression, or rollback of unrelated ordinary malformed updates.

A genuinely unrelated malformed input that cannot be uniquely associated with accepted evidence is rejected normally. A recognizable challenge to accepted evidence must never disappear because another field is stale, missing, malformed, semantically invalid, routed elsewhere or delivered after a terminal state. Ordinary valid updates remain atomic under their existing owner-local transaction rules; contradiction capture cannot be rolled back by failure of an unrelated ordinary update in the same delivery. Hydration restores accepted bindings, lookup indexes, raw retained challenges, quarantine and incident identities before new deliveries are processed.

This invariant applies to the active domains: native observations; native manifests and native attribution/clearance resolutions; financial coverage and component coverage; financial factual-basis/source-set proofs; financial allocation resolutions; entry-acceptance integrity; native-scope reconciliation; close/Day authority and coverage proofs; historical Market Data request/selection/page/snapshot ownership; and current-protection query/proof envelopes. For mixed native observations, factual execution/quantity contradictions remain execution facts while lineage/ownership/clearance-only contradictions remain proof facts. Historical frozen handoffs and immutable financial/quantity effects are never rewritten as an integrity response.

The factual-basis and financial-allocation histories, immutable financial source/alias core, source conservation and post-final receipt machinery retain their existing semantics. No external audit, sweep, test harness or historical artifact is normative for this rule.

## Research isolation — S-005 diagnostic-only boundary

S-005 is owned by Research and may be retained only as diagnostic context in isolated, pinned research/backtest/demo runs. It is not a canonical trading input. It MUST NOT affect Set matching, F-005 direction, Position decisions or construction (including sizing, stops and take profits), Portfolio approvals, Order Lifecycle behavior, or live or paper execution eligibility. It adds no business/API edge, wire field or live runtime dependency. Existing Set-owned volatility and BTC context remain distinct from S-005.

`CTX-REGIME@0.1.0` identifies a non-normative research/demo candidate, not an active methodology version. Its formula, windows, thresholds, labels, symbol/proxy scope and numeric implementation are not canonical product truth. No canonical S-005 formula, domain, input/output contract, numeric policy or live trading semantics is defined here. Research parameters remain configurable; no candidate formula or threshold is incorporated into active trading rules.

`UNKNOWN` and `INSUFFICIENT_DATA` are diagnostic outcomes only. Neither these states nor any regime label is permission, safety, eligibility or a profitability claim.

Research/backtest/demo runs using S-005 MUST retain the methodology package revision, contract versions, configuration IDs and content digests, the numeric policy IDs actually used, historical selectors/source snapshots, adapter/profile assumptions and execution-simulation assumptions. Restart or replay must retain those bindings rather than substitute current configuration or evidence. These diagnostic records have no authority over the certified trading pipeline.

This S-005 boundary is separate from protocol S05 — Global native quantity allocation identity, which remains unchanged.
