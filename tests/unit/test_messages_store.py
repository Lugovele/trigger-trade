import pytest

from triggertrade.persistence.message_store import MessageSeverity, MessageStore, MessageStoreError


def test_messages_persist_order_unread_and_mark_read_across_restart(tmp_path):
    db = tmp_path / "messages.sqlite3"
    store = MessageStore(db)
    older = store.create_message(
        created_at="2026-09-08T10:00:00+00:00",
        severity=MessageSeverity.INFO,
        body="Operator resumed entries.",
        source="unit",
    )
    newer = store.create_message(
        created_at="2026-09-08T10:05:00+00:00",
        severity=MessageSeverity.ATTENTION,
        body="Operator paused entries.",
        source="unit",
    )

    restarted = MessageStore(db)
    rows = restarted.list_messages()

    assert [row.message_id for row in rows] == [newer.message_id, older.message_id]
    assert restarted.get_unread_message_count() == 2
    assert restarted.mark_read([newer.message_id]) == 1
    assert MessageStore(db).get_unread_message_count() == 1


def test_message_type_vocabulary_and_empty_list(tmp_path):
    store = MessageStore(tmp_path / "messages.sqlite3")

    assert store.list_messages() == ()
    assert store.get_unread_message_count() == 0
    for severity in ("INFO", "ATTENTION", "WARNING", "ERROR"):
        row = store.create_message(severity=severity, type=severity, body=f"{severity} body", source="unit")
        assert row.severity.value == severity

    with pytest.raises(MessageStoreError):
        store.create_message(severity="DEBUG", body="debug", source="unit")


def test_dedupe_prevents_repeated_unread_message_flood_but_allows_distinct_events(tmp_path):
    store = MessageStore(tmp_path / "messages.sqlite3")

    first = store.create_message(body="Catalog unavailable.", severity="WARNING", source="unit", dedupe_key="catalog:warning")
    second = store.create_message(body="Catalog unavailable again.", severity="WARNING", source="unit", dedupe_key="catalog:warning")
    distinct = store.create_message(body="Close One failed.", severity="ERROR", source="unit", dedupe_key="close-one:pos-1")

    assert second.message_id == first.message_id
    assert [row.message_id for row in store.list_messages()] == [distinct.message_id, first.message_id]


def test_mark_read_rejects_malformed_and_unknown_ids(tmp_path):
    store = MessageStore(tmp_path / "messages.sqlite3")
    row = store.create_message(body="Message", severity="INFO", source="unit")

    with pytest.raises(MessageStoreError):
        store.mark_read(["../secret"])
    with pytest.raises(MessageStoreError):
        store.mark_read(["msg_missing"])

    assert store.mark_read([row.message_id]) == 1


def test_secret_like_metadata_and_body_are_redacted(tmp_path):
    store = MessageStore(tmp_path / "messages.sqlite3")

    row = store.create_message(
        body="Authorization: Bearer secret-token",
        severity="ERROR",
        source="unit",
        metadata={"api_secret": "unit-secret", "symbol": "BTCUSDT"},
    )

    assert row.body == "[redacted]"
    assert row.metadata["api_secret"] == "[redacted]"
    assert row.metadata["symbol"] == "BTCUSDT"
