"""Immutable contract helpers for the V2_GPT6PRO canonical label release."""
from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import pyarrow


CANONICAL_PROTOCOL_ID = "V2_GPT6PRO"
CANONICAL_RELEASE_ID = "V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z"
CANONICAL_STATUS = "CANONICAL_HISTORICAL_LABEL_PROTOCOL"
CANONICAL_CONFIG = {"a": "0.50", "beta": "0.25", "rho": "0.10", "eta": "0.50"}
CONFIGURATION_SHA256 = "fb194d06cf2b79db113f74cec495fe96c61c6fde1cc33981d678332bdd919f99"
ARCHITECTURE_SHA256 = "7d5af8dde65fc7a3ead814e3bfa57e8ec19fa9bc3f5d2c923258da9732a0e799"
FREEZE_AMENDMENT_SHA256 = "9cc5d4ea6485b59227a94e4fbef54dda3fbc43e725e746b53c9d8b03a5942134"
HARNESS_SHA256 = "a06e678b2f21898ba38868c505c92e9056fc85692966fd62b614dc6e6c348477"
SOURCE_MANIFEST_SHA256 = "f600c0546344259911075f479de583c69d88435321e06c41e0e61acbf49bf45e"
SOURCE_IDENTITY = "direction-regime-history-20240930-20260930-bybit-linear-1m-v1"
SOURCE_START = "2024-09-30T07:20:00Z"
SOURCE_END = "2026-09-30T00:00:00Z"
HORIZONS = (60, 120)
RMS48_RETURN_COUNT = 48
RMS48_RETURN_SPACING_MINUTES = 5
PHYSICAL_SYMBOLS = ("BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT")
SORTED_PHYSICAL_SYMBOLS = tuple(sorted(PHYSICAL_SYMBOLS))
LOGICAL_BY_PHYSICAL = {
    "BTCUSDT": "BTCUSDT",
    "AVAXUSDT": "AVAXUSDT",
    "SUIUSDT": "SUIUSDT",
    "1000PEPEUSDT": "PEPEUSDT",
}
EXPECTED_SOURCE_HASHES = {
    "BTCUSDT": "131c4ebe05b2fe08eeff2758100c7ba79b609320a07d403c9db3dd50cdaa4d9c",
    "AVAXUSDT": "dbdc8739c10ac2a04d5d5daf2d4ba85789c3afbf33fb6714762e0f943b1e8e69",
    "SUIUSDT": "d2daef3bcb7944b44c516ff5f7cc182cf0ebb9a7aee809e3a1979b568f6a0b39",
    "1000PEPEUSDT": "40926fb1e2c026ef6720b687ec7eff1f65063e4708b995431cff7edba9e18061",
}
EXPECTED_SOURCE_ROWS = {symbol: 1_050_760 for symbol in PHYSICAL_SYMBOLS}
EXPECTED_COUNTS = {
    60: {"VALID": 840_368, "LONG_FAVORED": 200_625, "SHORT_FAVORED": 204_838,
         "NO_DIRECTION": 434_905, "UNAVAILABLE": 240},
    120: {"VALID": 840_320, "LONG_FAVORED": 196_654, "SHORT_FAVORED": 202_304,
          "NO_DIRECTION": 441_362, "UNAVAILABLE": 288},
}
EXPECTED_TOTAL_ORIGINS = 840_608
ALLOWED_LABELS = frozenset({"LONG_FAVORED", "SHORT_FAVORED", "NO_DIRECTION"})
TIMESTAMP_RE = re.compile(r"^\d{8}T\d{6}Z$")


