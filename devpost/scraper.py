#!/usr/bin/env python3
"""
Universal Devpost Hackathon Scraper
====================================
Scrapes all projects from any Devpost hackathon gallery.
Extracts GitHub links, team members, tech stacks, and prizes.

Usage:
    pip3 install requests beautifulsoup4 lxml

    # Scrape a single hackathon
    python3 scraper.py https://treehacks-2026.devpost.com

    # Scrape with member profiles (GitHub/LinkedIn from Devpost profiles)
    python3 scraper.py https://treehacks-2026.devpost.com --profiles

    # Custom delay and workers
    python3 scraper.py https://treehacks-2026.devpost.com --delay 2.0 --workers 2

    # Batch scrape multiple hackathons
    python3 scraper.py https://treehacks-2026.devpost.com https://hackmit-2025.devpost.com

Output:
    output/<slug>_complete.json
    output/<slug>_complete.csv
"""

import requests
from bs4 import BeautifulSoup
import json, csv, time, os, sys, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


class DevpostScraper:
    def __init__(self, base_url, delay=1.2, workers=3, timeout=15, fetch_profiles=False):
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.workers = workers
        self.timeout = timeout
        self.fetch_profiles = fetch_profiles
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        parsed = urlparse(self.base_url)
        self.slug = parsed.netloc.split(".")[0]
        self.gallery_url = f"{self.base_url}/project-gallery"

    def fetch(self, url, retries=3):
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 429:
                    wait = min(30 * (2 ** attempt), 120)
                    print(f"\n  [rate-limit] 429 on {url[:50]}... waiting {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.text
            except requests.exceptions.ConnectionError:
                wait = 10 * (attempt + 1)
                print(f"\n  [conn-err] retry {attempt+1}/{retries} in {wait}s", flush=True)
                time.sleep(wait)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def get_project_list(self):
        """Crawl all gallery pages and extract project URLs + basic info."""
        projects = []
        page = 1
        while True:
            url = f"{self.gallery_url}?page={page}"
            print(f"  [gallery] page {page}...", end=" ", flush=True)
            try:
                html = self.fetch(url)
            except Exception as e:
                print(f"error: {e}")
                break

            soup = BeautifulSoup(html, "lxml")
            entries = soup.select("a.block-wrapper-link")
            if not entries:
                print("done")
                break

            for entry in entries:
                href = entry.get("href", "")
                if not href.startswith("http"):
                    href = "https://devpost.com" + href
                href = href.split("?")[0]

                name_el = entry.select_one(".software-entry-name")
                if name_el:
                    # Extract just the h5 title, not the tagline paragraph
                    h5 = name_el.select_one("h5")
                    if h5:
                        name = h5.get_text(strip=True)
                    else:
                        # Fallback: first direct text or first line
                        texts = [t.strip() for t in name_el.stripped_strings]
                        name = texts[0] if texts else ""
                else:
                    name = ""

                # Tagline (usually a <p> sibling of the h5)
                tagline = ""
                if name_el:
                    p = name_el.select_one("p")
                    if p:
                        tagline = p.get_text(strip=True)

                member_imgs = entry.select("img[title]")
                members_preview = [img["title"] for img in member_imgs if img.get("title")]

                winner = bool(entry.select_one(".entry-badge, .winner"))

                projects.append({
                    "name": name,
                    "tagline": tagline,
                    "project_url": href,
                    "winner": winner,
                    "members_preview": members_preview,
                })

            print(f"{len(entries)} projects")
            page += 1
            time.sleep(0.5)

        return projects

    def get_project_detail(self, project):
        """Scrape a single project page for all available fields."""
        url = project["project_url"]
        try:
            html = self.fetch(url)
        except Exception as e:
            project["error"] = str(e)
            return project

        soup = BeautifulSoup(html, "lxml")

        # ── Full description ──
        app_details = soup.select_one("#app-details-left")
        if app_details:
            for tag in app_details.select("script, style"):
                tag.decompose()
            project["description"] = app_details.get_text(separator="\n", strip=True)
        else:
            project["description"] = ""

        # ── All external links (GitHub, demo, try-it, etc.) ──
        github_links = []
        demo_links = []
        all_links = []
        for a in soup.select("nav.app-links a, a.url, #app-links a, #app-links-container a"):
            href = (a.get("href") or "").strip()
            if not href or href == "#":
                continue
            href = href.split("?")[0]
            if href not in all_links:
                all_links.append(href)
            if "github.com" in href and href not in github_links:
                github_links.append(href)
            elif "github.com" not in href and href not in demo_links:
                demo_links.append(href)
        project["github_links"] = github_links
        project["demo_links"] = demo_links
        project["all_links"] = all_links

        # ── Video URL ──
        video_url = ""
        for iframe in soup.select("iframe"):
            src = iframe.get("src", "")
            if "youtube" in src or "vimeo" in src or "loom" in src:
                video_url = src.split("?")[0]
                break
        project["video_url"] = video_url

        # ── Gallery images ──
        images = []
        for img in soup.select("#gallery img, .software-photos img"):
            src = img.get("src", "")
            if src and "cloudfront" in src:
                if src.startswith("//"):
                    src = "https:" + src
                images.append(src)
        project["images"] = images

        # ── Likes count ──
        likes_el = soup.select_one(".software-likes")
        if likes_el:
            likes_text = likes_el.get_text(strip=True).replace("Like", "").strip()
            project["likes"] = int(likes_text) if likes_text.isdigit() else 0
        else:
            project["likes"] = 0

        # ── Team members ──
        members = []
        seen = set()
        for link in soup.select("#app-team a.user-profile-link"):
            profile = (link.get("href") or "").split("?")[0]
            username = profile.rstrip("/").split("/")[-1]
            name = link.get_text(strip=True)
            if username and username not in seen and username != "software":
                seen.add(username)
                if not profile.startswith("http"):
                    profile = f"https://devpost.com/{username}"
                members.append({
                    "name": name,
                    "devpost_username": username,
                    "devpost_profile": profile,
                })
        if not members and project.get("members_preview"):
            members = [
                {"name": "", "devpost_username": u, "devpost_profile": f"https://devpost.com/{u}"}
                for u in project["members_preview"]
            ]
        project["members"] = members

        # ── Tech stack tags ──
        tags = [t.get_text(strip=True) for t in soup.select(".cp-tag, a.cp-tag")]
        project["tech_tags"] = [t for t in tags if t]

        # ── Prizes (with full names) ──
        prizes = []
        for li in soup.select(".software-list-content li"):
            txt = li.get_text(strip=True)
            if txt and "Winner" in txt:
                prizes.append(txt.replace("Winner", "").strip())
        if not prizes:
            prizes = [p.get_text(strip=True) for p in soup.select(".entry-badge")]
        project["prizes"] = [p for p in prizes if p]

        # ── Hackathon name ──
        hack_el = soup.select_one(".software-list-content a")
        if hack_el:
            project["hackathon"] = hack_el.get_text(strip=True)
        else:
            project["hackathon"] = ""

        return project

    def get_member_profile(self, member):
        """Scrape a member's Devpost profile for GitHub/LinkedIn/Twitter."""
        url = member["devpost_profile"]
        try:
            html = self.fetch(url)
        except Exception:
            return member

        soup = BeautifulSoup(html, "lxml")
        for a in soup.select("#portfolio-user-links a"):
            href = (a.get("href") or "").split("?")[0]
            if "github.com" in href:
                member["github_url"] = href
            elif "linkedin.com" in href:
                member["linkedin_url"] = href
            elif "twitter.com" in href or "x.com" in href:
                member["twitter_url"] = href
            elif href.startswith("http") and "devpost.com" not in href:
                member["website"] = href
        return member

    def save_json(self, projects, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        size_kb = os.path.getsize(path) / 1024
        print(f"  > JSON: {path} ({size_kb:.1f} KB)")

    def save_csv(self, projects, path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "hackathon", "project_name", "tagline", "description",
                "project_url", "video_url", "winner", "likes",
                "github_repos", "demo_links", "all_links",
                "member_name", "member_username", "member_devpost",
                "member_github", "member_linkedin", "member_twitter", "member_website",
                "tech_stack", "prizes", "image_count"
            ])

            for p in projects:
                mlist = p.get("members", []) or [{}]
                for m in mlist:
                    writer.writerow([
                        p.get("hackathon", ""), p.get("name", ""),
                        p.get("tagline", ""), p.get("description", ""),
                        p.get("project_url", ""), p.get("video_url", ""),
                        "Yes" if p.get("winner") else "", p.get("likes", 0),
                        "; ".join(p.get("github_links", [])),
                        "; ".join(p.get("demo_links", [])),
                        "; ".join(p.get("all_links", [])),
                        m.get("name", ""), m.get("devpost_username", ""),
                        m.get("devpost_profile", ""),
                        m.get("github_url", ""), m.get("linkedin_url", ""),
                        m.get("twitter_url", ""), m.get("website", ""),
                        ", ".join(p.get("tech_tags", [])),
                        "; ".join(p.get("prizes", [])),
                        len(p.get("images", [])),
                    ])
        size_kb = os.path.getsize(path) / 1024
        print(f"  > CSV:  {path} ({size_kb:.1f} KB)")

    def run(self, out_dir="output"):
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n{'='*55}")
        print(f"  Scraping: {self.slug}")
        print(f"  URL:      {self.base_url}")
        print(f"{'='*55}\n")

        # 1. Project list
        print("[1/3] Fetching project list...")
        projects = self.get_project_list()
        print(f"  Found {len(projects)} projects\n")
        if not projects:
            print("  No projects found. Check the URL or network.")
            return []

        # 2. Project details
        print(f"[2/3] Fetching project details (delay={self.delay}s, workers={self.workers})...")
        errors = 0

        def _process(idx_proj):
            idx, proj = idx_proj
            self.get_project_detail(proj)
            time.sleep(self.delay)
            return idx, proj

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(_process, (i, p)): i for i, p in enumerate(projects)}
            for future in as_completed(futures):
                idx, proj = future.result()
                gh = len(proj.get("github_links", []))
                m = len(proj.get("members", []))
                status = "!" if proj.get("error") else "+"
                if proj.get("error"):
                    errors += 1
                print(
                    f"  [{idx+1:3d}/{len(projects)}] {status} "
                    f"{proj.get('name','?')[:40]}  GH:{gh} M:{m}",
                    flush=True
                )

                # Save progress every 50 projects
                if (idx + 1) % 50 == 0:
                    self.save_json(projects, os.path.join(out_dir, f"{self.slug}_progress.json"))

        print(f"  Details complete (errors: {errors})\n")

        # 3. Member profiles (optional) — deduplicated + parallel
        if self.fetch_profiles:
            seen_users = set()
            unique_members = []
            for p in projects:
                for m in p.get("members", []):
                    u = m.get("devpost_username", "")
                    if u and u not in seen_users:
                        seen_users.add(u)
                        unique_members.append(m)
            print(f"[3/3] Fetching {len(unique_members)} unique member profiles (5 workers)...")
            done_profiles = [0]

            def _fetch_profile(m):
                self.get_member_profile(m)
                time.sleep(0.8)
                done_profiles[0] += 1
                if done_profiles[0] % 50 == 0:
                    gh = sum(1 for x in unique_members if x.get("github_url"))
                    li = sum(1 for x in unique_members if x.get("linkedin_url"))
                    print(f"  [{done_profiles[0]}/{len(unique_members)}] GH:{gh} LI:{li}", flush=True)
                return m

            with ThreadPoolExecutor(max_workers=5) as pool:
                list(pool.map(_fetch_profile, unique_members))

            # Propagate enriched data to duplicate members
            enriched = {m["devpost_username"]: m for m in unique_members}
            for p in projects:
                for m in p.get("members", []):
                    src = enriched.get(m.get("devpost_username", ""))
                    if src:
                        for k in ["github_url", "linkedin_url", "twitter_url", "website"]:
                            if k in src:
                                m[k] = src[k]

            gh = sum(1 for x in unique_members if x.get("github_url"))
            li = sum(1 for x in unique_members if x.get("linkedin_url"))
            print(f"  Profiles done: GH:{gh} LI:{li}\n")
        else:
            print("[3/3] Skipping member profiles (use --profiles to enable)\n")

        # Save results
        print("Saving results...")
        json_path = os.path.join(out_dir, f"{self.slug}_complete.json")
        csv_path = os.path.join(out_dir, f"{self.slug}_complete.csv")
        self.save_json(projects, json_path)
        self.save_csv(projects, csv_path)

        # Clean up progress file
        progress = os.path.join(out_dir, f"{self.slug}_progress.json")
        if os.path.exists(progress):
            os.remove(progress)

        # Stats
        with_gh = sum(1 for p in projects if p.get("github_links"))
        winners = sum(1 for p in projects if p.get("winner"))
        all_m = set(m.get("devpost_username") for p in projects for m in p.get("members", []))
        top_tags = {}
        for p in projects:
            for t in p.get("tech_tags", []):
                top_tags[t.lower()] = top_tags.get(t.lower(), 0) + 1
        top10 = sorted(top_tags.items(), key=lambda x: -x[1])[:10]

        print(f"\n{'='*55}")
        print(f"  Scrape complete!")
        print(f"{'='*55}")
        print(f"  Total projects:  {len(projects)}")
        print(f"  With GitHub:     {with_gh} ({with_gh*100//max(len(projects),1)}%)")
        print(f"  Winners:         {winners}")
        print(f"  Unique devs:     {len(all_m)}")
        if top10:
            print(f"  Top tech:        {', '.join(f'{t}({c})' for t,c in top10)}")
        print(f"\n  JSON: {json_path}")
        print(f"  CSV:  {csv_path}\n")

        return projects


def main():
    parser = argparse.ArgumentParser(description="Universal Devpost Hackathon Scraper")
    parser.add_argument("urls", nargs="+", help="Devpost hackathon URL(s)")
    parser.add_argument("--delay", type=float, default=1.2, help="Request delay in seconds (default: 1.2)")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent threads (default: 3)")
    parser.add_argument("--profiles", action="store_true", help="Fetch member Devpost profiles (GitHub/LinkedIn)")
    parser.add_argument("-o", "--output", default=None, help="Output directory (default: output/ in script dir)")
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

    all_projects = []
    for url in args.urls:
        url = url.rstrip("/")
        if not url.startswith("http"):
            url = f"https://{url}.devpost.com"
        scraper = DevpostScraper(
            url, delay=args.delay, workers=args.workers, fetch_profiles=args.profiles
        )
        projects = scraper.run(out_dir=args.output)
        all_projects.extend(projects)

    if len(args.urls) > 1:
        print(f"\n{'='*55}")
        print(f"  All done! Scraped {len(args.urls)} hackathons, {len(all_projects)} projects total")
        print(f"{'='*55}")


if __name__ == "__main__":
    main()
