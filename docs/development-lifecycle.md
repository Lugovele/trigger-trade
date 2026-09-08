# TriggerTrade Development Lifecycle

## Standard lifecycle

Canonical lifecycle:

```text
repository-state verification
        ->
classify change
        ->
architecture review if required
        ->
implementation
        ->
focused validation
        ->
adjacent validation
        ->
required specialist reviews
        ->
remediation + same specialist re-review
        ->
final triggertrade_change_reviewer review
        ->
remediation + same change reviewer re-review
        ->
APPROVED_FOR_COMMIT
        ->
stage intended files
        ->
commit
        ->
push
        ->
verify clean/synced
```

Tests are evidence. Tests do not replace reviewer approval.

Only `triggertrade_change_reviewer` may emit `APPROVED_FOR_COMMIT`.

The stage/commit/push tail runs automatically only when the current lifecycle
task explicitly requested commit/push. No additional user confirmation is
required after `APPROVED_FOR_COMMIT` in that case. If the task did not request
commit/push, stop at `APPROVED_FOR_COMMIT` and report readiness. If the task
explicitly says no commit or no push, that override wins.

## Security change review

Use `triggertrade_security_change_reviewer` for security-relevant development changes. It participates in the normal review/remediation model and may run in two phases:

- `PRE_CHANGE` before implementation when planning or architecture information is available;
- `POST_CHANGE` after implementation and validation, against the actual diff/current working tree.

Require it when a change affects exchange API integration, authenticated external APIs, secrets, sensitive environment variables, paper/test/live boundaries, live-mode enablement, execution authority, private exchange/account/order/fill data, risk controls whose failure could permit consequential execution, kill switches, network clients, HTTP/WebSocket/webhook/callback behavior, authentication, authorization, privileged routes, subprocess/shell execution, sensitive filesystem access, logging/diagnostics, persistence of sensitive or execution-critical state, deployment/CI/container/network exposure, TLS/security boundaries, material security dependencies, startup/bootstrap secret loading or live activation, untrusted input reaching consequential operations, unsafe serialization/deserialization, consequential retry/idempotency, or security-control configuration.

Do not require this reviewer for purely cosmetic, documentation-only, or unrelated low-risk changes unless the actual diff crosses a security boundary. `SECURITY_CHANGE_APPROVED` means only that the reviewed change has no unresolved security findings within scope; it does not mean TriggerTrade is secure and does not replace final change review.

## Agent security review

Use `triggertrade_agent_security_reviewer` when a change affects agent `.toml` files, agent instructions, agent registration, orchestrator routing, sandbox/write/network/filesystem/tool permissions, shell permissions, environment or secret access, Git permissions, automations, persistent agent tasks, reviewer/remediation authority, agent-to-agent delegation, prompt/context authority boundaries, untrusted context sources, model-driven consequential actions, or an agent's ability to reach exchange credentials or live execution paths.

The reviewer verifies least privilege, read-only reviewer boundaries, no remediation self-approval, no silent permission widening, no production credential access without explicit need and authorization, preservation of Git policy, and isolation from live trading side effects.

## Application security audit

Use `triggertrade_security_auditor` only for broad repository-level security audit workflows: explicit user request, requested periodic audit, preparation for broader live/deployment exposure, major architecture/security-boundary change, suspected credential leak, security incident, repeated systemic change-level findings, or an orchestrator-identified risk too broad for one diff.

Do not insert the auditor into every ordinary change lifecycle. Audit output is not a substitute for security change review, architecture review, trading-rules review, UX review, or general pre-commit review. Audit status must not directly produce `APPROVED_FOR_COMMIT`; remediation items become scoped changes that go through the applicable normal reviewers.

Auditor statuses are exactly:

```text
AUDIT_PASS
AUDIT_FINDINGS
AUDIT_BLOCKED
```

## Test planning

Use `triggertrade_test_planner` when a change is broad, risky, or has unclear
validation coverage. It is read-only and may propose focused, adjacent,
integration, migration, security, or regression tests. Test planning is support
evidence only: it does not replace architecture, trading-rules, UX, security,
agent-security, or final change review.

## Architecture review

Use before implementation when a change affects:

- module boundaries;
- execution flow;
- exchange contracts;
- persistence/state recovery;
- trigger/strategy/risk contracts;
- dashboard/runtime boundaries;
- security-sensitive design.

Architecture statuses are exactly:

```text
ARCHITECTURE_APPROVED
ARCHITECTURE_CHANGES_REQUIRED
ARCHITECTURE_BLOCKED
```

Architecture approval is domain-specific and cannot approve commit.

## Trading-rules review

Use when a change:

- creates or changes a trigger;
- changes a strategy condition;
- changes position sizing;
- changes stop-loss/take-profit semantics;
- changes cooldown/exposure rules;
- changes order eligibility;
- changes execution decision semantics.

The reviewer verifies faithful implementation of a decided rule. It does not decide whether a trading strategy is profitable.

Trading-rules statuses are exactly:

```text
TRADING_RULES_APPROVED
TRADING_RULES_CHANGES_REQUIRED
TRADING_RULES_BLOCKED
```

Trading-rules approval is domain-specific and cannot approve commit.

## Change review

After implementation, review:

- correctness;
- regressions;
- architecture compliance;
- unsafe execution paths;
- duplicate-order risk;
- partial-fill handling;
- exchange errors;
- precision;
- persistence;
- restart behavior;
- secrets leakage;
- tests;
- diff hygiene;
- scope creep.

