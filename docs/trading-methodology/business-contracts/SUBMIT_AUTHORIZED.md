# TriggerTrade — Submit Authorized / Order Submit

**Flow:** `Portfolio Rules → Order Lifecycle`  
**Contract version:** `5`  

## Authorization meaning

Order Submit is the short diagram label for this same message, not another flow. It means Portfolio atomically validated current Portfolio health/gates/capacity, consumed the exact approved grant/construction binding and booked `SUBMISSION_HOLD`. It cannot be emitted on initial opportunity APPROVE or before post-grant construction.

`held_committed_capital` equals the canonical constructed `actual_committed_capital` in both the confirmation and immutable Order Spec. It must not exceed `requested_capital_per_tranche` (the grant bound). Portfolio atomically revalidates current gates and books this exact amount plus one slot; unused grant capacity remains free immediately. A grant-bound violation produces no hold/authorization and no silent resize.

Lifecycle requires matching spec and authorization across every shared identity, symbol and exact spec digest. Either may arrive first. A missing counterpart causes durable waiting, not execution, time expiry or an assumed failure. A conflicting counterpart is an integrity failure. Lifecycle records its native create intent before any API side effect and reconciles ambiguity instead of blind retry.

Identical replay reuses authorization and creates no extra hold or create. A local hold cannot be erased because no native order is visible. Technical failure releases it only after definitive no-create/no-exposure proof. Current hard non-market compatibility is Lifecycle-owned; this authorization is not a prediction of exchange POST_ONLY acceptance.

## Canonical payloads

### SUBMIT_AUTHORIZED

```yaml
submit_authorized:
  contract_version: 5
  authorization_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  position_decision_id: string
  construction_result_id: string
  position_plan_id: string
  tranche_id: string
  order_spec_id: string
  symbol: string
  order_spec_digest: string
  held_committed_capital: decimal-string
  authorized_at: RFC3339-timestamp
  numeric_policy_version: TT_NUMERIC_V1
  order_spec_contract_version: 5
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## F03 / F07 version synchronization

The authorization is governed by TT_NUMERIC_V1 (`schemas/NUMERIC_POLICY.md`, P11) and exact P14 construction binding. Numeric value selection precedes canonical serialization/digest. All duplicated confirmation scalars and gate outputs equal the immutable spec independently of its digest. Confirmation and authorization explicitly target order_spec_contract_version 5; changed target identity/version/digest is non-submittable. Initial APPROVE still creates no grant or final trade IDs. A definitive no-create terminal authorization remains consumed; replay cannot restore a hold or resume submission. These checks add no business edge or trade-selection rule.
