#!/usr/bin/env python3
"""
GitHub Talent Discovery -- Interactive Dashboard
=================================================
Reads output/repos.json and generates a self-contained HTML dashboard
at output/dashboard.html.

Usage:
    python3 github_dashboard.py                # Generate dashboard
    python3 github_dashboard.py --open         # Generate and open in browser

The dashboard provides:
    - Summary cards (totals, star counts, language counts)
    - Category x Star-Tier heatmap matrix
    - Category x Language heatmap matrix
    - Owner-type breakdown per category
    - Source distribution chart
    - Filterable, sortable repo table
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPOS_JSON = SCRIPT_DIR / "output" / "repos.json"
OUTPUT_HTML = SCRIPT_DIR / "output" / "dashboard.html"

# ---------------------------------------------------------------------------
# Big-Tech org set (lowercase)
# ---------------------------------------------------------------------------
BIG_TECH_ORGS: set[str] = {
    "microsoft", "google", "meta", "facebook", "facebookresearch",
    "facebookincubator", "apple", "amazon", "aws", "awslabs",
    "aws-samples", "azure", "azure-samples", "openai", "anthropic",
    "nvidia", "nvidiaresearch", "deepmind", "google-deepmind",
    "google-research", "googleresearch", "alibaba", "bytedance",
    "tencent", "baidu", "huggingface", "vercel", "vercel-labs",
    "cloudflare", "ibm", "oracle", "salesforce", "intel",
    "intelai", "samsung", "samsungresearch", "databricks",
    "snowflakedb", "supabase", "netlify", "hashicorp", "elastic",
    "confluent", "redis", "mongodb", "cockroachdb",
}

# ---------------------------------------------------------------------------
# Category keyword rules
# ---------------------------------------------------------------------------
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Agent", [
        "agent", "agentic", "multi-agent", "autonomous",
        "crew", "autogen", "langgraph", "swarm",
    ]),
    ("RAG", [
        "rag", "retrieval augmented", "retrieval-augmented",
        "vector database", "vector db", "vectordb", "embedding",
        "semantic search", "knowledge base", "knowledge graph",
        "chromadb", "pinecone", "weaviate", "qdrant", "milvus",
    ]),
    ("MCP/Tools", [
        "mcp", "model context protocol", "function calling",
        "tool use", "tool-use", "plugins",
    ]),
    ("Infra/Serving", [
        "inference", "serving", "quantization", "fine-tuning",
        "finetuning", "fine tuning", "model serving", "vllm",
        "ollama", "llama.cpp", "gguf", "ggml", "mlops",
        "training", "deployment", "accelerat",
    ]),
    ("Coding/Dev", [
        "coding", "copilot", "code generation", "code assist",
        "ide", "developer tool", "dev tool", "linter", "debugg",
    ]),
    ("Chatbot/Assistant", [
        "chatbot", "chat bot", "assistant", "conversational",
        "chatgpt", "gpt-4", "gpt4", "dialogue", "chat ui",
    ]),
    ("Multimodal", [
        "multimodal", "multi-modal", "vision language",
        "image generation", "text-to-image", "text-to-speech",
        "speech-to-text", "voice ai", "audio", "video",
        "stable diffusion", "dall-e", "midjourney",
    ]),
    ("NLP/LLM Core", [
        "llm", "large language model", "transformer", "nlp",
        "natural language", "tokenizer", "bert", "gpt",
        "language model", "text generation", "prompt",
    ]),
    ("Data/Pipeline", [
        "data pipeline", "etl", "data processing",
        "web scraping", "crawler", "scraper",
        "dataset", "benchmark", "evaluation",
    ]),
    ("Security/Safety", [
        "safety", "alignment", "guardrail", "content filter",
        "red team", "jailbreak", "adversarial",
    ]),
]

# ---------------------------------------------------------------------------
# Star tier definitions (label, min_stars, max_stars_exclusive)
# Matches the tiers already in repos.json from the heuristic analyzer.
# ---------------------------------------------------------------------------
STAR_TIERS: list[tuple[str, int, int | None]] = [
    ("100k+",    100000, None),
    ("50k-100k", 50000,  100000),
    ("10k-50k",  10000,  50000),
    ("5k-10k",   5000,   10000),
    ("1k-5k",    1000,   5000),
    ("500-1k",   500,    1000),
    ("100-500",  100,    500),
    ("50-100",   50,     100),
    ("10-50",    10,     50),
    ("0-10",     0,      10),
]


def classify_star_tier(stars: int) -> str:
    """Return the star-tier label for a given star count."""
    for label, lo, hi in STAR_TIERS:
        if hi is None:
            if stars >= lo:
                return label
        elif lo <= stars < hi:
            return label
    return "0-10"


def classify_owner_type(full_name: str) -> str:
    """Classify repo owner as big_tech, company, or personal."""
    owner = full_name.split("/")[0].lower()
    if owner in BIG_TECH_ORGS:
        return "big_tech"
    # Heuristics for company-like orgs: contains hyphen, or all-lowercase multi-word
    # patterns typical of org accounts (e.g. "some-company", "labs", "inc", "io")
    company_signals = [
        "-labs", "-ai", "-dev", "-research", "-inc", "-io",
        "labs", "inc", "official", "hq",
    ]
    if any(sig in owner for sig in company_signals):
        return "company"
    if "-" in owner and len(owner) > 6:
        return "company"
    return "personal"


def classify_categories(repo: dict[str, Any]) -> list[str]:
    """Derive category labels from description, topics, sources, and name."""
    text_parts: list[str] = []
    text_parts.append(repo.get("description", "") or "")
    text_parts.append(repo.get("full_name", "") or "")
    text_parts.extend(repo.get("topics", []))
    for src in repo.get("sources", []):
        # e.g. "search:agent" -> "agent"
        if ":" in src:
            text_parts.append(src.split(":", 1)[1])
    blob = " ".join(text_parts).lower()

    matched: list[str] = []
    for cat_name, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in blob:
                matched.append(cat_name)
                break
    return matched if matched else ["Uncategorized"]


def classify_source_type(sources: list[str]) -> str:
    """Return the primary source bucket: search, topic, new, devpost, trending."""
    priority = ["trending", "search", "topic", "new", "devpost"]
    prefixes = {s.split(":")[0] for s in sources}
    for p in priority:
        if p in prefixes:
            return p
    return "other"


def enrich_repo(repo: dict[str, Any]) -> dict[str, Any]:
    """Add computed fields if not already present."""
    if "_star_tier" not in repo:
        repo["_star_tier"] = classify_star_tier(repo.get("stars", 0))
    if "_owner_type" not in repo:
        repo["_owner_type"] = classify_owner_type(repo.get("full_name", ""))
    if "_categories" not in repo:
        repo["_categories"] = classify_categories(repo)
    if "_primary_category" not in repo:
        repo["_primary_category"] = repo["_categories"][0]
    if "_source_type" not in repo:
        repo["_source_type"] = classify_source_type(repo.get("sources", []))
    return repo


# ---------------------------------------------------------------------------
# Slim down repo data for embedding in HTML
# ---------------------------------------------------------------------------
def slim_repo(repo: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields the dashboard needs, keeping HTML payload small."""
    return {
        "n": repo.get("full_name", ""),
        "s": repo.get("stars", 0),
        "l": repo.get("language", "") or "",
        "d": (repo.get("description", "") or "")[:200],
        "t": repo.get("topics", [])[:8],
        "cat": repo.get("_categories", ["Uncategorized"]),
        "pc": repo.get("_primary_category", "Uncategorized"),
        "st": repo.get("_star_tier", "<100"),
        "ot": repo.get("_owner_type", "Personal"),
        "src": repo.get("_source_type", "other"),
        "u": repo.get("html_url", ""),
    }


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------
def generate_html(repos: list[dict[str, Any]]) -> str:
    """Generate the full self-contained HTML dashboard string."""
    slim_data = [slim_repo(r) for r in repos]
    data_json = json.dumps(slim_data, separators=(",", ":"), ensure_ascii=False)
    # Escape sequences that could break <script> context
    data_json = data_json.replace("</", "<\\/").replace("<!--", "<\\!--")

    # Pre-compute aggregate stats for the summary cards
    total = len(repos)
    stars_100 = sum(1 for r in repos if r.get("stars", 0) >= 100)
    total_stars = sum(r.get("stars", 0) for r in repos)
    languages = len({r.get("language", "") for r in repos if r.get("language")})
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return _HTML_TEMPLATE.replace("__DATA_JSON__", data_json).replace(
        "__TOTAL__", str(total)
    ).replace(
        "__STARS_100__", str(stars_100)
    ).replace(
        "__TOTAL_STARS__", f"{total_stars:,}"
    ).replace(
        "__LANGUAGES__", str(languages)
    ).replace(
        "__GENERATED_AT__", generated_at
    )


