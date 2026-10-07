"""CLI bridge for immutable Research V2 hypothesis batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.canonical_json import canonical_json_digest  # noqa: E402
from triggertrade.research_v2_hypotheses import (  # noqa: E402
    RV2_HB001_MANIFEST_PATH,
    build_resolved_research_spec,
    load_rv2_hb001_hypothesis_jobs,
)
from tools.research_v2.run_7d_screen import (  # noqa: E402
    ResearchV2RunnerError,
    read_jsonl,
    run_screen_two_phase,
    validate_dataset,
    write_json,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, help="Frozen Research V2 dataset manifest.")
    parser.add_argument("--manifest", default=RV2_HB001_MANIFEST_PATH, type=Path, help="Hypothesis manifest.")
    parser.add_argument("--hypotheses", required=True, help="Comma-separated hypothesis IDs, e.g. H001,H002.")
    parser.add_argument("--output", required=True, type=Path, help="Deterministic output directory.")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted run in the output directory.")
    parser.add_argument("--resolve-only", action="store_true", help="Write resolved research passports without materializing or replaying.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dataset is None and not args.resolve_only:
        raise ResearchV2RunnerError("--dataset is required unless --resolve-only is used")
    manifest = validate_dataset(args.dataset) if args.dataset is not None else None
    jobs_by_id = load_rv2_hb001_hypothesis_jobs(args.manifest)
    requested = _parse_ids(args.hypotheses)
    missing = [hypothesis_id for hypothesis_id in requested if hypothesis_id not in jobs_by_id]
    if missing:
        raise ResearchV2RunnerError(f"unknown hypothesis IDs: {','.join(missing)}")
    jobs = [jobs_by_id[hypothesis_id] for hypothesis_id in requested]
    args.output.mkdir(parents=True, exist_ok=True)
    dataset_fingerprint = canonical_json_digest(_dataset_identity(manifest)) if manifest is not None else None
    _write_resolved_research_specs(
        jobs=jobs,
        output_dir=args.output,
        dataset_manifest_path=args.dataset,
        dataset_fingerprint=dataset_fingerprint,
    )
    if args.resolve_only:
        return 0
    assert manifest is not None
    write_json(
        args.output / "resolved_hypothesis_identity_pre_run.json",
        {
            "artifact_type": "RESEARCH_V2_HYPOTHESIS_IDENTITIES",
            "dataset_fingerprint": dataset_fingerprint,
            "manifest_path": str(args.manifest),
            "hypotheses": [job.identity_payload(dataset_fingerprint=dataset_fingerprint) for job in jobs],
        },
    )
    completed, total = run_screen_two_phase(manifest=manifest, selected_jobs=jobs, output_dir=args.output, resume=args.resume)
    population_path = args.output / "research_v2_set_population.json"
    population_fingerprint = None
    if population_path.exists():
        population_fingerprint = canonical_json_digest(json.loads(population_path.read_text(encoding="utf-8")))
    _write_resolved_research_specs(
        jobs=jobs,
        output_dir=args.output,
        dataset_manifest_path=args.dataset,
        dataset_fingerprint=dataset_fingerprint,
        population_fingerprint=population_fingerprint,
    )
    write_json(
        args.output / "resolved_hypothesis_identity.json",
        {
            "artifact_type": "RESEARCH_V2_HYPOTHESIS_IDENTITIES",
            "dataset_fingerprint": dataset_fingerprint,
            "population_fingerprint": population_fingerprint,
            "manifest_path": str(args.manifest),
            "hypotheses": [
                job.identity_payload(
                    dataset_fingerprint=dataset_fingerprint,
                    population_fingerprint=population_fingerprint,
                )
                for job in jobs
            ],
            "completed_contexts": completed,
            "total_contexts": total,
            "candidate_census_rows": len(read_jsonl(args.output / "hypothesis_candidate_census.jsonl")),
        },
    )
    return 0


def _parse_ids(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ResearchV2RunnerError("--hypotheses must name at least one hypothesis")
    return values


def _dataset_identity(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": manifest.get("dataset_id"),
        "window": manifest.get("window"),
        "symbols": manifest.get("symbols"),
        "artifacts": manifest.get("artifacts"),
    }


def _write_resolved_research_specs(
    *,
    jobs: Sequence[Any],
    output_dir: Path,
    dataset_manifest_path: Path | None,
    dataset_fingerprint: str | None,
    population_fingerprint: str | None = None,
) -> None:
    for job in jobs:
        hypothesis_dir = output_dir / job.job_id
        hypothesis_dir.mkdir(parents=True, exist_ok=True)
        passport_path = hypothesis_dir / "resolved_research_spec.json"
        passport = build_resolved_research_spec(
            job,
            dataset_manifest=None if dataset_manifest_path is None else str(dataset_manifest_path),
            dataset_fingerprint=dataset_fingerprint,
            population_fingerprint=population_fingerprint,
            output_path=str(hypothesis_dir),
        )
        write_json(passport_path, passport)


if __name__ == "__main__":
    raise SystemExit(main())
