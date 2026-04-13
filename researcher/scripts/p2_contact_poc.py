from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sources.dblp import DBLPAdapter
from sources.openreview import OpenReviewAdapter
from sources.orcid import OrcidAdapter

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
NOISE_EMAIL_DOMAIN_MARKERS = (
    "sentry.",
    ".sentry.",
    "wixpress.com",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 2 contact POC over staged OpenAlex authors")
    parser.add_argument("--input-run", required=True)
    parser.add_argument("--output-root", default="data")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-file", default=None)
    return parser


def load_authors(*, data_root: str | Path, run_id: str) -> list[dict]:
    path = Path(data_root) / "runs" / run_id / "openalex" / "authors_raw.jsonl"
    if not path.exists():
        raise SystemExit(f"Missing staged OpenAlex authors for run: {run_id}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def filter_candidate_emails(emails: list[str]) -> list[str]:
    filtered = []
    for email in emails:
        domain = email.rsplit("@", 1)[-1].lower()
        if any(marker in domain for marker in NOISE_EMAIL_DOMAIN_MARKERS):
            continue
        filtered.append(email)
    return filtered


def extract_homepage_emails(url: str) -> list[str]:
    request = Request(url, headers={"User-Agent": "WeKruit-Research-Bot/1.0 (adam@wekruit.com)"})
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="ignore")
    return sorted(set(filter_candidate_emails(EMAIL_RE.findall(html))))


def enrich_author(author_record: dict, *, orcid: OrcidAdapter, openreview: OpenReviewAdapter, dblp: DBLPAdapter) -> dict:
    raw = author_record.get("raw", {}) or {}
    name = raw.get("name")
    orcid_id = raw.get("orcid")

    result = {
        "openalex_author_id": author_record.get("source_record_id"),
        "name": name,
        "orcid": orcid_id,
        "institution": raw.get("institution"),
        "emails": [],
        "homepages": [],
        "profile_urls": [],
        "openreview": {},
        "dblp": {},
        "errors": [],
    }

    if orcid_id:
        try:
            contacts = orcid.extract_contacts(orcid.fetch_person(orcid_id))
            result["emails"].extend({"value": email, "source": "orcid"} for email in contacts["emails"])
            result["homepages"].extend({"value": url, "source": "orcid"} for url in contacts["homepages"])
        except Exception as exc:
            result["errors"].append(f"orcid:{exc}")

    if name:
        try:
            openreview_contacts = openreview.extract_contacts(openreview.search_profiles(name))
            result["openreview"] = openreview_contacts
            if openreview_contacts.get("homepage"):
                result["homepages"].append({"value": openreview_contacts["homepage"], "source": "openreview"})
            if openreview_contacts.get("dblp_url"):
                result["profile_urls"].append({"value": openreview_contacts["dblp_url"], "source": "openreview_dblp"})
        except Exception as exc:
            result["errors"].append(f"openreview:{exc}")

        try:
            dblp_contacts = dblp.extract_contacts(dblp.search_author(name))
            if not dblp_contacts.get("homepage") and dblp_contacts.get("dblp_profile_url"):
                try:
                    dblp_contacts["homepage"] = dblp.fetch_profile_homepage(dblp_contacts["dblp_profile_url"])
                except Exception as exc:
                    result["errors"].append(f"dblp_homepage:{exc}")
            result["dblp"] = dblp_contacts
            if dblp_contacts.get("homepage"):
                result["homepages"].append({"value": dblp_contacts["homepage"], "source": "dblp"})
            if dblp_contacts.get("dblp_profile_url"):
                result["profile_urls"].append({"value": dblp_contacts["dblp_profile_url"], "source": "dblp_profile"})
        except Exception as exc:
            result["errors"].append(f"dblp:{exc}")

    deduped_homepages = []
    seen_homepages = set()
    for item in result["homepages"]:
        key = item["value"]
        if key and key not in seen_homepages:
            seen_homepages.add(key)
            deduped_homepages.append(item)
    result["homepages"] = deduped_homepages

    deduped_profile_urls = []
    seen_profile_urls = set()
    for item in result["profile_urls"]:
        key = item["value"]
        if key and key not in seen_profile_urls:
            seen_profile_urls.add(key)
            deduped_profile_urls.append(item)
    result["profile_urls"] = deduped_profile_urls

    homepage_emails = []
    for item in result["homepages"][:3]:
        url = item["value"]
        if not isinstance(url, str) or not url.startswith("http"):
            continue
        try:
            for email in extract_homepage_emails(url):
                homepage_emails.append({"value": email, "source": f"homepage:{url}"})
        except Exception as exc:
            result["errors"].append(f"homepage:{url}:{exc}")
    result["emails"].extend(homepage_emails)

    deduped_emails = []
    seen_emails = set()
    for item in result["emails"]:
        key = item["value"]
        if key and key not in seen_emails:
            seen_emails.add(key)
            deduped_emails.append(item)
    result["emails"] = deduped_emails
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    authors = load_authors(data_root=args.output_root, run_id=args.input_run)[: args.limit]
    output_file = Path(args.output_file) if args.output_file else Path(args.output_root) / "poc_contact_enriched.jsonl"

    orcid = OrcidAdapter()
    openreview = OpenReviewAdapter()
    dblp = DBLPAdapter()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for author in authors:
            enriched = enrich_author(author, orcid=orcid, openreview=openreview, dblp=dblp)
            handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
