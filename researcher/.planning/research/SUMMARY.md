# Project Research Summary

**Project:** Researcher Pipeline
**Domain:** Academic researcher sourcing pipeline
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Executive Summary

This project is an internal sourcing pipeline, not a consumer product. Its job is to discover
researchers from official scholarly systems, link those researchers to papers and institutions,
attach public contact signals conservatively, and export ranked recruiter-usable outputs. The
correct build order is structured ingest first, identity correctness second, contact enrichment
third, and ranking/export only after the merged profile model is stable.

The recommended approach is to keep the implementation flat and script-driven, matching the current
repo. Use OpenAlex as the ingest backbone, Crossref as metadata backfill, OpenReview and DBLP as
AI/CS enrichers, and keep ORCID behind a compliance-aware enrichment gate rather than assuming it
is a frictionless public-email source. Generic crawling should stay a secondary enrichment tactic,
not the foundation.

The biggest risks are identity mistakes, ORCID/commercial-usage assumptions, and ranking drifting
into academic prestige instead of sourcing usefulness. Those risks directly shape the phase order.

## Key Findings

### Recommended Stack

The shortest path is Python 3.11+ with flat script stages, JSONL staging, CSV/JSONL export, and
thin adapters around official scholarly APIs. This matches the current repo better than introducing
an orchestration framework or database-first design.

**Core technologies:**
- Python 3.11+: pipeline implementation
- JSONL: replayable raw and intermediate staging
- CSV: recruiter-facing export

### Expected Features

**Must have (table stakes):**
- Official-source ingest with replayable raw staging
- Canonical researcher profile and conservative identity merge
- Provenance-aware contact enrichment
- Ranked recruiter export

**Should have (competitive):**
- AI/ML-first presets for venues, concepts, and keywords
- Cross-source identity resolution across OpenAlex, OpenReview, DBLP, and ORCID

**Defer (v2+):**
- Broad domain families before the AI/ML loop is stable
- Commercial waterfall and operator UI before the profile quality is proven

### Architecture Approach

The architecture should be staged and file-backed: source adapters → raw staging → canonical
normalization and identity merge → contact enrichment → ranking/export. The merge layer is the
core correctness boundary.

**Major components:**
1. Source adapters — source-specific fetch and parse logic
2. Raw staging — replayable source-native records and query metadata
3. Canonical merge layer — normalized profile model and conservative identity linking
4. Enrichment layer — public contact and affiliation signals with provenance
5. Ranking/export layer — recruiter-facing scored outputs

### Critical Pitfalls

1. **Wrong ORCID assumptions** — treat credential and commercial-usage review as a hard gate
2. **Over-merging identities** — stable IDs first, unresolved ambiguity left open
3. **Contact-before-identity** — enrich only after canonical merge
4. **Prestige-only ranking** — score for recruiting usefulness, not only citations
5. **Too-early domain expansion** — lock AI/ML first, then expand

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Official AI Ingest Foundation
**Rationale:** establishes deterministic source truth
**Delivers:** OpenAlex/Crossref-backed AI/ML raw staging
**Addresses:** ingest requirements and replayability
**Avoids:** crawl-first architecture

### Phase 2: Canonical Schema And Identity Graph
**Rationale:** correctness gate before enrichment
**Delivers:** normalized researcher/paper/contact model and conservative merge rules
**Uses:** flat Python transforms and stable-ID precedence
**Implements:** canonical merge component

### Phase 3: Contact Enrichment And Quality
**Rationale:** once identities are stable, public contact signals can attach safely
**Delivers:** ORCID/profile/homepage/PubMed enrichment with quality labels

### Phase 4: Ranking And Recruiter Export
**Rationale:** output quality matters only after profile completeness is real
**Delivers:** scoring and recruiter-facing exports

### Phase 5: Domain Expansion And Source Hardening
**Rationale:** schema and controls should be proven before adding new source families
**Delivers:** broader-domain support on the same profile model

### Phase Ordering Rationale

- Identity correctness must precede contact enrichment
- Contact enrichment must precede ranking
- AI/ML must precede broad domain rollout
- Compliance-sensitive sources must be validated before being treated as production inputs

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** ORCID credential/commercial path and exact OpenReview/DBLP integration shape
- **Phase 5:** which non-AI source family should be the first expansion target

Phases with standard patterns:
- **Phase 1:** flat ingest and raw staging
- **Phase 2:** canonical schema and stable-ID-first merge design

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Directly aligned to repo shape and official source constraints |
| Features | MEDIUM | Clear for AI-first loop; broader-domain expansion still needs source-specific choice |
| Architecture | HIGH | Phase order is dictated by correctness and source trust |
| Pitfalls | HIGH | Main risks are already visible before implementation |

**Overall confidence:** MEDIUM

### Gaps to Address

- ORCID production/commercial usage path must be explicitly resolved before implementation
- Semantic Scholar integration should be validated as supplemental enrichment, not assumed critical-path ingest
- OpenReview live API surface should be verified during phase planning, not assumed from historical examples alone

## Sources

### Primary (HIGH confidence)
- OpenAlex developer docs
- Crossref REST API documentation
- ORCID record-reading tutorial
- DBLP XML Requests documentation
- NCBI E-utilities documentation

### Secondary (MEDIUM confidence)
- Provided handoff package under `researcher/reference/p9-research-pipeline/`
- Current repo patterns from `devpost/` and `github/`

---
*Research completed: 2026-04-13*
*Ready for roadmap: yes*
