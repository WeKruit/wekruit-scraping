"""
S4: DBLP Author Lookup
Searches DBLP for author PIDs and homepages.

Usage:
  python scripts/s4_dblp_lookup.py --input data/authors.jsonl --output data/dblp_enriched.jsonl
"""
import argparse, json, os, sys, time
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

DBLP_SEARCH = "https://dblp.org/search/author/api"


def search_author(name: str) -> dict:
    try:
        r = requests.get(DBLP_SEARCH, params={"q": name, "format": "json", "h": 3}, timeout=15)
        r.raise_for_status()
        hits = r.json().get("result", {}).get("hits", {}).get("hit", [])
        if not hits:
            return {}
        info = hits[0].get("info", {})
        homepage = None
        notes = info.get("notes", {}).get("note", [])
        if isinstance(notes, dict): notes = [notes]
        for n in notes:
            if isinstance(n, dict) and n.get("@type") == "homepage":
                homepage = n.get("text", n.get("#text"))
        return {
            "dblp_name": info.get("author"),
            "dblp_url": info.get("url"),
            "dblp_pid": info.get("url", "").replace("https://dblp.org/pid/", "") if info.get("url") else None,
            "dblp_homepage": homepage,
        }
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="S4: DBLP author lookup")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/authors.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/dblp_enriched.jsonl")
    args = parser.parse_args()

    authors = [json.loads(l) for l in open(args.input) if l.strip()]
    print(f"[S4] DBLP lookup for {len(authors)} authors")

    for a in tqdm(authors, desc="DBLP"):
        name = a.get("name", "")
        if not name: continue
        dblp = search_author(name)
        a.update(dblp)
        time.sleep(1.1)  # DBLP asks ~1s between requests

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for a in authors:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    with_hp = sum(1 for a in authors if a.get("dblp_homepage"))
    print(f"[S4] Done: {with_hp} authors with homepage → {args.output}")


if __name__ == "__main__":
    main()
