"""Canonical JSON serialization and digests for TriggerTrade contracts."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


class CanonicalJsonError(TypeError):
    """Raised when a value cannot be encoded as TriggerTrade canonical JSON."""


def canonical_json_text(value: Any) -> str:
    """Return sorted-key compact UTF-8 JSON text for supported values."""

    return _encode(value)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the UTF-8 bytes covered by canonical digests."""

    return canonical_json_text(value).encode("utf-8")


def canonical_json_digest(value: Any) -> str:
    """Return the SHA-256 hex digest of the canonical JSON bytes."""

    return sha256(canonical_json_bytes(value)).hexdigest()


def canonical_decimal_text(value: Decimal) -> str:
    """Return a canonical JSON-number spelling for a finite Decimal."""

    if not value.is_finite():
        raise CanonicalJsonError("canonical decimals must be finite")
    if value.is_zero():
        return "0"
    sign, digits, exponent = value.as_tuple()
    digit_text = "".join(str(digit) for digit in digits)
    if exponent >= 0:
        integer = digit_text + ("0" * exponent)
        fraction = ""
    else:
        split_at = len(digit_text) + exponent
        if split_at > 0:
            integer = digit_text[:split_at]
            fraction = digit_text[split_at:]
        else:
            integer = "0"
            fraction = ("0" * abs(split_at)) + digit_text

    integer = integer.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    numeric = integer if not fraction else f"{integer}.{fraction}"
    return f"-{numeric}" if sign else numeric


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        return canonical_decimal_text(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, Mapping):
        return _encode_mapping(value)
    if isinstance(value, (tuple, list)):
        return "[" + ",".join(_encode(item) for item in value) + "]"
    if isinstance(value, float):
        raise CanonicalJsonError("binary floats are not supported in canonical JSON")
    raise CanonicalJsonError(f"unsupported canonical JSON type: {type(value).__name__}")


def _encode_mapping(value: Mapping[Any, Any]) -> str:
    items: list[tuple[str, Any]] = []
    seen_keys: set[str] = set()
    for key, item in value.items():
        if not isinstance(key, str):
            raise CanonicalJsonError("canonical JSON object keys must be strings")
        if key in seen_keys:
            raise CanonicalJsonError(f"duplicate canonical JSON object key: {key}")
        seen_keys.add(key)
        items.append((key, item))
    items.sort(key=lambda pair: pair[0])
    encoded_items = (
        f"{json.dumps(key, ensure_ascii=False, separators=(',', ':'))}:{_encode(item)}"
        for key, item in items
    )
    return "{" + ",".join(encoded_items) + "}"
