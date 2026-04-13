# P9 Supplemental Planning Note

## Accepted Additions

- **Source tiering**: Keep `P0/P1/P2` as a planning lens. `OpenAlex` remains the phase-1 backbone; `ORCID`, `OpenReview`, and `DBLP` stay core-family sources but activate only when their phase contracts are ready.
- **OpenAlex field matrix**: Add an explicit field map for paper, author, institution, concept, venue, and ID coverage so raw staging and canonical normalization are designed against known source-native fields rather than ad hoc extraction.
- **S1..S10 enrichment chain**: Use the supplemental chain as an enrichment checklist and ordering hint after canonical identity is stable, not as permission to collapse ingest, merge, and contact steps into one pass.
- **Library list**: Accept the proposed scholarly-source library set as implementation research input for source adapters, normalization, and export, provided phase plans keep the pipeline flat and script-driven.
- **Script sequence**: Accept the proposed script ordering as a draft operator flow for staged runs, replay, enrichment, and export; align final naming and boundaries to the existing phase model.
- **Domain priorities**: Keep AI/ML first, with explicit priority for AI/CS-oriented signals and later expansion into broader scholarly domains only after the first loop is correct.

## Corrected Assumptions

- **ORCID**: Do not treat ORCID as an anonymous, no-auth, always-safe source. Planning must assume credential review, commercial-use caution, and a gated production contract before ORCID becomes a standard enrichment input.
- **OpenReview**: Do not treat OpenReview as a direct email source. It is useful for identity, venue, profile, and homepage enrichment only.
- **Crossref**: Do not promote Crossref to ingest backbone status. It stays a metadata/DOI backfill source behind `OpenAlex`, not the primary discovery layer.

## Phase Implications

- **Phase 1**: Add the OpenAlex field matrix, source-tier annotations, and the operator script sequence to the ingest planning artifacts, but keep implementation centered on `OpenAlex` plus limited `Crossref` backfill.
- **Phase 2**: Reflect the S1..S10 chain in canonical field provenance and merge ordering so later enrichment steps attach to a stable researcher graph instead of changing identity logic.
- **Phase 3**: Treat `ORCID`, `OpenReview`, and `DBLP` as gated enrichers with explicit contracts, provenance, and quality labeling; do not let the supplemental plan bypass compliance or contact-quality controls.
- **Phase 5**: Use the domain-priority list to choose the first non-AI expansion path rather than reopening the canonical schema.

## Immediate Planning Decisions

- Preserve the current roadmap order: ingest -> canonical identity -> enrichment -> ranking/export -> expansion.
- Carry forward the supplemental plan only where it sharpens source ordering, field coverage, enrichment sequencing, library choices, and domain priority.
- Require future phase plans to document the OpenAlex field matrix and the staged script sequence explicitly.
- Keep `Crossref` scoped to backfill, `OpenReview` scoped to identity/profile enrichment, and `ORCID` behind verified auth/commercial review.
