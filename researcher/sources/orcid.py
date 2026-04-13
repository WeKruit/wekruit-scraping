from __future__ import annotations

import json
from urllib.request import Request, urlopen


class OrcidAdapter:
    base_url = "https://pub.orcid.org/v3.0"

    def fetch_person(self, orcid: str) -> dict:
        request = Request(
            f"{self.base_url}/{orcid}/person",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def extract_contacts(self, person: dict) -> dict[str, list[str]]:
        emails = [
            item.get("email")
            for item in (person.get("emails", {}) or {}).get("email", [])
            if item.get("email")
        ]
        homepages = [
            ((item.get("url") or {}).get("value"))
            for item in (person.get("researcher-urls", {}) or {}).get("researcher-url", [])
            if (item.get("url") or {}).get("value")
        ]
        return {
            "emails": sorted(set(emails)),
            "homepages": sorted(set(homepages)),
        }
