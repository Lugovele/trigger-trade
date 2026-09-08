from __future__ import annotations

from pathlib import Path
import tomllib


AGENTS_DIR = Path(".codex/agents")


def _agent_text(name: str) -> str:
    return (AGENTS_DIR / name).read_text(encoding="utf-8")


def _one_line(text: str) -> str:
    return " ".join(text.split())


def test_all_agent_toml_files_parse():
    for path in sorted(AGENTS_DIR.glob("*.toml")):
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
        assert parsed["name"]
        assert parsed["sandbox_mode"] in {"read-only", "workspace-write"}


def test_only_change_reviewer_declares_commit_approval_status():
    for path in sorted(AGENTS_DIR.glob("*.toml")):
        text = path.read_text(encoding="utf-8")
        if path.name == "triggertrade-change-reviewer.toml":
            assert "- APPROVED_FOR_COMMIT" in text
        else:
            assert "- APPROVED_FOR_COMMIT" not in text


def test_specialist_reviewer_status_vocabularies_are_domain_specific():
    assert "ARCHITECTURE_APPROVED" in _agent_text("triggertrade-architecture-reviewer.toml")
    assert "ARCHITECTURE_BLOCKED" in _agent_text("triggertrade-architecture-reviewer.toml")
    assert "NEXT_LAYER" + "_APPROVED" not in _agent_text("triggertrade-architecture-reviewer.toml")

    trading = _agent_text("triggertrade-trading-rules-reviewer.toml")
    assert "TRADING_RULES_APPROVED" in trading
    assert "TRADING_RULES_CHANGES_REQUIRED" in trading
    assert "TRADING_RULES_BLOCKED" in trading
    assert "TRADING_RULE" + "_CHANGES_REQUIRED" not in trading

    auditor = _agent_text("triggertrade-security-auditor.toml")
    assert "- AUDIT_PASS" in auditor
    assert "- AUDIT_FINDINGS" in auditor
    assert "- AUDIT_BLOCKED" in auditor
    assert "AUDIT_NO_CRITICAL" + "_OR_HIGH_FINDINGS" not in auditor
    assert "AUDIT_FINDINGS" + "_PRESENT" not in auditor
    assert "AUDIT_BLOCKING_RISK" + "_PRESENT" not in auditor
    assert "AUDIT_INCOMPLETE" + "_EVIDENCE" not in auditor


def test_governance_docs_pin_single_commit_gate_and_reviewer_loops():
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = agents_doc + "\n" + lifecycle_doc

    assert "Only `triggertrade_change_reviewer` may emit `APPROVED_FOR_COMMIT`" in combined
    assert "remediation + same specialist re-review" in combined
    assert "remediation + same change reviewer re-review" in combined
    assert "Tests are evidence. Tests do not replace reviewer approval." in combined
    assert "AUDIT_PASS" in combined


def test_lifecycle_auto_commits_only_when_task_explicitly_requests_it():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    remediation = _agent_text("triggertrade-review-remediation-agent.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, remediation, agents_doc, lifecycle_doc])

    assert "explicitly requested commit/push" in combined
    assert "No extra user confirmation is required" in combined
    assert "stop at APPROVED_FOR_COMMIT" in combined
    assert "no commit or no push" in combined
    assert "stage only files" in combined.lower()
    assert "belonging to the current" in combined.lower()
    assert "git diff --cached --name-only" in combined
    assert "The remediation agent cannot commit or push on its own" in combined


def test_explicit_consequential_scope_does_not_require_duplicate_consent():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    security = _agent_text("triggertrade-security-change-reviewer.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, security, agents_doc, lifecycle_doc])

    assert "SCOPE_AUTHORIZED" in orchestrator
    assert "GIT_AUTHORIZED" in orchestrator
    assert "Explicit task scope is authorization for the consequential behavior it clearly describes." in _one_line(agents_doc)
    assert "Consequential nature alone does not require a second confirmation after review." in _one_line(agents_doc)
    assert "Do not request duplicate consent" in orchestrator
    assert "Do not reinterpret an already explicit user request as missing consent" in _one_line(security)
    assert "Daily Loss gate on new entries" in lifecycle_doc
    assert "APPROVED_FOR_COMMIT -> AUTO_COMMIT_PUSH" in orchestrator


def test_new_out_of_scope_consequential_effect_requires_stop_and_user_approval():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, agents_doc, lifecycle_doc])

    assert "NEW_CONSEQUENTIAL_SCOPE_DISCOVERED" in orchestrator
    assert "USER_APPROVAL_REQUIRED" in orchestrator
    assert "new material consequence outside authorized scope -> stop -> user confirmation" in agents_doc
    assert "continue only after approval" in lifecycle_doc
    assert "automatic closing of existing positions" in _one_line(lifecycle_doc)
    assert "mainnet enablement" in lifecycle_doc


def test_explicit_do_not_commit_override_stops_after_final_approval():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, agents_doc, lifecycle_doc])

    assert "do not commit" in combined
    assert "that override wins" in combined
    assert "stop at `APPROVED_FOR_COMMIT`" in combined


def test_explicit_do_not_push_override_permits_only_authorized_git_tail():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, agents_doc, lifecycle_doc])

    assert "do not push" in combined
    assert "GIT_AUTHORIZED means the same current lifecycle task explicitly requested commit" in orchestrator
    assert "and/or push" in orchestrator
    assert "that override wins" in combined


def test_specialist_approval_without_final_change_approval_cannot_commit():
    orchestrator = _agent_text("triggertrade-change-lifecycle-orchestrator.toml")
    change_reviewer = _agent_text("triggertrade-change-reviewer.toml")
    agents_doc = Path("AGENTS.md").read_text(encoding="utf-8")
    lifecycle_doc = Path("docs/development-lifecycle.md").read_text(encoding="utf-8")
    combined = "\n".join([orchestrator, change_reviewer, agents_doc, lifecycle_doc])

    assert "Only `triggertrade_change_reviewer` may emit `APPROVED_FOR_COMMIT`" in combined
    assert "Specialist" in agents_doc
    assert "is not standalone permission to commit" in orchestrator
    assert "triggertrade_change_reviewer returns exactly\nAPPROVED_FOR_COMMIT" in orchestrator


def test_stale_manual_commit_policy_is_removed_from_active_contracts():
    active_text = "\n".join(
        [
            *(path.read_text(encoding="utf-8") for path in sorted(AGENTS_DIR.glob("*.toml"))),
            Path("AGENTS.md").read_text(encoding="utf-8"),
            Path("docs/development-lifecycle.md").read_text(encoding="utf-8"),
        ]
    )

    stale_phrases = [
        "APPROVED_FOR_COMMIT" + "_PENDING_USER_COMMIT",
        "The user performs git staging, commits, and pushes " + "manually",
        "The user performs staging, commits, and pushes " + "manually",
        "user performs git " + "manually",
        "manual commit " + "required",
        "wait for user to " + "commit",
        "Do not automatically stage, commit, " + "push",
    ]
    for phrase in stale_phrases:
        assert phrase not in active_text
