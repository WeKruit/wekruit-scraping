#!/usr/bin/env python3
"""
GitHub Talent Discovery — Repo Categorizer
=============================================
Categorizes discovered repos by AI domain, owner type, and star tier.
Operates incrementally — only processes repos missing metadata fields.

Usage:
    python3 github_categorizer.py                    # Categorize uncategorized repos
    python3 github_categorizer.py --force            # Re-categorize all repos
    python3 github_categorizer.py --stats            # Show category distribution only
"""

from __future__ import annotations

import json, os, sys, argparse, re
from collections import Counter
from typing import Optional

from github_config import OUTPUT_DIR


# ── Category Definitions ──
# Each entry: (category_name, list_of_keyword_patterns)
# Priority order matters — first match becomes _primary_category.
CATEGORY_RULES = [
    ("Agent", [
        r"\bagent\b", r"\bagentic\b", r"\bmulti[_-]?agent\b", r"\bautonomous\b",
    ]),
    ("RAG", [
        r"\brag\b", r"\bretrieval\b", r"\bvector\b", r"\bembedding\b",
        r"\bsemantic[_-]?search\b",
    ]),
    ("MCP/Tools", [
        r"\bmcp\b", r"\bmodel[_-]?context\b", r"\bfunction[_-]?call\b",
        r"\btool[_-]?use\b",
    ]),
    ("Chatbot/Assistant", [
        r"\bchatbot\b", r"\bchat\b", r"\bassistant\b", r"\bcopilot\b",
    ]),
    ("Fine-tuning", [
        r"\bfine[_-]?tun", r"\btraining\b", r"\blora\b", r"\bqlora\b",
    ]),
    ("Inference/Serving", [
        r"\binference\b", r"\bserving\b", r"\bdeploy\b", r"\bquantiz",
        r"\bvllm\b", r"\bollama\b",
    ]),
    ("Image Gen", [
        r"\bdiffusion\b", r"\bimage[_-]?gen", r"\bstable[_-]?diffusion\b",
        r"\bcomfyui\b",
    ]),
    ("Voice/Audio", [
        r"\bvoice\b", r"\btts\b", r"\bspeech\b", r"\baudio\b", r"\bwhisper\b",
    ]),
    ("AI Coding", [
        r"\bcoding\b", r"\bcode[_-]?gen", r"\bide\b", r"\bdeveloper[_-]?tool\b",
        r"\bclaude[_-]?code\b", r"\bcursor\b",
    ]),
    ("Workflow/Automation", [
        r"\bworkflow\b", r"\bautomation\b", r"\bpipeline\b", r"\borchestrat",
    ]),
    ("NLP/Transformers", [
        r"\bnlp\b", r"\btransformer\b", r"\bbert\b", r"\blanguage[_-]?model\b",
        r"\bhugging\s?face\b",
    ]),
    ("Data/Scraping", [
        r"\bdata\b", r"\bscraping\b", r"\bcrawl\b", r"\bextract\b", r"\bparser\b",
    ]),
]

# Compiled regex per category for speed
_COMPILED_RULES = [
    (name, re.compile("|".join(patterns), re.IGNORECASE))
    for name, patterns in CATEGORY_RULES
]

# ── Big Tech Org List ──
BIG_TECH_ORGS = {
    "microsoft", "google", "google-deepmind", "google-research",
    "meta", "meta-llama", "aws", "amazon", "nvidia", "apple",
    "huggingface", "openai", "anthropic", "langchain-ai",
    "alibaba", "tencent", "baidu", "bytedance",
    "deepseek", "mistralai", "cohere", "stability-ai",
}

# ── Star Tier Thresholds (descending) ──
STAR_TIER_THRESHOLDS = [
    (100_000, "100k+"),
    (50_000,  "50k-100k"),
    (10_000,  "10k-50k"),
    (5_000,   "5k-10k"),
    (1_000,   "1k-5k"),
    (500,     "500-1k"),
    (100,     "100-500"),
    (50,      "50-100"),
    (10,      "10-50"),
    (0,       "0-10"),
]


