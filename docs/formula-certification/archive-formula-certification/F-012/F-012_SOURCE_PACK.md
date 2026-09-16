# F-012 Source Pack

# F-012 - Risk/Reward and Minimum Net Edge Calculation

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-012 |
| Formula name | Risk/reward and minimum net edge calculation |
| Owner | Position Rules |
| Formula family | RISK_REWARD |
| Certification phase | Source Pack |
| Active methodology baseline | v1.2.14 |
| Source Pack status | Immutable pre-review provenance |

F-012 evaluates final Position eligibility from certified Entry, Stop, Take
Profit, final quantity/notional, fee facts and configured thresholds. It covers
gross structural Risk / Reward and planned Minimum Net Edge.

## 2. Source Index

| Source | Evidence |
|---|---|
| `docs/FORMULA_METRICS_CATALOG.md` | Catalog row marks F-012 certification-required; dependencies include F-008, F-009, F-010, A-003 and T-010. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 749-790 | Gross risk distance, reward distance and gross R:R comparator. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 794-835 | Gross TP/SL scenario P/L formulas using final quantity. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 838-917 | Fee facts and planned entry/TP/SL fee formulas. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 920-944 | Funding exclusion from planned Minimum Net Edge. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 948-1009 | TP total cost, net TP profit and planned Minimum Net Edge formula/gate. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1035-1054 | Planned SL cost/economics and diagnostic net R:R. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1058-1107 | Minimum R:R and Minimum Net Edge hard-gate behavior. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1135-1145 | After rounding, geometry, gross R:R and Minimum Net Edge are recomputed/revalidated; rule-result shape starts here. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1394-1465 | Successful and failed construction result payloads with minimum net edge rule result. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1554-1576 | Configuration validation examples: enabled minimum RR/net edge value missing is `CONFIG_INVALID`. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 4660-4675 | Canonical invariants for gross R:R, Minimum Net Edge and funding exclusion. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 4725-4739 | Gate serialization and exact construction equality. |
| `docs/trading-methodology/schemas/NUMERIC_POLICY.md` lines 16-27, 53-61, 82-88 | Exact arithmetic, exact finite monetary values, ratio report quantization, exact gate comparisons and canonical serialization. |
| `docs/trading-methodology/business-contracts/ORDER_SPEC.md` | Order Spec economics fields and `funding_in_planned_net_edge = false`. |
| `docs/trading-methodology/business-contracts/APPROVE_REJECT.md` | Construction result `minimum_net_edge` rule result and approved economics. |
| `docs/formula-certification/F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | Certified Entry source. |
| `docs/formula-certification/F-009/F-009_FINAL_FORMULA_SPECIFICATION.md` | Certified Stop source. |
| `docs/formula-certification/F-010/F-010_FINAL_FORMULA_SPECIFICATION.md` | Certified Take Profit source. |
| `docs/formula-certification/F-011/F-011_FINAL_FORMULA_SPECIFICATION.md` | Certified final quantity, actual order notional and actual committed capital source. |

## 3. Purpose and Trading Context

F-012 answers:

```text
Given final Entry, Stop, Take Profit, final quantity, actual order notional,
governed fee facts and configured thresholds, does the constructed Position
pass gross structural Risk / Reward and enabled planned Minimum Net Edge gates?
```

Trading role:

- ensure reward distance is sufficient relative to risk distance;
- estimate planned TP-side net profit after deterministic entry and TP fees;
- evaluate enabled minimum net edge against actual order notional;
- record final construction economics in the Order Spec and construction
  confirmation;
- reject construction when configured gates fail or required economic facts are
  unavailable.

F-012 does not size the position, calculate Entry/SL/TP, approve Portfolio
capital, authorize submission, model funding, guarantee fills or prove
profitability.

## 4. Exact Formula If Available

### 4.1 Structural distances

```text
risk_distance_price = abs(Entry - SL)
risk_distance_pct = 100 * risk_distance_price / Entry

