# Requirements: Sourcing Pipeline

**Defined:** 2026-04-15
**Milestone:** v1.2 Sourcing Service And Human Review Foundation
**Core Value:** Turn heterogeneous scraping outputs into durable, reviewable, source-backed entities with explicit reasoning, without forcing all source-specific payloads into SQL columns or rewriting working Python scrapers into TypeScript.

## Foundation Requirements (Validated)

- [x] **INGEST-01**: User can run official-source researcher paper and author ingest without relying on generic web crawling.
- [x] **INGEST-02**: User can target AI/ML papers through concept, venue, or keyword presets.
- [x] **INGEST-03**: User can replay raw source-native paper and author staging files for the same run configuration.
- [x] **QUALITY-02**: User can rerun the ingest pipeline incrementally with per-source limits, retries, and audit metadata preserved.
- [x] **CORPUS-01**: User can restrict the AI/CS ranking corpus to papers that pass explicit venue-tier inclusion rules.
- [x] **CORPUS-02**: User can review a local AI/CS venue-tier table that preserves upstream source, grade, normalized tier, and last-reviewed metadata.
- [x] **CORPUS-03**: User can see why a paper was included or excluded from the AI/CS ranking corpus.
- [x] **CORE-FOUNDATION-01**: Core-service already provides Firebase Functions, Firestore, zod, repository patterns, task queues, emulator config, and centralized collection naming.

## Milestone v1.2 Requirements

### Core-Service Sourcing Contract

- [x] **CORE-01**: User can review a `sourcing` service implementation that follows the existing core-service file-management pattern: `domain`, `application`, `repositories`, `functions/http`, and `functions/tasks`.
- [x] **CORE-02**: User can validate source runs, source records, evidence records, dedup candidates, review labels, and approved entities through zod schemas before Firestore writes.
- [x] **CORE-03**: User can store queryable source summaries, raw pointers, content hashes, and optional raw payloads in Firebase-owned sourcing records.
- [x] **CORE-04**: User can query sourcing Firestore collections without disrupting existing `matching` and `outbound` services.
- [x] **CORE-05**: User can verify every sourcing-owned Firestore collection, raw path, Cloud Tasks queue, and HTTP route uses explicit sourcing prefixes: `sourcing-*`, `sourcing/raw/...`, `sourcing-*`, and `/api/sourcing/...`.

### Core-Service Ingest API

- [x] **API-01**: User can create a source run through a core-service HTTP endpoint.
- [x] **API-02**: User can batch upsert source records through a core-service HTTP endpoint.
- [x] **API-03**: User can complete a source run and inspect stored source-record, evidence, and dedup-candidate counts.
- [x] **API-04**: User can reject invalid source-record payloads before they reach Firestore.

### Python Worker Integration

- [x] **PY-01**: User can run Python scraping workers locally and upload records through the core-service API instead of writing directly to Firebase.
- [x] **PY-02**: User can preserve local JSONL run artifacts for replay/debug while treating core-service/Firebase as product storage.
- [x] **PY-03**: User can upload a previous local JSONL run to core-service as a replay without re-fetching the source.

### Source Domain Integration

- [x] **DOMAIN-01**: User can map researcher OpenAlex outputs into generic `domain=researcher` source records.
- [x] **DOMAIN-02**: User can map researcher contact-enrichment outputs containing ORCID, DBLP, and OpenReview fields into generic `domain=researcher` source records.
- [x] **DOMAIN-03**: User can map existing `devpost` outputs into generic source records.
- [x] **DOMAIN-04**: User can map existing `github` outputs into generic source records.
- [x] **DOMAIN-05**: User can add a future source by implementing the source-record contract without changing core Firestore collections.

### Evidence Extraction And Dedup Candidate Generation

- [x] **EVIDENCE-01**: User can create first-class evidence records from source records for email, ORCID, GitHub, homepage, DBLP, OpenReview ID, Google Scholar ID, institution, paper DOI, source-native IDs, and source URLs.
- [x] **EVIDENCE-02**: User can inspect each evidence record with `sourceRecordId`, `evidenceType`, `rawValue`, `normalizedValue`, `valueHash`, extraction path, source URL, quality state, observed timestamp, and extractor version.
- [x] **EVIDENCE-03**: User can inspect evidence provenance and quality before the evidence participates in dedup candidate generation.
- [x] **DEDUP-01**: User can generate dedup candidates from exact and review-worthy evidence without automatically merging entities.
- [x] **DEDUP-02**: User can see machine-readable reasons for every dedup candidate, such as `orcid_exact`, `email_exact`, `github_exact`, `homepage_exact`, `dblp_exact`, `openreview_exact`, `google_scholar_exact`, `source_native_id_exact`, or `name_institution`.
- [x] **DEDUP-03**: User can verify every dedup reason points to one or more evidence IDs instead of free-text-only reasoning.
- [x] **DEDUP-04**: User can see suggested strength (`strong`, `medium`, `weak`) without that strength becoming an approval decision.

