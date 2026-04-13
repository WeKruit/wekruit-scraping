"""
S1: OpenAlex Paper & Author Fetch
Uses pyalex to batch-fetch papers by concept/venue/keyword,
then extracts and deduplicates author records.

Usage:
  python scripts/s1_openalex_fetch.py --concept "artificial intelligence" --since 2023 --max-papers 5000
  python scripts/s1_openalex_fetch.py --venue "NeurIPS" --since 2024
  python scripts/s1_openalex_fetch.py --search "transformer attention" --max-papers 1000
"""
import argparse, json, os, sys, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import OPENALEX_EMAIL, OPENALEX_API_KEY, DATA_DIR

from pyalex import Works, Authors, config as pyalex_config
from tqdm import tqdm

pyalex_config.email = OPENALEX_EMAIL
if OPENALEX_API_KEY:
    pyalex_config.api_key = OPENALEX_API_KEY


def fetch_works(concept=None, venue=None, search=None, since=None, max_papers=5000):
    """Fetch papers from OpenAlex with cursor pagination."""
    query = Works()

    if search:
        query = query.search(search)

    filters = {}
    if concept:
        # Try to use concept as display name search
        filters["concepts.display_name"] = concept
    if venue:
        filters["primary_location.source.display_name"] = venue
    if since:
        filters["from_publication_date"] = f"{since}-01-01"

    if filters:
        query = query.filter(**filters)

    query = query.sort(cited_by_count="desc")

    papers = []
    authors_seen = {}
    page_count = 0

    print(f"[S1] Fetching papers... (max {max_papers})")

    for page in query.paginate(per_page=200):
        for work in page:
            paper_rec = {
                "openalex_id": work.get("id"),
                "title": work.get("title", ""),
                "doi": work.get("doi"),
                "publication_date": work.get("publication_date"),
                "year": work.get("publication_year"),
                "cited_by_count": work.get("cited_by_count", 0),
                "venue": (work.get("primary_location", {}) or {}).get("source", {})
                         and work["primary_location"]["source"].get("display_name"),
                "type": work.get("type"),
                "concepts": [c.get("display_name") for c in (work.get("concepts") or [])[:5]],
                "authorships": [],
            }

            for authorship in work.get("authorships", []):
                author = authorship.get("author", {})
                author_id = author.get("id")
                insts = authorship.get("institutions", [])
                inst_name = insts[0].get("display_name") if insts else None
                inst_ror = insts[0].get("ror") if insts else None
                inst_country = insts[0].get("country_code") if insts else None

                auth_rec = {
                    "openalex_id": author_id,
                    "name": author.get("display_name"),
                    "orcid": author.get("orcid"),
                    "institution": inst_name,
                    "institution_ror": inst_ror,
                    "institution_country": inst_country,
                    "is_corresponding": authorship.get("is_corresponding", False),
                }
                paper_rec["authorships"].append(auth_rec)

                # Deduplicate authors
                if author_id and author_id not in authors_seen:
                    authors_seen[author_id] = {
                        "openalex_id": author_id,
                        "name": author.get("display_name"),
                        "orcid": author.get("orcid"),
                        "institution": inst_name,
                        "institution_ror": inst_ror,
                        "institution_country": inst_country,
                        "paper_count_in_batch": 0,
                    }
                if author_id:
                    authors_seen[author_id]["paper_count_in_batch"] += 1

            papers.append(paper_rec)

        page_count += 1
        print(f"  Page {page_count}: {len(papers)} papers, {len(authors_seen)} unique authors")

        if len(papers) >= max_papers:
            break

    return papers, list(authors_seen.values())


def enrich_top_authors(authors, top_n=500):
    """Fetch detailed author info for top N authors from OpenAlex."""
    print(f"\n[S1] Enriching top {top_n} authors with detail API...")
    sorted_authors = sorted(authors, key=lambda a: a.get("paper_count_in_batch", 0), reverse=True)

    enriched = []
    for auth in tqdm(sorted_authors[:top_n], desc="Author detail"):
        oa_id = auth["openalex_id"]
        try:
            detail = Authors()[oa_id]
            auth.update({
                "works_count": detail.get("works_count", 0),
                "cited_by_count": detail.get("cited_by_count", 0),
                "orcid": detail.get("orcid") or auth.get("orcid"),
                "last_known_institutions": [
                    {"name": i.get("display_name"), "ror": i.get("ror"), "country": i.get("country_code")}
                    for i in (detail.get("last_known_institutions") or [])
                ],
                "topics": [t.get("display_name") for t in (detail.get("topics") or [])[:5]],
            })
            enriched.append(auth)
            time.sleep(0.01)  # be polite
        except Exception as e:
            print(f"  ⚠ Failed {oa_id}: {e}")
            enriched.append(auth)

    return enriched


def save_jsonl(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  Saved {len(data)} records → {path}")


def main():
    parser = argparse.ArgumentParser(description="S1: Fetch papers & authors from OpenAlex")
    parser.add_argument("--concept", type=str, help="Concept/topic filter (e.g. 'artificial intelligence')")
    parser.add_argument("--venue", type=str, help="Venue filter (e.g. 'NeurIPS', 'ICLR')")
    parser.add_argument("--search", type=str, help="Full-text search query")
    parser.add_argument("--since", type=int, default=2023, help="Publication year lower bound")
    parser.add_argument("--max-papers", type=int, default=5000, help="Max papers to fetch")
    parser.add_argument("--enrich-top", type=int, default=500, help="Enrich top N authors with detail")
    parser.add_argument("--output-dir", type=str, default=DATA_DIR)
    args = parser.parse_args()

    print(f"[S1] OpenAlex Fetch")
    print(f"  Concept: {args.concept}")
    print(f"  Venue: {args.venue}")
    print(f"  Search: {args.search}")
    print(f"  Since: {args.since}")

    papers, authors = fetch_works(
        concept=args.concept, venue=args.venue, search=args.search,
        since=args.since, max_papers=args.max_papers
    )
    print(f"\n[S1] Result: {len(papers)} papers, {len(authors)} unique authors")

    if args.enrich_top > 0:
        authors = enrich_top_authors(authors, top_n=args.enrich_top)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_jsonl(papers, f"{args.output_dir}/papers_{ts}.jsonl")
    save_jsonl(authors, f"{args.output_dir}/authors_{ts}.jsonl")

    # Also save latest symlink-style
    save_jsonl(papers, f"{args.output_dir}/papers.jsonl")
    save_jsonl(authors, f"{args.output_dir}/authors.jsonl")

    # Summary stats
    with_orcid = sum(1 for a in authors if a.get("orcid"))
    print(f"\n[S1] Summary:")
    print(f"  Papers: {len(papers)}")
    print(f"  Authors: {len(authors)}")
    print(f"  With ORCID: {with_orcid} ({100*with_orcid/max(len(authors),1):.1f}%)")


if __name__ == "__main__":
    main()