# ---------------------------------------------------------------------------
# The HTML template (everything in one string)
# ---------------------------------------------------------------------------
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub AI Repo Dashboard</title>
<style>
/* ── Reset & Base ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; }
body {
    font-family: "SF Mono", "Fira Code", "Cascadia Code", "JetBrains Mono", monospace;
    background: #fafafa;
    color: #1a1a1a;
    line-height: 1.5;
    padding: 24px;
    max-width: 1600px;
    margin: 0 auto;
}
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ───────────────────────────────────────────────── */
.header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 24px;
    border-bottom: 2px solid #1a1a1a;
    padding-bottom: 12px;
}
.header h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.5px; }
.header .meta { font-size: 0.75rem; color: #666; }

/* ── Summary Cards ────────────────────────────────────────── */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}
.summary-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 20px;
    text-align: center;
}
.summary-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a1a;
}
.summary-card .label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* ── Section ──────────────────────────────────────────────── */
.section {
    margin-bottom: 40px;
}
.section-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #ccc;
    color: #333;
}

/* ── Heatmap Matrix ───────────────────────────────────────── */
.matrix-scroll { overflow-x: auto; }
.matrix {
    border-collapse: collapse;
    font-size: 0.8rem;
    width: 100%;
}
.matrix th {
    padding: 6px 10px;
    text-align: center;
    background: #f5f5f5;
    border: 1px solid #ddd;
    font-weight: 600;
    color: #555;
    white-space: nowrap;
}
.matrix th.row-label {
    text-align: left;
    min-width: 140px;
    position: sticky;
    left: 0;
    background: #f5f5f5;
    z-index: 1;
}
.matrix td {
    padding: 6px 10px;
    text-align: center;
    border: 1px solid #ddd;
    cursor: pointer;
    transition: outline 0.1s;
    min-width: 72px;
}
.matrix td:hover { outline: 2px solid #e97320; outline-offset: -2px; }
.matrix td.row-label {
    text-align: left;
    font-weight: 600;
    color: #333;
    cursor: default;
    position: sticky;
    left: 0;
    background: #fff;
    z-index: 1;
}
.matrix td.row-label:hover { outline: none; }
.matrix .row-total {
    font-weight: 700;
    background: #f9f9f9;
    color: #333;
    cursor: default;
}
.matrix .row-total:hover { outline: none; }

/* Heatmap cell colors — blue scale */
.heat-0 { background: #fff; color: #bbb; }
.heat-1 { background: #eff6ff; color: #1e40af; }
.heat-2 { background: #dbeafe; color: #1e40af; }
.heat-3 { background: #bfdbfe; color: #1e3a8a; }
.heat-4 { background: #93c5fd; color: #1e3a8a; }
.heat-5 { background: #60a5fa; color: #fff; }
.heat-6 { background: #3b82f6; color: #fff; }
.heat-7 { background: #2563eb; color: #fff; }
.heat-8 { background: #1d4ed8; color: #fff; }

/* ── Bar Charts ───────────────────────────────────────────── */
.bar-chart { margin-top: 8px; }
.bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    font-size: 0.8rem;
}
.bar-label {
    width: 140px;
    flex-shrink: 0;
    text-align: right;
    padding-right: 10px;
    color: #555;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.bar-track {
    flex: 1;
    height: 20px;
    background: #f0f0f0;
    border-radius: 3px;
    overflow: hidden;
    display: flex;
}
.bar-seg {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    color: #fff;
    font-weight: 600;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    transition: width 0.3s;
}
/* bar-seg colors are set inline via JS */
.bar-value {
    width: 48px;
    text-align: right;
    padding-left: 8px;
    color: #888;
    font-size: 0.75rem;
}

/* ── Legend for owner type ────────────────────────────────── */
.legend {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 0.75rem;
    color: #666;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
}
.legend-swatch {
    width: 12px;
    height: 12px;
    border-radius: 2px;
}

/* ── Source Distribution ──────────────────────────────────── */
.source-bars { margin-top: 8px; }
.src-bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    font-size: 0.8rem;
}
.src-bar-label {
    width: 100px;
    text-align: right;
    padding-right: 10px;
    color: #555;
    font-weight: 600;
}
.src-bar-track {
    flex: 1;
    height: 22px;
    background: #f0f0f0;
    border-radius: 3px;
    overflow: hidden;
}
.src-bar-fill {
    height: 100%;
    border-radius: 3px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    font-size: 0.7rem;
    color: #fff;
    font-weight: 600;
    transition: width 0.3s;
}
.src-bar-value {
    width: 60px;
    text-align: right;
    padding-left: 8px;
    color: #888;
    font-size: 0.75rem;
}

/* ── Filters ──────────────────────────────────────────────── */
.filters {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 16px;
    align-items: center;
}
.filters select, .filters input {
    font-family: inherit;
    font-size: 0.8rem;
    padding: 6px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    color: #333;
}
.filters select { min-width: 140px; }
.filters input[type="search"] { min-width: 260px; }
.filter-count {
    font-size: 0.75rem;
    color: #888;
    margin-left: auto;
}
.btn-clear {
    font-family: inherit;
    font-size: 0.75rem;
    padding: 5px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    color: #555;
    cursor: pointer;
}
.btn-clear:hover { background: #f0f0f0; }

/* ── Repo Table ───────────────────────────────────────────── */
.table-scroll { overflow-x: auto; }
.repo-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
}
.repo-table th {
    padding: 8px 10px;
    text-align: left;
    background: #f5f5f5;
    border-bottom: 2px solid #ddd;
    font-weight: 700;
    color: #555;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
}
.repo-table th:hover { color: #e97320; }
.repo-table th .sort-arrow { font-weight: 400; color: #bbb; margin-left: 4px; }
.repo-table th .sort-arrow.active { color: #e97320; }
.repo-table td {
    padding: 6px 10px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
}
.repo-table tr:hover td { background: #fefce8; }
.repo-table .col-stars { text-align: right; white-space: nowrap; font-weight: 600; }
.repo-table .col-name { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.repo-table .col-desc { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #666; }
.repo-table .col-topics { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #888; font-size: 0.7rem; }
.repo-table .col-lang { white-space: nowrap; }
.repo-table .col-cat { white-space: nowrap; }
.repo-table .col-owner { white-space: nowrap; }

.load-more-wrap { text-align: center; margin: 20px 0; }
.btn-load-more {
    font-family: inherit;
    font-size: 0.85rem;
    padding: 8px 24px;
    border: 2px solid #2563eb;
    border-radius: 4px;
    background: #fff;
    color: #2563eb;
    cursor: pointer;
    font-weight: 600;
}
.btn-load-more:hover { background: #eff6ff; }

/* ── Two-col layout for charts ────────────────────────────── */
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
}
@media (max-width: 900px) {
    .two-col { grid-template-columns: 1fr; }
}

/* ── Active filter highlight ──────────────────────────────── */
.matrix td.active-cell {
    outline: 3px solid #e97320;
    outline-offset: -3px;
}
</style>
</head>
<body>

<div class="header">
    <h1>GitHub AI Repo Dashboard</h1>
    <span class="meta">Generated __GENERATED_AT__ | __TOTAL__ repos</span>
</div>

<!-- Summary Cards -->
<div class="summary-grid">
    <div class="summary-card"><div class="value">__TOTAL__</div><div class="label">Total Repos</div></div>
    <div class="summary-card"><div class="value">__STARS_100__</div><div class="label">Repos 100+ Stars</div></div>
    <div class="summary-card"><div class="value">__TOTAL_STARS__</div><div class="label">Total Stars</div></div>
    <div class="summary-card"><div class="value">__LANGUAGES__</div><div class="label">Languages</div></div>
</div>

<!-- Category x Star Tier -->
<div class="section">
    <div class="section-title">Category x Star Tier Matrix</div>
    <div class="matrix-scroll" id="catStarMatrix"></div>
</div>

<!-- Category x Language (100+ stars only) -->
<div class="section">
    <div class="section-title">Category x Language (100+ stars only)</div>
    <div class="matrix-scroll" id="catLangMatrix"></div>
</div>

<!-- Two-col: Owner Type + Source Dist -->
<div class="two-col">
    <div class="section">
        <div class="section-title">Owner Type by Category</div>
        <div class="legend" id="ownerLegend"></div>
        <div id="ownerChart"></div>
    </div>
    <div class="section">
        <div class="section-title">Source Distribution</div>
        <div id="sourceChart"></div>
    </div>
</div>

<!-- Filterable Table -->
<div class="section">
    <div class="section-title">Repo Table</div>
    <div class="filters" id="tableFilters">
        <select id="fCat"><option value="">All Categories</option></select>
        <select id="fTier"><option value="">All Star Tiers</option></select>
        <select id="fLang"><option value="">All Languages</option></select>
        <select id="fOwner"><option value="">All Owner Types</option></select>
        <input type="search" id="fSearch" placeholder="Search name or description...">
        <button class="btn-clear" id="btnClear">Clear Filters</button>
        <span class="filter-count" id="filterCount"></span>
    </div>
    <div class="table-scroll">
        <table class="repo-table" id="repoTable">
            <thead>
                <tr>
                    <th data-key="s" data-type="num" class="col-stars">Stars <span class="sort-arrow">v</span></th>
                    <th data-key="n" data-type="str" class="col-name">Repository <span class="sort-arrow">v</span></th>
                    <th data-key="l" data-type="str" class="col-lang">Language <span class="sort-arrow">v</span></th>
                    <th data-key="pc" data-type="str" class="col-cat">Category <span class="sort-arrow">v</span></th>
                    <th data-key="ot" data-type="str" class="col-owner">Owner <span class="sort-arrow">v</span></th>
                    <th data-key="d" data-type="str" class="col-desc">Description <span class="sort-arrow">v</span></th>
                    <th class="col-topics">Topics</th>
                </tr>
            </thead>
            <tbody id="repoBody"></tbody>
        </table>
    </div>
    <div class="load-more-wrap" id="loadMoreWrap" style="display:none;">
        <button class="btn-load-more" id="btnLoadMore">Load More</button>
    </div>
</div>

<script>
// ── Embedded Data ────────────────────────────────────────────
var REPOS = __DATA_JSON__;

// ── Constants ────────────────────────────────────────────────
var TIER_ORDER = ["100k+","50k-100k","10k-50k","5k-10k","1k-5k","500-1k","100-500","50-100","10-50","0-10"];
var TIER_DISPLAY = {"100k+":"100k+","50k-100k":"50k-100k","10k-50k":"10k-50k","5k-10k":"5k-10k","1k-5k":"1k-5k","500-1k":"500-1k","100-500":"100-500","50-100":"50-100","10-50":"10-50","0-10":"0-10"};
var LANG_COLS = ["Python","TypeScript","Rust","Go","JavaScript","Other"];
var OWNER_TYPES = ["big_tech","company","personal"];
var OWNER_DISPLAY = {"big_tech":"Big Tech","company":"Company","personal":"Personal"};
var SOURCE_COLORS = {search:"#2563eb",topic:"#3b82f6","new":"#60a5fa",devpost:"#93c5fd",trending:"#e97320",other:"#bbb"};

// ── Helpers ──────────────────────────────────────────────────
function fmtStars(n) {
    if (n >= 1000) return (n/1000).toFixed(n >= 10000 ? 0 : 1) + "k";
    return String(n);
}
function escHtml(s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function heatClass(count, maxVal) {
    if (count === 0) return "heat-0";
    var ratio = Math.min(count / Math.max(maxVal, 1), 1);
    var level = Math.ceil(ratio * 8);
    return "heat-" + Math.min(level, 8);
}
function langBucket(lang) {
    if (!lang) return "Other";
    var l = lang.toLowerCase();
    if (l === "python") return "Python";
    if (l === "typescript") return "TypeScript";
    if (l === "rust") return "Rust";
    if (l === "go" || l === "golang") return "Go";
    if (l === "javascript") return "JavaScript";
    return "Other";
}

// ── Collect unique values ────────────────────────────────────
var allCategories = {};
var allLangs = {};
REPOS.forEach(function(r) {
    r.cat.forEach(function(c) { allCategories[c] = (allCategories[c]||0) + 1; });
    if (r.l) allLangs[r.l] = (allLangs[r.l]||0) + 1;
});
var catList = Object.keys(allCategories).sort(function(a,b) { return allCategories[b] - allCategories[a]; });

// ── Populate filter dropdowns ────────────────────────────────
(function() {
    var fCat = document.getElementById("fCat");
    var fTier = document.getElementById("fTier");
    var fLang = document.getElementById("fLang");
    var fOwner = document.getElementById("fOwner");
    catList.forEach(function(c) {
        var o = document.createElement("option"); o.value = c; o.textContent = c + " (" + allCategories[c] + ")";
        fCat.appendChild(o);
    });
    TIER_ORDER.forEach(function(t) {
        var o = document.createElement("option"); o.value = t; o.textContent = t;
        fTier.appendChild(o);
    });
    var topLangs = Object.keys(allLangs).sort(function(a,b){return allLangs[b]-allLangs[a];}).slice(0,20);
    topLangs.forEach(function(l) {
        var o = document.createElement("option"); o.value = l; o.textContent = l + " (" + allLangs[l] + ")";
        fLang.appendChild(o);
    });
    OWNER_TYPES.forEach(function(ot) {
        var o = document.createElement("option"); o.value = ot; o.textContent = OWNER_DISPLAY[ot];
        fOwner.appendChild(o);
    });
})();

// ── Build Category x Star Tier Matrix ────────────────────────
function buildCatStarMatrix() {
    var counts = {};
    var maxVal = 0;
    catList.forEach(function(cat) { counts[cat] = {}; TIER_ORDER.forEach(function(t) { counts[cat][t] = 0; }); });
    REPOS.forEach(function(r) {
        r.cat.forEach(function(c) {
            if (counts[c]) {
                counts[c][r.st] = (counts[c][r.st]||0) + 1;
                if (counts[c][r.st] > maxVal) maxVal = counts[c][r.st];
            }
        });
    });
    var html = '<table class="matrix"><thead><tr><th class="row-label">Category</th>';
    TIER_ORDER.forEach(function(t) { html += '<th>' + escHtml(t) + '</th>'; });
    html += '<th>Total</th></tr></thead><tbody>';
    catList.forEach(function(cat) {
        var rowTotal = 0;
        html += '<tr><td class="row-label">' + escHtml(cat) + '</td>';
        TIER_ORDER.forEach(function(t) {
            var v = counts[cat][t] || 0;
            rowTotal += v;
            html += '<td class="' + heatClass(v, maxVal) + '" data-cat="' + escHtml(cat) + '" data-tier="' + escHtml(t) + '">' + v + '</td>';
        });
        html += '<td class="row-total">' + rowTotal + '</td></tr>';
    });
    html += '</tbody></table>';
    document.getElementById("catStarMatrix").innerHTML = html;

    // Click handler for cells
    document.getElementById("catStarMatrix").addEventListener("click", function(e) {
        var td = e.target.closest("td[data-cat]");
        if (!td) return;
        var cat = td.getAttribute("data-cat");
        var tier = td.getAttribute("data-tier");
        document.getElementById("fCat").value = cat;
        document.getElementById("fTier").value = tier;
        applyFilters();
        document.getElementById("repoTable").scrollIntoView({behavior:"smooth"});
        // Highlight
        document.querySelectorAll("#catStarMatrix td.active-cell").forEach(function(el){el.classList.remove("active-cell");});
        td.classList.add("active-cell");
    });
}

// ── Build Category x Language Matrix (100+ stars) ────────────
function buildCatLangMatrix() {
    var counts = {};
    var maxVal = 0;
    catList.forEach(function(cat) { counts[cat] = {}; LANG_COLS.forEach(function(l) { counts[cat][l] = 0; }); });
    REPOS.forEach(function(r) {
        if (r.s < 100) return;
        var lb = langBucket(r.l);
        r.cat.forEach(function(c) {
            if (counts[c]) {
                counts[c][lb] = (counts[c][lb]||0) + 1;
                if (counts[c][lb] > maxVal) maxVal = counts[c][lb];
            }
        });
    });
    var html = '<table class="matrix"><thead><tr><th class="row-label">Category</th>';
    LANG_COLS.forEach(function(l) { html += '<th>' + escHtml(l) + '</th>'; });
    html += '<th>Total</th></tr></thead><tbody>';
    catList.forEach(function(cat) {
        var rowTotal = 0;
        html += '<tr><td class="row-label">' + escHtml(cat) + '</td>';
        LANG_COLS.forEach(function(l) {
            var v = counts[cat][l] || 0;
            rowTotal += v;
            html += '<td class="' + heatClass(v, maxVal) + '" data-cat="' + escHtml(cat) + '" data-lang="' + escHtml(l) + '">' + v + '</td>';
        });
        html += '<td class="row-total">' + rowTotal + '</td></tr>';
    });
    html += '</tbody></table>';
    document.getElementById("catLangMatrix").innerHTML = html;

    // Click handler
    document.getElementById("catLangMatrix").addEventListener("click", function(e) {
        var td = e.target.closest("td[data-cat]");
        if (!td) return;
        var cat = td.getAttribute("data-cat");
        var lang = td.getAttribute("data-lang");
        document.getElementById("fCat").value = cat;
        // For language filter, map bucket back to exact value (or clear if "Other")
        if (lang && lang !== "Other") {
            document.getElementById("fLang").value = lang;
        } else {
            document.getElementById("fLang").value = "";
        }
        applyFilters();
        document.getElementById("repoTable").scrollIntoView({behavior:"smooth"});
        document.querySelectorAll("#catLangMatrix td.active-cell").forEach(function(el){el.classList.remove("active-cell");});
        td.classList.add("active-cell");
    });
}

// ── Build Owner Type Chart ───────────────────────────────────
var OWNER_COLORS = {"big_tech":"#2563eb","company":"#60a5fa","personal":"#bfdbfe"};
var OWNER_TEXT_COLORS = {"big_tech":"#fff","company":"#fff","personal":"#1e3a8a"};

function buildOwnerChart() {
    // Build legend
    var legendHtml = "";
    OWNER_TYPES.forEach(function(ot) {
        legendHtml += '<div class="legend-item"><div class="legend-swatch" style="background:' + OWNER_COLORS[ot] + '"></div>' + escHtml(OWNER_DISPLAY[ot]) + '</div>';
    });
    document.getElementById("ownerLegend").innerHTML = legendHtml;

    var data = {};
    catList.forEach(function(cat) {
        data[cat] = {total:0};
        OWNER_TYPES.forEach(function(ot) { data[cat][ot] = 0; });
    });
    REPOS.forEach(function(r) {
        if (r.s < 100) return; // focus on notable repos
        r.cat.forEach(function(c) {
            if (data[c]) {
                data[c][r.ot] = (data[c][r.ot]||0) + 1;
                data[c].total++;
            }
        });
    });
    var html = '<div class="bar-chart">';
    catList.forEach(function(cat) {
        var d = data[cat];
        if (d.total === 0) return;
        html += '<div class="bar-row">';
        html += '<div class="bar-label">' + escHtml(cat) + '</div>';
        html += '<div class="bar-track">';
        OWNER_TYPES.forEach(function(ot) {
            var pct = (d[ot] / d.total * 100);
            if (pct < 1) return;
            html += '<div class="bar-seg" style="width:' + pct.toFixed(1) + '%;background:' + OWNER_COLORS[ot] + ';color:' + OWNER_TEXT_COLORS[ot] + '">';
            if (pct > 8) html += d[ot];
            html += '</div>';
        });
        html += '</div>';
        html += '<div class="bar-value">' + d.total + '</div>';
        html += '</div>';
    });
    html += '</div>';
    document.getElementById("ownerChart").innerHTML = html;
}

// ── Build Source Distribution Chart ──────────────────────────
function buildSourceChart() {
    var counts = {};
    REPOS.forEach(function(r) {
        counts[r.src] = (counts[r.src]||0) + 1;
    });
    var srcKeys = Object.keys(counts).sort(function(a,b){return counts[b]-counts[a];});
    var maxSrc = counts[srcKeys[0]] || 1;
    var html = '<div class="source-bars">';
    srcKeys.forEach(function(src) {
        var pct = counts[src] / maxSrc * 100;
        var color = SOURCE_COLORS[src] || "#999";
        html += '<div class="src-bar-row">';
        html += '<div class="src-bar-label">' + escHtml(src) + '</div>';
        html += '<div class="src-bar-track"><div class="src-bar-fill" style="width:' + pct.toFixed(1) + '%;background:' + color + '">';
        if (pct > 15) html += counts[src].toLocaleString();
        html += '</div></div>';
        html += '<div class="src-bar-value">' + counts[src].toLocaleString() + '</div>';
        html += '</div>';
    });
    html += '</div>';
    document.getElementById("sourceChart").innerHTML = html;
}

// ── Filterable Table ─────────────────────────────────────────
var currentSort = {key: "s", dir: -1}; // default: stars desc
var PAGE_SIZE = 200;
var currentPage = 1;
var filteredRepos = REPOS.slice();

function getFiltered() {
    var cat = document.getElementById("fCat").value;
    var tier = document.getElementById("fTier").value;
    var lang = document.getElementById("fLang").value;
    var owner = document.getElementById("fOwner").value;
    var search = document.getElementById("fSearch").value.toLowerCase().trim();

    var result = REPOS.filter(function(r) {
        if (cat && r.cat.indexOf(cat) === -1) return false;
        if (tier && r.st !== tier) return false;
        if (lang && r.l !== lang) return false;
        if (owner && r.ot !== owner) return false;
        if (search) {
            var blob = (r.n + " " + r.d).toLowerCase();
            if (blob.indexOf(search) === -1) return false;
        }
        return true;
    });

    // Sort
    var k = currentSort.key;
    var dir = currentSort.dir;
    result.sort(function(a, b) {
        var va = a[k], vb = b[k];
        if (typeof va === "string") va = va.toLowerCase();
        if (typeof vb === "string") vb = vb.toLowerCase();
        if (va < vb) return -dir;
        if (va > vb) return dir;
        return 0;
    });
    return result;
}

function renderTable() {
    filteredRepos = getFiltered();
    var total = filteredRepos.length;
    var limit = currentPage * PAGE_SIZE;
    var slice = filteredRepos.slice(0, limit);

    var html = "";
    slice.forEach(function(r) {
        html += "<tr>";
        html += '<td class="col-stars">' + fmtStars(r.s) + '</td>';
        html += '<td class="col-name"><a href="' + escHtml(r.u) + '" target="_blank" rel="noopener">' + escHtml(r.n) + '</a></td>';
        html += '<td class="col-lang">' + escHtml(r.l || "-") + '</td>';
        html += '<td class="col-cat">' + escHtml(r.pc) + '</td>';
        html += '<td class="col-owner">' + escHtml(OWNER_DISPLAY[r.ot] || r.ot) + '</td>';
        html += '<td class="col-desc" title="' + escHtml(r.d) + '">' + escHtml(r.d) + '</td>';
        html += '<td class="col-topics">' + r.t.map(function(t){return escHtml(t);}).join(", ") + '</td>';
        html += "</tr>";
    });
    document.getElementById("repoBody").innerHTML = html;
    document.getElementById("filterCount").textContent = total.toLocaleString() + " repos" + (total !== REPOS.length ? " (filtered)" : "");

    // Load more button
    var wrap = document.getElementById("loadMoreWrap");
    if (limit < total) {
        wrap.style.display = "block";
        document.getElementById("btnLoadMore").textContent = "Load More (" + (total - limit).toLocaleString() + " remaining)";
    } else {
        wrap.style.display = "none";
    }

    // Update sort arrows
    document.querySelectorAll(".repo-table th .sort-arrow").forEach(function(el) {
        var th = el.closest("th");
        if (th.getAttribute("data-key") === currentSort.key) {
            el.textContent = currentSort.dir === -1 ? "v" : "^";
            el.classList.add("active");
        } else {
            el.textContent = "v";
            el.classList.remove("active");
        }
    });
}

function applyFilters() {
    currentPage = 1;
    renderTable();
}

// Filter event listeners
["fCat","fTier","fLang","fOwner"].forEach(function(id) {
    document.getElementById(id).addEventListener("change", applyFilters);
});
document.getElementById("fSearch").addEventListener("input", function() {
    // Debounce
    clearTimeout(this._timer);
    this._timer = setTimeout(applyFilters, 200);
});
document.getElementById("btnClear").addEventListener("click", function() {
    document.getElementById("fCat").value = "";
    document.getElementById("fTier").value = "";
    document.getElementById("fLang").value = "";
    document.getElementById("fOwner").value = "";
    document.getElementById("fSearch").value = "";
    document.querySelectorAll("td.active-cell").forEach(function(el){el.classList.remove("active-cell");});
    applyFilters();
});
document.getElementById("btnLoadMore").addEventListener("click", function() {
    currentPage++;
    renderTable();
});

// Sort by column header click
document.querySelectorAll(".repo-table th[data-key]").forEach(function(th) {
    th.addEventListener("click", function() {
        var key = this.getAttribute("data-key");
        if (currentSort.key === key) {
            currentSort.dir *= -1;
        } else {
            currentSort.key = key;
            currentSort.dir = this.getAttribute("data-type") === "num" ? -1 : 1;
        }
        currentPage = 1;
        renderTable();
    });
});

// ── Initialize ───────────────────────────────────────────────
buildCatStarMatrix();
buildCatLangMatrix();
buildOwnerChart();
buildSourceChart();
renderTable();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def generate_dashboard(repos: list, output_path: str = None) -> str:
    """Generate dashboard HTML from repo list. Importable entry point."""
    from pathlib import Path
    output_path = Path(output_path) if output_path else OUTPUT_HTML
    for repo in repos:
        enrich_repo(repo)
    html = generate_html(repos)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Dashboard: {output_path} ({size_mb:.1f} MB)")
    return str(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an interactive HTML dashboard from repos.json"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated dashboard in the default browser",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(REPOS_JSON),
        help=f"Path to repos.json (default: {REPOS_JSON})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_HTML),
        help=f"Output HTML path (default: {OUTPUT_HTML})",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load repos
    if not input_path.exists():
        print(f"ERROR: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {input_path} ...")
    with open(input_path) as f:
        repos: list[dict[str, Any]] = json.load(f)

    if not isinstance(repos, list):
        print("ERROR: repos.json must contain a JSON array.", file=sys.stderr)
        sys.exit(1)

    print(f"  Loaded {len(repos):,} repos")

    # Check for pre-existing categorization
    categorized = sum(1 for r in repos if "_categories" in r)
    if categorized == 0:
        print("  WARNING: No repos have _categories field. Computing categories from heuristics ...")
    elif categorized < len(repos):
        print(f"  {categorized:,}/{len(repos):,} repos already categorized. Computing rest from heuristics ...")
    else:
        print(f"  All {categorized:,} repos already categorized.")

    # Enrich
    for repo in repos:
        enrich_repo(repo)

    # Stats
    cat_counts: Counter[str] = Counter()
    for r in repos:
        for c in r.get("_categories", []):
            cat_counts[c] += 1
    print(f"  Categories: {len(cat_counts)}")
    for cat, count in cat_counts.most_common():
        print(f"    {cat:24s} {count:>6,}")

    # Generate HTML
    print(f"\nGenerating dashboard ...")
    html = generate_html(repos)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Written to {output_path} ({size_mb:.1f} MB)")

    if args.open:
        url = output_path.as_uri()
        print(f"  Opening {url} ...")
        webbrowser.open(url)

    print("Done.")


if __name__ == "__main__":
    main()
