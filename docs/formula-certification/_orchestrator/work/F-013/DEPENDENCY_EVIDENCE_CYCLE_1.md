# F-013 Dependency Evidence - Cycle 1

## Purpose

This artifact supplies the narrow dependency evidence requested by the first
Full Council review of F-013. It does not change active methodology and does
not authorize implementation.

## N-008 / TT_SET_NUMERIC_V1

Evidence from `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`:

- Policy ID is `TT_SET_NUMERIC_V1`, package revision `v1.2.14`.
- The policy is a technical computation/serialization contract for existing Set
  formulas, timeframes, windows and thresholds. It does not add a signal,
  indicator or fallback.
- Raw decimals are parsed exactly; binary floating point, NaN, infinity and
  context-dependent parsing are forbidden.
- Set fixes one as-of cutoff and persists per-dataset selectors before Market
  Data Request v3 dispatch.
- No incomplete/still-forming candle or candle ending after as-of participates.
- Ambiguous order needed for recursive computation or a missing source interval
  is `UNAVAILABLE` until resolved.
- Working Set arithmetic uses exact integer/rational expressions in written
  formula order and rounds named continuous outputs once to `10^-36` with
  ROUND_HALF_EVEN.
- Clamp, sign and comparisons are applied in existing formula order to
  canonical values without epsilon.
- Boundary values crossing Market Handoff include exact integer counts/ordinals,
  exact direction/bindings/IDs/policy version and canonical decimal strings.
- Acceptance tests must cover exact boundaries, neighboring quanta, restart and
  raw-history replay.

## SYSTEM_PROTOCOLS Evidence Eligibility and Binding

Evidence from `docs/trading-methodology/SYSTEM_PROTOCOLS.md`:

- Set persists fixed per-dataset `selection_id`, as-of, interval, count,
  timeframe and cursor requests on the Market Data Request v3 boundary.
- API supplies requested factual ranges, snapshot/page identity, explicit
  coverage, missing ranges, source finality and pagination manifest; API never
  selects analytical windows.
- A response cannot silently replace a historical range with current data.
- Set reassembles the same immutable selection after restart, deduplicates
  complete pages and requires complete selected coverage before affected data
  become AVAILABLE.
- Any user/configuration-controlled rule set selected for an already-started
  cycle or attempt is immutable for that cycle or attempt.
- Later activation or editing of Set, Trigger/Core Set, Position Rules,
  Portfolio Rules, cooldown, thresholds, sizing parameters or other governed
  settings applies only to a new cycle/attempt.
- Hydration restores the persisted binding itself; it never reconstructs
  historical content from the latest configuration table.
- Set binds each unfinished formation to the selected Set/Trigger/Core Set
  configuration, and a MATCHED cycle retains that exact binding.

## Set Pending-Monitor Identity, Stop and Auditability

Evidence from `docs/trading-methodology/methodology/SET.md`:

- Binding baseline includes frozen original Set result, no silent threshold
  drift, no auto-reprice, no chase, no KEEP signal and `INVALID -> Order Cancel
  Signal`.
- Monitoring starts only after `Order Placed`.
- `Order Placed` must carry the same `decision_cycle_id`.
- Set must not activate monitoring by symbol alone, order timestamp alone or
  latest Set result inference.
- If the correlation key cannot be resolved unambiguously, monitoring activation
  must fail closed and surface an integrity/reconciliation error rather than
  being guessed.
- Monitoring governs only the active unfilled entry remainder associated with
  the matched decision cycle.
- Monitoring stops when authoritative Order Lifecycle state confirms no active
  unfilled entry remainder remains because the entry order is fully filled,
  cancelled, rejected, submission failed or otherwise confirmed terminal.
- For a partially filled entry, filled quantity becomes real exposure governed by
  TP / SL / Manual Close, while the unfilled remainder remains under Set
  pending-order monitoring.
- If Set emits `Order Cancel Signal`, monitoring remains logically pending until
  Order Lifecycle confirms terminal cancel/fill outcome for the unfilled
  remainder.
- Set must not infer terminal order state from market data.
- Pending-order monitoring has conceptual states `MONITORING_INACTIVE`,
  `MONITORING_ACTIVE`, `INVALIDATED`, `MONITORING_STOPPED` and
  `MONITORING_UNAVAILABLE`.
- Runtime auditability must reconstruct the matched decision cycle, activating
  Order Placed event, tranche/order linkage, active frozen invalidation
  predicates, current evaluated market values, invalidation time and emitted
  Order Cancel Signal.

## Order Lifecycle Remainder and Cancellation Handling

Evidence from `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`:

- Set owns pending-order market validity; Order Lifecycle executes cancellation.
- Pending LIMIT entry has no automatic TTL.
- An old pending order may end through fill, Set `Order Cancel Signal`, manual
  cancel, exchange rejection/expiry or operational reconciliation finding a
  terminal exchange state.
- Set market invalidation cancel input includes `decision_cycle_id`,
  `set_result_id`, `tranche_id`, `symbol`, `reason_code` and `invalidated_at`.
- Order Lifecycle does not validate the market reason. It verifies identity and
  current order state, then attempts cancellation of the unfilled remainder
  only.
- Set locates frozen conditions by decision cycle after `Order Placed`.
- Lifecycle terminal events stop/update the pending-order monitor and do not
  change market logic.
- `Order Cancel Signal` cancels only unfilled entry remainder.
- Set invalidation never closes already filled exposure.
- A cancel request does not release anything until exchange terminal truth is
  reconciled.
- Cumulative filled quantity is monotonic and duplicate executions never
  double-count quantity, fees or P/L.
- Terminal lifecycle state must be reconstructable after restart.

## Timestamp and Observation Boundaries

Evidence from Set and numeric policy:

- Monitoring starts only after actual exchange acceptance/placement.
- Semantic validation is event/condition-driven, not arbitrary fixed polling.
- Preferred triggers include new relevant completed bar, reference-level event,
  required market-data event, data-stream health change and reconnect/recovery.
- For Set-derived candle facts, no incomplete/still-forming candle or candle
  ending after the persisted as-of participates.
- Operational timers may exist but are not the semantic validity rule.
