# TriggerTrade Set Contract

**Document ID:** TT-METH-004
**Version:** 0.3.0
**Status:** REVIEWED BASELINE
**Scope:** Canonical structure and evaluation semantics for TriggerTrade Sets built from Triggers
**Dependencies:**
- `BYBIT_RAW_DATA_CATALOG` accepted baseline
- `TRIGGERTRADE_DERIVED_METRICS_CATALOG` reviewed baseline
- `TRIGGERTRADE_TRIGGER_CONTRACT` reviewed baseline

---

## 1. Purpose

This document defines the canonical TriggerTrade **Set Contract**.

A Set is a deterministic market configuration built from one or more TriggerTrade triggers plus explicit logical and, where required, temporal relationships between those triggers.

A Set answers:

> Has the required market configuration formed according to the exact rules of this Set?

A Set does **not** define whether the configuration has a profitable edge.

A Set contains **no trading Rules**.

The Set layer must not define, imply, or partially encode:

- entry logic;
- order type;
- execution method;
- stop-loss;
- take-profit;
- partial exits;
- time exits;
- trailing;
- re-entry;
- position sizing;
- leverage;
- portfolio exposure;
- risk limits;
- fee/slippage handling;
- trade management.

Those belong to the later **Rules** layer.

The methodology boundary is:

```text
SET = when the market configuration exists
RULES = what to do with it
```

A later complete trading candidate is formed by combining a Set with Rules, but this document defines the Set only.

The methodology chain is:

```text
Raw Data
    ↓
Derived Metrics
    ↓
Triggers
    ↓
Sets
    ↓
Rules
    ↓
Research
    ↓
Trading Rule Sets
```

---

## 2. Why the Set layer exists

A Trigger is atomic.

Example:

```text
OI_CHANGE_PCT(horizon=15m) >= X
```

A realistic market configuration usually requires several triggers and may require them to interact in a specific way.

For example:

```text
TRIGGER_A
AND
TRIGGER_B
THEN
TRIGGER_C within 10m
WHILE
TRIGGER_D remains TRUE
```

That structure cannot be represented correctly by treating every trigger as an unrelated Boolean value.

The Set Contract therefore standardizes:

- logical combination;
- grouping;
- sequence;
- temporal windows;
- persistence;
- expiry;
- reset;
- invalidation;
- trigger freshness;
- re-arming;
- evaluation state;
- duplicate firing behavior;
- Set identity and versioning.

The purpose is to make the same Set mean exactly the same thing in:

- methodology documentation;
- research specifications;
- backtests;
- paper evaluation;
- live evaluation;
- diagnostics;
- future UI/configuration.

---

## 3. Hard boundary: Set vs Rules

This separation is mandatory.

### Set

A Set answers only:

> Has the specified market configuration formed?

It may define:

- which triggers participate;
- Boolean relationships between triggers;
- ordering;
- timing between trigger events;
- trigger freshness;
- Set expiry;
- Set reset;
- Set re-arming;
- the timestamp at which the Set is considered matched.

These are **Set evaluation semantics**, not trading Rules.

### Rules

Rules answer later questions such as:

> What do we do after the Set is matched?

Examples:

- enter or do not enter;
- LONG or SHORT;
- market or limit order;
- stop placement;
- take-profit;
- partial exit;
- time stop;
- trailing;
- re-entry;
- risk per trade;
- leverage;
- maximum exposure;
- execution constraints.

None of these may appear inside a Set definition.

### Canonical separation

```text
SET
=
market configuration only

RULES
=
trading action and management only
```

A Set may be researched independently from any specific Rules package.

Different Rules may later be applied to the same Set.

Likewise, the same Rules architecture may later be tested across different Sets.

---

## 4. Core definition

A Set consists of:

```text
SET
=
TRIGGERS
+
RELATIONSHIPS
+
TEMPORAL RULES
+
LIFECYCLE RULES
```

Not every Set needs every element.

A simple Set may be:

```text
TRIGGER_A AND TRIGGER_B
```

A more complex Set may be:

