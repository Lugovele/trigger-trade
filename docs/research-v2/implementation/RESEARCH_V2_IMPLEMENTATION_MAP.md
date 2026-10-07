# Research V2 Implementation Map

Status: **COMPLETE_FOR_J0_J7**.

Scope: this map resolves the implementation ambiguities required to load and
test J0-J7 from `docs/research-v2/`. It does not certify any 7D economic
result, and no J0-J7 backtest has been run.

## Resolved Mappings

| Ambiguity | V2 concept | Repository-native contract | Status | Semantic fit |
| --- | --- | --- | --- | --- |
| AMB-001 | RET5/RET15 signal kernel | `triggertrade.research_v2.ret5_ret15_or_signal` / `V2-SIGNAL-RET5-RET15-OR-V1` | RESOLVED_FOR_J0_J7 | Exact new V2 contract |
| AMB-002 | G0/G1 stop families | `v2_stop_g0`, `v2_stop_g1` | RESOLVED_FOR_J0_J7 | Exact new V2 contract |
| AMB-003 | TTL lifecycle field | `ResearchV2JobConfig.runtime_profile.entry.ttl_minutes` | RESOLVED_FOR_J0_J7_CONFIGURATION | Exact config contract for later execution wiring |
| AMB-004 | Historical mark-price source | `research_v2_data_requirements(...).required_inputs` with DATA_INVALID on missing facts | RESOLVED_FOR_J0_J7_REQUIREMENT_CHECKS | Explicit data requirement |
| AMB-005 | Historical funding source adapter path | Existing Research BACKTEST funding facts path plus V2 `historical_funding_facts` requirement | RESOLVED_FOR_J0_J7_REQUIREMENT_CHECKS | Reuses preflight contract |
| AMB-006 | V2 daily-loss native representation | Existing portfolio-grant daily-loss availability fields plus V2 daily-loss config | RESOLVED_FOR_J0_J7_REQUIREMENT_CHECKS | Reuses preflight contract |
| AMB-007 | Risk-based sizing | `v2_risk_based_sizing` | RESOLVED_FOR_J0_J7 | Exact new V2 contract |
| AMB-008 | Numeric config equivalence | `ResearchV2JobConfig.normalized_config` and `config_fingerprint` | RESOLVED_FOR_J0_J7 | Exact fingerprint contract |

## Notes

- J0 remains a legacy control: `SET-R-003-V2`, legacy geometry/GTC, legacy
  sizing, leverage 1x, and no V2 entry/stop/sizing substitution.
- J1 differs from J0 only by `ttl_minutes=15` and the TTL time-in-force marker.
- J2-J7 use the common V2 profile primitives for entry, stop, TP, risk sizing,
  features, units, and cost/data requirements.
- J4 and J7 share the same continuation signal profile and differ only by stop
  family: G0 versus G1.
- Funding and daily-loss semantics intentionally reuse the corrected preflight
  repository contracts. Missing facts remain explicit and fail closed where the
  existing path requires that behavior.
- Historical mark facts are represented as an explicit requirement for later
  J0-J7 execution; no downloader or economic replay is introduced by this
  implementation task.
