# TriggerTrade Bybit Raw Market Data Catalog

**Document ID:** TT-DATA-001
**Version:** 0.2.1
**Status:** ACCEPTED BASELINE — methodology foundation
**Scope:** Bybit V5 public market data for `linear` perpetual futures, with primary emphasis on `LinearPerpetual` instruments
**Verified against Bybit V5 documentation:** 2026-09-09
**Governing methodology:** TriggerTrade Methodology Council and its contracts

---

## 1. Purpose

This document defines the **raw data boundary** of TriggerTrade.

Its purpose is to answer, before any indicator, setup, trigger, or Trading Rule Set is designed:

> **What market and exchange data can TriggerTrade observe from Bybit, at what native granularity, with what semantics, and with what historical/realtime availability?**

This is a methodology specification, not implementation code.

The document is deliberately limited to **raw and exchange-native data**. It does **not** define derived indicators such as ATR, RVOL, CVD, OI delta, volatility percentiles, market structure, order-book imbalance, regime classifications, setups, or entry triggers. Those belong to the next methodology layer.

---

## 2. Methodology role of this document

TriggerTrade must be built in the following order:

```text
BYBIT / EXCHANGE-NATIVE DATA
        ↓
TRIGGERTRADE NORMALIZED RAW DATA
        ↓
DERIVED METRICS
        ↓
MARKET INTERPRETATION / FEATURES
        ↓
MARKET REGIME
        ↓
SETUP
        ↓
TRIGGER
        ↓
TRADING RULE SET (TRS)
```

No later methodology layer may require a variable that cannot be traced back to an explicitly defined raw data source or an explicitly defined external source.

---

## 3. Relevant methodology lenses

This catalog is primarily governed by four existing TriggerTrade methodology roles:

- **Execution & Exchange Mechanics Specialist** — exchange semantics, execution constraints, precision, order book, funding, risk limits, timestamps, latency, and contract mechanics.
- **Market Microstructure & Order Flow Researcher** — trades, aggressor side, order book, liquidations, OI, funding, positioning, and other microstructure observables.
- **Quant Strategy Researcher** — historical availability, reproducibility, timestamp integrity, granularity, look-ahead prevention, and backtest feasibility.
- **Senior Intraday Crypto Trader** — completeness of the observable market-state universe needed later for context, setup, trigger, and trade management research.

This artifact does not promote any trading idea. No item in this catalog is a trading edge by itself.

---

# PART I — DATA GOVERNANCE

## 4. Scope decisions

### 4.1 Primary market type

Initial TriggerTrade research scope:

```yaml
exchange: BYBIT
api_family: V5
category: linear
contract_type: LinearPerpetual
trading_style: intraday
```

Both USDT-settled and USDC-settled linear perpetual instruments may exist under `category=linear`. Any later universe restriction must be explicit in the Trading Universe specification and must not be silently assumed here.

### 4.2 Public data only

This catalog covers **public market and exchange-reference data** required to understand the market.

Private account data such as wallet balance, own positions, own orders, own fills, realized PnL, margin balance, and account fee tier are outside this document and will belong to execution/risk/account-state specifications.

### 4.3 Raw means exchange-native

A field is considered raw when it is supplied directly by Bybit or is metadata necessary to interpret such a field.

Examples:

- `price` from public trade = raw.
- `openInterest` from Bybit = raw.
- `fundingRate` from Bybit = raw.
- `bid price / size` = raw.
- `CVD` = **not raw**.
- `OI change %` = **not raw**.
- `spread %` = **not raw** even though bid and ask are raw.
- `RVOL` = **not raw**.
- `ATR` = **not raw**.

---

## 5. Required availability vocabulary

Every data source must be classified using the following availability states.

| State | Meaning |
|---|---|
| `REST_SNAPSHOT` | Current/recent value can be requested over REST. |
| `REST_HISTORICAL` | A time range can be queried over the official V5 REST API. |
| `WS_REALTIME` | Public WebSocket stream is available for live use. |
| `ARCHIVE_HISTORICAL` | Historical data is available through an official Bybit archive/download mechanism rather than the normal V5 history endpoint. |
| `HISTORICAL_LIMITED` | Historical coverage or native granularity is materially narrower than realtime availability. |
| `REFERENCE_DATA` | Exchange/instrument metadata rather than continuously sampled market state. |

**Critical rule:** `WS_REALTIME` must never be interpreted as historical availability.

TriggerTrade will **not build a permanent proprietary archive of high-frequency Bybit market streams solely to expand backtest coverage**. Backtests must use data that Bybit makes historically available through supported API/history/archive mechanisms. Where suitable historical data does not exist, that data family is outside the core evidence path for TriggerTrade trigger methodology unless and until an official historical source becomes available.

A backtest may only use historical observations that are genuinely available with the required granularity and timestamp semantics. Realtime availability alone is not sufficient to qualify a data family as a core trigger input.

---

## 6. Timestamp contract

All normalized TriggerTrade raw records must preserve enough timing information to separate:

1. **exchange event time** — when the trade/order-book update/liquidation actually occurred or was generated by the matching engine;
2. **exchange system publication time** — when Bybit generated the message;
3. **ingestion time** — when TriggerTrade received the message;
4. **interval start/end** — for bar-like observations;
5. **closed/open status** — where the API exposes whether an interval is final.

Canonical timestamp rules:

