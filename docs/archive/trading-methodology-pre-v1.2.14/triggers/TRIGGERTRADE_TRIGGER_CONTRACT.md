# TriggerTrade Trigger Contract

**Document ID:** TT-METH-003
**Version:** 0.3.0
**Status:** REVIEWED BASELINE
**Scope:** Canonical representation and evaluation rules for TriggerTrade triggers built directly from metrics, references, and explicit comparison rules
**Dependencies:**
- `BYBIT_RAW_DATA_CATALOG` accepted baseline
- `TRIGGERTRADE_DERIVED_METRICS_CATALOG` reviewed baseline

---

## Review decision

The Trigger Contract architecture is accepted as the correct bridge between the Metrics Catalog and future trading hypotheses.

No separate mandatory `Market State` layer is required.

This baseline defines syntax and evaluation semantics only. It does not validate any threshold, timeframe, setup, trigger, or edge.

---

## 1. Purpose

This document defines the canonical TriggerTrade **Trigger Contract**.

A trigger is the smallest deterministic, evaluable market rule built directly from one or more metric/reference operands plus explicit parameters and comparison logic.

A trigger answers:

> Is this precisely defined market rule satisfied now?

Examples:

```text
OI_CHANGE_PCT(horizon=15m) >= 0.03
```

```text
EMA(window=20, input_timeframe=5m)
crosses_above
EMA(window=50, input_timeframe=5m)
```

```text
ATR_PCT(
    input_timeframe=5m,
    window=14,
    normalization=percentile,
    baseline=30d
) >= 80
```

TriggerTrade deliberately does **not** insert a mandatory `Condition` or `Market State` layer between metrics and triggers.

The canonical methodology chain is:

```text
Raw Data
    ↓
Derived Metrics
    ↓
Triggers
    ↓
Sets
    ↓
Research
    ↓
Trading Rule Sets
```

A trigger is not a proven edge and is not a trade by itself. It is a precisely defined evaluable building block that may later be combined with other triggers inside a Set.

---

## 2. Core definition

The basic TriggerTrade trigger has the form:

```text
LEFT_OPERAND
    OPERATOR
RIGHT_OPERAND
```

Example:

```text
OI_CHANGE_PCT(horizon=15m) >= 0.03
```

The left operand is normally a fully parameterized metric instance.

The right operand may be:

1. a fixed scalar value;
2. another metric instance;
3. an approved deterministic reference level.

Timeframe, horizon, window, anchor, normalization, baseline, persistence, and evaluation semantics are part of trigger identity whenever applicable.

---

## 3. Trigger versus metric

A metric answers:

> What is the measured value?

Example:

```text
OI_CHANGE_PCT(horizon=15m) = 0.042
```

A trigger answers:

> Does that measured value satisfy the explicitly defined rule?

Example:

```text
OI_CHANGE_PCT(horizon=15m) >= 0.03
→ TRUE
```

The threshold is not part of the metric definition.

It belongs to the trigger definition.

---

## 4. Trigger versus Set

A trigger is one evaluable rule.

A **Set** is a higher-level structure that combines multiple triggers and may add Boolean and temporal relationships between them.

Examples of Set-level relationships that are intentionally outside this Trigger Contract:

```text
TRIGGER_A AND TRIGGER_B
```

```text
TRIGGER_A OR TRIGGER_B
```

```text
TRIGGER_A THEN TRIGGER_B WITHIN 10m
```

```text
TRIGGER_A
THEN TRIGGER_B
WHILE TRIGGER_C remains TRUE
```

```text
RESET if TRIGGER_D fires
```

The Set Contract will define how such trigger combinations, sequences, windows, persistence relationships, expiry, and reset semantics work.

The Trigger Contract defines only the individual trigger building blocks.

---

# 5. Canonical trigger schema

Every trigger must be representable using the following logical fields.

## 5.1 Required fields

### `trigger_id`

Stable identifier inside a research specification or Trading Rule Set.

Example:

```text
TRG-001
```

### `left`

The primary operand.

Normally a fully parameterized metric instance.

Example:

```text
metric: OI_CHANGE_PCT
parameters:
  horizon: 15m
```

### `operator`

The comparison or event operator.

Example:

```text
>=
```

### `right`

The comparison operand.

It may be a scalar value, metric instance, or reference level.

Example:

```text
value: 3.0
unit: percent
```

---

## 5.2 Recommended fields

### `evaluation`

Defines when the trigger may be evaluated and is semantically material.

It must specify an evaluation cadence or event and the data-completion rule.

Examples:

- on every completed 1m bar;
- on every completed 5m bar;
- on every qualifying trade event;
- once per setup evaluation cycle.

