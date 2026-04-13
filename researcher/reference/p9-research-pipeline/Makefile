.PHONY: install test fetch-ai fetch-nlp enrich merge rank all clean

install:
	pip install -r requirements.txt
	cp -n config/settings.example.py config/settings.py 2>/dev/null || true
	mkdir -p data
	@echo "✅ Installed. Edit config/settings.py with your API keys."

test:
	python tests/test_apis.py

# ── Example: AI/ML pipeline ──
fetch-ai:
	python scripts/s1_openalex_fetch.py --concept "artificial intelligence" --since 2023 --max-papers 5000
	python scripts/s3_openreview_fetch.py --venue "ICLR 2025"

fetch-nlp:
	python scripts/s1_openalex_fetch.py --concept "natural language processing" --since 2023 --max-papers 3000

enrich:
	python scripts/s2_orcid_enrich.py --input data/authors.jsonl
	python scripts/s4_dblp_lookup.py --input data/authors.jsonl
	python scripts/s7_semantic_scholar.py --input data/authors.jsonl
	python scripts/s5_homepage_email.py --input data/orcid_enriched.jsonl

merge:
	python scripts/s9_merge_pipeline.py --input-dir data/

rank:
	python scripts/s10_score_rank.py --input data/merged_profiles.jsonl

verify:
	python scripts/s8_email_verify.py --input data/merged_profiles.jsonl

# Full pipeline
all: fetch-ai enrich merge rank
	@echo "✅ Pipeline complete. See data/ranked_researchers.csv"

clean:
	rm -f data/*.jsonl data/*.csv