```yaml
time_standard: UTC
storage: integer epoch milliseconds unless higher precision is natively available and materially useful
never_use_local_timezone_as_storage_key: true
preserve_exchange_timestamp: true
preserve_ingestion_timestamp_for_realtime_streams: true
```

For WebSocket order-book research, matching-engine timestamp (`cts`) and update sequence identifiers must be retained when supplied.

For WebSocket public trades, trade match time (`T`) must be retained.

For candles, an unclosed candle must not be treated as a final historical bar.

---

## 7. Numeric precision contract

Bybit commonly serializes numeric values as strings. TriggerTrade must not normalize price, size, OI, funding, or notional data through binary floating-point as the canonical stored representation.

Methodology requirement:

```yaml
canonical_numeric_semantics: decimal
preserve_exchange_precision: true
price_quantization_source: instrument.priceFilter.tickSize
quantity_quantization_source: instrument.lotSizeFilter.qtyStep
```

Implementation may later select Decimal, scaled integers, or another exact representation, but the methodology requires deterministic precision.

---

## 8. Symbol identity contract

Raw observations must not be keyed by a display label alone.

Minimum normalized identity:

```yaml
exchange: BYBIT
category: linear
symbol: BTCUSDT
contract_type: LinearPerpetual
base_coin: BTC
quote_coin: USDT
settle_coin: USDT
```

Instrument metadata is part of the data contract because symbol mechanics may change and instruments may be listed, pre-listed, delisted, or otherwise change status.

---

# PART II — MASTER RAW DATA INVENTORY

## 9. Inventory summary

| ID | Data family | Canonical Bybit source | Realtime | Historical/backfill | Primary future use |
|---|---|---|---|---|---|
| `REF-TIME-001` | Server time | Market Time REST | snapshot | n/a | clock alignment |
| `REF-INST-001` | Instrument specification | Instruments Info REST | poll/reference | current/reference | universe + precision + mechanics |
| `REF-RISK-001` | Risk limits | Risk Limit REST | poll/reference | not research time series by default | execution/risk feasibility |
| `MKT-TICK-001` | Market ticker snapshot | Tickers REST / WS | yes | no canonical bar history | current market state |
| `MKT-KLINE-001` | Trade-price OHLCV | Kline REST / WS | yes | yes | price/volume base layer |
| `MKT-MARK-001` | Mark-price OHLC | Mark Price Kline REST | current via ticker | yes | mark/index/basis research |
| `MKT-INDEX-001` | Index-price OHLC | Index Price Kline REST | current via ticker | yes | external fair-price anchor |
| `MKT-PREM-001` | Premium-index OHLC | Premium Index Price Kline REST | current funding/ticker context | yes | perp premium/crowding |
| `FLOW-TRADE-001` | Public executions | Recent Trades REST / Public Trade WS | yes, realtime | recent REST + official archive where available | aggressor flow / trade tape |
| `FLOW-BOOK-001` | Order book | Orderbook REST / WS | yes, high frequency | limited: snapshot/current access; no assumed Bybit-native full historical book replay | liquidity / spread / depth |
| `DERIV-OI-001` | Open interest | Open Interest REST / ticker | ticker current | yes | positioning/leverage |
| `DERIV-FUND-001` | Funding | Funding History REST / ticker | current via ticker | yes | perp positioning/carry |
| `DERIV-LS-001` | Long/short account ratio | Account Ratio REST | interval updates | yes | account positioning |
| `DERIV-LIQ-001` | Public liquidations | All Liquidation WS | yes | realtime-only unless Bybit provides a suitable historical source | forced-flow research |
| `EXCH-ADL-001` | ADL / insurance pool alert | ADL Alert REST / WS | yes | not treated as historical research feed by default | exchange stress / execution risk |

The catalog intentionally keeps overlapping sources. For example, OI appears in the ticker and in the dedicated OI endpoint. The **dedicated endpoint is canonical for historical OI**, while ticker OI is useful as current market state.

---

# PART III — SOURCE SPECIFICATIONS

## 10. `REF-TIME-001` — Bybit Server Time

**Type:** exchange reference / clock synchronization
**Endpoint:** `GET /v5/market/time`
**Availability:** `REST_SNAPSHOT`
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/time

### Raw fields

- `timeSecond`
- `timeNano`
- top-level response time where supplied

### Methodology purpose

- estimate clock drift between TriggerTrade and Bybit;
- validate timestamp alignment;
- support latency and ingestion diagnostics;
- prevent local machine clock from becoming the implicit market-time authority.

### Storage requirement

Server-time samples do not need tick-level permanent storage for market research, but clock-drift diagnostics should be retained when realtime acquisition is running.

---

## 11. `REF-INST-001` — Instrument Specification

**Type:** exchange reference metadata
**Endpoint:** `GET /v5/market/instruments-info`
**Filter:** `category=linear`, later filtered by `contractType=LinearPerpetual`
**Availability:** `REFERENCE_DATA`; must be refreshed
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/instrument

### Raw fields required for TriggerTrade

#### Identity

- `symbol`
- `symbolId` when available
- `contractType`
- `status`
- `baseCoin`
- `quoteCoin`
- `settleCoin`
- `symbolType`
- `displayName`
- `launchTime`
- `deliveryTime` / delisting time semantics when applicable

#### Price mechanics

- `priceScale`
- `priceFilter.minPrice`
- `priceFilter.maxPrice`
- `priceFilter.tickSize`

#### Quantity mechanics

