# Canonical monetary and economic arithmetic — TT_NUMERIC_V1

**Policy version:** `TT_NUMERIC_V1`  
**Package revision:** `v1.2.14` — stable policy ID remains `TT_NUMERIC_V1`.

This policy determines numeric values before serialization. It is normative for Portfolio and Position capital/economics, Lifecycle non-funding accounting and duplicated constructed values. It does not change a formula, threshold, signal, price-selection rule, leverage-selection rule or venue quantity grid. Existing funding allocation is explicitly separate. All producers and consumers persist the policy version with the governed grant, spec, construction confirmation, authorization, cumulative logical Order Event and financial result.

## 1. Arithmetic model and operation order

Input decimal strings are parsed exactly into signed arbitrary-precision integers with decimal scale. Add/subtract/multiply are exact. Division and expressions involving division retain an exact rational numerator/positive denominator, reduced or unreduced; integer cross multiplication is an equivalent implementation. **No finite-precision intermediate rounding is permitted.** Thus intermediate precision/scale is unbounded/exact, rather than an unspecified Decimal context or implicit decimal-18 rule. A rational need not be serialized as an intermediate wire value. Binary floats, nonfinite numbers, exponent-encoded canonical decimals and epsilon comparisons are forbidden.

Execute the existing formula's parentheses and dependency graph exactly, then apply only its output-class quantizer. Do not round each operand, a per-unit ratio, or a fee estimate before recombining it. Evaluating a rational expression with a limited local Decimal context is not equivalent. Storage/resource limits may reject an unrepresentable input explicitly; they cannot silently round it into a different trade.

Let `floor_q(x) = q × floor(x/q)`, `ceil_q(x) = q × ceil(x/q)`, and `trunc_q(x) = q × trunc_toward_zero(x/q)`. They operate on exact rational values, including signed values.

## 2. Output classes

| Class | Quantum / scale | Direction and use |
|---|---|---|
| Own-capital allocation, spendable capacity, requested grant | `Qcapital = 0.000000000001` (12 decimal places) | Grants and spendable capacities: floor at the final boundary. Persisted grants are exact multiples of Qcapital. No upward-created spendable capital. |
| Own-capital liability / actual committed capital | Qcapital | Ceiling of the exact nonnegative capital requirement. This tiny conservative retained amount is a liability, never new spendable capital. |
| SUBMISSION_HOLD and authorization held capital | Qcapital | Copy the constructed actual committed capital exactly; do not apply a second FLOOR or CEILING operation. |
| Exact notional and finite monetary products/sums | Exact finite decimal; input-derived scale | No rounding: quantity × price, target capital × leverage, planned fee notional × decimal fee rate, gross P&L and sums of normalized costs retain all exact finite digits. Product scale is the sum of input scales; sum scale is the maximum constituent scale. No fixed monetary display scale is substituted into accounting. |
| Execution-linked non-funding cashflow allocation | Authoritative positive `source_amount_quantum` | Exact rational weights; truncate allocations toward zero to that source quantum, then conserve the exact source via the specified residue recipient (P12). Never round the source amount. |
| Ratios / percentages in economic wire/report fields | `Qratio = 0.000000000000000001` (18 decimal places) | Floor the exact rational for serialization only. All gate decisions use the exact pre-report value. This report quantum does not govern money, source cashflows or funding. |
| Price and quantity | Existing instrument tick/quantity step | Existing direction-specific Entry/SL/TP rounding and quantity floor remain authoritative. No new rounding mode or price selection. Native factual quantities/prices are preserved exactly; they are not silently repaired. |
| Funding | Existing separate decimal-18 source quantum/algorithm | Existing Lifecycle §32 and P7 algorithm is unchanged. It is not replaced by source-quantum P12 allocation. |

Twelve capital decimals is a versioned internal own-capital allocation grid, not a claim about any native settlement precision. Native wallet cash and source settlements keep their factual precision. Conservative quantization dust remains in the account/coin's unallocated balance; it is not credited as trading P&L or assigned to a tranche without the normal grant flow. Native fees, rebates, funding and costs retain their actual source currency, amount and quantum. Exact native-currency conservation remains mandatory. FINAL aggregation is valid only in the one governed accounting/settlement currency under §2A; required unsupported cross-currency monetary evidence blocks FINAL. This baseline supports no general cross-currency conversion.

