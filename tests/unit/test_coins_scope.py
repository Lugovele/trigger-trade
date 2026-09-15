from __future__ import annotations

import pytest

from triggertrade.coins_scope import (
    CoinScopeDelta,
    CoinsAction,
    CoinsScopeError,
    SetScopeState,
    apply_set_scope_delta,
    build_coins_contract,
)
from triggertrade.contracts import parse_contract


NOW = "2026-09-15T00:00:00Z"


def test_build_coins_contract_validates_v2_shape_and_normalizes_symbols():
    parsed = build_coins_contract(
        event_id="coins-1",
        occurred_at=NOW,
        symbols=(
            CoinScopeDelta(symbol="btcusdt", scope_revision=1, action=CoinsAction.OPEN),
            CoinScopeDelta(symbol="ETHUSDT", scope_revision=3, action=CoinsAction.CLOSE),
        ),
    )

    payload = parsed.to_payload()

    assert payload["coins"]["contract_version"] == 2
    assert payload["coins"]["symbols"] == [
        {"symbol": "BTCUSDT", "scope_revision": 1, "action": "OPEN"},
        {"symbol": "ETHUSDT", "scope_revision": 3, "action": "CLOSE"},
    ]
    assert parse_contract("COINS", payload).to_payload() == payload


def test_coins_scope_rejects_invalid_revision_and_repeated_symbol_revision():
    with pytest.raises(CoinsScopeError, match="scope_revision"):
        CoinScopeDelta(symbol="BTCUSDT", scope_revision=1.5, action=CoinsAction.OPEN)
    with pytest.raises(CoinsScopeError, match="scope_revision"):
        CoinScopeDelta.from_payload({"symbol": "BTCUSDT", "scope_revision": 1.5, "action": "OPEN"})
    with pytest.raises(CoinsScopeError, match="symbol"):
        CoinScopeDelta.from_payload({"symbol": 123, "scope_revision": 1, "action": "OPEN"})
    with pytest.raises(CoinsScopeError, match="repeat a symbol revision"):
        build_coins_contract(
            event_id="coins-1",
            occurred_at=NOW,
            symbols=(
                CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),
                CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.CLOSE),
            ),
        )


def test_set_scope_delta_applies_only_newer_revisions():
    current = SetScopeState(
        symbol="BTCUSDT",
        scope_revision=4,
        action=CoinsAction.CLOSE,
        event_id="coins-4",
        occurred_at=NOW,
        payload_digest="digest-4",
    )

    assert (
        apply_set_scope_delta(
            current,
            CoinScopeDelta(symbol="BTCUSDT", scope_revision=3, action=CoinsAction.OPEN),
            event_id="coins-3",
            occurred_at=NOW,
            payload_digest="digest-3",
        )
        is None
    )
    newer = apply_set_scope_delta(
        current,
        CoinScopeDelta(symbol="BTCUSDT", scope_revision=5, action=CoinsAction.OPEN),
        event_id="coins-5",
        occurred_at=NOW,
        payload_digest="digest-5",
    )

    assert newer is not None
    assert newer.action is CoinsAction.OPEN
    assert newer.is_open is True
