"""Validate TriggerTrade methodology-source integrity for backend work.

TT-BE-INFRA-008 keeps the approved methodology under docs/trading-methodology/
as the canonical source while preventing implementation-control docs from
quietly treating archived methodology as authoritative.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


CANONICAL_DIR = Path("docs/trading-methodology")
CANONICAL_README = CANONICAL_DIR / "README.md"
ARCHIVE_DIR = Path("docs/archive/trading-methodology-pre-v1.2.14")
CONTROL_DOCS = (
    Path("docs/BACKEND_TARGET_MODEL.md"),
    Path("docs/BACKEND_IMPLEMENTATION_GAP_PLAN.md"),
    Path("docs/BACKEND_IMPLEMENTATION_TRACEABILITY.md"),
)

BASELINE_REVISION_RE = re.compile(r"(?im)^\*\*Package revision:\*\*\s*`([^`]+)`\s*$")
BASELINE_STATUS_RE = re.compile(r"(?im)^\*\*Status:\*\*\s*`IMPLEMENTATION SPECIFICATION BASELINE`\s*$")
BASELINE_APPROVAL_RE = re.compile(r"(?im)^\*\*Approval:\*\*\s*`APPROVED FOR IMPLEMENTATION`\s*$")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
CANONICAL_REF_RE = re.compile(r"^docs/trading-methodology(?:/.*)?$")
CANONICAL_GLOB_CHARS = set("*?[")

NON_NORMATIVE_ARCHIVE_CONTEXT = (
    "ignored",
    "archived",
    "non-normative",
    "non normative",
    "not normative",
    "not authoritative",
    "never authoritative",
    "historical only",
    "not used as normative",
    "not use",
    "do not use",
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: Path | None = None
    line: int | None = None

    def format(self) -> str:
        location = ""
        if self.path is not None:
            location = str(self.path)
            if self.line is not None:
                location = f"{location}:{self.line}"
            location = f"{location}: "
        return f"{self.code}: {location}{self.message}"


@dataclass(frozen=True)
class ValidationResult:
    baseline_revision: str | None
    canonical_references: tuple[Path, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_repository(root: Path) -> ValidationResult:
    root = root.resolve()
    issues: list[ValidationIssue] = []

    baseline_revision = _validate_canonical_baseline(root, issues)
    _validate_archive_context(root, issues)
    references = _validate_canonical_references(root, issues)
    _validate_methodology_worktree_clean(root, issues)

    return ValidationResult(
        baseline_revision=baseline_revision,
        canonical_references=tuple(sorted(references)),
        issues=tuple(issues),
    )


def extract_canonical_references(text: str) -> tuple[str, ...]:
    """Extract explicit canonical repo-relative references from Markdown text.

    Extraction intentionally looks only at Markdown code spans and link
    destinations. It strips section anchors written as " :: ..." so section
    citations resolve to their repository file path without trying to parse
    ordinary prose as a path.
    """

    references: set[str] = set()
    for raw in [*CODE_SPAN_RE.findall(text), *MARKDOWN_LINK_RE.findall(text)]:
        ref = _normalize_reference(raw)
        if ref is not None:
            references.add(ref)
    return tuple(sorted(references))


def is_non_normative_archive_context(line: str) -> bool:
    lowered = line.replace("\\", "/").lower().replace(ARCHIVE_DIR.as_posix().lower(), "")
    return any(marker in lowered for marker in NON_NORMATIVE_ARCHIVE_CONTEXT)


def _validate_canonical_baseline(root: Path, issues: list[ValidationIssue]) -> str | None:
    canonical_dir = root / CANONICAL_DIR
    if not canonical_dir.is_dir():
        issues.append(
            ValidationIssue(
                "CANONICAL_METHODOLOGY_DIR_MISSING",
                "canonical methodology directory is missing",
                CANONICAL_DIR,
            )
        )
        return None

    readme = root / CANONICAL_README
    if not readme.is_file():
        issues.append(
            ValidationIssue(
                "CANONICAL_BASELINE_README_MISSING",
                "canonical methodology README is missing",
                CANONICAL_README,
            )
        )
        return None

    text = _read_text(readme, CANONICAL_README, issues)
    if text is None:
        return None

    revision_match = BASELINE_REVISION_RE.search(text)
    status_match = BASELINE_STATUS_RE.search(text)
    approval_match = BASELINE_APPROVAL_RE.search(text)
    if revision_match is None:
        issues.append(
            ValidationIssue(
                "CANONICAL_BASELINE_MARKER_INVALID",
                "README is missing a package revision baseline marker",
                CANONICAL_README,
            )
        )
    if status_match is None:
        issues.append(
            ValidationIssue(
                "CANONICAL_BASELINE_MARKER_INVALID",
                "README status must identify IMPLEMENTATION SPECIFICATION BASELINE",
                CANONICAL_README,
            )
        )
    if approval_match is None:
        issues.append(
            ValidationIssue(
                "CANONICAL_BASELINE_MARKER_INVALID",
                "README approval must identify APPROVED FOR IMPLEMENTATION",
                CANONICAL_README,
            )
        )
    return revision_match.group(1) if revision_match else None


def _validate_archive_context(root: Path, issues: list[ValidationIssue]) -> None:
    archive_ref = ARCHIVE_DIR.as_posix()
    for doc in CONTROL_DOCS:
        text = _read_text(root / doc, doc, issues)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if archive_ref in line.replace("\\", "/") and not is_non_normative_archive_context(line):
                issues.append(
                    ValidationIssue(
                        "ARCHIVED_METHODOLOGY_USED_NORMATIVELY",
                        f"archive path must be explicitly non-authoritative: {archive_ref}",
                        doc,
                        line_number,
                    )
                )


def _validate_canonical_references(root: Path, issues: list[ValidationIssue]) -> set[Path]:
    references: set[Path] = set()
    for doc in CONTROL_DOCS:
        text = _read_text(root / doc, doc, issues)
        if text is None:
            continue
        for ref in extract_canonical_references(text):
            ref_path = Path(ref)
            references.add(ref_path)
            if any(char in ref for char in CANONICAL_GLOB_CHARS):
                if not list(root.glob(ref)):
                    issues.append(
                        ValidationIssue(
                            "CANONICAL_REFERENCE_MISSING",
                            f"canonical glob reference has no matches: {ref}",
                            doc,
                        )
                    )
                continue
            target = root / ref_path
            if not target.exists():
                issues.append(
                    ValidationIssue(
                        "CANONICAL_REFERENCE_MISSING",
                        f"canonical reference does not resolve: {ref}",
                        doc,
                    )
                )
    return references


def _validate_methodology_worktree_clean(root: Path, issues: list[ValidationIssue]) -> None:
    git_dir = root / ".git"
    if not git_dir.exists():
        return
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", CANONICAL_DIR.as_posix(), ARCHIVE_DIR.as_posix()],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        issues.append(
            ValidationIssue(
                "METHODOLOGY_WORKTREE_STATUS_UNAVAILABLE",
                "unable to inspect methodology worktree status",
            )
        )
        return
    changed_paths = [line for line in result.stdout.splitlines() if line.strip()]
    if changed_paths:
        issues.append(
            ValidationIssue(
                "METHODOLOGY_WORKTREE_MODIFIED",
                "canonical or archived methodology files have uncommitted changes",
            )
        )


def _normalize_reference(raw: str) -> str | None:
    candidate = raw.strip().strip("<>")
    candidate = candidate.split("::", 1)[0].strip()
    candidate = candidate.split("#", 1)[0].strip()
    candidate = candidate.replace("\\", "/")
    if not CANONICAL_REF_RE.match(candidate):
        return None
    return candidate.rstrip("/") if candidate != CANONICAL_DIR.as_posix() + "/" else CANONICAL_DIR.as_posix()


def _read_text(path: Path, display_path: Path, issues: list[ValidationIssue]) -> str | None:
    if not path.is_file():
        issues.append(
            ValidationIssue(
                "CONTROL_DOCUMENT_MISSING",
                "implementation-control document is missing",
                display_path,
            )
        )
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append(
            ValidationIssue(
                "DOCUMENT_READ_FAILED",
                "document is not valid UTF-8",
                display_path,
            )
        )
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TriggerTrade methodology-source integrity.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root to validate")
    args = parser.parse_args(argv)

    result = validate_repository(args.root)
    if result.ok:
        baseline = result.baseline_revision or "unknown"
        print(
            "methodology integrity validation passed "
            f"(baseline={baseline}, canonical_refs={len(result.canonical_references)})"
        )
        return 0

    print("methodology integrity validation failed", file=sys.stderr)
    for issue in result.issues:
        print(issue.format(), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
