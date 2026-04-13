from __future__ import annotations

import json
import re
from http.client import RemoteDisconnected
from time import monotonic, sleep
from urllib.parse import urlencode, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VISIT_URL_RE = re.compile(r'<a href="([^"]+)"[^>]*itemprop="url"')
NON_HOMEPAGE_HOSTS = {"doi.org", "dx.doi.org"}


class DBLPAdapter:
    base_url = "https://dblp.org/search/author/api"

    def __init__(self, *, backoff_seconds: float = 1.0, retry_limit: int = 3) -> None:
        self.backoff_seconds = backoff_seconds
        self.retry_limit = retry_limit
        self._last_request_started_at = 0.0

    def _throttle(self) -> None:
        elapsed = monotonic() - self._last_request_started_at
        if self._last_request_started_at and elapsed < self.backoff_seconds:
            sleep(self.backoff_seconds - elapsed)
        self._last_request_started_at = monotonic()

    def _open(self, request: Request, *, timeout: int = 60) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_limit + 1):
            self._throttle()
            try:
                with urlopen(request, timeout=timeout) as response:
                    return response.read().decode("utf-8", errors="ignore")
            except (HTTPError, URLError, RemoteDisconnected) as exc:
                last_error = exc
                if attempt >= self.retry_limit:
                    raise
                sleep(self.backoff_seconds * attempt)
        if last_error is not None:
            raise last_error
        raise RuntimeError("DBLP request failed without raising an exception")

    def search_author(self, name: str, *, limit: int = 3) -> dict:
        request = Request(
            f"{self.base_url}?{urlencode({'q': name, 'format': 'json', 'h': limit})}",
            headers={"User-Agent": "WeKruit-Research-Bot/1.0 (adam@wekruit.com)"},
        )
        return json.loads(self._open(request, timeout=60))

    def extract_contacts(self, payload: dict) -> dict[str, str | None]:
        hits = (((payload.get("result") or {}).get("hits") or {}).get("hit") or [])
        if isinstance(hits, dict):
            hits = [hits]
        if not hits:
            return {
                "dblp_pid": None,
                "dblp_profile_url": None,
                "homepage": None,
            }
        info = hits[0].get("info", {}) or {}
        notes = info.get("notes", {}) or {}
        note_items = notes.get("note", []) if isinstance(notes, dict) else []
        if isinstance(note_items, dict):
            note_items = [note_items]
        homepage = None
        for note in note_items:
            if isinstance(note, dict) and note.get("@type") == "homepage":
                homepage = note.get("text") or note.get("#text")
                break
        profile_url = info.get("url")
        pid = profile_url.replace("https://dblp.org/pid/", "") if profile_url else None
        return {
            "dblp_pid": pid,
            "dblp_profile_url": profile_url,
            "homepage": homepage,
        }

    def extract_profile_homepage(self, html: str) -> str | None:
        visit_pos = html.find('class="visit drop-down"')
        if visit_pos == -1:
            return None
        visit_slice = html[visit_pos : visit_pos + 12000]
        urls = VISIT_URL_RE.findall(visit_slice)
        for url in urls:
            host = urlparse(url).netloc.lower()
            if host in NON_HOMEPAGE_HOSTS:
                continue
            return url
        return urls[0] if urls else None

    def fetch_profile_homepage(self, profile_url: str) -> str | None:
        request = Request(
            profile_url,
            headers={"User-Agent": "WeKruit-Research-Bot/1.0 (adam@wekruit.com)"},
        )
        return self.extract_profile_homepage(self._open(request, timeout=30))
