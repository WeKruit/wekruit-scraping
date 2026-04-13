---
phase: 01-official-ai-ingest-foundation
plan: 02
subsystem: ingest
tags: [openalex, ai-ml, presets, argparse, fixtures]
requires:
  - phase: 01-official-ai-ingest-foundation
    provides: shared run/staging contract and source registry
provides:
  - explicit AI/ML venue/concept/keyword presets
  - OpenAlex adapter for query building and raw work/author parsing
  - ingest CLI that stages OpenAlex works and authors through shared helpers
affects: [01-03, openalex, crossref, replay]
tech-stack:
  added: []
  patterns: [fixture-backed source adapter tests, preset-driven query construction]
key-files:
  created:
    - presets/ai_ml.py
    - sources/openalex.py
    - scripts/s1_openalex_fetch.py
    - tests/test_openalex_ingest.py
    - tests/fixtures/openalex/works_page.json
  modified: []
key-decisions:
  - "AI/ML slicing is explicit and repo-owned through preset families instead of ad-hoc CLI filters."
  - "OpenAlex remains the only primary discovery path in phase 1."
  - "CLI writes staged work and author envelopes through shared run/staging helpers and records source-attempt metadata."
patterns-established:
  - "Source CLIs should accept explicit preset-family plus preset-name inputs."
  - "Adapters return raw envelopes for downstream staging instead of writing files directly."
requirements-completed: [INGEST-01, INGEST-02]
duration: 30min
completed: 2026-04-13
---

# Phase 1: Official AI Ingest Foundation Summary

**Wave 2 added the first real ingest path: explicit AI/ML presets, a thin OpenAlex adapter, and a CLI that stages raw works and authors into the shared phase-1 contract.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-04-13T15:30:00Z
- **Completed:** 2026-04-13T16:00:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added repo-owned AI/ML preset families for venue, concept, and keyword entrypoints.
- Implemented a thin OpenAlex adapter that builds query params from one preset and parses source-native work and deduped author envelopes.
- Added an argparse CLI for OpenAlex ingest that stages `works_raw.jsonl` and `authors_raw.jsonl` and writes source-attempt metadata back to the run manifest.
- Locked the ingest path with offline fixture-backed tests.

## Files Created/Modified

- `presets/ai_ml.py` - explicit AI/ML preset families and lookup helpers
- `sources/openalex.py` - OpenAlex query builder and raw page parser
- `scripts/s1_openalex_fetch.py` - phase-1 OpenAlex ingest CLI
- `tests/test_openalex_ingest.py` - offline ingest verification
- `tests/fixtures/openalex/works_page.json` - deterministic OpenAlex fixture payload

## Decisions Made

- Standardized OpenAlex raw entity naming on `works` instead of `papers` to match source-native terminology.
- Kept the adapter read-only and file-agnostic; staging stays in the shared pipeline helpers.
- Recorded source-attempt metadata in the run manifest so replay and Crossref backfill have stable lineage inputs.

## Deviations from Plan

None on scope. One correctness fix was applied during review: the first worker pass staged files correctly but did not persist `source_attempts` into the run manifest, so the CLI was tightened before wave 3 started.

## Issues Encountered

None beyond the earlier local pytest environment setup. All wave-2 verification stayed offline and deterministic.

## User Setup Required

None. The fixture-backed path does not require live OpenAlex credentials.

## Next Phase Readiness

Wave 3 can now consume staged OpenAlex `works_raw.jsonl` outputs, extend the same run contract for Crossref DOI backfill, and add replay/incremental state without redefining raw envelope semantics.

---
*Phase: 01-official-ai-ingest-foundation*
*Completed: 2026-04-13*