def _build_text(repo: dict) -> str:
    """Build a searchable text blob from repo metadata."""
    parts = [
        repo.get("full_name", ""),
        repo.get("description", ""),
    ]
    parts.extend(repo.get("topics", []))
    parts.extend(repo.get("sources", []))
    return " ".join(parts).lower()


def _classify_categories(text: str) -> list[str]:
    """Return all matching category names for the given text."""
    matches = []
    for name, pattern in _COMPILED_RULES:
        if pattern.search(text):
            matches.append(name)
    return matches if matches else ["Other AI"]


def _classify_owner(full_name: str) -> str:
    """Classify repo owner as big_tech, company, or personal."""
    owner = full_name.split("/")[0].lower() if "/" in full_name else ""

    if owner in BIG_TECH_ORGS:
        return "big_tech"

    # Heuristic: org names with hyphens, multiple words, or ending in
    # -ai, -io, -dev, -labs, -inc tend to be companies/orgs.
    org_signals = [
        "-ai", "-io", "-dev", "-labs", "-inc", "-corp", "-hq",
        "-team", "-project", "-org", "-official", "-studio",
    ]
    if any(owner.endswith(suffix) for suffix in org_signals):
        return "company"

    # Names with hyphens that look like org slugs (2+ segments)
    if owner.count("-") >= 1 and len(owner) > 10:
        return "company"

    return "personal"


def _classify_star_tier(stars: int) -> str:
    """Map star count to a tier label."""
    for threshold, label in STAR_TIER_THRESHOLDS:
        if stars >= threshold:
            return label
    return "0-10"


def categorize_repo(repo: dict) -> dict:
    """Add _categories, _primary_category, _owner_type, _star_tier to a repo dict."""
    text = _build_text(repo)
    categories = _classify_categories(text)

    repo["_categories"] = categories
    repo["_primary_category"] = categories[0]
    repo["_owner_type"] = _classify_owner(repo.get("full_name", ""))
    repo["_star_tier"] = _classify_star_tier(repo.get("stars", 0))

    return repo


def categorize_repos(repos: list[dict], force: bool = False) -> tuple[list[dict], int]:
    """Categorize repos in-place. Returns (repos, count_categorized).

    Args:
        repos: List of repo dicts (mutated in-place).
        force: If True, re-categorize all repos. Otherwise skip repos
               that already have a ``_categories`` field.

    Returns:
        Tuple of (repos list, number of repos categorized this run).
    """
    categorized = 0

    for repo in repos:
        if not force and "_categories" in repo:
            continue
        categorize_repo(repo)
        categorized += 1

    return repos, categorized