```text
TRIGGER_A
THEN
TRIGGER_B within 15m
THEN
TRIGGER_C within 5m
WHILE
TRIGGER_D remains TRUE
RESET if TRIGGER_E fires
EXPIRE after 30m
```

---

## 5. Set is not a Trigger

A Trigger is one explicit evaluable rule.

Example:

```text
RETURN(horizon=1h) > 0
```

A Set combines triggers.

Example:

```text
TRG-001 AND TRG-002 AND TRG-003
```

The Set must never hide new metric logic inside its structure.

If a new metric comparison is required, it must first be defined as a Trigger under the Trigger Contract.

---

## 7. Set is not Research

A Set describes a deterministic market configuration.

Example:

```text
TRG-001
AND
TRG-002
THEN
TRG-003 within 10m
```

Research later asks:

> Does this Set have predictive or economic value for a specified outcome?

Therefore:

```text
Set definition != hypothesis
Set definition != validated edge
```

The same Set may later be tested against:

- LONG outcomes;
- SHORT outcomes;
- different holding periods;
- different exits;
- different market regimes;
- different instrument universes.

---

# 7. Canonical Set schema

Every governed Set must contain the following fields.

## 6.1 `set_id`

Stable identifier.

Example:

```text
SET-001
```

## 6.2 `name`

Human-readable name.

Names are labels only and must not replace explicit trigger logic.

## 6.3 `version`

Material changes to trigger composition or Set semantics require a new version.

## 6.4 `trigger_refs`

Explicit references to Trigger definitions.

Example:

```yaml
trigger_refs:
  - TRG-001
  - TRG-002
  - TRG-003
```

## 6.5 `logic`

The explicit logical/temporal expression that defines Set completion.

## 6.6 `evaluation`

Defines when the Set engine reevaluates Set state.

## 6.7 `lifecycle`

Defines arming, expiry, reset, and re-arming semantics.

---

# 8. Set evaluation states

A Set is stateful.

Canonical states:

```text
INACTIVE
ARMED
PARTIALLY_MATCHED
MATCHED
EXPIRED
RESET
UNAVAILABLE
```

## INACTIVE

The Set is not currently in an active matching process.

## ARMED

The Set is eligible to begin matching.

## PARTIALLY_MATCHED

One or more required trigger steps have occurred, but the Set is not complete.

## MATCHED

The full Set definition has been satisfied.

## EXPIRED

The Set began forming but failed to complete within its allowed lifetime or window.

## RESET

A reset / set-formation set-formation invalidation rule explicitly cleared current progress.

## UNAVAILABLE

The Set cannot be evaluated correctly because one or more required trigger dependencies are unavailable.

These states are internal methodology/evaluation semantics.

They are not lifecycle statuses such as `BACKTESTED` or `LIVE_VALIDATED`.

---

# 9. Boolean relationships

## 8.1 AND

All specified triggers must satisfy the Set semantics.

Example:

```text
TRG-A AND TRG-B
```

For a purely simultaneous Set, all required triggers must be TRUE at the evaluation timestamp.

Tri-state semantics:

- `FALSE AND anything` → `FALSE`;
- `TRUE AND TRUE` → `TRUE`;
- `TRUE AND UNAVAILABLE` → `UNAVAILABLE`;
- `UNAVAILABLE AND UNAVAILABLE` → `UNAVAILABLE`.

## 9.2 OR

At least one branch must satisfy the Set semantics.

Example:

```text
TRG-A OR TRG-B
```

Tri-state semantics:

- `TRUE OR anything` → `TRUE`;
- `FALSE OR FALSE` → `FALSE`;
- `FALSE OR UNAVAILABLE` → `UNAVAILABLE`;
- `UNAVAILABLE OR UNAVAILABLE` → `UNAVAILABLE`.

An unavailable branch must not be silently treated as false when doing so would change the Set result.

## 8.3 NOT

A trigger must not be TRUE under the declared timing semantics.

Example:

```text
TRG-A AND NOT TRG-B
```

`NOT UNAVAILABLE` evaluates to `UNAVAILABLE`, not `TRUE`.

Missing evidence is not negative evidence.

## 8.4 Explicit grouping

Grouping must always be explicit.

