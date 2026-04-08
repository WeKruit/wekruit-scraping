#!/usr/bin/env python3
"""
Batch Devpost Hackathon Scraper
================================
Scrapes 60 hackathons with full project + member data.
Resumes automatically — skips already-completed hackathons.

Usage:
    # List all targets
    python3 targets.py --list

    # Scrape all S-tier with profiles
    python3 targets.py --run --tier S --profiles

    # Scrape all tiers with profiles
    python3 targets.py --run --profiles

    # Scrape without profiles (faster, no GitHub/LinkedIn)
    python3 targets.py --run
"""

import argparse, sys, os, time

TARGETS = [
    # ── S tier: Top CS school hackathons ──
    {"slug": "treehacks-2026",       "name": "TreeHacks 2026 (Stanford)",        "tier": "S", "reg": 1098},
    {"slug": "hackmit-2024",         "name": "HackMIT 2024",                     "tier": "S", "reg": 900},
    {"slug": "calhacks-11",          "name": "CalHacks 11.0 (UC Berkeley)",      "tier": "S", "reg": 850},
    {"slug": "la-hacks-2025",        "name": "LA Hacks 2025 (UCLA)",             "tier": "S", "reg": 583},
    {"slug": "pennapps-xxv",         "name": "PennApps XXV (UPenn)",             "tier": "S", "reg": 500},
    {"slug": "hackgt-x",             "name": "HackGT X (Georgia Tech)",          "tier": "S", "reg": 600},
    {"slug": "hackillinois-2026",    "name": "HackIllinois 2026 (UIUC)",        "tier": "S", "reg": 679},
    {"slug": "hacklytics-2026",      "name": "Hacklytics 2026 (Georgia Tech)",   "tier": "S", "reg": 730},
    {"slug": "devfest-2026",         "name": "DevFest 2026 (Columbia)",           "tier": "S", "reg": 566},
    {"slug": "mit-reality-hack-2025","name": "MIT Reality Hack 2025",            "tier": "S", "reg": 366},
    {"slug": "yhack-2026",           "name": "YHack 2026 (Yale)",                "tier": "S", "reg": 648},
    {"slug": "hacknyu-2025",         "name": "HackNYU 2025",                     "tier": "S", "reg": 642},

    # ── A tier: Large school + AI/enterprise hackathons ──
    {"slug": "bitcamp2025",          "name": "Bitcamp 2025 (UMD)",               "tier": "A", "reg": 764},
    {"slug": "hackutd-2025",         "name": "HackUTD 2025 (UT Dallas)",         "tier": "A", "reg": 1151},
    {"slug": "hacktx2025",           "name": "HackTX 2025 (UT Austin)",          "tier": "A", "reg": 729},
    {"slug": "shellhacks2025",       "name": "ShellHacks 2025 (FIU)",            "tier": "A", "reg": 840},
    {"slug": "nwhacks-2026",         "name": "nwHacks 2026 (UBC)",               "tier": "A", "reg": 631},
    {"slug": "hacknroll2026",        "name": "Hack&Roll 2026 (NUS)",             "tier": "A", "reg": 614},
    {"slug": "tamuhack-2025",        "name": "TAMUhack 2025 (Texas A&M)",        "tier": "A", "reg": 532},
    {"slug": "hoohacks-2026",        "name": "HooHacks 2026 (UVA)",              "tier": "A", "reg": 687},
    {"slug": "hacknc-2025",          "name": "HackNC 2025 (UNC)",                "tier": "A", "reg": 471},
    {"slug": "hoya-hacks-2026",      "name": "Hoya Hacks 2026 (Georgetown)",     "tier": "A", "reg": 462},
    {"slug": "hackumbc-2025",        "name": "hackUMBC 2025",                    "tier": "A", "reg": 450},
    {"slug": "hophops-fall-2025",    "name": "HopHacks Fall 2025 (JHU)",         "tier": "A", "reg": 310},
    {"slug": "hackduke-code-for-good-2025", "name": "HackDuke 2025",            "tier": "A", "reg": 188},
    {"slug": "wildhacks-2025",       "name": "WildHacks 2025 (Northwestern)",    "tier": "A", "reg": 350},
    {"slug": "mhacks-2025",          "name": "MHacks 2025 (Michigan)",           "tier": "A", "reg": 380},
    {"slug": "spartahack-x",         "name": "SpartaHack X (Michigan State)",    "tier": "A", "reg": 382},
    {"slug": "cruzhacks--2026",      "name": "CruzHacks 2026 (UC Santa Cruz)",   "tier": "A", "reg": 279},
    {"slug": "swamphacksx",          "name": "SwampHacks X (UF)",                "tier": "A", "reg": 340},
    {"slug": "rowdyhacks-xi",        "name": "RowdyHacks XI (UTSA)",             "tier": "A", "reg": 257},
    {"slug": "henhacks-2026",        "name": "HenHacks 2026 (UD)",               "tier": "A", "reg": 405},
    {"slug": "hackfax-x-patriothacks-2026", "name": "PatriotHacks 2026 (GMU)",   "tier": "A", "reg": 411},
    {"slug": "diamondhacks-2026",    "name": "DiamondHacks 2026",                "tier": "A", "reg": 367},
    {"slug": "hackncstate2026",      "name": "Hack_NCState 2026",                "tier": "A", "reg": 358},
    {"slug": "bigredhacks-28881",    "name": "BigRedHacks (Cornell)",             "tier": "A", "reg": 200},
    {"slug": "genai-genesis-2026",   "name": "GenAI Genesis 2026",               "tier": "A", "reg": 813},
    {"slug": "hack-canada-2026",     "name": "Hack Canada 2026",                 "tier": "A", "reg": 693},
    {"slug": "amazon-nova",          "name": "Amazon Nova AI Hackathon",          "tier": "A", "reg": 13465},
    {"slug": "gitlab",               "name": "GitLab AI Hackathon",               "tier": "A", "reg": 6985},
    {"slug": "digitalocean",         "name": "DigitalOcean Gradient AI Hackathon","tier": "A", "reg": 2633},
    {"slug": "genaidevhackathon",    "name": "GenAI Dev Hackathon",               "tier": "A", "reg": 544},

    # ── B tier: Mid-size / optional ──
    {"slug": "frostbyte-hackathon",  "name": "Frostbyte Hackathon",              "tier": "B", "reg": 688},
    {"slug": "makeuc-2025",          "name": "MakeUC 2025 (Cincinnati)",         "tier": "B", "reg": 159},
    {"slug": "pickhacks-2025mst",    "name": "PickHacks 2025 (Missouri S&T)",    "tier": "B", "reg": 173},
    {"slug": "hackthenorth2025",     "name": "Hack the North 2025 (Waterloo)",   "tier": "B", "reg": 870},
    {"slug": "hackthe6ix2025",       "name": "Hack the 6ix 2025 (Toronto)",      "tier": "B", "reg": 396},
    {"slug": "unitedhacksv6",        "name": "United Hacks V6",                  "tier": "B", "reg": 1193},
    {"slug": "hack-for-humanity-25", "name": "Hack for Humanity 2025",           "tier": "B", "reg": 1024},
    {"slug": "nexora-hacks-2026",    "name": "Nexora Hacks 2026",                "tier": "B", "reg": 682},
    {"slug": "utra-hacks-2026",      "name": "UTRA Hacks 2026 (Brown)",          "tier": "B", "reg": 327},
    {"slug": "hacked-2026",          "name": "Hacked 2026",                      "tier": "B", "reg": 332},
    {"slug": "hacksc-x-lovable-2025-","name": "HackSC 2025 (USC)",              "tier": "B", "reg": 91},
    {"slug": "scarlet-hacks-29528",  "name": "Scarlet Hacks 2026 (Rutgers)",     "tier": "B", "reg": 105},
    {"slug": "sunhacks2k26",         "name": "SunHacks 2026 (ASU)",              "tier": "B", "reg": 31},
    {"slug": "hacknroll2025",        "name": "Hack&Roll 2025 (NUS)",             "tier": "B", "reg": 428},
    {"slug": "hackrice-x",           "name": "HackRice X (Rice)",                "tier": "B", "reg": 277},
    {"slug": "conuhacks-ix",         "name": "ConUHacks IX (Concordia)",         "tier": "B", "reg": 500},
]


