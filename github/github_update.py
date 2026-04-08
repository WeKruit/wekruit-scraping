#!/usr/bin/env python3
"""
GitHub Talent Pipeline — Daily/Weekly Update
==============================================
Single command to run the full pipeline:
  1. Discover new repos (incremental merge)
  2. Categorize new repos
  3. Regenerate dashboard
  4. Print what's new

Usage:
    # Daily quick scan (trending + new repos only, ~5 min)
    python3 github_update.py --daily

    # Weekly full scan (all sources, ~1-2 hours)
    python3 github_update.py --weekly

    # Just refresh dashboard from existing data
    python3 github_update.py --dashboard-only

    # Show current stats
    python3 github_update.py --stats
"""

import json, os, sys, time, argparse
from datetime import datetime

from github_config import OUTPUT_DIR, HEADERS


def load_repos():
    """Load current repos.json."""
    path = os.path.join(OUTPUT_DIR, "repos.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def run_discover(sources, fresh=False):
    """Run discovery with specified sources."""
    from github_discover import GitHubDiscoverer
    discoverer = GitHubDiscoverer(incremental=not fresh)
    repos = discoverer.discover_all(sources=sources)
    discoverer.save(repos)
    return len(repos), len(repos) - discoverer._existing_count


def run_categorize():
    """Categorize uncategorized repos."""
    from github_categorizer import categorize_repos
    repos = load_repos()
    uncategorized = [r for r in repos if "_categories" not in r]
    if not uncategorized:
        print(f"\n  All {len(repos)} repos already categorized.")
        return 0

    categorize_repos(repos)

    # Save back
    path = os.path.join(OUTPUT_DIR, "repos.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)

    print(f"  Categorized {len(uncategorized)} new repos.")
    return len(uncategorized)


def run_dashboard():
    """Regenerate dashboard HTML."""
    from github_dashboard import generate_dashboard
    repos = load_repos()
    out_path = os.path.join(OUTPUT_DIR, "dashboard.html")
    generate_dashboard(repos, out_path)
    print(f"  Dashboard: {out_path}")


def print_stats():
    """Print current pipeline stats."""
    repos = load_repos()
    if not repos:
        print("  No repos found. Run --daily or --weekly first.")
        return

    total = len(repos)
    categorized = sum(1 for r in repos if "_categories" in r)

    # Star distribution
    star_tiers = {}
    for r in repos:
        tier = r.get("_star_tier", "unknown")
        star_tiers[tier] = star_tiers.get(tier, 0) + 1

    # Category distribution
    categories = {}
    for r in repos:
        cat = r.get("_primary_category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

    # Source distribution
    sources = {}
    for r in repos:
        for s in r.get("sources", []):
            key = s.split(":")[0]
            sources[key] = sources.get(key, 0) + 1

    # Owner types
    owners = {}
    for r in repos:
        ot = r.get("_owner_type", "unknown")
        owners[ot] = owners.get(ot, 0) + 1

    # Candidates
    cand_path = os.path.join(OUTPUT_DIR, "candidates.json")
    cand_count = 0
    cand_with_email = 0
    if os.path.exists(cand_path):
        with open(cand_path) as f:
            cands = json.load(f)
            cand_count = len(cands)
            cand_with_email = sum(1 for c in cands if c.get("emails"))

    print(f"\n{'='*55}")
    print(f"  GitHub Talent Pipeline Status")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")
    print(f"\n  Repos: {total:,} total, {categorized:,} categorized")
    print(f"  Candidates: {cand_count:,} enriched, {cand_with_email:,} with email")

    print(f"\n  Star tiers:")
    tier_order = ["100k+", "50k-100k", "10k-50k", "5k-10k", "1k-5k",
                  "500-1k", "100-500", "50-100", "10-50", "0-10"]
    for t in tier_order:
        if t in star_tiers:
            print(f"    {t:>10}: {star_tiers[t]:>6}")

    print(f"\n  Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat:<25}: {count:>6}")

    print(f"\n  Sources:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src:<12}: {count:>6}")

    print(f"\n  Owner types:")
    for ot, count in sorted(owners.items(), key=lambda x: -x[1]):
        print(f"    {ot:<12}: {count:>6}")

    # Files
    print(f"\n  Output files:")
    if os.path.exists(OUTPUT_DIR):
        for fname in sorted(os.listdir(OUTPUT_DIR)):
            fpath = os.path.join(OUTPUT_DIR, fname)
            size = os.path.getsize(fpath)
            if size > 1024 * 1024:
                print(f"    {fname:<35} {size/1024/1024:.1f} MB")
            else:
                print(f"    {fname:<35} {size/1024:.1f} KB")


def run_update(mode="daily"):
    """Run the full update pipeline."""
    start = time.time()

    print(f"\n{'#'*60}")
    print(f"  GitHub Talent Pipeline — {mode.upper()} Update")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Token: {'set' if HEADERS.get('Authorization') else 'NOT SET!'}")
    print(f"{'#'*60}")

    # Step 1: Discover
    if mode == "daily":
        sources = ["trending", "new"]
        print(f"\n[1/3] Quick discovery (trending + new repos)...")
    elif mode == "weekly":
        sources = ["search", "topics", "new", "trending", "devpost"]
        print(f"\n[1/3] Full discovery (all sources)...")
    else:
        sources = None

    total, new = run_discover(sources)

    # Step 2: Categorize
    print(f"\n[2/3] Categorizing new repos...")
    newly_categorized = run_categorize()

    # Step 3: Dashboard
    print(f"\n[3/3] Regenerating dashboard...")
    try:
        run_dashboard()
    except Exception as e:
        print(f"  Dashboard generation failed: {e}")
        print("  (Run `python3 github_dashboard.py` manually)")

    # Summary
    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n{'#'*60}")
    print(f"  Update Complete")
    print(f"  Duration: {mins}m {secs}s")
    print(f"  Total repos: {total:,}")
    print(f"  New this run: {new:,}")
    print(f"  Newly categorized: {newly_categorized}")
    print(f"{'#'*60}")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Talent Pipeline — Update Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 github_update.py --daily          Quick daily scan (~5 min)
  python3 github_update.py --weekly         Full weekly scan (~1-2 hours)
  python3 github_update.py --dashboard-only Refresh dashboard from existing data
  python3 github_update.py --stats          Show current pipeline stats

Schedule with cron/launchd:
  Daily:  0 8 * * * cd /path/to/github && GITHUB_TOKEN=xxx python3 github_update.py --daily
  Weekly: 0 2 * * 1 cd /path/to/github && GITHUB_TOKEN=xxx python3 github_update.py --weekly
        """,
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--daily", action="store_true", help="Quick scan: trending + new repos")
    mode_group.add_argument("--weekly", action="store_true", help="Full scan: all sources")
    mode_group.add_argument("--dashboard-only", action="store_true", help="Refresh dashboard only")
    mode_group.add_argument("--stats", action="store_true", help="Show pipeline stats")
    args = parser.parse_args()

    if args.stats:
        print_stats()
    elif args.dashboard_only:
        print("Refreshing dashboard...")
        run_dashboard()
    elif args.daily:
        run_update("daily")
    elif args.weekly:
        run_update("weekly")


if __name__ == "__main__":
    main()
