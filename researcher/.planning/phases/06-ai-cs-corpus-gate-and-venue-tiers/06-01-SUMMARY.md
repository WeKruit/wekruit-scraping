# 06-01 Summary

Implemented the Phase 6 venue-tier asset and strict offline validator in `researcher/` only.

## Changed Files

- `researcher/data/assets/ai_cs_venue_tiers.csv`
- `researcher/pipeline/venue_tiers.py`
- `researcher/tests/test_venue_tiers.py`

## What Changed

- Added a reviewed AI/CS venue-tier CSV keyed by exact OpenAlex source IDs.
- Added a strict loader/validator that enforces the fixed schema, normalized tier set, include/exclude consistency, duplicate source ID rejection, and stable asset hashing.
- Added contract tests for schema, row loading, reason-code exports, invalid asset rejection, and fingerprint stability.

## Verification

- Ran `.venv/bin/python -m pytest tests/test_venue_tiers.py -q`
- Result: `6 passed in 0.02s`

## Notes

- The asset includes included, excluded, and unresolved AI/CS venues.
- Bio/Pharma rows were not added.
- No live CCF/CORE/OpenAlex fetching was added to runtime or tests.
