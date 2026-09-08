from __future__ import annotations

from pathlib import Path
import tomllib


AGENTS_DIR = Path(".codex/agents")


def _agent_text(name: str) -> str:
    return (AGENTS_DIR / name).read_text(encoding="utf-8")


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