Unless a trigger explicitly uses event-time data, bar-based triggers use **completed observations only**.

### `persistence`

Optional rule specifying how long or how consistently the base comparison must hold.

### `availability_policy`

Defines what happens when required data is unavailable.

Canonical default:

```text
UNAVAILABLE → trigger does not evaluate true
```

Missing data must never be silently treated as zero.

### `notes`

Human-readable explanation of why the trigger exists in the research hypothesis or TRS.

---

# 6. Operand types

## 6.1 Metric operand

A metric plus all parameters needed to identify a concrete instance.

Example:

```text
ATR_PCT(
    input_timeframe=5m,
    window=14,
    smoothing=wilder
)
```

## 6.2 Scalar operand

A fixed numerical or categorical comparison value.

Examples:

```text
3.0%
```

```text
80th percentile
```

```text
0
```

Thresholds must be explicit and versioned with the hypothesis/TRS that uses them.

## 6.3 Metric-to-metric operand

Two metric instances may be compared directly.

Example:

```text
RETURN(horizon=5m) > RETURN(horizon=1h)
```

This comparison is syntactically valid, but economic meaning must be justified because differently scaled horizons may not be directly comparable.

A more meaningful example:

```text
EMA(window=20, input_timeframe=5m)
>
EMA(window=50, input_timeframe=5m)
```

## 6.4 Reference-level operand

A trigger may compare a metric or current price to a deterministic reference level.

Examples:

```text
PRICE > PREVIOUS_DAY_HIGH
```

```text
DISTANCE_TO_LEVEL(level_type=range_high) <= 0.20 ATR
```

The referenced level must itself have a deterministic, non-look-ahead definition.

## 6.5 Raw observable operands

The preferred dependency path is:

```text
raw data → canonical metric → trigger
```

A trigger should therefore reference a canonical metric whenever an equivalent metric exists.

A normalized raw observable may be used directly only when it represents a primitive market value for which creating a derived metric would add no information, for example the current tradable price used against a deterministic reference level.

Such operands must use an approved canonical observable name from the data contract. Free-form aliases such as `PRICE` are not permitted in governed artifacts unless that name is defined in the data/metrics vocabulary.

---

# 7. Unit semantics

Scalar thresholds must use the canonical unit of the metric definition.

Examples of values that are mathematically similar but **not interchangeable without an explicit unit contract**:

```text
0.03
3%
3 percentage points
```

For every scalar comparison:

- the metric's canonical output unit must be known;
- the right-hand scalar must declare or inherit exactly that unit;
- implementations must not guess whether a percentage is represented as `0.03` or `3.0`;
- research, backtest, paper, and live evaluation must use the same representation.

If the Metrics Catalog defines a metric as a decimal fraction, `3%` must be serialized as `0.03`.
If it defines percentage points, the serialized value must follow that definition.

Unit conversion may occur only through an explicit normalization/conversion rule, never implicitly inside the trigger engine.

---

# 8. Approved operator families

## 7.1 Scalar comparison operators

```text
>
>=
<
<=
==
!=
```

Use for ordinary threshold rules.

Example:

```text
OI_CHANGE_PCT(horizon=15m) >= 3.0%
```

---

## 7.2 Range operators

```text
between
outside
```

Example:

```text
RSI(window=14, input_timeframe=5m)
between [60, 75]
```

Boundary inclusion/exclusion must be explicit.

Canonical preferred representation:

```text
>= 60
AND
<= 75
```

when exact boundary semantics matter.

---

## 7.3 Crossing operators

```text
crosses_above
crosses_below
```

`crosses_above(A, B)` is true only when:

```text
A_(t-1) <= B_(t-1)
AND
A_t > B_t
```

`crosses_below(A, B)` is true only when:

```text
A_(t-1) >= B_(t-1)
AND
A_t < B_t
```

The evaluation timestamps for `t-1` and `t` must be explicit.

Example:

```text
EMA(20, 5m) crosses_above EMA(50, 5m)
```

---

## 7.4 Change / relative-change operators

Where possible, changes should use a canonical metric such as `RETURN` or `OI_CHANGE_PCT` rather than inventing a new trigger operator.

Preferred:

```text
OI_CHANGE_PCT(horizon=15m) >= 3%
```

Not preferred:

```text
OI increased by at least 3%
```

The metric catalog remains the source of formula definitions.

---

## 7.5 Reference breach operators

Price/reference interactions may be represented as crossing triggers.

Example:

```text
LAST_TRADED_PRICE crosses_above RANGE_HIGH
```

A simple:

