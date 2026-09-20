"""Generic immutable content-binding helpers for owner-local identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from triggertrade.canonical_json import CanonicalJsonError, canonical_json_digest


class IdentifierBindingError(ValueError):
    """Raised when an immutable identifier binding is malformed or conflicting."""


@dataclass(frozen=True)
class ImmutableBinding:
    """An opaque identity bound to exact canonical content."""

    identity: str
    content_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity or "\x00" in self.identity:
            raise IdentifierBindingError("identity is required")
        if not isinstance(self.content_digest, str) or len(self.content_digest) != 64:
            raise IdentifierBindingError("content_digest must be a sha256 hex digest")
        if any(char not in "0123456789abcdef" for char in self.content_digest):
            raise IdentifierBindingError("content_digest must be a sha256 hex digest")


def bind_immutable_content(identity: str, content: Mapping[str, Any]) -> ImmutableBinding:
    """Bind an existing opaque identity to exact canonical content bytes."""

    try:
        digest = canonical_json_digest(content)
    except CanonicalJsonError as exc:
        raise IdentifierBindingError(str(exc)) from exc
    return ImmutableBinding(identity=identity, content_digest=digest)


def ensure_same_binding(existing: ImmutableBinding, incoming: ImmutableBinding) -> None:
    """Reject a same-identity replay whose canonical content has changed."""

    if existing.identity == incoming.identity and existing.content_digest != incoming.content_digest:
        raise IdentifierBindingError(f"conflicting immutable binding for identity: {existing.identity}")


def bindings_conflict(existing: ImmutableBinding, incoming: ImmutableBinding) -> bool:
    """Return whether two bindings prove changed content for the same identity."""

    return existing.identity == incoming.identity and existing.content_digest != incoming.content_digest
