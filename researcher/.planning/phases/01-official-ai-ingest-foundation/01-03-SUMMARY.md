---
phase: 01-official-ai-ingest-foundation
plan: 03
subsystem: ingest
tags: [crossref, replay, incremental, doi, checkpoints]
requires:
  - phase: 01-official-ai-ingest-foundation
    provides: OpenAlex staged works and shared run/staging contract
provides:
  - Crossref DOI backfill over staged OpenAlex works
  - file-backed seen-id and checkpoint helpers
  - replay path for staged OpenAlex runs
affects: [phase-2, crossref, replay, incremental]
tech-stack:
  added: []
  patterns: [parent-run lineage, file-backed seen-doi tracking, replay without network]
key-files:
  created:
    - pipeline/incremental_state.py
    - sources/crossref.py
    - scripts/s1_crossref_backfill.py
    - tests/test_crossref_backfill.py
    - tests/fixtures/crossref/work.json
  modified:
    - scripts/s1_openalex_fetch.py
    - pipeline/run_context.py
key-decisions:
  - "Crossref remains DOI backfill only and never discovers works independently."
  - "Incremental state is keyed by upstream OpenAlex lineage and stored under `data/state/`."
  - "OpenAlex replay is file-backed and avoids network fetches entirely."
patterns-established:
  - "Backfill CLIs consume upstream run IDs and preserve `parent_run_id` in their manifests."
  - "Replay/resume controls extend manifest lineage without changing raw envelope shape."
requirements-completed: [INGEST-03, QUALITY-02]
duration: 35min
completed: 2026-04-13
---

# Phase 1: Official AI Ingest Foundation Summary

**Wave 3 completed the ingest foundation by adding Crossref DOI backfill, file-backed incremental state, and a replay path for staged OpenAlex runs.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-13T16:00:00Z
- **Completed:** 2026-04-13T16:35:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added a thin Crossref adapter that resolves one DOI at a time and stages raw Crossref work payloads.
- Added `s1_crossref_backfill.py`, which requires an upstream OpenAlex run, skips no-DOI records, preserves `parent_run_id`, and records attempt metadata.
- Added file-backed incremental helpers for seen DOI tracking and checkpoints under `data/state/`.
- Added a replay path to `s1_openalex_fetch.py` so existing staged runs can be exercised without network calls.
- Locked the whole backfill/replay path with offline pytest coverage.

## Files Created/Modified

- `pipeline/incremental_state.py` - seen-id and checkpoint persistence helpers
- `sources/crossref.py` - DOI normalization and raw Crossref fetch adapter
- `scripts/s1_crossref_backfill.py` - Crossref DOI backfill CLI over staged OpenAlex works
- `scripts/s1_openalex_fetch.py` - replay support and source-name correctness
- `tests/test_crossref_backfill.py` - offline Crossref backfill and replay verification
- `tests/fixtures/crossref/work.json` - deterministic Crossref fixture payload
- `pipeline/run_context.py` - source-aware manifest creation for non-OpenAlex runs

## Decisions Made

- Chose lineage keyed by upstream OpenAlex run ID instead of a broader preset hash for phase 1 incremental state; that keeps replay/backfill semantics explicit and auditable.
- Stored skip counts inside source-attempt request metadata rather than inventing a second reporting file.
- Added replay support to the existing OpenAlex CLI instead of creating a separate replay command.

## Deviations from Plan

None on scope. One correctness fix was required during review: `create_run_context()` originally hardcoded `source_name="openalex"`, which would have mislabeled Crossref manifests. That was corrected before final verification.

## Issues Encountered

None beyond ordinary test-driven fixes. All verification remained offline.

## User Setup Required

None for local fixture-backed verification. Live Crossref usage will still require a real settings file and polite-contact configuration.

## Next Phase Readiness

Phase 1 is now end-to-end ready for planner handoff: shared contracts exist, OpenAlex ingest is staged, Crossref backfill is lineage-safe, and replay/incremental state is file-backed. Phase 2 can focus purely on canonical schema and identity logic without reopening ingest semantics.

---
*Phase: 01-official-ai-ingest-foundation*
*Completed: 2026-04-13*
