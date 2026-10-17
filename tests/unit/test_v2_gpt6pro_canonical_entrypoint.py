from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tools.direction_labels import generate_v2_gpt6pro_canonical as generator
from tools.direction_labels.v2_gpt6pro_contract import (
    ARCHITECTURE_SHA256, CANONICAL_CONFIG, CANONICAL_PROTOCOL_ID, CANONICAL_RELEASE_ID,
    CANONICAL_STATUS, CONFIGURATION_SHA256, ContractError, FREEZE_AMENDMENT_SHA256,
    HARNESS_SHA256, HORIZONS, RMS48_RETURN_COUNT, RMS48_RETURN_SPACING_MINUTES,
    SOURCE_IDENTITY, assert_canonical_horizons, canonical_config_hash,
    calculation_version, canonicalize_harness_result, environment_identity, prepare_run_paths, sha256_file,
    validate_release_manifest_data, validate_source_manifest_data, verify_file_hash,
)
from tools.direction_labels.validate_v2_gpt6pro_canonical import (
    ORIGINS_PER_SYMBOL, expected_origin_utc, validate_generation_manifest_identity,
)
from tools.research_v2.v2_research_harness import ResearchConfig, evaluate_path


def release_manifest() -> dict:
    return {
        "release_id": CANONICAL_RELEASE_ID,
        "protocol_id": CANONICAL_PROTOCOL_ID,
        "status": CANONICAL_STATUS,
        "canonical_outputs_status": "NOT_GENERATED_IN_THIS_TASK",
        "configuration_identity": {
            "configuration_strings": CANONICAL_CONFIG,
            "configuration_sha256": CONFIGURATION_SHA256,
            "primary_horizon": "60m", "secondary_horizon": "120m",
            "architecture_sha256": ARCHITECTURE_SHA256,
            "freeze_amendment_sha256": FREEZE_AMENDMENT_SHA256,
            "harness_sha256": HARNESS_SHA256,
        },
    }


def source_manifest() -> dict:
    return {
        "corpus_id": SOURCE_IDENTITY, "status": "DATA_READY", "timeframe": "1m",
        "symbols": {
            "physical": ["BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"],
            "logical_physical_bindings": {
                "BTCUSDT": "BTCUSDT", "AVAXUSDT": "AVAXUSDT", "SUIUSDT": "SUIUSDT",
                "PEPEUSDT": "1000PEPEUSDT"},
        },
        "range": {"common_continuous_start": "2024-09-30T07:20:00Z",
                  "common_continuous_end": "2026-09-30T00:00:00Z"},
    }


def test_canonical_config_cannot_be_overridden():
    with pytest.raises(SystemExit):
        generator.build_parser().parse_args(["--a", "1.0"])
    assert canonical_config_hash(CANONICAL_CONFIG) == CONFIGURATION_SHA256


def test_wrong_config_hash_aborts():
    data = release_manifest()
    data["configuration_identity"]["configuration_sha256"] = "0" * 64
    with pytest.raises(ContractError, match="configuration SHA-256"):
        validate_release_manifest_data(data)


@pytest.mark.parametrize("name,expected", [
    ("architecture", ARCHITECTURE_SHA256), ("freeze", FREEZE_AMENDMENT_SHA256),
    ("harness", HARNESS_SHA256),
])
def test_wrong_identity_file_hash_aborts(name: str, expected: str):
    path = Path(__file__)
    with pytest.raises(ContractError, match="SHA-256"):
        verify_file_hash(path, expected, name)


def test_wrong_source_identity_aborts():
    data = source_manifest()
    data["corpus_id"] = "other"
    with pytest.raises(ContractError, match="source identity"):
        validate_source_manifest_data(data)


