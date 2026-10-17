# Git release plan

## Files to stage

- Canonical generator, validator, immutable contract module, frozen harness, and focused tests.
- The small formal canonical release package and archive.
- The canonical run's small manifest, summary, validation, and hash manifest.
- This final canonical output lock package and archive.

## Files intentionally not staged

- `canonical_labels.parquet`
- `canonical_labels_60m.parquet`
- `canonical_labels_120m.parquet`
- `canonical_diagnostics.parquet`
- `canonical_unavailable_rows.csv`
- Other runtime data, multi-GB audit payloads, temporary review folders, stale packages, and unrelated untracked files.

The repository ignores `runtime/`. The release records and small immutable manifests therefore use explicit `git add -f`; generated label payloads remain local and are bound by SHA-256 in this lock.

## Exact staging commands

```powershell
cd C:\Users\Елена\Documents\trigger-trade
git add -- "tools\direction_labels\__init__.py"
git add -- "tools\direction_labels\v2_gpt6pro_contract.py"
git add -- "tools\direction_labels\generate_v2_gpt6pro_canonical.py"
git add -- "tools\direction_labels\validate_v2_gpt6pro_canonical.py"
git add -- "tools\research_v2\v2_research_harness.py"
git add -- "tests\unit\test_v2_gpt6pro_canonical_entrypoint.py"
git add -- "tests\unit\test_v2_research_harness.py"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_CHANGE_CONTROL.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_CONFIGURATION_IDENTITY.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_EVIDENCE_CHAIN.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_HARNESS_IDENTITY.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_LIMITATIONS.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_POST_RELEASE_VALIDATION.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_PROTOCOL_IDENTITY.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_RELEASE_AMENDMENT.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_RELEASE_LOCK.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_RELEASE_MANIFEST.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\CANONICAL_SOURCE_IDENTITY.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\EXPERT_RELEASE_DECISIONS.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\OUTPUT_HASHES.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z\PACKAGE_VALIDATION.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z.zip"
git add -f -- "runtime\data\canonical_direction_labels\V2_GPT6PRO\20261017T054006Z\canonical_generation_manifest.json"
git add -f -- "runtime\data\canonical_direction_labels\V2_GPT6PRO\20261017T054006Z\canonical_generation_summary.csv"
git add -f -- "runtime\data\canonical_direction_labels\V2_GPT6PRO\20261017T054006Z\canonical_generation_validation.md"
git add -f -- "runtime\data\canonical_direction_labels\V2_GPT6PRO\20261017T054006Z\canonical_output_hashes.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_LOCK.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_IDENTITY.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_FILE_HASHES.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_COUNTS.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_INVENTORY.csv"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_OUTPUT_VALIDATION.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\CANONICAL_RELEASE_BINDING.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\GIT_RELEASE_PLAN.md"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z\OUTPUT_HASHES.json"
git add -f -- "runtime\audit\V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z.zip"
git diff --cached --name-only
git diff --cached --check
git diff --cached
git commit -m "feat: canonicalize v2_gpt6pro historical direction labels"
```

## Tag

- Tag: `direction-label-v2-gpt6pro-canonical-v1`
- Annotated message: `V2_GPT6PRO canonical historical direction-label protocol and first canonical output lock`

```powershell
cd C:\Users\Елена\Documents\trigger-trade
git tag -a direction-label-v2-gpt6pro-canonical-v1 -m "V2_GPT6PRO canonical historical direction-label protocol and first canonical output lock"
git push origin main
git push origin direction-label-v2-gpt6pro-canonical-v1
```

These commands are prepared only. No staging, commit, tag, or push was executed by this lock task.
