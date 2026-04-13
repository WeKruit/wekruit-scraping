# Researcher Pipeline

This directory is the third sourcing pipeline in the repo, alongside `devpost/` and `github/`.
It is being initialized as a standalone project for discovering researchers from official scholarly
data sources, linking them to papers and affiliations, and producing ranked, provenance-aware
contact candidates for WeKruit.

## What Lives Here

- `.planning/` — authoritative project docs created through the GSD initialization flow
- `docs/research_source_matrix_v2.xlsx` — standalone comparison sheet from the provided handoff
- `reference/p9-research-pipeline/` — preserved handoff package from `researcher_scraping.zip`

## Important Corrections To The Reference Package

The preserved handoff package is useful, but it should not be treated as production-ready without
review. Two assumptions need correction before implementation work starts:

1. ORCID should not be treated as a no-auth, always-safe source for a commercial pipeline.
   The current ORCID record-reading tutorial requires client credentials for Public API access,
   and ORCID documents that Public API terms are limited to non-commercial use cases. Commercial
   expert-finder usage may require Member API review and explicit credential planning.
2. OpenReview should be treated as a profile and homepage enrichment source, not an email source.
   It is useful for AI/ML identity resolution, but not as a reliable direct-contact database.

## Working Rule

The backbone for this pipeline is official scholarly APIs and dumps first. Generic web crawling is
allowed only as a secondary enrichment step after identity has already been resolved from trusted
sources.
