from decimal import Decimal, localcontext

import pytest

from triggertrade.canonical_json import (
    CanonicalJsonError,
    canonical_decimal_text,
    canonical_json_bytes,
    canonical_json_digest,
    canonical_json_text,
)


def test_mapping_key_order_has_exact_canonical_text_and_digest():
    left = {"beta": 2, "alpha": 1}
    right = {"alpha": 1, "beta": 2}

    assert canonical_json_text(left) == '{"alpha":1,"beta":2}'
    assert canonical_json_text(right) == '{"alpha":1,"beta":2}'
    assert canonical_json_digest(left) == "955c071f4fbee40a01b9bc6e8fb3627e81bda84811ae9c29fcc5812ba3a45162"
    assert canonical_json_digest(right) == "955c071f4fbee40a01b9bc6e8fb3627e81bda84811ae9c29fcc5812ba3a45162"


def test_nested_object_ordering_is_deterministic():
    payload = {
        "outer": {"z": True, "a": None},
        "array": [{"b": 2, "a": 1}],
    }

    assert canonical_json_text(payload) == '{"array":[{"a":1,"b":2}],"outer":{"a":null,"z":true}}'


def test_arrays_preserve_order_and_order_changes_digest():
    first = {"values": [1, 2, 3]}
    second = {"values": [3, 2, 1]}

    assert canonical_json_text(first) == '{"values":[1,2,3]}'
    assert canonical_json_text(second) == '{"values":[3,2,1]}'
    assert canonical_json_digest(first) != canonical_json_digest(second)


def test_unicode_is_utf8_stable_and_not_ascii_escaped():
    payload = {"symbol": "BTCUSDT", "note": "цена €"}

    assert canonical_json_text(payload) == '{"note":"цена €","symbol":"BTCUSDT"}'
    assert canonical_json_bytes(payload) == '{"note":"цена €","symbol":"BTCUSDT"}'.encode("utf-8")


def test_null_boolean_and_integer_values_have_exact_json_tokens():
    payload = {"active": True, "count": 3, "missing": None}

    assert canonical_json_text(payload) == '{"active":true,"count":3,"missing":null}'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("751.10"), "751.1"),
        (Decimal("-0"), "0"),
        (Decimal("00012.3400"), "12.34"),
        (Decimal("1E+3"), "1000"),
        (Decimal("0.000000000001"), "0.000000000001"),
    ],
)
def test_decimal_values_follow_numeric_policy_examples(value, expected):
    assert canonical_decimal_text(value) == expected


def test_decimal_values_encode_as_canonical_json_numbers():
    payload = {"actual_committed_capital": Decimal("67.333333333334"), "input_raw": "751.10"}

    assert canonical_json_text(payload) == '{"actual_committed_capital":67.333333333334,"input_raw":"751.10"}'


def test_decimal_serialization_does_not_use_active_decimal_context_precision():
    value = Decimal("123456789012345678901234567890.1234500")

    with localcontext() as ctx:
        ctx.prec = 5
        assert canonical_decimal_text(value) == "123456789012345678901234567890.12345"


@pytest.mark.parametrize("value", [1.0, float("nan"), float("inf"), object()])
def test_unsupported_or_ambiguous_types_fail_deterministically(value):
    with pytest.raises(CanonicalJsonError):
        canonical_json_text({"value": value})


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_nonfinite_decimals_fail_deterministically(value):
    with pytest.raises(CanonicalJsonError, match="finite"):
        canonical_json_text({"value": value})


def test_non_string_object_keys_fail_deterministically():
    with pytest.raises(CanonicalJsonError, match="keys must be strings"):
        canonical_json_text({1: "one"})


def test_changed_semantic_value_changes_text_and_digest():
    before = {"order_spec_contract_version": 5, "quantity": Decimal("1")}
    after = {"order_spec_contract_version": 5, "quantity": Decimal("2")}

    assert canonical_json_text(before) == '{"order_spec_contract_version":5,"quantity":1}'
    assert canonical_json_text(after) == '{"order_spec_contract_version":5,"quantity":2}'
    assert canonical_json_digest(before) != canonical_json_digest(after)


def test_reconstructed_replay_payload_has_identical_digest():
    original = {
        "spec": {"version": 5, "symbol": "BTCUSDT", "price": Decimal("751.10")},
        "lineage": {"set_result_id": "set-1", "decision_cycle_id": "cycle-1"},
    }
    reconstructed = {
        "lineage": {"decision_cycle_id": "cycle-1", "set_result_id": "set-1"},
        "spec": {"price": Decimal("751.1"), "symbol": "BTCUSDT", "version": 5},
    }

    expected_text = (
        '{"lineage":{"decision_cycle_id":"cycle-1","set_result_id":"set-1"},'
        '"spec":{"price":751.1,"symbol":"BTCUSDT","version":5}}'
    )
    assert canonical_json_text(original) == expected_text
    assert canonical_json_text(original) == canonical_json_text(reconstructed)
    assert canonical_json_digest(original) == canonical_json_digest(reconstructed)
    assert canonical_json_digest(original) == "4f3c73bce177415481b693e49de0a6a36aea80caa3db93c64dc586e454e23995"
