# TriggerTrade Methodology Lifecycle

## Phase 1 — Observe

Input may be informal:

- market observation;
- trader intuition;
- known market mechanism;
- data anomaly;
- candidate trigger;
- failure observed in an existing rule.

Output: `IDEA`.

## Phase 2 — Explain

The Senior Trader and Microstructure Researcher determine whether there is a plausible market mechanism.

Output: `HYPOTHESIS` or `REJECTED`.

## Phase 3 — Contextualize

The Market Regime Analyst determines where the mechanism should and should not work.

Output: allowed/prohibited regimes and context rules.

## Phase 4 — Formalize

The Quant Researcher converts the hypothesis into measurable definitions and a reproducible research plan.

Output: `RESEARCH_CANDIDATE`.

## Phase 5 — Make tradable

Risk and Execution roles define how the theoretical edge becomes an executable trade.

Output: entry, invalidation, stops, exits, sizing, order mechanics, cost assumptions.

## Phase 6 — Attack

The Adversarial Reviewer attempts to invalidate the candidate.

Output: `REJECT`, `REVISE`, or `APPROVE_FOR_NEXT_STAGE`.

## Phase 7 — Validate

Backtest → robustness → paper → controlled live.

## Phase 8 — Diagnose

Performance Analyst evaluates results by:

- TRS;
- trigger;
- regime;
- coin;
- direction;
- session/time-of-day;
- volatility bucket;
- liquidity bucket;
- fees and slippage;
- MAE/MFE;
- drawdown;
- correlated exposure.

Findings feed back into a new TRS version rather than silently rewriting history.
