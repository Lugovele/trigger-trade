def test_package_import_does_not_require_secrets(monkeypatch):
    monkeypatch.delenv("TRIGGERTRADE_EXCHANGE_API_KEY", raising=False)
    monkeypatch.delenv("TRIGGERTRADE_EXCHANGE_API_SECRET", raising=False)

    import triggertrade
    from triggertrade.config import load_config

    assert triggertrade.__version__
    assert load_config().trading_mode == "paper"
