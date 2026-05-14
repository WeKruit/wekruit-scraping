from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from pipeline.raw_staging import build_raw_envelope

try:
    from config.settings import CROSSREF_MAILTO  # type: ignore
except ModuleNotFoundError:
    CROSSREF_MAILTO = "adam@wekruit.com"

CROSSREF_API_URL = "https://api.crossref.org/works"


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.lower().startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    return normalized.lower()


class CrossrefAdapter:
    source_id = "crossref"

    def __init__(self, *, mailto: str | None = None) -> None:
        self.mailto = (mailto if mailto is not None else CROSSREF_MAILTO).strip()

    def _headers(self) -> dict[str, str]:
        if self.mailto:
            return {
                "Accept": "application/json",
                "User-Agent": f"WeKruit-Research-Bot/1.0 (mailto:{self.mailto})",
            }
        return {
            "Accept": "application/json",
            "User-Agent": "WeKruit-Research-Bot/1.0",
        }

    def fetch_work(self, doi: str) -> dict:
        normalized = normalize_doi(doi)
        if not normalized:
            raise ValueError("DOI is required for Crossref backfill")
        request = Request(
            f"{CROSSREF_API_URL}/{quote(normalized)}",
            headers=self._headers(),
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def build_work_record(
        self,
        *,
        run_id: str,
        doi: str,
        slice_definition: dict[str, str],
        payload: dict,
    ) -> dict:
        normalized = normalize_doi(doi)
        if not normalized:
            raise ValueError("DOI is required for Crossref work records")
        return build_raw_envelope(
            run_id=run_id,
            source_id=self.source_id,
            entity_type="works",
            source_record_id=normalized,
            slice_definition=slice_definition,
            checkpoint_cursor=normalized,
            raw=payload,
        )
