"""
S10: Score & Rank Researchers
Computes a composite score and exports ranked CSV.

Usage:
  python scripts/s10_score_rank.py --input data/merged_profiles.jsonl --output data/ranked_researchers.csv
"""
import argparse, csv, json, math, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR


def compute_score(p: dict) -> float:
    works = p.get("works_count", 0)
    cited = p.get("cited_by_count", 0)

    # h-index proxy: sqrt(cited_by_count) capped
    h_proxy = min(math.sqrt(cited), 300)

    # Recency bonus (has recent publications)
    recency_bonus = 1.0

    # Contact bonus
    contact_bonus = 1.2 if p.get("emails") else (1.1 if p.get("homepages") else 1.0)

    # Source diversity bonus
    sources = p.get("sources", [])
    source_bonus = 1.0 + len(sources) * 0.05

    score = h_proxy * contact_bonus * source_bonus * recency_bonus
    return round(score, 2)


def main():
    parser = argparse.ArgumentParser(description="S10: Score & rank")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/merged_profiles.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/ranked_researchers.csv")
    parser.add_argument("--top-n", type=int, default=0, help="Export top N only (0=all)")
    args = parser.parse_args()

    profiles = [json.loads(l) for l in open(args.input) if l.strip()]
    print(f"[S10] Scoring {len(profiles)} profiles")

    for p in profiles:
        p["score"] = compute_score(p)

    profiles.sort(key=lambda p: p["score"], reverse=True)

    if args.top_n > 0:
        profiles = profiles[:args.top_n]

    # Export CSV
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    fieldnames = [
        "rank", "name", "score", "institution", "orcid", "openalex_id",
        "works_count", "cited_by_count", "email", "homepage",
        "dblp_pid", "s2_id", "openreview_id", "sources", "topics"
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, p in enumerate(profiles, 1):
            best_email = ""
            if p.get("emails"):
                e = p["emails"][0]
                best_email = e.get("email") if isinstance(e, dict) else e
            best_hp = p.get("homepages", [""])[0] if p.get("homepages") else ""
            writer.writerow({
                "rank": i,
                "name": p.get("name", ""),
                "score": p.get("score", 0),
                "institution": p.get("institution", ""),
                "orcid": p.get("orcid", ""),
                "openalex_id": p.get("openalex_id", ""),
                "works_count": p.get("works_count", 0),
                "cited_by_count": p.get("cited_by_count", 0),
                "email": best_email,
                "homepage": best_hp,
                "dblp_pid": p.get("dblp_pid", ""),
                "s2_id": p.get("s2_id", ""),
                "openreview_id": p.get("openreview_id", ""),
                "sources": ",".join(p.get("sources", [])),
                "topics": "|".join(p.get("topics", [])[:5]),
            })

    print(f"[S10] Ranked {len(profiles)} → {args.output}")
    print(f"  Top 5:")
    for p in profiles[:5]:
        e = p["emails"][0].get("email") if p.get("emails") and isinstance(p["emails"][0], dict) else ""
        print(f"    {p['score']:8.1f}  {p['name']:30s}  {p.get('institution',''):30s}  {e}")


if __name__ == "__main__":
    main()
