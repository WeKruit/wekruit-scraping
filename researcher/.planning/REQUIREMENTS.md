# Requirements: Researcher Pipeline

**Defined:** 2026-04-15
**Milestone:** v1.2 Four-Source Human Review Merge Foundation
**Core Value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and outreach can trust who the researcher is, what they worked on, how the contact signal was found, and why multiple source records were or were not merged.

## Foundation Requirements (Validated)

- [x] **INGEST-01**: User can run official-source paper and author ingest without relying on generic web crawling.
- [x] **INGEST-02**: User can target AI/ML papers through concept, venue, or keyword presets.
- [x] **INGEST-03**: User can replay raw source-native paper and author staging files for the same run configuration.
- [x] **QUALITY-02**: User can rerun the ingest pipeline incrementally with per-source limits, retries, and audit metadata preserved.
- [x] **CORPUS-01**: User can restrict the AI/CS ranking corpus to papers that pass explicit venue-tier inclusion rules.
- [x] **CORPUS-02**: User can review a local AI/CS venue-tier table that preserves upstream source, grade, normalized tier, and last-reviewed metadata.
- [x] **CORPUS-03**: User can see why a paper was included or excluded from the AI/CS ranking corpus.

## Milestone v1.2 Requirements

### Durable Storage

- [ ] **STORE-01**: User can persist source runs, source profiles, extracted signals, candidate groups, review labels, and approved people in Postgres.
- [ ] **STORE-02**: User can inspect raw source payloads as JSONB while still querying normalized identifiers, signals, labels, and group state through relational columns.
- [ ] **STORE-03**: User can trace every stored profile, signal, candidate reason, and human label back to source system, source record ID, run ID, and observed timestamp.

### Four Source Profile Pipelines

- [ ] **PIPE-01**: User can trigger the OpenAlex profile pipeline independently and persist OpenAlex author/profile records.
- [ ] **PIPE-02**: User can trigger the ORCID profile pipeline independently and persist ORCID public profile records.
- [ ] **PIPE-03**: User can trigger the DBLP profile pipeline independently and persist DBLP author records.
- [ ] **PIPE-04**: User can trigger the OpenReview profile pipeline independently and persist OpenReview profile records.
- [ ] **PIPE-05**: User can run all four pipelines for the same researcher search batch without requiring the outputs to share one source-native schema.

### Signal Extraction

- [ ] **SIGNAL-01**: User can extract comparable identity/contact signals from source profiles: ORCID, email, homepage, GitHub, DBLP PID, OpenReview profile ID, Google Scholar ID, LinkedIn, institution, paper DOI, and OpenAlex author/work IDs.
- [ ] **SIGNAL-02**: User can extract derived homepage/GitHub/email signals from public URLs without turning those pages into separate canonical source systems.
- [ ] **SIGNAL-03**: User can inspect signal provenance and quality state instead of seeing only flattened strings.

### Candidate Grouping And Reasoning

- [ ] **CAND-01**: User can generate candidate groups from exact and review-worthy signals without automatically merging people.
- [ ] **CAND-02**: User can see machine-readable merge reasons for every candidate group, such as `orcid_exact`, `email_exact`, `github_exact`, `homepage_exact`, `dblp_link`, `openreview_dblp_link`, `paper_overlap`, or `name_institution`.
- [ ] **CAND-03**: User can see suggested strength (`strong`, `medium`, `weak`) without that strength becoming an approval decision.

### Human Review

- [ ] **REVIEW-01**: User can export a human review queue as CSV and JSONL with candidate group ID, profiles, names, institutions, signals, reasons, suggested strength, `human_label`, and notes.
- [ ] **REVIEW-02**: User can ingest human labels: `same_person`, `not_same_person`, and `unsure`.
- [ ] **REVIEW-03**: User can preserve negative and unsure labels so repeated pipeline runs do not keep re-surfacing the same already-reviewed candidates.

### Approved People And Incremental Operation

- [ ] **APPROVE-01**: User can export approved researcher groups only from human-labeled `same_person` candidates.
- [ ] **APPROVE-02**: User can export unresolved candidates separately from approved people.
- [ ] **INCR-01**: User can run new source-profile batches and generate only new or materially changed review candidates.
- [ ] **INCR-02**: User can inspect run-level counts for profiles stored, signals extracted, candidate groups created, labels ingested, approved groups exported, and repeated candidates suppressed.

## Future Requirements

- [ ] **RANK-01**: User can rank AI/CS papers with explicit component scores for recency, citation signal, venue tier, and author influence.
- [ ] **RANK-02**: User can choose between `latest`, `impact`, and `balanced` ranking modes.
- [ ] **RANK-03**: User can inspect score breakdowns for each ranked paper and ranked researcher record.
- [ ] **EXPORT-01**: User can export ranked AI/CS papers as CSV and JSONL with provenance and score breakdown retained.
- [ ] **EXPORT-02**: User can export ranked AI/CS researchers as CSV and JSONL with top-paper context and contact-quality context retained.
- [ ] **BIO-01**: User can support a Bio/Pharma ranking track without sharing venue or citation semantics with the AI/CS track.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic person merge | User explicitly wants every candidate reviewed by a human |
| NoSQL as primary store | Review labels, negative pairs, constraints, and audit-safe state need relational guarantees |
| Neo4j as primary store | Current bottleneck is evidence and human review, not graph traversal |
| Ranking from unreviewed identities | Ranking before approved people would amplify uncertain merge state |
| Dashboard or operator UI | CSV/JSONL review queues are enough for this milestone |
| Closed-platform or login-gated scraping | Outside the source policy for this project |
| Generic crawl-first discovery | Conflicts with the official-source backbone and increases schema/compliance risk |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Validated |
| INGEST-02 | Phase 1 | Validated |
| INGEST-03 | Phase 1 | Validated |
| QUALITY-02 | Phase 1 | Validated |
| CORPUS-01 | Phase 6 | Validated |
| CORPUS-02 | Phase 6 | Validated |
| CORPUS-03 | Phase 6 | Validated |
| STORE-01 | Phase 11 | Pending |
| STORE-02 | Phase 11 | Pending |
| STORE-03 | Phase 11 | Pending |
| PIPE-01 | Phase 12 | Pending |
| PIPE-02 | Phase 12 | Pending |
| PIPE-03 | Phase 12 | Pending |
| PIPE-04 | Phase 12 | Pending |
| PIPE-05 | Phase 12 | Pending |
| SIGNAL-01 | Phase 13 | Pending |
| SIGNAL-02 | Phase 13 | Pending |
| SIGNAL-03 | Phase 13 | Pending |
| CAND-01 | Phase 13 | Pending |
| CAND-02 | Phase 13 | Pending |
| CAND-03 | Phase 13 | Pending |
| REVIEW-01 | Phase 14 | Pending |
| REVIEW-02 | Phase 14 | Pending |
| REVIEW-03 | Phase 14 | Pending |
| APPROVE-01 | Phase 15 | Pending |
| APPROVE-02 | Phase 15 | Pending |
| INCR-01 | Phase 15 | Pending |
| INCR-02 | Phase 15 | Pending |

**Coverage:**
- Foundation requirements validated: 7
- Milestone v1.2 requirements: 21
- Future requirements deferred: 6

---
*Last updated: 2026-04-15 after milestone v1.2 requirements definition*