def test_horizons_are_evaluated_independently():
    calls = []
    def evaluator(closes, index, config, horizon, **kwargs):
        calls.append(horizon)
        return {"status": "RESEARCH_CANDIDATE", "candidate_label":
                "LONG_FAVORED" if horizon == 60 else "SHORT_FAVORED"}
    values = np.ones(400)
    results = generator.evaluate_horizons_independently(
        values, values, values, 244, "2026-01-01T00:00:00Z",
        ResearchConfig.from_explicit(CANONICAL_CONFIG), evaluator)
    assert calls == [60, 120]
    assert results[60]["candidate_label"] == "LONG_FAVORED"
    assert results[120]["candidate_label"] == "SHORT_FAVORED"


def test_research_only_horizons_are_rejected():
    with pytest.raises(ContractError, match="canonical horizons"):
        assert_canonical_horizons((55, 60, 65, 115, 120, 125))


def test_rms48_contract_is_48_five_minute_returns():
    assert RMS48_RETURN_COUNT == 48
    assert RMS48_RETURN_SPACING_MINUTES == 5


def test_p4_preserves_boolean_opposing_phase_semantics():
    config = ResearchConfig.from_explicit(CANONICAL_CONFIG)
    result = evaluate_path([0.0] * 60, config, horizon=60)
    for side, opposite in (("LONG", "SHORT"), ("SHORT", "LONG")):
        side_result = result["sides"][side]
        opposite_result = result["sides"][opposite]
        p4 = list(side_result["predicates"].values())[3]
        assert p4 is (not side_result["opposing_phase"])
        assert side_result["opposing_phase"] is (opposite_result["B"] >= 1 - 1e-12)


def test_unavailable_is_not_no_direction():
    label, status, reasons = canonicalize_harness_result(
        {"status": "UNAVAILABLE", "candidate_label": None,
         "availability_reasons": ["INCOMPLETE_FUTURE"]})
    assert label is None
    assert status == "UNAVAILABLE"
    assert json.loads(reasons) == ["INCOMPLETE_FUTURE"]


def test_generation_iteration_order_is_deterministic():
    keys = [(symbol, index) for symbol in generator.SORTED_PHYSICAL_SYMBOLS
            for index in generator.canonical_origin_indices(20)]
    assert keys == sorted(keys)
    assert keys[:4] == [("1000PEPEUSDT", 4), ("1000PEPEUSDT", 9),
                        ("1000PEPEUSDT", 14), ("1000PEPEUSDT", 19)]
    assert ORIGINS_PER_SYMBOL == 210_152
    assert expected_origin_utc(0) == "2024-09-30T07:25:00Z"
    assert expected_origin_utc(ORIGINS_PER_SYMBOL - 1) == "2026-09-30T00:00:00Z"


def test_existing_output_directory_is_not_overwritten(monkeypatch):
    import tools.direction_labels.v2_gpt6pro_contract as contract
    monkeypatch.setattr(contract, "validate_timestamp", lambda value: value)
    with pytest.raises(ContractError, match="already exists"):
        prepare_run_paths(Path("."), "tests")


def test_generated_manifest_records_required_identities():
    environment = environment_identity("a" * 64, "b" * 64, "c" * 64)
    manifest = generator.build_generation_manifest(
        timestamp="20261017T120000Z", environment=environment,
        calculation_id=calculation_version(environment),
        source_manifest_sha256="f600c0546344259911075f479de583c69d88435321e06c41e0e61acbf49bf45e",
        source_hashes={}, payload_hashes={}, statistics={}, generation_command="python -m generator",
        release_manifest_sha256="d" * 64)
    validate_generation_manifest_identity(manifest, "20261017T120000Z", environment)
    assert set(manifest) >= {
        "configuration_identity", "architecture_identity", "freeze_identity", "harness_identity",
        "source_identity", "canonical_horizons_minutes", "rms48_contract", "calculation_environment",
        "input_file_hashes", "output_file_hashes", "row_counts", "generation_command",
        "generator_source_sha256", "validator_source_sha256",
    }


def test_frozen_harness_hash_is_unchanged():
    root = Path(__file__).resolve().parents[2]
    assert sha256_file(root / "tools/research_v2/v2_research_harness.py") == HARNESS_SHA256

