# TriggerTrade Research V2

Status: **J0_J7_IMPLEMENTED_NOT_RUN**.

Research V2 is a proposed research specification package for evaluating whether TriggerTrade can reach an economic target of **20-30% net per 30D** on **1000 USDT** starting capital, using **7D screening first**, **30D confirmation for promising candidates**, and **no 90D work at this stage**.

## Status Terms

- Specification: source-faithful proposed research definitions in this package.
- Implementation: backend code capable of running those definitions. Not provided by this package.
- Backtest result: realized output from a run. No J0-J7 backtests were run by this package.
- Production approval: permission to change live/frozen trading behavior. Not granted here.

## Package Layout

- Common profile: `RESEARCH_V2_COMMON_PROFILE.json` and `.md`.
- Hypotheses: `hypotheses/V2-01` through `hypotheses/V2-12`.
- Initial jobs: `jobs/J0` through `jobs/J7`, plus `jobs/INITIAL_7D_JOBS.json`.
- Screening gates and metrics: `screening/`.
- Provenance and ambiguities: `provenance/`.
- Canonical package index: `RESEARCH_V2_MANIFEST.json`.

## Implementation Status

- Specification materialized: **YES**.
- Shared Research V2 primitives implemented: **YES**, in `src/triggertrade/research_v2.py`.
- J0-J7 executable job configurations implemented: **YES**, loadable from the repository specs.
- Implementation mappings resolved: **YES**, see `implementation/RESEARCH_V2_IMPLEMENTATION_MAP.md` and `.json`.
- Economic runs: **NOT_STARTED**.
- Production approval: **NO**.

## Explicit Boundary

This package does not change frozen trading methodology, production configuration, formulas, or live behavior. The implementation adds repository-native Research V2 primitives and job definitions only; no J0-J7 7D backtest has been run by this package.
