# Native factual evidence profile — F01 / F02 / F06

**Document version:** 1; package revision `v1.2.15`. This document constrains normalized evidence on existing API boundaries. It is not a new adapter implementation, new business block, or certification of native exchange behavior. Synthetic profile names in this document are deliberately not production Bybit profiles.

## 1. Evidence, not outbound intent

`orders[]` is a factual collection, never a reconstruction of what Lifecycle requested. Each record carries source endpoint/record identity and per-field provenance: normalized field, endpoint, native record/field, exact raw value, mapping-profile version and retrievable evidence reference. Preserve missing values as null and an unknown role as UNKNOWN. A required Boolean with unknown native meaning is null, not false. “NOT_APPLICABLE” requires supported native semantics; it is not a missing-value substitute.

`native_parent_order_id`, `native_parent_client_order_link_id` and `native_link_group_id` are different native facts, not interchangeable aliases. Populate only a relationship actually present and meaningful under the pinned profile. A client link may join the durable native-entry registry only if that native/client identity is provably bound to one logical entry. A pair/group identity must be native and unique enough for the same purpose; never invent a pair from two matching prices. No tranche, plan, cycle or allocation ID is inserted into these API rows. `order_role` is normalized from native type/create/role evidence; MANUAL_CLOSE or EXTERNAL_REDUCTION must not be inferred merely from a reduction side or absence of TP/SL metadata. Unknown roles stay UNKNOWN.

`native_side` identifies the affected native position side; `order_side` is the order's execution side. These can differ for a protective reduction. Bind symbol, account/environment/category context, position index and supported native position mode. If one-way semantics cannot prove affected position side, that observation is unresolved; do not assign ownership from Buy/Sell alone.

## 2. Narrow Bybit documentation mapping, not acceptance certification

Official references reviewed on 2026-09-12 are recorded below. The following is an evidence-handling constraint, not proof that a runtime profile can reconstruct every native order.

For order realtime/history records, map `orderId`/`orderLinkId` to order/client IDs; `side` to order_side; `positionIdx` to position_idx; `orderType` to native post-trigger execution type; `stopOrderType`/`createType` to retained native conditional/create types. Preserve conditional trigger price, direction and source, reduction/close flags and TP/SL mode. `createdTime` is a creation timestamp; it is **not** automatically `entry_accepted_at`. [S1]

`parentOrderLinkId` may establish a parent-client relationship for attached derivatives protection, but its documented meaning is conditional on how protection was attached. It is not an exchange parent-order ID or a general TP/SL pair ID. An attachment route for which that relationship is meaningless must return null normalized linkage. `protected_qty` may use native qty only where the pinned mode proves its protected quantity meaning; full-position mode is not an individual tranche quantity. [S1]

A successful trading-stop request is not installed-child evidence. The API can create internal conditional orders, and one-sided modifications can break pairing. Lifecycle must query actual native children and verify them, rather than inventing identifiers from request success. These cautions do not authorize a different execution strategy or protection mode. [S2]

For executions, preserve native execId, execTime, quantity, price and seq. Bybit documents that equal-time transactions can share seq and symbols can reuse it. It is not a universal intra-group total order. A display sorting recommendation using IDs is not adopted as proof of economic chronology. Equal-time unresolved native ties remain reconciliation under P13. [S3]

## 3. Proven acceptance profile

An adapter may emit acceptance status PROVEN only with a pinned endpoint/event+field mapping whose native semantics establish the original accepted/live time for that order (not merely the time of a later status update). It must retain the normalized timestamp and exact provenance. This specification baseline does not certify `createdTime` as such a mapping. With the documented facts alone and no independently verified acceptance mapping, the safe result is `entry_acceptance_status=UNAVAILABLE`, both acceptance fields null, even if the order currently exists or has filled.

The synthetic example profile `SYNTHETIC_ACCEPTANCE_V1` explicitly defines `SYNTHETIC/accepted-events.accepted_at` as original exchange acceptance. It illustrates the complete transport/ledger/cooldown contract and is not a claim that Bybit returns that synthetic field. Native adapter validation must supply authentic evidence or remain unresolved; arbitrary mapping strings do not count as verified provenance.