## 2A. One governed accounting unit; unsupported currency blocks FINAL

The governed accounting/settlement currency is the explicit currency of the tranche's account/product accounting configuration, common to Portfolio's monetary accounting and Position's monetary construction. At the tranche's first accounting use, Lifecycle inherits and durably retains that already-pinned currency and configuration/profile identity/version/content under P17; it does not select a new accounting profile for an already-started tranche. Restart restores the same binding. It cannot choose a currency from the first received source row, change it to fit later evidence, or resolve it from whichever configuration is current at finalization. A missing, ambiguous or conflicting governed-currency binding leaves finality unresolved. This binding does not change the independent accounting-day policy or require a new wire object.

Every required monetary source/component participating in a logical tranche FINAL result must already be denominated in that governed currency: actual trading fees and rebates, funding, supported other realized costs, attributable credits/debits and the execution-derived gross result. The existing `financial_result.currency` identifies this same unit; it does not relabel its inputs. Monetary additions/subtractions and the P7 net-result formula are performed only after semantic validation of that common unit for all required sources and their allocations.

A required source in a different currency is retained with its exact native amount/currency/quantum, identity, aliases, provenance, coverage and attribution. It must not be omitted, zeroed, labeled NOT_APPLICABLE because it is unsupported, netted away with another unsupported amount, added as a bare scalar to another currency, relabeled, or converted using inferred FX, current market price, execution price or an arbitrarily selected source. The current baseline has no supported cross-currency valuation profile. While any required source fails the currency rule, the affected financial component and parent result remain reconciliation/finality-blocked; no FINAL logical result or consequent capital/slot release is permitted, even when all source coverage is COMPLETE and exposure is zero.

Source-level allocation remains native-currency accounting, not currency conversion. P12 retains its existing exact signed source-quantum allocation/conservation and residue rules; the native source identity supplies the currency of every attributed amount. P7/Lifecycle §32 retain the separate existing funding algorithm and settlement-currency quantum. A completed source allocation, COMPLETE coverage or numeric zero does not waive currency admissibility for FINAL. All source-sign rules, exact arithmetic, rounding, quantization and allocation ordering/formulas remain unchanged.

A supported venue/account/product may establish at native-profile/runtime conformance that its required monetary sources are already in the governed currency. That expectation does not override contrary factual evidence: retain the contrary source and block finality under P7. Structural acceptance of an arbitrary `financial_record.currency` string is intentional factual transport, not permission for FINAL aggregation. The semantic validator/finality transaction enforces the currency rule in addition to JSON Schema.

Future cross-currency support requires a separately governed specification defining at least supported source currencies, target accounting currency, authoritative valuation source, valuation timestamp/effective-time rule, conversion direction, exact arithmetic, rounding/quantization, allocation-versus-conversion order, valuation provenance, version/configuration binding, replay/restart behavior and finality requirements. This paragraph grants no present conversion authority and partially implementing that future subsystem is not supported.

## 3. Portfolio grant and atomic capacity gates

Compute the existing free-capital and limit expressions with exact inputs first. Spendable capacity `Cfree = floor_Qcapital(exact_free_capital)`. For positive remaining slots `S`, the requested grant is `floor_Qcapital(Cfree / S)`. The division residue stays in free capital; it is not distributed to an arbitrary final grant. Zero slots, nonpositive resulting grant, missing inputs or negative capacity do not create a trade.

A grant is still **not** a reservation. Concurrent grants do not change available capital. The existing final Portfolio transaction recomputes the actual current available amount and atomically compares the proposed hold, other holds/commitments, exact configured limits and slot counts. Equality passes an inclusive capacity limit; values above it fail, with no tolerance. Floors applied to spendable capacities can only make this gate more conservative. Duplicate authorization/grant identity cannot add another hold.

`751.10 / 3` yields grant `250.366666666666`. If three independently constructed actual commitments equal those grants, their holds total `751.099999999998`, leaving `0.000000000002` unallocated. They cannot each round upward. A fourth hold still needs both a slot and actual current capital; a stale capacity snapshot grants no authority.

## 4. Position final construction and proof of no overcommit

