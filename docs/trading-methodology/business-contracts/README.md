# TriggerTrade — Business Contracts

**Package revision:** `v1.2.15`.

Current governed business boundaries:

| Contract | Version | Boundary |
|---|---:|---|
| COINS | 2 | Portfolio Rules → Set |
| MARKET_HANDOFF | 4 | Set → Position Rules |
| APPROVE_REJECT | 5 | Position Rules → Portfolio Rules |
| CAPITAL_AND_LIMITS | 5 | Portfolio Rules → Position Rules |
| ORDER_SPEC | 5 | Position Rules → Order Lifecycle |
| SUBMIT_AUTHORIZED | 5 | Portfolio Rules → Order Lifecycle |
| ORDER_EVENT | 7 | Order Lifecycle → Portfolio Rules |
| ORDER_PLACED | 3 | Order Lifecycle → Set |
| ORDER_CANCEL_SIGNAL | 2 | Set → Order Lifecycle |

Shared invariants are defined in `../SYSTEM_PROTOCOLS.md`; identifier ownership and timing are defined in `../IDENTIFIER_LINEAGE.md`.
