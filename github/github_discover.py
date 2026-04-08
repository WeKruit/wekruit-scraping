#!/usr/bin/env python3
"""
GitHub Talent Discovery — Project Discovery (v2)
==================================================
Discovers AI-related GitHub repositories from 6 sources:
  1. GitHub Search API — paginated (up to 1000 results per query)
  2. Topic-based search — by GitHub topics
  3. New repos radar — recently created, low star threshold
  4. GitHub Trending — daily/weekly HTML scrape
  5. GitHub Events firehose — real-time CreateEvent/WatchEvent
  6. Devpost integration — GitHub links from hackathon scrapes

Usage:
    python3 github_discover.py                     # All sources
    python3 github_discover.py --search-only       # Search API only
    python3 github_discover.py --trending-only     # Trending only
    python3 github_discover.py --new-only          # New repos radar only
    python3 github_discover.py --events-only       # Events firehose only
    python3 github_discover.py --devpost-only      # Devpost repos only
"""

import requests
from bs4 import BeautifulSoup
import json, time, os, sys, argparse, re
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote

from github_config import (
    API_BASE, HEADERS, SEARCH_KEYWORDS, STAR_RANGES, LANGUAGES,
    TOPICS, TRENDING_LANGUAGES, TRENDING_PERIODS, SEED_REPOS,
    DEVPOST_OUTPUT_DIR, OUTPUT_DIR, SEARCH_DELAY, REQUEST_DELAY,
    RETRY_MAX, RETRY_BACKOFF_BASE, PUSHED_AFTER_MONTHS, CREATED_AFTER_MONTHS,
)

WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# AI-related keywords for filtering events firehose
AI_KEYWORDS_RE = re.compile(
    r'\b(llm|gpt|ai agent|langchain|rag|vector|embedding|transformer|'
    r'chatbot|copilot|fine.?tun|inference|diffusion|neural|deep.?learn|'
    r'machine.?learn|nlp|anthropic|openai|hugging.?face|llama|mistral|'
    r'gemma|claude|mcp|function.?call|multi.?modal|gen.?ai|agentic)\b',
    re.IGNORECASE
)


