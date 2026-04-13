<!-- GSD:project-start source:PROJECT.md -->
## Project

**Researcher Pipeline**

This is a standalone `researcher/` pipeline for WeKruit that sources researchers from official
scholarly systems first, then enriches identity and contactability. It links papers, authors,
affiliations, and public contact channels into ranked researcher profiles for recruiting use
without relying on generic web scraping as the primary ingest path.

**Core Value:** Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and
outreach can trust who the researcher is, what they worked on, and how the contact signal was found.

### Constraints

- **Source policy**: Official scholarly APIs and dumps first — generic crawling may only appear after identity resolution.
- **Commercial compliance**: ORCID usage must be validated against credential and terms requirements before it becomes a production contact source.
- **Identity correctness**: Stable identifiers outrank names; ambiguous matches must stay unmerged by default.
- **Repo fit**: Keep the implementation as a flat Python pipeline aligned with the existing repo, not a new framework.
- **Traceability**: Each contact and profile field must preserve source provenance and quality state.
- **Scope discipline**: AI/ML first, broader domains later — no all-domain blast radius in phase 1.
- **Operational resilience**: Per-source rate limits, retries, and replayable raw staging are mandatory from the start.
- **No compatibility layer**: Define one canonical researcher record shape up front instead of maintaining multiple legacy formats.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Main implementation language | Matches the current repo, minimizes setup overhead, and is well-supported by scholarly API clients |
| JSONL | n/a | Raw staging and intermediate exchange | Replayable, diffable, script-friendly, and consistent with the handoff package |
| CSV | n/a | Recruiter-facing export | Lowest-friction downstream handoff format for ranked lists |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `requests` | 2.31+ | HTTP for APIs and secondary enrichment | Default for direct API work and simple authenticated flows |
| `pyalex` | current stable | OpenAlex ingest client | Phase 1 backbone for papers/authors |
| `habanero` | current stable | Crossref REST client | DOI metadata backfill and identifier enrichment |
| `biopython` | current stable | NCBI E-utilities access | Targeted PubMed/PMC enrichment |
| `beautifulsoup4` + `lxml` | current stable | Homepage parsing | Secondary contact enrichment after identity resolution |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `argparse` | CLI surface for pipeline modes | Consistent with existing repo scripts |
| `pytest` or smoke scripts | Basic connector verification | Keep verification pragmatic; phase 1 can start with API smoke coverage |
| environment variables | Secrets and source config | Aligns with the current repo’s flat-script style |
## Installation
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Flat script modules | Heavy orchestration framework | Only if scheduling/state complexity becomes the real bottleneck |
| JSONL intermediate files | Database-first ingest | Only after the normalized model is stable and replay needs exceed file-based staging |
| Direct API clients + `requests` | Browser automation / generic scraping | Only for narrow secondary enrichment where no official source exists |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Generic HTML crawling as phase 1 | Low determinism, brittle schema, higher compliance risk | Official scholarly APIs and dumps |
| UI/dashboard work before core ingest works | Moves effort away from correctness | CSV/JSONL output first |
| Premature frameworkization | The current repo is script-driven and this pipeline still needs schema discovery | Flat Python modules with explicit stage ownership |
## Stack Patterns by Variant
- Prefer the official or established client
- Because it reduces pagination/auth boilerplate and keeps code focused on normalization
- Use `requests` directly with a thin adapter
- Because the pipeline needs conservative, inspectable I/O more than abstraction
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `pyalex` | Python 3.11+ | Foundation for OpenAlex-backed ingest |
| `habanero` | Python 3.11+ | Use polite pool with `mailto` for production calls |
| `biopython` | Python 3.11+ | Keep PubMed use targeted, not core backbone |
## Sources
- OpenAlex Authentication & Pricing — API key required for scale; free snapshot/download path remains available: https://developers.openalex.org/guides/authentication
- Crossref REST API / Access and authentication — no signup required; polite pool uses `mailto` or agent header: https://www.crossref.org/documentation/retrieve-metadata/rest-api/ and https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
- ORCID “Read Data on a Record” tutorial — Public API uses client credentials; member API is the documented path when use exceeds public quotas or conflicts with Public API terms: https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/
- DBLP XML Requests — use API/XML endpoints instead of HTML pages: https://dblp.org/xml/docu/dblpxmlreq.pdf
- NCBI E-utilities — public API to Entrez databases including PubMed and PMC: https://www.ncbi.nlm.nih.gov/books/NBK25501/
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
