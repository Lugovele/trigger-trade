from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from triggertrade.exchanges import BybitResponse
from triggertrade.execution.futures import PositionAction
from triggertrade.instruments import CatalogError, InstrumentExclusionReason, PriceNormalizationPurpose
from triggertrade.persistence import InstrumentCatalogStore, TradingRulesStore
from triggertrade.rules import CoinRule, TradingRulesError, TradingRulesService
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from tests.unit.test_trading_rules_registry import _config


class PagedClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def linear_instruments_info(self, *, cursor=None, limit=1000):
        self.calls.append((cursor, limit))
        return BybitResponse(0, "OK", self.pages[cursor])


def test_refresh_fetches_all_pages_dedupes_and_persists_tradeable_catalog(tmp_path):
    store = InstrumentCatalogStore(tmp_path / "catalog.sqlite3")
    client = PagedClient(
        {
            None: {"list": [_item("BTCUSDT"), _item("ETHUSDT")], "nextPageCursor": "next"},
            "next": {"list": [_item("BTCUSDT"), _item("SOLUSDT")], "nextPageCursor": ""},
        }
    )
    service = InstrumentCatalogService(store=store, client=client, clock=lambda: _now())

    result = service.refresh_instrument_catalog()

    assert client.calls == [(None, 1000), ("next", 1000)]
    assert result.status == "OK"
    assert result.fetched_count == 3
    assert result.tradeable_count == 3
    assert [item.symbol for item in service.list_tradeable_instruments()] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    assert service.get_instrument("btcusdt").catalog_hash == result.catalog_hash



def test_empty_or_malformed_success_response_preserves_previous_cache(tmp_path):
    path = tmp_path / "catalog.sqlite3"
    service = _catalog_service(tmp_path, db_path=path)
    assert [item.symbol for item in service.list_tradeable_instruments()] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    empty = InstrumentCatalogService(
        store=InstrumentCatalogStore(path),
        client=PagedClient({None: {"list": [], "nextPageCursor": ""}}),
        clock=lambda: _now() + timedelta(minutes=3),
    )
    result = empty.refresh_instrument_catalog()

    assert result.status == "FAILED"
    assert [item.symbol for item in empty.list_tradeable_instruments()] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    malformed = InstrumentCatalogService(
        store=InstrumentCatalogStore(path),
        client=PagedClient({None: {"nextPageCursor": ""}}),
        clock=lambda: _now() + timedelta(minutes=4),
    )
    assert malformed.refresh_instrument_catalog().status == "FAILED"
    assert [item.symbol for item in malformed.list_tradeable_instruments()] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def test_refresh_cursor_loop_fails_without_replacing_previous_cache(tmp_path):
    store = InstrumentCatalogStore(tmp_path / "catalog.sqlite3")
    ok = InstrumentCatalogService(store=store, client=PagedClient({None: {"list": [_item("BTCUSDT")], "nextPageCursor": ""}}), clock=lambda: _now())
    assert ok.refresh_instrument_catalog().status == "OK"
    failing = InstrumentCatalogService(
        store=store,
        client=PagedClient(
            {
                None: {"list": [_item("ETHUSDT")], "nextPageCursor": "loop"},
                "loop": {"list": [_item("SOLUSDT")], "nextPageCursor": "loop"},
            }
        ),
        clock=lambda: _now() + timedelta(minutes=1),
    )

    result = failing.refresh_instrument_catalog()

    assert result.status == "FAILED"
    assert [item.symbol for item in failing.list_tradeable_instruments()] == ["BTCUSDT"]


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"quoteCoin": "USDC"}, InstrumentExclusionReason.WRONG_PRODUCT),
        ({"settleCoin": "USDC"}, InstrumentExclusionReason.WRONG_SETTLE_COIN),
        ({"contractType": "LinearFutures"}, InstrumentExclusionReason.NOT_PERPETUAL),
        ({"status": "PreLaunch"}, InstrumentExclusionReason.NOT_TRADING),
        ({"priceFilter": {"tickSize": "0"}}, InstrumentExclusionReason.INCOMPLETE_METADATA),
        ({"lotSizeFilter": {"qtyStep": "0", "minOrderQty": "0.001", "maxOrderQty": "100", "minNotionalValue": "5"}}, InstrumentExclusionReason.INCOMPLETE_METADATA),
        ({"lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "maxOrderQty": "100"}}, InstrumentExclusionReason.INCOMPLETE_METADATA),
        ({"leverageFilter": {"maxLeverage": "100", "leverageStep": "0.01"}}, InstrumentExclusionReason.INCOMPLETE_METADATA),
        ({"leverageFilter": {"minLeverage": "1", "maxLeverage": "100"}}, InstrumentExclusionReason.INCOMPLETE_METADATA),
    ],
)
def test_product_filtering_marks_non_tradeable_instruments(tmp_path, overrides, reason):
    item = _item("BTCUSDT", **overrides)
    service = InstrumentCatalogService(
        store=InstrumentCatalogStore(tmp_path / "catalog.sqlite3"),
        client=PagedClient({None: {"list": [item], "nextPageCursor": ""}}),
        clock=lambda: _now(),
    )

    service.refresh_instrument_catalog()
    instrument = service.get_instrument("BTCUSDT")

    assert instrument.is_tradeable is False
    assert instrument.exclusion_reason == reason
    with pytest.raises(CatalogError):
        service.validate_symbol("BTCUSDT")


