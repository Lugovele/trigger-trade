# V2_GPT6PRO canonical release amendment

**Release ID:** `V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z`  
**Canonical release timestamp (UTC):** `2026-10-17T04:35:56Z`  
**Research freeze date:** `2026-10-13`  
**Status:** `CANONICAL_HISTORICAL_LABEL_PROTOCOL`  
**Scope:** `RETROSPECTIVE HISTORICAL MARKET-DIRECTION LABELING ONLY`

## Release decision

Research candidate `V2_GPT6PRO_RC_GPT6` is promoted to canonical protocol `V2_GPT6PRO`. V2-REL-01 and V2-REL-02 are closed. Claude and GPT-6 Pro independently returned `APPROVE_CANONICAL_RELEASE`. No semantic, stability, or implementation blocker remains.

This amendment creates the canonical record and lock. It generates no canonical labels.

## Canonical target and classes

> A material one-sided market advantage sustained over a material part of the evaluation horizon, with sufficient advantage still present at the horizon boundary.

Canonical classes: `LONG_FAVORED`, `SHORT_FAVORED`, `NO_DIRECTION`.

This protocol is a retrospective historical target. It is not a live estimator, signal, strategy, trading decision engine, execution model, or P/L validation.

## Frozen configuration

- `a="0.50"`
- `beta="0.25"`
- `rho="0.10"`
- `eta="0.50"`
- Canonical serialization: `{"a":"0.50","beta":"0.25","rho":"0.10","eta":"0.50"}`
- Configuration SHA-256: `fb194d06cf2b79db113f74cec495fe96c61c6fde1cc33981d678332bdd919f99`
- `tau = 1e-12`

Derived horizon constants:

| Horizon | Role | p | w | L_min |
|---|---|---:|---:|---:|
| 60m | PRIMARY | 6 | 11 | 15 |
| 120m | SECONDARY, independently evaluated | 12 | 23 | 30 |

The 120m result does not confirm, veto, overwrite, fill, or alter the 60m canonical label. Research-only 55m, 65m, 115m, and 125m results are not canonical fields.

## RMS48 calculation contract

RMS48 uses exactly **48 causal five-minute returns** from the frozen harness, not 48 one-minute returns. For adjacent 5m origins under continuous data, one 5m return normally enters, one exits, and 47 remain.

## Six-predicate directional conjunction

For each side `q`, all six conditions must pass:

1. `GE(J_q, beta)` — sufficient J.
2. `M_q > 0` — positive M, strictly compared to zero.
3. `GE(B_q, 1)` — material establishment.
4. `NOT material_phase_exists(opposite side)` — no material opposing phase.
5. `R_q > 0` — positive remainder, strictly compared to zero.
6. `GE(R_q, min(eta * B_q, 1))` — sufficient retained advantage.

`GE(u,v)` means `u >= v - tau`. P4 is the exact Boolean complement of opposing material-phase existence; it is not a generic `GE_WITH_TAU` scalar comparison. LONG and SHORT use exact mirror-symmetric rules without priority.

## Source and runtime binding

- Architecture SHA-256: `7d5af8dde65fc7a3ead814e3bfa57e8ec19fa9bc3f5d2c923258da9732a0e799`
- Freeze amendment SHA-256: `9cc5d4ea6485b59227a94e4fbef54dda3fbc43e725e746b53c9d8b03a5942134`
- Harness SHA-256: `a06e678b2f21898ba38868c505c92e9056fc85692966fd62b614dc6e6c348477`
- Corpus: `direction-regime-history-20240930-20260930-bybit-linear-1m-v1`
- Source manifest SHA-256: `f600c0546344259911075f479de583c69d88435321e06c41e0e61acbf49bf45e`
- Symbols: BTCUSDT, AVAXUSDT, SUIUSDT, 1000PEPEUSDT; logical PEPEUSDT maps to physical 1000PEPEUSDT.
- Common range: 2024-09-30T07:20:00Z through 2026-09-30T00:00:00Z.

## Fresh-panel evidence

- Panel selection SHA-256: `94adafcfa644231825d06f5424d4a1dda04846d99cacaa80a1065eb63fd50cca`
- Cases: 412; case-horizon rows: 824.
- Reviewer agreement: 60m 337/412 = 81.80%; 120m 353/412 = 85.68%.
- Opposite-direction reviewer disagreements: 0 at 60m; 0 at 120m.
- Candidate matches agreed reviewers: 308/337 at 60m; 314/353 at 120m.
- Candidate opposite agreed direction: 0 at both horizons.
- HIGH/HIGH agreed rows: 321; candidate disagreements: 3.

Reviewer agreement is not ground truth. The exact provenance limitations remain in `CANONICAL_LIMITATIONS.md`.

## 68-row semantic adjudication

All 68 candidate-versus-agreed-reviewer disagreement rows were adjudicated. Independent expert conclusions were `CONTINUE_RC_GPT6_UNCHANGED`; no semantic contradiction was demonstrated. The exact retained disagreement ledger is bound in `CANONICAL_EVIDENCE_CHAIN.json`. Ambiguity is not collapsed into a claim that the candidate was “correct.”

## Final blocker state

- `V2_REL_01: CLOSED`
- `V2_REL_02: CLOSED`
- `SEMANTIC_BLOCKER: NO`
- `STABILITY_BLOCKER: NO`
- `IMPLEMENTATION_BLOCKER: NO`
- Claude: `APPROVE_CANONICAL_RELEASE`
- GPT-6 Pro: `APPROVE_CANONICAL_RELEASE`

## Active evidence status

- Active closure wrapper: `RC_GPT6_RELEASE_BLOCKER_CLOSURE_20261016T055025Z`.
- Stale historical-only wrapper: `RC_GPT6_RELEASE_BLOCKER_CLOSURE_20261016T050339Z`.
- Precision chain: 042006Z base → superseded 050339Z partial repair → 055025Z final overlay.
- Section16 chain: 042006Z base → 050339Z completion.

Known accepted limitations, change control, post-release obligations, and immutable evidence identities are incorporated by reference from this release directory.