- `lotSizeFilter.minNotionalValue`
- `lotSizeFilter.minOrderQty`
- `lotSizeFilter.maxOrderQty`
- `lotSizeFilter.maxMktOrderQty`
- `lotSizeFilter.qtyStep`

#### Leverage mechanics

- `leverageFilter.minLeverage`
- `leverageFilter.maxLeverage`
- `leverageFilter.leverageStep`

#### Funding mechanics

- `fundingInterval` in minutes
- `upperFundingRate`
- `lowerFundingRate`

#### Other execution/reference flags

- `unifiedMarginTrade`
- pre-listing fields when applicable
- exchange risk parameters when exposed

### Important Bybit constraint

Bybit explicitly warns that some maximum-order-quantity fields can be adjusted periodically. TriggerTrade therefore must **not treat instrument metadata as immutable configuration**.

### Methodology use

This source will later support:

- tradeable-universe filtering;
- minimum liquidity/execution constraints;
- valid order rounding;
- leverage rules;
- funding schedule alignment;
- listing-age requirements;
- exclusion of non-trading or prelaunch instruments.

### Historical requirement

For reproducible backtests, TriggerTrade should eventually retain **effective-dated snapshots** of instrument metadata. Using today's tick size, quantity limits, funding bounds, or symbol status to model an old trade can create historical inconsistency.

---

## 12. `REF-RISK-001` — Exchange Risk Limit Parameters

**Type:** exchange mechanics reference
**Endpoint:** `GET /v5/market/risk-limit`
**Availability:** `REFERENCE_DATA`
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/risk-limit

### Candidate raw fields

Retain all tier-level parameters returned for linear contracts, including risk tier identifiers and leverage/margin-related limits.

### Methodology use

- determine whether a theoretically valid position size is executable;
- constrain future leverage rules;
- model exchange-imposed risk tiers;
- identify execution/risk feasibility changes.

### Research status

Not a market-entry signal. Do not include in strategy features unless a separate causal hypothesis is formally opened.

---

## 13. `MKT-TICK-001` — Market Ticker Snapshot

**Type:** current aggregate market state
**REST:** `GET /v5/market/tickers`
**WS:** `tickers.{symbol}`
**Availability:** `REST_SNAPSHOT`, `WS_REALTIME`
**Official documentation:**
https://bybit-exchange.github.io/docs/v5/market/tickers
https://bybit-exchange.github.io/docs/v5/websocket/public/ticker

### Raw fields relevant to linear perpetuals

- `symbol`
- `lastPrice`
- `indexPrice`
- `markPrice`
- `prevPrice24h`
- `price24hPcnt`
- `highPrice24h`
- `lowPrice24h`
- `prevPrice1h`
- `openInterest`
- `openInterestValue`
- `singleOpenInterest` when returned
- `singleOpenInterestValue` when returned
- `turnover24h`
- `volume24h`
- `fundingRate`
- `nextFundingTime`
- `bid1Price`
- `bid1Size`
- `ask1Price`
- `ask1Size`
- `basis` / `basisRate` where applicable
- pre-market fields only when such instruments are deliberately included
- WS `ts`, `cs`, and message type where supplied

### Methodology rule

Ticker fields such as `price24hPcnt`, `volume24h`, and `turnover24h` are **exchange-provided rolling aggregates**. They are raw exchange fields even though they represent exchange-side calculations.

However, when TriggerTrade can reproduce an aggregate from lower-level retained data, methodology should distinguish:

```text
EXCHANGE_NATIVE_AGGREGATE
vs
TRIGGERTRADE_DERIVED_METRIC
```

### Historical limitation

Ticker WS is not treated as a canonical historical series. TriggerTrade will not maintain a permanent ticker-state archive for backtesting. Research that depends on exact historical ticker-state replay is therefore outside the default backtest scope unless Bybit provides an appropriate historical source.

---

## 14. `MKT-KLINE-001` — Trade-Price Klines / OHLCV

**Type:** exchange-native aggregated trade data
**REST:** `GET /v5/market/kline`
**WS:** `kline.{interval}.{symbol}`
**Availability:** `REST_HISTORICAL`, `WS_REALTIME`
**Official documentation:**
https://bybit-exchange.github.io/docs/v5/market/kline
https://bybit-exchange.github.io/docs/v5/websocket/public/kline

### Native intervals

- 1m
- 3m
- 5m
- 15m
- 30m
- 60m
- 120m
- 240m
- 360m
- 720m
- 1D
- 1W
- 1M

### Raw fields

- interval start time
- interval end time where supplied
- `open`
- `high`
- `low`
- `close`
- `volume`
- `turnover`
- interval identifier
- `confirm` for WS candle closure
- last matched-order timestamp within the candle where supplied

### Critical methodology rule

A Kline is already an **exchange aggregation of lower-level trades**. It is raw relative to TriggerTrade, but it is not tick-level raw market microstructure.

### Candle-finality rule

`confirm=false` is a mutable current observation and must not be silently mixed with closed historical candles.

Normalized contract must include:

```yaml
is_closed: true | false
```

### Later metrics enabled

This source can later support price returns, ranges, candle anatomy, volume, turnover, ATR-family metrics, volatility, momentum, structure, VWAP-like research where mathematically appropriate, and many other derived features.

None of those are defined here.

---

## 15. `MKT-MARK-001` — Mark Price Klines

