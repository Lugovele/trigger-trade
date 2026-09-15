```yaml
formula_id: F-010
review_mode: REVALIDATION
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
reviewed_candidate: F-010_REVISED_SPEC_CYCLE_2.md
```

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Structural targets and sequential selection are coherent for the declared TP role; profitability remains unproven. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Inward rounding respects the target boundary. Structural levels and ATR do not establish liquidity or fill probability. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Frozen family selection is consistent; stale structure, regime transitions and ATR lag remain limitations. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Inclusive ATR comparisons, total ordering and directional quantizers are mathematically consistent. Calibration remains empirical. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Terminal failures prohibit repair. Entry and stop ownership remain intact; final-price geometry and economics remain downstream. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Positive tick-grid output and inward rounding are correct. Exchange acceptance and execution are outside certification. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Binding validation, capability separation and terminal traversal rules withstand the reviewed edge cases; defensive branches are distinguished below. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Frozen evidence and ordering support primary-result replay. Research must include rejected and unfilled opportunities; persistence implementation remains unverified. |

## Blocker Closure Assessment

| Finding | Disposition | Evidence |
|---|---|---|
| F010-C01 | CLOSED; no regression identified | Producer binding, dangling-ID, availability and duplicate-ID failures precede selection. `PREFERRED` fallback requires contract-valid evidence. Section 5.15 controls primary reasons, including over the general `REQUIRED` eligibility wording in Section 5.5. |
| F010-C02 | CLOSED; no regression identified | Exact availability, exact distance and case-sensitive Unicode code-point ID ordering form a portable total order. Array order and diagnostic ages cannot decide selection. |
| F010-C03 | CLOSED | Capability now derives from the existing frozen collection, with explicit usability checks and separate directional/basic/traversable pools. Reason precedence and primary-result restart equality are specified. |

## Reachability And Fixtures

The capability fixtures are schematic pool examples, not complete F-008-compatible
handoffs. A complete LONG handoff also needs an entry-side reference. Nevertheless,
all three intended capability outcomes are reachable without changing the
specification:

| Common valid setup: LONG, match price `101`, entry-side low `100`, `A=4`, `t=0.25`, F-008 entry `100` | F-010 outcome |
|---|---|
| No permitted high reference | `NO_FAVORABLE_SIDE_GEOMETRY` |
| Add permitted high `100.25` | `NO_ELIGIBLE_REFERENCE` |
| Add permitted high `104` instead | `AVAILABLE`, TP `104` |

Assuming valid identities, availability, configuration and null `NONE` thesis
pairs, exact integer arithmetic confirms these witnesses and their SHORT
counterparts. The supplied rounding fixtures also correctly produce
`TARGET_TOO_CLOSE_AFTER_ROUNDING`.

Every current family hierarchy contains every permitted directional type.
Consequently, `basic_pool != empty` with `traversable_pool == empty` is
unreachable under the pinned tables. That defensive branch introduces no
conflicting reachable result; `NO_REACHABLE_TARGET` remains reachable through
all-too-close exhaustion.

## Dependency Compatibility

F-010 consumes F-008's frozen, rounded entry without revising it. An empty or
unusable entire collection is defensive input handling, not a valid successful
F-008 path.

F-009 supplies no target-selection input. Its stop remains unchanged, and joint
final-price checks remain downstream.

## Blockers

```text
blockers: []
```

- `EMPIRICAL_QUESTION` - Non-blocking: ATR thresholds, hierarchy, recency preference and too-far termination require chronological out-of-sample research, including costs, rejected opportunities and nonfills.
- `NON_BLOCKING_LIMITATION` - Fixtures establish calculation semantics, not complete integration or persistence conformance. Replay approval covers the same primary target/price or rejection from identical frozen evidence; optional diagnostics do not establish portable byte-for-byte serialization.
- `NON_BLOCKING_LIMITATION` - Frozen structure may become stale; fills, profitability and inherited F-008 corrected-history uncertainty remain unresolved.

## Final Approval Record

```yaml
approved_by: FULL_COUNCIL
review_date: 2026-09-15
reviewed_candidate_sha256: 9ba54b04f5786d6947f11423c7f4df51d73906b0df8c02aa30e6e91452601622
trading_fitness: ADEQUATE_FOR_DECLARED_DYNAMIC_TP_ROLE_WITH_LIMITATIONS
blocker_disposition: {F010-C01: CLOSED, F010-C02: CLOSED, F010-C03: CLOSED}
approved_semantics:
  - Frozen Market Handoff v4 collection capability and directional type restrictions.
  - Section 5.15 reason precedence and validated thesis-policy behavior.
  - Versioned structural hierarchy and exact total candidate ordering.
  - Strict raw distance greater than one tick; inclusive raw ATR band [0.75, 4.00].
  - TOO_CLOSE skips; default-traversal TOO_FAR terminates.
  - LONG floor and SHORT ceiling rounding inward to the tick grid.
  - Positive finite grid-aligned favorable output; rounded ATR band revalidation.
  - Terminal post-rounding failure under every thesis policy; no repair.
  - Immutable F-008 entry, independent F-009 stop boundary, and primary-result replay.
limitations_and_research: Preserve candidate Sections 22-24 and the limitations recorded above.
new_council_semantic_definitions: NONE
excluded_certifications: [implementation, persistence, execution, F-011, F-012]
```

Only the three supplied files were read. No files were modified or additional
agents spawned.
