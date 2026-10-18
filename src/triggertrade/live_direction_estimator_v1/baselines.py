"""Fixed B0–B3 in-memory baseline states; source sign is supplied by caller."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Iterable

from . import SPEC_ID, SPEC_VERSION
from .calibration import hard_class
from .model import CLASSES
from .source import SYMBOLS


@dataclass(frozen=True)
class BaselineFitRow:
    physical_symbol: str
    label: str
    trailing_h_sign: int


def _check(symbol: str, sign: int | None = None) -> int:
    if symbol not in SYMBOLS or (sign is not None and sign not in (-1, 0, 1)):
        raise ValueError("invalid physical symbol or trailing-H sign")
    return SYMBOLS.index(symbol)


@dataclass(frozen=True)
class BaselineState:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]
    sign_counts_by_symbol_bin_class: tuple[tuple[tuple[int, int, int], ...], ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_json(cls, data: str) -> BaselineState:
        d = json.loads(data)
        d["counts_by_symbol_class"] = tuple(tuple(a) for a in d["counts_by_symbol_class"])
        d["sign_counts_by_symbol_bin_class"] = tuple(tuple(tuple(b) for b in a) for a in d["sign_counts_by_symbol_bin_class"])
        result = cls(**d)
        if result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or result.horizon_minutes not in (60, 120):
            raise ValueError("incompatible baseline artifact")
        return result

    def b0_symbol_majority(self, symbol: str) -> str:
        return hard_class(self.counts_by_symbol_class[_check(symbol)])

    def b1_symbol_prior(self, symbol: str) -> tuple[float, float, float]:
        counts = self.counts_by_symbol_class[_check(symbol)]
        total = sum(counts)
        return tuple((n + 0.5) / (total + 1.5) for n in counts)

    def b3_symbol_sign_frequency(self, symbol: str, sign: int) -> tuple[float, float, float]:
        index = _check(symbol, sign)
        counts = self.sign_counts_by_symbol_bin_class[index][sign + 1]
        prior = self.b1_symbol_prior(symbol)
        total = sum(counts)
        if total == 0:
            return prior
        return tuple((counts[c] + 3 * prior[c]) / (total + 3) for c in range(3))

    def b0_state(self) -> B0State:
        return B0State(self.spec_id, self.spec_version, self.horizon_minutes, self.counts_by_symbol_class)

    def b1_state(self) -> B1State:
        return B1State(self.spec_id, self.spec_version, self.horizon_minutes, self.counts_by_symbol_class)

    def b3_state(self) -> B3State:
        return B3State(self.spec_id, self.spec_version, self.horizon_minutes, self.counts_by_symbol_class,
                       self.sign_counts_by_symbol_bin_class)


def _read_state(data: str, expected: str, cls: type) -> object:
    d = json.loads(data)
    if d.pop("baseline_id") != expected:
        raise ValueError("wrong baseline ID")
    d["counts_by_symbol_class"] = tuple(tuple(a) for a in d["counts_by_symbol_class"])
    if "sign_counts_by_symbol_bin_class" in d:
        d["sign_counts_by_symbol_bin_class"] = tuple(tuple(tuple(b) for b in a) for a in d["sign_counts_by_symbol_bin_class"])
    result = cls(**d)
    if result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or result.horizon_minutes not in (60, 120):
        raise ValueError("incompatible baseline state")
    return result


def _state_json(value: object, baseline_id: str) -> str:
    return json.dumps({**asdict(value), "baseline_id": baseline_id}, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class B0State:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]

    def predict(self, symbol: str) -> str:
        return hard_class(self.counts_by_symbol_class[_check(symbol)])

    def to_json(self) -> str:
        return _state_json(self, "B0_SYMBOL_MAJORITY")

    @classmethod
    def from_json(cls, data: str) -> B0State:
        return _read_state(data, "B0_SYMBOL_MAJORITY", cls)


@dataclass(frozen=True)
class B1State:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]

    def predict(self, symbol: str) -> tuple[float, float, float]:
        counts = self.counts_by_symbol_class[_check(symbol)]
        total = sum(counts)
        return tuple((n + 0.5) / (total + 1.5) for n in counts)

    def to_json(self) -> str:
        return _state_json(self, "B1_SYMBOL_PRIOR")

    @classmethod
    def from_json(cls, data: str) -> B1State:
        return _read_state(data, "B1_SYMBOL_PRIOR", cls)


@dataclass(frozen=True)
class B3State:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]
    sign_counts_by_symbol_bin_class: tuple[tuple[tuple[int, int, int], ...], ...]

    def predict(self, symbol: str, sign: int) -> tuple[float, float, float]:
        index = _check(symbol, sign)
        counts = self.sign_counts_by_symbol_bin_class[index][sign + 1]
        prior = B1State(self.spec_id, self.spec_version, self.horizon_minutes,
                        self.counts_by_symbol_class).predict(symbol)
        total = sum(counts)
        return prior if total == 0 else tuple((counts[c] + 3 * prior[c]) / (total + 3) for c in range(3))

    def to_json(self) -> str:
        return _state_json(self, "B3_SYMBOL_SIGN_FREQUENCY")

    @classmethod
    def from_json(cls, data: str) -> B3State:
        return _read_state(data, "B3_SYMBOL_SIGN_FREQUENCY", cls)


def b2_trailing_h_sign(sign: int) -> str:
    if sign not in (-1, 0, 1):
        raise ValueError("trailing-H sign must be -1, 0, or +1")
    return CLASSES[0 if sign == 1 else 1 if sign == -1 else 2]


def fit_baselines(rows: Iterable[BaselineFitRow], *, horizon_minutes: int) -> BaselineState:
    if horizon_minutes not in (60, 120):
        raise ValueError("horizon must be 60 or 120")
    counts = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(4)]
    for row in rows:
        s = _check(row.physical_symbol, row.trailing_h_sign)
        if row.label not in CLASSES:
            raise ValueError("invalid class")
        counts[s][row.trailing_h_sign + 1][CLASSES.index(row.label)] += 1
    totals = tuple(tuple(sum(counts[s][b][c] for b in range(3)) for c in range(3)) for s in range(4))
    if any(sum(row) == 0 for row in totals):
        raise ValueError("baseline fit requires every physical symbol")
    return BaselineState(SPEC_ID, SPEC_VERSION, horizon_minutes, totals,
                         tuple(tuple(tuple(bin_counts) for bin_counts in symbol) for symbol in counts))