**Type:** exchange-native derivative fair-price series
**Endpoint:** `GET /v5/market/mark-price-kline`
**Availability:** `REST_HISTORICAL`; current mark price also available in ticker
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/mark-kline

### Native intervals

1m, 3m, 5m, 15m, 30m, 60m, 120m, 240m, 360m, 720m, D, W, M.

### Raw fields

- start timestamp
- open mark price
- high mark price
- low mark price
- close mark price

### Methodology use

- compare traded price, mark price, and index price;
- understand liquidation-relevant pricing context;
- derive future premium/basis features;
- separate traded-price dislocations from mark-price behavior.

### Important distinction

Mark price is not the same object as last traded price and must never be merged into one generic `price` field without a price-type discriminator.

---

## 16. `MKT-INDEX-001` — Index Price Klines

**Type:** external/fair-price benchmark used by Bybit
**Endpoint:** `GET /v5/market/index-price-kline`
**Availability:** `REST_HISTORICAL`; current index price also available in ticker
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/index-kline

### Native intervals

1m, 3m, 5m, 15m, 30m, 60m, 120m, 240m, 360m, 720m, D, W, M.

### Raw fields

- start timestamp
- open index price
- high index price
- low index price
- close index price

### Methodology use

- benchmark against perpetual contract pricing;
- later basis/premium calculations;
- detection of exchange-specific traded-price deviations;
- liquidation/execution context.

---

## 17. `MKT-PREM-001` — Premium Index Price Klines

**Type:** exchange-native perpetual premium series
**Endpoint:** `GET /v5/market/premium-index-price-kline`
**Scope:** USDT and USDC perpetuals
**Availability:** `REST_HISTORICAL`
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/premium-index-kline

### Native intervals

1m, 3m, 5m, 15m, 30m, 60m, 120m, 240m, 360m, 720m, D, W, M.

### Raw fields

- start timestamp
- open premium-index value
- high premium-index value
- low premium-index value
- close premium-index value

### Methodology use

Potential basis for later research into:

- perpetual premium;
- crowding;
- funding context;
- dislocation between perpetual and reference market.

No directional interpretation is accepted at this stage.

---

## 18. `FLOW-TRADE-001` — Public Trade Executions

**Type:** executed trade tape / microstructure event stream
**REST:** `GET /v5/market/recent-trade`
**WS:** `publicTrade.{symbol}`
**Availability:** `REST_SNAPSHOT` of recent trades, `WS_REALTIME`, `ARCHIVE_HISTORICAL` where Bybit provides archived trades
**Official documentation:**
https://bybit-exchange.github.io/docs/v5/market/recent-trade
https://bybit-exchange.github.io/docs/v5/websocket/public/trade

### Raw fields

#### REST

- `execId`
- `symbol`
- `price`
- `size`
- `side` — taker side
- `time`
- `isBlockTrade`
- `isRPITrade`
- `seq`

#### WebSocket

At minimum retain:

- trade match timestamp `T`
- symbol `s`
- taker side `S`
- trade size `v`
- trade price `p`
- price-change direction where supplied
- message timestamp `ts`
- sequence information where supplied
- trade identifiers/flags supplied by the stream

### Critical semantic rule

`side=Buy` means **taker side Buy**, not that “buyers outnumber sellers.” Every execution necessarily has both a buyer and seller.

This field later enables aggressor-flow calculations, but those calculations are derived metrics.

### Historical rule

The normal recent-trades endpoint is not a general time-range historical query. Where Bybit provides an official archived historical-trade dataset, it may be used for research after its coverage and timestamp semantics are validated. TriggerTrade does not create its own permanent trade archive solely for backtesting.

### Later metrics enabled

Potentially:

- aggressive buy/sell volume;
- trade delta;
- CVD;
- trade-count imbalance;
- average/median trade size;
- large-trade classifications;
- execution bursts;
- short-horizon realized microstructure features.

All remain undefined until the Derived Metrics Catalog.

---

## 19. `FLOW-BOOK-001` — Order Book

**Type:** displayed resting liquidity
**REST:** `GET /v5/market/orderbook`
**WS:** `orderbook.{depth}.{symbol}`
**Availability:** `REST_SNAPSHOT`, `WS_REALTIME`, `HISTORICAL_LIMITED`
**Official documentation:**
https://bybit-exchange.github.io/docs/v5/market/orderbook
https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook

### Linear/inverse WebSocket depths and current documented push frequencies

| Depth | Push frequency |
|---:|---:|
| 1 | 10 ms |
| 50 | 20 ms |
| 200 | 100 ms |
| 1000 | 200 ms |

### Raw fields

- symbol
- bids: `[price, size]`
- asks: `[price, size]`
- snapshot/delta message type
- exchange/system timestamp `ts`
- matching-engine timestamp `cts`
- update id `u`
- cross sequence `seq`
- depth subscription level

### Reconstruction rule

A historical/realtime local book must respect Bybit snapshot/delta semantics:

- initialize from snapshot;
- apply subsequent deltas in sequence;
- size `0` removes a level;
- a new snapshot resets the local book;
- sequence/update identifiers must be retained for integrity checking.

### Bybit limitation

Bybit states that RPI orders are not included in public order-book messages. TriggerTrade therefore observes **public displayed book liquidity**, not the complete universe of all executable/hidden liquidity.

### Critical research limitation

Order-book features are particularly vulnerable to:

- cancelled orders;
- spoof-like displayed liquidity;
- latency;
- missed deltas;
- depth choice;
- survivorship of displayed liquidity;
- using a reconstructed book that differs from the state available to the strategy at decision time.

Consequently, order-book-derived research cannot be considered historically backtestable merely because realtime WS access exists. TriggerTrade may use order-book data in live or paper operation, but default methodology will not require permanent full-depth order-book retention. Any historical validation claim must be limited to whatever historical order-book data Bybit actually makes available.

---

## 20. `DERIV-OI-001` — Open Interest

**Type:** derivatives positioning / outstanding contracts
**Endpoint:** `GET /v5/market/open-interest`
**Availability:** `REST_HISTORICAL`; current OI also available through ticker
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/open-interest

### Native historical periods

- 5min
- 15min
- 30min
- 1h
- 4h
- 1d

### Raw fields

- `symbol`
- `category`
- `openInterest` — sum of both sides
- `singleOpenInterest` — single-side OI where supplied
- `timestamp`

### Unit semantics

Bybit documents that the OI unit depends on contract type. For linear BTCUSDT, the OI quantity is denominated in BTC; inverse examples use USD.

TriggerTrade must therefore retain an explicit normalized unit and must never compare absolute OI quantities across instruments without normalization.

### Important limitation

Historical OI is not natively offered by this endpoint at 1m or 3m intervals. Any metric requiring sub-5m historical OI therefore has **limited historical testability** under the default TriggerTrade methodology and must not be backtested as though native 1m/3m OI history existed.

### Later metrics enabled

- OI absolute value;
- notionalized OI;
- OI change / percent change;
- OI velocity/acceleration;
- OI percentile / z-score;
- price × OI interaction.

These are derived metrics, not raw data.

---

## 21. `DERIV-FUND-001` — Funding Rate

**Type:** perpetual funding / carry state
**Historical endpoint:** `GET /v5/market/funding/history`
**Current value:** ticker REST/WS
**Availability:** `REST_HISTORICAL`, `REST_SNAPSHOT`, `WS_REALTIME` through ticker current state
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/history-fund-rate

### Raw historical fields

Retain the exchange-returned symbol, funding rate, and funding timestamp/settlement time.

### Required companion metadata

`REF-INST-001.fundingInterval` must be retained because Bybit states that funding intervals can differ by symbol.

### Current-state fields from ticker

- `fundingRate`
- `nextFundingTime`

### Methodology rule

Funding must be modeled on its **native settlement schedule**. It must not be mechanically transformed into a “1-minute funding indicator” without an explicit derived-metric definition.

### Later metrics enabled

- funding percentile;
- funding z-score;
- funding trend/changes;
- extreme funding flags;
- funding × OI × price interactions;
- realized funding cost for held positions.

---

## 22. `DERIV-LS-001` — Long/Short Account Ratio

**Type:** exchange account-positioning aggregate
**Endpoint:** `GET /v5/market/account-ratio`
**Availability:** `REST_HISTORICAL`
**Official documentation:** https://bybit-exchange.github.io/docs/v5/market/long-short-ratio

### Native periods

- 5min
- 15min
- 30min
- 1h
- 4h
- 1d

### Exchange semantics

Bybit defines:

- Long account ratio = number of position holders with long positions / total position holders.
- Short account ratio = number of position holders with short positions / total position holders.
- Long-short account ratio = long account ratio / short account ratio.

### Raw fields

Retain:

- symbol
- timestamp
- period
- buy/long ratio
- sell/short ratio
- any exchange-returned ratio field

### Historical note

Bybit documents an earliest query start time of **2020-07-20** for this endpoint.

### Critical interpretation rule

This is an **account-count positioning statistic**, not total long notional versus total short notional and not a direct directional forecast.

---

## 23. `DERIV-LIQ-001` — Public Liquidations

**Type:** forced-position-close event stream
**WS:** `allLiquidation.{symbol}`
**Availability:** `WS_REALTIME`; no suitable historical liquidation series is assumed for core TriggerTrade research unless Bybit provides an official historical source
**Documented push frequency:** 500 ms
**Official documentation:** https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation

### Raw fields

- event/update timestamp `T`
- symbol `s`
- position side `S`
- executed liquidation size `v`
- bankruptcy price `p`
- message timestamp `ts`

### Critical side semantic

Bybit explicitly documents:

- `Buy` update = a **long position has been liquidated**.

TriggerTrade normalized schema must therefore use a field such as `liquidated_position_side`, not blindly rename Bybit `S` to generic trade side.

### Historical limitation

The public V5 market liquidation feed does not qualify as a core TriggerTrade trigger input unless a suitable official historical source exists for the required research horizon and granularity. TriggerTrade will not maintain a permanent liquidation archive solely to make such features backtestable. Liquidation observations may still be documented as market context, but they must not be promoted into a core trigger rule without adequate historical evidence.

### Later metrics enabled

- long liquidation notional;
- short liquidation notional;
- liquidation intensity;
- liquidation clusters;
- liquidation × volume / OI / price interactions.

None are raw fields.

---

## 24. `EXCH-ADL-001` — ADL Alert and Insurance Pool State

**Type:** exchange stress / auto-deleveraging mechanics
**REST:** `GET /v5/market/adlAlert`
**WS:** `adlAlert.{coin}`
**Availability:** REST periodic + WS realtime
**Official documentation:**
https://bybit-exchange.github.io/docs/v5/market/adl-alert
https://bybit-exchange.github.io/docs/v5/websocket/public/adl-alert