```text
PRICE > RANGE_HIGH
```

means only that price is currently above the level.

It does **not** prove that a breakout occurred at the current evaluation timestamp.

This distinction must remain explicit.

---

# 9. Persistence and temporal qualification

A trigger may need more than a single instantaneous observation.

Persistence is part of the trigger, not a new metric.

Persistence does not create independent observations. If a rolling 15m metric is evaluated every 5m, consecutive evaluations overlap heavily. Research must account for this dependence and must not interpret three overlapping evaluations as three independent confirmations.

## 8.1 Consecutive observations

Example:

```text
OI_CHANGE_PCT(15m) >= 3%
for 3 consecutive completed 5m evaluations
```

Canonical fields:

```text
persistence:
  mode: consecutive
  observations: 3
  evaluation_interval: 5m
```

## 8.2 Duration

Example:

```text
PRICE > VWAP
for at least 10 minutes
```

Canonical fields:

```text
persistence:
  mode: duration
  duration: 10m
```

## 8.3 Count within lookback

Example:

```text
trigger true at least 4 times
within the last 6 evaluations
```

This may be used later when research demonstrates a reason for it.

It must not be introduced merely to optimize a backtest.

---

# 10. Multi-timeframe triggers

Multi-timeframe evaluation is a first-class requirement of TriggerTrade.

All operands in one evaluation must be aligned using **as-of semantics**:

> At evaluation timestamp `T`, each operand uses the latest value that was fully available at or before `T`.

A 1h metric must therefore never use the still-forming 1h candle merely because a 5m trigger is being evaluated inside that hour.

The same metric may be instantiated on several horizons or timeframes inside the same setup or trigger.

Example:

```text
RETURN(horizon=1h) > 0
AND
RETURN(horizon=15m) > 0
AND
RETURN(horizon=5m) < 0
```

This could describe:

- positive larger context;
- positive intermediate context;
- short-term pullback.

It does not automatically imply a profitable setup.

Another example:

```text
OI_CHANGE_PCT(horizon=1h) > 5%
AND
OI_CHANGE_PCT(horizon=5m) < 0
```

This expresses a relationship between longer-term position expansion and recent position contraction.

The Trigger Contract must therefore preserve every metric's complete temporal key.

---

# 11. Normalized triggers

A trigger may use an approved normalization mode from the Metrics Catalog.

Example:

```text
ATR_PCT(
    timeframe=5m,
    window=14,
    normalization=percentile,
    baseline=30d
) >= 80
```

This means the current ATR% lies at or above the 80th percentile relative to the declared baseline.

The baseline definition is part of the trigger and must never be implicit.

Possible baseline parameters include:

- lookback length;
- same-symbol history;
- time-of-day triggering;
- rolling versus expanding baseline.

No percentile or z-score threshold is treated as an edge without validation.

---

# 12. Composite Boolean expressions

Triggers may be combined using Boolean logic.

Approved logical operators:

```text
AND
OR
NOT
```

Example:

```text
TRG-001
AND
TRG-002
AND
TRG-003
```

Complex expressions must preserve grouping explicitly.

Example:

```text
TRG-001
AND
(
    TRG-002
    OR
    TRG-003
)
```

Implicit operator precedence is not allowed in governed methodology artifacts.

---

# 13. Setup triggers versus triggers

The Trigger Contract does not create different syntaxes for setup and trigger rules.

The distinction is **methodological role**, not mathematical representation.

Example:

## Context trigger

```text
RETURN(BTC, horizon=1h) > 0
```

## Setup trigger

```text
DISTANCE_TO_LEVEL(
    level_type=range_high,
    normalization=ATR
) <= 0.20
```

## Trigger trigger

```text
LAST_TRADED_PRICE crosses_above RANGE_HIGH
```

All three use the same Trigger Contract.

The Trading Rule Set determines which role each trigger plays.

---

# 14. Trigger groups

A future Set or Trading Rule Set may assign triggers to roles such as:

```text
context_triggers
setup_triggers
entry_trigger_triggers
invalidation_triggers
exit_triggers
risk_triggers
```

The same contract applies to every group.

This prevents the methodology and implementation from developing separate ad hoc rule languages.

---

# 15. No hidden semantics

Human shorthand may be used in discussion:

```text
OI is expanding
```

But governed methodology must resolve that shorthand into an explicit trigger before research or implementation.

For example:

```text
OI_CHANGE_PCT(horizon=15m) >= X
```

Similarly:

```text
high volatility
```

must eventually resolve to something measurable, such as:

```text
ATR_PCT(..., normalization=percentile) >= X
```

