# TriggerTrade Development Lifecycle

## Standard lifecycle

For material runtime changes:

```text
repository-state verification
        ->
architecture review
        ->
implementation
        ->
focused validation
        ->
adjacent validation
        ->
pre-commit change review
        ->
remediation if required
        ->
same-originating-reviewer re-review
        ->
APPROVED_FOR_COMMIT
```

Tests are evidence. Tests do not replace reviewer approval.

## Architecture review

Use before implementation when a change affects:

- module boundaries;
- execution flow;
- exchange contracts;
- persistence/state recovery;
- trigger/strategy/risk contracts;
- dashboard/runtime boundaries;
- security-sensitive design.

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

## Remediation

The remediation agent makes the smallest necessary fix and cannot approve its own changes.

Maximum remediation status:

```text
REMEDIATION_COMPLETE_PENDING_REVIEW
```

The same originating reviewer then re-reviews.

## Repository-state checks

When Git exists, inspect at least:

```text
git status --short
git log --oneline -n 12
git show --stat HEAD
git diff --check
```

Do not automatically stage, commit, push, reset, restore, clean, switch branches, or rewrite history.

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