### Human Review And Approved Entities

- [x] **REVIEW-01**: User can export or query a human review queue with dedup candidate ID, source records, names, institutions, evidence, reasons, suggested strength, status, and notes.
- [x] **REVIEW-02**: User can ingest human labels: `same_person`, `not_same_person`, and `unsure`.
- [x] **REVIEW-03**: User can preserve negative and unsure labels so repeated pipeline runs do not keep re-surfacing the same already-reviewed candidates.
- [x] **APPROVE-01**: User can create approved entities only from human-labeled `same_person` dedup candidates.
- [x] **APPROVE-02**: User can export approved entities separately from unresolved dedup candidates.

### Minimal Review Web And Firebase Hosting

- [x] **WEB-01**: User can open a minimal Firebase-hosted sourcing review page for JSONL/CSV upload, pending dedup review, review-label submission, and approved-entity inspection.
- [x] **WEB-02**: User can configure API base URL in the web page without rebuilding the static site.
- [x] **WEB-03**: User can deploy or emulate the static review web through Firebase Hosting config without changing sourcing Firestore collection prefixes.

## Future Requirements

- [ ] **CLOUDRUN-01**: User can run Python scraping workers as Cloud Run Jobs after the local-worker ingest contract is proven.
- [ ] **RANK-01**: User can rank AI/CS papers with explicit component scores for recency, citation signal, venue tier, and author influence.
- [ ] **RANK-02**: User can choose between `latest`, `impact`, and `balanced` ranking modes.
- [ ] **EXPORT-01**: User can export ranked AI/CS researchers with top-paper context and contact-quality context retained.
- [ ] **GRAPH-01**: User can project approved entities into Neo4j or another graph read model if traversal becomes a measured product need.
- [ ] **OUTBOUND-01**: User can convert a human-approved entity into an `outbound-candidates` record only after approved contact evidence satisfies the current outbound-required fields.
- [ ] **OUTBOUND-02**: User can trace an outbound candidate back to the approved entity, review label, dedup candidate, evidence records, and source records that produced it.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rewriting Python scrapers into TypeScript | Adds migration risk without improving sourcing correctness |
| Python workers writing directly to Firestore | Bypasses core-service schema, auth, logging, and product write ownership |
| Postgres as v1.2 primary store | Conflicts with schema-document preference and existing Firebase backend |
| MongoDB or another new document DB | Firebase already exists in core-service |
| Neo4j as primary store | Current bottleneck is evidence and human review, not graph traversal |
| Automatic person/entity merge | User explicitly wants every candidate reviewed by a human |
| Full product-grade reviewer/admin UI | v1.2 only includes minimal Firebase-hosted upload/review/approved inspection |
| Ranking from unreviewed identities | Ranking before approved entities would amplify uncertain merge state |

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
| CORE-FOUNDATION-01 | Phase 11 | Validated |
| CORE-01 | Phase 11 | Validated |
| CORE-02 | Phase 11 | Validated |
| CORE-03 | Phase 11 | Validated |
| CORE-04 | Phase 11 | Validated |
| CORE-05 | Phase 11 | Validated |
| API-01 | Phase 12 | Validated |
| API-02 | Phase 12 | Validated |
| API-03 | Phase 12 | Validated |
| API-04 | Phase 12 | Validated |
| PY-01 | Phase 13 | Validated |
| PY-02 | Phase 13 | Validated |
| PY-03 | Phase 13 | Validated |
| DOMAIN-01 | Phase 14 | Validated |
| DOMAIN-02 | Phase 14 | Validated |
| DOMAIN-03 | Phase 14 | Validated |
| DOMAIN-04 | Phase 14 | Validated |
| DOMAIN-05 | Phase 14 | Validated |
| EVIDENCE-01 | Phase 15 | Validated |
| EVIDENCE-02 | Phase 15 | Validated |
| EVIDENCE-03 | Phase 15 | Validated |
| DEDUP-01 | Phase 15 | Validated |
| DEDUP-02 | Phase 15 | Validated |
| DEDUP-03 | Phase 15 | Validated |
| DEDUP-04 | Phase 15 | Validated |
| REVIEW-01 | Phase 16 | Validated |
| REVIEW-02 | Phase 16 | Validated |
| REVIEW-03 | Phase 16 | Validated |
| APPROVE-01 | Phase 16 | Validated |
| APPROVE-02 | Phase 16 | Validated |
| WEB-01 | Phase 17 | Validated |
| WEB-02 | Phase 17 | Validated |
| WEB-03 | Phase 17 | Validated |

**Coverage:**
- Foundation requirements validated: 8
- Milestone v1.2 requirements: 32
- Future requirements deferred: 7

---
*Last updated: 2026-04-15 after local Firebase emulator validation of sourcing review/store POC*
