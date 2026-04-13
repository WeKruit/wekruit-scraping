# Researcher Pipeline

## What This Is

This is a standalone `researcher/` pipeline for WeKruit that sources researchers from official
scholarly systems first, then enriches identity and contactability. It links papers, authors,
affiliations, and public contact channels into ranked researcher profiles for recruiting use
without relying on generic web scraping as the primary ingest path.

## Core Value

Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and
outreach can trust who the researcher is, what they worked on, and how the contact signal was found.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Build the researcher pipeline as a third isolated repo module, separate from `devpost/` and `github/`.
- [ ] Use official scholarly APIs and dumps as the primary ingest path, starting with AI/ML-focused coverage.
- [ ] Preserve source-native raw paper and author records so upstream data can be replayed and audited.
- [ ] Normalize papers, researchers, affiliations, and contacts into one canonical record shape.
- [ ] Merge identities conservatively using stable IDs first and names only as a late signal.
- [ ] Enrich public contact paths with provenance and quality labels instead of treating any source as guaranteed-email truth.
- [ ] Rank and export recruiter-usable researcher lists after identity and contact quality are established.
- [ ] Expand beyond AI/ML only after the AI-first loop works end to end.

### Out of Scope

- Generic web crawling as the backbone — official scholarly APIs are the primary ingest path.
- UI dashboards or operator consoles — not needed before the data loop is correct.
- Social/profile scraping unrelated to scholarly identity resolution — increases noise without solving the core problem.
- Closed-platform or login-gated scraping — conflicts with source-policy and compliance goals.
- “Guaranteed direct email” as a product promise — contact is an enrichment output with varying quality.

## Context

The root repository already contains two sourcing pipelines with different shapes: `devpost/` is a
source-specific scraper with a curated target list, while `github/` is a staged, multi-source
pipeline with centralized config, incremental output, and orchestration scripts. `researcher/`
should follow the cleaner parts of the `github/` model: one config surface, one orchestrator, one
aggregation boundary, and isolated source adapters.

The provided `researcher_scraping.zip` has been preserved under `researcher/reference/` as a
reference package, along with the spreadsheet under `researcher/docs/`. It is useful, but not the
authoritative design. Two assumptions from that handoff were specifically corrected during project
initialization:

- ORCID should not be treated as an anonymous/no-auth source for a commercial pipeline.
- OpenReview should be treated as identity/homepage enrichment, not as a direct email source.

The initial rollout is AI/ML first because that is the highest-signal wedge for WeKruit. The
architecture, schema, and source ordering should remain broad enough to support adjacent domains
without redesigning the core merge model.

The supplemental P9 source plan is useful as a source-tiering and enrichment checklist, not as an
authoritative source contract. Its biggest contribution is clarifying which systems belong in the
core scholarly graph versus later expansion. Its main corrections are around ORCID and rate-limit
assumptions: production ORCID usage is not a no-auth anonymous path for this pipeline, and exact
per-source quotas must come from current official docs during phase planning instead of being copied
from older examples.

## Constraints

- **Source policy**: Official scholarly APIs and dumps first — generic crawling may only appear after identity resolution.
- **Commercial compliance**: ORCID usage must be validated against credential and terms requirements before it becomes a production contact source.
- **Identity correctness**: Stable identifiers outrank names; ambiguous matches must stay unmerged by default.
- **Repo fit**: Keep the implementation as a flat Python pipeline aligned with the existing repo, not a new framework.
- **Traceability**: Each contact and profile field must preserve source provenance and quality state.
- **Scope discipline**: AI/ML first, broader domains later — no all-domain blast radius in phase 1.
- **Operational resilience**: Per-source rate limits, retries, and replayable raw staging are mandatory from the start.
- **No compatibility layer**: Define one canonical researcher record shape up front instead of maintaining multiple legacy formats.
- **Tiered sources, staged activation**: A source can be core (`P0`) for the overall program without being a phase-1 blocking ingest dependency.
- **Official-doc precedence**: If a handoff note conflicts with live official docs, planning follows the official docs.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `researcher/` is an isolated pipeline | The root repo already treats sourcing domains as separate folders | — Pending |
| OpenAlex is the ingest backbone | Broad paper/author/affiliation coverage with stable identifiers and bulk/snapshot options | — Pending |
| Crossref is metadata backfill, not backbone | Strong DOI and affiliation metadata, but not the best primary discovery layer | — Pending |
| OpenReview and DBLP are AI/CS enrichers | Stronger profile signal for AI/ML and CS than general-purpose sources | — Pending |
| Source tiers use `P0/P1/P2`, but phase order still gates activation | `P0` identifies core source families, not “implement all at once in phase 1” | — Pending |
| ORCID stays behind a verified source contract | Official docs require client credentials for API use and constrain Public API usage; public fields are not a blanket direct-email guarantee | — Pending |
| Contact is an enrichment layer | Contact quality varies by source and must not distort identity resolution | — Pending |
| AI/ML is the first domain slice | Highest immediate value and cleanest place to validate the architecture | — Pending |
| Reference package stays under `reference/` | Preserves prior work without forcing unreviewed code into the mainline | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after P9 supplemental source-plan absorption*
