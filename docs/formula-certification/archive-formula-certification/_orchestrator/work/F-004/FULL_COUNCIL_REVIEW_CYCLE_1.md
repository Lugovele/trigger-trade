# F-004 Full Council Review Cycle 1

```text
formula_id: F-004
review_mode: FULL_REVIEW / DISCOVERY
assessment_method: all eight perspectives applied by one Council agent
full_council_approved: NO
another_review_cycle_required: YES
disposition: CHANGES_REQUIRED
candidate_status: COUNCIL_DEFINED_ARITHMETIC_SUBSET_ONLY
blocking_findings: F004-C02, F004-C03
```

## Council Decision

The Council rejected full F-004 certification in Cycle 1. The arithmetic supports a narrow `COUNCIL_DEFINED` candidate, but complete reference-population rules and the local 5-minute ATR dependency require closure.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | CHANGES_REQUIRED | The composite is conceptually usable as directional evidence. The extracted gate set omitted directional efficiency, and unresolved population rules can change eligibility. Centered momentum measures deviation from its historical mean; a positive return can produce negative momentum evidence. |
| Market Microstructure & Order Flow Researcher | CHANGES_REQUIRED | The active methodology defines 5-minute aggressive flow using buyer/seller-initiated quote notional, distinct from F-002 base volume. Activity and flow measure participation, not executable liquidity or authentic buying interest. Reference eligibility must be deterministic. |
| Market Regime & Context Analyst | CHANGES_REQUIRED | Completed-day normalization and volatility percentiles provide context, but the 14-29 day population ambiguity prevents reproducible comparisons during warmup. Percentile thresholds are product calibration, not established regime-quality boundaries. |
| Quant Strategy Researcher | CHANGES_REQUIRED | Population variance, correctly rounded square root, clipping and the fixed weighted sum are coherent. Exact population membership remains incomplete. The score must use exact products of canonical factor values, not independently rounded audit contributions. |
| Risk & Trade Management Architect | CHANGES_REQUIRED | Missing evidence must prevent eligible downstream classification. A calculable five-factor score cannot compensate for an unavailable required local-momentum veto. Missing factors cannot become zero or trigger weight redistribution. |
| Execution & Exchange Mechanics Specialist | CHANGES_REQUIRED | Set working precision and downstream wire precision remain distinct. F-003 certifies the 15-minute volatility instance; it cannot silently cover the required 5-minute instance. |
| Adversarial Strategy Reviewer | CHANGES_REQUIRED | Material cases include warmup subsets, missing historical observations, rounded-zero standard deviation, zero volatility denominators, midnight population membership and contribution-rounding differences. |
| Performance & Strategy Diagnostics Analyst | CHANGES_REQUIRED | Diagnostics must distinguish missing data, failed gates, side-specific vetoes and the downstream score dead zone. Predictive calibration and net benefit remain unestablished. |

## Findings

| ID | Classification | Disposition |
|---|---|---|
| F004-C01 | SPECIFICATION_DEFECT | Resolved through discovery for Council record. The final candidate must include `DE < 0.30` as a hard gate, `DE_STRENGTH = clip((DE - 0.30) / 0.40, 0, 1)`, completed-5-minute evaluation, `ALTCOIN_VS_BTC` scope and the eleven required inputs in SET Part II §35. |
| F004-C02 | SPECIFICATION_DEFECT | Blocking. `[D - 30 days, D)` and minimum 14 completed days do not fully specify the usable population when only 14-29 days exist. Define permissible initial history, eligible-day selection, treatment of unavailable historical derived values, and proven absence versus missing requested data. Apply equivalent explicit rules to same-clock turnover references. |
| F004-C03 | DEPENDENCY_GAP | Blocking. SET §16.2 requires 5-minute ATR_PCT/Wilder(14) for the local VNM veto. F-003 certifies 15-minute ATR only. Close through a revised F-004 candidate or separate approved dependency; do not inherit certification by changing timeframe. |
| F004-C04 | PRODUCT_DECISION | Resolved. F-004 owns numerical analytics and gate/veto diagnostics; F-005 owns final direction and directional handoff. Extracted weights and thresholds are pinned methodology parameters, not empirically optimized values. |
| F004-C05 | SPECIFICATION_DEFECT | Resolved arithmetic interpretation. SET §32 writes score as a sum of products. Under numeric policy §2, products remain exact until the score's Q36 output. Independently rounded weighted-contribution diagnostics must not become substitute score operands. |
| F004-C06 | EMPIRICAL_QUESTION | Non-blocking for a complete mathematical specification. Gate calibration, weights, factor redundancy, centered-sign usefulness, symbol/side asymmetry and performance after costs remain unestablished. |
| F004-C07 | NON_BLOCKING_LIMITATION | The score is a heuristic mixture of structure, historical anomalies and signed flow. It is neither probability nor expected return, liquidity, trade quality or a complete risk model. Corrected-history acceptance/reconciliation release remains externally unresolved. |

