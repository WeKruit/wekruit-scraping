"""
S5: Homepage Email Extractor
Fetches homepage URLs and extracts email addresses.

Usage:
  python scripts/s5_homepage_email.py --input data/orcid_enriched.jsonl --output data/homepage_emails.jsonl
"""
import argparse, json, os, re, sys, time
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
EXCLUDE_DOMAINS = {"example.com", "email.com", "your-email.com", "sentry.io", "w3.org"}


def extract_emails_from_url(url: str) -> list[str]:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "WeKruit-Research-Bot/1.0 (adam@wekruit.com)"})
        r.raise_for_status()
        found = EMAIL_RE.findall(r.text)
        return [e for e in set(found) if e.split("@")[1] not in EXCLUDE_DOMAINS
                and not e.endswith(".png") and not e.endswith(".jpg")]
    except Exception:
        return []


def collect_homepages(author: dict) -> list[str]:
    urls = set()
    for key in ("orcid_homepages", "dblp_homepage", "homepage", "homepages"):
        val = author.get(key)
        if isinstance(val, list):
            urls.update(v for v in val if v)
        elif isinstance(val, str) and val:
            urls.add(val)
    return [u for u in urls if u.startswith("http")]


def main():
    parser = argparse.ArgumentParser(description="S5: Homepage email extraction")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/orcid_enriched.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/homepage_emails.jsonl")
    args = parser.parse_args()

    authors = [json.loads(l) for l in open(args.input) if l.strip()]
    results = []
    total_emails = 0

    for a in tqdm(authors, desc="Homepage scrape"):
        urls = collect_homepages(a)
        if not urls: continue
        all_emails = []
        for url in urls[:3]:
            emails = extract_emails_from_url(url)
            all_emails.extend(emails)
            time.sleep(0.5)  # polite
        if all_emails:
            results.append({
                "name": a.get("name"),
                "openalex_id": a.get("openalex_id"),
                "orcid": a.get("orcid"),
                "homepage_emails": list(set(all_emails)),
                "source_urls": urls,
            })
            total_emails += len(set(all_emails))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[S5] Found emails for {len(results)} authors ({total_emails} total) → {args.output}")


if __name__ == "__main__":
    main()
