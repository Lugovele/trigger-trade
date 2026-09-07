"""Service boundary for Bybit USDT linear perpetual instrument metadata."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from triggertrade.exchanges import BybitApiError, BybitDemoClient
from triggertrade.execution.futures import PositionAction
from triggertrade.instruments import (
    CATALOG_SOURCE,
    CatalogError,
    FuturesInstrument,
    InstrumentCatalogRefreshResult,
    PriceNormalizationPurpose,
    catalog_hash,
    instrument_from_bybit,
    instrument_to_metadata,
    normalize_price_for_instrument,
    normalize_qty_for_instrument,
)
from triggertrade.persistence.instrument_catalog_store import InstrumentCatalogStore


class InstrumentCatalogService:
    """Read/refresh facade for locally cached futures instruments."""

    def __init__(
        self,
        *,
        store: InstrumentCatalogStore,
        client: BybitDemoClient | None = None,
        clock=None,
        stale_after: timedelta = timedelta(hours=24),
    ) -> None:
        self._store = store
        self._client = client
        self._clock = clock or (lambda: datetime.now(UTC))
        self._stale_after = stale_after

    def refresh_instrument_catalog(self) -> InstrumentCatalogRefreshResult:
        if self._client is None:
            result = InstrumentCatalogRefreshResult(0, 0, 0, self._clock().isoformat(), None, "FAILED", "catalog refresh requires Bybit public client")
            self._store.record_failed_refresh(result)
            return result
        updated_at = self._clock().isoformat()
        try:
            raw_items = self._fetch_all_pages()
            if not raw_items:
                raise CatalogError("Bybit instrument catalog returned no rows")
            instruments = tuple(_normalize_items(raw_items, updated_at=updated_at))
            digest = catalog_hash(instruments)
            instruments = tuple(replace(instrument, catalog_hash=digest) for instrument in instruments)
            result = InstrumentCatalogRefreshResult(
                fetched_count=len(raw_items),
                tradeable_count=sum(1 for item in instruments if item.is_tradeable),
                excluded_count=sum(1 for item in instruments if not item.is_tradeable),
                updated_at=updated_at,
                catalog_hash=digest,
                status="OK",
            )
            self._store.replace_catalog(instruments, result=result)
            return result
        except Exception as exc:
            result = InstrumentCatalogRefreshResult(0, 0, 0, updated_at, None, "FAILED", _safe_error(exc))
            self._store.record_failed_refresh(result)
            return result

    def ensure_available(self) -> InstrumentCatalogRefreshResult | None:
        latest = self._store.latest_refresh()
        if latest is None or self.catalog_is_stale():
            result = self.refresh_instrument_catalog()
            if result.status != "OK":
                raise CatalogError("instrument catalog refresh failed; new entries fail closed")
            return result
        return latest

    def catalog_is_stale(self) -> bool:
        latest = self._store.latest_refresh()
        if latest is None or latest.status != "OK":
            return True
        try:
            updated = datetime.fromisoformat(latest.updated_at)
        except ValueError:
            return True
        return self._clock() - updated > self._stale_after

    def list_tradeable_instruments(self, *, search: str | None = None) -> tuple[FuturesInstrument, ...]:
        return self._store.list_instruments(tradeable_only=True, search=search)

    def list_tradeable_coins(self, *, search: str | None = None) -> tuple[dict[str, str | None], ...]:
        return tuple(
            {
                "symbol": item.symbol,
                "base_coin": item.base_coin,
                "quote_coin": item.quote_coin,
                "status": item.status,
                "max_leverage": str(item.max_leverage),
                "min_order_qty": str(item.min_order_qty),
                "qty_step": str(item.qty_step),
                "tick_size": str(item.tick_size),
                "launch_time": item.launch_time,
            }
            for item in self.list_tradeable_instruments(search=search)
        )

    def get_instrument(self, symbol: str) -> FuturesInstrument | None:
        return self._store.get_instrument(symbol)

    def validate_symbol(self, symbol: str) -> FuturesInstrument:
        normalized = symbol.strip().upper()
        instrument = self._store.get_instrument(normalized)
        if instrument is None:
            raise CatalogError("instrument is not present in the local catalog")
        if not instrument.is_tradeable:
            reason = "unknown" if instrument.exclusion_reason is None else instrument.exclusion_reason.value
            raise CatalogError(f"instrument is not tradeable: {reason}")
        return instrument

    def metadata_for_symbol(self, symbol: str):
        return instrument_to_metadata(self.validate_symbol(symbol))

    def normalize_qty(self, symbol: str, qty: Decimal, *, price: Decimal | None = None) -> Decimal:
        return normalize_qty_for_instrument(self.validate_symbol(symbol), qty, price=price)

    def normalize_price(self, symbol: str, price: Decimal, *, purpose: PriceNormalizationPurpose, action: PositionAction) -> Decimal:
        instrument = self._store.get_instrument(symbol.strip().upper())
        if instrument is None:
            raise CatalogError("instrument is not present in the local catalog")
        return normalize_price_for_instrument(instrument, price, purpose=purpose, action=action)

    def _fetch_all_pages(self) -> tuple[dict[str, Any], ...]:
        seen_cursors: set[str] = set()
        seen_symbols: set[str] = set()
        cursor: str | None = None
        items: list[dict[str, Any]] = []
        while True:
            response = self._client.linear_instruments_info(cursor=cursor)  # type: ignore[union-attr]
            page_items = response.result.get("list")
            if not isinstance(page_items, list) or not page_items:
                raise CatalogError("Bybit instrument catalog page was empty or malformed")
            for item in page_items:
                symbol = str(item.get("symbol") or "").upper()
                if symbol and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    items.append(item)
            next_cursor = str(response.result.get("nextPageCursor") or "").strip() or None
            if next_cursor is None:
                break
            if next_cursor in seen_cursors:
                raise CatalogError("Bybit instrument pagination cursor loop detected")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        return tuple(items)


def _normalize_items(raw_items: tuple[dict[str, Any], ...], *, updated_at: str) -> tuple[FuturesInstrument, ...]:
    instruments: list[FuturesInstrument] = []
    for item in raw_items:
        try:
            instruments.append(instrument_from_bybit(item, updated_at=updated_at, source=CATALOG_SOURCE))
        except CatalogError:
            symbol = str(item.get("symbol") or "UNKNOWN").upper()
            instruments.append(_excluded_incomplete(symbol=symbol, updated_at=updated_at))
    return tuple(sorted(instruments, key=lambda item: item.symbol))


def _excluded_incomplete(*, symbol: str, updated_at: str) -> FuturesInstrument:
    from triggertrade.instruments import InstrumentExclusionReason

    return FuturesInstrument(
        symbol=symbol,
        base_coin=symbol.removesuffix("USDT"),
        quote_coin="",
        settle_coin="",
        contract_type="",
        status="",
        tick_size=Decimal("0"),
        price_scale=None,
        min_order_qty=Decimal("0"),
        max_order_qty=Decimal("0"),
        qty_step=Decimal("0"),
        min_notional_value=None,
        max_market_order_qty=None,
        min_leverage=None,
        max_leverage=Decimal("0"),
        leverage_step=None,
        launch_time=None,
        delivery_time=None,
        is_tradeable=False,
        updated_at=updated_at,
        source=CATALOG_SOURCE,
        exclusion_reason=InstrumentExclusionReason.INCOMPLETE_METADATA,
    )


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, (BybitApiError, CatalogError)):
        return str(exc)
    return exc.__class__.__name__