class GitHubDiscoverer:
    def __init__(self, incremental=True):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.repos = {}  # full_name -> repo dict (dedup key)
        self.api_calls = 0
        self.search_calls = 0
        self._existing_count = 0

        # Incremental: load existing repos.json so we merge, not overwrite
        if incremental:
            repos_path = os.path.join(OUTPUT_DIR, "repos.json")
            if os.path.exists(repos_path):
                try:
                    with open(repos_path, "r") as f:
                        existing = json.load(f)
                    for r in existing:
                        key = r["full_name"].lower()
                        self.repos[key] = r
                    self._existing_count = len(self.repos)
                except Exception:
                    pass

    def _api_get(self, url, params=None, is_search=False):
        """Make a GitHub API call with rate-limit handling."""
        for attempt in range(RETRY_MAX):
            try:
                resp = self.session.get(url, params=params, timeout=30)

                # Rate limit detection
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
                if remaining < 10:
                    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_ts - time.time(), 1) + 5
                    print(f"  [rate-limit] {remaining} remaining, sleeping {wait:.0f}s", flush=True)
                    time.sleep(wait)

                if resp.status_code == 403 and "rate limit" in resp.text.lower():
                    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_ts - time.time(), 60) + 5
                    print(f"  [rate-limit] 403 hit, sleeping {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue

                if resp.status_code == 422:
                    print(f"  [422] Bad query: {resp.json().get('message', '')[:80]}")
                    return None

                resp.raise_for_status()

                if is_search:
                    self.search_calls += 1
                else:
                    self.api_calls += 1

                return resp.json()

            except requests.exceptions.ConnectionError:
                wait = RETRY_BACKOFF_BASE * (attempt + 1)
                print(f"  [conn-err] retry {attempt+1}/{RETRY_MAX} in {wait}s", flush=True)
                time.sleep(wait)
            except requests.exceptions.HTTPError:
                if resp.status_code == 404:
                    return None
                raise

        return None

    def _add_repo(self, full_name, stars, language, created_at, pushed_at,
                  description, topics, source, html_url=None):
        """Add or update a repo in the deduped collection."""
        key = full_name.lower()
        if key in self.repos:
            existing = self.repos[key]
            if source not in existing["sources"]:
                existing["sources"].append(source)
            if stars and stars > existing.get("stars", 0):
                existing["stars"] = stars
            return False
        else:
            self.repos[key] = {
                "full_name": full_name,
                "html_url": html_url or f"https://github.com/{full_name}",
                "stars": stars or 0,
                "language": language or "",
                "created_at": created_at or "",
                "pushed_at": pushed_at or "",
                "description": (description or "")[:500],
                "topics": topics or [],
                "sources": [source],
                "discovered_at": datetime.now().isoformat(),
            }
            return True

    def _search_paginated(self, q, source_tag, max_pages=10):
        """Run a search query with full pagination (up to 1000 results)."""
        total_new = 0
        total_results = 0

        for page in range(1, max_pages + 1):
            data = self._api_get(
                f"{API_BASE}/search/repositories",
                params={"q": q, "sort": "stars", "order": "desc",
                        "per_page": 100, "page": page},
                is_search=True,
            )
            time.sleep(SEARCH_DELAY)

            if not data or "items" not in data:
                break

            if page == 1:
                total_results = data.get("total_count", 0)

            items = data["items"]
            if not items:
                break

            for item in items:
                added = self._add_repo(
                    full_name=item["full_name"],
                    stars=item.get("stargazers_count", 0),
                    language=item.get("language", ""),
                    created_at=item.get("created_at", ""),
                    pushed_at=item.get("pushed_at", ""),
                    description=item.get("description", ""),
                    topics=item.get("topics", []),
                    source=source_tag,
                    html_url=item.get("html_url", ""),
                )
                if added:
                    total_new += 1

            # Stop if we've fetched all results
            fetched = page * 100
            if fetched >= min(total_results, 1000):
                break

        return total_new, total_results

    # ── Source 1: GitHub Search API (paginated) ──

    def search_repos(self):
        """Run the keyword x star x language search matrix with pagination."""
        print("\n[Source 1] GitHub Search API (paginated)")
        print("=" * 55)

        pushed_after = (datetime.now() - timedelta(days=PUSHED_AFTER_MONTHS * 30)).strftime("%Y-%m-%d")

        total_new = 0
        query_count = 0

        for group_name, keywords in SEARCH_KEYWORDS.items():
            print(f"\n  [{group_name}]")
            for keyword in keywords:
                for lang in LANGUAGES:
                    for range_name, (star_min, star_max) in STAR_RANGES.items():
                        star_q = f"stars:{star_min}..{star_max}" if star_max else f"stars:>={star_min}"
                        q = f"{keyword} language:{lang} {star_q} pushed:>{pushed_after}"

                        query_count += 1
                        new, total = self._search_paginated(q, f"search:{group_name}")

                        total_new += new
                        pages_needed = min((total + 99) // 100, 10) if total > 100 else 1
                        if new > 0:
                            print(f"    {keyword}/{lang}/{range_name}: +{new} new "
                                  f"({total} total, {pages_needed} pages)")

        print(f"\n  Search complete: {query_count} queries, {total_new} new repos, "
              f"total in collection: {len(self.repos)}")
        return total_new

    # ── Source 2: Topic-based search (paginated) ──

    def search_topics(self):
        """Search by GitHub topics with pagination."""
        print("\n[Source 2] Topic Search (paginated)")
        print("=" * 55)

        pushed_after = (datetime.now() - timedelta(days=PUSHED_AFTER_MONTHS * 30)).strftime("%Y-%m-%d")
        total_new = 0

        for topic in TOPICS:
            for range_name, (star_min, star_max) in STAR_RANGES.items():
                star_q = f"stars:{star_min}..{star_max}" if star_max else f"stars:>={star_min}"
                q = f"topic:{topic} {star_q} pushed:>{pushed_after}"

                new, total = self._search_paginated(q, f"topic:{topic}")

                total_new += new
                if new > 0:
                    print(f"    topic:{topic}/{range_name}: +{new} new ({total} total)")

        print(f"\n  Topic search complete: {total_new} new repos")
        return total_new

    # ── Source 3: New Repos Radar (low star threshold, recently created) ──

    def search_new_repos(self):
        """Find brand-new AI repos created in the last 7/30 days.
        These won't have 100+ stars yet — that's the whole point."""
        print("\n[Source 3] New Repos Radar")
        print("=" * 55)

        total_new = 0

        # Time windows: 7 days and 30 days
        windows = [
            ("7d",  (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),  0),
            ("30d", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), 5),
        ]

        # Broader keyword set for new repo detection
        new_repo_keywords = [
            "llm", "ai agent", "rag", "gpt", "chatbot", "copilot",
            "langchain", "fine-tuning", "embedding", "vector database",
            "transformer", "diffusion", "mcp", "agentic",
            "generative ai", "multimodal", "voice ai",
        ]

        for window_name, created_after, min_stars in windows:
            print(f"\n  [{window_name} window, stars >= {min_stars}]")
            for keyword in new_repo_keywords:
                for lang in LANGUAGES[:2]:  # python + typescript only for speed
                    star_q = f"stars:>={min_stars}" if min_stars else ""
                    q = f"{keyword} language:{lang} created:>{created_after} {star_q}".strip()

                    new, total = self._search_paginated(
                        q, f"new:{window_name}", max_pages=3  # 300 results max per query
                    )

                    total_new += new
                    if new > 0:
                        print(f"    {keyword}/{lang}: +{new} new ({total} total)")

        print(f"\n  New repos radar complete: {total_new} new repos")
        return total_new

    # ── Source 4: GitHub Trending ──

    def scrape_trending(self):
        """Scrape GitHub Trending pages for hot repos."""
        print("\n[Source 4] GitHub Trending")
        print("=" * 55)

        total_new = 0
        web_session = requests.Session()
        web_session.headers.update(WEB_HEADERS)

        for lang in TRENDING_LANGUAGES:
            for period in TRENDING_PERIODS:
                url = f"https://github.com/trending/{lang}?since={period}"
                print(f"  Fetching {lang}/{period}...", end=" ", flush=True)

                try:
                    resp = web_session.get(url, timeout=30)
                    resp.raise_for_status()
                except Exception as e:
                    print(f"error: {e}")
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                articles = soup.select("article.Box-row")

                new_count = 0
                for article in articles:
                    h2 = article.select_one("h2 a")
                    if not h2:
                        continue
                    href = h2.get("href", "").strip("/")
                    if not href or "/" not in href:
                        continue

                    stars = 0
                    for span in article.select("span.d-inline-block"):
                        txt = span.get_text(strip=True).replace(",", "")
                        if txt.isdigit():
                            stars = int(txt)
                            break

                    desc_el = article.select_one("p")
                    desc = desc_el.get_text(strip=True) if desc_el else ""

                    lang_el = article.select_one("span[itemprop='programmingLanguage']")
                    repo_lang = lang_el.get_text(strip=True) if lang_el else lang

                    added = self._add_repo(
                        full_name=href, stars=stars, language=repo_lang,
                        created_at="", pushed_at="", description=desc,
                        topics=[], source=f"trending:{lang}/{period}",
                    )
                    if added:
                        new_count += 1

                total_new += new_count
                print(f"{len(articles)} repos, +{new_count} new")
                time.sleep(1)

        print(f"\n  Trending complete: {total_new} new repos")
        return total_new

    # ── Source 5: GitHub Events Firehose ──

    def scan_events(self, pages=10):
        """Scan GitHub public events for AI-related repo activity.
        Catches repos being starred/created RIGHT NOW across all of GitHub."""
        print("\n[Source 5] GitHub Events Firehose")
        print("=" * 55)

        total_new = 0
        events_scanned = 0
        ai_events = 0

        for page in range(1, pages + 1):
            data = self._api_get(
                f"{API_BASE}/events",
                params={"per_page": 100, "page": page},
            )
            time.sleep(REQUEST_DELAY)

            if not data or not isinstance(data, list):
                break

            for event in data:
                events_scanned += 1
                event_type = event.get("type", "")
                repo = event.get("repo", {})
                repo_name = repo.get("name", "")

                if not repo_name or "/" not in repo_name:
                    continue

                # Filter for relevant event types
                if event_type not in ("CreateEvent", "WatchEvent", "ForkEvent", "PublicEvent"):
                    continue

                # For CreateEvent, only care about new repositories
                if event_type == "CreateEvent":
                    payload = event.get("payload", {})
                    if payload.get("ref_type") != "repository":
                        continue

                # Check if the repo name or description matches AI keywords
                desc = event.get("payload", {}).get("description", "") or ""
                full_text = f"{repo_name} {desc}"

                if not AI_KEYWORDS_RE.search(full_text):
                    continue

                ai_events += 1
                added = self._add_repo(
                    full_name=repo_name, stars=0, language="",
                    created_at="", pushed_at="",
                    description=desc[:500],
                    topics=[], source=f"events:{event_type}",
                )
                if added:
                    total_new += 1

            print(f"  Page {page}: scanned {len(data)} events, "
                  f"AI-related: {ai_events}, new repos: {total_new}", flush=True)

        print(f"\n  Events firehose complete: {events_scanned} events scanned, "
              f"{ai_events} AI-related, {total_new} new repos")
        return total_new

    # ── Source 6: Devpost Integration ──

    def load_devpost_repos(self):
        """Extract GitHub repo URLs from Devpost scraper output."""
        print("\n[Source 6] Devpost Integration")
        print("=" * 55)

        devpost_dir = DEVPOST_OUTPUT_DIR
        if not os.path.isdir(devpost_dir):
            print(f"  Devpost output not found: {devpost_dir}")
            return 0

        total_new = 0
        json_files = [f for f in os.listdir(devpost_dir) if f.endswith("_complete.json")]

        for fname in sorted(json_files):
            path = os.path.join(devpost_dir, fname)
            hackathon = fname.replace("_complete.json", "")
            try:
                with open(path, "r") as f:
                    projects = json.load(f)
            except Exception as e:
                print(f"  Error reading {fname}: {e}")
                continue

            new_count = 0
            for project in projects:
                for gh_link in project.get("github_links", []):
                    parsed = urlparse(gh_link)
                    if "github.com" not in parsed.netloc:
                        continue
                    parts = parsed.path.strip("/").split("/")
                    if len(parts) >= 2:
                        full_name = f"{parts[0]}/{parts[1]}"
                        added = self._add_repo(
                            full_name=full_name, stars=0, language="",
                            created_at="", pushed_at="",
                            description=project.get("tagline", ""),
                            topics=project.get("tech_tags", [])[:10],
                            source=f"devpost:{hackathon}",
                        )
                        if added:
                            new_count += 1

            total_new += new_count
            print(f"  {hackathon}: {new_count} new repos from {len(projects)} projects")

        print(f"\n  Devpost integration complete: {total_new} new repos")
        return total_new

    # ── Source 7: Seed Repos ──

    def load_seed_repos(self):
        """Load manually curated seed repos."""
        if not SEED_REPOS:
            return 0

        print("\n[Source 7] Seed Repos")
        print("=" * 55)

        total_new = 0
        for full_name in SEED_REPOS:
            data = self._api_get(f"{API_BASE}/repos/{full_name}")
            time.sleep(REQUEST_DELAY)

            if not data:
                print(f"  {full_name}: not found")
                continue

            added = self._add_repo(
                full_name=data["full_name"],
                stars=data.get("stargazers_count", 0),
                language=data.get("language", ""),
                created_at=data.get("created_at", ""),
                pushed_at=data.get("pushed_at", ""),
                description=data.get("description", ""),
                topics=data.get("topics", []),
                source="seed",
                html_url=data.get("html_url", ""),
            )
            if added:
                total_new += 1
                print(f"  + {full_name} ({data.get('stargazers_count', 0)} stars)")

        print(f"\n  Seed repos complete: {total_new} new repos")
        return total_new

    # ── Orchestration ──

    def discover_all(self, sources=None):
        """Run all discovery sources and produce deduplicated repo list."""
        all_sources = sources or ["search", "topics", "new", "trending", "events", "devpost", "seed"]

        print(f"\nGitHub Repo Discovery (v2)")
        print(f"{'='*55}")
        print(f"  Sources: {', '.join(all_sources)}")
        print(f"  Existing repos: {self._existing_count}")
        print(f"  Token: {'set' if HEADERS.get('Authorization') else 'NOT SET (rate limits apply!)'}")

        if "search" in all_sources:
            self.search_repos()
        if "topics" in all_sources:
            self.search_topics()
        if "new" in all_sources:
            self.search_new_repos()
        if "trending" in all_sources:
            self.scrape_trending()
        if "events" in all_sources:
            self.scan_events()
        if "devpost" in all_sources:
            self.load_devpost_repos()
        if "seed" in all_sources:
            self.load_seed_repos()

        return list(self.repos.values())

    def save(self, repos=None, path=None):
        """Save discovered repos to JSON."""
        repos = repos or list(self.repos.values())
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = path or os.path.join(OUTPUT_DIR, "repos.json")

        repos.sort(key=lambda r: -r.get("stars", 0))

        with open(path, "w", encoding="utf-8") as f:
            json.dump(repos, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(path) / 1024
        print(f"\n  Saved {len(repos)} repos to {path} ({size_kb:.1f} KB)")

        # Stats
        sources = {}
        for r in repos:
            for s in r.get("sources", []):
                key = s.split(":")[0]
                sources[key] = sources.get(key, 0) + 1

        languages = {}
        for r in repos:
            lang = r.get("language", "unknown") or "unknown"
            languages[lang] = languages.get(lang, 0) + 1

        new_count = len(repos) - self._existing_count

        print(f"\n{'='*55}")
        print(f"  Discovery Summary")
        print(f"{'='*55}")
        print(f"  Previously known: {self._existing_count}")
        print(f"  Newly discovered: {new_count}")
        print(f"  Total unique repos: {len(repos)}")
        print(f"  By source: {', '.join(f'{k}({v})' for k, v in sorted(sources.items(), key=lambda x: -x[1]))}")
        print(f"  Top languages: {', '.join(f'{k}({v})' for k, v in sorted(languages.items(), key=lambda x: -x[1])[:5])}")
        print(f"  API calls: {self.api_calls} REST + {self.search_calls} search")

        return repos


def main():
    parser = argparse.ArgumentParser(description="GitHub AI Project Discovery (v2)")
    parser.add_argument("--search-only", action="store_true", help="Search API only")
    parser.add_argument("--trending-only", action="store_true", help="Trending scrape only")
    parser.add_argument("--new-only", action="store_true", help="New repos radar only")
    parser.add_argument("--events-only", action="store_true", help="Events firehose only")
    parser.add_argument("--devpost-only", action="store_true", help="Devpost repos only")
    parser.add_argument("--seed-only", action="store_true", help="Seed repos only")
    parser.add_argument("--fresh", action="store_true", help="Start fresh (don't load existing repos.json)")
    parser.add_argument("-o", "--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    sources = None
    if args.search_only:
        sources = ["search", "topics"]
    elif args.trending_only:
        sources = ["trending"]
    elif args.new_only:
        sources = ["new"]
    elif args.events_only:
        sources = ["events"]
    elif args.devpost_only:
        sources = ["devpost"]
    elif args.seed_only:
        sources = ["seed"]

    discoverer = GitHubDiscoverer(incremental=not args.fresh)
    repos = discoverer.discover_all(sources=sources)
    discoverer.save(repos, path=args.output)


if __name__ == "__main__":
    main()
