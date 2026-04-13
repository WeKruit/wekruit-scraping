"""
S7: Semantic Scholar Enrichment
Enriches authors with citation data, external IDs, and homepage from S2 API.

Usage:
  python scripts/s7_semantic_scholar.py --input data/authors.jsonl --output data/s2_enriched.jsonl
"""
import argparse, json, os, sys, time
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, S2_API_KEY

from semanticscholar import SemanticScholar


def main():
    parser = argparse.ArgumentParser(description="S7: Semantic Scholar enrichment")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/authors.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/s2_enriched.jsonl")
    parser.add_argument("--max-authors", type=int, default=500)
    args = parser.parse_args()

    sch = SemanticScholar(api_key=S2_API_KEY) if S2_API_KEY else SemanticScholar()
    authors = [json.loads(l) for l in open(args.input) if l.strip()][:args.max_authors]
    print(f"[S7] S2 enrichment for {len(authors)} authors")

    delay = 0.01 if S2_API_KEY else 1.1

    for a in tqdm(authors, desc="S2 enrich"):
        name = a.get("name", "")
        if not name: continue
        try:
            results = sch.search_author(name, limit=1)
            if results and results.items:
                s2a = results.items[0]
                a["s2_id"] = s2a.authorId
                a["s2_name"] = s2a.name
                a["s2_paper_count"] = s2a.paperCount
                a["s2_citation_count"] = s2a.citationCount
                a["s2_homepage"] = s2a.homepage
                eids = s2a.externalIds or {}
                a["s2_orcid"] = eids.get("ORCID")
                a["s2_dblp"] = eids.get("DBLP")
        except Exception as e:
            a["s2_error"] = str(e)
        time.sleep(delay)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for a in authors:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    with_s2 = sum(1 for a in authors if a.get("s2_id"))
    print(f"[S7] Matched {with_s2}/{len(authors)} → {args.output}")


if __name__ == "__main__":
    main()
