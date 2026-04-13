---
phase: 01-official-ai-ingest-foundation
plan: 01
subsystem: ingest
tags: [openalex, crossref, jsonl, pytest, run-manifest]
requires: []
provides:
  - phase-1 config surface for official ingest only
  - source registry for OpenAlex and Crossref
  - run manifest builder and persistence helpers
  - append-only raw staging helpers for source-native envelopes
affects: [01-02, 01-03, openalex, crossref, replay]
tech-stack:
  added: [pytest]
  patterns: [file-backed manifests, append-only raw JSONL staging, stable source registry]
key-files:
  created:
    - requirements.txt
    - config/settings.example.py
    - config/source_registry.py
    - pipeline/run_context.py
    - pipeline/raw_staging.py
    - tests/test_phase1_contracts.py
  modified: []
key-decisions:
  - "OpenAlex remains the default primary ingest source; Crossref stays metadata backfill only."
  - "Raw staging preserves source-native payloads under `raw` and does not introduce phase-2 schema."
  - "Run manifests carry slice, limits, retry defaults, and per-source attempt metadata for replay."
patterns-established:
  - "Source adapters read config from a shared registry instead of hardcoding source behavior."
  - "Scripts should use shared run/staging helpers rather than ad-hoc JSON output."
requirements-completed: [INGEST-03, QUALITY-02]
duration: 40min
completed: 2026-04-13
---

# Phase 1: Official AI Ingest Foundation Summary

**Wave 1 established the replayable ingest contract: phase-1-only settings, a two-source registry, run manifests, and append-only raw envelopes for official scholarly sources.**

## Performance

- **Duration:** 40 min
- **Started:** 2026-04-13T14:50:00Z
- **Completed:** 2026-04-13T15:30:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added a phase-1-only config example with no phase-2/3 enrichment settings.
- Defined a shared OpenAlex/Crossref source registry with explicit role, retry, and polite-contact metadata.
- Implemented run-manifest and raw-staging helpers so later source adapters inherit one stable contract.
- Locked the contract with offline pytest coverage.

## Files Created/Modified

- `requirements.txt` - phase-1 runtime and test dependencies
- `config/settings.example.py` - minimal official-ingest settings surface
- `config/source_registry.py` - source registry and accessors for `openalex` and `crossref`
- `pipeline/run_context.py` - run manifest dataclasses, context paths, and persistence helpers
- `pipeline/raw_staging.py` - raw envelope builder and JSONL staging helpers
- `tests/test_phase1_contracts.py` - offline contract coverage for settings, registry, manifests, and raw staging

## Decisions Made

- Kept `OPENALEX_API_KEY` optional at the config level but explicit in the source contract.
- Used dataclasses plus file-backed JSON instead of bringing in a schema or workflow framework.
- Standardized raw records on `source`, `entity_type`, `source_record_id`, `slice`, and `raw` so wave 2/3 can compose safely.

## Deviations from Plan

None - plan executed on the intended boundary, with one correction during review: the initial worker output used `payload`/`record_type` field names, and that drift was corrected immediately to the `raw`/`entity_type` contract before wave 2 started.

## Issues Encountered

- System Python was PEP-668 managed, so local verification required a project `.venv`.
- Plain `pytest` in the worker environment reported a capture-path segfault, but `python -m pytest` inside the project venv passed cleanly.

## User Setup Required

None yet. Source credentials and mailto values are still represented by the example settings file only.

## Next Phase Readiness

Wave 2 can now build the OpenAlex adapter and CLI directly on top of the shared run/staging contract. Wave 3 can extend the same contract for Crossref backfill and incremental replay without redefining envelope or manifest shape.

---
*Phase: 01-official-ai-ingest-foundation*
*Completed: 2026-04-13*
