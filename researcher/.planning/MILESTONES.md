# Milestones: Researcher Pipeline

## v1.0 Foundation

**Status:** Foundation shipped

**Goal:** Establish the isolated `researcher/` pipeline and official-source ingest backbone for AI/ML-first scholarly discovery.

**Shipped:**
- Standalone `researcher/` module initialized inside the repo
- OpenAlex-led official ingest and Crossref DOI backfill
- Replayable raw staging contracts and run manifests
- Initial contact-enrichment POC proving ORCID/homepage pathways can surface real public contact signals

**Did not yet close:**
- Durable source-profile storage
- Human-reviewed identity merge queue
- Approved researcher groups
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
- The next critical path is four-source profile ingest, durable storage, candidate reasoning, and human labeling.

## v1.2 Four-Source Human Review Merge Foundation

**Status:** Current

**Goal:** Build four independently triggerable researcher-profile pipelines and a human-reviewed merge workflow with explicit reasoning for every candidate group.

**Target scope:**
- Durable Postgres storage for source runs, source profiles, extracted signals, candidate groups, review labels, and approved people
- Four source-profile pipelines: OpenAlex, ORCID, DBLP, and OpenReview
- Derived homepage/GitHub/email signal extraction from public profile URLs
- Candidate grouping by evidence, with no automatic person merge
- Human review queue showing why profiles may belong to the same person
- Label ingest for `same_person`, `not_same_person`, and `unsure`
- Approved researcher-group export after human review

**Explicitly not in scope:**
- Neo4j or graph database as primary store
- NoSQL as the primary identity/review store
- Automatic merge without human approval
- Ranking or recruiter outreach exports before approved researcher groups exist

---
*Last updated: 2026-04-15 after starting milestone v1.2 for four-source human-reviewed merge*
