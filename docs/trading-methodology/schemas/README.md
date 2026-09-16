# TriggerTrade — Current Schemas and Numeric Policies

`CONTRACT_REGISTRY.json` governs the active business and API contract families.
`wire.schema.json` contains the strict shared wire definitions.
`NUMERIC_POLICY.md` governs monetary/capital arithmetic, including §2A's single-unit FINAL aggregation rule. `financial_record.currency` continues to carry actual native currency; its structurally valid string is not sufficient for FINAL. SYSTEM_PROTOCOLS P7.1 requires semantic validation of each required source/allocation against the tranche's pinned accounting/settlement currency and retains a finality block for unsupported cross-currency amounts. No conversion wire object is defined.
`SET_NUMERIC_POLICY.md` governs deterministic Set indicator computation and handoff serialization.

**Package revision:** `v1.2.15`. Stable policy IDs and the contract-family versions below are independent from the package revision.

Current contract versions:

- COINS 2
- MARKET_HANDOFF 4
- APPROVE_REJECT 5
- CAPITAL_AND_LIMITS 5
- ORDER_SPEC 5
- SUBMIT_AUTHORIZED 5
- ORDER_EVENT 7
- ORDER_PLACED 3
- ORDER_CANCEL_SIGNAL 2
- PORTFOLIO_DATA_REQUEST 5
- MARKET_DATA_REQUEST 3
- ORDER_MANAGEMENT 4
