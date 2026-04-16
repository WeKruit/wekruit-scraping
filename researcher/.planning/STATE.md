---
phase: "Phase 17"
name: "Minimal Review Web And Firebase Hosting"
created: 2026-04-15
status: complete
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-15)

**Core value:** Turn heterogeneous scraping outputs into durable, reviewable, source-backed entities with explicit reasoning, without forcing all source-specific payloads into SQL columns or rewriting working Python scrapers into TypeScript.
**Current focus:** v1.2 Firebase sourcing review/store POC complete; next focus is production deploy/Cloud Run scheduling or outbound handoff.

## Current Position

Phase: 17 of 17 (Minimal Review Web And Firebase Hosting)
Plan: 17-02
Status: Complete
Last activity: 2026-04-15 — core-service sourcing API, Firebase persistence, evidence/dedup review loop, CSV/JSONL upload web, and Python upload bridge validated in local emulators

Progress: [██████████] 100%

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
- [Milestone v1.2]: Sourcing-owned Firebase resources must use explicit `sourcing` prefixes.
- [Milestone v1.2]: Outbound is a downstream consumer of approved entities only, not dedup candidates.
- [Milestone v1.2]: Minimal Firebase-hosted review web is now in scope for upload/review/approved inspection.
- [Milestone v1.2]: Full product-grade reviewer UI is deferred; only minimal Firebase-hosted review web is in scope.
- [Milestone v1.2]: The minimal loop is API-backed and Firebase-stored; Python scraping workers remain local uploaders.
- [Milestone v1.2]: Devpost, GitHub, and manual CSV/JSON/JSONL imports use the same generic source-record uploader.
- [Identity]: All dedup candidates require human review. The system provides evidence-linked reasoning, not automatic merges.

### Pending Todos

None yet.

### Blockers/Concerns

- Production deploy still needs a deliberate Firebase deploy decision for staging vs production.
- Cloud Run or Mac mini scheduling for Python scraping workers is not implemented yet.
- OpenReview live-access reliability still needs validation before Phase 14 implementation.
- Future outbound handoff must preserve lineage back to approved entity, review label, dedup candidate, evidence, and source records.

## Session Continuity

Last session: 2026-04-15 19:10 PDT
Stopped at: v1.2 local Firebase sourcing loop validated; next step is production deploy decision or outbound handoff planning.
Resume file: None
