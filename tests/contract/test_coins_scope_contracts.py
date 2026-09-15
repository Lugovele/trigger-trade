from __future__ import annotations

from triggertrade.coins_scope import CoinScopeDelta, CoinsAction, build_coins_contract
from triggertrade.contracts import contract_digest, implemented_contract_registry


def test_coins_scope_uses_approved_current_coins_v2_contract():
    registry = implemented_contract_registry()
    assert registry["COINS"] == {"version": 2, "definitions": ("COINS",)}

    payload = build_coins_contract(
        event_id="coins-contract-1",
        occurred_at="2026-09-15T00:00:00Z",
        symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
    ).to_payload()

    assert payload == {
        "coins": {
            "contract_version": 2,
            "event_id": "coins-contract-1",
            "occurred_at": "2026-09-15T00:00:00Z",
            "symbols": [{"symbol": "BTCUSDT", "scope_revision": 1, "action": "OPEN"}],
        }
    }
    assert contract_digest(payload) == contract_digest(build_coins_contract(
        event_id="coins-contract-1",
        occurred_at="2026-09-15T00:00:00Z",
        symbols=(CoinScopeDelta(symbol="btcusdt", scope_revision=1, action="OPEN"),),
    ))
