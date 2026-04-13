"""
Academic Data Source API Test Suite
Tests: pyalex, habanero, semanticscholar, ORCID, DBLP, OpenReview

Setup:
  pip install pyalex habanero semanticscholar openreview-py requests

Run:
  python test_academic_apis.py
"""
import json, time, sys, requests

SEPARATOR = "=" * 60
results = {}

# ─── 1. PyAlex (OpenAlex) ───────────────────────────────────
print(f"\n{SEPARATOR}\n1. PyAlex (OpenAlex) - Paper + Author lookup\n{SEPARATOR}")
try:
    from pyalex import Works, Authors, config
    config.email = "adam@wekruit.com"  # polite pool

    # Search AI papers (concept C154945302 = "Artificial Intelligence")
    works = Works().search("transformer attention mechanism").get(per_page=3)
    print(f"✅ Works search: {len(works)} papers returned")

    for w in works[:2]:
        print(f"\n   📄 {w['title'][:90]}")
        print(f"      DOI: {w.get('doi','N/A')}  |  Cited: {w.get('cited_by_count',0)}")
        for a in w.get('authorships', [])[:3]:
            author = a.get('author', {})
            insts = a.get('institutions', [])
            inst_name = insts[0].get('display_name', '—') if insts else '—'
            print(f"      👤 {author.get('display_name','?'):30s} ORCID: {author.get('orcid','N/A'):40s} Inst: {inst_name}")

    # Author detail from first result
    if works and works[0].get('authorships'):
        aid = works[0]['authorships'][0]['author']['id']
        ad = Authors()[aid]
        print(f"\n   🔍 Author Detail: {ad.get('display_name')}")
        print(f"      ID: {ad.get('id')}")
        print(f"      ORCID: {ad.get('orcid', 'N/A')}")
        print(f"      Works: {ad.get('works_count')}  Cited: {ad.get('cited_by_count')}")
        insts = ad.get('last_known_institutions', [])
        if insts:
            print(f"      Institution: {insts[0].get('display_name', '—')}")
        # ⬆️ This is your main entry point: from here you get ORCID → ORCID API for email

    results['pyalex'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['pyalex'] = f'❌ {e}'


# ─── 2. Habanero (Crossref) ─────────────────────────────────
print(f"\n{SEPARATOR}\n2. Habanero (Crossref) - DOI + Author metadata\n{SEPARATOR}")
try:
    from habanero import Crossref
    cr = Crossref(mailto="adam@wekruit.com")  # polite pool

    res = cr.works(query="deep learning neural network", limit=3)
    items = res['message']['items']
    total = res['message']['total-results']
    print(f"✅ Works search: {len(items)} returned (total matched: {total:,})")

    for item in items[:2]:
        title = item.get('title', ['N/A'])[0][:90] if item.get('title') else 'N/A'
        print(f"\n   📄 {title}")
        print(f"      DOI: {item.get('DOI','N/A')}")
        for a in item.get('author', [])[:3]:
            orcid = a.get('ORCID', '—')
            affils = a.get('affiliation', [])
            aname = affils[0].get('name', '—') if affils else '—'
            print(f"      👤 {a.get('given','?')} {a.get('family','?'):20s} ORCID: {orcid:45s} Affil: {aname}")

    results['habanero'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['habanero'] = f'❌ {e}'


# ─── 3. Semantic Scholar ────────────────────────────────────
print(f"\n{SEPARATOR}\n3. Semantic Scholar - Paper + Author + Citations\n{SEPARATOR}")
try:
    from semanticscholar import SemanticScholar
    sch = SemanticScholar()

    # Lookup the famous "Attention Is All You Need" paper
    paper = sch.get_paper('10.5555/3295222.3295349')  # Attention paper
    print(f"✅ Paper: {paper.title}")
    print(f"   Year: {paper.year}  Citations: {paper.citationCount}")
    print(f"   Venue: {paper.venue}")
    for a in paper.authors[:5]:
        print(f"   👤 {a.name:30s} S2-ID: {a.authorId}")

    # Author detail
    if paper.authors:
        author = sch.get_author(paper.authors[0].authorId)
        print(f"\n   🔍 Author Detail: {author.name}")
        print(f"      S2 ID: {author.authorId}")
        print(f"      Papers: {author.paperCount}  Citations: {author.citationCount}")
        print(f"      Homepage: {author.homepage or 'N/A'}")
        eids = author.externalIds or {}
        print(f"      DBLP: {eids.get('DBLP', 'N/A')}")
        print(f"      ORCID: {eids.get('ORCID', 'N/A')}")

    results['semanticscholar'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['semanticscholar'] = f'❌ {e}'


# ─── 4. ORCID Public API ───────────────────────────────────
print(f"\n{SEPARATOR}\n4. ORCID Public API - Email + Institution + Homepage\n{SEPARATOR}")
try:
    # Test with Yoshua Bengio
    orcid_id = "0000-0002-5668-2690"
    headers = {"Accept": "application/json"}

    # Person summary (name, emails, researcher-urls, keywords)
    r = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/person", headers=headers, timeout=15)
    r.raise_for_status()
    person = r.json()

    name = person.get('name', {})
    given = name.get('given-names', {}).get('value', '?')
    family = name.get('family-name', {}).get('value', '?')
    print(f"✅ Person: {given} {family}")

    # Emails
    emails = person.get('emails', {}).get('email', [])
    print(f"   📧 Emails (public): {len(emails)}")
    for e in emails:
        print(f"      {e.get('email')}")

    # Researcher URLs (homepages)
    rurls = person.get('researcher-urls', {}).get('researcher-url', [])
    print(f"   🔗 Researcher URLs: {len(rurls)}")
    for u in rurls[:5]:
        print(f"      {u.get('url-name','')}: {u.get('url',{}).get('value','')}")

    # Keywords
    kws = person.get('keywords', {}).get('keyword', [])
    if kws:
        print(f"   🏷️ Keywords: {', '.join(k.get('content','') for k in kws[:8])}")

    # Employments
    r2 = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id}/employments", headers=headers, timeout=15)
    r2.raise_for_status()
    emp = r2.json()
    groups = emp.get('affiliation-group', [])
    print(f"   🏛️ Employments: {len(groups)}")
    for g in groups[:4]:
        for s in g.get('summaries', []):
            es = s.get('employment-summary', {})
            org = es.get('organization', {}).get('name', '?')
            role = es.get('role-title', '—')
            print(f"      {org} — {role}")

    # Test another researcher with public email (more common in bio)
    print(f"\n   --- Testing another ORCID (bio researcher) ---")
    orcid_id2 = "0000-0003-1419-2405"  # example bio researcher
    r3 = requests.get(f"https://pub.orcid.org/v3.0/{orcid_id2}/person", headers=headers, timeout=15)
    r3.raise_for_status()
    p2 = r3.json()
    n2 = p2.get('name', {})
    e2 = p2.get('emails', {}).get('email', [])
    print(f"   Person: {n2.get('given-names',{}).get('value','?')} {n2.get('family-name',{}).get('value','?')}")
    print(f"   Emails: {len(e2)} public {'→ ' + e2[0].get('email','') if e2 else '(none public)'}")

    results['orcid'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['orcid'] = f'❌ {e}'


# ─── 5. DBLP ───────────────────────────────────────────────
print(f"\n{SEPARATOR}\n5. DBLP - Author search + Homepage\n{SEPARATOR}")
try:
    r = requests.get(
        "https://dblp.org/search/author/api",
        params={"q": "Yann LeCun", "format": "json", "h": 3},
        timeout=15
    )
    r.raise_for_status()
    hits = r.json().get('result', {}).get('hits', {}).get('hit', [])
    print(f"✅ Author search: {len(hits)} hits")

    for h in hits[:2]:
        info = h.get('info', {})
        print(f"\n   👤 {info.get('author','?')}")
        print(f"      DBLP URL: {info.get('url','N/A')}")
        # Notes might contain homepage
        notes = info.get('notes', {}).get('note', [])
        if isinstance(notes, dict):
            notes = [notes]
        for n in notes:
            if isinstance(n, dict):
                if n.get('@type') == 'homepage':
                    print(f"      🏠 Homepage: {n.get('text', n.get('#text', 'N/A'))}")

    # Get publications for first author
    if hits:
        author_url = hits[0].get('info', {}).get('url', '')
        if author_url:
            pid = author_url.replace('https://dblp.org/pid/', '')
            r2 = requests.get(f"https://dblp.org/pid/{pid}.json", timeout=15)
            r2.raise_for_status()
            pdata = r2.json()
            pubs = pdata.get('person', {}).get('r', [])
            print(f"\n   📚 Publications: {len(pubs)} total")
            for p in pubs[:3]:
                # Each pub is a dict with one key like 'article', 'inproceedings', etc
                for ptype, pinfo in p.items():
                    title = pinfo.get('title', 'N/A')
                    if isinstance(title, dict):
                        title = title.get('text', title.get('#text', 'N/A'))
                    year = pinfo.get('year', '?')
                    print(f"      [{year}] {str(title)[:80]}")

    results['dblp'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['dblp'] = f'❌ {e}'


# ─── 6. OpenReview ──────────────────────────────────────────
print(f"\n{SEPARATOR}\n6. OpenReview - Profile + Paper lookup\n{SEPARATOR}")
try:
    # Use raw API (openreview-py needs more setup)
    r = requests.get(
        "https://api2.openreview.net/profiles",
        params={"fullname": "Yoshua Bengio"},
        timeout=15
    )
    r.raise_for_status()
    profiles = r.json().get('profiles', [])
    print(f"✅ Profile search: {len(profiles)} results")

    for p in profiles[:1]:
        content = p.get('content', {})
        names = content.get('names', [])
        name_str = f"{names[0].get('first','?')} {names[0].get('last','?')}" if names else '?'
        print(f"\n   👤 {name_str}")
        print(f"      OR ID: {p.get('id','N/A')}")

        # Homepage
        homepage = content.get('homepage', 'N/A')
        print(f"      🏠 Homepage: {homepage}")

        # DBLP
        dblp = content.get('dblp', 'N/A')
        print(f"      DBLP: {dblp}")

        # Google Scholar
        gscholar = content.get('gscholar', 'N/A')
        print(f"      Google Scholar: {gscholar}")

        # Institution history
        history = content.get('history', [])
        print(f"      🏛️ Positions: {len(history)}")
        for h in history[:3]:
            inst = h.get('institution', {}).get('name', '?')
            pos = h.get('position', '—')
            print(f"         {inst} — {pos}")

    results['openreview'] = '✅'
except Exception as e:
    print(f"❌ Error: {e}")
    results['openreview'] = f'❌ {e}'


# ─── SUMMARY ────────────────────────────────────────────────
print(f"\n{SEPARATOR}")
print("SUMMARY — Library & API Test Results")
print(SEPARATOR)
for k, v in results.items():
    print(f"  {k:20s} {v}")

print(f"\n{'='*60}")
print("NEXT STEPS:")
print("  1. pip install pyalex habanero semanticscholar openreview-py requests")
print("  2. Get free API keys:")
print("     - Semantic Scholar: https://www.semanticscholar.org/product/api#api-key")
print("     - PubMed E-Utils:   https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/")
print("     - OpenAlex:         https://openalex.org/users/me (free, recommended)")
print("  3. Run this script locally to verify all endpoints")
print("  4. Then start building the pipeline scripts (S1-S10)")