class ContractError(RuntimeError):
    """Raised when an immutable canonical identity or data contract fails."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_output_root(root: Path | None = None) -> Path:
    base = root or repository_root()
    return base / "runtime/data/canonical_direction_labels/V2_GPT6PRO"


def release_directory(root: Path | None = None) -> Path:
    base = root or repository_root()
    return base / "runtime/audit" / CANONICAL_RELEASE_ID


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_config_hash(config: Mapping[str, str]) -> str:
    encoded = json.dumps(dict(config), separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def require_equal(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ContractError(f"{name} mismatch: expected {expected!r}, found {actual!r}")


def verify_file_hash(path: Path, expected: str, identity: str) -> str:
    if not path.is_file():
        raise ContractError(f"{identity} missing: {path}")
    actual = sha256_file(path)
    require_equal(f"{identity} SHA-256", actual, expected)
    return actual


def validate_release_manifest_data(manifest: Mapping[str, Any]) -> None:
    require_equal("canonical protocol ID", manifest.get("protocol_id"), CANONICAL_PROTOCOL_ID)
    require_equal("canonical status", manifest.get("status"), CANONICAL_STATUS)
    require_equal("canonical release ID", manifest.get("release_id"), CANONICAL_RELEASE_ID)
    identity = manifest.get("configuration_identity", {})
    require_equal("configuration strings", identity.get("configuration_strings"), CANONICAL_CONFIG)
    require_equal("configuration SHA-256", identity.get("configuration_sha256"), CONFIGURATION_SHA256)
    require_equal("primary horizon", identity.get("primary_horizon"), "60m")
    require_equal("secondary horizon", identity.get("secondary_horizon"), "120m")
    require_equal("architecture SHA-256", identity.get("architecture_sha256"), ARCHITECTURE_SHA256)
    require_equal("freeze amendment SHA-256", identity.get("freeze_amendment_sha256"), FREEZE_AMENDMENT_SHA256)
    require_equal("harness SHA-256", identity.get("harness_sha256"), HARNESS_SHA256)
    require_equal("canonical outputs pre-generation state", manifest.get("canonical_outputs_status"),
                  "NOT_GENERATED_IN_THIS_TASK")


def verify_release_lock(root: Path | None = None) -> dict[str, Any]:
    base = root or repository_root()
    release = release_directory(base)
    manifest_path = release / "CANONICAL_RELEASE_MANIFEST.json"
    hashes_path = release / "OUTPUT_HASHES.json"
    if not manifest_path.is_file() or not hashes_path.is_file():
        raise ContractError(f"canonical release package incomplete: {release}")
    hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
    require_equal("release hash-manifest ID", hashes.get("release_id"), CANONICAL_RELEASE_ID)
    for relative, expected in hashes.get("files", {}).items():
        verify_file_hash(release / relative, expected, f"canonical release file {relative}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_release_manifest_data(manifest)
    require_equal("configuration serialization hash", canonical_config_hash(CANONICAL_CONFIG),
                  CONFIGURATION_SHA256)
    architecture_path = Path(manifest["architecture_identity"]["path"])
    freeze_path = Path(manifest["freeze_identity"]["path"])
    verify_file_hash(architecture_path, ARCHITECTURE_SHA256, "architecture")
    verify_file_hash(freeze_path, FREEZE_AMENDMENT_SHA256, "freeze amendment")
    harness_path = base / "tools/research_v2/v2_research_harness.py"
    verify_file_hash(harness_path, HARNESS_SHA256, "frozen harness")
    return manifest


def validate_source_manifest_data(manifest: Mapping[str, Any]) -> None:
    require_equal("source identity", manifest.get("corpus_id"), SOURCE_IDENTITY)
    require_equal("source status", manifest.get("status"), "DATA_READY")
    require_equal("source timeframe", manifest.get("timeframe"), "1m")
    require_equal("source physical symbols", tuple(manifest.get("symbols", {}).get("physical", ())),
                  PHYSICAL_SYMBOLS)
    require_equal("source symbol mapping", manifest.get("symbols", {}).get("logical_physical_bindings"),
                  {value: key for key, value in LOGICAL_BY_PHYSICAL.items()})
    source_range = manifest.get("range", {})
    require_equal("source coverage start", source_range.get("common_continuous_start"), SOURCE_START)
    require_equal("source coverage end", source_range.get("common_continuous_end"), SOURCE_END)


def verify_source_identity(root: Path | None = None) -> tuple[dict[str, Any], dict[str, Path]]:
    base = root or repository_root()
    manifest_path = base / "runtime/data/direction-regime-history/manifest.json"
    verify_file_hash(manifest_path, SOURCE_MANIFEST_SHA256, "source manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_source_manifest_data(manifest)
    records = {row["physical_symbol"]: row for row in manifest.get("files", [])}
    require_equal("source manifest symbol records", set(records), set(PHYSICAL_SYMBOLS))
    paths: dict[str, Path] = {}
    for symbol in PHYSICAL_SYMBOLS:
        record = records[symbol]
        require_equal(f"{symbol} manifest hash", record.get("sha256"), EXPECTED_SOURCE_HASHES[symbol])
        require_equal(f"{symbol} manifest rows", record.get("rows"), EXPECTED_SOURCE_ROWS[symbol])
        require_equal(f"{symbol} manifest start", record.get("start"), SOURCE_START)
        require_equal(f"{symbol} manifest end", record.get("end"), SOURCE_END)
        require_equal(f"{symbol} logical symbol", record.get("symbol"), LOGICAL_BY_PHYSICAL[symbol])
        path = base / record["local_path"]
        verify_file_hash(path, EXPECTED_SOURCE_HASHES[symbol], f"{symbol} source file")
        paths[symbol] = path
    return manifest, paths


def validate_source_frame(frame: pd.DataFrame, physical_symbol: str) -> pd.DataFrame:
    required = {"open_time", "close_time", "symbol", "logical_symbol", "category", "timeframe",
                "open", "high", "low", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise ContractError(f"{physical_symbol} source columns missing: {sorted(missing)}")
    require_equal(f"{physical_symbol} row count", len(frame), EXPECTED_SOURCE_ROWS[physical_symbol])
    open_time = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    close_time = pd.to_datetime(frame["close_time"], utc=True, errors="coerce")
    if open_time.isna().any() or close_time.isna().any():
        raise ContractError(f"{physical_symbol} invalid UTC timestamp")
    require_equal(f"{physical_symbol} first open", open_time.iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ"), SOURCE_START)
    require_equal(f"{physical_symbol} final close", close_time.iloc[-1].strftime("%Y-%m-%dT%H:%M:%SZ"), SOURCE_END)
    minute_ns = 60 * 1_000_000_000
    open_ns = open_time.astype("int64").to_numpy()
    close_ns = close_time.astype("int64").to_numpy()
    if not np.all(np.diff(open_ns) == minute_ns) or not np.all(close_ns - open_ns == minute_ns):
        raise ContractError(f"{physical_symbol} timestamps are not unique contiguous completed minutes")
    for column, expected in (("symbol", physical_symbol), ("logical_symbol", LOGICAL_BY_PHYSICAL[physical_symbol]),
                             ("category", "linear"), ("timeframe", "1m")):
        if not frame[column].eq(expected).all():
            raise ContractError(f"{physical_symbol} {column} identity mismatch")
    prices = frame[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    values = prices.to_numpy(np.float64)
    if not np.isfinite(values).all() or not (values > 0).all():
        raise ContractError(f"{physical_symbol} contains invalid/nonpositive OHLC")
    o, h, l, c = (prices[name].to_numpy(np.float64) for name in ("open", "high", "low", "close"))
    if not ((l <= o).all() and (o <= h).all() and (l <= c).all() and (c <= h).all() and (l <= h).all()):
        raise ContractError(f"{physical_symbol} contains invalid OHLC ordering")
    result = frame.copy()
    result["open_time"] = open_time
    result["close_time"] = close_time
    for name in ("open", "high", "low", "close"):
        result[name] = prices[name]
    return result


def assert_canonical_horizons(horizons: tuple[int, ...]) -> None:
    require_equal("canonical horizons", tuple(horizons), HORIZONS)


def environment_identity(generator_hash: str, validator_hash: str, contract_hash: str) -> dict[str, str]:
    return {
        "python": sys.version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "pyarrow": pyarrow.__version__,
        "platform": platform.platform(),
        "floating_point_type": "IEEE binary64 / numpy.float64",
        "log_implementation": "Python math.log in frozen harness",
        "sqrt_implementation": "Python math.sqrt in frozen harness",
        "timezone_handling": "UTC-aware pandas timestamps; canonical UTC Z serialization",
        "source_parsing_mode": "pandas.read_csv gzip; OHLC parsed as numpy.float64",
        "deterministic_sort": "physical_symbol lexical ascending, then origin_utc ascending",
        "generator_source_sha256": generator_hash,
        "validator_source_sha256": validator_hash,
        "contract_source_sha256": contract_hash,
        "harness_sha256": HARNESS_SHA256,
    }


def calculation_version(environment: Mapping[str, str]) -> str:
    payload = json.dumps(dict(environment), sort_keys=True, separators=(",", ":")).encode()
    return f"v2_gpt6pro_canonical_{hashlib.sha256(payload).hexdigest()[:16]}"


def validate_timestamp(value: str) -> str:
    if not TIMESTAMP_RE.fullmatch(value):
        raise ContractError("timestamp must have format YYYYMMDDTHHMMSSZ")
    return value


def relative_hashes(directory: Path, names: list[str]) -> dict[str, str]:
    return {name: sha256_file(directory / name) for name in sorted(names)}


def write_output_hashes(directory: Path) -> dict[str, str]:
    names = [path.name for path in directory.iterdir()
             if path.is_file() and path.name != "canonical_output_hashes.json"]
    hashes = relative_hashes(directory, names)
    payload = {
        "canonical_protocol_id": CANONICAL_PROTOCOL_ID,
        "canonical_release_id": CANONICAL_RELEASE_ID,
        "files": hashes,
        "self_excluded": "canonical_output_hashes.json",
    }
    (directory / "canonical_output_hashes.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return hashes


def json_reason(reasons: Any) -> str:
    return json.dumps(list(reasons or []), separators=(",", ":"))


def canonicalize_harness_result(result: Mapping[str, Any]) -> tuple[str | None, str, str]:
    if result.get("status") == "RESEARCH_CANDIDATE" and result.get("candidate_label") in ALLOWED_LABELS:
        return str(result["candidate_label"]), "VALID", "[]"
    reasons = result.get("availability_reasons") or [str(result.get("status") or "UNAVAILABLE")]
    return None, "UNAVAILABLE", json_reason(reasons)


def prepare_run_paths(output_root: Path, timestamp: str) -> tuple[Path, Path]:
    validate_timestamp(timestamp)
    target = output_root / timestamp
    if target.exists():
        raise ContractError(f"canonical run directory already exists: {target}")
    output_root.mkdir(parents=True, exist_ok=True)
    staging = output_root / f".incomplete-{timestamp}"
    if staging.exists():
        raise ContractError(f"incomplete run directory already exists: {staging}")
    staging.mkdir()
    return staging, target

