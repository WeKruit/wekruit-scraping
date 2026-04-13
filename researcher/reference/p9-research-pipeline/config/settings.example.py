# config/settings.py — Copy from settings.example.py and fill in your keys
# DO NOT commit this file (add to .gitignore)

# ── OpenAlex ──
OPENALEX_EMAIL = "adam@wekruit.com"      # for polite pool
OPENALEX_API_KEY = ""                     # free, get from https://openalex.org/users/me

# ── Crossref ──
CROSSREF_EMAIL = "adam@wekruit.com"       # for polite pool (50 req/s)

# ── Semantic Scholar ──
S2_API_KEY = ""                           # free, https://www.semanticscholar.org/product/api#api-key

# ── PubMed / NCBI ──
NCBI_API_KEY = ""                         # free, https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
NCBI_EMAIL = "adam@wekruit.com"

# ── NeverBounce ──
NEVERBOUNCE_API_KEY = ""                  # paid, https://app.neverbounce.com

# ── ContactOut (WeKruit existing) ──
CONTACTOUT_API_KEY = ""

# ── People Data Labs (WeKruit existing) ──
PDL_API_KEY = ""

# ── Pipeline Settings ──
DATA_DIR = "data"
DEFAULT_PER_PAGE = 200
MAX_CONCURRENT_REQUESTS = 5
REQUEST_DELAY_SECONDS = 0.1              # default delay between requests
ORCID_RATE_LIMIT = 24                    # requests per second
S2_RATE_LIMIT_FREE = 1                   # without key
S2_RATE_LIMIT_KEY = 100                  # with key
PUBMED_RATE_LIMIT_FREE = 3
PUBMED_RATE_LIMIT_KEY = 10