reward_distance_price = abs(TP - Entry)
reward_distance_pct = 100 * reward_distance_price / Entry
```

### 4.2 Gross Risk / Reward

```text
gross_rr = reward_distance_price / risk_distance_price
```

The explicit user Minimum Risk / Reward rule uses `gross_rr`. Equivalent
monetary ratio may be logged, but is not the comparator.

### 4.3 Gross TP scenario P/L

Let:

```text
Q = final_qty
```

LONG:

```text
gross_profit_tp = (TP - Entry) * Q
```

SHORT:

```text
gross_profit_tp = (Entry - TP) * Q
```

### 4.4 Gross SL scenario P/L

Positive loss magnitude.

LONG:

```text
gross_loss_sl = (Entry - SL) * Q
```

SHORT:

```text
gross_loss_sl = (SL - Entry) * Q
```

### 4.5 Planned fees

Entry baseline is LIMIT + POST_ONLY, so:

```text
expected_entry_fee = actual_order_notional * maker_fee_rate
```

TP exit baseline is MARKET, so:

```text
tp_exit_notional = TP * final_qty
expected_tp_exit_fee = tp_exit_notional * taker_fee_rate
```

SL exit baseline is MARKET, so:

```text
sl_exit_notional = SL * final_qty
expected_sl_exit_fee = sl_exit_notional * taker_fee_rate
```

### 4.6 Planned TP costs and net profit

```text
tp_total_cost =
  expected_entry_fee
  + expected_tp_exit_fee
  + other_exchange_costs_if_deterministic

net_profit_tp =
  gross_profit_tp
  - tp_total_cost
```

Credits must preserve sign.

### 4.7 Planned Minimum Net Edge

```text
net_edge_pct =
  100 * net_profit_tp / actual_order_notional
```

Hard gate:

```text
net_edge_pct >= configured_minimum_net_edge_pct
```

Failure:

```text
NET_EDGE_BELOW_MINIMUM
```

Funding is excluded:

```text
funding_in_planned_net_edge = false
```

### 4.8 Net R:R diagnostic

```text
net_rr = net_profit_tp / net_loss_sl
```

The source says this is diagnostic only and is not the comparator for user
Minimum Risk / Reward.

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `Entry` | Certified F-008 | Positive final Entry for same decision cycle. |
| `SL` | Certified F-009 | Positive final Stop for same direction/cycle. |
| `TP` | Certified F-010 | Positive final Take Profit for same direction/cycle. |
| `Q` / `final_qty` | Certified F-011 | Positive final quantity. |
| `actual_order_notional` | Certified F-011 | Positive actual order notional `Q * Entry`. |
| `direction` | Market Handoff / Position | Immutable `LONG` or `SHORT`. |
| `maker_fee_rate` | Capital and Limits fee facts / A-003 policy | Governed exact fee fact; not invented or fetched by Position. |
| `taker_fee_rate` | Capital and Limits fee facts / A-003 policy | Governed exact fee fact; not invented or fetched by Position. |
| `fee_schedule_version`, `fee_effective_at`, `fee_rate_source_ref` | Capital and Limits | Fee provenance for replay/audit. |
| `configured_minimum_rr` | Position configuration / T-005 | Required if Minimum R:R is enabled. |
| Minimum R:R enabled flag | Position configuration | Determines PASS/FAIL/NOT_APPLICABLE handling. |
| `configured_minimum_net_edge_pct` | Position configuration / T-006 | Required if Minimum Net Edge is enabled. |
| Minimum Net Edge enabled flag | Position configuration | Disabled gate is NOT_APPLICABLE, not fabricated PASS. |
| deterministic other exchange costs | Active approved policy if any / T-010 | Included only if deterministic and approved for planned order mechanics. |

## 6. Outputs

Primary outputs:

```text
risk_distance_price
risk_distance_pct
reward_distance_price
reward_distance_pct
gross_rr
gross_profit_tp
gross_loss_sl
expected_entry_fee
tp_exit_notional
expected_tp_exit_fee
sl_exit_notional
expected_sl_exit_fee
tp_total_cost
net_profit_tp
net_edge_pct
minimum_rr_result
minimum_net_edge_result
funding_in_planned_net_edge = false
```

Order Spec economics:

```yaml
economics:
  gross_rr: decimal-string
  planned_net_edge_pct: decimal-string
  minimum_net_edge_enabled: boolean
  minimum_net_edge_result: PASS | NOT_APPLICABLE
  maker_fee_rate: decimal-string
  taker_fee_rate: decimal-string
  fee_schedule_version: string
  fee_rate_source_ref: string
  funding_in_planned_net_edge: false
