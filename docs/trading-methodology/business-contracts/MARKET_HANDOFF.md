# TriggerTrade — Market Handoff

**Flow:** `Set → Position Rules`  
**Contract version:** `4`  

## Producer and reference provenance

Set creates `decision_cycle_id` and `set_result_id` for a concrete MATCHED Core Set, before Position's decision. Direction is immutable LONG/SHORT. The message includes no capital/grant and no Frozen Condition.

Follow [P4](../SYSTEM_PROTOCOLS.md#p4--exact-producer-bound-thesis-references). Every non-null thesis reference has a concrete level ID and `origin_binding` identifying the exact configured role, Core Set, constituent, Trigger version/occurrence and reference key that produced it. Set persists this binding at MATCHED. All role/indicator/timeframe/level choices are inherited from that originating configuration and matched structure; there is no post-match ranking among same-type levels.

REQUIRED: one exact bound reference must exist in `reference_geometry.levels`, be uniquely identified and available at match; otherwise no valid handoff is emitted. PREFERRED: retain the exact configured binding when available, or null only under the existing approved fallback semantics. Nonunique/conflicting bindings are errors, not a heuristic fallback. NONE: both thesis ID and origin binding are null.

Position validates/consumes, never selects a replacement thesis. Existing PREFERRED/NONE calculation-candidate hierarchies remain distinct from producer thesis binding. A candidate selected by such a fallback does not rewrite `thesis_reference_level_id` or origin_binding. REQUIRED has no fallback. Level IDs are unique in the frozen array; a bound timeframe/type/price must agree with the actual originating reference evidence.

For event-dependent formation, the producer must satisfy the in-package Trigger contract in `../methodology/SET.md`, Part I §§10–12 and §17: an authoritative same-epoch FALSE -> TRUE only, no bridge across UNAVAILABLE, authoritative TRUE evaluation time and durable once-only event consumption. These remain Set-local formation records. The existing MATCHED occurrence/reference bindings and handoff schema are unchanged; Position consumes the frozen result rather than reconstructing Trigger events.

## Canonical integer age

`age_seconds` is the ceiling of the exact nonnegative timestamp delta: `ceil(market_snapshot_at - available_at)` measured in seconds. Timestamps themselves remain exact. Therefore `60.000000 -> 60`, `60.000001 -> 61`, and `60.750000 -> 61`. This clarification does not change Market Handoff contract version 4 or the integer schema shape.

## Frozen Condition and monitor lifecycle

Frozen Condition remains in Set's persisted record keyed by this exact cycle. Lifecycle later emits Order Placed/terminal synchronization over the existing boundary. Set uses that cycle only, never latest/nearest cycle matching. Persisted terminal tombstones prevent a delayed placement from reactivating monitoring. The three Position contexts are calculation inputs, not a transfer of pending-order invalidation ownership.

## Canonical payloads

### MARKET_HANDOFF

```yaml
market_handoff:
  contract_version: 4
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  created_at: RFC3339-timestamp
  set_provenance:
    set_id: string
    set_version: string
    core_set_id: string
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
  snapshot:
    matched_at: RFC3339-timestamp
    market_snapshot_at: RFC3339-timestamp
    market_snapshot_id: string
    direction: LONG | SHORT
    set_match_reference_price: decimal-string
    reference_price_basis: LAST_TRADED_PRICE
    reference_price_observed_at: RFC3339-timestamp
    reference_price_source: string
  instrument:
    tick_size: decimal-string
    metadata_revision: string
    metadata_as_of: RFC3339-timestamp
  volatility:
    atr_15m: decimal-string
    atr_pct_15m: decimal-string
  reference_geometry:
    levels:
    - level_id: string
      level_type: string
      price: decimal-string
      timeframe: string
      formed_at:
        nullable: RFC3339-timestamp
      confirmed_at:
        nullable: RFC3339-timestamp
      available_at: RFC3339-timestamp
      source_metric:
        nullable: string
      age_seconds: nonnegative-integer  # ceil(market_snapshot_at - available_at) in exact seconds
      relative_position: BELOW_REFERENCE | AT_REFERENCE | ABOVE_REFERENCE
  entry_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  sl_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  tp_context:
    set_family: TREND_CONTINUATION | RANGE | BREAKOUT_RECLAIM | GENERIC
    thesis_reference_policy: REQUIRED | PREFERRED | NONE
    thesis_reference_level_id:
      nullable: string
    origin_binding:
      nullable:
        binding_id: string
        role_id: string
        core_set_id: string
        core_set_constituent_id: string
        trigger_id: string
        trigger_version: string
        trigger_occurrence_id: string
        reference_key: string
        indicator_id:
          nullable: string
        timeframe: string
        level_id: string
  set_numeric_policy_version: TT_SET_NUMERIC_V1
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

