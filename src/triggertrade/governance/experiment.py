"""Deterministic intraday TEST Trigger Set evidence governance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvidenceReadiness(StrEnum):
    COLLECTING = "COLLECTING"
    EARLY = "EARLY"
    REVIEW_READY = "REVIEW_READY"
    STRONG_EVIDENCE = "STRONG_EVIDENCE"
    INSUFFICIENT_DIVERSITY = "INSUFFICIENT_DIVERSITY"
    BLOCKED = "BLOCKED"


class RecommendationAction(StrEnum):
    CONTINUE_TEST = "CONTINUE_TEST"
    EXTEND_SAMPLE = "EXTEND_SAMPLE"
    CREATE_NEW_VERSION = "CREATE_NEW_VERSION"
    COMPARE_WITH_BASELINE = "COMPARE_WITH_BASELINE"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    READY_FOR_PROMOTION_REVIEW = "READY_FOR_PROMOTION_REVIEW"


class EvidenceCapability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GovernancePolicy:
    policy_id: str = "intraday-governance-defaults"
    version: str = "0.1.0"
    minimum_age_days: int = 7
    minimum_candidate_signals: int = 100
    minimum_closed_trades: int = 50
    strong_evidence_multiplier: int = 2
    regime_diversity_required: bool = False


@dataclass(frozen=True)
class GovernanceEvidence:
    testing_started_at: str
    age_days: int
    signals_observed: int
    closed_trades_observed: int | None
    closed_trades_capability: EvidenceCapability
    regime_coverage: str | None
    regime_capability: EvidenceCapability
    baseline_comparison_available: bool
    critical_failures: int = 0
    explicit_rejection: bool = False
    new_version_recommended: bool = False


@dataclass(frozen=True)
class GovernanceResult:
    policy_id: str
    policy_version: str
    testing_started_at: str
    age_days: int
    signals_observed: int
    closed_trades_observed: int | None
    remaining_age_days_to_gate: int
    remaining_signals_to_gate: int
    remaining_trades_to_gate: int | None
    regime_coverage: str
    readiness: EvidenceReadiness
    recommendation_action: RecommendationAction
    blocking_reasons: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    comparison_available: bool


def evaluate_readiness(evidence: GovernanceEvidence, policy: GovernancePolicy | None = None) -> GovernanceResult:
    """Evaluate review readiness without promotion or trading side effects."""

    policy = policy or GovernancePolicy()
    remaining_age = max(policy.minimum_age_days - evidence.age_days, 0)
    remaining_signals = max(policy.minimum_candidate_signals - evidence.signals_observed, 0)
    remaining_trades = None
    gaps: list[str] = []
    blockers: list[str] = []

    if evidence.critical_failures > 0:
        blockers.append(f"{evidence.critical_failures} critical runtime failure(s) recorded")
    if remaining_age:
        gaps.append(f"{evidence.age_days} / {policy.minimum_age_days} required calendar days")
    if remaining_signals:
        gaps.append(f"{evidence.signals_observed} / {policy.minimum_candidate_signals} required candidate signals")
    if evidence.closed_trades_capability is EvidenceCapability.UNAVAILABLE:
        gaps.append("closed trade accounting unavailable")
    else:
        closed = evidence.closed_trades_observed or 0
        remaining_trades = max(policy.minimum_closed_trades - closed, 0)
        if remaining_trades:
            gaps.append(f"{closed} / {policy.minimum_closed_trades} required closed trades")
    if policy.regime_diversity_required and evidence.regime_capability is EvidenceCapability.UNAVAILABLE:
        blockers.append("regime diversity unavailable")
    elif policy.regime_diversity_required and not evidence.regime_coverage:
        blockers.append("regime diversity insufficient")
    if not evidence.baseline_comparison_available:
        gaps.append("baseline comparison unavailable")

    if evidence.explicit_rejection:
        readiness = EvidenceReadiness.BLOCKED
        action = RecommendationAction.REJECT_CANDIDATE
        blockers.append("candidate explicitly rejected")
    elif blockers:
        readiness = EvidenceReadiness.BLOCKED
        action = RecommendationAction.EXTEND_SAMPLE
    elif not gaps:
        strong_signal_gate = policy.minimum_candidate_signals * policy.strong_evidence_multiplier
        strong_trade_gate = policy.minimum_closed_trades * policy.strong_evidence_multiplier
        if (
            evidence.signals_observed >= strong_signal_gate
            and evidence.closed_trades_observed is not None
            and evidence.closed_trades_observed >= strong_trade_gate
        ):
            readiness = EvidenceReadiness.STRONG_EVIDENCE
        else:
            readiness = EvidenceReadiness.REVIEW_READY
        action = RecommendationAction.READY_FOR_PROMOTION_REVIEW
    elif evidence.new_version_recommended:
        readiness = EvidenceReadiness.EARLY
        action = RecommendationAction.CREATE_NEW_VERSION
    elif evidence.signals_observed > 0 or evidence.age_days > 0:
        readiness = EvidenceReadiness.EARLY
        action = RecommendationAction.EXTEND_SAMPLE
    else:
        readiness = EvidenceReadiness.COLLECTING
        action = RecommendationAction.CONTINUE_TEST

    return GovernanceResult(
        policy_id=policy.policy_id,
        policy_version=policy.version,
        testing_started_at=evidence.testing_started_at,
        age_days=evidence.age_days,
        signals_observed=evidence.signals_observed,
        closed_trades_observed=evidence.closed_trades_observed,
        remaining_age_days_to_gate=remaining_age,
        remaining_signals_to_gate=remaining_signals,
        remaining_trades_to_gate=remaining_trades,
        regime_coverage=evidence.regime_coverage or "unavailable",
        readiness=readiness,
        recommendation_action=action,
        blocking_reasons=tuple(blockers),
        evidence_gaps=tuple(gaps),
        comparison_available=evidence.baseline_comparison_available,
    )
