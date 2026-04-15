# Roadmap: Researcher Pipeline

## Overview

This roadmap is milestone-specific for v1.2 Four-Source Human Review Merge Foundation. It pauses
the previous ranking-first path after the completed AI/CS corpus gate and moves the critical path
to durable source-profile storage, four independently triggerable profile pipelines, evidence-based
candidate grouping, human review, and approved researcher-group export.

Ranking, recruiter outreach, and graph-database projection are intentionally out of scope until
human-reviewed people exist.

## Phases

**Phase Numbering:**
- Integer phases continue from prior researcher work.
- Phase 1 and Phase 6 are shipped foundations.
- Phase 7-10 from the prior ranking roadmap are superseded by this milestone and not executed.

- [ ] **Phase 11: Storage And Source Profile Contract** - Define and implement the durable Postgres storage contract for source profiles, signals, candidate groups, review labels, and approved people.
- [ ] **Phase 12: Four Source Profile Pipelines** - Trigger OpenAlex, ORCID, DBLP, and OpenReview profile pipelines independently and persist their outputs.
- [ ] **Phase 13: Signal Extraction And Candidate Reasoning** - Extract comparable identity/contact signals and generate candidate groups with explicit reasons, without auto-merge.
- [ ] **Phase 14: Human Review Queue And Label Ingest** - Export review queues and ingest human labels for same/not-same/unsure decisions.
- [ ] **Phase 15: Approved People Export And Incremental Hygiene** - Export approved people and suppress repeated already-reviewed candidates in future runs.

## Phase Details

### Phase 11: Storage And Source Profile Contract
**Goal**: Users can persist source runs, source profiles, extracted signals, candidate groups, review labels, and approved people in Postgres with provenance intact.
**Depends on**: Phase 1, Phase 6
**Requirements**: [STORE-01, STORE-02, STORE-03]
**Success Criteria** (what must be TRUE):
  1. User can apply a Postgres schema for source runs, source profiles, signals, candidate groups, group reasons, review labels, and approved people.
  2. User can store raw source payloads as JSONB while querying normalized identifiers and review state through relational columns.
  3. User can trace every stored record back to source system, source record ID, run ID, and observed timestamp.
**Plans**: 2 plans

Plans:
- [ ] 11-01: Define Postgres schema and migration contract
- [ ] 11-02: Implement storage adapter and loader fixtures

### Phase 12: Four Source Profile Pipelines
**Goal**: Users can trigger OpenAlex, ORCID, DBLP, and OpenReview profile pipelines independently and persist source-profile outputs.
**Depends on**: Phase 11
**Requirements**: [PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05]
**Success Criteria** (what must be TRUE):
  1. User can run each of the four source pipelines independently.
  2. User can run the four pipelines for the same researcher search batch.
  3. Each pipeline writes source-native raw payload and a normalized source-profile envelope into durable storage.
**Plans**: 3 plans

Plans:
- [ ] 12-01: Persist OpenAlex and ORCID profile pipeline outputs
- [ ] 12-02: Persist DBLP and OpenReview profile pipeline outputs
- [ ] 12-03: Add four-source batch trigger and run summary counts

### Phase 13: Signal Extraction And Candidate Reasoning
**Goal**: Users can extract comparable signals and generate human-review candidate groups with explicit reasons.
**Depends on**: Phase 12
**Requirements**: [SIGNAL-01, SIGNAL-02, SIGNAL-03, CAND-01, CAND-02, CAND-03]
**Success Criteria** (what must be TRUE):
  1. User can extract ORCID, email, homepage, GitHub, DBLP PID, OpenReview ID, Google Scholar ID, LinkedIn, institution, paper DOI, OpenAlex author ID, and OpenAlex work ID signals.
  2. User can see candidate groups produced from exact and review-worthy signals.
  3. User can inspect why each group exists and see suggested strength without any automatic approval.
**Plans**: 3 plans

Plans:
- [ ] 13-01: Implement signal extraction with provenance and quality states
- [ ] 13-02: Implement candidate grouping from evidence signals
- [ ] 13-03: Emit candidate reasoning packets and strength labels

### Phase 14: Human Review Queue And Label Ingest
**Goal**: Users can review candidate groups manually and ingest labels without losing reasoning or provenance.
**Depends on**: Phase 13
**Requirements**: [REVIEW-01, REVIEW-02, REVIEW-03]
**Success Criteria** (what must be TRUE):
  1. User can export review queues as CSV and JSONL.
  2. User can label candidate groups as `same_person`, `not_same_person`, or `unsure`.
  3. User can ingest labels and preserve negative/unsure decisions for future suppression.
**Plans**: 2 plans

Plans:
- [ ] 14-01: Export reviewer-ready candidate queue files
- [ ] 14-02: Ingest human labels and persist reviewed state

### Phase 15: Approved People Export And Incremental Hygiene
**Goal**: Users can export approved researcher groups and avoid repeated review spam as new source-profile runs arrive.
**Depends on**: Phase 14
**Requirements**: [APPROVE-01, APPROVE-02, INCR-01, INCR-02]
**Success Criteria** (what must be TRUE):
  1. User can export `approved_people.jsonl` only from human-labeled `same_person` groups.
  2. User can export unresolved candidates separately from approved people.
  3. User can run new batches and see only new or materially changed candidate groups return to review.
  4. User can inspect counts for profiles stored, signals extracted, candidates created, labels ingested, approved groups exported, and repeats suppressed.
**Plans**: 2 plans

Plans:
- [ ] 15-01: Export approved people and unresolved candidates
- [ ] 15-02: Add incremental review suppression and run-level metrics

## Progress

**Execution Order:**
Phases execute in numeric order: 11 → 12 → 13 → 14 → 15

**Historical Note:**
- Phase 1 official-source ingest foundation shipped on 2026-04-13.
- Phase 6 AI/CS corpus gate shipped on 2026-04-14.
- Prior v1.1 ranking phases 7-10 are superseded until human-reviewed identity groups exist.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Official AI Ingest Foundation | 3/3 | Complete | 2026-04-13 |
| 6. AI/CS Corpus Gate And Venue Tiers | 3/3 | Complete | 2026-04-14 |
| 11. Storage And Source Profile Contract | 0/2 | Ready to plan | - |
| 12. Four Source Profile Pipelines | 0/3 | Not started | - |
| 13. Signal Extraction And Candidate Reasoning | 0/3 | Not started | - |
| 14. Human Review Queue And Label Ingest | 0/2 | Not started | - |
| 15. Approved People Export And Incremental Hygiene | 0/2 | Not started | - |