## Boundary Decision

F-004 should produce canonical normalized values, percentiles, effective factors, weighted-contribution diagnostics, `DIRECTION_SCORE`, required-data status, hard-gate diagnostics and separate LONG-side and SHORT-side veto predicates. Active hard gates are data availability, directional efficiency, activity and volatility. Missing evidence is distinguishable from a failed numerical gate or inactive veto.

F-005 owns inclusive `+0.35` / `-0.35` classification thresholds, candidate-side selection, applicable veto consumption, `LONG/SHORT/NONE`, primary rejection resolution, directional matching and handoff. No F-004 score or passing gate independently creates a match or authorizes execution.

## Dependency Compatibility

| Dependency | Council classification |
|---|---|
| F-001 | Compatible formation evidence, not a mathematical definition of 15-minute momentum. Preserve current completed 1-minute slot freshness and signed diagnostics. Do not substitute its displacement for F-004 returns or VNM. |
| F-002 | Compatible direction-neutral formation evidence. Its 60-minute base-volume median/rank is not time-of-day quote turnover, aggressive flow or F-004 participation strength. |
| F-003 | Compatible for current and historical 15-minute work ATR_PCT with authentic canonical ancestry. Use work values, not 18-place exports. The 5-minute instance remains F004-C03. |
| Directional efficiency and swing states | Sufficient active-methodology definitions. SET §§9-12 define pivot confirmation, ties, one-tick structural comparisons, two-high/two-low requirements, eight-interval efficiency, zero-path result and modifier. |
| Time-of-day turnover and aggressive delta | Supported by SET §§8 and 21-23. Aggressor-side mapping is explicit. Turnover population eligibility remains subject to F004-C02. F-002 cannot supply a substitute. |
| BTC context and weights | Supported by SET §§24-32. This is an altcoin-versus-BTC method; applying it to BTC itself is outside reviewed scope. |

## Council-Defined Arithmetic Candidate

1. Normalization: For supplied canonical reference values `b_1..b_n`, compute exact `mu = sum(b)/n` and `v = sum((b - mu)^2)/n`; use TT_SET_NUMERIC_V1 correctly rounded sqrt. If `n = 0`, inputs are unavailable, or rounded `sigma = 0`, normalization is `UNAVAILABLE`. Otherwise `z = Q36((x - mu) / sigma)` and normalized score `Q36(clip(z / 2, -1, 1))`. Do not round mean or variance separately.
2. Percentile: `K = count(b <= x)` exactly including ties; `P = Q36(100K/n)`. Equal-valued references do not make percentile undefined; a current value equal to all references ranks at `100`. Volatility gate fails below `15` or above `97`; equality passes.
3. Aggregation: Given canonical available factors `(S, M, R, F, B)` in `[-1,1]`, calculate `Q36(0.35S + 0.25M + 0.15R + 0.15F + 0.10B)` with exact products and addition. Missing factors make complete score unavailable; no replacement or renormalization.
4. Diagnostic contributions: Retain each `Q36(w_i f_i)` separately. Their sum need not equal the score at the last working quantum and must not feed F-005 thresholding.

## Evidence Boundary

The Council reviewed the F-004 Source Pack, certified F-001, F-002 and F-003 final specifications, and used the necessary active SET methodology and SET numeric policy excerpts because omitted square-root and factor/veto definitions blocked reliable assessment. No files, tests or trading actions were changed by the Council.
