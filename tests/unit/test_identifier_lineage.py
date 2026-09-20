import pytest

from triggertrade.identifier_lineage import (
    ImmutableBinding,
    IdentifierBindingError,
    bind_immutable_content,
    bindings_conflict,
    ensure_same_binding,
)


def test_same_identity_and_same_content_replays_without_conflict():
    first = bind_immutable_content("opaque-id-1", {"symbol": "BTCUSDT", "at": "2026-09-20T00:00:00Z"})
    replay = bind_immutable_content("opaque-id-1", {"at": "2026-09-20T00:00:00Z", "symbol": "BTCUSDT"})

    ensure_same_binding(first, replay)
    assert first == replay
    assert bindings_conflict(first, replay) is False


def test_same_identity_with_different_content_is_conflict():
    first = bind_immutable_content("opaque-id-1", {"symbol": "BTCUSDT", "revision": 1})
    changed = bind_immutable_content("opaque-id-1", {"symbol": "BTCUSDT", "revision": 2})

    assert bindings_conflict(first, changed) is True
    with pytest.raises(IdentifierBindingError, match="conflicting immutable binding"):
        ensure_same_binding(first, changed)


def test_similar_factual_coordinates_with_different_identities_remain_distinct():
    first = bind_immutable_content("opaque-id-1", {"symbol": "BTCUSDT", "at": "2026-09-20T00:00:00Z"})
    second = bind_immutable_content("opaque-id-2", {"symbol": "BTCUSDT", "at": "2026-09-20T00:00:00Z"})

    ensure_same_binding(first, second)
    assert first.identity != second.identity
    assert first.content_digest == second.content_digest
    assert bindings_conflict(first, second) is False


def test_binding_does_not_guess_nearest_or_latest_identity():
    older = bind_immutable_content("opaque-id-older", {"symbol": "BTCUSDT", "at": "2026-09-20T00:00:00Z"})
    newer = bind_immutable_content("opaque-id-newer", {"symbol": "BTCUSDT", "at": "2026-09-20T00:00:01Z"})

    ensure_same_binding(older, newer)
    assert bindings_conflict(older, newer) is False


def test_binding_rejects_float_content_and_malformed_digest():
    with pytest.raises(IdentifierBindingError, match="binary floats"):
        bind_immutable_content("opaque-id-1", {"value": 1.0})
    with pytest.raises(IdentifierBindingError, match="sha256 hex digest"):
        ImmutableBinding("opaque-id-1", "not-a-digest")