The threshold remains `PARAMETER_TO_TEST` until validated.

---

# 16. Parameter-to-test semantics

If a threshold or temporal parameter is not yet validated, it must be explicitly represented as a research parameter rather than silently fixed.

Example:

```text
OI_CHANGE_PCT(horizon=H) >= X
```

where:

```text
H = PARAMETER_TO_TEST
X = PARAMETER_TO_TEST
```

The Trigger Contract may contain symbolic placeholders such as `H` and `X`, but the **candidate grid/range belongs to the Research Specification**, not to the canonical trigger definition.

Example of a research specification using the trigger:

```text
H ∈ {5m, 15m, 30m, 1h}
X ∈ {1%, 2%, 3%, 5%}
```

These candidate sets are research design inputs, not validated rules.

The final Trading Rule Set may contain a fixed parameter only after the relevant lifecycle evidence supports it.

---

# 17. Trigger historical testability

The historical testability of a trigger is constrained by its least-testable dependency.

Example:

```text
RETURN(15m) > 1%
AND
OI_CHANGE_PCT(15m) > 3%
```

If both metrics are historically reconstructable, the trigger can be backtested over the common historical period.

If a trigger depends on a metric with `LIMITED` or `NONE` historical testability, the trigger inherits that limitation.

TriggerTrade will not create its own large historical high-frequency archive merely to improve the testability of such a trigger.

---

# 18. Missing-data behavior

A trigger may evaluate to one of three internal states:

```text
TRUE
FALSE
UNAVAILABLE
```

`UNAVAILABLE` occurs when:

- required raw data is missing;
- the metric is undefined;
- the requested window/horizon is incomplete;
- a required benchmark is unavailable;
- a required reference level has not yet been formed.

For trading eligibility:

```text
UNAVAILABLE != TRUE
```

A strategy may not treat missing evidence as satisfied. `UNAVAILABLE` must remain distinguishable from `FALSE` for diagnostics and research, even though neither is sufficient to satisfy an entry trigger.

Diagnostics should retain the reason for unavailability.

---

# 19. Look-ahead and evaluation-time rules

Every trigger must be evaluated using only information that was available at the evaluation timestamp.

Examples:

- a 5m closed-candle trigger cannot use that candle before it closes;
- a confirmed swing point becomes available only at its documented confirmation timestamp;
- a previous-day high is available only after the prior day has completed;
- cross-sectional triggers must use the point-in-time universe applicable at the evaluation timestamp.

Backtest and live implementations must use the same availability semantics.

---

# 20. Comparison compatibility

Triggers must compare compatible quantities.

Valid:

```text
RETURN(5m) >= 0.01
```

Valid:

```text
EMA(20,5m) > EMA(50,5m)
```

Potentially invalid without transformation:

```text
ATR_PCT > OI_CHANGE_PCT
```

because the quantities represent different economic objects even though both may be percentages.

Metric-to-metric comparison requires explicit methodological justification whenever the metrics are not naturally commensurable.

---

# 21. Trigger identity and versioning

A trigger's identity includes all semantically material components:

- metric ID;
- symbol/benchmark scope;
- metric parameters;
- normalization;
- operator;
- right-hand operand and scalar unit;
- persistence;
- evaluation cadence and completion rule;
- baseline parameters;
- alignment/as-of semantics when multiple timeframes are involved.

Changing any of these creates a materially different trigger for research purposes.

Example:

```text
OI_CHANGE_PCT(15m) >= 3%
```

is not the same trigger as:

```text
OI_CHANGE_PCT(1h) >= 3%
```

and not the same as:

```text
OI_CHANGE_PCT(15m) >= 5%
```

Research results must not be pooled across materially different trigger definitions without explicit analysis.

---

# 22. Canonical examples

## 21.1 Fixed threshold

```yaml
trigger_id: TRG-001
left:
  metric: OI_CHANGE_PCT
  parameters:
    horizon: 15m
operator: ">="
right:
  value: 0.03
  unit: decimal_fraction
```

## 21.2 Multi-timeframe context

```yaml
trigger_id: TRG-002
left:
  metric: RETURN
  scope:
    symbol: BTCUSDT
  parameters:
    horizon: 1h
operator: ">"
right:
  value: 0
```

## 21.3 Metric-to-metric comparison

```yaml
trigger_id: TRG-003
left:
  metric: EMA
  parameters:
    input_timeframe: 5m
    window: 20
operator: ">"
right:
  metric: EMA
  parameters:
    input_timeframe: 5m
    window: 50
```

## 21.4 Crossover

