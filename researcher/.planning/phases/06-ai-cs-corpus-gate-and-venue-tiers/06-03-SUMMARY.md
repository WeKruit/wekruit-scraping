# 06-03 Summary

Implemented the full Phase 6 decision log and append-only rerun semantics.

## Changed Files

- `researcher/pipeline/corpus_gate.py`
- `researcher/scripts/s2_corpus_gate.py`
- `researcher/tests/test_corpus_gate.py`
- `researcher/tests/fixtures/corpus_gate/expected_gate_decisions.jsonl`
- `researcher/.planning/phases/06-ai-cs-corpus-gate-and-venue-tiers/06-03-SUMMARY.md`

## What Changed

- Added `gate_decisions.jsonl` output with one decision record per staged OpenAlex work.
- Kept `reason_codes` as a list in the decision log, even when there is only one reason.
- Added readable `title` and `publication_date` fields to each decision record without duplicating the full raw work payload.
- Locked append-only rerun semantics by creating new gate runs for new parent runs or venue-table revisions and refusing to overwrite an existing gate run directory.

## Verification

- Ran `.venv/bin/python -m pytest tests/test_corpus_gate.py -q`
- Result: `5 passed in 0.12s`
- Ran `python scripts/s2_corpus_gate.py --help >/dev/null`
- Result: exited successfully with no output

## Notes

- The decision log uses only Phase 6 reason codes and remains a strict superset of the included corpus.
- No seen-ID state, scheduler, or database layer was added.
