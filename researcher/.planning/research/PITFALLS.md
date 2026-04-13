# Pitfalls Research

**Domain:** Academic researcher sourcing pipeline
**Researched:** 2026-04-13
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Treating ORCID as a frictionless public-email source

**What goes wrong:**
The pipeline is built around direct ORCID calls and public-email expectations that do not hold for commercial usage or real-world coverage.

**Why it happens:**
Older examples and informal scripts make ORCID look like a simple public endpoint.

**How to avoid:**
Treat ORCID as a gated enrichment source from day one. Validate credential mode, terms, and actual public-field coverage before making it part of the production contact path.

**Warning signs:**
- ORCID is assumed to need no credentials
- commercial usage review is missing
- contact coverage forecasts depend heavily on ORCID email

**Phase to address:**
Phase 3

---

### Pitfall 2: Over-merging people with similar names

**What goes wrong:**
Different researchers get merged into one profile because name matching outruns identifier quality.

**Why it happens:**
Researcher data is full of homonyms, initials, institution changes, and venue-specific profile variance.

**How to avoid:**
Use stable identifiers first, institution/name only as secondary evidence, and leave ambiguous profiles unresolved instead of forcing a merge.

**Warning signs:**
- merge rules start with names
- one profile has incompatible institutions or fields
- OpenReview/DBLP/PubMed records collapse into suspiciously broad people

**Phase to address:**
Phase 2

---

### Pitfall 3: Letting contact enrichment drive identity logic

**What goes wrong:**
The pipeline chases emails and homepages before identity is stable, causing wrong attachments and low trust.

**Why it happens:**
Recruiting pressure makes direct contact feel like the main output.

**How to avoid:**
Make identity resolution the gate. Contact enrichment happens only on merged profiles, and every contact candidate keeps provenance and quality state.

**Warning signs:**
- email scraping is planned before canonical merge
- contact source determines the profile shape
- enrichment code mutates identity keys

**Phase to address:**
Phase 3

---

### Pitfall 4: Using prestige metrics as the ranking objective

**What goes wrong:**
The ranking becomes an academic leaderboard instead of a recruiter tool.

**Why it happens:**
Citations and h-index proxies are easy to compute and easy to justify.

**How to avoid:**
Blend research signal with topical fit, recency, completeness, and contact quality. Keep the recruiting objective explicit.

**Warning signs:**
- score is mostly citations
- recent/high-fit researchers rank below unreachable famous profiles
- export is optimized for “top academics” rather than “actionable sourcing”

**Phase to address:**
Phase 4

---

### Pitfall 5: Expanding domains before the AI/ML loop is stable

**What goes wrong:**
Source-specific edge cases multiply before the core schema and merge model are proven.

**Why it happens:**
Coverage sounds more valuable than correctness in early discussions.

**How to avoid:**
Lock AI/ML as the first wedge and treat cross-domain expansion as a later phase on the same schema.

**Warning signs:**
- new source families are added before phase 2 or 3 is complete
- schema fields keep changing to satisfy one new connector
- merge rules become source-specific exceptions

**Phase to address:**
Phase 5

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Merge while ingesting | Faster first script | Impossible to replay/debug source truth | Never |
| Crawl homepages broadly before identity resolution | Higher raw email counts | Wrong-person contacts and noisy outputs | Never |
| Skip provenance on contact fields | Faster export schema | No one can trust the output later | Never |
| Defer retry/rate-limit handling | Faster prototype | Brittle reruns and inconsistent coverage | Only for disposable one-off tests |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAlex | Treating search as the only path | Use filtered ingest and keep query metadata |
| Crossref | Anonymous/public use without identification | Use polite identification and limit it to metadata backfill |
| ORCID | Assuming Public API is production-safe for commercial use | Treat credentials and ToS review as an implementation gate |
| DBLP | Scraping HTML pages | Use DBLP API/XML/JSON endpoints |
| PubMed | Using it as a universal backbone | Keep it targeted to biomedical expansion or corresponding-author use cases |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unbounded source pagination | Runs slow or time out unpredictably | Add explicit query slices, cutoffs, and checkpoints | Early, once source coverage expands |
| Contact enrichment on unresolved identities | Duplicate or conflicting contacts | Run enrichment after canonical merge | Immediately |
| Ranking over raw staged data | Inconsistent exports | Rank only merged profiles | Immediately |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Treating public researcher data as unbounded commercial free use | Terms/compliance exposure | Validate each source’s commercial usage expectations |
| Storing secrets inline in scripts | Credential leakage | Use environment/config boundaries |
| Scraping gated or personal pages broadly | Privacy and compliance issues | Limit enrichment to public, researcher-owned or official-source fields |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Export without provenance columns | Recruiters cannot trust the source of a contact | Include source and quality state in every export |
| Export without domain or relevance context | Lists are hard to triage | Surface topic/venue/relevance cues alongside score |
| Binary “has email / no email” output | Hides signal quality differences | Use quality states such as public, homepage, verified, unknown |

## "Looks Done But Isn't" Checklist

- [ ] **OpenAlex ingest:** query metadata and source provenance are stored with staged records
- [ ] **Identity merge:** ambiguous profiles remain unresolved instead of being force-merged
- [ ] **Contact enrichment:** every contact field carries source and quality state
- [ ] **Ranking:** scoring aligns with recruiting usefulness, not only academic prestige
- [ ] **Cross-domain expansion:** uses the same canonical schema without source-specific hacks

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong ORCID assumptions | MEDIUM | Rework source contract, credential model, and forecast |
| Bad identity merges | HIGH | Rebuild merged profiles from raw staging with corrected rules |
| Prestige-only ranking | LOW | Reweight score and regenerate exports from merged profiles |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ORCID commercial/credential mismatch | Phase 3 | Document source contract before enabling ORCID production enrichment |
| Name-based over-merge | Phase 2 | Review merge rules and ambiguous cases before enrichment |
| Contact-before-identity | Phase 3 | Ensure enrichment input is merged profiles only |
| Prestige-only ranking | Phase 4 | Verify score factors include relevance/contact quality |
| Too-early domain expansion | Phase 5 | Expand only after AI/ML export loop is stable |

## Sources

- ORCID record-reading tutorial
- DBLP XML Requests documentation
- OpenAlex developer docs
- Crossref REST API documentation
- NCBI E-utilities documentation
- Provided handoff package and current repo comparison

---
*Pitfalls research for: academic researcher sourcing pipeline*
*Researched: 2026-04-13*