### Candidate raw fields

- update timestamp
- insurance-pool coin
- symbol
- insurance fund balance
- symbol PnL-drawdown ratio field where exposed
- ADL trigger threshold fields
- ADL stop threshold fields

### Methodology use

This feed is not initially part of the core entry-feature set. It belongs to the **exchange-stress and execution-risk layer** and may later support no-trade filters or emergency risk controls if research justifies them.

### Historical status

Do not assume full historical backfill. If later methodology uses ADL state as a decision variable, historical availability must be separately verified before backtesting.

---

# PART IV — NORMALIZED TRIGGERTRADE RAW DATA CONTRACT

## 25. Why normalization is mandatory

TriggerTrade methodology must not directly depend on Bybit response field names throughout the system.

Required architecture:

```text
Bybit REST / WebSocket
        ↓
Bybit acquisition adapter
        ↓
Bybit-native payload preservation (optional, short-lived diagnostic only)
        ↓
TriggerTrade normalized raw records
        ↓
Derived Metrics Engine
        ↓
Methodology / Research / Backtest / Live decision layers
```

This separation allows:

- API field changes without rewriting strategy logic;
- consistent timestamp semantics;
- consistent decimal precision;
- later addition of another exchange;
- exact lineage from a metric back to its source;
- reproducible research.

---

## 26. Universal raw-record envelope

Every normalized observation must contain, where applicable:

```yaml
record_id: unique deterministic or generated identifier
schema_version: string
source_id: e.g. FLOW-TRADE-001
exchange: BYBIT
api_family: V5
category: linear
symbol: string | null
contract_type: LinearPerpetual | null

exchange_event_ts: integer | null
exchange_publish_ts: integer | null
ingested_ts: integer
interval_start_ts: integer | null
interval_end_ts: integer | null

source_transport: REST | WS | ARCHIVE
source_endpoint_or_topic: string
sequence_id: string | integer | null

quality_status: VALID | GAP | OUT_OF_ORDER | DUPLICATE | RESET | PARTIAL | UNKNOWN
raw_payload_ref: optional
```

Fields not applicable to a record type remain null rather than being fabricated.

---

## 27. Canonical normalized entity types

### 27.1 `InstrumentSnapshot`

```yaml
symbol
symbol_id
contract_type
status
base_coin
quote_coin
settle_coin
launch_ts
delivery_or_delist_ts
price_scale
min_price
max_price
tick_size
min_notional
min_order_qty
max_limit_order_qty
max_market_order_qty
qty_step
min_leverage
max_leverage
leverage_step
funding_interval_minutes
funding_rate_upper_bound
funding_rate_lower_bound
effective_from_ts
```

### 27.2 `MarketTicker`

```yaml
last_price
mark_price
index_price
best_bid_price
best_bid_size
best_ask_price
best_ask_size
prev_price_1h
prev_price_24h
high_price_24h
low_price_24h
volume_24h
turnover_24h
open_interest_qty
open_interest_value
single_open_interest_qty
single_open_interest_value
funding_rate
next_funding_ts
basis
basis_rate
```

### 27.3 `TradeKline`

```yaml
interval
interval_start_ts
interval_end_ts
open
high
low
close
volume
turnover
is_closed
last_trade_ts
```

### 27.4 `ReferencePriceKline`

```yaml
price_type: MARK | INDEX | PREMIUM_INDEX
interval
interval_start_ts
open
high
low
close
```

### 27.5 `PublicTrade`

```yaml
trade_id
trade_ts
price
quantity
taker_side: BUY | SELL
is_block_trade
is_rpi_trade
sequence_id
```

### 27.6 `OrderBookUpdate`

```yaml
book_depth
message_type: SNAPSHOT | DELTA
matching_engine_ts
exchange_publish_ts
update_id
cross_sequence
bids: [[price, size], ...]
asks: [[price, size], ...]
```

### 27.7 `OpenInterestObservation`

```yaml
interval
observation_ts
open_interest_qty
single_open_interest_qty
unit
```

### 27.8 `FundingObservation`

```yaml
funding_ts
funding_rate
funding_interval_minutes
```

### 27.9 `LongShortAccountRatioObservation`

```yaml
period
observation_ts
long_account_ratio
short_account_ratio
long_short_account_ratio
```

### 27.10 `LiquidationEvent`

```yaml
liquidation_ts
liquidated_position_side: LONG | SHORT
executed_quantity
bankruptcy_price
```

### 27.11 `ExchangeStressObservation`

```yaml
observation_ts
insurance_pool_coin
insurance_pool_balance
symbol_pnl_drawdown_ratio
adl_trigger_threshold
adl_stop_threshold
```

---

# PART V — HISTORICAL RESEARCH BOUNDARIES

## 28. Historical availability matrix

