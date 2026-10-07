# Research V2 Execution Profile Map

Status: IMPLEMENTED_FOR_J0_J7_BRIDGE

Research V2 separates Set-owned signal logic from downstream execution
configuration.

`ResearchV2SetResolution` decides whether a signal episode is `MATCHED` and
which direction it owns. `ResearchV2ExecutionProfile` records the immutable
downstream execution configuration for Position, Portfolio, Order Spec, and
BACKTEST lifecycle wiring.

## J0-J7 Mapping

- J0: legacy SET-R-003-V2 with legacy POS001/PR201 behavior, GTC, legacy
  tranche sizing.
- J1: same as J0 except entry TTL is 15 minutes.
- J2: legacy Set selection with V2 common execution profile and G0 stop.
- J3: RET5/RET15 OR signal with V2 common execution profile and G0 stop.
- J4: momentum continuation Set with V2 common execution profile and G0 stop.
- J5: compression breakout Set with V2 common execution profile and G0 stop.
- J6: confirmed reversal Set with V2 common execution profile and G0 stop.
- J7: same Set signal as J4 with G1 stop.

## Fingerprints

Every execution profile has a deterministic `config_fingerprint`.

J4 and J7 intentionally have:

- the same V2 Set identity for identical facts;
- different execution profile fingerprints because the stop family differs.

## Downstream Compatibility

The bridge does not add a V2-only backtester. Execution profiles are immutable
configuration records for mapping V2 jobs into the existing canonical
Position/Portfolio/Order/Lifecycle path.

The versioned downstream execution contract is documented in
`RESEARCH_V2_CANONICAL_EXECUTION_EXTENSION.md`. For J2-J7 the bridge maps the
profile into `ORDER_SPEC` contract version 6 so TTL, pending-inclusive
portfolio caps, V2 risk sizing, G0/G1 stop construction, and TP net-floor
evidence are enforced by canonical downstream components. Legacy J0 remains on
the unchanged v5/GTC path; J1 uses the same legacy profile with the TTL-capable
validity extension.