```

Construction result:

```yaml
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
```

Successful constructed specs accept only:

```text
minimum_net_edge_enabled = true  with minimum_net_edge_result = PASS
minimum_net_edge_enabled = false with minimum_net_edge_result = NOT_APPLICABLE
```

## 7. Units

| Item | Unit |
|---|---|
| Entry, SL, TP, distances | Instrument quote price units |
| `Q` / final quantity | Base contract/coin quantity units |
| gross profit/loss, fees, costs, actual order notional | Governed quote/settlement monetary unit |
| `gross_rr`, `net_rr` | Dimensionless ratios |
| `risk_distance_pct`, `reward_distance_pct`, `net_edge_pct`, configured thresholds | Percent units; numeric `1` means one percent |
| fee rates | Decimal fraction unless active fee contract states otherwise |

## 8. Parameters

| Parameter | Class | Notes |
|---|---|---|
| Minimum Risk / Reward enabled flag and threshold | `RESEARCH_PARAMETER` / T-005 | Gate semantics need certification; threshold value remains configurable/research-governed. |
| Minimum Net Edge enabled flag and threshold | `RESEARCH_PARAMETER` / T-006 | Gate semantics need certification; threshold value remains configurable/research-governed. |
| Maker/taker fee rates | A-003 / fee facts | Factual fee inputs supplied through upstream contracts. |
| Other deterministic exchange costs | T-010 / research or approved policy | Source only allows deterministic costs; no arbitrary spread/slippage/funding assumption in planned net edge. |

## 9. Thresholds

Extracted comparisons:

```text
gross_rr >= configured_minimum_rr
net_edge_pct >= configured_minimum_net_edge_pct
```

Both are inclusive when enabled. Enabled gate with missing configured threshold
is `CONFIG_INVALID`. Disabled Minimum Net Edge is `NOT_APPLICABLE`, never
fabricated `PASS`.

## 10. Sign and Direction Semantics

Direction is immutable and must not be re-inferred.

Gross TP profit:

```text
LONG:  (TP - Entry) * Q
SHORT: (Entry - TP) * Q
```

Gross SL loss magnitude:

```text
LONG:  (Entry - SL) * Q
SHORT: (SL - Entry) * Q
```

Costs and credits preserve sign. Funding is excluded from planned Minimum Net
Edge.

## 11. Domain and Preconditions

F-012 can evaluate when:

1. F-008 Entry, F-009 Stop, F-010 Take Profit and F-011 sizing are certified,
   available and identity-matched for the same cycle.
2. Entry, SL, TP, final quantity and actual order notional are positive finite
   exact values.
3. Direction is LONG or SHORT.
4. Gross risk distance is positive.
5. Fee facts required for enabled Minimum Net Edge are available with provenance.
6. Enabled thresholds have configured exact values.
7. Position configuration identity/version/content digest is pinned.

Missing values are not guessed, zero-filled or replaced by research
assumptions.

## 12. Boundaries

F-012 includes:

```text
gross risk distance
gross reward distance
gross R:R comparator
gross TP profit
gross SL loss magnitude
planned deterministic entry and TP fees
planned TP total cost
net TP profit
planned net edge percent
minimum RR and minimum net edge gate results
Order Spec economics fields
construction result minimum_net_edge rule result
```

F-012 excludes:

```text
Entry, Stop or Take Profit selection
position sizing / quantity construction
Portfolio grant / hold / authorization
Order Lifecycle execution and fills
funding prediction in planned net edge
liquidation, maintenance margin or maximum-loss modeling
spread/slippage assumptions unless separately approved as deterministic planned costs
realized PnL accounting
fee cashflow attribution implementation
```

## 13. Precision

`TT_NUMERIC_V1` applies:

- exact decimal parsing and exact arithmetic;
- exact finite monetary products/sums retain all digits;
- ratios/percentages serialize at `Qratio = 0.000000000000000001` by flooring
  the exact rational for report fields only;
- all gate decisions use exact pre-report values;
- display formatting cannot affect a gate, grant or spec;
- no binary floats, finite-precision intermediate rounding or epsilon
  comparisons.

## 14. Time Semantics

F-012 uses the same immutable construction cycle and pinned Position
configuration. It uses governed fee facts supplied through upstream contracts
and does not fetch fees directly. Funding events that occur after opening are
realized downstream; they are not part of planned Minimum Net Edge.

## 15. State, Replay and Restart

Replay/restart must preserve:

```text
decision_cycle_id
set_result_id
position_decision_id
capital_grant_id
construction_result_id
position_plan_id
tranche_id
direction
certified F-008 Entry identity/value
certified F-009 Stop identity/value
certified F-010 TP identity/value
certified F-011 sizing identity/quantity/notional values
Position configuration identity/version/content digest
Minimum RR enabled flag and threshold
Minimum Net Edge enabled flag and threshold
fee facts and provenance
numeric_policy_version = TT_NUMERIC_V1
computed exact pre-report ratios and monetary values
serialized economics fields
rule result statuses/reasons
Order Spec digest and construction confirmation bindings
```

Changed content under an existing identity fails closed. Replay must reproduce
the same gates and no failed gate may be repaired by changing Entry, SL, TP,
leverage, quantity or capital.

## 16. Version and Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
Capital and Limits contract_version = 5
Order Spec contract_version = 5
Approve/Reject contract_version = 5
TT_NUMERIC_V1
Position Rules configuration identity/version/content digest
certified F-008 final specification
certified F-009 final specification
certified F-010 final specification
certified F-011 final specification
```