Retain the existing sequence: exact target notional = grant × selected leverage; exact raw quantity = target / the already-selected planned entry reference; quantity is floored to the existing quantity step; actual notional = exact final quantity × exact immutable Entry. The existing formula `actual_committed_capital = actual_order_notional / leverage` defines its mathematical value. Its **persisted monetary output** is `ceil_Qcapital` of that value. The Position-owned final construction calculation takes the already-selected final Entry; it does not select or modify the planned entry reference or any price rule.

After all existing construction gates, independently require both exact capital requirement ≤ granted capital and quantized committed capital ≤ granted capital. A grant is quantum-aligned, so ceiling a value not exceeding it cannot exceed that grant. A violation fails construction; do not clamp, resize, reprice, or create a replacement grant. Quantity zero remains an existing unsuccessful construction, not a submit candidate.

`actual_order_notional = 202`, leverage `3` gives exact requirement `202/3`; persisted liability is `67.333333333334`. With grant `67.34`, unused capacity is exactly `0.006666666666`; it is never held. The hold is the persisted liability `67.333333333334`, not the grant. Rounding the liability down would create a small amount of incorrectly spendable capital; therefore liability and grant rounding are intentionally different.

Initial gross-R:R and post-grant net-edge gates evaluate the existing exact ratios against exact configured thresholds; reporting precision never turns a FAIL into a PASS. The successful Order Spec, construction confirmation and authorization must carry the same policy version and canonical constructed values.

## 5. Pre-close partial-entry apportionment and residue owner

Let `A` be the approved, quantum-aligned actual capital; `Q` the approved quantity; `F` cumulative entry-filled quantity; `R` the still-authorized entry remainder. Validate `Q > 0`, `0 ≤ F`, `0 ≤ R`, `F + R ≤ Q`. The exact `approved_capital_per_unit = A/Q` is an internal rational, not a separately rounded multiplier.

Before any close acquire:

```text
retained_entry_total = ceil_Qcapital(A × (F + R) / Q)
if R > 0:
    filled_committed_capital = floor_Qcapital(A × F / Q)
    remaining_reserved_capital = retained_entry_total - filled_committed_capital
else:
    filled_committed_capital = retained_entry_total
    remaining_reserved_capital = 0
released_unfilled_capital = A - retained_entry_total
```

All apportionment residue belongs to the reserved remainder while that remainder exists, otherwise to the retained filled commitment. With `A=1, Q=3, F=1, R=2`, filled=`0.333333333333`, reserved=`0.666666666667`, total=`1`. Terminally cancelling the remainder retains ceiling of the filled exact liability, not a rounded-down per-unit result. These rules cannot be reused to proportionally release capital during a close: existing P6 freezes the full then-committed amount and slot until canonical CLOSED.

## 6. Canonical serialization and replay

After numeric value selection: decimal point only where needed; no exponent, leading plus, redundant leading integer zeros or trailing fractional zeros; negative zero becomes `0`. Hence `751.10` as factual input normalizes to canonical constructed `751.1`. Native raw values remain verbatim in provenance, never altered for a digest. Values that remain nonterminating must first use their defined output quantizer; serializing an arbitrary context approximation is invalid.

Repeated evaluation and deserialize/recompute/serialize must be byte-equivalent for canonical values. Object digest rules remain sorted keys, compact UTF-8 JSON, no NaN/ASCII escaping; the complete immutable spec envelope including versions is covered. Display formatting cannot be fed back into a gate, grant or spec.

Acceptance tests derived from this policy must independently cover integer/rational arithmetic, boundary quantization and residue behavior. Such specification tests do not establish database decimal-column sizing or native precision conformance.

## 7. Exact hold and separate Set arithmetic

SUBMISSION_HOLD copies the already canonical CEILING-quantized actual liability. It is not independently floored as a fresh grant. Confirmation, spec, held amount and authorization compare exactly. `actual_committed_capital > grant` fails without hold; the positive grant-minus-actual difference stays unallocated, never reserved and later released.

Set-derived calculations use the separate `TT_SET_NUMERIC_V1` contract in `SET_NUMERIC_POLICY.md`. Monetary rational rules do not implicitly choose indicator seeds, square roots or a handoff approximation. The money/funding algorithms above are unchanged.
