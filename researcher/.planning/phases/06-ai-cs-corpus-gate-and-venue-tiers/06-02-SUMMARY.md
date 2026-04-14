# 06-02 Summary

Implemented the strict Phase 6 corpus gate runtime over staged OpenAlex runs.

## Changed Files

- `researcher/pipeline/run_context.py`
- `researcher/pipeline/corpus_gate.py`
- `researcher/scripts/s2_corpus_gate.py`
- `researcher/tests/test_corpus_gate.py`
- `researcher/tests/fixtures/corpus_gate/works_raw.jsonl`

## What Changed

- Added a derived-run manifest helper for append-only gate runs with parent lineage, input/output paths, asset fingerprints, and included/excluded counts.
- Added a strict corpus-gate runtime that reads `data/runs/<input_run>/openalex/works_raw.jsonl`, joins only on exact `raw.primary_location.source.id`, and writes only included works to `gated_works.jsonl`.
- Added a CLI entrypoint for the gate stage and offline tests backed by a local JSONL fixture.

## Verification

- Ran `.venv/bin/python -m pytest tests/test_corpus_gate.py -q`
- Result: `3 passed in 0.08s`
- Ran `python scripts/s2_corpus_gate.py --help >/dev/null`
- Result: exited successfully with no output

## Notes

- No live CCF/CORE/OpenAlex fetches were added.
- The gate does not mutate Phase 1 raw runs in place.
- The output preserves parent lineage and stamps the resolved venue row slug and normalized tier onto included records.