```yaml
trigger_id: TRG-004
left:
  metric: EMA
  parameters:
    input_timeframe: 5m
    window: 20
operator: crosses_above
right:
  metric: EMA
  parameters:
    input_timeframe: 5m
    window: 50
```

## 21.5 Structural proximity

```yaml
trigger_id: TRG-005
left:
  metric: DISTANCE_TO_LEVEL
  parameters:
    level_type: range_high
    input_timeframe: 5m
    normalization: ATR
operator: "<="
right:
  value: 0.20
```

## 21.6 Parameterized research trigger

```yaml
trigger_id: TRG-006
left:
  metric: AGGRESSIVE_VOLUME_DELTA_PCT
  parameters:
    horizon: H
operator: ">="
right:
  value: X
research_parameters:
  H:
    candidates: [1m, 5m, 15m]
  X:
    candidates: [10, 20, 30, 40]
```

This is a research candidate specification, not a validated trading rule.

---

# 23. What this contract deliberately does not define

This document does not define:

- profitable thresholds;
- preferred timeframes;
- market regimes;
- setups;
- entry triggers;
- exit rules;
- stop placement;
- position sizing;
- strategy combinations;
- Trading Rule Sets;
- evidence that any trigger has predictive value.

Those belong to later methodology layers and must follow the methodology lifecycle.

---

# 24. Relationship to the methodology lifecycle

A trigger can exist before any research hypothesis is validated.

Trigger definitions themselves do not receive lifecycle statuses such as `BACKTESTED` or `LIVE_VALIDATED`.

The later **research candidate / Trading Rule Set using the trigger or Set** receives lifecycle status:

```text
IDEA
HYPOTHESIS
RESEARCH_CANDIDATE
BACKTESTED
PAPER_VALIDATED
LIVE_CANDIDATE
LIVE_VALIDATED
REJECTED
```

A trigger may therefore appear in multiple hypotheses with different parameters and different evidence outcomes.

Failure of one threshold does not prove the entire underlying metric has no value.

---

# 25. Governance rules

1. Every governed trading rule must ultimately resolve to explicit triggers.
2. Every trigger must resolve to canonical metrics, deterministic reference levels, or explicit constants.
3. Thresholds must not be hidden inside human labels.
4. Timeframe/horizon/window must not be implicit.
5. Multi-timeframe relationships are allowed and expected.
6. Missing data must not create false positives.
7. No look-ahead is allowed.
8. Research parameters must remain visibly unvalidated until promotion.
9. Backtest and live evaluation semantics must match.
10. A trigger's presence in a strategy does not establish edge.
11. Adding triggers increases model complexity and therefore raises overfitting risk.
12. Triggers should be added because they express a falsifiable market hypothesis, not because they improve an in-sample equity curve.

---

# 26. Acceptance criteria for the Trigger Contract

This contract is ready to become a methodology baseline when review confirms that:

- every individual TriggerTrade trigger can be represented directly from approved metrics/references without introducing an additional mandatory Condition or Market State layer;
- metric temporal parameters remain fully explicit;
- scalar, metric-to-metric, crossover, structural, and multi-timeframe triggers are supported;
- unit representation is deterministic;
- multi-timeframe as-of alignment is explicit;
- persistence semantics are sufficient and overlapping observations are not misinterpreted as independent;
- missing-data behavior is tri-state and deterministic;
- look-ahead prevention is explicit;
- the contract can be used consistently by research, backtest, TRS, live evaluation, and diagnostics;
- it does not contain trading thresholds presented as proven values.

---

## Review outcome

`REVIEWED BASELINE v0.3.0`

The methodology review accepts the Trigger Contract as the direct bridge between the Metrics Catalog and the future Set Contract.

Binding decisions:

1. there is no mandatory `Condition` layer;
2. there is no mandatory `Market State` layer;
3. `metric + parameters + operator + comparison operand/value` is itself a Trigger;
4. a Trigger may use scalar, metric-to-metric, reference-level, range, crossing, persistence, and approved normalized comparisons;
5. timeframe/horizon/window/anchor/baseline are explicit parts of trigger identity where applicable;
6. trigger evaluation is tri-state: `TRUE / FALSE / UNAVAILABLE`;
7. scalar unit representation must be deterministic;
8. multi-timeframe operands use completed-data `as-of` alignment;
9. ad hoc transformations are not allowed inside triggers;
10. triggers do not define profitability or edge;
11. complex combinations and temporal chains between multiple triggers belong to the next layer: the **Set Contract**.

The next methodology document should define the structure and semantics of a TriggerTrade **Set**: how multiple triggers are combined, sequenced, kept active, expired, reset, and evaluated as one market configuration.
