from decimal import Decimal

from triggertrade.market_data import (
    parse_spot_candles,
    parse_spot_instrument,
    parse_spot_ticker,
)


def test_public_instrument_response_parsing():
    instrument = parse_spot_instrument(
        {
            "list": [
                {
                    "symbol": "BTCUSDT",
                    "baseCoin": "BTC",
                    "quoteCoin": "USDT",
                    "priceFilter": {"tickSize": "0.01"},
                    "lotSizeFilter": {
                        "basePrecision": "0.000001",
                        "minOrderQty": "0.00001",
                        "minOrderAmt": "5",
                    },
                }
            ]
        }
    )

    assert instrument.symbol == "BTCUSDT"
    assert instrument.price_tick == Decimal("0.01")
    assert instrument.quantity_step == Decimal("0.000001")


def test_public_ticker_response_parsing():
    ticker = parse_spot_ticker(
        {
            "list": [
                {
                    "symbol": "BTCUSDT",
                    "lastPrice": "70000.12",
                    "bid1Price": "70000.11",
                    "ask1Price": "70000.13",
                }
            ]
        }
    )

    assert ticker.last_price == Decimal("70000.12")
    assert ticker.bid_price == Decimal("70000.11")
    assert ticker.ask_price == Decimal("70000.13")


def test_public_candle_response_parsing():
    candles = parse_spot_candles(
        {
            "list": [
                ["1710000000000", "1", "2", "0.5", "1.5", "10", "15"],
                ["1710000060000", "1.5", "3", "1", "2", "20", "40"],
            ]
        }
    )

    assert len(candles) == 2
    assert candles[0].start_time_ms == 1710000000000
    assert candles[1].close == Decimal("2")
