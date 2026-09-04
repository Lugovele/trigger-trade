from decimal import Decimal

from triggertrade.exchanges import parse_wallet_balance


def test_account_balance_response_parsing():
    balances = parse_wallet_balance(
        {
            "list": [
                {
                    "accountType": "UNIFIED",
                    "coin": [
                        {"coin": "BTC", "walletBalance": "0.01"},
                        {"coin": "USDT", "walletBalance": "100"},
                    ],
                }
            ]
        }
    )

    assert balances["BTC"] == Decimal("0.01")
    assert balances["USDT"] == Decimal("100")
