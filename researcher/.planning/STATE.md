---
phase: "Phase 11"
name: "Sourcing Firebase Schema And Collection Contract"
created: 2026-04-15
status: ready_to_plan
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-15)

**Core value:** Turn heterogeneous scraping outputs into durable, reviewable, source-backed entities with explicit reasoning, without forcing all source-specific payloads into SQL columns or rewriting working Python scrapers into TypeScript.
**Current focus:** Phase 11 — Sourcing Firebase Schema And Collection Contract

## Current Position

Phase: 11 of 16 (Sourcing Firebase Schema And Collection Contract)
Plan: —
Status: Ready to plan
Last activity: 2026-04-15 — v1.2 phase plan reframed around shared sourcing service, Firebase/core-service backend, and Python worker upload boundary

Progress: [████░░░░░░] 38%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 35 min
- Total execution time: 3.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | 1.75h | 35 min |
| 6 | 3 | 1.75h | 35 min |

**Recent Trend:**
- Last 5 plans: 5 completed
- Trend: Stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 1]: OpenAlex ingest plus Crossref backfill remains the foundation for researcher paper and author discovery.
- [Phase 6]: AI/CS corpus membership is determined only by explicit venue-tier rows keyed by exact OpenAlex source IDs.
- [Milestone v1.2]: The platform direction is shared `sourcing`, not researcher-only storage.
- [Milestone v1.2]: Local Python workers execute fetching/parsing and upload through core-service APIs.
- [Milestone v1.2]: Core-service owns Firebase persistence, schema validation, review labels, and approved entities.
- [Milestone v1.2]: Python workers must not write directly to Firestore.
- [Milestone v1.2]: Evidence is a first-class Firestore document, not a hidden field on candidate reasoning.
- [Milestone v1.2]: Dedup candidates are review proposals and never become approved entities without human labels.
- [Milestone v1.2]: Full reviewer UI is deferred until API/CSV/JSONL review flow is proven.
- [Identity]: All dedup candidates require human review. The system provides evidence-linked reasoning, not automatic merges.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 11 must inspect core-service structure before defining concrete file paths; follow existing `matching` and `outbound` conventions.
- Cross-repo execution means Phase 11 and Phase 12 must clearly separate core-service changes from scraping repo changes.
- Core-service repository access and branch strategy must be confirmed before implementation starts.
- OpenReview live-access reliability still needs validation before Phase 14 implementation.
- Dedup candidate generation must preserve negative and unsure labels so the system does not repeatedly ask humans to review the same rejected profiles.
- Phase 15 must ensure dedup candidate IDs are deterministic and evidence-linked.

## Session Continuity

Last session: 2026-04-15 10:20 PDT
Stopped at: v1.2 phase plan updated; next step is `$gsd-plan-phase 11`.
Resume file: None
