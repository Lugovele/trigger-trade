"""Explicit UTC-bound source boundary for prospective capture receipts.

No repository component currently measures a trustworthy UTC error bound.
Production defaults to unverified until a separately validated source is
installed. Host wall time or a Bybit server timestamp alone cannot attest it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from .bybit_rest_source import CollectorClockEvidence
from .source import utc


class ClockAttestationError(ValueError):
    """An external source supplied an invalid receipt-specific UTC bound."""


@dataclass(frozen=True)
class UtcReceiptBound:
    receipt_ref: str
    verified_at: datetime
    maximum_error: timedelta
    authority_reference: str


class TrustedUtcBoundSource(Protocol):
    """Deployment-supplied source with an independently established error bound."""

    def bound_receipt(self, receipt_ref: str, received_at: datetime) -> UtcReceiptBound | None: ...


class UnverifiedClockAttestor:
    """Fail-closed production default when no bounded UTC source is installed."""

    def __call__(self, receipt_ref: str, received_at: datetime) -> None:
        return None


class ExternalBoundClockAttestor:
    """Validate a receipt-specific bound from an explicitly trusted source."""

    def __init__(self, source: TrustedUtcBoundSource) -> None:
        self._source = source

    def __call__(self, receipt_ref: str, received_at: datetime) -> CollectorClockEvidence | None:
        received = utc(received_at)
        bound = self._source.bound_receipt(receipt_ref, received)
        if bound is None:
            return None
        try:
            verified = utc(bound.verified_at)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ClockAttestationError("UTC bound timestamp is invalid") from exc
        if (bound.receipt_ref != receipt_ref or verified != received or
                not bound.authority_reference or not isinstance(bound.maximum_error, timedelta) or
                bound.maximum_error < timedelta(0)):
            raise ClockAttestationError("UTC bound does not cover this receipt")
        return CollectorClockEvidence(
            bound.authority_reference, receipt_ref, received, bound.maximum_error)
