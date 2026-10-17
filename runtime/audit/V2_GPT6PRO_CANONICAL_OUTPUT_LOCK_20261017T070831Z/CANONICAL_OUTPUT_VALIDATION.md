# Canonical output validation

Validation: PASS

Read-only validation timestamp: `2026-10-17T07:08:31Z`

1. expected run directory exists: PASS
2. expected canonical files exist: PASS
3. generated manifest is internally consistent: PASS
4. output hashes reconcile: PASS
5. expected 60m counts match exactly: PASS
6. expected 120m counts match exactly: PASS
7. no duplicate canonical keys: PASS
8. deterministic sort holds: PASS
9. unavailable remains distinct from NO_DIRECTION: PASS
10. no dual-direction contradiction: PASS
11. protocol ID matches: PASS
12. release ID matches: PASS
13. configuration hash matches: PASS
14. architecture hash matches: PASS
15. freeze hash matches: PASS
16. harness hash matches: PASS
17. source identity matches: PASS
18. existing validator reports PASS: PASS
19. no canonical file was modified during this task: PASS
20. no calculation rerun occurred: PASS

The existing validator was invoked with `write_report=False`; it did not regenerate labels or write canonical run files.
