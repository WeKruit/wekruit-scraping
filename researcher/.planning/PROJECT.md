# Researcher Pipeline

## What This Is

This is a standalone `researcher/` pipeline for WeKruit that sources researchers from official
scholarly systems first, then enriches identity and contactability. It links papers, source-native
researcher profiles, public contact signals, and human review decisions into approved researcher
groups for recruiting use.

The pipeline must not pretend that a name match is an identity match. Its job is to collect source
profiles, extract comparable signals, explain why profiles may represent the same person, and let a
human approve or reject the merge.

## Core Value

Produce high-confidence researcher profiles with defensible provenance so downstream sourcing and
outreach can trust who the researcher is, what they worked on, how the contact signal was found,
and why multiple source records were or were not merged.

## Current Milestone: v1.2 Four-Source Human Review Merge Foundation

**Goal:** Build four independently triggerable researcher-profile pipelines and a human-reviewed merge workflow with explicit reasoning for every candidate group.

**Target features:**
- Persist source runs, raw source profiles, extracted identity/contact signals, candidate groups, review labels, and approved people in Postgres.
- Trigger four profile pipelines independently: OpenAlex, ORCID, DBLP, and OpenReview.
- Extract comparable identity/contact signals such as ORCID, email, homepage, GitHub, DBLP PID, OpenReview profile ID, Google Scholar ID, institution, and paper DOI.
- Generate candidate groups with visible merge reasoning, but do not auto-merge people.
- Export a human review queue where every candidate includes the evidence that caused it to be grouped.
- Ingest human labels (`same_person`, `not_same_person`, `unsure`) and use them to produce approved researcher groups.

## Requirements

### Validated

- Official-source ingest backbone exists for AI/ML-first paper and author discovery (Phase 1).
- Raw paper and author staging is replayable and audit-friendly through run manifests (Phase 1).
- OpenAlex is the working ingest backbone and Crossref is the DOI backfill layer (Phase 1).
- AI/CS paper corpus gating exists with venue-tier decisions and include/exclude reason logs (Phase 6).

### Active

- [ ] Define one durable Postgres schema for source runs, source profiles, extracted signals, candidate groups, review labels, and approved people.
- [ ] Convert source-native researcher outputs into source-profile records without claiming they are canonical people.
- [ ] Trigger OpenAlex, ORCID, DBLP, and OpenReview profile pipelines independently and persist their outputs.
- [ ] Extract exact-match and review-match signals from source profiles and public profile pages.
- [ ] Generate candidate groups with machine-readable reasons and reviewer-readable evidence packets.
- [ ] Require human review for every candidate group before it becomes an approved researcher group.
- [ ] Ingest human labels and suppress already-reviewed negative or unsure candidates from repeated review spam.
- [ ] Export approved people and unresolved review queues with provenance intact.

### Out of Scope

- Generic web crawling as the backbone — official scholarly APIs and public profile URLs are the primary source paths.
- Neo4j or another graph database as the primary store — graph projection can be reconsidered later if traversal becomes a measured product need.
- NoSQL as the primary identity/review store — merge review needs constraints, transactions, labels, and audit history.
- Automatic merge without human approval — all candidate groups require a label before they become approved people.
- UI dashboards or operator consoles — CSV/JSONL review queues are enough for this milestone.
- Ranking, outreach, or recruiter export based on unreviewed identities — ranking resumes only after approved researcher groups exist.
- Closed-platform or login-gated scraping — conflicts with source-policy and compliance goals.
- “Guaranteed direct email” as a product promise — contact is an enrichment output with varying quality.

## Context

The root repository currently has separate sourcing domains (`devpost/`, `github/`, and
`researcher/`). Inside `researcher/`, Phase 1 established official-source scholarly ingest and Phase
6 established an AI/CS corpus gate. The next bottleneck is not another ranking function. The next
bottleneck is identity confidence across source profiles.

The four profile pipelines for this milestone are:

1. `OpenAlex` — paper and author backbone, source-native author IDs, works, institutions, and ORCID hints.
2. `ORCID` — identity and public self-declared profile fields such as email, URLs, employment, and works.
3. `DBLP` — CS author profile, homepage, publication list, and coauthor context.
4. `OpenReview` — AI/ML profile enrichment such as homepage, DBLP links, Google Scholar, GitHub/LinkedIn-style public profile signals when available.

Homepage, GitHub, and email extraction are derived signal stages, not separate canonical source
systems. They enrich evidence for review, but they do not bypass the human review gate.

## Constraints

- **Human-reviewed merge**: Candidate groups can be strong, medium, or weak, but no candidate becomes a person without human labeling.
- **Source profile first**: A row from OpenAlex, ORCID, DBLP, or OpenReview is a `source_profile`, not a canonical person.
- **Reasoning required**: Every candidate group must preserve why it exists, such as `email_exact`, `orcid_exact`, `homepage_exact`, `github_exact`, `dblp_link`, `paper_overlap`, or `name_institution`.
- **Postgres first**: Durable storage uses Postgres with JSONB raw payloads and relational evidence tables.
- **No NoSQL primary**: Document stores are not the source of truth for merge review because review labels, negative evidence, and reversible identity decisions need relational guarantees.
- **No graph DB primary**: Neo4j can be a later projection, not the first durable store.
- **Traceability**: Each signal and review decision must retain source system, source record ID, run ID, and observed timestamp.
- **Incremental review hygiene**: New pipeline runs must not repeatedly ask humans to review the same rejected candidate pair.
- **Scope discipline**: Ranking and outreach wait until approved people exist.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `researcher/` is an isolated pipeline | The root repo treats sourcing domains as separate folders | ✓ Good |
| OpenAlex is the ingest backbone | Broad paper/author/affiliation coverage with stable identifiers and bulk/snapshot options | ✓ Good |
| Crossref is metadata backfill, not researcher identity backbone | Strong DOI metadata, but weak direct person-profile value for this milestone | ✓ Good |
| OpenReview and DBLP are AI/CS profile enrichers | Stronger profile signal for AI/ML and CS than general-purpose sources | ✓ Good |
| ORCID remains a profile source with public-field caveats | Public profile fields are useful evidence but not blanket contact truth | ✓ Good |
| AI/CS venue tiers gate ranking corpus | Broad concept search leaks non-AI papers into the ranking set | ✓ Good |
| v1.1 ranking work is paused after corpus gate | Ranking before human-reviewed identity merge would amplify uncertain people | ✓ Good |
| Postgres is the durable store for v1.2 | Source profiles, evidence, review labels, and approved groups need constraints and transactions | ✓ Good |
| NoSQL is not the primary store | JSON documents alone do not solve merge labels, negative pairs, or audit-safe review state | ✓ Good |
| Neo4j is optional later projection only | Current bottleneck is identity evidence and review workflow, not graph traversal | ✓ Good |
| All merge candidates require human review | The business requirement is explainable grouping, not automatic identity collapse | ✓ Good |

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
*Last updated: 2026-04-15 after milestone v1.2 kickoff for four-source human-reviewed merge*