Valid:

```text
TRG-A AND (TRG-B OR TRG-C)
```

Implicit precedence is not permitted in governed Set definitions.

---

# 10. Simultaneous versus event logic

This distinction is mandatory.

## 9.1 State-style trigger

A trigger may remain TRUE for a period.

Example:

```text
RETURN(1h) > 0
```

## 9.2 Event-style trigger

A trigger may fire at a specific transition.

Example:

```text
EMA(20,5m) crosses_above EMA(50,5m)
```

The Set Contract must distinguish:

```text
is_true(TRG-A)
```

from:

```text
fires(TRG-A)
```

A Set may require either current truth or a new firing event.

For a state-style trigger, `fires(TRG-A)` means the trigger transitions from a non-TRUE state (`FALSE` or, where explicitly allowed, `UNAVAILABLE`) to `TRUE` at the current evaluation timestamp. Implementations must not repeatedly emit a fresh event while the trigger simply remains TRUE.

This prevents a long-lived TRUE trigger from being incorrectly treated as a newly occurring event on every evaluation cycle.

---

# 11. Sequence operator

## THEN

`A THEN B` means:

1. A must fire or become satisfied according to the declared trigger mode;
2. only after A is recognized may B complete the next sequence step.

Example:

```text
TRG-A THEN TRG-B
```

If B happened before A, it does not satisfy the sequence unless the Set explicitly allows pre-existing state.

If A and B become satisfied at the same evaluation timestamp, the Set must explicitly declare whether equal timestamps are allowed for that sequence. Default baseline: `THEN` requires B's canonical event timestamp to be strictly later than A's.

This ordering rule must be deterministic.

---

# 12. Temporal windows

A sequence may constrain the allowed delay between steps.

Example:

```text
TRG-A
THEN TRG-B WITHIN 10m
```

The clock starts from the canonical timestamp at which A completed its required role.

If B completes after the 10-minute deadline:

```text
sequence step fails
```

The Set then follows its explicitly declared Set-lifecycle behavior, for example:

- expire the current attempt;
- reset the current attempt and re-arm;
- return to a defined earlier sequence step.

No implicit behavior is allowed.

---

# 13. Maximum Set lifetime

A Set may define an overall lifetime.

Example:

```text
max_lifetime: 30m
```

The Set must explicitly define what starts the lifetime clock: Set arming, first matched trigger, or another declared Set-formation event. The Set must fully match before the resulting deadline.

If not:

```text
SET → EXPIRED
```

This prevents old partial configurations from remaining indefinitely active.

---

# 14. WHILE / maintained-state requirement

A Set may require another trigger to remain TRUE while a sequence develops.

Example:

```text
TRG-A
THEN TRG-B
WHILE TRG-C remains TRUE
```

If TRG-C becomes FALSE before Set completion:

```text
the Set follows its declared set-formation invalidation / reset behavior
```

This is distinct from requiring TRG-C to have fired once.

---

# 16. UNTIL / Set-formation invalidation

A Set may remain eligible only until a specific trigger occurs.

Example:

```text
TRG-A
THEN TRG-B
UNTIL TRG-X fires
```

If TRG-X fires before completion:

```text
current Set attempt is invalidated
```

This is not a trading invalidation rule and must not be interpreted as stop-loss, exit, or trade-management logic.

It invalidates only the current Set-formation attempt.

---

# 16. RESET semantics

A Set must explicitly define what clears partial progress.

Possible reset causes include:

- explicit reset trigger;
- failed maintained condition;
- sequence timeout;
- overall expiry;
- session boundary;
- symbol state change;
- required context becoming unavailable.

Example:

```yaml
reset:
  on_trigger: TRG-X
  on_expiry: true
```

Reset returns the Set to its declared initial state.

---

# 17. Trigger freshness

A Set must define whether an already-TRUE trigger may satisfy a step or whether a fresh firing is required.

Canonical modes:

```text
CURRENT_STATE
FRESH_EVENT
SINCE_SET_ARMED
```

## CURRENT_STATE

The trigger only needs to be TRUE when evaluated.

## FRESH_EVENT

