from fractions import Fraction

import pytest

from triggertrade.numeric_policy import (
    NumericPolicyError,
    NumericValueClass,
    Q18,
    Q36,
    QCAPITAL,
    QRATIO,
    RoundingMode,
    canonical_decimal_text,
    ceil_to_grid,
    compare_exact,
    exact_divide,
    exact_midpoint_sqrt,
    floor_to_grid,
    half_even_to_grid,
    parse_decimal_text,
    q18_wire,
    q36_working,
    qcapital_ceil,
    qcapital_floor,
    qratio_floor,
    quantize,
    truncate_to_grid,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0", Fraction(0)),
        ("-0", Fraction(0)),
        ("123456789012345678901234567890", Fraction(123456789012345678901234567890)),
        ("0.000000000001", Fraction(1, 10**12)),
        ("751.10", Fraction(75110, 100)),
        ("-12.3400", Fraction(-123400, 10000)),
    ],
)
def test_parse_decimal_text_is_exact(raw, expected):
    assert parse_decimal_text(raw) == expected


@pytest.mark.parametrize("raw", ["+1", "01", "1.", ".1", "1e3", "NaN", "Infinity", "-Infinity", "", " "])
def test_parse_decimal_text_rejects_noncanonical_or_nonfinite_text(raw):
    with pytest.raises(NumericPolicyError):
        parse_decimal_text(raw)


@pytest.mark.parametrize("value", [1, 1.0, object(), True])
def test_parse_decimal_text_rejects_non_text_inputs(value):
    with pytest.raises(NumericPolicyError):
        parse_decimal_text(value)  # type: ignore[arg-type]


def test_exact_rational_division_and_comparison_do_not_round():
    assert exact_divide(Fraction(1), Fraction(3)) == Fraction(1, 3)
    assert exact_divide(Fraction(2), Fraction(7)) == Fraction(2, 7)
    assert exact_divide(Fraction(202), Fraction(3)) == Fraction(202, 3)
    assert exact_divide(parse_decimal_text("751.10"), Fraction(3)) == Fraction(75110, 300)
    assert compare_exact(Fraction(100, 51), parse_decimal_text("1.960784313725490196")) == 1


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (RoundingMode.FLOOR, "-2"),
        (RoundingMode.CEIL, "-1"),
        (RoundingMode.TRUNCATE, "-1"),
        (RoundingMode.HALF_EVEN, "-2"),
    ],
)
def test_signed_rounding_modes(mode, expected):
    assert canonical_decimal_text(quantize(parse_decimal_text("-1.5"), Fraction(1), mode)) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.5", "2"),
        ("2.5", "2"),
        ("-1.5", "-2"),
        ("-2.5", "-2"),
        ("1.499999999999", "1"),
        ("1.500000000001", "2"),
    ],
)
def test_half_even_ties_and_neighbors(raw, expected):
    assert canonical_decimal_text(half_even_to_grid(parse_decimal_text(raw), Fraction(1))) == expected


@pytest.mark.parametrize("quantum", [Fraction(0), Fraction(-1), 0, -1])
def test_invalid_quantum_fails_explicitly(quantum):
    with pytest.raises(NumericPolicyError, match="quantum"):
        floor_to_grid(Fraction(1), quantum)


def test_qcapital_floor_and_ceil_examples():
    liability = qcapital_ceil(Fraction(202, 3))
    grant = qcapital_floor(exact_divide(parse_decimal_text("751.10"), Fraction(3)))
    total = grant.value * 3

    assert QCAPITAL == parse_decimal_text("0.000000000001")
    assert liability.text == "67.333333333334"
    assert grant.text == "250.366666666666"
    assert canonical_decimal_text(total) == "751.099999999998"
    assert canonical_decimal_text(parse_decimal_text("751.10") - total) == "0.000000000002"


