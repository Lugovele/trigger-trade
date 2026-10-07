# Research V2 Pre-Flight Corrections

Status: **IMPLEMENTATION_PROVENANCE**. This is not a trading specification.

- Future-state leak issue: decisions could observe future portfolio reservations/releases.
- Daily-loss null issue: unavailable daily-loss facts were mislabeled as `DAILY_LOSS_LIMIT_REACHED`.
- Funding censor issue: filled paths crossing funding boundaries censored without historical funding facts.

## Latest Implementation Report Context

- causal event-time model corrected
- R014 witness PASS
- future reserve/release invisible
- daily loss unavailable semantics corrected
- funding facts path added
- V2_PREFLIGHT_READY = YES
- J0_J7_READY = YES
