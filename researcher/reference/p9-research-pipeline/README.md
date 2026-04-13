# P9 — Academic Researcher Sourcing Pipeline

> **Goal**: Build a data pipeline to discover AI/ML and cross-domain researchers,
> extract their publications, and obtain verified contact information at scale.
>
> **Owner**: Adam (WeKruit CTO)
> **Status**: Research & scaffolding complete, ready for implementation
> **Target**: Feed into WeKruit's AI headhunting/placement pipeline

---

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌─────────────┐
│  S1: OpenAlex │───▶│ S9: Merge &  │───▶│ S10: Score &  │───▶│  Output:    │
│  S3: OpenReview│   │   Deduplicate │   │   Rank        │   │  ranked     │
│  S4: DBLP     │   │   (unified    │   │   (h-index,   │   │  profiles   │
│  S7: Sem.Sch. │   │    schema)    │   │   recency)    │   │  .csv/.json │
└──────┬────────┘   └──────┬───────┘   └───────────────┘   └─────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌───────────────┐
│ S2: ORCID     │   │ S5: Homepage  │   │ S8: NeverBounce│
│   (email,     │   │   Email       │   │   (verify)     │
│   institution)│   │   Extract     │   │               │
│ S6: PubMed    │   └──────────────┘   └───────────────┘
│   (corr.email)│
└──────────────┘
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy config and add your API keys
cp config/settings.example.py config/settings.py
# Edit config/settings.py with your keys

# 3. Test all API connections
python tests/test_apis.py

