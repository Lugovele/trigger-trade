# TriggerTrade — Market Data Request API Contract

**Boundary:** `Set ↔ API`  
**Contract version:** `3`  

## 1. Authority and version

Set chooses analytical windows, as-of cutoffs, datasets and candle timeframes/counts. API is only a factual transport/normalization interface; it does not choose a market regime, trigger, history window, reference or fallback. v3 replaces the ungoverned dataset list with explicit per-dataset `selections`. No new API/business edge is added. Historical v2 clients must not be silently interpreted as v3.

## 2. Stable selection and request identity

Set persists each selection before dispatch. selection_id identifies one immutable symbol/dataset/mode/as_of/range/timeframe/count/completed-only/page-size tuple; cursor is the only page-request variant. The canonical selection digest is SHA256 of sorted-key compact UTF-8 JSON containing symbol and all selector fields except cursor. IDs, defaults and nulls are explicit. A request_id identifies the exact persisted technical page request; retry after timeout/restart uses identical bytes. Advancing a cursor uses a new request_id but the same selection_id/digest and fixed source snapshot.

Each requested selection must have exactly one result in that response; no duplicate or unrelated selection/dataset is permitted. The same dataset may be requested in more than one distinct interval/timeframe under different selection IDs. `decision_cycle_id` and `set_result_id` are present for an existing PENDING_ORDER_MONITORING cycle and absent/null for new analysis before those existing-cycle identities are applicable. No Frozen Condition is transmitted.

## 3. Time, ranges and dataset selectors

All selection timestamps are canonical UTC `Z` RFC3339, with at most six fractional digits and no trailing fractional zeros. as_of is the fixed economic evaluation cutoff, not requested_at/response receipt time. range_from is inclusive and range_to is exclusive; require range_from < range_to <= as_of.

