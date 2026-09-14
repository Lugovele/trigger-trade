"""Strategy boundary for converting signals into trade intents."""

__all__ = [
    "BuyCandidateStrategy",
    "FuturesStrategyDecision",
    "IntegrationDirectionalFuturesStrategy",
    "RegimeStrategyContext",
    "STR_FUT_RULE_ID",
    "STR_FUT_VERSION",
    "StrategyContextInterpretation",
]


def __getattr__(name: str):
    if name == "BuyCandidateStrategy":
        from .buy_candidate import BuyCandidateStrategy

        return BuyCandidateStrategy
    if name in {"RegimeStrategyContext", "StrategyContextInterpretation"}:
        from . import context

        return getattr(context, name)
    if name in {"STR_FUT_RULE_ID", "STR_FUT_VERSION", "FuturesStrategyDecision", "IntegrationDirectionalFuturesStrategy"}:
        from . import futures_directional

        return getattr(futures_directional, name)
    raise AttributeError(name)