# 4. Run pipeline (example: AI/ML researchers from ICLR)
python scripts/s1_openalex_fetch.py --concept "artificial intelligence" --venue "ICLR" --since 2023
python scripts/s2_orcid_enrich.py --input data/authors.jsonl
python scripts/s9_merge_pipeline.py --input-dir data/
python scripts/s10_score_rank.py --input data/merged_profiles.jsonl --output data/ranked.csv
```

## Data Sources — Priority Map

| Priority | Source | Library | What we get | Auth needed? |
|----------|--------|---------|-------------|--------------|
| **P0** | OpenAlex | `pyalex` | Paper/author/institution/citation graph | Free API key (2026+) |
| **P0** | ORCID | `requests` | Email, homepage, employment history | None (public API) |
| **P0** | OpenReview | `openreview-py` | AI/ML profiles, homepage, dblp link | None |
| **P0** | DBLP | `requests` | CS author pages, homepage, coauthors | None |
| **P0** | Crossref | `habanero` | DOI metadata, ORCID, affiliation | None (mailto header) |
| **P1** | Semantic Scholar | `semanticscholar` | Citations, embeddings, external IDs | Free API key |
| **P1** | PubMed | `biopython` | Corresponding author email (bio only) | Free API key |
| **P1** | arXiv | `requests` | Latest preprints | None |
| **P2** | Europe PMC | `requests` | Bio + European papers | None |
| **P2** | Papers w/ Code | `requests` | Code/benchmark signals | None |

## Registration Checklist

| Service | Action | Time | Link |
|---------|--------|------|------|
| OpenAlex | Get free API key | 2 min | https://openalex.org/users/me |
| Crossref | Just add mailto header | 0 min | — |
| Semantic Scholar | Request free API key | 5 min | https://www.semanticscholar.org/product/api#api-key |
| PubMed E-Utils | Get NCBI API key | 5 min | https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/ |
| ORCID | None needed (public API) | 0 min | — |
| DBLP | None needed | 0 min | — |
| OpenReview | None needed | 0 min | — |
| NeverBounce | Register + credit card | 10 min | https://app.neverbounce.com/register |
| ContactOut | Already have (WeKruit) | 0 min | — |
| PDL | Already have (WeKruit) | 0 min | — |

## Script Inventory

| # | Script | Priority | Input | Output | Description |
|---|--------|----------|-------|--------|-------------|
| S1 | `s1_openalex_fetch.py` | P0 | CLI args (concept/venue/keyword) | `papers.jsonl`, `authors.jsonl` | Bulk fetch papers + authors via pyalex |
| S2 | `s2_orcid_enrich.py` | P0 | `authors.jsonl` | `orcid_enriched.jsonl` | ORCID public API → email, homepage, employment |
| S3 | `s3_openreview_fetch.py` | P0 | CLI args (venue) | `or_profiles.jsonl` | OpenReview profiles + paper metadata |
| S4 | `s4_dblp_lookup.py` | P1 | `authors.jsonl` | `dblp_enriched.jsonl` | DBLP author → homepage + publications |
| S5 | `s5_homepage_email.py` | P1 | URLs from S2/S3/S4 | `homepage_emails.jsonl` | Scrape homepage for email |
| S6 | `s6_pubmed_corr_email.py` | P1 | PMID list | `pubmed_emails.jsonl` | PubMed XML → corresponding author email |
| S7 | `s7_semantic_scholar.py` | P1 | DOI/S2-ID list | `s2_enriched.jsonl` | S2 → citations, externalIds, homepage |
| S8 | `s8_email_verify.py` | P1 | All emails | `verified_emails.jsonl` | NeverBounce verification |
| S9 | `s9_merge_pipeline.py` | P0 | All .jsonl outputs | `merged_profiles.jsonl` | Dedupe + merge by ORCID/name/inst |
| S10 | `s10_score_rank.py` | P1 | `merged_profiles.jsonl` | `ranked_researchers.csv` | Score by citations, recency, h-index proxy |

## Author → Email Pipeline (Expected Coverage)

```
Step 1: OpenAlex → author_id, orcid, institution         → baseline
Step 2: ORCID API → public email                          → 15-25% hit
Step 3: ORCID/OpenReview/DBLP → homepage URL              → collect URLs
Step 4: Homepage scrape → email                           → +10-15%
Step 5: PubMed XML → corresponding author email (bio)     → +20-30% (bio only)
Step 6: Institution email pattern inference                → +10-15%
Step 7: Commercial waterfall (ContactOut/PDL)              → +15-25%
Step 8: NeverBounce verification                           → filter invalid
────────────────────────────────────────────────────────────
Expected total: 60-80% verified email coverage
```

## Unified Data Schema

See `schemas/unified_schema.py` for full Pydantic models.

**Researcher Profile** (final merged output):
```json
{
  "researcher_id": "wk_r_abc123",
  "name": "Yann LeCun",
  "openalex_id": "A5073352938",
  "orcid": "0000-0002-3192-2550",
  "dblp_pid": "l/YannLeCun",
  "s2_id": "1688681",
  "openreview_id": "~Yann_LeCun1",
  "emails": [
    {"email": "yann@cs.nyu.edu", "source": "orcid", "verified": true}
  ],
  "homepages": ["http://yann.lecun.com"],
  "institution": "New York University",
  "institution_history": [...],
  "works_count": 412,
  "cited_by_count": 385000,
  "h_index_proxy": 180,
  "top_venues": ["NeurIPS", "ICML", "CVPR"],
  "research_topics": ["deep learning", "computer vision", "self-supervised learning"],
  "last_publication_date": "2025-12-01",
  "score": 98.5,
  "sources_merged": ["openalex", "orcid", "dblp", "openreview", "s2"]
}
```

## Domain Priority

| Domain | Primary Sources | Contact Quality | WeKruit Match |
|--------|----------------|-----------------|---------------|
| AI/ML/DL | OpenAlex + DBLP + OpenReview | ★★★ High | ★★★ Core |
| NLP/CL | OpenAlex + ACL Anthology + DBLP | ★★★ High | ★★★ Core |
| CV/Robotics | OpenAlex + DBLP + arXiv | ★★☆ Med-High | ★★★ Core |
| Systems/Infra | OpenAlex + DBLP | ★★☆ Med-High | ★★☆ Key |
| Biotech/Pharma | OpenAlex + PubMed/PMC | ★★★ High | ★★☆ Key |
| Quant/FinTech | OpenAlex + arXiv (q-fin) | ★☆☆ Med-Low | ★★☆ Key |
| Data Science | OpenAlex + DBLP + Kaggle | ★★☆ Med-High | ★★☆ Key |

## File Structure

```
p9-research-pipeline/
├── README.md                          ← this file
├── requirements.txt
├── Makefile
├── config/
│   ├── settings.example.py            ← template (commit this)
│   └── settings.py                    ← actual keys (gitignore)
├── schemas/
│   └── unified_schema.py              ← Pydantic models
├── scripts/
│   ├── s1_openalex_fetch.py
│   ├── s2_orcid_enrich.py
│   ├── s3_openreview_fetch.py
│   ├── s4_dblp_lookup.py
│   ├── s5_homepage_email.py
│   ├── s6_pubmed_corr_email.py
│   ├── s7_semantic_scholar.py
│   ├── s8_email_verify.py
│   ├── s9_merge_pipeline.py
│   └── s10_score_rank.py
├── tests/
│   └── test_apis.py
├── data/                              ← gitignore, runtime output
│   ├── papers.jsonl
│   ├── authors.jsonl
│   └── ...
└── docs/
    └── research_source_matrix.xlsx    ← comparison spreadsheet
```
