"""Generate the identity-locked V2_GPT6PRO historical label corpus."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from tools.direction_labels.v2_gpt6pro_contract import (
    ARCHITECTURE_SHA256, CANONICAL_CONFIG, CANONICAL_PROTOCOL_ID,
    CANONICAL_RELEASE_ID, CANONICAL_STATUS, CONFIGURATION_SHA256, ContractError,
    EXPECTED_SOURCE_HASHES, FREEZE_AMENDMENT_SHA256, HARNESS_SHA256, HORIZONS, LOGICAL_BY_PHYSICAL,
    RMS48_RETURN_COUNT, RMS48_RETURN_SPACING_MINUTES,
    SORTED_PHYSICAL_SYMBOLS, SOURCE_IDENTITY, assert_canonical_horizons,
    calculation_version, canonical_output_root, canonicalize_harness_result,
    environment_identity, prepare_run_paths, repository_root, sha256_file,
    validate_source_frame, verify_file_hash, verify_release_lock, verify_source_identity,
    write_output_hashes,
)
from tools.research_v2.v2_research_harness import ResearchConfig, evaluate_from_minute_arrays


GENERATOR_PATH = Path(__file__).resolve()
VALIDATOR_PATH = GENERATOR_PATH.with_name("validate_v2_gpt6pro_canonical.py")
CONTRACT_PATH = GENERATOR_PATH.with_name("v2_gpt6pro_contract.py")
CHUNK_ORIGINS = 512


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the frozen V2_GPT6PRO canonical historical labels. No semantic overrides exist.")
    parser.add_argument(
        "--timestamp",
        help="Unique UTC run suffix (YYYYMMDDTHHMMSSZ). Defaults to the current UTC time.",
    )
    return parser


def evaluate_horizons_independently(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    origin_index: int,
    origin_utc: str,
    config: ResearchConfig,
    evaluator: Callable[..., dict[str, Any]] = evaluate_from_minute_arrays,
) -> dict[int, dict[str, Any]]:
    assert_canonical_horizons(HORIZONS)
    return {
        horizon: evaluator(closes, origin_index, config, horizon, highs=highs, lows=lows,
                           origin_utc=origin_utc)
        for horizon in HORIZONS
    }


def _identity_fields(calculation_id: str) -> dict[str, str]:
    return {
        "configuration_sha256": CONFIGURATION_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "freeze_amendment_sha256": FREEZE_AMENDMENT_SHA256,
        "harness_sha256": HARNESS_SHA256,
        "source_identity": SOURCE_IDENTITY,
        "canonical_protocol_id": CANONICAL_PROTOCOL_ID,
        "canonical_release_id": CANONICAL_RELEASE_ID,
        "calculation_version": calculation_id,
    }


def canonical_origin_indices(row_count: int) -> range:
    """Return the fixed ascending five-minute origin grid for a one-minute source."""
    return range(4, row_count, 5)


def _diagnostic_row(physical: str, logical: str, origin: str, horizon: int,
                    label: str | None, status: str, reasons: str,
                    result: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "symbol": logical, "physical_symbol": physical, "origin_utc": origin,
        "horizon_minutes": horizon, "label": label, "status": status,
        "reason_codes_json": reasons,
        "p0": result.get("p0"), "rms48": result.get("rms48"), "s_H": result.get("s_h"),
        "p_N": result.get("p_N"), "w_N": result.get("w_N"),
    }
    sides = result.get("sides") or {}
    for side_name in ("LONG", "SHORT"):
        prefix = side_name.lower()
        side = sides.get(side_name) or {}
        predicates = list((side.get("predicates") or {}).values())
        row[f"{prefix}_passes"] = side.get("passes")
        row[f"{prefix}_material_phase_exists"] = bool(side.get("B", 0) >= 1 - 1e-12) if side else None
        row[f"{prefix}_opposing_phase_exists"] = side.get("opposing_phase")
        for index in range(6):
            row[f"{prefix}_predicate_{index + 1}"] = predicates[index] if len(predicates) == 6 else None
    return row


def _write_table(writer: pq.ParquetWriter | None, path: Path, rows: list[dict[str, Any]]) -> pq.ParquetWriter:
    table = pa.Table.from_pylist(rows)
    if writer is None:
        writer = pq.ParquetWriter(path, table.schema, compression="zstd")
    writer.write_table(table)
    return writer


def _read_authenticated_symbol(path: Path, physical_symbol: str) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        compression="gzip",
        dtype={"symbol": "string", "logical_symbol": "string", "category": "string", "timeframe": "string"},
    )
    return validate_source_frame(frame, physical_symbol)


def _generate_payload(staging: Path, source_paths: Mapping[str, Path], calculation_id: str,
                      config: ResearchConfig) -> dict[str, Any]:
    horizon_paths = {h: staging / f"canonical_labels_{h}m.parquet" for h in HORIZONS}
    wide_path = staging / "canonical_labels.parquet"
    diagnostics_path = staging / "canonical_diagnostics.parquet"
    unavailable_path = staging / "canonical_unavailable_rows.csv"
    writers: dict[str, pq.ParquetWriter | None] = {"wide": None, "diagnostics": None, "60": None, "120": None}
    counts: dict[int, Counter[str]] = {h: Counter() for h in HORIZONS}
    symbol_counts: dict[tuple[int, str], Counter[str]] = defaultdict(Counter)
    identity = _identity_fields(calculation_id)
    with unavailable_path.open("w", encoding="utf-8", newline="") as unavailable_file:
        unavailable = csv.DictWriter(unavailable_file, fieldnames=[
            "symbol", "physical_symbol", "origin_utc", "horizon_minutes", "status", "reason_codes_json"])
        unavailable.writeheader()
        try:
            for physical in SORTED_PHYSICAL_SYMBOLS:
                logical = LOGICAL_BY_PHYSICAL[physical]
                frame = _read_authenticated_symbol(source_paths[physical], physical)
                closes = frame["close"].to_numpy(np.float64)
                highs = frame["high"].to_numpy(np.float64)
                lows = frame["low"].to_numpy(np.float64)
                close_times = frame["close_time"]
                wide_rows: list[dict[str, Any]] = []
                horizon_rows: dict[int, list[dict[str, Any]]] = {h: [] for h in HORIZONS}
                diagnostic_rows: list[dict[str, Any]] = []
                for origin_index in canonical_origin_indices(len(frame)):
                    origin = close_times.iloc[origin_index].strftime("%Y-%m-%dT%H:%M:%SZ")
                    results = evaluate_horizons_independently(
                        closes, highs, lows, origin_index, origin, config)
                    wide = {"symbol": logical, "physical_symbol": physical, "origin_utc": origin, **identity}
                    for horizon in HORIZONS:
                        result = results[horizon]
                        label, status, reasons = canonicalize_harness_result(result)
                        wide[f"label_{horizon}m"] = label
                        wide[f"status_{horizon}m"] = status
                        wide[f"reason_codes_{horizon}m"] = reasons
                        row = {
                            "symbol": logical, "physical_symbol": physical, "origin_utc": origin,
                            "horizon_minutes": horizon, "label": label, "status": status,
                            "reason_codes_json": reasons, **identity,
                        }
                        horizon_rows[horizon].append(row)
                        diagnostic_rows.append(_diagnostic_row(
                            physical, logical, origin, horizon, label, status, reasons, result))
                        bucket = label if status == "VALID" else "UNAVAILABLE"
                        counts[horizon][bucket] += 1
                        symbol_counts[(horizon, physical)][bucket] += 1
                        if status == "VALID":
                            counts[horizon]["VALID"] += 1
                            symbol_counts[(horizon, physical)]["VALID"] += 1
                        if status != "VALID":
                            unavailable.writerow({
                                "symbol": logical, "physical_symbol": physical, "origin_utc": origin,
                                "horizon_minutes": horizon, "status": status, "reason_codes_json": reasons,
                            })
                    wide_rows.append(wide)
                    if len(wide_rows) >= CHUNK_ORIGINS:
                        writers["wide"] = _write_table(writers["wide"], wide_path, wide_rows)
                        writers["diagnostics"] = _write_table(
                            writers["diagnostics"], diagnostics_path, diagnostic_rows)
                        for horizon in HORIZONS:
                            key = str(horizon)
                            writers[key] = _write_table(writers[key], horizon_paths[horizon], horizon_rows[horizon])
                            horizon_rows[horizon].clear()
                        wide_rows.clear()
                        diagnostic_rows.clear()
                if wide_rows:
                    writers["wide"] = _write_table(writers["wide"], wide_path, wide_rows)
                    writers["diagnostics"] = _write_table(writers["diagnostics"], diagnostics_path, diagnostic_rows)
                    for horizon in HORIZONS:
                        key = str(horizon)
                        writers[key] = _write_table(writers[key], horizon_paths[horizon], horizon_rows[horizon])
                print(json.dumps({"completed_symbol": physical,
                                  "origins": len(canonical_origin_indices(len(frame)))}), flush=True)
                del frame, closes, highs, lows
        finally:
            for writer in writers.values():
                if writer is not None:
                    writer.close()
    summary_path = staging / "canonical_generation_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        fields = ["horizon_minutes", "physical_symbol", "total", "valid", "unavailable",
                  "long_favored", "short_favored", "no_direction"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for horizon in HORIZONS:
            for physical in (*SORTED_PHYSICAL_SYMBOLS, "ALL"):
                counter = counts[horizon] if physical == "ALL" else symbol_counts[(horizon, physical)]
                writer.writerow({
                    "horizon_minutes": horizon, "physical_symbol": physical,
                    "total": counter["VALID"] + counter["UNAVAILABLE"], "valid": counter["VALID"],
                    "unavailable": counter["UNAVAILABLE"], "long_favored": counter["LONG_FAVORED"],
                    "short_favored": counter["SHORT_FAVORED"], "no_direction": counter["NO_DIRECTION"],
                })
    return {
        "counts": {str(h): dict(counts[h]) for h in HORIZONS},
        "symbol_counts": {f"{h}:{s}": dict(c) for (h, s), c in sorted(symbol_counts.items())},
    }


def build_generation_manifest(
    *, timestamp: str, environment: Mapping[str, str], calculation_id: str,
    source_manifest_sha256: str, source_hashes: Mapping[str, str],
    payload_hashes: Mapping[str, str], statistics: Mapping[str, Any],
    generation_command: str, release_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "run_id": timestamp,
        "run_timestamp_utc": datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "canonical_protocol_id": CANONICAL_PROTOCOL_ID,
        "canonical_release_id": CANONICAL_RELEASE_ID,
        "status": CANONICAL_STATUS,
        "configuration_identity": {"strings": CANONICAL_CONFIG, "sha256": CONFIGURATION_SHA256},
        "architecture_identity": {"sha256": ARCHITECTURE_SHA256},
        "freeze_identity": {"sha256": FREEZE_AMENDMENT_SHA256},
        "harness_identity": {"sha256": HARNESS_SHA256},
        "source_identity": {"corpus_id": SOURCE_IDENTITY, "manifest_sha256": source_manifest_sha256},
        "canonical_horizons_minutes": list(HORIZONS),
        "horizon_relationship": "INDEPENDENT",
        "rms48_contract": {"return_count": RMS48_RETURN_COUNT,
                           "return_spacing_minutes": RMS48_RETURN_SPACING_MINUTES},
        "calculation_environment": dict(environment),
        "calculation_version": calculation_id,
        "input_file_hashes": dict(source_hashes),
        "output_file_hashes": dict(payload_hashes),
        "row_counts": dict(statistics),
        "generation_command": generation_command,
        "generator_source_sha256": environment["generator_source_sha256"],
        "validator_source_sha256": environment["validator_source_sha256"],
        "contract_source_sha256": environment["contract_source_sha256"],
        "deterministic_sort": "physical_symbol lexical ascending, then origin_utc ascending",
        "release_manifest_sha256": release_manifest_sha256,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    timestamp = args.timestamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = repository_root()
    assert_canonical_horizons(HORIZONS)
    verify_release_lock(root)
    _, source_paths = verify_source_identity(root)
    config = ResearchConfig.from_explicit(CANONICAL_CONFIG)
    if config.config_hash != CONFIGURATION_SHA256 or dict(config.exact) != CANONICAL_CONFIG:
        raise ContractError("frozen harness configuration identity mismatch")
    generator_hash = sha256_file(GENERATOR_PATH)
    validator_hash = sha256_file(VALIDATOR_PATH)
    contract_hash = sha256_file(CONTRACT_PATH)
    environment = environment_identity(generator_hash, validator_hash, contract_hash)
    calculation_id = calculation_version(environment)
    staging, target = prepare_run_paths(canonical_output_root(root), timestamp)
    try:
        statistics = _generate_payload(staging, source_paths, calculation_id, config)
        data_files = ["canonical_labels.parquet", "canonical_labels_60m.parquet",
                      "canonical_labels_120m.parquet", "canonical_diagnostics.parquet",
                      "canonical_generation_summary.csv", "canonical_unavailable_rows.csv"]
        payload_hashes = {name: sha256_file(staging / name) for name in data_files}
        manifest = build_generation_manifest(
            timestamp=timestamp, environment=environment, calculation_id=calculation_id,
            source_manifest_sha256=sha256_file(root / "runtime/data/direction-regime-history/manifest.json"),
            source_hashes={symbol: sha256_file(path) for symbol, path in source_paths.items()},
            payload_hashes=payload_hashes, statistics=statistics,
            generation_command=" ".join([
                shlex.quote(sys.executable), "-m", "tools.direction_labels.generate_v2_gpt6pro_canonical",
                *(shlex.quote(value) for value in sys.argv[1:]),
            ]),
            release_manifest_sha256=sha256_file(
                root / "runtime/audit" / CANONICAL_RELEASE_ID / "CANONICAL_RELEASE_MANIFEST.json"),
        )
        (staging / "canonical_generation_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (staging / "canonical_generation_validation.md").write_text(
            "# Canonical generation validation\n\nStatus: NOT_RUN\n", encoding="utf-8")
        write_output_hashes(staging)
        for symbol, path in source_paths.items():
            verify_file_hash(path, EXPECTED_SOURCE_HASHES[symbol], f"{symbol} source file after generation")
        os.replace(staging, target)
        from tools.direction_labels.validate_v2_gpt6pro_canonical import validate_run
        try:
            validate_run(target, write_report=True)
        except Exception:
            failed = target.parent / f".failed-{timestamp}-{os.getpid()}"
            os.replace(target, failed)
            raise
    except Exception:
        raise
    print(str(target.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