def test_qratio_is_report_only_and_exact_value_remains_available():
    exact = Fraction(100, 51)
    reported = qratio_floor(exact)

    assert QRATIO == parse_decimal_text("0.000000000000000001")
    assert reported.value_class is NumericValueClass.REPORT_ONLY
    assert reported.text == "1.960784313725490196"
    assert exact > reported.value


def test_q36_working_and_q18_wire_are_distinct_and_wire_does_not_mutate_work():
    exact = Fraction(1, 7)
    working = q36_working(exact)
    exported = q18_wire(working.value)

    assert Q36 == parse_decimal_text("0.000000000000000000000000000000000001")
    assert Q18 == parse_decimal_text("0.000000000000000001")
    assert working.value_class is NumericValueClass.WORKING
    assert exported.value_class is NumericValueClass.WIRE
    assert working.text == "0.142857142857142857142857142857142857"
    assert exported.text == "0.142857142857142857"
    assert working.text != exported.text


def test_q18_export_cannot_reconstruct_near_threshold_working_value():
    threshold = parse_decimal_text("0.1")
    below_work = threshold - Q36

    assert compare_exact(below_work, threshold) == -1
    assert q18_wire(below_work).text == "0.1"
    assert q18_wire(below_work).value == threshold


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Fraction(0), "0"),
        (Fraction(4), "2"),
        (Fraction(2), "1.414213562373095048801688724209698079"),
    ],
)
def test_exact_midpoint_sqrt_basic_cases(value, expected):
    assert exact_midpoint_sqrt(value).text == expected


def test_exact_midpoint_sqrt_half_even_ties():
    scale = 1
    even_lower_midpoint = Fraction(25, 400)
    even_upper_midpoint = Fraction(225, 400)

    assert exact_midpoint_sqrt(even_lower_midpoint, scale=scale).text == "0.2"
    assert exact_midpoint_sqrt(even_upper_midpoint, scale=scale).text == "0.8"
    assert exact_midpoint_sqrt(even_lower_midpoint - Fraction(1, 10000), scale=scale).text == "0.2"
    assert exact_midpoint_sqrt(even_lower_midpoint + Fraction(1, 10000), scale=scale).text == "0.3"


def test_exact_midpoint_sqrt_rejects_negative_values_and_uses_large_integer_arithmetic():
    huge = Fraction(123456789012345678901234567890123456789, 7)

    assert exact_midpoint_sqrt(huge).text.startswith("4199605236759856607.")
    with pytest.raises(NumericPolicyError, match="nonnegative"):
        exact_midpoint_sqrt(Fraction(-1))


def test_directional_grid_helpers_are_exact_and_generic():
    value = parse_decimal_text("-1.234")
    quantum = parse_decimal_text("0.01")

    assert canonical_decimal_text(floor_to_grid(value, quantum)) == "-1.24"
    assert canonical_decimal_text(ceil_to_grid(value, quantum)) == "-1.23"
    assert canonical_decimal_text(truncate_to_grid(value, quantum)) == "-1.23"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (parse_decimal_text("751.10"), "751.1"),
        (parse_decimal_text("0.000000000001"), "0.000000000001"),
        (parse_decimal_text("-0.000"), "0"),
        (parse_decimal_text("100.0000"), "100"),
    ],
)
def test_canonical_decimal_serialization_examples(value, expected):
    assert canonical_decimal_text(value) == expected


def test_nonterminating_rational_requires_governed_quantizer_before_serialization():
    with pytest.raises(NumericPolicyError, match="nonterminating"):
        canonical_decimal_text(Fraction(1, 3))


def test_binary_float_and_decimal_context_paths_are_not_accepted_by_b1_primitives():
    with pytest.raises(NumericPolicyError, match="unsupported"):
        floor_to_grid(1.0, QCAPITAL)  # type: ignore[arg-type]
    with pytest.raises(NumericPolicyError, match="unsupported"):
        floor_to_grid(Fraction(1), 0.01)  # type: ignore[arg-type]
