# TriggerTrade Agent Git Policy Remediation

## 1. Root Cause

The governance conflict was stale or overly broad Git-authority language in agent policy headers. The desired lifecycle allows normal task-scoped Git completion when the current task explicitly requires it, but some agent definitions still treated stage/commit/push as broadly restricted repository mutation rather than normal scoped lifecycle behavior.

No exact remaining file inspected contained the literal sentence "The user performs git staging, commits, and pushes manually." The relevant older semantics were phrases such as read-only reviewers never staging/committing/pushing, automatic stage/commit/push belonging only to the parent lifecycle, and agent-security language grouping Git mutation with restricted actions without separately naming normal scoped Git mutation. Read-only reviewer wording is role-specific and remains valid; the agent-security classification needed sharper separation.

## 2. Files Updated

| File | Why Changed |
|---|---|
| `AGENTS.md` | Made the root Git policy explicit about normal scoped Git operations allowed by task-explicit Git completion, staged-diff inspection, explicit path staging, and still-restricted destructive operations. |
| `.codex/agents/triggertrade-change-lifecycle-orchestrator.toml` | Aligned orchestrator instructions with the same normal scoped Git-completion lifecycle and explicit staging/diff verification requirements. |
| `.codex/agents/triggertrade-review-remediation-agent.toml` | Clarified write-capable remediation behavior: no self-approved Git completion, but task-scoped staging/commit/push discipline applies when parent lifecycle explicitly delegates Git completion authority. |
| `.codex/agents/triggertrade-agent-security-reviewer.toml` | Added `NORMAL_SCOPED_GIT_MUTATION` versus `DESTRUCTIVE_OR_PRIVILEGED_ACTION` classification so normal scoped commit/push is not flagged as a policy violation when gates and task authority are satisfied. |
| `docs/AGENT_GIT_POLICY_REMEDIATION.md` | Records root cause, changed files, sandbox findings, remaining search hits, and acceptance criteria for this governance remediation. |

## 3. Old vs New Semantics

OLD: Git staging, commit, and push were described in places as parent lifecycle behavior, but the policy did not consistently distinguish normal scoped Git completion from destructive or privileged Git mutation. This could lead agents or reviewers to require manual user staging/commit/push even when the current task explicitly requested Git completion and all gates had passed.

NEW: For normal TriggerTrade development tasks, when the current task explicitly requires Git completion, the implementing/orchestrating agent may complete scoped staging, commit, and `git push origin main` after required validation and review gates pass. Destructive/history-rewriting Git operations remain separately restricted.

Read-only reviewers remain read-only. Their role-specific prohibition on staging, committing, pushing, or mutating the repository is not changed.

## 4. Allowed Git Operations

Allowed for the implementing/orchestrating lifecycle only when the current task explicitly requires Git completion and all required gates have passed:

- `git add <explicit task-scoped paths>`
- `git diff --cached --name-only`
- `git diff --cached --check`
- `git diff --cached`
- `git commit -m "<message>"`
- `git push origin main`
- read-only Git commands including `git status`, `git log`, `git rev-parse`, `git diff`, and `git branch --show-current`

The agent must inspect staged paths and staged diff, use the repository commit convention, avoid unrelated changes, and verify branch synchronization plus clean working tree after push.

## 5. Still-Restricted Git Operations

The policy continues to restrict:

- `git commit --amend`
- `git reset`
- `git restore`
- `git clean`
- `git checkout` or `git switch` when they change development state
- `git rebase`
- history rewriting
- force push
- branch deletion
- tag deletion
- destructive cleanup
- reverting unrelated user work
- modifying Git hooks or security controls to bypass policy

These require separate explicit user authorization where allowed at all.

## 6. Reviewer Independence

Reviewer independence is unchanged. Read-only reviewers remain read-only. `triggertrade_review_remediation_agent` may remediate scoped findings but cannot approve its own work. Specialist reviewer cycles still return to the same originating reviewer after remediation. Tests do not replace required reviewer approval. `triggertrade_change_reviewer` remains the final commit gate.

## 7. Sandbox Findings

No sandbox mode was changed.

| Agent | sandbox_mode | Git policy allows normal scoped commit? | Runtime permission likely sufficient? | Change required? |
|---|---|---|---|---|
| `triggertrade_change_lifecycle_orchestrator` | `workspace-write` | YES, after task-explicit Git completion and required gates | UNCLEAR; workspace-write should permit workspace edits, but prior `.git/index.lock` failure indicates possible runtime filesystem restriction outside policy | Policy text updated; sandbox unchanged |
| `triggertrade_review_remediation_agent` | `workspace-write` | Only when explicitly delegated by parent lifecycle; otherwise no | UNCLEAR for same reason | Policy text updated; sandbox unchanged |
| `triggertrade_agent_security_reviewer` | `read-only` | NO; reviewer only classifies/reviews | NO by role | Policy classification updated; sandbox unchanged |
| `triggertrade_change_reviewer` | `read-only` | NO; reviewer emits approval only | NO by role | No change |
| `triggertrade_architecture_reviewer` | `read-only` | NO | NO by role | No change |
| `triggertrade_trading_rules_reviewer` | `read-only` | NO | NO by role | No change |
| `triggertrade_security_change_reviewer` | `read-only` | NO | NO by role | No change |
| `triggertrade_security_auditor` | `read-only` | NO | NO by role | No change |
| `triggertrade_test_planner` | `read-only` | NO | NO by role | No change |
| `triggertrade_ux_reviewer` | `read-only` | NO | NO by role | No change |

No repository agent configuration inspected showed a separate explicit filesystem exclusion for `.git`. The observed `.git/index.lock` permission error is therefore recorded as a runtime/sandbox behavior, not an agent-policy contradiction.

## 8. Acceptance Criteria

- No relevant agent still says the user must always stage/commit/push manually.
- Normal scoped add/commit/push is allowed when the current task explicitly requires Git completion.
- Destructive/history-rewriting operations remain restricted.
- Reviewer independence remains intact.
- No live-trading or secret authority is broadened.
- Agent-security reviewer distinguishes normal scoped Git from destructive Git.
- No contradictory Git policy remains across agent files.

Remaining search-hit explanations after remediation:

- `Never run git add`, `Never run git commit`, and `Never run git push` remain only in read-only reviewer policies such as `triggertrade_ux_reviewer`; these are role-specific and non-contradictory.
- `without direct user request` remains only in user-facing task text or validation searches if present; it is not used as an always-manual Git policy.
- `Git policy` remains as section headings and aligned policy text.