| Source | Bybit historical availability | Realtime | Default historical testability | Initial research priority |
|---|---|---:|---|---|
| Instrument info | current/reference | poll | `LIMITED` for exact historical metadata state | HIGH |
| Trade-price klines | yes | yes | `FULL` at supported intervals | CRITICAL |
| Mark-price klines | yes | current | `FULL` at supported intervals | HIGH |
| Index-price klines | yes | current | `FULL` at supported intervals | HIGH |
| Premium-index klines | yes | limited current context | `FULL` at supported intervals | HIGH |
| Public trades | recent REST + official historical archive where available | yes | `FULL` or `LIMITED` depending on archive coverage | CRITICAL |
| Order book | current snapshot; realtime WS | yes | `LIMITED/NONE` for historical book dynamics unless Bybit supplies history | OUTSIDE CORE TRIGGER PATH if adequate history is unavailable |
| Open interest | yes, minimum native period 5m | current | `FULL` at native periods; `NONE` below native historical granularity | CRITICAL |
| Funding | yes | current | `FULL` for available funding history | CRITICAL |
| Long/short account ratio | yes | interval | `FULL` at native periods | MEDIUM/HIGH |
| Liquidations | realtime feed; no historical V5 market series assumed here | yes | `NONE` unless an official historical source exists | OUTSIDE CORE TRIGGER PATH if adequate history is unavailable |
| ADL/insurance stress | current/realtime | yes | `NONE/LIMITED` by default | LOW initially |
| Risk limits | current/reference | poll | `LIMITED` for exact historical tier reproduction | MEDIUM |

---

## 29. Default TriggerTrade historical-data policy

TriggerTrade adopts the following methodology policy:

```yaml
permanent_market_stream_archiving_for_backtests: false
backtest_sources:
  - Bybit historical REST endpoints
  - Bybit official historical/archive datasets where available
  - other explicitly approved historical sources only if methodology scope is later expanded
realtime_sources:
  - Bybit public WebSocket
  - Bybit current REST snapshots
```

### Consequences

1. The system may process realtime WebSocket data for live/paper decisions without retaining a permanent high-frequency market archive.
2. A metric can be valid for live use even if historical testability is limited or absent.
3. Lack of historical data does **not** justify fabricating a lower-frequency proxy and calling it equivalent.
4. Research conclusions must explicitly state when evidence covers only the historically available subset of a metric.
5. The methodology should preferentially select metrics that provide substantial information gain relative to their data/operational complexity; high-volume streams do not receive priority merely because they exist.

This is an intentional architecture constraint, not a temporary infrastructure gap.

---

# PART VI — DATA QUALITY AND RESEARCH INTEGRITY

## 30. Mandatory data quality checks

Every acquired raw dataset must support at least the following checks.

### Identity

- symbol known in instrument metadata;
- expected contract type;
- expected settle coin;
- observation falls after launch and before delisting where applicable.

### Time

- timestamps parse correctly;
- no impossible future event time;
- interval boundaries align with requested interval;
- closed candles are distinguishable from open candles;
- event ordering can be reconstructed where sequence IDs exist.

### Completeness

- expected bars are not silently missing;
- WS disconnect intervals are explicitly marked;
- order-book sequence gaps invalidate the reconstructed book until recovery;
- pagination is fully consumed where required.

### Numeric validity

- prices and quantities are non-negative where logically required;
- tick/step precision is respected;
- numeric strings parse without float-rounding corruption;
- units are explicit.

### Duplication

- REST pagination overlap is deduplicated;
- trade IDs / sequence IDs are used when available;
- repeated WS snapshots are handled according to source semantics.

### Source lineage

Every normalized record used by TriggerTrade must be traceable to:

- source family ID;
- endpoint/topic;
- acquisition timestamp;
- schema version.

---

## 31. Look-ahead prevention rules

The raw layer must make future leakage difficult by construction.

Examples:

- an open candle cannot be replaced in an event-time backtest with its final high/low/close;
- funding must be associated with the time at which the value was known or settled, depending on the research question;
- later order-book deltas cannot reconstruct a state that was not available at decision time;
- current instrument metadata must not automatically overwrite historical metadata snapshots used by old simulations;
- daily/24h aggregates must be treated according to their actual publication semantics, not as if they were fixed at the start of the window.

---

# PART VII — WHAT IS EXPLICITLY NOT IN THIS DOCUMENT

## 32. Derived metrics deferred to TT-DATA-002

The following are intentionally **not yet defined**:

### Price / structure

- return / log return;
- candle body/range/wick ratios;
- rolling high/low;
- swing structure;
- breakouts/reclaims/sweeps.

### Volatility

- True Range;
- ATR / ATR%;
- realized volatility;
- volatility percentile;
- compression/expansion.

### Volume / trade flow

- RVOL;
- buy volume / sell volume;
- delta;
- CVD;
- trade-size distributions;
- large-trade classifications.

### Derivatives

- OI delta / OI% / OI velocity;
- funding z-score / percentile;
- premium/basis features;
- positioning divergence.

### Order book

- spread;
- depth;
- imbalance;
- microprice;
- book slope;
- wall/replenishment/sweep logic.

### Liquidations

- liquidation notional;
- liquidation intensity;
- liquidation clusters;
- long-vs-short liquidation imbalance.

These belong to the future **TriggerTrade Derived Metrics Catalog** where formula, source dependency, required granularity, observation horizon, normalization, interpretation, limitations, and candidate methodology role will be defined for every metric.

---

# PART VIII — OPEN DECISIONS

## 33. Decisions still required before implementation freeze

The following are not fixed by this document and must remain explicit design decisions:

1. **Trading universe:** USDT perpetual only, or USDT + USDC linear perpetuals.
2. **Minimum listing age** before a symbol becomes research/live eligible.
3. **Official historical trade source:** exact Bybit archive coverage and reproducibility validation where trade-level backtests are required.
4. **Realtime order-book depth:** L1, L50, L200, L1000, or another explicitly justified live-processing choice.
5. **Realtime buffer policy:** only the transient state needed for calculations/reconnect integrity; not a permanent research archive.
6. **Metadata refresh frequency** for instrument/risk-limit changes.
7. **Storage precision and physical representation** for normalized values — Decimal vs scaled integer.
8. **Gap policy** — when missing API data invalidates an observation or research interval.
9. **Cross-exchange/external data** — deliberately out of scope for this Bybit-only foundation.

These are **architecture parameters to decide**, not trading hypotheses.

---

# PART IX — IMPLEMENTATION HANDOFF CONTRACT

## 34. Minimum data-layer acceptance criteria

When this methodology is later handed to development, the Bybit data layer should not be considered complete until it can demonstrate:

1. Complete paginated discovery of eligible `linear` perpetual instruments.
2. Reliable current instrument metadata and explicit metadata refresh/version semantics where needed.
3. Historical retrieval for all specified Bybit-supported historical datasets.
4. Realtime WebSocket consumption with reconnect handling for sources used by live/paper methodology.
5. Sequence-aware order-book reconstruction **in memory or bounded operational state** when order-book features are enabled.
6. UTC-normalized timestamps while preserving relevant exchange event/publication timestamps.
7. Exact numeric semantics without uncontrolled floating-point rounding.
8. Explicit gap and quality flags.
9. Deduplication and idempotent historical retrieval.
10. Raw-to-normalized lineage.
11. Deterministic schemas with schema versioning.
12. No requirement to retain permanent high-frequency raw market streams solely for future backtesting.

---

## 35. Data provenance requirement for future metrics

Every future derived metric must declare:

```yaml
metric_id: string
raw_dependencies:
  - source_id: string
    fields: [string]
required_native_granularity: string
historical_testability: FULL | LIMITED | NONE
```

A metric without this dependency declaration may not become a required TRS field.

---

# PART X — METHODOLOGY DECISION

## 36. Current decision

```yaml
artifact: TT-DATA-001
status: ACCEPTED_BASELINE
methodology_decision: APPROVE_AS_FOUNDATION_WITH_OPEN_PARAMETERS
trading_edge_claimed: false
trs_status: NOT_APPLICABLE
```

### What is established

- TriggerTrade requires a formal raw-data layer before metric design.
- Bybit exchange-native data and TriggerTrade-derived metrics are separate methodology layers.
- Realtime availability and historical testability are separate properties.
- TriggerTrade deliberately does not require permanent high-frequency market-stream retention for backtesting.
- Realtime order-book/liquidation availability does not by itself qualify those features for the core TriggerTrade trigger methodology. If adequate official history is unavailable, they remain outside the core trigger evidence path.
- Instrument metadata is part of research integrity, not merely an execution implementation detail.
- Every future metric must have explicit raw-data lineage.

### What is not established

- No indicator has yet been selected.
- No timeframe hierarchy has yet been selected for trading decisions.
- No market regime has yet been defined.
- No setup or trigger has yet been defined.
- No hypothesis has been promoted to `RESEARCH_CANDIDATE`.
- No trading edge is claimed.

---

# Appendix A — Canonical Bybit documentation references

Verified 2026-09-09.

- Server Time — https://bybit-exchange.github.io/docs/v5/market/time
- Instruments Info — https://bybit-exchange.github.io/docs/v5/market/instrument
- Risk Limit — https://bybit-exchange.github.io/docs/v5/market/risk-limit
- Tickers — https://bybit-exchange.github.io/docs/v5/market/tickers
- Kline — https://bybit-exchange.github.io/docs/v5/market/kline
- Mark Price Kline — https://bybit-exchange.github.io/docs/v5/market/mark-kline
- Index Price Kline — https://bybit-exchange.github.io/docs/v5/market/index-kline
- Premium Index Price Kline — https://bybit-exchange.github.io/docs/v5/market/premium-index-kline
- Recent Public Trades — https://bybit-exchange.github.io/docs/v5/market/recent-trade
- Open Interest — https://bybit-exchange.github.io/docs/v5/market/open-interest
- Funding Rate History — https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- Long/Short Account Ratio — https://bybit-exchange.github.io/docs/v5/market/long-short-ratio
- REST Orderbook — https://bybit-exchange.github.io/docs/v5/market/orderbook
- WS Public Trades — https://bybit-exchange.github.io/docs/v5/websocket/public/trade
- WS Orderbook — https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
- WS Ticker — https://bybit-exchange.github.io/docs/v5/websocket/public/ticker
- WS Kline — https://bybit-exchange.github.io/docs/v5/websocket/public/kline
- WS All Liquidation — https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- REST ADL Alert — https://bybit-exchange.github.io/docs/v5/market/adl-alert
- WS ADL Alert — https://bybit-exchange.github.io/docs/v5/websocket/public/adl-alert

---

# Appendix B — Next canonical artifact

Recommended next methodology document:

```text
TT-DATA-002 — TriggerTrade Derived Metrics Catalog
```

For every candidate metric it should define:

```yaml
id
name
family
raw_dependencies
formula
units
native_input_granularity
candidate_observation_horizons
normalization
market_information_content
possible_interpretation
what_it_does_not_prove
interactions_to_research
historical_testability
known_biases_and_limitations
candidate_methodology_role
parameter_status
```

That document should be built only after the raw-data boundary in TT-DATA-001 is accepted or revised.