## 4. Chronology profile

The factual execution row preserves nullable native_sequence, native_sequence_domain, native_subsequence, chronology_profile_version and chronology_provenance. Native_sequence_domain identifies the native stream/scope in which order is meaningful; profile version states the supported ordering rule, not a locally generated sequence. A verified profile can order numeric native sequence values within one domain at equal timestamps. Equal native sequence additionally needs a supported native sub-order. Neither callback counters nor lexical execution IDs are allowed substitutes. Different domains or absent evidence remain unresolved. The synthetic sequence profile has a documented ascending integer sequence and is illustrative only.

## 5. Runtime verification still required

Before enabling a native profile, verify source field meanings, native-side identification, attachment-route linkage, actual protected quantity and semantics, pagination/history across restart, sequence scope, accepted-time provenance, duplicate/alias handling and persistence with real native test artifacts. Unsupported or incomplete proof must exercise reconciliation; it must not be filled in from outbound requests or another tranche's geometry. Native-exchange conformance certification is not provided by this specification baseline.

## Financial settlement-currency conformance

The current accounting baseline permits FINAL only for required monetary source/components already denominated in the tranche's pinned governed accounting/settlement currency (SYSTEM_PROTOCOLS P7.1; `../schemas/NUMERIC_POLICY.md` §2A). Native-profile/runtime verification may establish that the supported venue/account/product supplies fees, rebates, funding and costs in that unit; this document does not certify that guarantee. Contrary factual currency evidence must be retained unchanged and block logical finality, not be filtered out, relabeled, zeroed or converted with market/execution price. Source-sign and allocation provenance remain independent checks. No FX/valuation profile is supplied or authorized here.

## Official sources

[S1] Bybit, Get Open & Closed Orders, response fields and attached TP/SL linkage caveats:
`https://bybit-exchange.github.io/docs/v5/order/open-order`

[S2] Bybit, Set Trading Stop, internal conditional orders and pair-binding caveat:
`https://bybit-exchange.github.io/docs/v5/position/trading-stop`

[S3] Bybit, Get Trade History, executed timestamp and cross-sequence semantics:
`https://bybit-exchange.github.io/docs/v5/order/execution`

## Consumer fact-merge clarification (wire unchanged)

Order Management remains contract v4. Its existing native fields/provenance can express enrichment; no new business decision is delegated to API. Lifecycle distinguishes immutable proven facts, unavailable-to-known enrichment and mutable factual state. Retain per-field authoritative provenance independently of the most recently observed endpoint; whole-row equality is not native consistency. The pinned profile must define mutable status/cumulative-fill/remaining/update ordering and terminal monotonicity. Without that evidence, do not overwrite proven state. The documented synthetic conformance profile uses authoritative updated_at plus nondecreasing cumulative fill and no terminal resurrection; this is a test profile, not certified native exchange behavior.

Acceptance source mappings remain exact and factual. API exposes the original accepted_at evidence, while Lifecycle aggregates contradictions and publishes their separate integrity state in Order Event v7. A known timestamp plus conflicting proof cannot become PROVEN eligibility. See SYSTEM_PROTOCOLS P10. Native deployment must verify mapping semantics, historical linkage recovery and mutable state order empirically.

## Field-evidence clarification

For a mutable field, UNKNOWN/UNAVAILABLE/null or a non-null value lacking authoritative matching field provenance is not a proven earlier value. First proven enrichment is allowed at the same enclosing source timestamp. Persist field-specific proven source version/history so that another field's newer enclosing update cannot retroactively version an absent or unproven field. Compare two conflicting proven facts only within the pinned profile's authoritative ordering. Preserve cumulative-fill regression, terminal resurrection and equal-version contradiction checks. Order Lifecycle's per-field proven version and content histories are private durable ledger metadata, not wire fields or claims of native Bybit profile verification.
