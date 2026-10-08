"""Prepare the frozen Research V2 J0-J7 7D market-data package.

The command downloads and validates public historical facts only. It never
executes Research jobs or simulates positions.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import sleep
from typing import Any, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.backtest.data import validate_historical_candles  # noqa: E402
from triggertrade.backtest.models import BACKTEST_DATA_SOURCE_VERSION, HistoricalCandle  # noqa: E402
from triggertrade.market_data.raw_trades import (  # noqa: E402
    BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
    bybit_public_trade_archive_url,
    bybit_raw_trade_archive_manifest,
    instrument_symbol_for_logical_symbol,
)
from triggertrade.research_v2 import (  # noqa: E402
    atr15,
    confirmed_swing5_references,
    ema15,
    load_research_v2_jobs,
    return_pct_points,
    rvol5,
    turnover_acceleration,
    wilder_atr_series,
    aggregate_completed_bars,
)


DATASET_ID = "research-v2-7d-20260819-20260826-v1"
SCREEN_START = datetime(2026, 8, 19, tzinfo=UTC)
SCREEN_END = datetime(2026, 8, 26, tzinfo=UTC)
WARMUP_START = datetime(2026, 8, 4, tzinfo=UTC)
DATASET_ROOT = ROOT / "runtime" / "data" / "research-v2" / "7d_20260819_20260826"
TRADING_LOGICAL = ("AVAXUSDT", "SUIUSDT", "PEPEUSDT")
CONTEXT = ("BTCUSDT",)
BYBIT_API_BASE = "https://api.bybit.com"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", help="Trading window start, UTC ISO timestamp. Default is the certified August start.")
    parser.add_argument("--end", help="Trading window end, UTC ISO timestamp. Default is the certified August end.")
    parser.add_argument("--output-root", type=Path, help="Dataset root. Defaults to runtime/data/research-v2/7d_YYYYMMDD_YYYYMMDD.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_dataset_window(start=args.start, end=args.end, output_root=args.output_root)
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    for child in ("candles", "raw_trades", "funding", "mark_price", "instruments"):
        (DATASET_ROOT / child).mkdir(parents=True, exist_ok=True)

    files: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    candle_summary: dict[str, Any] = {}
    raw_summary: dict[str, Any] = {}
    funding_summary: dict[str, Any] = {}
    mark_summary: dict[str, Any] = {}
    instrument_summary: dict[str, Any] = {}
    feature_summary: dict[str, Any] = {}

    physical_by_logical = {symbol: instrument_symbol_for_logical_symbol(symbol) for symbol in TRADING_LOGICAL}
    candle_symbols = tuple(physical_by_logical.values()) + CONTEXT

    for symbol in candle_symbols:
        try:
            record = prepare_candles(symbol)
            files.extend(record["files"])
            candle_summary[symbol] = record["summary"]
        except Exception as exc:  # noqa: BLE001 - data prep must report all source failures.
            errors.append(_error("candles", symbol, str(exc)))

    for logical, physical in physical_by_logical.items():
        try:
            record = prepare_raw_trades(logical, physical)
            files.extend(record["files"])
            raw_summary[logical] = record["summary"]
        except Exception as exc:  # noqa: BLE001
            errors.append(_error("raw_trades", logical, str(exc), physical_symbol=physical))

    for logical, physical in physical_by_logical.items():
        try:
            record = prepare_funding(logical, physical)
            files.extend(record["files"])
            funding_summary[logical] = record["summary"]
        except Exception as exc:  # noqa: BLE001
            errors.append(_error("funding", logical, str(exc), physical_symbol=physical))

    for logical, physical in physical_by_logical.items():
        try:
            record = prepare_mark_price(logical, physical)
            files.extend(record["files"])
            mark_summary[logical] = record["summary"]
        except Exception as exc:  # noqa: BLE001
            errors.append(_error("mark_price", logical, str(exc), physical_symbol=physical))

    for symbol in tuple(physical_by_logical.values()) + CONTEXT:
        try:
            record = prepare_instrument(symbol)
            files.extend(record["files"])
            instrument_summary[symbol] = record["summary"]
        except Exception as exc:  # noqa: BLE001
            errors.append(_error("instrument_metadata", symbol, str(exc)))

    for logical, physical in physical_by_logical.items():
        try:
            feature_summary[logical] = feature_readiness(physical)
        except Exception as exc:  # noqa: BLE001
            feature_summary[logical] = {"status": "NOT_READY", "reason": str(exc)}
            errors.append(_error("feature_readiness", logical, str(exc), physical_symbol=physical))

    job_readiness = build_job_readiness(
        candle_summary=candle_summary,
        raw_summary=raw_summary,
        funding_summary=funding_summary,
        mark_summary=mark_summary,
        instrument_summary=instrument_summary,
        feature_summary=feature_summary,
    )
    dataset_status = "DATA_READY" if not errors and all(row["overall_status"] == "READY" for row in job_readiness) else "BLOCKED_DATA_INCOMPLETE"

    inventory_path = DATASET_ROOT / "data_inventory.csv"
    write_inventory(inventory_path, files)
    files.append(file_record(inventory_path, data_type="inventory", symbol=None, source="local_generated"))

    validation = {
        "status": "PASS" if dataset_status == "DATA_READY" else "FAIL",
        "errors": errors,
        "candle_coverage": candle_summary,
        "raw_trades_coverage": raw_summary,
        "funding_coverage": funding_summary,
        "mark_price_coverage": mark_summary,
        "instrument_metadata": instrument_summary,
        "feature_readiness": feature_summary,
        "job_readiness": job_readiness,
    }
    validation_path = DATASET_ROOT / "validation_summary.json"
    write_json(validation_path, validation)
    files.append(file_record(validation_path, data_type="validation", symbol=None, source="local_generated"))

    manifest = {
        "dataset_id": DATASET_ID,
        "status": dataset_status,
        "screen_start": iso(SCREEN_START),
        "screen_end": iso(SCREEN_END),
        "warmup_start": iso(WARMUP_START),
        "symbols": {
            "trading_logical": list(TRADING_LOGICAL),
            "trading_physical": sorted(set(physical_by_logical.values())),
            "context_only": list(CONTEXT),
        },
        "logical_physical_bindings": physical_by_logical,
        "data_families": {
            "candles": "1m Bybit linear kline, higher timeframes derived causally from 1m",
            "raw_trades": "official Bybit public daily trading archives",
            "funding": "Bybit linear funding history",
            "mark_price": "Bybit linear mark-price kline, 1m",
            "instrument_metadata": "Bybit linear instruments-info",
        },
        "files": sorted(files, key=lambda item: str(item["local_path"])),
        "coverage": validation,
        "hashes": {str(item["local_path"]): item["sha256"] for item in files},
        "provenance": {
            "api_base": BYBIT_API_BASE,
            "raw_archive_revision": BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
            "candle_source_version": BACKTEST_DATA_SOURCE_VERSION,
            "research_v2_specs": [
                "docs/research-v2/RESEARCH_V2_MANIFEST.json",
                "docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json",
                "docs/research-v2/jobs/INITIAL_7D_JOBS.json",
                "docs/research-v2/implementation/RESEARCH_V2_IMPLEMENTATION_MAP.json",
            ],
        },
        "created_at": iso(datetime.now(UTC)),
        "validation": {
            "status": validation["status"],
            "job_ready_count": sum(1 for row in job_readiness if row["overall_status"] == "READY"),
            "job_count": len(job_readiness),
            "error_count": len(errors),
        },
    }
    manifest_path = DATASET_ROOT / "dataset_manifest.json"
    write_json(manifest_path, manifest)

    print(json.dumps({
        "dataset_status": dataset_status,
        "dataset_manifest": str(manifest_path),
        "validation_summary": str(validation_path),
        "errors": errors,
    }, indent=2, sort_keys=True))
    return 0 if dataset_status == "DATA_READY" else 2


def configure_dataset_window(*, start: str | None = None, end: str | None = None, output_root: Path | None = None) -> None:
    global DATASET_ID, SCREEN_START, SCREEN_END, WARMUP_START, DATASET_ROOT

    if start is None and end is None and output_root is None:
        return
    if start is None or end is None:
        raise ValueError("--start and --end must be supplied together")
    screen_start = parse_time(start)
    screen_end = parse_time(end)
    if screen_end <= screen_start:
        raise ValueError("--end must be after --start")
    if screen_end - screen_start != timedelta(days=7):
        raise ValueError("Research V2 dataset windows must be exactly 7 days")
    warmup_start = screen_start - timedelta(days=15)
    suffix = f"7d_{screen_start:%Y%m%d}_{screen_end:%Y%m%d}"
    DATASET_ID = f"research-v2-7d-{screen_start:%Y%m%d}-{screen_end:%Y%m%d}-v1"
    SCREEN_START = screen_start
    SCREEN_END = screen_end
    WARMUP_START = warmup_start
    DATASET_ROOT = output_root if output_root is not None else ROOT / "runtime" / "data" / "research-v2" / suffix


def prepare_candles(symbol: str) -> dict[str, Any]:
    candles = fetch_kline(symbol=symbol, endpoint="/v5/market/kline", result_key="list", start=WARMUP_START, end=SCREEN_END)
    validated = validate_historical_candles(tuple(candles), symbol=symbol, category="linear", timeframe="1m", start=WARMUP_START, end=SCREEN_END)
    rows = [candle_to_dict(candle) for candle in validated]
    path = DATASET_ROOT / "candles" / f"{symbol}__linear__1m__{stamp(WARMUP_START)}__{stamp(SCREEN_END)}.json"
    write_json(path, rows)
    meta = {
        "symbol": symbol,
        "category": "linear",
        "timeframe": "1m",
        "start": iso(WARMUP_START),
        "end": iso(SCREEN_END),
        "rows": len(rows),
        "source": "bybit_public_v5_market_kline",
        "content_hash": sha256_json(rows),
        "validated": True,
    }
    meta_path = path.with_suffix(".metadata.json")
    write_json(meta_path, meta)
    return {
        "files": [
            file_record(path, data_type="candles_1m", symbol=symbol, physical_symbol=symbol, start=WARMUP_START, end=SCREEN_END, rows=len(rows), source=meta["source"]),
            file_record(meta_path, data_type="candles_metadata", symbol=symbol, physical_symbol=symbol, start=WARMUP_START, end=SCREEN_END, rows=1, source="local_generated"),
        ],
        "summary": {
            "status": "READY" if _candle_volume_turnover_ready(rows) else "DATA_INVALID",
            "rows": len(rows),
            "expected_rows": int((SCREEN_END - WARMUP_START).total_seconds() // 60),
            "start": rows[0]["open_time"],
            "end": rows[-1]["close_time"],
            "missing_intervals": [],
            "volume_zero_count": sum(1 for row in rows if Decimal(str(row["volume"])) == 0),
            "volume_positive_count": sum(1 for row in rows if Decimal(str(row["volume"])) > 0),
            "turnover_zero_count": sum(1 for row in rows if Decimal(str(row["turnover"])) == 0),
            "turnover_positive_count": sum(1 for row in rows if Decimal(str(row["turnover"])) > 0),
            "min_volume": str(min(Decimal(str(row["volume"])) for row in rows)),
            "max_volume": str(max(Decimal(str(row["volume"])) for row in rows)),
            "min_turnover": str(min(Decimal(str(row["turnover"])) for row in rows)),
            "max_turnover": str(max(Decimal(str(row["turnover"])) for row in rows)),
        },
    }


def _candle_volume_turnover_ready(rows: Sequence[Mapping[str, Any]]) -> bool:
    if not rows:
        return False
    return any(Decimal(str(row["volume"])) > 0 for row in rows) and any(Decimal(str(row["turnover"])) > 0 for row in rows)


def prepare_raw_trades(logical: str, physical: str) -> dict[str, Any]:
    files = []
    rows = []
    missing = []
    for day in days(SCREEN_START.date(), (SCREEN_END - timedelta(days=1)).date()):
        path = DATASET_ROOT / "raw_trades" / f"{physical}{day.isoformat()}.csv.gz"
        if not path.exists():
            download_file(bybit_public_trade_archive_url(physical, day), path)
        manifest = bybit_raw_trade_archive_manifest(
            path,
            logical_symbol=logical,
            archive_date=day,
            factual_validation_status="OBJECTIVE_REMOTE_METADATA_VERIFIED",
        )
        count = count_gzip_csv_rows(path)
        if count <= 0:
            missing.append(day.isoformat())
        rows.append({"date": day.isoformat(), "rows": count, "sha256": manifest.content_sha256, "path": str(path)})
        files.append(file_record(path, data_type="raw_trades_archive", symbol=logical, physical_symbol=physical, start=day_start(day), end=day_start(day + timedelta(days=1)), rows=count, source=manifest.canonical_source_url))
    return {"files": files, "summary": {"status": "READY" if not missing else "DATA_INVALID", "days": rows, "missing_days": missing}}


def prepare_funding(logical: str, physical: str) -> dict[str, Any]:
    boundaries = funding_boundaries()
    payload_rows = fetch_paginated_time_series(
        "/v5/market/funding/history",
        {"category": "linear", "symbol": physical},
        start=SCREEN_START,
        end=SCREEN_END + timedelta(milliseconds=1),
        time_field="fundingRateTimestamp",
        limit=200,
    )
    by_time = {datetime.fromtimestamp(int(row["fundingRateTimestamp"]) / 1000, UTC): row for row in payload_rows}
    records = []
    missing = []
    for boundary in boundaries:
        row = by_time.get(boundary)
        if row is None:
            missing.append(iso(boundary))
            records.append({"symbol": physical, "logical_symbol": logical, "funding_time": iso(boundary), "status": "MISSING"})
            continue
        records.append({
            "symbol": physical,
            "logical_symbol": logical,
            "funding_time": iso(boundary),
            "status": "AVAILABLE",
            "funding_rate": str(Decimal(str(row["fundingRate"]))),
            "source": "bybit_public_v5_market_funding_history",
        })
    path = DATASET_ROOT / "funding" / f"{physical}__funding__{stamp(SCREEN_START)}__{stamp(SCREEN_END)}.json"
    write_json(path, records)
    csv_path = DATASET_ROOT / "funding" / f"{physical}__funding_coverage.csv"
    write_csv(csv_path, records, ["symbol", "logical_symbol", "funding_time", "status", "funding_rate", "source"])
    return {
        "files": [
            file_record(path, data_type="funding_facts", symbol=logical, physical_symbol=physical, start=SCREEN_START, end=SCREEN_END, rows=len(records), source="bybit_public_v5_market_funding_history"),
            file_record(csv_path, data_type="funding_coverage", symbol=logical, physical_symbol=physical, start=SCREEN_START, end=SCREEN_END, rows=len(records), source="local_generated"),
        ],
        "summary": {"status": "READY" if not missing else "DATA_INVALID", "required_boundaries": [iso(item) for item in boundaries], "missing": missing, "rows": len(records)},
    }


def prepare_mark_price(logical: str, physical: str) -> dict[str, Any]:
    rows = fetch_kline(symbol=physical, endpoint="/v5/market/mark-price-kline", result_key="list", start=WARMUP_START, end=SCREEN_END)
    path = DATASET_ROOT / "mark_price" / f"{physical}__mark_price__1m__{stamp(WARMUP_START)}__{stamp(SCREEN_END)}.json"
    data = [candle_to_dict(row) for row in rows]
    write_json(path, data)
    expected = int((SCREEN_END - WARMUP_START).total_seconds() // 60)
    end_mark = next((row for row in reversed(data) if row["close_time"] == iso(SCREEN_END)), None)
    return {
        "files": [file_record(path, data_type="mark_price_1m", symbol=logical, physical_symbol=physical, start=WARMUP_START, end=SCREEN_END, rows=len(data), source="bybit_public_v5_market_mark_price_kline")],
        "summary": {"status": "READY" if len(data) == expected and end_mark is not None else "DATA_INVALID", "rows": len(data), "expected_rows": expected, "end_boundary_mark_available": end_mark is not None},
    }


def prepare_instrument(symbol: str) -> dict[str, Any]:
    response = bybit_get("/v5/market/instruments-info", {"category": "linear", "symbol": symbol})
    rows = response.get("result", {}).get("list") or []
    if not rows:
        raise RuntimeError("instrument metadata missing")
    row = rows[0]
    path = DATASET_ROOT / "instruments" / f"{symbol}__instrument_metadata.json"
    write_json(path, {"source": "bybit_public_v5_instruments_info_linear", "fetched_at": iso(datetime.now(UTC)), "payload": row})
    pf = row.get("priceFilter") or {}
    lf = row.get("lotSizeFilter") or {}
    lev = row.get("leverageFilter") or {}
    required = {
        "tick_size": pf.get("tickSize"),
        "qty_step": lf.get("qtyStep"),
        "min_order_qty": lf.get("minOrderQty"),
        "min_notional": lf.get("minNotionalValue"),
        "max_order_qty": lf.get("maxOrderQty"),
        "contract_type": row.get("contractType"),
        "trading_status": row.get("status"),
        "max_leverage": lev.get("maxLeverage"),
    }
    ready = all(value not in {None, ""} for value in required.values()) and row.get("contractType") == "LinearPerpetual" and row.get("status") == "Trading"
    return {"files": [file_record(path, data_type="instrument_metadata", symbol=symbol, physical_symbol=symbol, rows=1, source="bybit_public_v5_instruments_info_linear")], "summary": {"status": "READY" if ready else "DATA_INVALID", **required}}


def feature_readiness(physical: str) -> dict[str, Any]:
    path = DATASET_ROOT / "candles" / f"{physical}__linear__1m__{stamp(WARMUP_START)}__{stamp(SCREEN_END)}.json"
    candles = tuple(dict_to_candle(row) for row in json.loads(path.read_text(encoding="utf-8")))
    checks = {
        "ATR15": atr15(candles, cutoff=SCREEN_START),
        "return5": return_pct_points(candles, cutoff=SCREEN_START, window_minutes=5),
        "return15": return_pct_points(candles, cutoff=SCREEN_START, window_minutes=15),
        "EMA20": ema15(candles, cutoff=SCREEN_START, period=20),
        "EMA50": ema15(candles, cutoff=SCREEN_START, period=50),
        "RVOL5": rvol5(candles, cutoff=SCREEN_START),
        "turnover_acceleration": turnover_acceleration(candles, cutoff=SCREEN_START),
    }
    swing_count = len(confirmed_swing5_references(candles, cutoff=SCREEN_START))
    atr_values = tuple(value for _, value in wilder_atr_series(aggregate_completed_bars(candles, timeframe_minutes=15, cutoff=SCREEN_START), period=14))
    compression_ready = len(atr_values) >= 97
    unavailable = {name: obs.reason for name, obs in checks.items() if obs.status.value == "UNAVAILABLE"}
    if swing_count <= 0:
        unavailable["swing5"] = "NO_CONFIRMED_SWING_HISTORY"
    if not compression_ready:
        unavailable["compression_median"] = "INSUFFICIENT_ATR15_HISTORY"
    return {"status": "READY" if not unavailable else "NOT_READY", "unavailable": unavailable, "swing5_confirmed_count": swing_count, "atr15_values_for_compression": len(atr_values)}


def build_job_readiness(**summaries: Any) -> list[dict[str, Any]]:
    jobs = load_research_v2_jobs()
    result = []
    for job_id in sorted(jobs):
        candles_ready = all(item.get("status") == "READY" for item in summaries["candle_summary"].values())
        raw_ready = all(item.get("status") == "READY" for item in summaries["raw_summary"].values())
        funding_ready = all(item.get("status") == "READY" for item in summaries["funding_summary"].values())
        mark_ready = all(item.get("status") == "READY" for item in summaries["mark_summary"].values())
        instrument_ready = all(item.get("status") == "READY" for item in summaries["instrument_summary"].values())
        feature_ready = all(item.get("status") == "READY" for item in summaries["feature_summary"].values())
        row = {
            "job_id": job_id,
            "candles_ready": candles_ready,
            "raw_trades_ready": raw_ready,
            "funding_ready": funding_ready,
            "mark_ready": mark_ready,
            "instrument_ready": instrument_ready,
            "warmup_ready": candles_ready and feature_ready,
        }
        row["overall_status"] = "READY" if all(value for key, value in row.items() if key != "job_id") else "DATA_INVALID"
        result.append(row)
    return result


def fetch_kline(*, symbol: str, endpoint: str, result_key: str, start: datetime, end: datetime) -> list[HistoricalCandle]:
    cursor = start
    rows: list[HistoricalCandle] = []
    while cursor < end:
        batch_end = min(cursor + timedelta(minutes=1000), end)
        payload = bybit_get(endpoint, {
            "category": "linear",
            "symbol": symbol,
            "interval": "1",
            "start": str(ms(cursor)),
            "end": str(ms(batch_end) - 1),
            "limit": "1000",
        })
        raw_rows = payload.get("result", {}).get(result_key) or []
        for item in raw_rows:
            candle = bybit_kline_row_to_candle(item, symbol)
            if start <= candle.open_time < end:
                rows.append(candle)
        cursor = batch_end
    return sorted(rows, key=lambda candle: candle.open_time)


def fetch_paginated_time_series(path: str, params: dict[str, str], *, start: datetime, end: datetime, time_field: str, limit: int) -> list[dict[str, Any]]:
    cursor = start
    out: list[dict[str, Any]] = []
    while cursor <= end:
        query = {**params, "startTime": str(ms(cursor)), "endTime": str(ms(end)), "limit": str(limit)}
        payload = bybit_get(path, query)
        rows = payload.get("result", {}).get("list") or []
        if not rows:
            break
        parsed = sorted(rows, key=lambda item: int(item[time_field]))
        out.extend(row for row in parsed if ms(start) <= int(row[time_field]) <= ms(end))
        next_cursor = datetime.fromtimestamp(int(parsed[-1][time_field]) / 1000, UTC) + timedelta(milliseconds=1)
        if next_cursor <= cursor or next_cursor > end:
            break
        cursor = next_cursor
    by_ts = {row[time_field]: row for row in out}
    return [by_ts[key] for key in sorted(by_ts, key=lambda value: int(value))]


def bybit_get(path: str, params: dict[str, str]) -> dict[str, Any]:
    url = f"{BYBIT_API_BASE}{path}?{urlencode(params)}"
    for attempt in range(3):
        try:
            with urlopen(Request(url, method="GET"), timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if int(payload.get("retCode", -1)) != 0:
                raise RuntimeError(f"Bybit retCode={payload.get('retCode')}: {payload.get('retMsg')}")
            return payload
        except Exception:
            if attempt == 2:
                raise
            sleep(0.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def download_file(url: str, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    for attempt in range(3):
        try:
            with urlopen(Request(url, method="GET"), timeout=120) as response:
                tmp.write_bytes(response.read())
            tmp.replace(path)
            return
        except Exception:
            if attempt == 2:
                if tmp.exists():
                    tmp.unlink()
                raise
            sleep(1 + attempt)


def bybit_kline_row_to_candle(item: list[Any], symbol: str) -> HistoricalCandle:
    open_time = datetime.fromtimestamp(int(item[0]) / 1000, UTC)
    return HistoricalCandle(
        symbol=symbol,
        category="linear",
        timeframe="1m",
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=Decimal(str(item[1])),
        high=Decimal(str(item[2])),
        low=Decimal(str(item[3])),
        close=Decimal(str(item[4])),
        volume=Decimal(str(item[5])) if len(item) > 5 else Decimal("0"),
        turnover=Decimal(str(item[6])) if len(item) > 6 else Decimal("0"),
        completed=True,
    )


def candle_to_dict(candle: HistoricalCandle) -> dict[str, Any]:
    data = asdict(candle)
    data["open_time"] = iso(candle.open_time)
    data["close_time"] = iso(candle.close_time)
    for key in ("open", "high", "low", "close", "volume", "turnover"):
        data[key] = str(data[key])
    return data


def dict_to_candle(row: dict[str, Any]) -> HistoricalCandle:
    return HistoricalCandle(
        symbol=str(row["symbol"]),
        category=str(row["category"]),
        timeframe=str(row["timeframe"]),
        open_time=parse_time(str(row["open_time"])),
        close_time=parse_time(str(row["close_time"])),
        open=Decimal(str(row["open"])),
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        close=Decimal(str(row["close"])),
        volume=Decimal(str(row["volume"])),
        turnover=Decimal(str(row["turnover"])),
        completed=bool(row["completed"]),
    )


def funding_boundaries() -> list[datetime]:
    out = []
    cursor = SCREEN_START
    while cursor <= SCREEN_END:
        if cursor.hour in {0, 8, 16} and cursor >= SCREEN_START:
            out.append(cursor)
        cursor += timedelta(hours=1)
    return out


def days(start: date, end: date) -> list[date]:
    out = []
    cursor = start
    while cursor <= end:
        out.append(cursor)
        cursor += timedelta(days=1)
    return out


def day_start(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_inventory(path: Path, files: list[dict[str, Any]]) -> None:
    fields = ["type", "symbol", "physical_symbol", "start", "end", "rows", "bytes", "sha256", "source", "local_path"]
    write_csv(path, files, fields)


def file_record(
    path: Path,
    *,
    data_type: str,
    symbol: str | None,
    source: str,
    physical_symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    rows: int | None = None,
) -> dict[str, Any]:
    return {
        "type": data_type,
        "symbol": symbol,
        "physical_symbol": physical_symbol,
        "start": None if start is None else iso(start),
        "end": None if end is None else iso(end),
        "rows": rows,
        "bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "source": source,
        "local_path": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def count_gzip_csv_rows(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def sha256_json(payload: Any) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def stamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def ms(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp() * 1000)


def _error(data_family: str, symbol: str, error: str, *, physical_symbol: str | None = None) -> dict[str, str]:
    return {"data_family": data_family, "symbol": symbol, "physical_symbol": physical_symbol or symbol, "error": error}


if __name__ == "__main__":
    raise SystemExit(main())
