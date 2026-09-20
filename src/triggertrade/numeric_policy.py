"""Exact numeric primitives for TriggerTrade policy-bound calculations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from math import isqrt
import re
from typing import Final


TT_NUMERIC_POLICY_VERSION: Final = "TT_NUMERIC_V1"
TT_SET_NUMERIC_POLICY_VERSION: Final = "TT_SET_NUMERIC_V1"

QCAPITAL: Final = Fraction(1, 10**12)
QRATIO: Final = Fraction(1, 10**18)
Q36: Final = Fraction(1, 10**36)
Q18: Final = Fraction(1, 10**18)

_DECIMAL_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


class NumericPolicyError(ValueError):
    """Raised when exact numeric policy primitives cannot represent a value."""


class RoundingMode(StrEnum):
    FLOOR = "FLOOR"
    CEIL = "CEIL"
    TRUNCATE = "TRUNCATE"
    HALF_EVEN = "HALF_EVEN"


class NumericValueClass(StrEnum):
    WORKING = "WORKING"
    WIRE = "WIRE"
    REPORT_ONLY = "REPORT_ONLY"


@dataclass(frozen=True)
class QuantizedDecimal:
    """A decimal value selected for a specific policy boundary."""

    value: Fraction
    quantum: Fraction
    value_class: NumericValueClass
    policy_version: str

    @property
    def text(self) -> str:
        return canonical_decimal_text(self.value)


def parse_decimal_text(value: str) -> Fraction:
    """Parse a finite non-exponent decimal string into an exact rational."""

    if not isinstance(value, str):
        raise NumericPolicyError("decimal input must be text")
    if not _DECIMAL_RE.fullmatch(value):
        raise NumericPolicyError("decimal input must be plain finite decimal text")
    sign = -1 if value.startswith("-") else 1
    body = value[1:] if sign < 0 else value
    integer_text, dot, fraction_text = body.partition(".")
    numerator_text = integer_text + (fraction_text if dot else "")
    numerator = int(numerator_text) if numerator_text else 0
    denominator = 10 ** len(fraction_text)
    return Fraction(sign * numerator, denominator)


def exact_divide(numerator: Fraction | int, denominator: Fraction | int) -> Fraction:
    """Return an exact rational quotient without finite-context rounding."""

    left = _as_fraction(numerator)
    right = _as_fraction(denominator)
    if right == 0:
        raise NumericPolicyError("division denominator must be nonzero")
    return left / right


def compare_exact(left: Fraction | int, right: Fraction | int) -> int:
    """Compare two exact values using rational cross multiplication."""

    left_fraction = _as_fraction(left)
    right_fraction = _as_fraction(right)
    return (left_fraction > right_fraction) - (left_fraction < right_fraction)


def quantize(value: Fraction | int, quantum: Fraction | int, mode: RoundingMode) -> Fraction:
    """Quantize an exact value to an exact positive grid quantum."""

    resolved_value = _as_fraction(value)
    resolved_quantum = _positive_quantum(quantum)
    scaled = resolved_value / resolved_quantum
    if mode is RoundingMode.FLOOR:
        units = _floor_integer(scaled)
    elif mode is RoundingMode.CEIL:
        units = _ceil_integer(scaled)
    elif mode is RoundingMode.TRUNCATE:
        units = _trunc_integer(scaled)
    elif mode is RoundingMode.HALF_EVEN:
        units = _half_even_integer(scaled)
    else:
        raise NumericPolicyError(f"unsupported rounding mode: {mode!r}")
    return units * resolved_quantum


def floor_to_grid(value: Fraction | int, quantum: Fraction | int) -> Fraction:
    return quantize(value, quantum, RoundingMode.FLOOR)


def ceil_to_grid(value: Fraction | int, quantum: Fraction | int) -> Fraction:
    return quantize(value, quantum, RoundingMode.CEIL)


def truncate_to_grid(value: Fraction | int, quantum: Fraction | int) -> Fraction:
    return quantize(value, quantum, RoundingMode.TRUNCATE)


def half_even_to_grid(value: Fraction | int, quantum: Fraction | int) -> Fraction:
    return quantize(value, quantum, RoundingMode.HALF_EVEN)


def qcapital_floor(value: Fraction | int) -> QuantizedDecimal:
    return QuantizedDecimal(floor_to_grid(value, QCAPITAL), QCAPITAL, NumericValueClass.WIRE, TT_NUMERIC_POLICY_VERSION)


def qcapital_ceil(value: Fraction | int) -> QuantizedDecimal:
    return QuantizedDecimal(ceil_to_grid(value, QCAPITAL), QCAPITAL, NumericValueClass.WIRE, TT_NUMERIC_POLICY_VERSION)


def qratio_floor(value: Fraction | int) -> QuantizedDecimal:
    return QuantizedDecimal(floor_to_grid(value, QRATIO), QRATIO, NumericValueClass.REPORT_ONLY, TT_NUMERIC_POLICY_VERSION)


def q36_working(value: Fraction | int) -> QuantizedDecimal:
    return QuantizedDecimal(half_even_to_grid(value, Q36), Q36, NumericValueClass.WORKING, TT_SET_NUMERIC_POLICY_VERSION)


def q18_wire(value: Fraction | int) -> QuantizedDecimal:
    return QuantizedDecimal(half_even_to_grid(value, Q18), Q18, NumericValueClass.WIRE, TT_SET_NUMERIC_POLICY_VERSION)


def exact_midpoint_sqrt(value: Fraction | int, *, scale: int = 36) -> QuantizedDecimal:
    """Return sqrt(value) rounded HALF_EVEN to the decimal grid 10^-scale."""

    resolved_value = _as_fraction(value)
    if resolved_value < 0:
        raise NumericPolicyError("square root input must be nonnegative")
    if scale < 0:
        raise NumericPolicyError("square root scale must be nonnegative")
    factor = 10**scale
    numerator = resolved_value.numerator * factor * factor
    denominator = resolved_value.denominator
    k = isqrt(numerator // denominator)
    while (k + 1) * (k + 1) * denominator <= numerator:
        k += 1
    while k * k * denominator > numerator:
        k -= 1

    midpoint_left = 4 * numerator
    midpoint_right = denominator * (2 * k + 1) * (2 * k + 1)
    if midpoint_left > midpoint_right:
        k += 1
    elif midpoint_left == midpoint_right and k % 2:
        k += 1
    return QuantizedDecimal(Fraction(k, factor), Fraction(1, factor), NumericValueClass.WORKING, TT_SET_NUMERIC_POLICY_VERSION)


def canonical_decimal_text(value: Fraction | int) -> str:
    """Return policy canonical plain decimal text for a finite exact decimal."""

    resolved = _as_fraction(value)
    if resolved == 0:
        return "0"
    sign = "-" if resolved < 0 else ""
    numerator = abs(resolved.numerator)
    denominator = resolved.denominator
    twos = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    fives = 0
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise NumericPolicyError("nonterminating rational requires a governed quantizer before decimal serialization")
    scale = max(twos, fives)
    scaled = numerator * (2 ** (scale - twos)) * (5 ** (scale - fives))
    digits = str(scaled)
    if scale:
        digits = digits.rjust(scale + 1, "0")
        integer = digits[:-scale].lstrip("0") or "0"
        fraction = digits[-scale:].rstrip("0")
        text = integer if not fraction else f"{integer}.{fraction}"
    else:
        text = digits
    return f"{sign}{text}"


def _as_fraction(value: Fraction | int) -> Fraction:
    if isinstance(value, bool):
        raise NumericPolicyError("boolean is not a numeric value")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    raise NumericPolicyError(f"unsupported exact numeric type: {type(value).__name__}")


def _positive_quantum(value: Fraction | int) -> Fraction:
    quantum = _as_fraction(value)
    if quantum <= 0:
        raise NumericPolicyError("quantum must be positive")
    return quantum


def _floor_integer(value: Fraction) -> int:
    return value.numerator // value.denominator


def _ceil_integer(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def _trunc_integer(value: Fraction) -> int:
    return _floor_integer(value) if value >= 0 else _ceil_integer(value)


def _half_even_integer(value: Fraction) -> int:
    floor = _floor_integer(value)
    remainder_numerator = value.numerator - floor * value.denominator
    doubled = 2 * remainder_numerator
    if doubled < value.denominator:
        return floor
    if doubled > value.denominator:
        return floor + 1
    return floor if floor % 2 == 0 else floor + 1
