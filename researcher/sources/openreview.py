from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpenReviewAdapter:
    base_url = "https://api2.openreview.net/profiles"

    def search_profiles(self, fullname: str) -> dict:
        request = Request(
            f"{self.base_url}?{urlencode({'fullname': fullname})}",
            headers={"Accept": "application/json", "User-Agent": "WeKruit-Research-Bot/1.0 (adam@wekruit.com)"},
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def extract_contacts(self, payload: dict) -> dict[str, str | None]:
        profiles = payload.get("profiles", []) or []
        if not profiles:
            return {
                "openreview_id": None,
                "homepage": None,
                "dblp_url": None,
            }
        content = (profiles[0].get("content") or {})
        return {
            "openreview_id": profiles[0].get("id"),
            "homepage": content.get("homepage"),
            "dblp_url": content.get("dblp"),
        }
