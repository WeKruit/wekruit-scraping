#!/usr/bin/env python3
"""
GitHub Talent Discovery — Full Pipeline
=========================================
End-to-end orchestrator: discover repos -> extract contributors ->
enrich profiles -> score quality -> output CSV.

Usage:
    # Full pipeline (all sources)
    python3 github_pipeline.py --full

    # Discovery only (no contributor extraction)
    python3 github_pipeline.py --discover-only

    # Trending scan only (quick daily check)
    python3 github_pipeline.py --trending-only

    # From Devpost repos only
    python3 github_pipeline.py --from-devpost

    # Skip discovery, just re-process existing repos.json
    python3 github_pipeline.py --enrich-only

    # Re-score existing candidates
    python3 github_pipeline.py --score-only

    # Limit repos to process (for testing)
    python3 github_pipeline.py --full --limit 10
"""

import argparse, os, sys, time, json
from datetime import datetime

from github_config import OUTPUT_DIR, HEADERS
from github_discover import GitHubDiscoverer
from github_contributors import GitHubContributors
from github_scorer import GitHubScorer


def run_pipeline(mode="full", limit=None, threshold=40, workers=5):
    """Run the full or partial pipeline."""
    start_time = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n{'#'*60}")
    print(f"  GitHub Talent Discovery Pipeline")
    print(f"  Mode: {mode}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Token: {'configured' if HEADERS.get('Authorization') else 'NOT SET!'}")
    print(f"{'#'*60}\n")

    repos_path = os.path.join(OUTPUT_DIR, "repos.json")
    candidates_path = os.path.join(OUTPUT_DIR, "candidates.json")

    # ── Phase 1: Discovery ──
    if mode in ("full", "discover-only", "trending-only", "new-only", "events-only", "from-devpost"):
        source_map = {
            "full": None,  # All sources
            "discover-only": None,
            "trending-only": ["trending"],
            "new-only": ["new"],
            "events-only": ["events"],
            "from-devpost": ["devpost"],
        }
        sources = source_map.get(mode)

        discoverer = GitHubDiscoverer()
        repos = discoverer.discover_all(sources=sources)
        discoverer.save(repos)
        print(f"\n  Phase 1 complete: {len(repos)} repos discovered")

        if mode == "discover-only":
            _print_summary(start_time, repos=len(repos))
            return

    # ── Phase 2+3: Contributor extraction + enrichment ──
    if mode in ("full", "trending-only", "new-only", "events-only", "from-devpost", "enrich-only"):
        if not os.path.exists(repos_path):
            print(f"Error: {repos_path} not found. Run discovery first.")
            sys.exit(1)

        with open(repos_path, "r") as f:
            repos = json.load(f)

        extractor = GitHubContributors(workers=workers)
        candidates = extractor.extract_all(repos, limit=limit)
        extractor.save(candidates)
        print(f"\n  Phase 2+3 complete: {len(candidates)} candidates enriched")

    # ── Phase 4+5: Scoring + output ──
    if mode in ("full", "trending-only", "new-only", "events-only", "from-devpost", "enrich-only", "score-only"):
        if not os.path.exists(candidates_path):
            print(f"Error: {candidates_path} not found. Run extraction first.")
            sys.exit(1)

        with open(candidates_path, "r") as f:
            candidates = json.load(f)

        scorer = GitHubScorer(threshold=threshold)
        scored = scorer.score_all(candidates)
        scorer.save(scored)
        print(f"\n  Phase 4+5 complete: {len(scored)} candidates above threshold")

    elapsed = time.time() - start_time
    _print_summary(start_time, elapsed=elapsed)


def _print_summary(start_time, repos=None, elapsed=None):
    """Print pipeline execution summary."""
    elapsed = elapsed or (time.time() - start_time)
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n{'#'*60}")
    print(f"  Pipeline Complete")
    print(f"  Duration: {mins}m {secs}s")
    print(f"{'#'*60}")

    # Show what's in output/
    if os.path.exists(OUTPUT_DIR):
        files = sorted(os.listdir(OUTPUT_DIR))
        print(f"\n  Output files:")
        for f in files:
            path = os.path.join(OUTPUT_DIR, f)
            size_kb = os.path.getsize(path) / 1024
            print(f"    {f} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Talent Discovery Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 github_pipeline.py --full              Full pipeline, all sources
  python3 github_pipeline.py --trending-only     Quick daily trending scan
  python3 github_pipeline.py --from-devpost      Repos from Devpost scrapes
  python3 github_pipeline.py --discover-only     Discovery only, no enrichment
  python3 github_pipeline.py --enrich-only       Re-process existing repos.json
  python3 github_pipeline.py --score-only        Re-score existing candidates
  python3 github_pipeline.py --full --limit 10   Test run with 10 repos
        """,
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--full", action="store_true", help="Full pipeline, all sources")
    mode_group.add_argument("--discover-only", action="store_true", help="Discovery phase only")
    mode_group.add_argument("--trending-only", action="store_true", help="Trending scan only")
    mode_group.add_argument("--new-only", action="store_true", help="New repos radar only")
    mode_group.add_argument("--events-only", action="store_true", help="Events firehose only")
    mode_group.add_argument("--from-devpost", action="store_true", help="Devpost repos only")
    mode_group.add_argument("--enrich-only", action="store_true", help="Skip discovery, enrich existing repos.json")
    mode_group.add_argument("--score-only", action="store_true", help="Re-score existing candidates")

    parser.add_argument("--limit", type=int, default=None, help="Limit repos to process (for testing)")
    parser.add_argument("--threshold", type=int, default=40, help="Minimum score threshold (default: 40)")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent enrichment workers (default: 5)")
    args = parser.parse_args()

    # Determine mode
    mode = "full"
    for m in ["full", "discover_only", "trending_only", "new_only", "events_only", "from_devpost", "enrich_only", "score_only"]:
        if getattr(args, m, False):
            mode = m.replace("_", "-")
            break

    run_pipeline(mode=mode, limit=args.limit, threshold=args.threshold, workers=args.workers)


if __name__ == "__main__":
    main()