The trigger must newly fire after the relevant Set step becomes active.

## SINCE_SET_ARMED

The trigger may have fired at any point after the Set became ARMED.

This distinction is critical for temporal correctness.

---

# 18. Trigger validity / staleness

A Set may specify how long a trigger result remains acceptable.

Example:

```text
TRG-A freshness <= 5m
```

A trigger that fired 40 minutes ago cannot silently satisfy a Set intended to describe a current market configuration.

Freshness rules must be explicit.

---

# 19. Repeated trigger firing

A trigger may fire multiple times while a Set is forming.

The Set must define whether repeated firing:

- replaces the previous timestamp;
- is ignored;
- restarts a window;
- creates a new parallel Set attempt.

Canonical baseline default:

```text
one active attempt per set_id + set_version + symbol
```

Repeated firing does not create parallel attempts unless the Set definition explicitly opts into parallel-attempt semantics. Parallel attempts are deferred and should not be used in the baseline methodology because they increase ambiguity and combinatorial complexity.

---

# 20. Re-arming after MATCHED

After a Set reaches `MATCHED`, the methodology must define when it may match again.

Supported policies:

```text
AFTER_RESET
AFTER_ALL_REQUIRED_TRIGGERS_CLEAR
AFTER_COOLDOWN
NEXT_SESSION
```

`IMMEDIATE` re-arming is intentionally excluded from the baseline because a long-lived TRUE configuration could otherwise generate repeated `MATCHED` events without a new market formation.

No automatic repeat firing policy should be assumed.

This is important for both backtest event counts and live behavior.

---

# 21. Cooldown

A Set may define a cooldown after `MATCHED`, `EXPIRED`, or `RESET`.

Example:

```text
cooldown_after_match: 15m
```

Cooldown is a Set lifecycle parameter.

It is not a trading exit/risk rule.

Any cooldown introduced for research remains `PARAMETER_TO_TEST` until validated.

---

# 22. Multi-timeframe triggers inside a Set

Triggers already preserve their own timeframe/horizon/window parameters.

A Set may combine triggers from different timeframes.

Example:

```text
TRG-A: RETURN(BTC,1h) > 0
TRG-B: OI_CHANGE_PCT(asset,15m) >= X
TRG-C: LAST_TRADED_PRICE crosses_above RANGE_HIGH(5m)
```

The Set engine uses Trigger Contract `as-of` semantics.

At Set evaluation timestamp `T`, no trigger may use information unavailable at or before `T`.

---

# 23. Branching Sets

A Set may allow alternative valid paths.

Example:

```text
TRG-A
AND
(
    TRG-B THEN TRG-C
    OR
    TRG-D THEN TRG-E
)
```

Both branches must be fully explicit.

Branching should be used sparingly because every branch increases research degrees of freedom and overfitting risk.

---

# 24. Optional triggers

The baseline Set Contract does not treat optional triggers as contributing to Set completion.

A trigger is either required by the Set logic or it is not.

If later research needs scoring/weighting such as:

```text
3 of 5 triggers
```

or:

```text
weighted score >= threshold
```

that should be introduced as a deliberate extension, not silently encoded through optional fields.

This avoids turning the Set layer into an unconstrained scoring model prematurely.

---

# 25. N-of-M logic

`N of M` is supported as an explicit Set operator, but it is not part of the minimal core and should be used only when the Set definition has a clear market rationale.

Example:

```text
AT_LEAST 3 OF [TRG-A, TRG-B, TRG-C, TRG-D, TRG-E]
```

It must not be represented as vague language such as:

```text
most bullish triggers are present
```

N and M are parameters and materially change the Set definition.

Because N-of-M introduces substantial combinatorial flexibility, its use should require explicit research justification.

---

# 26. Set completion timestamp

Every matched Set must have one canonical `matched_at` timestamp.

For sequential Sets:

```text
matched_at = timestamp at which the final required step completed
```

For simultaneous Boolean Sets:

```text
matched_at = first evaluation timestamp at which the full expression became TRUE
```

The completion timestamp is required for:

- outcome labeling;
- research;
- research/backtest event alignment;
- diagnostics;
- duplicate suppression.

