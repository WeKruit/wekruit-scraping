"""
S2: ORCID Enrichment
Takes authors.jsonl (with orcid field), hits ORCID public API for:
  - Public email
  - Researcher URLs (homepages)
  - Employment history
  - Keywords

Usage:
  python scripts/s2_orcid_enrich.py --input data/authors.jsonl --output data/orcid_enriched.jsonl
"""
import argparse, json, os, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, ORCID_RATE_LIMIT

ORCID_BASE = "https://pub.orcid.org/v3.0"
HEADERS = {"Accept": "application/json"}
DELAY = 1.0 / ORCID_RATE_LIMIT  # ~0.042s per request


def fetch_orcid_person(orcid_id: str) -> dict:
    """Fetch person summary from ORCID public API."""
    try:
        r = requests.get(f"{ORCID_BASE}/{orcid_id}/person", headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_orcid_employments(orcid_id: str) -> dict:
    try:
        r = requests.get(f"{ORCID_BASE}/{orcid_id}/employments", headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def extract_person_info(person: dict, orcid_id: str) -> dict:
    """Extract structured info from ORCID person response."""
    if "error" in person:
        return {"orcid": orcid_id, "orcid_error": person["error"]}

    name = person.get("name", {}) or {}
    emails_raw = (person.get("emails", {}) or {}).get("email", [])
    urls_raw = (person.get("researcher-urls", {}) or {}).get("researcher-url", [])
    kws_raw = (person.get("keywords", {}) or {}).get("keyword", [])

    return {
        "orcid": orcid_id,
        "given_name": (name.get("given-names") or {}).get("value"),
        "family_name": (name.get("family-name") or {}).get("value"),
        "emails": [e.get("email") for e in emails_raw if e.get("email")],
        "homepages": [u.get("url", {}).get("value") for u in urls_raw if u.get("url", {}).get("value")],
        "homepage_labels": [u.get("url-name", "") for u in urls_raw],
        "keywords": [k.get("content", "") for k in kws_raw if k.get("content")],
    }


def extract_employment_info(emp_data: dict) -> list[dict]:
    """Extract employment history."""
    groups = emp_data.get("affiliation-group", [])
    history = []
    for g in groups:
        for s in g.get("summaries", []):
            es = s.get("employment-summary", {})
            org = es.get("organization", {})
            start = es.get("start-date") or {}
            end = es.get("end-date") or {}
            history.append({
                "institution": org.get("name"),
                "role": es.get("role-title"),
                "department": es.get("department-name"),
                "country": (org.get("address") or {}).get("country"),
                "start_year": (start.get("year") or {}).get("value"),
                "end_year": (end.get("year") or {}).get("value"),
            })
    return history


def enrich_single(author: dict) -> dict:
    """Enrich a single author record with ORCID data."""
    orcid_id = author.get("orcid")
    if not orcid_id:
        author["orcid_status"] = "no_orcid"
        return author

    # Clean ORCID (might be full URL)
    if "orcid.org/" in orcid_id:
        orcid_id = orcid_id.split("orcid.org/")[-1]

    person = fetch_orcid_person(orcid_id)
    info = extract_person_info(person, orcid_id)

    emp_data = fetch_orcid_employments(orcid_id)
    employment = extract_employment_info(emp_data)

    author["orcid_emails"] = info.get("emails", [])
    author["orcid_homepages"] = info.get("homepages", [])
    author["orcid_keywords"] = info.get("keywords", [])
    author["orcid_given_name"] = info.get("given_name")
    author["orcid_family_name"] = info.get("family_name")
    author["orcid_employment"] = employment
    author["orcid_status"] = "enriched"

    time.sleep(DELAY)
    return author


def main():
    parser = argparse.ArgumentParser(description="S2: ORCID enrichment")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/authors.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/orcid_enriched.jsonl")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent workers (keep ≤ ORCID rate limit)")
    args = parser.parse_args()

    # Load authors
    authors = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                authors.append(json.loads(line))

    with_orcid = [a for a in authors if a.get("orcid")]
    without_orcid = [a for a in authors if not a.get("orcid")]
    print(f"[S2] Loaded {len(authors)} authors, {len(with_orcid)} with ORCID")

    # Enrich
    enriched = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(enrich_single, a): a for a in with_orcid}
        for future in tqdm(as_completed(futures), total=len(futures), desc="ORCID enrich"):
            try:
                enriched.append(future.result())
            except Exception as e:
                orig = futures[future]
                orig["orcid_status"] = f"error: {e}"
                enriched.append(orig)

    # Add back authors without ORCID
    for a in without_orcid:
        a["orcid_status"] = "no_orcid"
    enriched.extend(without_orcid)

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for a in enriched:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    # Stats
    with_email = sum(1 for a in enriched if a.get("orcid_emails"))
    with_homepage = sum(1 for a in enriched if a.get("orcid_homepages"))
    print(f"\n[S2] Results:")
    print(f"  Total: {len(enriched)}")
    print(f"  With ORCID email: {with_email} ({100*with_email/max(len(with_orcid),1):.1f}% of ORCID holders)")
    print(f"  With homepage: {with_homepage}")
    print(f"  Saved → {args.output}")


if __name__ == "__main__":
    main()
