# Pitfalls Research — Milestone v1.1 AI/CS Ranking And Recruiter Readiness

**Scope:** Only the mistakes that can break this milestone.
**Researched:** 2026-04-14
**Confidence:** High

## Risk Register

### P0 — Corpus contamination

**Failure mode**
Broad OpenAlex concept search leaks non-AI/CS papers into the ranked set.

**Why it happens**
Concept IDs and keyword search are discovery tools, not clean ranking corpora.

**Prevention**
- Gate ranking through explicit AI/CS venue tiers
- Store exclusion reasons
- Review top excluded and included examples during calibration

### P0 — Venue tier drift

**Failure mode**
Venue rankings become stale or inconsistent across CCF and CORE sources.

**Why it happens**
Venue lists change over time and names vary across source systems.

**Prevention**
- Maintain a local normalized tier table with `last_reviewed_at`
- Record the upstream source and grade used for every mapping
- Treat unknown venues as unknown, not low confidence top-tier substitutes

### P0 — Bad citation fairness

**Failure mode**
Older papers dominate because raw total citations are used without normalization.

**Why it happens**
Raw `cited_by_count` is easy to compute and looks authoritative.

**Prevention**
- Normalize citations within publication year or recency bucket
- Keep raw citation count and normalized citation score separate

### P0 — Wrong author influence semantics

**Failure mode**
Author influence is computed from all coauthors equally or guessed from shallow authorship data.

**Why it happens**
Large collaboration papers make naive averages look legitimate.

**Prevention**
- Backfill author detail explicitly
- Limit influence inputs to key authors (`first`, `last`, `corresponding`)
- Keep paper score and researcher score logic separate

### P1 — Black-box ranking

**Failure mode**
The export exposes a final score but not the reasons behind it.

**Why it happens**
Single-number scoring is easy to display.

**Prevention**
- Emit component scores and ranking mode
- Preserve `score_breakdown` in JSONL and flattened columns in CSV

### P1 — Contact confidence inflation

**Failure mode**
Homepage or public-profile signals are shown as if they were equivalent to verified direct contacts.

**Why it happens**
Recruiter workflows naturally bias toward any reachable signal.

**Prevention**
- Preserve contact quality state
- Separate researcher ranking from contact actionability
- Never let contact quality alter identity logic

### P1 — Cross-domain leakage

**Failure mode**
Bio/Pharma or unrelated CS-adjacent venue logic gets pulled into the same milestone and distorts ranking semantics.

**Why it happens**
Coverage conversations expand faster than evaluation standards.

**Prevention**
- Keep `domain_scope=ai_cs` explicit in the venue tier asset
- Reject mixed-domain ranking in this milestone

## Looks Done But Isn’t

- [ ] Ranking corpus is gated before scoring
- [ ] Venue tiers are versioned and reviewable
- [ ] Citation normalization is explicit
- [ ] Author influence uses real author details
- [ ] Score breakdowns are exported
- [ ] Unknown venues stay unknown instead of being silently coerced

## Phase Ownership

| Risk | Owning phase |
|------|--------------|
| Corpus contamination | Phase 6 |
| Venue tier drift | Phase 6 |
| Wrong author influence semantics | Phase 8 |
| Black-box ranking | Phase 9 |
| Contact confidence inflation | Phase 8 / 10 |
| Cross-domain leakage | Whole milestone governance |
