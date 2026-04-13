from __future__ import annotations

from collections import OrderedDict
import json
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pipeline.raw_staging import build_raw_envelope


OPENALEX_API_URL = "https://api.openalex.org/works"


def _strip_openalex_id(value: str | None) -> str | None:
    if not value:
        return None
    return value.rsplit("/", 1)[-1]


def _build_slice_definition(preset: dict[str, Any]) -> dict[str, str]:
    return {"type": str(preset["family"]), "value": str(preset["label"])}


class OpenAlexAdapter:
    source_id = "openalex"

    def build_query(
        self,
        preset: dict[str, Any],
        *,
        since_year: int,
        max_records: int,
        max_pages: int | None,
        cursor: str = "*",
        per_page: int | None = None,
    ) -> dict[str, Any]:
        filters = dict(preset.get("filter", {}))
        filters["from_publication_date"] = f"{since_year}-01-01"
        params: dict[str, Any] = {
            "search": str(preset["search"]),
            "filter": ",".join(f"{key}:{value}" for key, value in filters.items()),
            "per-page": per_page or min(max_records, 200),
            "cursor": cursor,
        }
        return {
            "url": OPENALEX_API_URL,
            "params": params,
            "preset": preset,
            "max_records": max_records,
            "max_pages": max_pages,
        }

    def fetch_page(self, query: dict[str, Any], *, cursor: str = "*") -> dict[str, Any]:
        params = dict(query["params"])
        params["cursor"] = cursor
        request = Request(
            f"{query['url']}?{urlencode(params)}",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def parse_page(
        self,
        works: Iterable[dict[str, Any]],
        *,
        preset: dict[str, Any],
        run_id: str,
        page_number: int | None = None,
        checkpoint_cursor: str | None = None,
        seen_authors: OrderedDict[str, dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        slice_definition = _build_slice_definition(preset)
        author_index = seen_authors if seen_authors is not None else OrderedDict()
        work_records: list[dict[str, Any]] = []
        new_author_ids: list[str] = []

        for work in works:
            work_id = work.get("id")
            if not work_id:
                continue
            work_records.append(
                build_raw_envelope(
                    run_id=run_id,
                    source_id=self.source_id,
                    entity_type="works",
                    source_record_id=str(work_id),
                    slice_definition=slice_definition,
                    checkpoint_cursor=checkpoint_cursor,
                    page_number=page_number,
                    raw=work,
                )
            )

            for authorship in work.get("authorships", []) or []:
                author = authorship.get("author", {}) or {}
                author_id = author.get("id")
                if not author_id:
                    continue
                dedup_key = str(author_id)
                if dedup_key not in author_index:
                    institutions = authorship.get("institutions", []) or []
                    first_institution = institutions[0] if institutions else {}
                    author_index[dedup_key] = {
                        "source_record_id": dedup_key,
                        "name": author.get("display_name"),
                        "orcid": _strip_openalex_id(author.get("orcid")),
                        "institution": first_institution.get("display_name"),
                        "institution_ror": first_institution.get("ror"),
                        "institution_country": first_institution.get("country_code"),
                        "is_corresponding": bool(authorship.get("is_corresponding", False)),
                        "paper_count_in_batch": 0,
                    }
                    new_author_ids.append(dedup_key)
                author_index[dedup_key]["paper_count_in_batch"] += 1
                if authorship.get("is_corresponding"):
                    author_index[dedup_key]["is_corresponding"] = True

        author_records = [
            build_raw_envelope(
                run_id=run_id,
                source_id=self.source_id,
                entity_type="authors",
                source_record_id=author_data["source_record_id"],
                slice_definition=slice_definition,
                checkpoint_cursor=checkpoint_cursor,
                page_number=page_number,
                raw=author_data,
            )
            for author_id, author_data in author_index.items()
            if author_id in new_author_ids
        ]
        return work_records, author_records