## 17. Ownership

Position Rules owns F-012 planned risk/reward and net-edge gate evaluation.
Portfolio Rules owns capital grant/hold/authorization. API/Portfolio-supplied
facts own fee facts and provenance. Order Lifecycle owns execution, fills,
cashflows and realized accounting. Accounting owns realized fee cashflow
calculation/attribution under A-003; F-012 consumes fee facts for planned
pre-trade economics only.

## 18. Downstream Consumers

F-012 feeds:

- final Position construction eligibility;
- Order Spec economics fields;
- construction confirmation `minimum_net_edge` rule result;
- Portfolio hold/authorization eligibility through successful `CONSTRUCTED`;
- research diagnostics and post-trade evaluation.

## 19. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | `CERTIFIED_FORMULA` | Entry price. |
| F-009 | `CERTIFIED_FORMULA` | Stop price. |
| F-010 | `CERTIFIED_FORMULA` | Take Profit price. |
| F-011 | `CERTIFIED_FORMULA` | Final quantity and actual order notional. |
| A-003 | `APPROVED_POLICY` | Fee cashflow/factual fee basis; implementation not certified here. |
| T-005 | `RESEARCH_PARAMETER` | Minimum R:R threshold. |
| T-006 | `RESEARCH_PARAMETER` | Minimum Net Edge threshold. |
| T-010 | `RESEARCH_PARAMETER` | Fee/spread/slippage/funding assumptions; planned F-012 excludes non-deterministic funding and arbitrary assumptions. |
| TT_NUMERIC_V1 | `APPROVED_POLICY` | Exact arithmetic and ratio report quantization. |
| Capital and Limits v5 | `DOCUMENTATION_DEPENDENCY` | Fee facts and provenance. |
| Order Spec v5 | `DOCUMENTATION_DEPENDENCY` | Economics output fields. |
| Approve/Reject v5 | `DOCUMENTATION_DEPENDENCY` | Construction result rule-result output. |

## 20. Existing Worked Examples

No complete worked F-012 example was found in the extracted sources.

The methodology provides formula definitions but no numeric example covering
Entry, SL, TP, quantity, actual notional, maker/taker rates, enabled thresholds
and resulting gate statuses.

## 21. Explicit Source Gaps and Review Questions

Source gaps for Full Council review:

1. The source text in Section 39 appears to say "If enabled" then gives the
   pass comparison, but the following "Else" block returns `RR_BELOW_MINIMUM`.
   Council should confirm intended enabled/disabled/fail mapping for Minimum
   R:R.
2. The Source Pack found no explicit rule-result output field for Minimum R:R in
   final construction payloads, while methodology says initial opportunity
   checks include `minimum_rr`. Council should define whether F-012 final spec
   owns only the formula/gate semantics or also any output field beyond
   construction confirmation's Minimum Net Edge result.
3. `other_exchange_costs_if_deterministic` is named but not enumerated. Council
   should define whether only entry and TP fees are included for the current
   baseline absent a separate approved deterministic cost.
4. The formulas define `expected_sl_exit_fee`, `sl_total_cost`, `net_loss_sl`
   and `net_rr` diagnostic, but the extracted lines include only partial context
   for SL total cost. Council should decide whether these are required outputs,
   diagnostics, or out-of-scope for the hard gates.
5. Failure-code precedence is incomplete for invalid geometry, zero
   risk-distance denominator, missing fee facts, invalid fee facts, disabled
   gates, unavailable dependencies and negative/zero net edge.
6. The catalog dependency list omits F-011, but F-012 requires final quantity
   and actual order notional; the dependency graph has been updated to include
   certified F-011.
7. A-003 is `APPROVED_AS_DEFINED` in the catalog, not a certified final formula
   in the formula-certification tree. Council should decide whether this is
   sufficient as approved policy/factual fee basis for planned F-012.

## 22. Reviewer Handoff Summary

F-012 has explicit source formulas for gross price-distance R:R and planned TP
net edge:

```text
gross_rr = abs(TP - Entry) / abs(Entry - SL)
net_edge_pct = 100 * ((directional TP profit) - deterministic planned TP costs) / actual_order_notional
```

The review should:

- certify exact mathematical semantics and denominator validity;
- separate gross structural R:R from net-edge economics;
- define complete gate behavior and failure mapping;
- preserve funding exclusion from planned Minimum Net Edge;
- preserve certified F-008/F-009/F-010/F-011 boundaries;
- decide whether A-003 approved policy/factual fee basis is sufficient;
- avoid introducing slippage/spread/funding assumptions unless already
  approved as deterministic planned costs.
