import pytest

from triggertrade.config import ConfigError, Market, load_bybit_credentials, load_config
from triggertrade.services.runtime import validate_bybit_demo_private_runtime_env, validate_bybit_demo_runtime_env


def test_bybit_demo_base_url_selection():
    config = load_config(
        {
            "TRIGGERTRADE_EXCHANGE": "bybit",
            "TRIGGERTRADE_BYBIT_ENV": "demo",
            "BYBIT_BASE_URL": "https://api-demo.bybit.com",
            "TRIGGERTRADE_MARKET": "spot",
            "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        }
    )

    assert config.exchange.name == "bybit"
    assert config.bybit.base_url == "https://api-demo.bybit.com"
    assert config.market is Market.SPOT
    assert config.watchlist[0].symbol == "BTCUSDT"


def test_linear_market_is_supported_for_futures_runtime():
    config = load_config({"TRIGGERTRADE_MARKET": "linear"})

    assert config.market is Market.LINEAR
    assert config.futures_runtime.category == "linear"


def test_live_trading_enabled_fails_closed():
    with pytest.raises(ConfigError):
        load_config(
            {
                "TRIGGERTRADE_TRADING_MODE": "paper",
                "TRIGGERTRADE_LIVE_TRADING_ENABLED": "true",
                "BYBIT_API_KEY": "unit-key",
                "BYBIT_API_SECRET": "unit-signing-value",
            }
        )


def test_missing_required_credentials_fail_for_private_connectivity():
    with pytest.raises(ConfigError):
        load_bybit_credentials({})


def test_credentials_repr_does_not_leak_secret():
    credentials = load_bybit_credentials(
        {"BYBIT_API_KEY": "unit-key", "BYBIT_API_SECRET": "unit-signing-value"}
    )

    assert "unit-signing-value" not in repr(credentials)
    assert "unit-key" not in repr(credentials)


def test_private_bybit_demo_runtime_contract_requires_explicit_safe_endpoint():
    env = {
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api-demo.bybit.com",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "BYBIT_API_KEY": "unit-key",
        "BYBIT_API_SECRET": "unit-signing-value",
    }
    config = load_config(env)

    validate_bybit_demo_private_runtime_env(env, config)


def test_public_bybit_demo_runtime_contract_does_not_require_secrets():
    env = {
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api-demo.bybit.com",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
    }
    config = load_config(env)

    validate_bybit_demo_runtime_env(env, config)


def test_private_bybit_demo_runtime_contract_rejects_missing_explicit_base_url():
    env = {
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "BYBIT_API_KEY": "unit-key",
        "BYBIT_API_SECRET": "unit-signing-value",
    }
    config = load_config(env)

    with pytest.raises(ConfigError, match="BYBIT_BASE_URL"):
        validate_bybit_demo_private_runtime_env(env, config)


def test_private_bybit_demo_runtime_contract_rejects_live_url_mismatch():
    env = {
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api.bybit.com",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "BYBIT_API_KEY": "unit-key",
        "BYBIT_API_SECRET": "unit-signing-value",
    }
    config = load_config(env)

    with pytest.raises(ConfigError, match="BYBIT_BASE_URL"):
        validate_bybit_demo_private_runtime_env(env, config)
