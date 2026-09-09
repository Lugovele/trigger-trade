# Agent Handoff Contract

Every agent receives a structured artifact and returns an updated artifact plus a handoff note.

## Input requirements

Each handoff must include:

- TRS id and version;
- current status;
- source hypothesis or observation;
- prior agent findings;
- unresolved questions;
- evidence available;
- fields that are explicitly unknown.

## Output requirements

Each agent must return:

1. `assessment` — its domain-specific conclusion;
2. `changes_to_trs` — fields added, removed, or changed;
3. `assumptions` — explicit assumptions introduced;
4. `parameters_to_test` — all non-validated thresholds;
5. `risks` — weaknesses discovered;
6. `blocking_questions` — only questions that prevent the next stage;
7. `handoff_decision` — `PASS`, `REVISE`, or `REJECT`.

## Prohibited behavior

Agents must not:

- overwrite findings from another domain without explaining the conflict;
- promote a rule because it is intuitively attractive;
- invent empirical performance;
- hide missing data behind a confidence score;
- convert an unresolved parameter into a fixed constant without evidence;
- treat correlated positions as independent risk.

## Conflict handling

If two agents disagree materially:

- both positions remain in the TRS review section;
- the disagreement is converted into a testable research question where possible;
- the Senior Intraday Crypto Trader may synthesize the decision only after both arguments are explicit.
