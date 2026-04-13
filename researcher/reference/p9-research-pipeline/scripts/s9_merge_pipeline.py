"""
S9: Merge Pipeline
Combines all source outputs into unified researcher profiles.
Deduplicates by ORCID → OpenAlex ID → name+institution.

Usage:
  python scripts/s9_merge_pipeline.py --input-dir data/ --output data/merged_profiles.jsonl
"""
import argparse, json, os, sys, glob
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())


def merge_profiles(input_dir: str) -> list[dict]:
    # Load all sources
    authors = load_jsonl(f"{input_dir}/authors.jsonl")
    orcid_enriched = load_jsonl(f"{input_dir}/orcid_enriched.jsonl")
    or_profiles = load_jsonl(f"{input_dir}/or_profiles.jsonl")
    dblp_enriched = load_jsonl(f"{input_dir}/dblp_enriched.jsonl")
    s2_enriched = load_jsonl(f"{input_dir}/s2_enriched.jsonl")
    homepage_emails = load_jsonl(f"{input_dir}/homepage_emails.jsonl")
    pubmed_emails = load_jsonl(f"{input_dir}/pubmed_emails.jsonl")

    # Index by ORCID and OpenAlex ID
    by_orcid = {}
    by_oaid = {}
    by_name = {}

    def get_or_create(orcid=None, oaid=None, name=None):
        if orcid and orcid in by_orcid:
            return by_orcid[orcid]
        if oaid and oaid in by_oaid:
            return by_oaid[oaid]
        nname = normalize_name(name) if name else None
        if nname and nname in by_name:
            return by_name[nname]
        profile = {
            "name": name or "", "orcid": orcid, "openalex_id": oaid,
            "emails": [], "homepages": [], "sources": set(),
            "institution": None, "works_count": 0, "cited_by_count": 0,
            "topics": [], "dblp_pid": None, "s2_id": None, "openreview_id": None,
        }
        if orcid: by_orcid[orcid] = profile
        if oaid: by_oaid[oaid] = profile
        if nname: by_name[nname] = profile
        return profile

    # Merge OpenAlex authors
    for a in authors + orcid_enriched:
        p = get_or_create(a.get("orcid"), a.get("openalex_id"), a.get("name"))
        p["sources"].add("openalex")
        p["name"] = a.get("name") or p["name"]
        p["openalex_id"] = a.get("openalex_id") or p.get("openalex_id")
        p["orcid"] = a.get("orcid") or p.get("orcid")
        p["institution"] = a.get("institution") or p.get("institution")
        p["works_count"] = max(a.get("works_count", 0), p.get("works_count", 0))
        p["cited_by_count"] = max(a.get("cited_by_count", 0), p.get("cited_by_count", 0))
        p["topics"] = a.get("topics") or p.get("topics", [])
        # ORCID enrichment
        for e in a.get("orcid_emails", []):
            if e and e not in [x.get("email") if isinstance(x, dict) else x for x in p["emails"]]:
                p["emails"].append({"email": e, "source": "orcid"})
        for hp in a.get("orcid_homepages", []):
            if hp and hp not in p["homepages"]:
                p["homepages"].append(hp)
        if a.get("orcid_status") == "enriched":
            p["sources"].add("orcid")

    # Merge OpenReview
    for orp in or_profiles:
        p = get_or_create(name=orp.get("name"))
        p["sources"].add("openreview")
        p["openreview_id"] = orp.get("openreview_id")
        if orp.get("homepage") and orp["homepage"] not in p["homepages"]:
            p["homepages"].append(orp["homepage"])
        if orp.get("dblp"):
            p["dblp_pid"] = orp["dblp"]
        p["institution"] = orp.get("current_institution") or p.get("institution")

    # Merge DBLP
    for d in dblp_enriched:
        p = get_or_create(d.get("orcid"), d.get("openalex_id"), d.get("name"))
        p["sources"].add("dblp")
        p["dblp_pid"] = d.get("dblp_pid") or p.get("dblp_pid")
        if d.get("dblp_homepage") and d["dblp_homepage"] not in p["homepages"]:
            p["homepages"].append(d["dblp_homepage"])

    # Merge S2
    for s in s2_enriched:
        p = get_or_create(s.get("orcid") or s.get("s2_orcid"), s.get("openalex_id"), s.get("name"))
        p["sources"].add("s2")
        p["s2_id"] = s.get("s2_id")
        if s.get("s2_homepage") and s["s2_homepage"] not in p["homepages"]:
            p["homepages"].append(s["s2_homepage"])

    # Merge homepage emails
    for he in homepage_emails:
        p = get_or_create(he.get("orcid"), he.get("openalex_id"), he.get("name"))
        for e in he.get("homepage_emails", []):
            if e not in [x.get("email") if isinstance(x, dict) else x for x in p["emails"]]:
                p["emails"].append({"email": e, "source": "homepage"})

    # Merge PubMed emails (match by author name)
    for pm in pubmed_emails:
        for author_name in pm.get("authors", []):
            nname = normalize_name(author_name)
            if nname in by_name:
                p = by_name[nname]
                for e in pm.get("corr_emails", []):
                    if e not in [x.get("email") if isinstance(x, dict) else x for x in p["emails"]]:
                        p["emails"].append({"email": e, "source": "pubmed_corr"})

    # Collect all unique profiles
    seen_ids = set()
    all_profiles = []
    for store in [by_orcid, by_oaid, by_name]:
        for p in store.values():
            pid = id(p)
            if pid not in seen_ids:
                seen_ids.add(pid)
                p["sources"] = sorted(list(p["sources"]))
                all_profiles.append(p)

    return all_profiles


def main():
    parser = argparse.ArgumentParser(description="S9: Merge pipeline")
    parser.add_argument("--input-dir", type=str, default=DATA_DIR)
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/merged_profiles.jsonl")
    args = parser.parse_args()

    print(f"[S9] Merging from {args.input_dir}/")
    profiles = merge_profiles(args.input_dir)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False, default=str) + "\n")

    with_email = sum(1 for p in profiles if p.get("emails"))
    with_hp = sum(1 for p in profiles if p.get("homepages"))
    print(f"[S9] Merged: {len(profiles)} profiles")
    print(f"  With email: {with_email} ({100*with_email/max(len(profiles),1):.1f}%)")
    print(f"  With homepage: {with_hp}")
    print(f"  → {args.output}")


if __name__ == "__main__":
    main()
