---
phase: "Phase 7"
name: "Canonical Schema And Identity Resolution"
created: 2026-04-14
status: ready_to_plan
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-13)

**Core value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and outreach can trust who the researcher is, what they worked on, and how the contact signal was found.
**Current focus:** Phase 7 — Canonical Schema And Identity Resolution

## Current Position

Phase: 7 of 10 (Canonical Schema And Identity Resolution)
Plan: —
Status: Ready to plan
Last activity: 2026-04-14 — Phase 6 shipped with venue-tier asset, corpus gate runtime, decision logs, and local POCs

Progress: [████░░░░░░] 35%

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
- Trend: Increasing

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 1]: OpenAlex ingest plus Crossref backfill remains the foundation for v1.1 work
- [Roadmap]: v1.1 phase numbering continues at 6 and replaces prior forward-looking placeholder phases
- [Roadmap]: AI/CS venue-tier corpus gating happens before canonical schema, enrichment, and ranking
- [Roadmap]: Bio/Pharma and UI work stay out of scope for milestone v1.1
- [Phase 6]: AI/CS corpus membership is determined only by explicit venue-tier rows keyed by exact OpenAlex source IDs
- [Storage]: Canonical identity should move into Postgres with append-only evidence, with Neo4j only as a later projection if traversal becomes a true product need

### Pending Todos

None yet.

### Blockers/Concerns

- OpenAlex author-detail throughput should be verified before Phase 8 implementation
- OpenReview live-access reliability should be confirmed during Phase 8 planning
- Ranking calibration must be accepted before exported recruiter outputs are treated as trustworthy
- Canonical identity tables and merge/unmerge evidence rules must be fixed in Phase 7 before any cross-source contact enrichment expands further

## Session Continuity

Last session: 2026-04-14 18:10 PDT
Stopped at: Phase 6 executed, local corpus-gate POCs completed, and graph-storage strategy synthesized from two research teams
Resume file: None
