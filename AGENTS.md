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

Git staging, commit, and push are task-scoped lifecycle actions.

When the current lifecycle task explicitly includes commit and push, Codex may
continue automatically after all required specialist reviewers approve, final
`triggertrade_change_reviewer` returns `APPROVED_FOR_COMMIT`, and required
validation passes:

- `git add`
- `git commit`
- `git push`

No extra user confirmation is required at that point; the original lifecycle
prompt is the commit/push authority. Stage only files belonging to the current
lifecycle unit, verify `git diff --cached --name-only`, push only to
`origin/main`, then verify `HEAD == origin/main` and a clean working tree.

If the current task does not explicitly request commit/push, stop at
`APPROVED_FOR_COMMIT` and report readiness. If the current task explicitly says
no commit or no push, that instruction wins.

Never run:

- `git commit --amend`
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

Canonical lifecycle:

`repository state -> classify change -> architecture review if required -> implementation -> focused tests -> adjacent tests -> required specialist reviews -> remediation + same specialist re-review -> final change review -> remediation + same change reviewer re-review -> APPROVED_FOR_COMMIT -> stage intended files -> commit -> push -> verify clean/synced`

The stage/commit/push tail runs only when the current task explicitly requested
commit/push. Otherwise the lifecycle stops at `APPROVED_FOR_COMMIT` with a
readiness report.

Available reviewers:

- `triggertrade_architecture_reviewer`: read-only structure/boundary review; status `ARCHITECTURE_APPROVED`, `ARCHITECTURE_CHANGES_REQUIRED`, or `ARCHITECTURE_BLOCKED`; not a commit gate.
- `triggertrade_trading_rules_reviewer`: read-only trading-semantic review for triggers, strategy, sizing, exits, exposure, and execution eligibility; status `TRADING_RULES_APPROVED`, `TRADING_RULES_CHANGES_REQUIRED`, or `TRADING_RULES_BLOCKED`; not a commit gate.
- `triggertrade_ux_reviewer`: read-only UX/fidelity review for frontend or materially user-facing state presentation; status `UX_APPROVED`, `UX_CHANGES_REQUIRED`, or `UX_BLOCKED`.
- `triggertrade_security_change_reviewer`: read-only per-change application security review when a change touches secrets, authenticated APIs, execution authority, privileged routes, safety controls, network exposure, sensitive persistence/logging, or other security boundaries; status `SECURITY_CHANGE_APPROVED`, `SECURITY_CHANGES_REQUIRED`, or `SECURITY_BLOCKED`.
- `triggertrade_agent_security_reviewer`: read-only review for agent definitions, routing, permissions, approval boundaries, delegation, automation, and agent access to secrets or live execution paths; status `AGENT_SECURITY_APPROVED`, `AGENT_SECURITY_CHANGES_REQUIRED`, or `AGENT_SECURITY_BLOCKED`.
- `triggertrade_security_auditor`: read-only broad application-security audit for explicit/periodic/systemic audit workflows; status `AUDIT_PASS`, `AUDIT_FINDINGS`, or `AUDIT_BLOCKED`; audit status is not commit approval.
- `triggertrade_change_reviewer`: read-only final pre-commit review; status `APPROVED_FOR_COMMIT`, `CHANGES_REQUIRED`, or `BLOCKED`.
- `triggertrade_test_planner`: read-only test planning support; never replaces reviewer approval.

`triggertrade_review_remediation_agent` may make scoped fixes for reviewer findings but cannot approve its own work. Every specialist finding returns to the same originating reviewer after remediation. General change review and tests cannot bypass a required specialist approval.

The remediation agent cannot commit or push on its own. Commit/push, when
explicitly requested by the current task, occurs only through the parent
lifecycle after final `APPROVED_FOR_COMMIT`.

Only `triggertrade_change_reviewer` may emit `APPROVED_FOR_COMMIT`. Specialist
approvals are domain-specific evidence only. Security audit status is advisory
audit evidence, not a normal commit gate. Tests cannot bypass required review,
specialist approval cannot bypass final change review, and final change review
cannot bypass a required specialist reviewer.

For frontend changes, dashboard changes, or backend changes with material user-facing UX/state-presentation impact, insert `triggertrade_ux_reviewer -> remediation if required -> same triggertrade_ux_reviewer re-review` after validation and before change review. UX review is not required for backend-only changes with no material user-facing effect.

For security-relevant development changes, insert `triggertrade_security_change_reviewer` before implementation when planning evidence is available and again after validation against the actual diff. Use `triggertrade_review_remediation_agent` for findings, then return to the same security change reviewer.

For agent definition, permission, sandbox, routing, automation, delegation, approval-boundary, Git-authority, or agent access-to-secrets/live-execution changes, insert `triggertrade_agent_security_reviewer -> remediation if required -> same triggertrade_agent_security_reviewer re-review`.

Use `triggertrade_security_auditor` only for explicit or periodic broad application-security audits and systemic security concerns. Audit status is not commit approval and does not replace change-level reviewers.

Tests are evidence, not reviewer approval.
