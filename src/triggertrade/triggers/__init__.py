"""Deterministic trigger boundary."""

from .contracts import Signal, SignalType
from .declarative_metric_predicate import (
    DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
    DECLARATIVE_METRIC_PREDICATE_SCHEMA,
    DeclarativeMetricPredicateConfig,
    DeclarativeMetricPredicateTrigger,
    DeclarativeTriggerConfigError,
    DeclarativeTriggerContext,
)
from .percentage_price_move import PercentagePriceMoveTrigger
from .registry import evaluate_declarative_metric_predicate, implementation_exists, implementation_key, is_declarative_metric_predicate
from .volume_confirmation import (
    RobustVolumeConfirmationTrigger,
    VolumeCandleWindow,
    VolumeConfirmationConfig,
    VolumeConfirmationEvaluation,
    VolumeConfirmationResult,
    empirical_percentile_rank,
    median_decimal,
)

__all__ = [
    "PercentagePriceMoveTrigger",
    "RobustVolumeConfirmationTrigger",
    "DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY",
    "DECLARATIVE_METRIC_PREDICATE_SCHEMA",
    "DeclarativeMetricPredicateConfig",
    "DeclarativeMetricPredicateTrigger",
    "DeclarativeTriggerConfigError",
    "DeclarativeTriggerContext",
    "Signal",
    "SignalType",
    "VolumeCandleWindow",
    "VolumeConfirmationConfig",
    "VolumeConfirmationEvaluation",
    "VolumeConfirmationResult",
    "evaluate_declarative_metric_predicate",
    "empirical_percentile_rank",
    "implementation_exists",
    "implementation_key",
    "is_declarative_metric_predicate",
    "median_decimal",
]
