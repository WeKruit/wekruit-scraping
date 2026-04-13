# Feature Research

**Domain:** Academic researcher sourcing pipeline
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Official-source ingest | The pipeline must start from trusted scholarly sources | MEDIUM | Backbone must not be crawl-first |
| Raw staging and replay | Sourcing data must be auditable and re-runnable | MEDIUM | JSONL staging is sufficient initially |
| Canonical researcher profile | Downstream users need one merged profile per person | HIGH | The identity model is the correctness gate |
| Provenance-aware contact enrichment | Contact fields must show where they came from | HIGH | Prevents false confidence in outreach |
| Ranked export | Recruiting needs prioritized output, not raw corpora | MEDIUM | Ranking must stay aligned to recruiting, not prestige only |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI/ML venue presets | Fast initial wedge for WeKruit’s highest-value use case | LOW | Keeps first loop narrow and testable |
| Cross-source identity merge | Better researcher resolution than relying on a single database | HIGH | Stable IDs first, names last |
| Domain-ready schema | Lets the pipeline expand beyond AI/ML without re-architecture | MEDIUM | Expansion comes after AI-first validation |
| Contact quality labeling | Makes outreach safer by separating verified, public, and speculative channels | MEDIUM | Important for recruiter trust |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Generic crawl-first sourcing | Feels universal and fast | Poor identity quality, brittle extraction, higher compliance risk | Official-source backbone plus secondary enrichment |
| Aggressive fuzzy merge | Increases record counts quickly | Easily merges different researchers with similar names | Stable-ID-first merge with unresolved leftovers |
| Prestige-only ranking | Easy to explain using citation count | Misaligns with recruiting relevance | Blend citations with recency, topical fit, and contact quality |
| Broad domain rollout immediately | Feels like faster coverage | Multiplies schema drift before the AI loop is correct | AI/ML first, then adjacent domains |

## Feature Dependencies

```text
Official-source ingest
    └──requires──> raw staging
                         └──requires──> canonical schema
                                              └──requires──> identity merge
                                                                  └──requires──> contact enrichment
                                                                                      └──requires──> ranked export

Domain expansion ──requires──> canonical schema + stable merge rules
```

### Dependency Notes

- **Ranked export requires contact enrichment:** recruiter output is lower value if profiles are not contactable.
- **Contact enrichment requires identity merge:** otherwise contacts are assigned to the wrong person.
- **Domain expansion requires schema stability:** otherwise each new source family changes the meaning of the profile model.

## MVP Definition

### Launch With (v1)

- [ ] OpenAlex-led AI/ML ingest with replayable raw staging
- [ ] Canonical paper/researcher/contact schema
- [ ] Stable-ID-first identity merge
- [ ] ORCID plus AI/CS enrichment path with provenance
- [ ] Ranked CSV/JSONL recruiter export

### Add After Validation (v1.x)

- [ ] Targeted PubMed/PMC enrichment for biomedical researchers
- [ ] Better contact quality states and verification workflow
- [ ] Additional ranking controls tuned for recruiting workflows

### Future Consideration (v2+)

- [ ] Wider domain families beyond AI/ML and first adjacent domains
- [ ] Commercial waterfall integrations after the core profile quality is proven
- [ ] Operator/reporting UI if a real ops need emerges

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Official-source ingest | HIGH | MEDIUM | P1 |
| Canonical schema + merge | HIGH | HIGH | P1 |
| Contact provenance | HIGH | MEDIUM | P1 |
| Ranked export | HIGH | MEDIUM | P1 |
| AI/ML presets | MEDIUM | LOW | P2 |
| Domain expansion | MEDIUM | MEDIUM | P2 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Paper coverage | OpenAlex-style graph coverage | Crossref-style DOI metadata coverage | Use both, but keep one ingest backbone |
| AI profile signal | OpenReview-style venue profiles | DBLP-style CS publication graph | Combine them only after identity is stable |
| Contact signal | ORCID/public profile hints | Homepage/corresponding-author hints | Keep contact quality labeled, not binary |

## Sources

- Official source docs listed in `STACK.md`
- Provided handoff package under `researcher/reference/p9-research-pipeline/`
- Existing repo patterns from `devpost/` and `github/`

---
*Feature research for: academic researcher sourcing pipeline*
*Researched: 2026-04-13*