def print_stats(repos: list[dict]) -> None:
    """Print distribution statistics for categorized repos."""
    total = len(repos)
    has_cats = [r for r in repos if "_categories" in r]

    print(f"\nRepo Categorization Stats")
    print(f"{'='*60}")
    print(f"  Total repos:       {total}")
    print(f"  Categorized:       {len(has_cats)}")
    print(f"  Uncategorized:     {total - len(has_cats)}")

    if not has_cats:
        print("\n  No categorized repos to analyze.")
        return

    # ── Category distribution (repos can appear in multiple) ──
    cat_counter: Counter[str] = Counter()
    for r in has_cats:
        for cat in r.get("_categories", []):
            cat_counter[cat] += 1

    print(f"\n  Category Distribution")
    print(f"  {'-'*56}")
    for cat, count in cat_counter.most_common():
        pct = count / len(has_cats) * 100
        bar = "#" * int(pct / 2)
        print(f"    {cat:<22} {count:>6}  ({pct:5.1f}%)  {bar}")

    # ── Primary category distribution ──
    primary_counter: Counter[str] = Counter()
    for r in has_cats:
        primary_counter[r.get("_primary_category", "Other AI")] += 1

    print(f"\n  Primary Category Distribution")
    print(f"  {'-'*56}")
    for cat, count in primary_counter.most_common():
        pct = count / len(has_cats) * 100
        bar = "#" * int(pct / 2)
        print(f"    {cat:<22} {count:>6}  ({pct:5.1f}%)  {bar}")

    # ── Owner type distribution ──
    owner_counter: Counter[str] = Counter()
    for r in has_cats:
        owner_counter[r.get("_owner_type", "personal")] += 1

    print(f"\n  Owner Type Distribution")
    print(f"  {'-'*56}")
    for owner_type, count in owner_counter.most_common():
        pct = count / len(has_cats) * 100
        bar = "#" * int(pct / 2)
        print(f"    {owner_type:<22} {count:>6}  ({pct:5.1f}%)  {bar}")

    # ── Star tier distribution ──
    tier_counter: Counter[str] = Counter()
    for r in has_cats:
        tier_counter[r.get("_star_tier", "0-10")] += 1

    # Sort tiers by threshold order
    tier_order = [label for _, label in STAR_TIER_THRESHOLDS]
    print(f"\n  Star Tier Distribution")
    print(f"  {'-'*56}")
    for tier in tier_order:
        count = tier_counter.get(tier, 0)
        if count == 0:
            continue
        pct = count / len(has_cats) * 100
        bar = "#" * int(pct / 2)
        print(f"    {tier:<22} {count:>6}  ({pct:5.1f}%)  {bar}")

    # ── Multi-category repos ──
    multi = [r for r in has_cats if len(r.get("_categories", [])) > 1]
    print(f"\n  Multi-category repos:  {len(multi)} ({len(multi)/len(has_cats)*100:.1f}%)")

    # ── Top repos per category ──
    print(f"\n  Top 3 Repos Per Category (by stars)")
    print(f"  {'-'*56}")
    for cat in [name for name, _ in CATEGORY_RULES] + ["Other AI"]:
        in_cat = [r for r in has_cats if cat in r.get("_categories", [])]
        if not in_cat:
            continue
        in_cat.sort(key=lambda r: -r.get("stars", 0))
        top3 = in_cat[:3]
        print(f"    {cat}:")
        for r in top3:
            stars = r.get("stars", 0)
            stars_fmt = f"{stars:,}"
            print(f"      {r['full_name']:<45} {stars_fmt:>10} stars")


def load_repos(path: str | None = None) -> list[dict]:
    """Load repos from JSON file."""
    path = path or os.path.join(OUTPUT_DIR, "repos.json")
    if not os.path.exists(path):
        print(f"Error: repos file not found: {path}")
        print("Run github_discover.py first to generate repos.json")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        repos = json.load(f)

    return repos


def save_repos(repos: list[dict], path: str | None = None) -> None:
    """Save repos back to JSON file."""
    path = path or os.path.join(OUTPUT_DIR, "repos.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(path) / 1024
    print(f"  Saved {len(repos)} repos to {path} ({size_kb:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Repo Categorizer — classify repos by AI domain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 github_categorizer.py                    Categorize uncategorized repos
  python3 github_categorizer.py --force            Re-categorize all repos
  python3 github_categorizer.py --stats            Show category distribution only
  python3 github_categorizer.py --input path.json  Use custom input file
        """,
    )
    parser.add_argument("--force", action="store_true",
                        help="Re-categorize all repos, even those already categorized")
    parser.add_argument("--stats", action="store_true",
                        help="Show category distribution without modifying data")
    parser.add_argument("--input", default=None,
                        help="Path to repos JSON file (default: output/repos.json)")

    args = parser.parse_args()

    repos_path = args.input or os.path.join(OUTPUT_DIR, "repos.json")
    repos = load_repos(repos_path)
    print(f"Loaded {len(repos)} repos from {repos_path}")

    if args.stats:
        print_stats(repos)
        return

    # Count how many already categorized
    already = sum(1 for r in repos if "_categories" in r)
    to_process = len(repos) if args.force else len(repos) - already

    print(f"\nRepo Categorization")
    print(f"{'='*60}")
    print(f"  Already categorized: {already}")
    print(f"  To categorize:       {to_process}")
    print(f"  Force mode:          {'yes' if args.force else 'no'}")

    if to_process == 0:
        print(f"\n  Nothing to do — all repos already categorized.")
        print(f"  Use --force to re-categorize or --stats to view distribution.")
        return

    repos, count = categorize_repos(repos, force=args.force)

    print(f"\n  Categorized {count} repos")

    # Save
    print(f"\nSaving results...")
    save_repos(repos, repos_path)

    # Show stats
    print_stats(repos)


if __name__ == "__main__":
    main()
