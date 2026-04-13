# Researcher Pipeline Brief

## Objective

Build a mature sourcing pipeline for AI-first and cross-domain researchers that can:

- discover papers and authors from official scholarly sources
- resolve researcher identity conservatively across multiple databases
- enrich public contact channels with provenance and quality labels
- rank researchers for recruiting and export recruiter-friendly output

## Why This Exists

The current repository already has `devpost/` and `github/` pipelines for builder talent.
What is missing is a third pipeline for researcher talent, where the core objects are papers,
authors, institutions, and reachable public contact paths rather than hackathon projects or
GitHub repos.

## Backbone Source Strategy

Official scholarly sources first:

- OpenAlex — paper, author, affiliation, citation backbone
- Crossref — DOI metadata and affiliation/identifier backfill
- OpenReview — AI/ML profile enrichment
- DBLP — CS author/profile enrichment
- ORCID — identity, employment, homepage, and credentialed public-record access
- PubMed / PMC — targeted biomedical contact and metadata enrichment
- Semantic Scholar — supplemental citation and external-ID enrichment, not primary ingest

## Non-Goals

- No generic crawl-first architecture
- No login bypasses or gated-source scraping
- No product UI or dashboard before the sourcing loop works
- No broad all-discipline rollout before the AI/ML path works end to end

## Implementation Shape

Shortest path:

1. official-source ingest
2. raw staging
3. canonical schema + identity merge
4. contact enrichment + quality labeling
5. ranking + export
6. broader domain expansion
