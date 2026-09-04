import importlib


def test_primary_module_boundaries_are_importable():
    modules = [
        "triggertrade.config",
        "triggertrade.market_data",
        "triggertrade.triggers",
        "triggertrade.strategies",
        "triggertrade.risk",
        "triggertrade.execution",
        "triggertrade.exchanges",
        "triggertrade.persistence",
        "triggertrade.services",
        "triggertrade.dashboard",
        "triggertrade.exchanges.bybit",
        "triggertrade.market_data.bybit",
    ]

    for module in modules:
        assert importlib.import_module(module)


def test_execution_and_exchange_contracts_are_available():
    execution = importlib.import_module("triggertrade.execution")
    exchanges = importlib.import_module("triggertrade.exchanges")

    assert hasattr(execution, "OrderStatus")
    assert hasattr(execution, "ExecutionService")
    assert hasattr(execution, "TradeIntent")
    assert hasattr(exchanges, "ExchangeAdapter")