def test_price_normalization_is_direction_aware_for_protective_orders(tmp_path):
    service = _catalog_service(tmp_path)

    assert service.normalize_price("BTCUSDT", Decimal("101.07"), purpose=PriceNormalizationPurpose.TAKE_PROFIT, action=PositionAction.OPEN_LONG) == Decimal("101.0")
    assert service.normalize_price("BTCUSDT", Decimal("99.94"), purpose=PriceNormalizationPurpose.STOP_LOSS, action=PositionAction.OPEN_LONG) == Decimal("100.0")
    assert service.normalize_price("BTCUSDT", Decimal("98.93"), purpose=PriceNormalizationPurpose.TAKE_PROFIT, action=PositionAction.OPEN_SHORT) == Decimal("99.0")
    assert service.normalize_price("BTCUSDT", Decimal("100.06"), purpose=PriceNormalizationPurpose.STOP_LOSS, action=PositionAction.OPEN_SHORT) == Decimal("100.0")


def test_qty_normalization_enforces_step_min_max_and_min_notional(tmp_path):
    service = _catalog_service(tmp_path)

    assert service.normalize_qty("BTCUSDT", Decimal("1.2349"), price=Decimal("100")) == Decimal("1.234")

    with pytest.raises(CatalogError, match="minimum order"):
        service.normalize_qty("BTCUSDT", Decimal("0.0009"), price=Decimal("100"))
    with pytest.raises(CatalogError, match="maximum"):
        service.normalize_qty("BTCUSDT", Decimal("101"), price=Decimal("100"))
    with pytest.raises(CatalogError, match="minimum notional"):
        service.normalize_qty("BTCUSDT", Decimal("0.01"), price=Decimal("100"))


def test_rules_version_creation_validates_enabled_coins_against_catalog(tmp_path):
    catalog = _catalog_service(tmp_path)
    service = TradingRulesService(TradingRulesStore(tmp_path / "rules.sqlite3"), symbol_validator=catalog.validate_symbol)
    service.ensure_initial_version(_config(tmp_path / "rules.sqlite3"))

    accepted = service.create_rules_version_from_current(changes={"coins": (CoinRule("ETHUSDT", True, None),)}, created_source="unit")
    assert accepted.changed is True
    assert accepted.rules.draft.coins == (CoinRule("ETHUSDT", True, None),)

    with pytest.raises(TradingRulesError, match="catalog"):
        service.create_rules_version_from_current(changes={"coins": (CoinRule("DOGEUSDT", True, None),)}, created_source="unit")


def test_historical_rules_version_remains_immutable_after_catalog_update(tmp_path):
    path = tmp_path / "catalog.sqlite3"
    catalog = _catalog_service(tmp_path, db_path=path)
    rules = TradingRulesService(TradingRulesStore(tmp_path / "rules.sqlite3"), symbol_validator=catalog.validate_symbol)
    rules.ensure_initial_version(_config(tmp_path / "rules.sqlite3"))
    v2 = rules.create_rules_version_from_current(changes={"coins": (CoinRule("ETHUSDT", True, None),)}, created_source="unit").rules

    replacement = InstrumentCatalogService(
        store=InstrumentCatalogStore(path),
        client=PagedClient({None: {"list": [_item("ETHUSDT", status="PreLaunch")], "nextPageCursor": ""}}),
        clock=lambda: _now() + timedelta(minutes=2),
    )
    replacement.refresh_instrument_catalog()

    assert rules.get_rules_version(v2.rules_version_id).draft.coins == (CoinRule("ETHUSDT", True, None),)
    with pytest.raises(TradingRulesError, match="catalog"):
        rules.create_rules_version_from_current(changes={"coins": (CoinRule("ETHUSDT", True, None),)}, created_source="unit")


def test_cached_catalog_staleness_and_search(tmp_path):
    service = _catalog_service(tmp_path, clock=lambda: _now(), stale_after=timedelta(seconds=1))
    assert service.catalog_is_stale() is False

    later = InstrumentCatalogService(store=service._store, client=None, clock=lambda: _now() + timedelta(seconds=2), stale_after=timedelta(seconds=1))
    assert later.catalog_is_stale() is True
    assert [item["symbol"] for item in later.list_tradeable_coins(search="eth")] == ["ETHUSDT"]


def _catalog_service(tmp_path, *, db_path=None, clock=lambda: _now(), stale_after=timedelta(hours=24)):
    service = InstrumentCatalogService(
        store=InstrumentCatalogStore(db_path or tmp_path / "catalog.sqlite3"),
        client=PagedClient({None: {"list": [_item("BTCUSDT"), _item("ETHUSDT"), _item("SOLUSDT")], "nextPageCursor": ""}}),
        clock=clock,
        stale_after=stale_after,
    )
    assert service.refresh_instrument_catalog().status == "OK"
    return service


def _now():
    return datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def _item(symbol, **overrides):
    data = {
        "symbol": symbol,
        "baseCoin": symbol.removesuffix("USDT"),
        "quoteCoin": "USDT",
        "settleCoin": "USDT",
        "contractType": "LinearPerpetual",
        "status": "Trading",
        "priceScale": "1",
        "priceFilter": {"tickSize": "0.1"},
        "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "maxOrderQty": "100", "minNotionalValue": "5", "maxMktOrderQty": "50"},
        "leverageFilter": {"minLeverage": "1", "maxLeverage": "100", "leverageStep": "0.01"},
        "launchTime": "1700000000000",
        "deliveryTime": "0",
    }
    data.update(overrides)
    return data
