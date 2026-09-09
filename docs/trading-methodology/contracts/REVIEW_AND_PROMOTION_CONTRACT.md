# Review and Promotion Contract

Promotion is evidence-gated.

## IDEA → HYPOTHESIS

Requires:

- explicit market mechanism;
- identifiable setup;
- proposed direction and scope;
- no obvious contradiction with market mechanics.

## HYPOTHESIS → RESEARCH_CANDIDATE

Requires:

- measurable variables;
- formal event definition;
- required data identified;
- regime assumptions identified;
- test plan;
- success and rejection criteria.

## RESEARCH_CANDIDATE → BACKTESTED

Requires:

- reproducible backtest;
- fees included;
- slippage assumptions documented;
- funding included where material;
- no look-ahead leakage;
- sufficient sample;
- out-of-sample or walk-forward evidence where feasible;
- robustness checks.

## BACKTESTED → PAPER_VALIDATED

Requires:

- execution logic implementable in real time;
- paper execution under live market conditions;
- observed fill/slippage behavior;
- no material divergence from backtest assumptions.

## PAPER_VALIDATED → LIVE_CANDIDATE

Requires:

- defined risk budget;
- defined kill conditions;
- bounded leverage;
- monitoring metrics;
- incident/review path.

## LIVE_CANDIDATE → LIVE_VALIDATED

Requires:

- statistically meaningful live sample;
- positive net expectancy after costs;
- drawdown within expected bounds;
- no unexplained regime-specific failure;
- no hidden dependence on one coin, period, or exceptional event.

## Rejection

A TRS should be rejected when:

- mechanism is contradicted by evidence;
- edge disappears after realistic costs;
- results are parameter-fragile;
- performance is concentrated in a narrow period or instrument without justification;
- drawdown or tail risk is unacceptable;
- execution assumptions are unrealistic;
- robustness checks fail materially.