Analytical selection precedes serialization. For ordinary normalization, Set selects the fixed UTC completed-calendar-day window defined in [Set methodology, Part II §6](../methodology/SET.md#6-canonical-normalization-baseline), then expresses its exact boundaries as UTC `Z` timestamps here. If `D` is UTC midnight starting the day containing `as_of`, the 30-completed-UTC-calendar-day lookback is `[D - 30 UTC calendar days, D)`; the 14-completed-UTC-calendar-day minimum warmup uses the same calendar. The current incomplete UTC day is excluded. UTC is fixed, not a configurable analytical timezone; neither local/account/Portfolio/exchange calendars nor a trailing-hours window may replace this ordinary population.

Other explicitly governed metric-specific calendar/bucket selectors retain their own analytical rules; Set expresses the resulting exact boundaries in UTC. API does not select or infer an analytical timezone/window. UTC timestamp serialization alone does not define the population, and this clarification adds no selector field or wire-shape change.

RAW_TRADES, QUOTE_TURNOVER and KLINES use INTERVAL mode. Raw trades select event timestamps in [range_from,range_to); quote turnover selects complete factual buckets wholly contained in that interval. KLINES select closed intervals wholly contained in it, with exact timeframe and completed_only=true. Normalized candle close_time denotes the exclusive interval end; adapters document any native millisecond-end normalization. count, when provided for KLINES, selects the latest requested number among the complete interval's correctly ordered candles. Insufficient count is incomplete, not a shorter available window. Non-KLINES interval selectors carry null timeframe/count. Missing history cannot be replaced by a shifted interval.

TICKER, BEST_BID_ASK, VOLUME, OPEN_INTEREST, FUNDING_RATE and INSTRUMENT_METADATA use AS_OF mode with null range/timeframe/count. The adapter must return a factual point snapshot effective at or before the requested cutoff, with exact source as_of/provenance. If historical point facts for that cutoff are unsupported or cannot be established, return UNAVAILABLE; never substitute the current snapshot. No more recent source fact is permitted. This is factual selection, not a local marketability gate.

## 4. Payloads and explicit availability

Each result echoes its complete selector (including cursor), selection_digest, stable page_id/page_index and source_snapshot_id. Its payload contains exactly the selected dataset key, with factual data, source_endpoint, source as_of and AVAILABLE/PARTIAL/UNAVAILABLE status. Data shapes retain the existing raw facts (candles, trade IDs/sides/turnover, quotes, instruments); no API indicator or Set trading logic is introduced.

UNAVAILABLE requires null data and an explicit reason; it cannot assert complete/final source coverage. PARTIAL carries the available subset and missing ranges/reason as applicable. Missing selected data remains unavailable to the affected Set computation; availability of another selection cannot satisfy it. Response wall-clock snapshot timestamps are provenance, not evidence that all selected datasets form one atomic market snapshot.

## 5. Pagination, completeness and deterministic assembly

Coverage is separate for every selection/page: covered_ranges, missing_ranges, coverage_complete, pagination_complete, next_cursor, expected_page_ids, source_finality_confirmed and reason_code. Ranges are non-overlapping and within the requested interval; covered and missing ranges cannot overlap. Complete INTERVAL coverage means their exact union covers the requested interval, with no missing interval. AS_OF completeness means the selected point snapshot is factually available and final at the cutoff; its range arrays are empty.

A one-page AVAILABLE result must be complete, source-final, pagination-complete, with next_cursor=null and its own single page ID as the complete manifest. Paginated payload pages remain PARTIAL; a final page may certify full query coverage/finality and enumerate the complete ordered page-ID set even though earlier pages have not reached Set. `pagination_complete` means no more API page exists, not that every page has been delivered. Nonfinal pages have a next_cursor; final pages have none. A source lacking stable pagination/finality must remain PARTIAL/UNAVAILABLE rather than claim completion.

Set durably reassembles a single selector/digest/source snapshot. Require all and only manifest page IDs, unique contiguous page indices, the initial null cursor and exact next-cursor chain, and the final source certificate. Do not infer that the first allocation/page completes the dataset. Identical duplicate pages are no-ops; changed same page ID, mixed snapshots, incompatible selector reuse or equal native record ID with differing content is an integrity/reconciliation condition. Record de-duplication uses native ID (or the dataset's canonical factual interval identity), never callback order. Return assembled AVAILABLE only after complete coverage and count checks pass. Restart reuses the persisted selector/pages/cursors; no automatic shift to a newer as_of.

Exact boundary behavior: a trade at range_from is included, one at range_to is excluded; a completed candle/bucket whose exclusive end equals range_to is included. A still-forming candle or any record after as_of is invalid. A complete source certificate contradicted by later source evidence causes reconciliation, not silent rewriting of a frozen matched handoff.

## 6. Producer/consumer validation

Strict schema rejects unknown history selectors and unsupported v2 shapes. Acceptance tests derived from this contract must cover selector identity, time bounds, dataset/cardinality, snapshot/page provenance, coverage, assembly, raw-trade history, completed turnover buckets, fixed-as-of candles, partial/multipage delivery, reverse page arrival, restart and boundary inclusion/exclusion. Native endpoint completeness remains a runtime conformance gate.

## 7. Strict governed payload shapes

### MARKET_DATA_REQUEST.request

```yaml
market_data_request:
  contract_version: 3
  request_id: string
  requested_at: RFC3339-timestamp
  symbol: string
  purpose: INITIAL_ANALYSIS | PENDING_ORDER_MONITORING
  decision_cycle_id:
    nullable: string
  set_result_id:
    nullable: string
  selections:
  - selection_id: string
    dataset: TICKER | BEST_BID_ASK | KLINES | VOLUME | OPEN_INTEREST | FUNDING_RATE
      | RAW_TRADES | QUOTE_TURNOVER | INSTRUMENT_METADATA
    mode: INTERVAL | AS_OF
    as_of: RFC3339-timestamp
    range_from:
      nullable: RFC3339-timestamp
    range_to:
      nullable: RFC3339-timestamp
    bounds: FROM_INCLUSIVE_TO_EXCLUSIVE
    completed_only: boolean
    timeframe:
      nullable: string
    count:
      nullable: nonnegative-integer
    cursor:
      nullable: string
    page_size: nonnegative-integer
```

### MARKET_DATA_REQUEST.response

```yaml
market_data_response:
  contract_version: 3
  request_id: string
  response_id: string
  symbol: string
  snapshot_started_at: RFC3339-timestamp
  snapshot_completed_at: RFC3339-timestamp
  as_of: RFC3339-timestamp
  source: exchange_api
  selection_results:
  - selection:
      selection_id: string
      dataset: TICKER | BEST_BID_ASK | KLINES | VOLUME | OPEN_INTEREST | FUNDING_RATE
        | RAW_TRADES | QUOTE_TURNOVER | INSTRUMENT_METADATA
      mode: INTERVAL | AS_OF
      as_of: RFC3339-timestamp
      range_from:
        nullable: RFC3339-timestamp
      range_to:
        nullable: RFC3339-timestamp
      bounds: FROM_INCLUSIVE_TO_EXCLUSIVE
      completed_only: boolean
      timeframe:
        nullable: string
      count:
        nullable: nonnegative-integer
      cursor:
        nullable: string
      page_size: nonnegative-integer
    selection_digest: string
    page_id: string
    page_index: nonnegative-integer
    source_snapshot_id: string
    payload:
      TICKER:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            last_price: decimal-string
            mark_price: decimal-string
            index_price: decimal-string
      BEST_BID_ASK:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            bid: decimal-string
            ask: decimal-string
      KLINES:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
          - timeframe: string
            candles:
            - open_time: RFC3339-timestamp
              open: decimal-string
              high: decimal-string
              low: decimal-string
              close: decimal-string
              volume: decimal-string
              close_time: RFC3339-timestamp
              is_closed: boolean
      VOLUME:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            value: decimal-string
      OPEN_INTEREST:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            value: decimal-string
      FUNDING_RATE:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            value: decimal-string
      RAW_TRADES:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
          - trade_id: string
            occurred_at: RFC3339-timestamp
            taker_side: BUY | SELL
            price: decimal-string
            quantity_base: decimal-string
            notional_quote: decimal-string
      QUOTE_TURNOVER:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
          - interval_start: RFC3339-timestamp
            interval_end: RFC3339-timestamp
            turnover_quote: decimal-string
        unit: USDT
      INSTRUMENT_METADATA:
        status: AVAILABLE | UNAVAILABLE | PARTIAL
        as_of: RFC3339-timestamp
        source_endpoint: string
        data:
          nullable:
            tick_size: decimal-string
            qty_step: decimal-string
            min_order_qty: decimal-string
            min_notional: decimal-string
            max_leverage: decimal-string
            contract_type: LINEAR_USDT_PERPETUAL
            metadata_revision: string
    coverage:
      covered_ranges:
      - from: RFC3339-timestamp
        to: RFC3339-timestamp
      missing_ranges:
      - from: RFC3339-timestamp
        to: RFC3339-timestamp
      coverage_complete: boolean
      pagination_complete: boolean
      next_cursor:
        nullable: string
      expected_page_ids:
      - string
      source_finality_confirmed: boolean
      reason_code:
        nullable: string
```

## Consumer assembly consistency (wire version unchanged)

The existing fixed selection/snapshot/page identities are immutable. For one request/selection/source snapshot, two incompatible complete page manifests are a source-proof conflict, not an optional alternate assembly. A changed immutable record under the same native trade/candle/turnover identity is also a conflict. Set must invalidate the current assembled eligibility immediately when relevant supporting evidence changes, then reconstruct from a consistent accepted proof or remain RECONCILING. Presence of a cached `assembled` entry is never sufficient for AVAILABLE.

The durable assembly proof identifies supporting request(s), immutable selector, source snapshot, manifest, exact page IDs/content digests and completeness/finality certificate, plus record content identities. The wire has no mutable page-revision replacement protocol: same page identity must have identical content; older identical replay is idempotent. Preserve prior frozen handoffs/evidence unchanged while blocking new use of contradicted history. These rules neither change Set's analytical-window ownership nor give API analytical discretion; see SYSTEM_PROTOCOLS S04/P16.


## V05 known-identity validation failure — no wire change

Contract version remains 3. SYSTEM_PROTOCOLS.md V05 requires the Set-side ingestion path to retain challenges to accepted immutable request/selection/page/source evidence even when this response fails semantic validity. A known page that contradicts source_finality_confirmed, completeness, final-page membership, snapshot identity or immutable record content invalidates current derived eligibility; it does not overwrite accepted facts or previously frozen handoffs. Unrelated malformed input can be rejected without invalidating an unrelated accepted selection. No range selection, indicator, schema field or page revision is added.


## W02 — Accepted ownership on rejected responses

Wire version and shape remain unchanged. Before relying on incoming selection_id or rejecting its echo, resolve retained request/page ownership or the scoped snapshot/dataset/native-source relationship. A common page name alone is insufficient. Changed selection/request ownership under accepted evidence is journaled with the raw response and semantic error, even if normal validation rejects it. Invalidate the ORIGINAL current assembly atomically; do not rebind pages or revise old frozen handoffs. New handoffs remain blocked across replay/restart; unrelated malformed input stays ordinary rejection. See SYSTEM_PROTOCOLS.md W02 for exact ownership scope and no-implicit-recovery rule.


## X02 accepted graph before dual echo rejection

Version 3 and all request/response shapes remain unchanged. Contradiction preflight must not require either incoming selection_id or page_id to match accepted storage. Resolve exact accepted request/selection-digest and scoped snapshot/native-record relationships across accepted pages first (SYSTEM_PROTOCOLS X02). Journal known challenges and semantic errors durably before rejecting malformed echoes. Preserve accepted original pages and frozen handoffs, block new handoffs, and never infer ownership from unscoped numeric IDs or superficial similarity. Existing evidence replay alone does not clear the block.
