"""Validate an existing V2_GPT6PRO canonical label run without regeneration."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Mapping

import pyarrow.parquet as pq

from tools.direction_labels.v2_gpt6pro_contract import (
    ALLOWED_LABELS, ARCHITECTURE_SHA256, CANONICAL_CONFIG, CANONICAL_PROTOCOL_ID,
    CANONICAL_RELEASE_ID, CANONICAL_STATUS, CONFIGURATION_SHA256, ContractError,
    EXPECTED_COUNTS, EXPECTED_SOURCE_HASHES, EXPECTED_TOTAL_ORIGINS,
    FREEZE_AMENDMENT_SHA256, HARNESS_SHA256, HORIZONS, LOGICAL_BY_PHYSICAL,
    SORTED_PHYSICAL_SYMBOLS, SOURCE_IDENTITY,
    SOURCE_MANIFEST_SHA256, calculation_version, canonical_output_root,
    environment_identity, repository_root, sha256_file, verify_release_lock,
    verify_source_identity, write_output_hashes,
)


PAYLOAD_FILES = frozenset({
    "canonical_labels.parquet", "canonical_labels_60m.parquet",
    "canonical_labels_120m.parquet", "canonical_diagnostics.parquet",
    "canonical_generation_summary.csv", "canonical_unavailable_rows.csv",
})
REQUIRED_FILES = PAYLOAD_FILES | {
    "canonical_generation_manifest.json", "canonical_output_hashes.json",
    "canonical_generation_validation.md",
}
IDENTITY_COLUMNS = {
    "configuration_sha256": CONFIGURATION_SHA256,
    "architecture_sha256": ARCHITECTURE_SHA256,
    "freeze_amendment_sha256": FREEZE_AMENDMENT_SHA256,
    "harness_sha256": HARNESS_SHA256,
    "source_identity": SOURCE_IDENTITY,
    "canonical_protocol_id": CANONICAL_PROTOCOL_ID,
    "canonical_release_id": CANONICAL_RELEASE_ID,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a generated V2_GPT6PRO canonical run.")
    parser.add_argument("run_directory", type=Path)
    return parser


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _iter_parquet_rows(path: Path, columns: list[str]) -> Iterator[dict[str, Any]]:
    parquet = pq.ParquetFile(path)
    _require(set(columns) <= set(parquet.schema_arrow.names), f"{path.name} schema incomplete")
    for batch in parquet.iter_batches(columns=columns, batch_size=65_536):
        data = batch.to_pydict()
        for index in range(batch.num_rows):
            yield {column: data[column][index] for column in columns}


FIRST_ORIGIN_UTC = datetime(2024, 9, 30, 7, 25, tzinfo=UTC)
ORIGINS_PER_SYMBOL = EXPECTED_TOTAL_ORIGINS // len(SORTED_PHYSICAL_SYMBOLS)


def expected_origin_utc(position: int) -> str:
    return (FIRST_ORIGIN_UTC + timedelta(minutes=5 * position)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_horizon_file(
    path: Path, horizon: int, expected_calculation_version: str,
) -> tuple[Counter[str], dict[str, Counter[str]], int]:
    columns = ["symbol", "physical_symbol", "origin_utc", "horizon_minutes", "label", "status",
               "reason_codes_json", *IDENTITY_COLUMNS, "calculation_version"]
    counts: Counter[str] = Counter()
    symbol_counts: dict[str, Counter[str]] = defaultdict(Counter)
    previous: tuple[str, str] | None = None
    positions: Counter[str] = Counter()
    rows = 0
    for row in _iter_parquet_rows(path, columns):
        key = (row["physical_symbol"], row["origin_utc"])
        _require(previous is None or key > previous, f"{path.name} is not strictly sorted/unique")
        previous = key
        physical = row["physical_symbol"]
        _require(physical in SORTED_PHYSICAL_SYMBOLS, f"{path.name} unsupported physical symbol")
        _require(row["symbol"] == LOGICAL_BY_PHYSICAL[physical], f"{path.name} logical symbol mismatch")
        position = positions[physical]
        _require(position < ORIGINS_PER_SYMBOL, f"{path.name} excess origins for {physical}")
        _require(row["origin_utc"] == expected_origin_utc(position),
                 f"{path.name} origin grid mismatch for {physical} at position {position}")
        positions[physical] += 1
        _require(row["horizon_minutes"] == horizon, f"{path.name} horizon mismatch")
        status, label = row["status"], row["label"]
        if status == "VALID":
            _require(label in ALLOWED_LABELS, f"{path.name} invalid canonical label")
            _require(row["reason_codes_json"] == "[]", f"{path.name} valid row has reasons")
            counts["VALID"] += 1
            counts[label] += 1
            symbol_counts[row["physical_symbol"]]["VALID"] += 1
            symbol_counts[row["physical_symbol"]][label] += 1
        else:
            _require(status == "UNAVAILABLE" and label is None,
                     f"{path.name} unavailable is not distinct from NO_DIRECTION")
            _require(row["reason_codes_json"] != "[]", f"{path.name} unavailable reason missing")
            counts["UNAVAILABLE"] += 1
            symbol_counts[row["physical_symbol"]]["UNAVAILABLE"] += 1
        for column, expected in IDENTITY_COLUMNS.items():
            _require(row[column] == expected, f"{path.name} {column} mismatch")
        _require(row["calculation_version"] == expected_calculation_version,
                 f"{path.name} calculation version mismatch")
        rows += 1
    _require(rows == EXPECTED_TOTAL_ORIGINS, f"{path.name} row count mismatch")
    _require(set(positions) == set(SORTED_PHYSICAL_SYMBOLS) and
             all(positions[symbol] == ORIGINS_PER_SYMBOL for symbol in SORTED_PHYSICAL_SYMBOLS),
             f"{path.name} physical-symbol population mismatch")
    _require(dict(counts) == EXPECTED_COUNTS[horizon],
             f"{path.name} conformance counts mismatch: {dict(counts)}")
    return counts, dict(symbol_counts), rows


def _validate_diagnostic_semantics(row: Mapping[str, Any]) -> None:
    if row["status"] != "VALID":
        return
    long_passes, short_passes = row["long_passes"], row["short_passes"]
    _require(not (long_passes and short_passes), "dual-direction row found")
    expected = "LONG_FAVORED" if long_passes else "SHORT_FAVORED" if short_passes else "NO_DIRECTION"
    _require(row["label"] == expected, "label does not match predicate conjunction")
    _require(row["long_predicate_4"] == (not row["long_opposing_phase_exists"]),
             "LONG P4 Boolean semantics mismatch")
    _require(row["short_predicate_4"] == (not row["short_opposing_phase_exists"]),
             "SHORT P4 Boolean semantics mismatch")
    _require(row["long_opposing_phase_exists"] == row["short_material_phase_exists"],
             "LONG opposing phase linkage mismatch")
    _require(row["short_opposing_phase_exists"] == row["long_material_phase_exists"],
             "SHORT opposing phase linkage mismatch")


def _next_or_fail(iterator: Iterator[dict[str, Any]], description: str) -> dict[str, Any]:
    try:
        return next(iterator)
    except StopIteration as error:
        raise ContractError(f"{description} ended before canonical_labels.parquet") from error


def _require_exhausted(iterator: Iterator[Any], description: str) -> None:
    try:
        next(iterator)
    except StopIteration:
        return
    raise ContractError(f"{description} has extra rows")


def _reconcile_outputs(run: Path, expected_calculation_version: str) -> None:
    wide_columns = ["symbol", "physical_symbol", "origin_utc",
                    "label_60m", "status_60m", "reason_codes_60m",
                    "label_120m", "status_120m", "reason_codes_120m",
                    *IDENTITY_COLUMNS, "calculation_version"]
    horizon_columns = ["symbol", "physical_symbol", "origin_utc", "horizon_minutes",
                       "label", "status", "reason_codes_json"]
    diagnostic_columns = ["symbol", "physical_symbol", "origin_utc", "horizon_minutes",
                          "label", "status", "reason_codes_json", "long_passes", "short_passes",
                          "long_material_phase_exists", "short_material_phase_exists",
                          "long_opposing_phase_exists", "short_opposing_phase_exists",
                          "long_predicate_4", "short_predicate_4"]
    wide_iter = _iter_parquet_rows(run / "canonical_labels.parquet", wide_columns)
    horizon_iters = {h: _iter_parquet_rows(run / f"canonical_labels_{h}m.parquet", horizon_columns)
                     for h in HORIZONS}
    diagnostic_iter = _iter_parquet_rows(run / "canonical_diagnostics.parquet", diagnostic_columns)
    with (run / "canonical_unavailable_rows.csv").open(encoding="utf-8", newline="") as stream:
        unavailable_iter = iter(csv.DictReader(stream))
        previous: tuple[str, str] | None = None
        rows = 0
        for wide in wide_iter:
            key = (wide["physical_symbol"], wide["origin_utc"])
            _require(previous is None or key > previous,
                     "canonical_labels.parquet is not strictly sorted/unique")
            previous = key
            for column, expected in IDENTITY_COLUMNS.items():
                _require(wide[column] == expected, f"canonical_labels.parquet {column} mismatch")
            _require(wide["calculation_version"] == expected_calculation_version,
                     "wide calculation version mismatch")
            for horizon in HORIZONS:
                horizon_row = _next_or_fail(horizon_iters[horizon], f"canonical_labels_{horizon}m.parquet")
                diagnostic = _next_or_fail(diagnostic_iter, "canonical_diagnostics.parquet")
                expected_key = (wide["symbol"], wide["physical_symbol"], wide["origin_utc"], horizon)
                _require((horizon_row["symbol"], horizon_row["physical_symbol"], horizon_row["origin_utc"],
                          horizon_row["horizon_minutes"]) == expected_key,
                         f"{horizon}m key does not match wide output")
                _require((diagnostic["symbol"], diagnostic["physical_symbol"], diagnostic["origin_utc"],
                          diagnostic["horizon_minutes"]) == expected_key,
                         f"{horizon}m diagnostic key does not match wide output")
                expected_values = (wide[f"label_{horizon}m"], wide[f"status_{horizon}m"],
                                   wide[f"reason_codes_{horizon}m"])
                _require((horizon_row["label"], horizon_row["status"], horizon_row["reason_codes_json"])
                         == expected_values, f"{horizon}m horizon/wide values disagree")
                _require((diagnostic["label"], diagnostic["status"], diagnostic["reason_codes_json"])
                         == expected_values, f"{horizon}m diagnostic/wide values disagree")
                _validate_diagnostic_semantics(diagnostic)
                if expected_values[1] == "UNAVAILABLE":
                    unavailable = _next_or_fail(unavailable_iter, "canonical_unavailable_rows.csv")
                    _require((unavailable["symbol"], unavailable["physical_symbol"], unavailable["origin_utc"],
                              int(unavailable["horizon_minutes"]), unavailable["status"],
                              unavailable["reason_codes_json"]) == (*expected_key, expected_values[1],
                                                                    expected_values[2]),
                             "unavailable CSV row does not match Parquet outputs")
            rows += 1
        _require(rows == EXPECTED_TOTAL_ORIGINS, "canonical_labels.parquet row count mismatch")
        _require_exhausted(unavailable_iter, "canonical_unavailable_rows.csv")
    for horizon, iterator in horizon_iters.items():
        _require_exhausted(iterator, f"canonical_labels_{horizon}m.parquet")
    _require_exhausted(diagnostic_iter, "canonical_diagnostics.parquet")


def validate_generation_manifest_identity(manifest: Mapping[str, Any], run_name: str,
                                          environment: Mapping[str, str]) -> None:
    _require(manifest.get("run_id") == run_name, "run directory and manifest run_id mismatch")
    _require(manifest.get("canonical_protocol_id") == CANONICAL_PROTOCOL_ID, "protocol ID mismatch")
    _require(manifest.get("canonical_release_id") == CANONICAL_RELEASE_ID, "release ID mismatch")
    _require(manifest.get("status") == CANONICAL_STATUS, "canonical status mismatch")
    _require(manifest.get("configuration_identity") == {"strings": CANONICAL_CONFIG,
                                                         "sha256": CONFIGURATION_SHA256},
             "configuration identity mismatch")
    for field, expected in (("architecture_identity", ARCHITECTURE_SHA256),
                            ("freeze_identity", FREEZE_AMENDMENT_SHA256),
                            ("harness_identity", HARNESS_SHA256)):
        _require(manifest.get(field, {}).get("sha256") == expected, f"{field} mismatch")
    _require(manifest.get("source_identity") == {"corpus_id": SOURCE_IDENTITY,
                                                  "manifest_sha256": SOURCE_MANIFEST_SHA256},
             "source identity mismatch")
    _require(manifest.get("canonical_horizons_minutes") == list(HORIZONS), "canonical horizons mismatch")
    _require(manifest.get("horizon_relationship") == "INDEPENDENT", "horizon independence missing")
    _require(manifest.get("rms48_contract") == {"return_count": 48, "return_spacing_minutes": 5},
             "RMS48 contract mismatch")
    _require(manifest.get("calculation_environment") == dict(environment),
             "calculation environment mismatch")
    _require(manifest.get("calculation_version") == calculation_version(environment),
             "calculation version mismatch")
    _require(manifest.get("generator_source_sha256") == environment["generator_source_sha256"],
             "generator source hash mismatch")
    _require(manifest.get("validator_source_sha256") == environment["validator_source_sha256"],
             "validator source hash mismatch")
    _require(manifest.get("contract_source_sha256") == environment["contract_source_sha256"],
             "contract source hash mismatch")
    _require(manifest.get("deterministic_sort") ==
             "physical_symbol lexical ascending, then origin_utc ascending", "sort contract mismatch")
    _require(bool(manifest.get("generation_command")), "generation command missing")


def _validate_hash_manifests(run: Path, manifest: Mapping[str, Any]) -> None:
    payload_hashes = manifest.get("output_file_hashes")
    _require(isinstance(payload_hashes, dict) and set(payload_hashes) == PAYLOAD_FILES,
             "generation manifest payload hash set mismatch")
    for name, expected in payload_hashes.items():
        _require(sha256_file(run / name) == expected, f"payload hash mismatch: {name}")
    output_hashes = json.loads((run / "canonical_output_hashes.json").read_text(encoding="utf-8"))
    _require(output_hashes.get("canonical_protocol_id") == CANONICAL_PROTOCOL_ID,
             "output hash manifest protocol mismatch")
    _require(output_hashes.get("canonical_release_id") == CANONICAL_RELEASE_ID,
             "output hash manifest release mismatch")
    _require(output_hashes.get("self_excluded") == "canonical_output_hashes.json",
             "output hash manifest self-exclusion mismatch")
    expected_files = REQUIRED_FILES - {"canonical_output_hashes.json"}
    _require(set(output_hashes.get("files", {})) == expected_files,
             "output hash manifest file set mismatch")
    for name, expected in output_hashes["files"].items():
        _require(sha256_file(run / name) == expected, f"output hash mismatch: {name}")


def _validate_summary(run: Path, counts: Mapping[int, Counter[str]],
                      symbol_counts: Mapping[int, Mapping[str, Counter[str]]]) -> None:
    expected: dict[tuple[int, str], tuple[int, ...]] = {}
    for horizon in HORIZONS:
        for physical in (*sorted(EXPECTED_SOURCE_HASHES), "ALL"):
            counter = counts[horizon] if physical == "ALL" else symbol_counts[horizon][physical]
            expected[(horizon, physical)] = (
                counter["VALID"] + counter["UNAVAILABLE"], counter["VALID"], counter["UNAVAILABLE"],
                counter["LONG_FAVORED"], counter["SHORT_FAVORED"], counter["NO_DIRECTION"])
    with (run / "canonical_generation_summary.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    _require(len(rows) == len(expected), "generation summary row count mismatch")
    actual = {}
    for row in rows:
        key = (int(row["horizon_minutes"]), row["physical_symbol"])
        _require(key not in actual, "duplicate generation summary row")
        actual[key] = tuple(int(row[name]) for name in (
            "total", "valid", "unavailable", "long_favored", "short_favored", "no_direction"))
    _require(actual == expected, "generation summary does not reconcile to Parquet outputs")


def validate_run(run_directory: Path, *, write_report: bool = True) -> dict[str, Any]:
    run = run_directory.resolve()
    root = repository_root()
    output_root = canonical_output_root(root).resolve()
    _require(run.parent == output_root, f"run directory must be directly under {output_root}")
    for name in REQUIRED_FILES:
        _require((run / name).is_file(), f"required output missing: {name}")
    verify_release_lock(root)
    _, source_paths = verify_source_identity(root)
    current_hashes = {
        "generator_hash": sha256_file(Path(__file__).with_name("generate_v2_gpt6pro_canonical.py")),
        "validator_hash": sha256_file(Path(__file__)),
        "contract_hash": sha256_file(Path(__file__).with_name("v2_gpt6pro_contract.py")),
    }
    environment = environment_identity(**current_hashes)
    manifest = json.loads((run / "canonical_generation_manifest.json").read_text(encoding="utf-8"))
    validate_generation_manifest_identity(manifest, run.name, environment)
    _require(manifest.get("input_file_hashes") == EXPECTED_SOURCE_HASHES, "input file hashes mismatch")
    release_manifest_path = root / "runtime/audit" / CANONICAL_RELEASE_ID / "CANONICAL_RELEASE_MANIFEST.json"
    _require(manifest.get("release_manifest_sha256") == sha256_file(release_manifest_path),
             "release manifest hash mismatch")
    for symbol, path in source_paths.items():
        _require(sha256_file(path) == manifest["input_file_hashes"][symbol],
                 f"input file changed: {symbol}")
    _validate_hash_manifests(run, manifest)
    counts: dict[int, Counter[str]] = {}
    symbol_counts: dict[int, dict[str, Counter[str]]] = {}
    for horizon in HORIZONS:
        counts[horizon], symbol_counts[horizon], _ = _validate_horizon_file(
            run / f"canonical_labels_{horizon}m.parquet", horizon, manifest["calculation_version"])
    _reconcile_outputs(run, manifest["calculation_version"])
    _validate_summary(run, counts, symbol_counts)
    actual_statistics = {
        "counts": {str(h): dict(counts[h]) for h in HORIZONS},
        "symbol_counts": {f"{h}:{symbol}": dict(counter)
                          for h in HORIZONS for symbol, counter in sorted(symbol_counts[h].items())},
    }
    _require(manifest.get("row_counts") == actual_statistics,
             "manifest row/class counts do not reconcile to Parquet outputs")
    report = {
        "validation": "PASS", "canonical_protocol_id": CANONICAL_PROTOCOL_ID,
        "canonical_release_id": CANONICAL_RELEASE_ID,
        "counts": {str(h): dict(counts[h]) for h in HORIZONS},
        "full_corpus_regenerated_by_validator": "NO",
    }
    if write_report:
        text = ["# Canonical generation validation", "", "Validation: PASS", "",
                f"Canonical protocol: `{CANONICAL_PROTOCOL_ID}`", f"Canonical release: `{CANONICAL_RELEASE_ID}`",
                "", "The validator read existing outputs only and did not regenerate labels.", ""]
        (run / "canonical_generation_validation.md").write_text("\n".join(text), encoding="utf-8")
        write_output_hashes(run)
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_run(args.run_directory, write_report=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
