# Trading Rule Set Contract

A Trading Rule Set (TRS) is the canonical unit of TriggerTrade methodology.

## Required fields

```yaml
id: TRS-XXX
name: string
version: string
status: IDEA | HYPOTHESIS | RESEARCH_CANDIDATE | BACKTESTED | PAPER_VALIDATED | LIVE_CANDIDATE | LIVE_VALIDATED | REJECTED
owner_stage: string

market_mechanism:
  thesis: string
  causal_chain: [string]
  known_failure_modes: [string]

scope:
  instruments: [string]
  market_type: perpetual_futures
  direction: LONG | SHORT | BOTH
  timeframes: [string]

regime:
  allowed: [string]
  prohibited: [string]
  unresolved: [string]

context_rules:
  - id: CTX-001
    condition: string
    type: required | optional | prohibited
    parameter_status: FIXED | PARAMETER_TO_TEST

setup:
  description: string
  observable_preconditions: [string]

entry_triggers:
  - id: TRG-001
    condition: string
    timeframe: string
    parameter_status: FIXED | PARAMETER_TO_TEST

invalidation:
  thesis_failure_condition: string

stop_logic:
  rule: string

exit_rules:
  - id: EXT-001
    rule: string

risk_rules:
  risk_per_trade: string
  correlated_exposure_rule: string
  concurrent_position_rule: string
  daily_loss_rule: string
  leverage_rule: string

no_trade_filters:
  - id: NTF-001
    condition: string

execution_assumptions:
  order_type: string
  maker_taker_assumption: string
  slippage_model: string
  funding_model: string
  fill_model: string

required_data:
  - field: string
    granularity: string
    source_requirement: string

research:
  hypothesis: string
  backtest_design: string
  sample_requirements: string
  robustness_tests: [string]
  success_criteria: [string]
  rejection_criteria: [string]

performance:
  expected_frequency: UNKNOWN | string
  expectancy: UNKNOWN | string
  net_rr: UNKNOWN | string
  max_drawdown: UNKNOWN | string

review:
  red_team_findings: [string]
  unresolved_questions: [string]
  decision: PENDING | REVISE | REJECT | APPROVE_FOR_NEXT_STAGE
```

## Contract rules

- Unknown values must remain `UNKNOWN`; agents may not fabricate them.
- Plausible mechanism is not evidence.
- A field marked `PARAMETER_TO_TEST` cannot silently become fixed.
- Every rule must belong to one layer: regime, context, setup, trigger, invalidation, exit, risk, execution, or no-trade.
- Duplicate or overlapping rules must be explicitly identified.