Final status:

```text
APPROVED_FOR_COMMIT
CHANGES_REQUIRED
BLOCKED
```

This is the only active reviewer vocabulary that may include
`APPROVED_FOR_COMMIT`.

## Remediation

The remediation agent makes the smallest necessary fix and cannot approve its own changes.

Maximum remediation status:

```text
REMEDIATION_COMPLETE_PENDING_REVIEW
```

The same originating reviewer then re-reviews.

This same-originating-reviewer loop applies to architecture, trading-rules, UX, security change, agent-security, and general change findings. Audit-driven remediation must be converted into a scoped normal change; the auditor does not replace the required change-level reviewers.

`APPROVED_FOR_COMMIT` requires approval from every reviewer required by the specific change after any remediation. Tests, security change approval, agent-security approval, UX approval, trading-rules approval, architecture approval, and audit status are not standalone commit approval.

## Repository-state checks

When Git exists, inspect at least:

```text
git status --short
git log --oneline -n 12
git show --stat HEAD
git diff --check
```

Before staging for an approved lifecycle task, inspect `git status --short --branch`
and `git diff --name-only`. Stage only intended files for the current lifecycle
unit and inspect `git diff --cached --name-only` before committing.

Never run `git commit --amend`, force push, reset, restore, clean, switch
branches, destructive cleanup, or history rewrite as part of the normal
lifecycle.

## Worktrees

Use temporary worktrees/branches only when isolation is useful:

- parallel work;
- risky refactor;
- dirty main;
- independent review/remediation;
- explicit user request.

Do not create them for every small task.

## Trigger Set Changes

Changes that add, remove, promote, archive, or alter trigger set membership require architecture review. If they change the semantic meaning of a trigger, strategy, or risk rule, they also require trading-rules review.

A trigger set promotion must be explicit and audited. Tests may provide evidence that a TESTING set behaved as expected, but tests do not automatically promote that set to ACTIVE. The dashboard may display ACTIVE and TEST evidence, but it must not perform promotion or change rule configuration.

The reviewer should verify that lane-specific idempotency keys include `lane`, `symbol`, `timeframe`, `candle_id`, `trigger_set_id`, and `trigger_set_version`, and that legacy records remain readable after schema extension.

## Rule Recommendation Lifecycle

Analytics/recommendation changes require architecture review for rule-version immutability, recommendation boundaries, no automatic promotion, no execution shortcuts, and dashboard read-only behavior. Changes introducing or changing trigger semantics require trading-rules review for exact inputs, units, operators, boundary behavior, stale/missing behavior, and TEST/ACTIVE status.

Recommendations must keep Observation, Hypothesis, and Recommended Experiment separate. Review evidence must not claim unsupported causality or fabricate P&L, win-rate, return, drawdown, or expectancy metrics when backend accounting semantics do not exist.


## Registry Bootstrap Changes

Changes to production registry initialization require architecture review. Reviewers should verify a single shared bootstrap path, consistent runtime/dashboard DB resolution, idempotency across repeated startup, safe additive legacy migration, no dashboard-owned business initialization, and fail-closed behavior for same-version semantic mismatch. Bootstrap evidence must distinguish configured registry entities from runtime evidence; tests must not populate fake candles, trades, fills, P&L, or recommendations to make the dashboard look active.

## Intraday Governance Changes

Intraday experiment governance changes require architecture review when they add
readiness states, recommendation actions, persistence, dashboard controls, or
execution safety gates. Trading-rules review is required only when trigger,
strategy, or risk semantics change.

Readiness policy defaults are lifecycle governance settings, not trading alpha
rules. The initial policy (`intraday-governance-defaults@0.1.0`) uses 7 calendar
days, 100 candidate signals, and 50 closed trades as review-readiness gates.
Unsupported capabilities must be represented explicitly as unavailable and must
not be rendered as zero evidence.

STOP TRADING changes must be persisted and audited. Paused state must survive
restart, block only new ACTIVE submissions at the execution boundary, and leave
TEST lane evidence, analytics, market data, and reconciliation available.

## Perpetual Futures Changes

Perpetual futures lifecycle units require architecture and trading-rules review
before implementation. Reviews must confirm the exact product category,
position state machine, leverage defaults, margin/cost/funding contracts,
net-edge behavior, and Demo-only safety.

Futures implementation must remain additive until migration is explicitly
approved: Spot execution history stays readable, dashboard projections stay
read-only, and no live/mainnet call may be introduced. Real Demo futures smoke
tests are opt-in and must stop if a safe PostOnly limit scenario cannot be
derived.

## Historical Replay Changes

Historical replay changes require architecture review because they touch
persistence, evidence sources, analytics, and runtime parity. Trading-rules
review is required only when replay work changes trigger, strategy, risk,
regime, cost, or accounting semantics; replaying already approved versions does
not by itself create a new trading rule.

A backtest run must pin the Trigger Set version, all Rule Versions, regime
version, strategy version, risk policy version, simulator version, accounting
version, cost model, data source, period, timeframe, warmup, parameters and
historical data hash. Reviewers should verify no-lookahead behavior, immutable
completed runs, idempotent reruns, source-aware `BACKTEST` evidence, no private
or order API calls, no optimizer, no auto-promotion, and no dashboard-created
historical evidence.
