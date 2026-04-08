#!/usr/bin/env python3
"""
GitHub Talent Discovery — Configuration
=========================================
Central config for search parameters, scoring weights, and API settings.

Set your GitHub PAT:
    export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
"""

import os

# ── GitHub Authentication ──
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# ── Search Keyword Groups ──
# Each group targets a specific AI sub-domain
SEARCH_KEYWORDS = {
    "agent": [
        "ai agent", "llm agent", "autonomous agent",
        "multi-agent", "agentic", "agent framework",
    ],
    "rag": [
        "rag", "retrieval augmented", "vector database",
        "embedding", "knowledge base", "semantic search",
    ],
    "infra": [
        "llm framework", "inference engine", "model serving",
        "fine-tuning", "llm inference", "quantization",
    ],
    "application": [
        "ai coding", "ai assistant", "copilot",
        "chatbot", "ai workflow", "ai automation",
    ],
    "frontier": [
        "mcp server", "function calling", "tool use",
        "multimodal", "vision language model", "voice ai",
    ],
}

# ── Star Ranges (maps to project tiers) ──
STAR_RANGES = {
    "emerging":    (100, 500),
    "rising":      (500, 2000),
    "established": (2000, 5000),
    "major":       (5000, None),   # 5000+, no upper bound
}

# ── Languages to search ──
LANGUAGES = ["python", "typescript", "rust"]

# ── GitHub Topics for targeted search ──
TOPICS = [
    # Core AI (existing)
    "llm", "langchain", "rag", "agents", "gpt",
    "chatgpt", "openai", "anthropic", "llama",
    "transformer", "nlp", "generative-ai",
    # AI Agent ecosystem
    "ai-agent", "ai-agents", "autonomous-agents", "agentic",
    "mcp", "model-context-protocol", "claude", "claude-code",
    # AI/ML fundamentals
    "ai", "artificial-intelligence", "machine-learning",
    "deep-learning", "pytorch", "huggingface",
    # AI infra
    "ollama", "vllm", "inference", "fine-tuning", "lora",
    "embeddings", "vector-database", "prompt-engineering",
    # AI coding/tools
    "ai-coding", "ai-assistant", "copilot", "devtools",
    # Adjacent high-signal
    "gemini", "mistral", "mlops", "multimodal",
]

# ── Trending page config ──
TRENDING_LANGUAGES = ["python", "typescript"]
TRENDING_PERIODS = ["daily", "weekly"]

# ── Contributor extraction ──
MIN_COMMITS = 3           # Minimum commits to be considered
MAX_CONTRIBUTORS = 20     # Max contributors per repo
ENRICHMENT_WORKERS = 5    # Concurrent profile fetches

# ── Scoring weights (total = 100) ──
SCORING = {
    "activity": {
        "weight": 40,
        "commit_count_max": 15,       # pts for commit volume
        "repo_count_max": 10,         # pts for multi-project
        "recency_max": 10,            # pts for recent activity
        "public_repos_max": 5,        # pts for own repos
    },
    "influence": {
        "weight": 30,
        "project_stars_max": 15,      # pts for contributed project stars
        "followers_max": 10,          # pts for personal followers
        "personal_stars_max": 5,      # pts for personal repo stars
    },
    "reachability": {
        "weight": 20,
        "has_email": 20,              # full pts
        "has_twitter_or_blog": 10,    # partial pts
        "nothing": 0,
    },
    "profile": {
        "weight": 10,
        "has_name": 3,
        "has_bio": 3,
        "has_company": 2,
        "has_location": 2,
    },
}

SCORE_THRESHOLD = 40      # Minimum score to include in output

# ── Rate Limit Settings ──
REST_RATE_LIMIT = 5000         # requests per hour (authenticated)
SEARCH_RATE_LIMIT = 30         # requests per minute
REQUEST_DELAY = 0.8            # seconds between REST API calls
SEARCH_DELAY = 2.5             # seconds between search queries
RETRY_MAX = 3
RETRY_BACKOFF_BASE = 10        # seconds

# ── Time Windows ──
# How far back to look for active projects
PUSHED_AFTER_MONTHS = 6        # Only repos pushed in last N months
CREATED_AFTER_MONTHS = 18      # For "emerging" projects, created in last N months

# ── Seed repos (manually curated) ──
SEED_REPOS = [
    # Add repos you want to always track
    # "langchain-ai/langchain",
    # "vllm-project/vllm",
    # "run-llama/llama_index",
]

# ── Devpost integration ──
DEVPOST_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "devpost", "output"
)

# ── Output paths ──
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# ── Email filters ──
INVALID_EMAIL_PATTERNS = [
    "@users.noreply.github.com",
    "@github.com",
    "noreply@",
    "@example.com",
]
