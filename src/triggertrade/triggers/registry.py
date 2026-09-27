"""Trigger implementation resolution helpers."""

from __future__ import annotations

from triggertrade.trigger_sets import RuleDefinition

from .declarative_metric_predicate import (
    DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
    DeclarativeMetricPredicateTrigger,
    DeclarativeTriggerContext,
)
from .percentage_price_move import PercentagePriceMoveTrigger
from .volume_confirmation import RobustVolumeConfirmationTrigger


PERCENTAGE_PRICE_MOVE_IMPLEMENTATION_KEY = "triggertrade.triggers.PercentagePriceMoveTrigger"
ROBUST_VOLUME_CONFIRMATION_IMPLEMENTATION_KEY = "triggertrade.triggers.RobustVolumeConfirmationTrigger"


def implementation_key(rule: RuleDefinition) -> str:
    explicit = rule.definition.get("implementation_key")
    if explicit:
        return str(explicit)
    known = {
        "TRG-001": PERCENTAGE_PRICE_MOVE_IMPLEMENTATION_KEY,
        "TRG-002": ROBUST_VOLUME_CONFIRMATION_IMPLEMENTATION_KEY,
    }
    return known.get(rule.rule_id, "")


def is_declarative_metric_predicate(rule: RuleDefinition) -> bool:
    return implementation_key(rule) == DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY


def implementation_exists(key: str) -> bool:
    return key in {
        PERCENTAGE_PRICE_MOVE_IMPLEMENTATION_KEY,
        ROBUST_VOLUME_CONFIRMATION_IMPLEMENTATION_KEY,
        DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
    }


def evaluate_declarative_metric_predicate(rule: RuleDefinition, context: DeclarativeTriggerContext):
    return DeclarativeMetricPredicateTrigger(rule).evaluate(context)
