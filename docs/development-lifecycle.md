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
