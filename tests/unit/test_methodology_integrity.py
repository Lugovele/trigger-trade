from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.validate_methodology_integrity import (
    ARCHIVE_DIR,
    CANONICAL_DIR,
    CANONICAL_README,
    CONTROL_DOCS,
    extract_canonical_references,
    is_non_normative_archive_context,
    validate_repository,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_current_repository_methodology_integrity_passes():
    result = validate_repository(REPO_ROOT)

    assert result.ok, [issue.format() for issue in result.issues]
    assert result.baseline_revision == "v1.2.14"
    assert CANONICAL_README in result.canonical_references


def test_missing_canonical_methodology_reference_is_detected():
    with _workspace_temp_dir() as tmp:
        repo = _minimal_repo(tmp)
        (repo / CONTROL_DOCS[0]).write_text(
            "Source: `docs/trading-methodology/methodology/MISSING.md :: §1`\n",
            encoding="utf-8",
        )

        result = validate_repository(repo)

    assert not result.ok
    assert _issue_codes(result) >= {"CANONICAL_REFERENCE_MISSING"}


def test_normative_archived_methodology_reference_is_rejected():
    with _workspace_temp_dir() as tmp:
        repo = _minimal_repo(tmp)
        (repo / CONTROL_DOCS[0]).write_text(
            f"Canonical source: `{ARCHIVE_DIR.as_posix()}/README.md`\n",
            encoding="utf-8",
        )

        result = validate_repository(repo)

    assert not result.ok
    assert _issue_codes(result) >= {"ARCHIVED_METHODOLOGY_USED_NORMATIVELY"}


def test_normative_windows_style_archived_methodology_reference_is_rejected():
    with _workspace_temp_dir() as tmp:
        repo = _minimal_repo(tmp)
        (repo / CONTROL_DOCS[0]).write_text(
            r"Canonical source: `docs\archive\trading-methodology-pre-v1.2.14\README.md`" + "\n",
            encoding="utf-8",
        )

        result = validate_repository(repo)

    assert not result.ok
    assert _issue_codes(result) >= {"ARCHIVED_METHODOLOGY_USED_NORMATIVELY"}


def test_positive_archive_source_wording_is_rejected():
    with _workspace_temp_dir() as tmp:
        repo = _minimal_repo(tmp)
        (repo / CONTROL_DOCS[0]).write_text(
            f"Canonical archive source: `{ARCHIVE_DIR.as_posix()}/README.md`\n",
            encoding="utf-8",
        )

        result = validate_repository(repo)

    assert not result.ok
    assert _issue_codes(result) >= {"ARCHIVED_METHODOLOGY_USED_NORMATIVELY"}


@pytest.mark.parametrize(
    "line",
    [
        f"Archived methodology `{ARCHIVE_DIR.as_posix()}/README.md` is historical only.",
        f"Do not use `{ARCHIVE_DIR.as_posix()}/README.md` as normative evidence.",
        f"`{ARCHIVE_DIR.as_posix()}/README.md` is non-normative.",
    ],
)
def test_explicitly_non_normative_archive_warning_is_allowed(line):
    with _workspace_temp_dir() as tmp:
        repo = _minimal_repo(tmp)
        (repo / CONTROL_DOCS[0]).write_text(line + "\n", encoding="utf-8")

        result = validate_repository(repo)

    assert result.ok, [issue.format() for issue in result.issues]
    assert is_non_normative_archive_context(line)


def test_canonical_reference_extraction_is_deterministic():
    text = """
    Source: `docs/trading-methodology/methodology/SET.md :: §2`.
    Repeated: `docs/trading-methodology/methodology/SET.md :: §2`.
    Link: [schemas](docs/trading-methodology/schemas/README.md#schema-package)
    Prose mention docs/trading-methodology/methodology/IGNORED.md is not extracted.
    Archive: `docs/archive/trading-methodology-pre-v1.2.14/README.md`.
    """

    assert extract_canonical_references(text) == (
        "docs/trading-methodology/methodology/SET.md",
        "docs/trading-methodology/schemas/README.md",
    )


def _minimal_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / CANONICAL_DIR / "methodology").mkdir(parents=True)
    (repo / CANONICAL_DIR / "schemas").mkdir(parents=True)
    (repo / CANONICAL_README).write_text(
        "# TriggerTrade - Active Specification Documentation v1.2.14\n\n"
        "**Package revision:** `v1.2.14`\n"
        "**Status:** `IMPLEMENTATION SPECIFICATION BASELINE`\n"
        "**Approval:** `APPROVED FOR IMPLEMENTATION`\n",
        encoding="utf-8",
    )
    (repo / CANONICAL_DIR / "methodology" / "SET.md").write_text("set\n", encoding="utf-8")
    (repo / CANONICAL_DIR / "schemas" / "README.md").write_text("schemas\n", encoding="utf-8")
    for doc in CONTROL_DOCS:
        (repo / doc).parent.mkdir(parents=True, exist_ok=True)
        (repo / doc).write_text(
            "Source: `docs/trading-methodology/README.md :: IMPLEMENTATION SPECIFICATION BASELINE`\n",
            encoding="utf-8",
        )
    archive = repo / ARCHIVE_DIR
    archive.mkdir(parents=True)
    (archive / "README.md").write_text("archived\n", encoding="utf-8")
    return repo


@contextmanager
def _workspace_temp_dir():
    root = REPO_ROOT / "pytest_methodology_cases"
    root.mkdir(exist_ok=True)
    case_dir = root / uuid.uuid4().hex
    case_dir.mkdir()
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)
        try:
            root.rmdir()
        except OSError:
            pass


def _issue_codes(result) -> set[str]:
    return {issue.code for issue in result.issues}