---

# 27. Set attempt identity

Every active formation attempt should have a unique attempt identity conceptually:

```text
set_id
set_version
symbol
attempt_started_at
```

This is necessary to distinguish:

- one failed attempt;
- one expired attempt;
- one matched attempt;
- another later attempt of the same Set.

The methodology does not require a particular database implementation.

---

# 28. Missing data behavior

A Set must preserve trigger-level `UNAVAILABLE`.

Rules:

1. `UNAVAILABLE` must never be silently converted to TRUE.
2. `NOT UNAVAILABLE` must not count as satisfied negative evidence.
3. A Set whose required branch cannot be evaluated may become `UNAVAILABLE` according to its logic.
4. Diagnostics must retain which trigger caused unavailability.

---

# 29. No hidden trigger logic inside Set operators

Invalid:

```text
TRG-A THEN "strong momentum"
```

Invalid:

```text
TRG-A AND "OI is rising fast"
```

Every atomic market rule must resolve to an explicit Trigger ID.

The Set layer is responsible for composition, not for inventing new metric semantics.

---

# 30. Parameterization

Set-level parameters may include:

- sequence windows;
- max lifetime;
- freshness;
- cooldown;
- reset policy;
- re-arm policy;
- N-of-M threshold.

Unvalidated values must remain:

```text
PARAMETER_TO_TEST
```

Research parameter grids belong to future Research Specifications.

The Set Contract defines parameter semantics only.

---

# 31. Canonical simple examples

## 30.1 Simultaneous Set

```yaml
set_id: SET-001
version: 0.1
triggers:
  - TRG-001
  - TRG-002
logic:
  all:
    - current_state: TRG-001
    - current_state: TRG-002
```

Meaning:

```text
TRG-001 AND TRG-002 must be TRUE simultaneously
```

---

## 30.2 Sequential Set

```yaml
set_id: SET-002
version: 0.1
logic:
  sequence:
    - fresh_event: TRG-001
    - fresh_event: TRG-002
      within: 10m
```

Meaning:

```text
TRG-001 fires
THEN
TRG-002 fires within 10m
```

---

## 30.3 Sequence with maintained context

```yaml
set_id: SET-003
version: 0.1
logic:
  while:
    current_state: TRG-CONTEXT
  sequence:
    - fresh_event: TRG-A
    - fresh_event: TRG-B
      within: 10m
```

Meaning:

```text
TRG-CONTEXT must remain TRUE
while
TRG-A → TRG-B within 10m
```

---

## 30.4 Sequence with invalidation

```yaml
set_id: SET-004
version: 0.1
logic:
  sequence:
    - fresh_event: TRG-A
    - fresh_event: TRG-B
      within: 10m
lifecycle:
  reset_if:
    - fires: TRG-X
```

---

# 32. What belongs in a Set definition

A governed Set definition should specify:

- Set ID;
- version;
- constituent Trigger IDs;
- Boolean grouping;
- state-vs-event requirement for each trigger;
- order, if relevant;
- inter-step timing, if relevant;
- trigger freshness, if relevant;
- maintained conditions, if relevant;
- Set expiry;
- reset / set-formation set-formation invalidation rules;
- re-arm policy;
- cooldown, if used;
- canonical `matched_at` rule.

---

# 34. What does not belong in a Set definition

Trading Rules are prohibited inside a Set definition.

A Set must not contain or imply:

- whether to enter a trade;
- LONG / SHORT action;
- entry timing as a trading action;
- entry order type;
- execution method;
- stop-loss;
- take-profit;
- partial exits;
- time exits;
- trailing;
- re-entry;
- position sizing;
- leverage;
- portfolio exposure;
- risk limits;
- fee/slippage handling;
- trade management.

The following also do not belong in the Set definition:

- expected profit;
- expected return;
- win rate;
- research sample design;
- promotion criteria;
- claims that the Set has edge.

Set-lifecycle concepts such as `reset`, `expiry`, and `matched_at` describe only whether the **market configuration** exists. They must never be interpreted as trading actions.

---

# 34. Set complexity and overfitting

