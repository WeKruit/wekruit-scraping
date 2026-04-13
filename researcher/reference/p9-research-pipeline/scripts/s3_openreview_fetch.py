"""
S3: OpenReview Profile & Paper Fetch
Fetches AI/ML researcher profiles from OpenReview by venue.

Usage:
  python scripts/s3_openreview_fetch.py --venue "ICLR 2025" --max-papers 1000
  python scripts/s3_openreview_fetch.py --venue "NeurIPS 2024"
"""
import argparse, json, os, sys, time
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

OR_API = "https://api2.openreview.net"


def fetch_notes(venue: str, max_papers=1000):
    """Fetch papers (notes) from a venue."""
    papers = []
    offset = 0
    limit = 100
    while offset < max_papers:
        r = requests.get(f"{OR_API}/notes", params={
            "content.venue": venue, "limit": limit, "offset": offset
        }, timeout=30)
        r.raise_for_status()
        batch = r.json().get("notes", [])
        if not batch:
            break
        papers.extend(batch)
        offset += limit
        print(f"  Fetched {len(papers)} papers...")
        time.sleep(0.5)
    return papers[:max_papers]


def fetch_profile(fullname: str) -> dict:
    """Fetch an OpenReview profile by name."""
    try:
        r = requests.get(f"{OR_API}/profiles", params={"fullname": fullname}, timeout=15)
        r.raise_for_status()
        profiles = r.json().get("profiles", [])
        return profiles[0] if profiles else {}
    except Exception:
        return {}


def extract_profile_info(profile: dict) -> dict:
    content = profile.get("content", {})
    names = content.get("names", [])
    name = f"{names[0].get('first','')} {names[0].get('last','')}" if names else "?"
    history = content.get("history", [])
    return {
        "openreview_id": profile.get("id"),
        "name": name.strip(),
        "homepage": content.get("homepage"),
        "dblp": content.get("dblp"),
        "gscholar": content.get("gscholar"),
        "linkedin": content.get("linkedin"),
        "institution_history": [
            {"institution": h.get("institution", {}).get("name"),
             "position": h.get("position"),
             "start": h.get("start"), "end": h.get("end")}
            for h in history[:5]
        ],
        "current_institution": history[0].get("institution", {}).get("name") if history else None,
    }


def main():
    parser = argparse.ArgumentParser(description="S3: OpenReview fetch")
    parser.add_argument("--venue", type=str, required=True, help="Venue string (e.g. 'ICLR 2025')")
    parser.add_argument("--max-papers", type=int, default=1000)
    parser.add_argument("--max-profiles", type=int, default=300, help="Max unique author profiles to fetch")
    parser.add_argument("--output-dir", type=str, default=DATA_DIR)
    args = parser.parse_args()

    print(f"[S3] OpenReview: {args.venue}")
    papers = fetch_notes(args.venue, args.max_papers)
    print(f"  Got {len(papers)} papers")

    # Extract unique author names
    author_names = set()
    for p in papers:
        content = p.get("content", {})
        authors = content.get("authors", {})
        if isinstance(authors, dict):
            authors = authors.get("value", [])
        for name in authors:
            if isinstance(name, str):
                author_names.add(name)

    print(f"  Unique authors: {len(author_names)}")

    # Fetch profiles
    profiles = []
    for name in tqdm(list(author_names)[:args.max_profiles], desc="Profiles"):
        p = fetch_profile(name)
        if p:
            info = extract_profile_info(p)
            info["source_venue"] = args.venue
            profiles.append(info)
        time.sleep(0.3)

    # Save
    os.makedirs(args.output_dir, exist_ok=True)
    out_papers = f"{args.output_dir}/or_papers.jsonl"
    out_profiles = f"{args.output_dir}/or_profiles.jsonl"
    with open(out_papers, "w") as f:
        for p in papers:
            f.write(json.dumps({"openreview_id": p.get("id"), "title": p.get("content",{}).get("title",{}).get("value",""),
                                "venue": args.venue}, ensure_ascii=False) + "\n")
    with open(out_profiles, "w") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with_hp = sum(1 for p in profiles if p.get("homepage"))
    print(f"\n[S3] Results: {len(profiles)} profiles, {with_hp} with homepage")
    print(f"  → {out_profiles}")


if __name__ == "__main__":
    main()
