# TriggerTrade — Approve / Reject and Construction Confirmation

**Flow:** `Position Rules → Portfolio Rules`  
**Contract version:** `5`  

## Two-stage meaning on one existing boundary

This boundary first carries the market/trade opportunity decision, then only after an issued grant carries its construction outcome. Follow [P1](../SYSTEM_PROTOCOLS.md#p1--topology-and-approvalconstruction-sequence). These variants do not add a business edge or repeat Set analysis.

Before `OPPORTUNITY_DECISION` is produced, Position pins the exact Position Rules configuration identity/version/content digest to `position_decision_id + decision_cycle_id` as defined by P17 and POSITION_RULES §1B. This binding is durable producer state even though contract v5 does not add a new wire field for it. The `opportunity_checks.configuration` result is evaluated against that pinned configuration, and any later CONSTRUCTION_RESULT for the decision must use the same binding. `OPPORTUNITY_DECISION` is emitted exactly once for the Set-owned cycle. Initial APPROVE means opportunity checks passed; the enabled gross Minimum R:R must pass or be NOT_APPLICABLE when disabled. No capital-dependent result is invented. `construction_gates = NOT_YET_EVALUATED` is a stage marker, not an extra status in the four-valued gate model. Initial REJECT ends the opportunity. Its payload has no grant, plan, tranche, spec or approved economics; strict schemas reject those premature fields.

Only Portfolio creates the post-APPROVE grant. Position binds it to the same initial decision and cycle, calculates the original sizing/leverage/economic formulas, and publishes `CONSTRUCTION_RESULT`. Successful `CONSTRUCTED` contains the immutable final IDs, spec digest and exact approved capital basis. The corresponding Order Spec and confirmation are persisted with outboxes in one transaction. A construction `REJECT` contains failed gates and no successful plan/economics; it creates no hold or authorization. This does not revise the earlier market decision or create another opportunity.

Portfolio books a hold only after CONSTRUCTED, current Portfolio gate/capacity validation, immutable lineage/digest binding and one-time grant consumption. It never books a hold at initial APPROVE. The enabled Minimum Net Edge pairing is true/PASS; disabled is false/NOT_APPLICABLE. FAIL/UNAVAILABLE cannot become CONSTRUCTED or a submit-eligible spec.

## Replay

Position-owned `position_decision_id` identifies the initial decision. `event_id` identifies each durable message. `construction_result_id` identifies the one post-grant outcome. Identical replay is a no-op; changed content under an existing identity fails closed. Portfolio uses cycle/decision identity, not symbol, time, or delivery order, to issue/replay the one grant. No second initial APPROVE is required or allowed.

## Canonical payloads

### APPROVE_REJECT.initial

```yaml
position_decision:
  contract_version: 5
  event_variant: OPPORTUNITY_DECISION
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  decision: APPROVE | REJECT
  reason_code: string
  opportunity_checks:
    configuration: PASS | FAIL | UNAVAILABLE
    set_direction: PASS | FAIL | UNAVAILABLE
    market_context: PASS | FAIL | UNAVAILABLE
    price_geometry: PASS | FAIL | UNAVAILABLE
    minimum_rr: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  construction_gates: NOT_YET_EVALUATED
```

### APPROVE_REJECT.constructed

```yaml
position_construction_result:
  contract_version: 5
  event_variant: CONSTRUCTION_RESULT
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  construction_result_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  reason_code: string
  rule_results:
    minimum_net_edge:
      enabled: boolean
      status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
      configured_value:
        nullable: decimal-string
      calculated_value:
        nullable: decimal-string
      reason_code:
        nullable: string
  outcome: CONSTRUCTED
  position_plan_id: string
  tranche_id: string
  order_spec_id: string
  order_spec_digest: string
  approved_economics:
    approved_entry: decimal-string
    approved_quantity: decimal-string
    approved_leverage: decimal-string
    approved_actual_order_notional: decimal-string
    approved_actual_committed_capital: decimal-string
  numeric_policy_version: TT_NUMERIC_V1
  direction: LONG | SHORT
  order_spec_contract_version: 5
```

### APPROVE_REJECT.failed

```yaml
position_construction_result:
  contract_version: 5
  event_variant: CONSTRUCTION_RESULT
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  construction_result_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  reason_code: string
  rule_results:
    minimum_net_edge:
      enabled: boolean
      status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
      configured_value:
        nullable: decimal-string
      calculated_value:
        nullable: decimal-string
      reason_code:
        nullable: string
  outcome: REJECT
  failed_gates:
  - string
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## F03 / F07 version synchronization

The confirmation is governed by TT_NUMERIC_V1 (`schemas/NUMERIC_POLICY.md`, P11) and exact P14 construction binding. Numeric value selection precedes canonical serialization/digest. All duplicated confirmation scalars and gate outputs equal the immutable spec independently of its digest. Confirmation and authorization explicitly target order_spec_contract_version 5; changed target identity/version/digest is non-submittable. Initial APPROVE still creates no grant or final trade IDs. A definitive no-create terminal authorization remains consumed; replay cannot restore a hold or resume submission. These checks add no business edge or trade-selection rule.
