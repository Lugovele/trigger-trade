# TriggerTrade Repository Rules

## Project

TriggerTrade is a small personal automated crypto trading bot for a limited watchlist of coins.

Core runtime path:

`Market Data -> Trigger -> Signal -> Strategy -> Trade Intent -> Risk -> Execution -> Exchange`

The project is not a general trading platform.

## Architecture invariants

1. Exchange API details are isolated behind exchange adapters.
2. Triggers never place orders directly.
3. Triggers produce deterministic signals only.
4. Strategies convert signals into trade intents.
5. Risk checks are mandatory before execution.
6. Only the execution layer may submit/cancel/reconcile orders.
7. Paper and live modes share the same execution contract through separate adapters.
8. UI code never contains trading logic.
9. LLMs must not be in the live trading decision path.
10. Secrets never enter Git, logs, UI payloads, fixtures, screenshots, or review evidence.
11. Every material decision is traceable from market observation through execution result.
12. Restarts must not silently lose open-order or open-position state.
13. Duplicate order submission must be prevented explicitly.
14. Exchange precision and limits must be validated before submission.
15. When critical execution state is uncertain, fail closed.
16. Paper mode is the default during development. Live mode must be explicitly enabled.

## Git policy

The user performs staging, commits, and pushes manually.

Never run without direct user request:

- `git add`
- `git commit`
- `git commit --amend`
- `git push`
- `git reset`
- `git restore`
- `git clean`
- `git checkout`
- `git switch`
- history rewrites
- destructive branch/worktree cleanup

Before implementation, when Git exists, inspect:

- `git status --short`
- `git log --oneline -n 12`
- `git show --stat HEAD`
- `git diff --check`

## Commit convention

Use:

- `feat:`
- `fix:`
- `refine:`
- `refactor:`
- `test:`
- `docs:`
- `chore:`

Rules:

- lowercase subject;
- short and specific;
- no final period;
- no vague `updates`, `changes`, or `cleanup`;
- independent tasks should be committed independently.

## Worktrees

Create a temporary `codex/*` branch/worktree only when isolation is actually useful, such as:

- parallel work;
- risky refactor;
- dirty `main`;
- independent reviewer/remediation flow;
- explicit user request.

Do not create worktrees by habit for short sequential tasks.

## Development lifecycle

For material runtime changes:

`repository state -> architecture review -> implementation -> focused tests -> adjacent tests -> change review -> remediation -> same-originating-reviewer re-review -> APPROVED_FOR_COMMIT`

Tests are evidence, not reviewer approval.
