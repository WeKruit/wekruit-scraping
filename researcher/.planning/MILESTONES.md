# Milestones: Sourcing Pipeline

## v1.0 Researcher Foundation

**Status:** Foundation shipped

**Goal:** Establish the isolated `researcher/` pipeline and official-source ingest backbone for AI/ML-first scholarly discovery.

**Shipped:**
- Standalone `researcher/` module initialized inside `wekruit-scraping`
- OpenAlex-led official ingest and Crossref DOI backfill
- Replayable raw staging contracts and run manifests
- Initial contact-enrichment POC proving ORCID/homepage pathways can surface real public contact signals

**Did not yet close:**
- Durable product storage
- Cross-source review queue
- Approved entity groups
- Explainable ranking and recruiter-facing export

## v1.1 AI/CS Corpus Gate

**Status:** Paused after Phase 6

**Goal:** Gate AI/CS papers before ranking so downstream ranking does not start from broad concept-search noise.

**Shipped:**
- AI/CS venue-tier asset keyed by exact OpenAlex source IDs
- Strict corpus gate over staged OpenAlex works
- Include/exclude decision logs with reason codes
- Append-only rerun semantics and local POCs

**Paused because:**
- Ranking before human-reviewed identity merge would amplify uncertain researcher records.
- The next critical path is a shared sourcing backend, not another researcher-only data file.

## v1.2 Sourcing Service And Human Review Foundation

**Status:** Current

**Goal:** Turn `wekruit-scraping` outputs into a shared schema-first sourcing service backed by the existing Firebase/Core Functions stack.

**Target scope:**
- Core-service `sourcing` service following the existing `matching` / `outbound` file-management pattern
- Firestore collections and zod schemas for source runs, source records, extracted signals, candidate groups, review labels, and approved entities
- Cloud Storage pointer contract for large raw payloads
- HTTP ingest API in core-service
- Python ingest client in `wekruit-scraping`
- Local Python workers continue to execute scraping and upload source records through the core-service API
- Researcher four-source integration: OpenAlex, ORCID, DBLP, OpenReview
- Existing scraping domains can emit the same `sourceRecord` contract: `devpost`, `github`, and future sources
- Candidate grouping with explicit reasoning and mandatory human review

**Explicitly not in scope:**
- Rewriting Python scrapers into TypeScript
- Letting Python workers write directly to Firestore
- Postgres as the v1.2 primary store
- MongoDB or another new document database
- Neo4j or graph database as primary store
- Automatic merge without human approval
- Full reviewer UI before the API/CSV review loop is proven
- Ranking or recruiter outreach exports before approved entities exist

---
*Last updated: 2026-04-15 after reframing v1.2 as shared sourcing service*