def print_list(targets, tiers=None):
    filtered = targets if not tiers else [t for t in targets if t["tier"] in tiers]
    filtered.sort(key=lambda t: (-{"S": 3, "A": 2, "B": 1}[t["tier"]], -t["reg"]))
    print(f"\n{'Tier':<5} {'Reg':>6}  {'Slug':<35} {'Name'}")
    print("-" * 95)
    for t in filtered:
        print(f"  {t['tier']}   {t['reg']:>5}  {t['slug']:<35} {t['name']}")
    print(f"\nTotal: {len(filtered)}")
    for tier in ["S", "A", "B"]:
        c = sum(1 for t in filtered if t["tier"] == tier)
        if c:
            print(f"  Tier {tier}: {c}")


def run_scrape(targets, tiers=None, profiles=False, output="output"):
    # Import our scraper
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from scraper import DevpostScraper

    filtered = targets if not tiers else [t for t in targets if t["tier"] in tiers]
    filtered.sort(key=lambda t: (-{"S": 3, "A": 2, "B": 1}[t["tier"]], -t["reg"]))

    # Skip already-completed hackathons
    done = set()
    if os.path.exists(output):
        for f in os.listdir(output):
            if f.endswith("_complete.json"):
                done.add(f.replace("_complete.json", ""))

    todo = [t for t in filtered if t["slug"] not in done]
    skipped = len(filtered) - len(todo)
    if skipped:
        print(f"  Skipping {skipped} already-scraped hackathons")

    print(f"  To scrape: {len(todo)} hackathons")
    print(f"  Profiles: {'yes' if profiles else 'no'}")
    print(f"  Output: {output}/\n")

    for i, t in enumerate(todo):
        print(f"\n{'#'*60}")
        print(f"  [{i+1}/{len(todo)}] {t['name']} (tier {t['tier']}, ~{t['reg']} reg)")
        print(f"{'#'*60}")

        url = f"https://{t['slug']}.devpost.com"
        scraper = DevpostScraper(
            url, delay=1.5, workers=3, fetch_profiles=profiles
        )
        try:
            scraper.run(out_dir=output)
        except KeyboardInterrupt:
            print("\n\nInterrupted! Progress saved. Re-run to resume.")
            sys.exit(0)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        # Cooldown between hackathons to avoid rate limiting
        if i < len(todo) - 1:
            wait = 15
            print(f"\n  Cooling down {wait}s before next hackathon...", flush=True)
            time.sleep(wait)

    # Summary
    print(f"\n\n{'='*60}")
    print(f"  BATCH COMPLETE!")
    print(f"{'='*60}")
    completed = set()
    if os.path.exists(output):
        for f in os.listdir(output):
            if f.endswith("_complete.json"):
                completed.add(f.replace("_complete.json", ""))
    print(f"  Total CSV/JSON files: {len(completed)}")
    print(f"  Output directory: {output}/")


def main():
    parser = argparse.ArgumentParser(description="Batch Devpost Hackathon Scraper")
    parser.add_argument("--list", action="store_true", help="Show target list")
    parser.add_argument("--run", action="store_true", help="Start scraping")
    parser.add_argument("--tier", action="append", choices=["S", "A", "B"], help="Filter by tier")
    parser.add_argument("--profiles", action="store_true", help="Fetch member GitHub/LinkedIn")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

    if not args.list and not args.run:
        args.list = True

    if args.list:
        print_list(TARGETS, args.tier)

    if args.run:
        run_scrape(TARGETS, args.tier, args.profiles, args.output)


if __name__ == "__main__":
    main()
