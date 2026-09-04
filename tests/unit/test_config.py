import pytest

from triggertrade.config import ConfigError, TradingMode, load_config


def test_load_config_defaults_to_safe_paper_mode_without_secrets():
    config = load_config({})

    assert config.trading_mode is TradingMode.PAPER
    assert config.exchange.name == "paper"


def test_live_mode_requires_explicit_non_placeholder_secrets():
    with pytest.raises(ConfigError):
        load_config(
            {
                "TRIGGERTRADE_TRADING_MODE": "live",
                "TRIGGERTRADE_EXCHANGE_API_KEY": "replace-with-local-secret",
                "TRIGGERTRADE_EXCHANGE_API_SECRET": "replace-with-local-secret",
            }
        )


def test_invalid_trading_mode_fails_closed():
    with pytest.raises(ConfigError):
        load_config({"TRIGGERTRADE_TRADING_MODE": "enabled"})
