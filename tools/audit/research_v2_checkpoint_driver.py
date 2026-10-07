from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_DATASET = Path("runtime/data/research-v2/7d_20260819_20260826/dataset_manifest.json")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Research V2 J0-J7 checkpointed shell replay.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jobs", default="ALL", help="Comma-separated job IDs or ALL")
    parser.add_argument("--population", type=Path, default=None, help="Existing materialized Research V2 Set population")
    parser.add_argument("--replay-only", action="store_true", help="Skip materialization and replay an existing population")
    parser.add_argument(
        "--finalize-existing",
        action="store_true",
        help="Evidence-only finalization for an already completed run; does not replay trading decisions",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def run_research_v2_checkpoint_driver(
    *,
    output_dir: Path,
    dataset: Path = DEFAULT_DATASET,
    jobs: str = "ALL",
    limit: int | None = None,
    resume: bool = False,
    population: Path | None = None,
    replay_only: bool = False,
    finalize_existing: bool = False,
    executor=None,
) -> dict[str, object]:
    repo = _repo_root()
    sys.path.insert(0, str(repo / "src"))
    from tools.research_v2.run_7d_screen import finalize_research_v2_existing_run, run_screen

    dataset_path = dataset if dataset.is_absolute() else repo / dataset
    output_path = output_dir if output_dir.is_absolute() else repo / output_dir
    if finalize_existing:
        if executor is not None:
            raise ValueError("--finalize-existing cannot use an injected replay executor")
        result = finalize_research_v2_existing_run(output_dir=output_path, dataset_path=dataset_path, jobs_arg=jobs)
        completed = int(result.get("contexts") or 0)
        total = completed
        payload = _summary_payload(
            output_dir=output_path,
            dataset_path=dataset_path,
            jobs=jobs,
            completed=completed,
            total=total,
        )
        payload.update(result)
        payload["status"] = "COMPLETE"
        return payload
    completed, total = run_screen(
        dataset_path=dataset_path,
        output_dir=output_path,
        jobs_arg=jobs,
        resume=resume,
        max_jobs=limit,
        population_path=population,
        replay_only=replay_only,
        executor=executor,
    )
    return _summary_payload(
        output_dir=output_path,
        dataset_path=dataset_path,
        jobs=jobs,
        completed=completed,
        total=total,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_research_v2_checkpoint_driver(
        output_dir=args.output_dir,
        dataset=args.dataset,
        jobs=args.jobs,
        limit=args.limit,
        resume=args.resume,
        population=args.population,
        replay_only=args.replay_only,
        finalize_existing=args.finalize_existing,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if int(summary["errors"]) == 0 else 30


def _summary_payload(
    *,
    output_dir: Path,
    dataset_path: Path,
    jobs: str,
    completed: int,
    total: int,
) -> dict[str, object]:
    errors_path = output_dir / "job_errors.jsonl"
    results_path = output_dir / "job_results.jsonl"
    summary_path = output_dir / "screen_summary.json"
    return {
        "status": "COMPLETE" if completed == total else "INCOMPLETE",
        "dataset_manifest": str(dataset_path),
        "output_dir": str(output_dir),
        "jobs": jobs,
        "completed": completed,
        "total": total,
        "errors": _count_jsonl(errors_path),
        "checkpoint_results_path": str(results_path),
        "checkpoint_errors_path": str(errors_path),
        "summary_path": str(summary_path),
    }


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


if __name__ == "__main__":
    raise SystemExit(main())
