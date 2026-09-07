"""SQLite cache for normalized futures instrument catalog metadata."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import sqlite3

from triggertrade.instruments import FuturesInstrument, InstrumentCatalogRefreshResult, InstrumentExclusionReason


class InstrumentCatalogStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def replace_catalog(
        self,
        instruments: tuple[FuturesInstrument, ...],
        *,
        result: InstrumentCatalogRefreshResult,
    ) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM futures_instrument_catalog")
            for instrument in sorted(instruments, key=lambda item: item.symbol):
                conn.execute(
                    f"INSERT INTO futures_instrument_catalog ({', '.join(_INSTRUMENT_COLUMNS)}) VALUES ({', '.join('?' for _ in _INSTRUMENT_COLUMNS)})",
                    _instrument_values(instrument),
                )
            self._insert_refresh(conn, result)

    def record_failed_refresh(self, result: InstrumentCatalogRefreshResult) -> None:
        with self._connect() as conn:
            self._insert_refresh(conn, result)

    def get_instrument(self, symbol: str) -> FuturesInstrument | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM futures_instrument_catalog WHERE symbol = ?", (symbol.strip().upper(),)).fetchone()
        return None if row is None else _row_to_instrument(row)

    def list_instruments(self, *, tradeable_only: bool = False, search: str | None = None) -> tuple[FuturesInstrument, ...]:
        clauses: list[str] = []
        params: list[str | int] = []
        if tradeable_only:
            clauses.append("is_tradeable = 1")
        if search:
            term = f"%{search.strip().upper()}%"
            clauses.append("(symbol LIKE ? OR base_coin LIKE ?)")
            params.extend([term, term])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM futures_instrument_catalog{where} ORDER BY symbol", params).fetchall()
        return tuple(_row_to_instrument(row) for row in rows)

    def latest_refresh(self) -> InstrumentCatalogRefreshResult | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM futures_instrument_catalog_refreshes ORDER BY updated_at DESC, refresh_id DESC LIMIT 1").fetchone()
        if row is None:
            return None
        warnings = tuple(item for item in (row["warnings"] or "").split("\n") if item)
        return InstrumentCatalogRefreshResult(
            fetched_count=row["fetched_count"],
            tradeable_count=row["tradeable_count"],
            excluded_count=row["excluded_count"],
            updated_at=row["updated_at"],
            catalog_hash=row["catalog_hash"],
            status=row["status"],
            error=row["error"],
            warnings=warnings,
        )

    def _insert_refresh(self, conn: sqlite3.Connection, result: InstrumentCatalogRefreshResult) -> None:
        conn.execute(
            """
            INSERT INTO futures_instrument_catalog_refreshes(
                source, fetched_count, tradeable_count, excluded_count, updated_at, catalog_hash, status, error, warnings
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "bybit_public_v5_instruments_info_linear",
                result.fetched_count,
                result.tradeable_count,
                result.excluded_count,
                result.updated_at,
                result.catalog_hash,
                result.status,
                result.error,
                "\n".join(result.warnings),
            ),
        )

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_instrument_catalog (
                    symbol TEXT PRIMARY KEY,
                    base_coin TEXT NOT NULL,
                    quote_coin TEXT NOT NULL,
                    settle_coin TEXT NOT NULL,
                    contract_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tick_size TEXT NOT NULL,
                    price_scale INTEGER,
                    min_order_qty TEXT NOT NULL,
                    max_order_qty TEXT NOT NULL,
                    qty_step TEXT NOT NULL,
                    min_notional_value TEXT,
                    max_market_order_qty TEXT,
                    min_leverage TEXT,
                    max_leverage TEXT NOT NULL,
                    leverage_step TEXT,
                    launch_time TEXT,
                    delivery_time TEXT,
                    is_tradeable INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    exclusion_reason TEXT,
                    catalog_hash TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_futures_instrument_tradeable ON futures_instrument_catalog(is_tradeable, symbol)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_instrument_catalog_refreshes (
                    refresh_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    fetched_count INTEGER NOT NULL,
                    tradeable_count INTEGER NOT NULL,
                    excluded_count INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    catalog_hash TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    warnings TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


_INSTRUMENT_COLUMNS = tuple(field.name for field in fields(FuturesInstrument))


def _instrument_values(instrument: FuturesInstrument) -> tuple[str | int | None, ...]:
    values = []
    for key in _INSTRUMENT_COLUMNS:
        value = getattr(instrument, key)
        if key == "is_tradeable":
            values.append(1 if value else 0)
        elif key == "price_scale":
            values.append(value)
        elif isinstance(value, InstrumentExclusionReason):
            values.append(value.value)
        elif value is None:
            values.append(None)
        else:
            values.append(str(value))
    return tuple(values)


def _row_to_instrument(row: sqlite3.Row) -> FuturesInstrument:
    from decimal import Decimal

    reason = row["exclusion_reason"]
    return FuturesInstrument(
        symbol=row["symbol"],
        base_coin=row["base_coin"],
        quote_coin=row["quote_coin"],
        settle_coin=row["settle_coin"],
        contract_type=row["contract_type"],
        status=row["status"],
        tick_size=Decimal(row["tick_size"]),
        price_scale=row["price_scale"],
        min_order_qty=Decimal(row["min_order_qty"]),
        max_order_qty=Decimal(row["max_order_qty"]),
        qty_step=Decimal(row["qty_step"]),
        min_notional_value=None if row["min_notional_value"] is None else Decimal(row["min_notional_value"]),
        max_market_order_qty=None if row["max_market_order_qty"] is None else Decimal(row["max_market_order_qty"]),
        min_leverage=None if row["min_leverage"] is None else Decimal(row["min_leverage"]),
        max_leverage=Decimal(row["max_leverage"]),
        leverage_step=None if row["leverage_step"] is None else Decimal(row["leverage_step"]),
        launch_time=row["launch_time"],
        delivery_time=row["delivery_time"],
        is_tradeable=bool(row["is_tradeable"]),
        updated_at=row["updated_at"],
        source=row["source"],
        exclusion_reason=None if reason is None else InstrumentExclusionReason(reason),
        catalog_hash=row["catalog_hash"],
    )
