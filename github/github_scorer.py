#!/usr/bin/env python3
"""
GitHub Talent Discovery — Quality Scoring
==========================================
Scores each candidate based on:
  - Technical activity (40 pts)
  - Influence signals (30 pts)
  - Reachability (20 pts)
  - Profile completeness (10 pts)

Filters by threshold and outputs ranked CSV + JSON.

Usage:
    python3 github_scorer.py                               # From candidates.json
    python3 github_scorer.py --candidates path/to/file.json
    python3 github_scorer.py --threshold 30                # Lower threshold
"""

import json, csv, os, sys, argparse, math
from datetime import datetime

from github_config import SCORING, SCORE_THRESHOLD, OUTPUT_DIR


class GitHubScorer:
    def __init__(self, threshold=SCORE_THRESHOLD):
        self.threshold = threshold

    def _score_activity(self, candidate):
        """Score technical activity (40 pts max)."""
        cfg = SCORING["activity"]
        score = 0

        # Commit volume: log scale, cap at max
        total_commits = candidate.get("total_commits", 0)
        if total_commits > 0:
            # 1 commit = 0, 10 = ~7, 50 = ~12, 200+ = 15
            score += min(math.log(total_commits + 1, 2) * 2, cfg["commit_count_max"])

        # Multi-project: each additional repo = 3 pts, max 10
        repo_count = len(candidate.get("repos", []))
        score += min((repo_count - 1) * 3, cfg["repo_count_max"]) if repo_count > 1 else 0

        # Recency: based on profile updated_at
        updated = candidate.get("profile", {}).get("updated_at", "")
        if updated:
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                days_ago = (datetime.now(updated_dt.tzinfo) - updated_dt).days
                if days_ago <= 30:
                    score += cfg["recency_max"]
                elif days_ago <= 90:
                    score += cfg["recency_max"] * 0.7
                elif days_ago <= 180:
                    score += cfg["recency_max"] * 0.4
                elif days_ago <= 365:
                    score += cfg["recency_max"] * 0.1
            except (ValueError, TypeError):
                pass

        # Public repos
        public_repos = candidate.get("profile", {}).get("public_repos", 0)
        if public_repos >= 50:
            score += cfg["public_repos_max"]
        elif public_repos >= 20:
            score += cfg["public_repos_max"] * 0.7
        elif public_repos >= 5:
            score += cfg["public_repos_max"] * 0.4

        return min(score, cfg["weight"])

    def _score_influence(self, candidate):
        """Score influence signals (30 pts max)."""
        cfg = SCORING["influence"]
        score = 0

        # Contributed project stars (sum across all repos)
        project_stars = sum(r.get("stars", 0) for r in candidate.get("repos", []))
        if project_stars >= 10000:
            score += cfg["project_stars_max"]
        elif project_stars >= 5000:
            score += cfg["project_stars_max"] * 0.8
        elif project_stars >= 1000:
            score += cfg["project_stars_max"] * 0.6
        elif project_stars >= 500:
            score += cfg["project_stars_max"] * 0.4
        elif project_stars >= 100:
            score += cfg["project_stars_max"] * 0.2

        # Personal followers
        followers = candidate.get("profile", {}).get("followers", 0)
        if followers >= 1000:
            score += cfg["followers_max"]
        elif followers >= 500:
            score += cfg["followers_max"] * 0.8
        elif followers >= 100:
            score += cfg["followers_max"] * 0.6
        elif followers >= 50:
            score += cfg["followers_max"] * 0.4
        elif followers >= 10:
            score += cfg["followers_max"] * 0.2

        # Personal stars (approximation via followers as proxy — full calculation would require extra API)
        # Skip for now, award bonus for high public repo count + followers
        if followers >= 100 and candidate.get("profile", {}).get("public_repos", 0) >= 20:
            score += cfg["personal_stars_max"]
        elif followers >= 50 and candidate.get("profile", {}).get("public_repos", 0) >= 10:
            score += cfg["personal_stars_max"] * 0.5

        return min(score, cfg["weight"])

    def _score_reachability(self, candidate):
        """Score reachability (20 pts max)."""
        cfg = SCORING["reachability"]

        if candidate.get("emails"):
            return cfg["has_email"]

        profile = candidate.get("profile", {})
        if profile.get("twitter_username") or profile.get("blog"):
            return cfg["has_twitter_or_blog"]

        return cfg["nothing"]

    def _score_profile(self, candidate):
        """Score profile completeness (10 pts max)."""
        cfg = SCORING["profile"]
        score = 0
        profile = candidate.get("profile", {})

        if profile.get("name"):
            score += cfg["has_name"]
        if profile.get("bio"):
            score += cfg["has_bio"]
        if profile.get("company"):
            score += cfg["has_company"]
        if profile.get("location"):
            score += cfg["has_location"]

        return min(score, cfg["weight"])

    def score_candidate(self, candidate):
        """Calculate total score for a candidate."""
        activity = self._score_activity(candidate)
        influence = self._score_influence(candidate)
        reachability = self._score_reachability(candidate)
        profile = self._score_profile(candidate)

        total = activity + influence + reachability + profile

        return {
            "total": round(total, 1),
            "activity": round(activity, 1),
            "influence": round(influence, 1),
            "reachability": round(reachability, 1),
            "profile": round(profile, 1),
        }

    def score_all(self, candidates):
        """Score and rank all candidates."""
        print(f"\nQuality Scoring")
        print(f"{'='*55}")
        print(f"  Candidates to score: {len(candidates)}")
        print(f"  Threshold: {self.threshold}")

        for c in candidates:
            c["score"] = self.score_candidate(c)

        # Sort by total score descending
        candidates.sort(key=lambda c: -c["score"]["total"])

        # Apply threshold
        above = [c for c in candidates if c["score"]["total"] >= self.threshold]
        below = len(candidates) - len(above)

        print(f"  Above threshold: {len(above)}")
        print(f"  Below threshold: {below}")

        # Score distribution
        brackets = {"80+": 0, "60-79": 0, "40-59": 0, "20-39": 0, "0-19": 0}
        for c in candidates:
            s = c["score"]["total"]
            if s >= 80:
                brackets["80+"] += 1
            elif s >= 60:
                brackets["60-79"] += 1
            elif s >= 40:
                brackets["40-59"] += 1
            elif s >= 20:
                brackets["20-39"] += 1
            else:
                brackets["0-19"] += 1
        print(f"  Distribution: {', '.join(f'{k}:{v}' for k, v in brackets.items())}")

        return above

    def save_json(self, candidates, path=None):
        """Save scored candidates to JSON."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = path or os.path.join(OUTPUT_DIR, "scored_candidates.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(path) / 1024
        print(f"  Saved JSON: {path} ({size_kb:.1f} KB)")

    def save_csv(self, candidates, path=None):
        """Save scored candidates to CSV for easy viewing."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = path or os.path.join(OUTPUT_DIR, "scored_candidates.csv")

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "username", "name", "email", "bio", "company", "location",
                "blog", "twitter", "source_repos", "total_commits",
                "project_stars_sum", "followers", "public_repos",
                "score_total", "score_activity", "score_influence",
                "score_reachability", "score_profile", "discovered_date",
            ])

            for c in candidates:
                profile = c.get("profile", {})
                emails = c.get("emails", [])
                repos = c.get("repos", [])
                score = c.get("score", {})

                writer.writerow([
                    c.get("username", ""),
                    profile.get("name", ""),
                    "; ".join(emails) if emails else "",
                    profile.get("bio", "")[:200],
                    profile.get("company", ""),
                    profile.get("location", ""),
                    profile.get("blog", ""),
                    profile.get("twitter_username", ""),
                    "; ".join(r["full_name"] for r in repos),
                    c.get("total_commits", 0),
                    sum(r.get("stars", 0) for r in repos),
                    profile.get("followers", 0),
                    profile.get("public_repos", 0),
                    score.get("total", 0),
                    score.get("activity", 0),
                    score.get("influence", 0),
                    score.get("reachability", 0),
                    score.get("profile", 0),
                    datetime.now().strftime("%Y-%m-%d"),
                ])

        size_kb = os.path.getsize(path) / 1024
        print(f"  Saved CSV:  {path} ({size_kb:.1f} KB)")

    def save(self, candidates, json_path=None, csv_path=None):
        """Save both JSON and CSV outputs."""
        print(f"\nSaving results...")
        self.save_json(candidates, json_path)
        self.save_csv(candidates, csv_path)

        # Top 10 summary
        print(f"\n{'='*55}")
        print(f"  Top 10 Candidates")
        print(f"{'='*55}")
        for i, c in enumerate(candidates[:10]):
            profile = c.get("profile", {})
            name = profile.get("name") or c.get("username", "")
            email_flag = "E" if c.get("emails") else "-"
            repos_count = len(c.get("repos", []))
            print(f"  {i+1:2d}. [{c['score']['total']:5.1f}] {name:<25} "
                  f"R:{repos_count} C:{c.get('total_commits', 0):>4} {email_flag}")


def main():
    parser = argparse.ArgumentParser(description="GitHub Candidate Quality Scoring")
    parser.add_argument("--candidates", default=None, help="Path to candidates.json")
    parser.add_argument("--threshold", type=int, default=SCORE_THRESHOLD, help=f"Score threshold (default: {SCORE_THRESHOLD})")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    candidates_path = args.candidates or os.path.join(OUTPUT_DIR, "candidates.json")
    if not os.path.exists(candidates_path):
        print(f"Error: candidates file not found: {candidates_path}")
        print("Run github_contributors.py first to generate candidates.json")
        sys.exit(1)

    with open(candidates_path, "r") as f:
        candidates = json.load(f)

    print(f"Loaded {len(candidates)} candidates from {candidates_path}")

    scorer = GitHubScorer(threshold=args.threshold)
    scored = scorer.score_all(candidates)

    out_dir = args.output_dir or OUTPUT_DIR
    scorer.save(
        scored,
        json_path=os.path.join(out_dir, "scored_candidates.json"),
        csv_path=os.path.join(out_dir, "scored_candidates.csv"),
    )


if __name__ == "__main__":
    main()
