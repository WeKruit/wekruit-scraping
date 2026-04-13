# Phase 1 Context: Official AI Ingest Foundation

## Goal

Deliver a replayable AI/ML ingest path from official scholarly sources with source-native raw
staging and source-aware run metadata. Phase 1 stops at ingest foundation; it does not normalize
into the canonical researcher profile yet.

## Sources Read

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/research/SUMMARY.md`
- `reference/p9-research-pipeline/README.md`
- `reference/p9-research-pipeline/scripts/s1_openalex_fetch.py`
- `reference/p9-research-pipeline/schemas/unified_schema.py`

## Decisions

- **D-01**: OpenAlex is the only primary Phase 1 ingest backbone. Phase 1 discovery starts from
  OpenAlex works/authorships, not from Crossref or generic crawling.
- **D-02**: Crossref is Phase 1 metadata backfill only. It may enrich DOI-backed records that were
  already discovered through OpenAlex, but it must not become a second primary discovery path.
- **D-03**: Raw staging and run metadata are mandatory in Phase 1. Every source fetch must produce
  source-native raw envelopes plus a run manifest that supports replay and audit.
- **D-04**: AI/ML presets are mandatory in Phase 1 for all three slice types: venue, concept, and
  keyword.
- **D-05**: Keep the implementation flat and repo-aligned. Use simple Python modules, argparse
  CLIs, file-backed state, and JSONL staging. Do not introduce a workflow framework, service
  layer, database, or UI.
- **D-06**: Phase 1 ends at official ingest foundation. Canonical identity merge, contact
  enrichment, ranking, export, and domain expansion stay in later phases.
- **D-07**: Generic crawling is not allowed in Phase 1, even as a fallback path for missing OpenAlex
  or Crossref fields.

## Deferred Ideas

- ORCID, OpenReview, DBLP, PubMed, Semantic Scholar, or homepage enrichment
- Canonical researcher schema implementation and identity merge logic
- Contact quality labeling, recruiter ranking, or CSV/JSONL export logic
- Non-AI domain expansion
- Dashboard, operator UI, background workers, databases, or orchestration frameworks

## Claude's Discretion

- Use minimal module names under the `researcher/` project root as long as they stay explicit about
  source and responsibility.
- Prefer stdlib data structures or lightweight dataclasses for Phase 1 run/staging contracts unless
  tests become materially worse without a validation library.
- Keep automated verification fixture-driven or monkeypatched. Do not make live API calls part of
  the default test path.
- Reuse the useful shape of the reference package where it helps, but do not inherit its incorrect
  ORCID assumptions or its broader multi-source scope.

## Phase 1 Plan Mapping

- `01-01-PLAN.md`: config surface, source registry, run metadata, and raw staging contract
- `01-02-PLAN.md`: OpenAlex-led ingest and AI/ML query presets
- `01-03-PLAN.md`: Crossref metadata backfill and replay/incremental controls

## Phase Boundaries

### In Scope

- OpenAlex-backed AI/ML raw ingest
- Crossref DOI metadata backfill against staged OpenAlex works
- Source registry, run manifest, raw staging envelope, replay/incremental controls
- Fixture-backed verification for OpenAlex and Crossref adapters

### Out Of Scope

- Generic crawling
- Any Phase 2+ schema/merge/enrichment/ranking work
- Production scheduling, queues, service hosting, or dashboards

## Expected Project-Root Shape After Phase 1

- `requirements.txt`
- `config/settings.example.py`
- `config/source_registry.py`
- `pipeline/run_context.py`
- `pipeline/raw_staging.py`
- `pipeline/incremental_state.py`
- `presets/ai_ml.py`
- `sources/openalex.py`
- `sources/crossref.py`
- `scripts/s1_openalex_fetch.py`
- `scripts/s1_crossref_backfill.py`
- `tests/` for phase-1 verification
- `data/runs/<run_id>/...` and `data/state/...` for runtime artifacts only

## Notes From Reference Material

- The preserved `reference/p9-research-pipeline/` is useful for CLI shape and source naming, but it
  is not authoritative.
- `reference/.../schemas/unified_schema.py` informs future naming and data expectations, but Phase 1
  should only preserve raw source-native data and run metadata, not implement the Phase 2 canonical
  merge model early.
