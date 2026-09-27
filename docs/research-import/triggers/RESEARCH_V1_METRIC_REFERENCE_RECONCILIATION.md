# Research V1 Metric Reference Reconciliation

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

The 10 previously blocked Research references are not renamed. They are reconciled to existing Metrics Library formula objects or classified as state/classifier outputs with source evidence.

| RESEARCH_REFERENCE | CURRENT_METRIC_ID | MATCH_TYPE | EVIDENCE | STATUS |
|---|---|---|---|---|
| `AGGRESSIVE_VOLUME_DELTA_PCT` | `F-004` | `DERIVED_FROM_EXISTING` | docs/METRICS_LIBRARY_V1.md documents AGGRESSIVE_VOLUME_DELTA_PCT in F-004 flow normalization; docs/research-v1/.../WEB_RESEARCH_CONFIGURATION_MODEL.md section 3 maps it to methodology/SET.md Part II §§21-23. | `DERIVED_FROM_EXISTING` |
| `ATR percentile` | `F-004 via F-003 input` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 outputs ATR_PCT percentile and depends on F-003 for 15m ATR/ATR_PCT; R3 Web Research Configuration Model section 3 maps ATR percentile to methodology/SET.md Part II §§13-15 and §§3-6. | `DERIVED_FROM_EXISTING` |
| `BTC_CONTEXT_SCORE` | `F-004` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 defines BTC_CONTEXT_SCORE and its BTC structure/momentum components; R3 Web Research Configuration Model section 3 maps it to methodology/SET.md Part II BTC context sections. | `DERIVED_FROM_EXISTING` |
| `DE` | `F-004` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 includes DE 15m as a required normalized input and produces DE_STRENGTH/gate diagnostics; R3 section 3 maps DE to methodology/SET.md Part II §§11-12. | `DERIVED_FROM_EXISTING` |
| `RELATIVE_RETURN_15m` | `F-004` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 defines RELATIVE_RETURN_15m = RETURN(asset,15m) - RETURN(BTC,15m) and relative score/veto diagnostics; R3 section 3 maps it to methodology/SET.md Part II §§19-20 and §§3-6. | `DERIVED_FROM_EXISTING` |
| `RETURN(asset,5m)` | `F-004 local input/output diagnostic` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 local 5m momentum section defines VNM_5m from RETURN_5m / ATR_PCT_decimal_5m; R3 BTC predicates explicitly bind RETURN(asset=BTC,5m) and section 3 maps RETURN(asset,5m) to Set methodology return/context sections. | `DERIVED_FROM_EXISTING` |
| `SWING_SEQUENCE_STATE(asset,1h)` | `F-004 structure input` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 consumes asset structure 1h/15m and structure score; R3 section 3 maps SWING_SEQUENCE_STATE(asset,1h) to methodology/SET.md Part II §§9-10. | `DERIVED_FROM_EXISTING` |
| `TOD_REL_TURNOVER` | `F-004` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 defines TOD_REL_TURNOVER same-clock turnover ratio and participation strength/activity gate; R3 section 3 maps it to methodology/SET.md Part II §8 and §§21-23. | `DERIVED_FROM_EXISTING` |
| `VNM_5m_z` | `F-004 local momentum diagnostic` | `DERIVED_FROM_EXISTING` | Metrics Library F-004 defines VNM_5m/local 5m momentum veto inputs and preserves underlying z-score/availability; R3 section 3 maps VNM_5m_z to methodology/SET.md Part II §§16-18 and numeric policy. | `DERIVED_FROM_EXISTING` |
| `classifier_direction` | `F-005` | `NOT_A_METRIC` | Metrics Library F-005 is the Set Direction Classifier and outputs LONG/SHORT/NONE. R3 section 3 lists classifier_direction as an enum state output, not a separate metrics-library metric object. | `NOT_A_METRIC` |
