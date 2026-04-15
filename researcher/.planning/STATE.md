---
phase: "Phase 11"
name: "Storage And Source Profile Contract"
created: 2026-04-15
status: ready_to_plan
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-15)

**Core value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and outreach can trust who the researcher is, what they worked on, how the contact signal was found, and why multiple source records were or were not merged.
**Current focus:** Phase 11 — Storage And Source Profile Contract

## Current Position

Phase: 11 of 15 (Storage And Source Profile Contract)
Plan: —
Status: Ready to plan
Last activity: 2026-04-15 — Milestone v1.2 started for four-source human-reviewed merge and durable storage

Progress: [████░░░░░░] 40%

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

- [Phase 1]: OpenAlex ingest plus Crossref backfill remains the foundation for paper and author discovery.
- [Phase 6]: AI/CS corpus membership is determined only by explicit venue-tier rows keyed by exact OpenAlex source IDs.
- [Milestone v1.2]: Ranking pauses until human-reviewed researcher groups exist.
- [Milestone v1.2]: Four profile sources are OpenAlex, ORCID, DBLP, and OpenReview.
- [Milestone v1.2]: Homepage, GitHub, and email extraction are derived signal stages, not separate canonical source systems.
- [Storage]: Postgres is the durable store for source profiles, signals, candidate groups, review labels, and approved people.
- [Storage]: NoSQL and Neo4j are not primary stores for this milestone; Neo4j can be reconsidered later as a projection if graph traversal becomes a measured need.
- [Identity]: All candidate groups require human review. The system provides reasoning, not automatic merges.

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 11 must lock the Postgres schema before any source pipeline writes durable data.
- Candidate grouping must preserve negative and unsure labels so the system does not repeatedly ask humans to review the same rejected profiles.
- OpenReview live-access reliability still needs validation before Phase 12 implementation.
- Contact quality must remain evidence attached to source profiles and review groups, not a direct merge decision.

## Session Continuity

Last session: 2026-04-15 09:20 PDT
Stopped at: Milestone v1.2 planning created; next step is Phase 11 planning.
Resume file: None
