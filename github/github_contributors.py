#!/usr/bin/env python3
"""
GitHub Talent Discovery — Contributor Extraction + Profile Enrichment
======================================================================
For each discovered repo:
  - Extract top contributors (by commit count)
  - Fetch user profiles (bio, company, location, socials)
  - Extract emails from commit history / events API
  - Deduplicate across repos, merge multi-project contributions

Usage:
    python3 github_contributors.py                          # From repos.json
    python3 github_contributors.py --repos path/to/repos.json
    python3 github_contributors.py --limit 50               # Process first 50 repos
"""

import requests
import json, time, os, sys, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from github_config import (
    API_BASE, HEADERS, OUTPUT_DIR, MIN_COMMITS, MAX_CONTRIBUTORS,
    ENRICHMENT_WORKERS, REQUEST_DELAY, RETRY_MAX, RETRY_BACKOFF_BASE,
    INVALID_EMAIL_PATTERNS,
)


class GitHubContributors:
    def __init__(self, workers=ENRICHMENT_WORKERS):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.workers = workers
        self.candidates = {}  # username -> candidate dict
        self.api_calls = 0
        self._progress_count = 0
        self._total_repos = 0

    def _api_get(self, url, params=None, is_search=False):
        """GitHub API call with rate-limit handling and retries."""
        for attempt in range(RETRY_MAX):
            try:
                resp = self.session.get(url, params=params, timeout=30)

                remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
                if remaining < 10:
                    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_ts - time.time(), 1) + 5
                    print(f"\n  [rate-limit] {remaining} left, sleeping {wait:.0f}s", flush=True)
                    time.sleep(wait)

                if resp.status_code == 403 and "rate limit" in resp.text.lower():
                    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_ts - time.time(), 60) + 5
                    print(f"\n  [rate-limit] 403 hit, sleeping {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue

                if resp.status_code in (404, 422):
                    return None

                if resp.status_code == 204:
                    return []

                resp.raise_for_status()
                self.api_calls += 1
                return resp.json()

            except requests.exceptions.ConnectionError:
                wait = RETRY_BACKOFF_BASE * (attempt + 1)
                print(f"\n  [conn-err] retry {attempt+1}/{RETRY_MAX} in {wait}s", flush=True)
                time.sleep(wait)

        return None

    def _is_valid_email(self, email):
        """Check if email is useful (not a noreply or invalid pattern)."""
        if not email or not isinstance(email, str):
            return False
        email = email.lower().strip()
        if not email or "@" not in email:
            return False
        for pattern in INVALID_EMAIL_PATTERNS:
            if pattern.lower() in email:
                return False
        return True

    # ── Step 1: Extract contributors per repo ──

    def get_contributors(self, repo):
        """Get top contributors for a repo."""
        full_name = repo["full_name"]
        data = self._api_get(
            f"{API_BASE}/repos/{full_name}/contributors",
            params={"per_page": MAX_CONTRIBUTORS, "anon": "false"},
        )
        time.sleep(REQUEST_DELAY)

        if not data or not isinstance(data, list):
            return []

        contributors = []
        for item in data:
            if item.get("type") != "User":
                continue
            username = item.get("login", "")
            commits = item.get("contributions", 0)
            if not username or commits < MIN_COMMITS:
                continue
            contributors.append({
                "username": username,
                "commits": commits,
                "avatar_url": item.get("avatar_url", ""),
            })

        return contributors[:MAX_CONTRIBUTORS]

    # ── Step 2: Fetch user profile ──

    def get_user_profile(self, username):
        """Fetch GitHub user profile data."""
        data = self._api_get(f"{API_BASE}/users/{username}")
        time.sleep(REQUEST_DELAY)

        if not data:
            return {}

        return {
            "name": data.get("name", "") or "",
            "email": data.get("email", "") or "",
            "bio": data.get("bio", "") or "",
            "company": data.get("company", "") or "",
            "location": data.get("location", "") or "",
            "blog": data.get("blog", "") or "",
            "twitter_username": data.get("twitter_username", "") or "",
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "html_url": data.get("html_url", ""),
        }

    # ── Step 3: Extract emails from commit history ──

    def extract_emails(self, username):
        """Extract emails from user's public events (PushEvent commits)."""
        emails = set()

        # Method 1: Public events API
        data = self._api_get(
            f"{API_BASE}/users/{username}/events/public",
            params={"per_page": 100},
        )
        time.sleep(REQUEST_DELAY)

        if data and isinstance(data, list):
            for event in data:
                if event.get("type") != "PushEvent":
                    continue
                payload = event.get("payload", {})
                for commit in payload.get("commits", []):
                    author = commit.get("author", {})
                    email = author.get("email", "")
                    if self._is_valid_email(email):
                        emails.add(email.lower().strip())

        return list(emails)

    # ── Step 3b: Get merged PR count ──

    def get_merged_prs(self, username):
        """Count how many PRs this user has had merged (across all of GitHub).
        Uses search/issues API — 1 call per user."""
        data = self._api_get(
            f"{API_BASE}/search/issues",
            params={"q": f"author:{username} type:pr is:merged", "per_page": 1},
            is_search=True,
        )
        time.sleep(REQUEST_DELAY)

        if data and isinstance(data, dict):
            return data.get("total_count", 0)
        return 0

    # ── Step 4: Merge candidate data ──

    def _merge_candidate(self, username, repo_info, commits):
        """Add or merge contributor into candidates dict."""
        key = username.lower()
        if key in self.candidates:
            c = self.candidates[key]
            # Add repo contribution
            c["repos"].append({
                "full_name": repo_info["full_name"],
                "stars": repo_info.get("stars", 0),
                "commits": commits,
            })
            c["total_commits"] += commits
        else:
            self.candidates[key] = {
                "username": username,
                "repos": [{
                    "full_name": repo_info["full_name"],
                    "stars": repo_info.get("stars", 0),
                    "commits": commits,
                }],
                "total_commits": commits,
                "profile": {},
                "emails": [],
                "enriched": False,
            }

    # ── Step 5: Enrich a single candidate ──

    def _enrich_candidate(self, username):
        """Fetch profile and emails for a candidate."""
        key = username.lower()
        c = self.candidates.get(key)
        if not c or c.get("enriched"):
            return c

        # Profile
        profile = self.get_user_profile(username)
        c["profile"] = profile

        # Emails from profile
        emails = set()
        if self._is_valid_email(profile.get("email")):
            emails.add(profile["email"].lower().strip())

        # Emails from commit history
        commit_emails = self.extract_emails(username)
        for e in commit_emails:
            emails.add(e)

        c["emails"] = list(emails)

        # Merged PR count
        c["merged_prs"] = self.get_merged_prs(username)

        c["enriched"] = True

        return c

    # ── Main extraction pipeline ──

    def extract_all(self, repos, limit=None):
        """Extract contributors from all repos, then enrich profiles."""
        if limit:
            repos = repos[:limit]

        self._total_repos = len(repos)
        print(f"\nContributor Extraction")
        print(f"{'='*55}")
        print(f"  Repos to process: {len(repos)}")
        print(f"  Min commits: {MIN_COMMITS}")
        print(f"  Token: {'set' if HEADERS.get('Authorization') else 'NOT SET'}")

        # Phase 1: Extract contributors from each repo
        print(f"\n[1/2] Extracting contributors...")
        for i, repo in enumerate(repos):
            contributors = self.get_contributors(repo)
            for c in contributors:
                self._merge_candidate(c["username"], repo, c["commits"])

            if (i + 1) % 10 == 0 or i == len(repos) - 1:
                print(f"  [{i+1}/{len(repos)}] {len(self.candidates)} unique candidates so far", flush=True)

            # Progress save
            if (i + 1) % 50 == 0:
                self._save_progress()

        print(f"\n  Extraction complete: {len(self.candidates)} unique candidates from {len(repos)} repos")

        # Phase 2: Enrich profiles
        print(f"\n[2/2] Enriching {len(self.candidates)} profiles ({self.workers} workers)...")
        usernames = [c["username"] for c in self.candidates.values() if not c.get("enriched")]
        done = [0]

        def _enrich(username):
            result = self._enrich_candidate(username)
            done[0] += 1
            if done[0] % 100 == 0:
                with_email = sum(1 for c in self.candidates.values() if c.get("emails"))
                print(f"  [{done[0]}/{len(usernames)}] with email: {with_email}", flush=True)
                self._save_progress()
            return result

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            list(pool.map(_enrich, usernames))

        # Stats
        with_email = sum(1 for c in self.candidates.values() if c.get("emails"))
        multi_repo = sum(1 for c in self.candidates.values() if len(c.get("repos", [])) > 1)
        print(f"\n  Enrichment complete!")
        print(f"  With email: {with_email} ({with_email*100//max(len(self.candidates),1)}%)")
        print(f"  Multi-project: {multi_repo}")

        return list(self.candidates.values())

    def _save_progress(self):
        """Save progress checkpoint."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR, "candidates_progress.json")
        candidates = list(self.candidates.values())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

    def save(self, candidates=None, path=None):
        """Save final candidates to JSON + CSV with raw metrics (no scoring)."""
        candidates = candidates or list(self.candidates.values())
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = path or os.path.join(OUTPUT_DIR, "candidates.json")

        # Sort by merged PRs desc, then total commits desc
        candidates.sort(key=lambda c: (-c.get("merged_prs", 0), -c.get("total_commits", 0)))

        with open(path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(path) / 1024
        print(f"\n  Saved {len(candidates)} candidates to {path} ({size_kb:.1f} KB)")

        # Clean up progress file
        progress = os.path.join(OUTPUT_DIR, "candidates_progress.json")
        if os.path.exists(progress):
            os.remove(progress)

        # Write CSV with raw metrics — no scores, just data
        csv_path = os.path.join(OUTPUT_DIR, "candidates.csv")
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow([
                "username", "name", "email", "merged_prs", "total_commits",
                "repos_contributed", "project_stars_sum", "followers",
                "public_repos", "company", "location", "bio",
                "blog", "twitter", "source_repos", "github_url",
            ])
            for c in candidates:
                p = c.get("profile", {})
                repos = c.get("repos", [])
                emails = c.get("emails", [])
                w.writerow([
                    c.get("username", ""),
                    p.get("name", ""),
                    " | ".join(emails) if emails else "",
                    c.get("merged_prs", 0),
                    c.get("total_commits", 0),
                    len(repos),
                    sum(r.get("stars", 0) for r in repos),
                    p.get("followers", 0),
                    p.get("public_repos", 0),
                    p.get("company", ""),
                    p.get("location", ""),
                    (p.get("bio", "") or "")[:200],
                    p.get("blog", ""),
                    p.get("twitter_username", ""),
                    " | ".join(r["full_name"] for r in repos),
                    p.get("html_url", ""),
                ])

        size_kb = os.path.getsize(csv_path) / 1024
        print(f"  Saved CSV: {csv_path} ({size_kb:.1f} KB)")

        # Summary
        print(f"\n{'='*55}")
        print(f"  Candidate Summary")
        print(f"{'='*55}")
        print(f"  Total candidates: {len(candidates)}")
        with_email = sum(1 for c in candidates if c.get("emails"))
        with_name = sum(1 for c in candidates if c.get("profile", {}).get("name"))
        with_bio = sum(1 for c in candidates if c.get("profile", {}).get("bio"))
        with_company = sum(1 for c in candidates if c.get("profile", {}).get("company"))
        with_twitter = sum(1 for c in candidates if c.get("profile", {}).get("twitter_username"))
        with_merged = sum(1 for c in candidates if c.get("merged_prs", 0) > 0)
        multi = sum(1 for c in candidates if len(c.get("repos", [])) > 1)
        print(f"  With email:      {with_email} ({with_email*100//max(len(candidates),1)}%)")
        print(f"  With merged PRs: {with_merged} ({with_merged*100//max(len(candidates),1)}%)")
        print(f"  With name:       {with_name}")
        print(f"  With company:    {with_company}")
        print(f"  With Twitter:    {with_twitter}")
        print(f"  Multi-project:   {multi}")
        print(f"  API calls:       {self.api_calls}")

        return candidates


def main():
    parser = argparse.ArgumentParser(description="GitHub Contributor Extraction + Enrichment")
    parser.add_argument("--repos", default=None, help="Path to repos.json (default: output/repos.json)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of repos to process")
    parser.add_argument("--workers", type=int, default=ENRICHMENT_WORKERS, help=f"Concurrent workers (default: {ENRICHMENT_WORKERS})")
    parser.add_argument("-o", "--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    repos_path = args.repos or os.path.join(OUTPUT_DIR, "repos.json")
    if not os.path.exists(repos_path):
        print(f"Error: repos file not found: {repos_path}")
        print("Run github_discover.py first to generate repos.json")
        sys.exit(1)

    with open(repos_path, "r") as f:
        repos = json.load(f)

    print(f"Loaded {len(repos)} repos from {repos_path}")

    extractor = GitHubContributors(workers=args.workers)
    candidates = extractor.extract_all(repos, limit=args.limit)
    extractor.save(candidates, path=args.output)


if __name__ == "__main__":
    main()