Every additional trigger, branch, sequence step, timer, reset rule, or exception increases model complexity.

Therefore methodology review must treat these as research degrees of freedom.

A Set should not become more complex merely because additional rules improve in-sample backtest results.

Complexity requires a market rationale and later robustness evidence.

---

# 35. Set identity and material changes

The Set identity includes:

- Set ID;
- version;
- Trigger IDs and Trigger versions;
- Boolean structure;
- event/state modes;
- sequence order;
- timing windows;
- freshness;
- expiry;
- reset policy;
- re-arm policy;
- cooldown;
- N-of-M parameters where used.

Changing any semantically material component creates a new Set version for research purposes.

---

# 36. Relationship to future Research

A Set is the market-pattern object that Research evaluates.

Future research may ask:

```text
When SET-X matches, what happens to price over 5m / 15m / 1h?
```

or:

```text
Does SET-X behave differently in LONG versus SHORT direction?
```

or:

```text
Does adding TRG-D to SET-X improve net expectancy robustly?
```

The Set must remain stable and versioned so these questions are scientifically meaningful.

---

# 38. Governance rules

1. A Set is composed only from approved Trigger definitions.
2. A Set contains no trading Rules.
3. `SET MATCHED` means only that the specified market configuration formed.
4. Set composition must be explicit.
5. Boolean grouping must be explicit.
6. Tri-state propagation (`TRUE / FALSE / UNAVAILABLE`) must be deterministic.
7. State versus event semantics must be explicit.
8. Sequence order and equal-timestamp behavior must be explicit.
9. Time windows and their clock-start events must be explicit.
10. Expiry, reset, Set-formation invalidation, and re-arm behavior must be explicit where relevant.
11. Missing data must remain distinguishable.
12. Look-ahead is prohibited.
13. Multi-timeframe trigger values inherit Trigger Contract as-of semantics.
14. Set parameters are not assumed to be optimal.
15. One active attempt per Set/version/symbol is the baseline default.
16. Set complexity is a research risk.
17. A Set is not evidence of edge.
18. A matched Set does not imply entry, direction, or any trading action.
19. Research, backtest, paper, and live implementations must interpret the same Set identically.

---

# 38. Acceptance criteria

The Set Contract is ready for baseline promotion when methodology review confirms that it can represent:

- simultaneous multi-trigger configurations;
- AND / OR / NOT;
- explicit grouping;
- state-style and event-style trigger use;
- ordered sequences;
- inter-step time windows;
- maintained trigger requirements;
- set-formation invalidation / reset;
- Set expiry;
- trigger freshness;
- re-arming;
- cooldown;
- multi-timeframe triggers;
- deterministic match timestamps;
- missing-data semantics;

without introducing any trading Rules into the Set layer.

Baseline promotion also requires:

- deterministic tri-state Boolean semantics;
- deterministic state-to-event firing semantics;
- deterministic handling of equal timestamps in sequences;
- a defined Set-lifetime clock start;
- one-active-attempt baseline semantics;
- no language that makes `MATCHED` equivalent to a trade signal.

---

## Review outcome

`REVIEWED BASELINE v0.3.0`

The methodology review accepts the Set Contract with the following binding decisions:

1. Set is a pure market-configuration object built only from Triggers.
2. Set contains no trading Rules.
3. `MATCHED` is a market-configuration event, not a trade instruction.
4. Boolean logic uses deterministic tri-state semantics.
5. Trigger use inside Sets explicitly distinguishes current state from fresh firing.
6. Temporal sequences define ordering, time windows, and equal-timestamp behavior.
7. Set lifecycle covers only formation semantics: arming, partial match, expiry, reset, re-arm, and freshness.
8. Baseline permits one active Set attempt per `set_id + version + symbol`.
9. No Set-lifecycle operation may be interpreted as entry, exit, stop, or other trade management.
10. Set complexity remains a research degree of freedom and must be justified later.

The next methodology layer is the separate **Rules Contract**.

The combination of:

```text
SET + RULES
```

creates the complete candidate trading construction that can later move into Research.

Research comes after both Set and Rules structures are defined.
