"""Historical public linear kline data source, validation, and cache."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from time import sleep

from triggertrade.exchanges import BybitDemoClient
from triggertrade.market_data import BybitCandle, parse_spot_candles
from triggertrade.services.runtime import interval_delta

from .models import BACKTEST_DATA_SOURCE_VERSION, HistoricalCandle


class HistoricalDataError(ValueError):
    pass


@dataclass(frozen=True)
class HistoricalCacheRecord:
    path: Path
    metadata_path: Path
    content_hash: str
    candles: tuple[HistoricalCandle, ...]


def validate_historical_candles(
    candles: tuple[HistoricalCandle, ...],
    *,
    symbol: str = "BTCUSDT",
    category: str = "linear",
    timeframe: str = "1m",
    require_contiguous: bool = True,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[HistoricalCandle, ...]:
    if not candles:
        raise HistoricalDataError("historical data is empty")
    expected_symbol = symbol.upper()
    expected_category = category.lower()
    expected_timeframe = _timeframe(timeframe)
    interval = interval_delta(expected_timeframe)
    ordered = tuple(sorted(candles, key=lambda item: item.open_time))
    if ordered != candles:
        raise HistoricalDataError("historical candles must be ordered ascending")
    seen: set[datetime] = set()
    previous = None
    for candle in ordered:
        if candle.symbol.upper() != expected_symbol:
            raise HistoricalDataError("wrong historical candle symbol")
        if candle.category.lower() != expected_category:
            raise HistoricalDataError("wrong historical candle category")
        if _timeframe(candle.timeframe) != expected_timeframe:
            raise HistoricalDataError("wrong historical candle timeframe")
        if not candle.completed:
            raise HistoricalDataError("historical replay accepts completed candles only")
        if candle.open_time.tzinfo is None or candle.close_time.tzinfo is None:
            raise HistoricalDataError("historical candle timestamps must be timezone-aware")
        if candle.open_time in seen:
            raise HistoricalDataError("duplicate historical candle")
        seen.add(candle.open_time)
        if candle.close_time != candle.open_time + interval:
            raise HistoricalDataError("malformed historical candle close time")
        if any(value <= 0 for value in (candle.open, candle.high, candle.low, candle.close)):
            raise HistoricalDataError("malformed historical candle price")
        if candle.volume < 0 or candle.turnover < 0:
            raise HistoricalDataError("malformed historical candle volume")
        if previous is not None and require_contiguous and candle.open_time != previous.close_time:
            raise HistoricalDataError("historical candle gap")
        previous = candle
    if start is not None and ordered[0].open_time != _utc(start):
        raise HistoricalDataError("historical data does not start at requested boundary")
    if end is not None and ordered[-1].close_time != _utc(end):
        raise HistoricalDataError("historical data does not end at requested boundary")
    return ordered


class HistoricalKlineCache:
    def __init__(self, root: str | Path = "runtime/history") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime) -> HistoricalCacheRecord | None:
        path = self._path(symbol=symbol, category=category, timeframe=timeframe, start=start, end=end)
        meta = path.with_suffix(".metadata.json")
        if not path.exists() or not meta.exists():
            return None
        rows = json.loads(path.read_text(encoding="utf-8"))
        candles = tuple(_dict_to_candle(row) for row in rows)
        content_hash = _hash_rows(rows)
        metadata = json.loads(meta.read_text(encoding="utf-8"))
        expected = {
            "symbol": symbol.upper(),
            "category": category.lower(),
            "timeframe": _timeframe(timeframe),
            "start": _utc(start).isoformat(),
            "end": _utc(end).isoformat(),
            "data_source_version": BACKTEST_DATA_SOURCE_VERSION,
            "content_hash": content_hash,
        }
        for key, value in expected.items():
            if metadata.get(key) != value:
                raise HistoricalDataError("historical cache metadata mismatch")
        return HistoricalCacheRecord(path, meta, content_hash, validate_historical_candles(candles, symbol=symbol, category=category, timeframe=timeframe, start=start, end=end))

    def save(self, candles: tuple[HistoricalCandle, ...], *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime) -> HistoricalCacheRecord:
        validated = validate_historical_candles(candles, symbol=symbol, category=category, timeframe=timeframe, start=start, end=end)
        rows = [_candle_to_dict(candle) for candle in validated]
        content_hash = _hash_rows(rows)
        path = self._path(symbol=symbol, category=category, timeframe=timeframe, start=start, end=end)
        meta = path.with_suffix(".metadata.json")
        path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
        meta.write_text(
            json.dumps(
                {
                    "symbol": symbol.upper(),
                    "category": category.lower(),
                    "timeframe": _timeframe(timeframe),
                    "start": _utc(start).isoformat(),
                    "end": _utc(end).isoformat(),
                    "data_source_version": BACKTEST_DATA_SOURCE_VERSION,
                    "content_hash": content_hash,
                    "candles": len(validated),
                    "validated": True,
                    "fetched_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return HistoricalCacheRecord(path, meta, content_hash, validated)

    def _path(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime) -> Path:
        name = "__".join([symbol.upper(), category.lower(), _timeframe(timeframe), _stamp(start), _stamp(end), BACKTEST_DATA_SOURCE_VERSION])
        return self.root / f"{name}.json"


class BybitHistoricalDataSource:
    """Public-only Bybit Demo linear kline source with deterministic pagination."""

    def __init__(self, client: BybitDemoClient, *, cache: HistoricalKlineCache | None = None, retry_sleep_seconds: float = 0.2) -> None:
        self._client = client
        self._cache = cache or HistoricalKlineCache()
        self._retry_sleep_seconds = retry_sleep_seconds

    def load(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime, use_cache: bool = True) -> HistoricalCacheRecord:
        if category.lower() != "linear":
            raise HistoricalDataError("historical replay supports Bybit linear perpetual only")
        if symbol.upper() != "BTCUSDT":
            raise HistoricalDataError("historical replay supports BTCUSDT only")
        if _timeframe(timeframe) != "1m":
            raise HistoricalDataError("historical replay supports 1m candles only")
        if _utc(start) >= _utc(end):
            raise HistoricalDataError("historical range start must be before end")
        cached = self._cache.load(symbol=symbol, category=category, timeframe=timeframe, start=start, end=end) if use_cache else None
        if cached is not None:
            return cached
        candles = self._fetch(symbol=symbol, timeframe=timeframe, start=start, end=end)
        return self._cache.save(candles, symbol=symbol, category=category, timeframe=timeframe, start=start, end=end)

    def _fetch(self, *, symbol: str, timeframe: str, start: datetime, end: datetime) -> tuple[HistoricalCandle, ...]:
        interval = interval_delta(timeframe)
        cursor = _utc(start)
        result: list[HistoricalCandle] = []
        while cursor < _utc(end):
            batch_end = min(cursor + interval * 200, _utc(end))
            response = _retry(
                lambda: self._client.linear_historical_candles(
                    symbol=symbol,
                    interval="1",
                    start_ms=int(cursor.timestamp() * 1000),
                    end_ms=int(batch_end.timestamp() * 1000) - 1,
                    limit=200,
                ),
                sleep_seconds=self._retry_sleep_seconds,
            )
            batch = tuple(
                _from_bybit_candle(item, symbol=symbol, category="linear", timeframe=_timeframe(timeframe))
                for item in parse_spot_candles(response.result)
                if _utc(start) <= _dt(item) < _utc(end)
            )
            result.extend(batch)
            cursor = batch_end
        return validate_historical_candles(tuple(sorted(result, key=lambda item: item.open_time)), symbol=symbol, category="linear", timeframe=timeframe, start=start, end=end)


def historical_to_bybit(candle: HistoricalCandle) -> BybitCandle:
    return BybitCandle(
        start_time_ms=int(candle.open_time.timestamp() * 1000),
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
        turnover=candle.turnover,
    )


def cache_hash(candles: tuple[HistoricalCandle, ...]) -> str:
    return _hash_rows([_candle_to_dict(candle) for candle in candles])


def _retry(call, *, sleep_seconds: float):
    last_exc = None
    for attempt in range(3):
        try:
            return call()
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                sleep(sleep_seconds * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def _from_bybit_candle(candle: BybitCandle, *, symbol: str, category: str, timeframe: str) -> HistoricalCandle:
    open_time = _dt(candle)
    return HistoricalCandle(symbol.upper(), category.lower(), _timeframe(timeframe), open_time, open_time + interval_delta(timeframe), candle.open, candle.high, candle.low, candle.close, candle.volume, candle.turnover, True)


def _candle_to_dict(candle: HistoricalCandle) -> dict[str, str | bool]:
    data = asdict(candle)
    data["open_time"] = candle.open_time.astimezone(UTC).isoformat()
    data["close_time"] = candle.close_time.astimezone(UTC).isoformat()
    for key in ("open", "high", "low", "close", "volume", "turnover"):
        data[key] = str(data[key])
    return data


def _dict_to_candle(row: dict[str, str]) -> HistoricalCandle:
    return HistoricalCandle(
        symbol=row["symbol"],
        category=row["category"],
        timeframe=row["timeframe"],
        open_time=datetime.fromisoformat(row["open_time"]).astimezone(UTC),
        close_time=datetime.fromisoformat(row["close_time"]).astimezone(UTC),
        open=Decimal(row["open"]),
        high=Decimal(row["high"]),
        low=Decimal(row["low"]),
        close=Decimal(row["close"]),
        volume=Decimal(row["volume"]),
        turnover=Decimal(row["turnover"]),
        completed=bool(row["completed"]),
    )


def _hash_rows(rows: list[dict[str, object]]) -> str:
    return sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _dt(candle: BybitCandle) -> datetime:
    return datetime.fromtimestamp(candle.start_time_ms / 1000, UTC)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _stamp(value: datetime) -> str:
    return _utc(value).strftime("%Y%m%dT%H%M%SZ")


def _timeframe(value: str) -> str:
    if value.strip().lower() in {"1", "1m"}:
        return "1m"
    raise HistoricalDataError("only 1m historical timeframe is supported")
