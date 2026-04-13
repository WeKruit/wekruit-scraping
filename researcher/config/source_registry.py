from __future__ import annotations

from copy import deepcopy


SOURCE_REGISTRY = {
    "openalex": {
        "source_id": "openalex",
        "source_type": "primary_ingest",
        "display_name": "OpenAlex",
        "auth": {
            "api_key_setting": "OPENALEX_API_KEY",
            "required": False,
        },
        "polite_contact": {
            "email_setting": "OPENALEX_EMAIL",
        },
        "retry": {
            "limit_setting": "DEFAULT_RETRY_LIMIT",
            "backoff_setting": "OPENALEX_BACKOFF_SECONDS",
        },
        "rate_limit": {
            "requests_per_second": 10,
        },
        "run_limits": {
            "page_size_setting": "OPENALEX_PAGE_SIZE",
            "max_records_setting": "DEFAULT_MAX_RECORDS",
            "max_pages_setting": "DEFAULT_MAX_PAGES",
        },
        "required_config_keys": [
            "DATA_ROOT",
            "OPENALEX_EMAIL",
            "OPENALEX_PAGE_SIZE",
            "OPENALEX_BACKOFF_SECONDS",
            "DEFAULT_MAX_RECORDS",
            "DEFAULT_MAX_PAGES",
            "DEFAULT_RETRY_LIMIT",
        ],
        "supported_operations": ["discover", "stage_raw"],
        "raw_paths": {
            "works": "data/runs/{run_id}/openalex/works_raw.jsonl",
            "authors": "data/runs/{run_id}/openalex/authors_raw.jsonl",
        },
        "checkpoint_keys": ["cursor", "page_count", "record_count"],
    },
    "crossref": {
        "source_id": "crossref",
        "source_type": "metadata_backfill",
        "display_name": "Crossref",
        "auth": {
            "api_key_setting": None,
            "required": False,
        },
        "polite_contact": {
            "mailto_setting": "CROSSREF_MAILTO",
        },
        "retry": {
            "limit_setting": "DEFAULT_RETRY_LIMIT",
            "backoff_setting": "CROSSREF_BACKOFF_SECONDS",
        },
        "rate_limit": {
            "requests_per_second": 50,
        },
        "run_limits": {
            "page_size_setting": "CROSSREF_PAGE_SIZE",
            "max_records_setting": "DEFAULT_MAX_RECORDS",
            "max_pages_setting": "DEFAULT_MAX_PAGES",
        },
        "required_config_keys": [
            "DATA_ROOT",
            "CROSSREF_MAILTO",
            "CROSSREF_PAGE_SIZE",
            "CROSSREF_BACKOFF_SECONDS",
            "DEFAULT_MAX_RECORDS",
            "DEFAULT_MAX_PAGES",
            "DEFAULT_RETRY_LIMIT",
        ],
        "supported_operations": ["backfill_raw"],
        "raw_paths": {
            "works_backfill": "data/runs/{run_id}/crossref/works_backfill_raw.jsonl",
        },
        "checkpoint_keys": ["doi_cursor", "page_count", "record_count"],
    },
}


def get_source_registry() -> dict[str, dict[str, object]]:
    return deepcopy(SOURCE_REGISTRY)


def get_source_config(source_id: str) -> dict[str, object]:
    if source_id not in SOURCE_REGISTRY:
        raise KeyError(f"Unknown phase-1 source: {source_id}")
    return deepcopy(SOURCE_REGISTRY[source_id])


def validate_source_selection(source_selection: str | list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if source_selection is None:
        return ("openalex",)

    if isinstance(source_selection, str):
        requested = (source_selection,)
    else:
        requested = tuple(source_selection)

    invalid = [source_id for source_id in requested if source_id not in SOURCE_REGISTRY]
    if invalid:
        raise ValueError(f"Unknown phase-1 source(s): {', '.join(invalid)}")

    return requested
