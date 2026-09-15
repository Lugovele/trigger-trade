"""Native factual profile conformance review gates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class NativeProfileConformanceError(ValueError):
    pass


class NativeProfileStatus(StrEnum):
    REVIEWED = "REVIEWED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class NativeProfileEvidence:
    requirement: str
    status: NativeProfileStatus
    evidence: str

    def to_payload(self) -> dict[str, str]:
        return {
            "requirement": self.requirement,
            "status": self.status.value,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class NativeProfileConformanceReport:
    profile_id: str
    profile_revision: str
    exchange: str
    environment: str
    product: str
    smoke_evidence: dict[str, str]
    evidence: tuple[NativeProfileEvidence, ...]

    @property
    def certified(self) -> bool:
        return False

    @property
    def exposure_changing_enabled(self) -> bool:
        return False

    @property
    def unresolved_requirements(self) -> tuple[str, ...]:
        return tuple(item.requirement for item in self.evidence if item.status is NativeProfileStatus.UNRESOLVED)

    def to_payload(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "exchange": self.exchange,
            "environment": self.environment,
            "product": self.product,
            "certified": self.certified,
            "exposure_changing_enabled": self.exposure_changing_enabled,
            "smoke_evidence": dict(self.smoke_evidence),
            "evidence": [item.to_payload() for item in self.evidence],
            "unresolved_requirements": list(self.unresolved_requirements),
        }


def bybit_demo_native_profile_conformance(
    smoke_evidence: Mapping[str, Any] | None = None,
) -> NativeProfileConformanceReport:
    smoke = _smoke_evidence(smoke_evidence or {})
    return NativeProfileConformanceReport(
        profile_id="bybit-demo-linear-usdt-perpetual",
        profile_revision="native-profile-review-v1",
        exchange="BYBIT",
        environment="DEMO",
        product="LINEAR_USDT_PERPETUAL",
        smoke_evidence=smoke,
        evidence=(
            NativeProfileEvidence(
                "demo_linear_endpoint_scope",
                NativeProfileStatus.REVIEWED,
                "Opt-in smoke evidence confirms Demo endpoint, linear category, no spot calls, and no mainnet calls.",
            ),
            NativeProfileEvidence(
                "accepted_time_provenance",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md section 3 does not certify Bybit createdTime as original accepted/live time.",
            ),
            NativeProfileEvidence(
                "protective_child_linkage",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md section 2 requires empirical attachment-route proof before parent/child linkage is trusted.",
            ),
            NativeProfileEvidence(
                "protected_quantity_semantics",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md section 2 requires pinned mode proof before native quantity is treated as protected quantity.",
            ),
            NativeProfileEvidence(
                "chronology_sequence_scope",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md section 4 preserves nullable sequence evidence until a verified ordering profile exists.",
            ),
            NativeProfileEvidence(
                "mutable_order_state_ordering",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md consumer fact-merge clarification requires a pinned mutable ordering profile.",
            ),
            NativeProfileEvidence(
                "settlement_currency_conformance",
                NativeProfileStatus.UNRESOLVED,
                "NATIVE_FACT_PROFILE.md financial settlement-currency section leaves runtime currency support uncertified.",
            ),
        ),
    )


def _smoke_evidence(raw: Mapping[str, Any]) -> dict[str, str]:
    if not raw:
        return {"available": "false"}
    evidence = {str(key): str(value) for key, value in raw.items()}
    expected = {
        "demo_endpoint": "OK",
        "category": "linear",
        "spot_calls": "0",
        "mainnet_calls": "0",
    }
    for key, value in expected.items():
        if evidence.get(key) != value:
            raise NativeProfileConformanceError(f"Bybit Demo native profile smoke evidence failed {key}")
    return evidence
