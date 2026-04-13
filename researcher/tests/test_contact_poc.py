import json
from http.client import RemoteDisconnected
from pathlib import Path

from scripts.p2_contact_poc import enrich_author, filter_candidate_emails
from sources.dblp import DBLPAdapter
from sources.openreview import OpenReviewAdapter
from sources.orcid import OrcidAdapter


ROOT = Path(__file__).resolve().parents[1]


def _fixture(path: str) -> dict:
    return json.loads((ROOT / "tests" / "fixtures" / path).read_text(encoding="utf-8"))


def test_orcid_extracts_public_emails_and_homepages():
    payload = _fixture("orcid/person.json")
    contacts = OrcidAdapter().extract_contacts(payload)
    assert contacts == {
        "emails": ["shan.wang@example.edu"],
        "homepages": ["https://shanwang.example.edu"],
    }


def test_openreview_extracts_homepage_and_dblp_url():
    payload = _fixture("openreview/profiles.json")
    contacts = OpenReviewAdapter().extract_contacts(payload)
    assert contacts["openreview_id"] == "~Shan_Wang1"
    assert contacts["homepage"] == "https://openreview-home.example.edu"
    assert contacts["dblp_url"] == "https://dblp.org/pid/62/3650"


def test_dblp_extracts_profile_and_homepage():
    payload = _fixture("dblp/search_author.json")
    contacts = DBLPAdapter().extract_contacts(payload)
    assert contacts["dblp_pid"] == "62/3650"
    assert contacts["dblp_profile_url"] == "https://dblp.org/pid/62/3650"
    assert contacts["homepage"] == "https://dblp-home.example.edu"


def test_dblp_extracts_homepage_from_profile_html():
    html = (ROOT / "tests" / "fixtures" / "dblp" / "profile.html").read_text(encoding="utf-8")
    homepage = DBLPAdapter().extract_profile_homepage(html)
    assert homepage == "http://yann.lecun.com/"


def test_dblp_extracts_first_non_doi_homepage_from_profile_html():
    html = (ROOT / "tests" / "fixtures" / "dblp" / "profile_with_doi_first.html").read_text(encoding="utf-8")
    homepage = DBLPAdapter().extract_profile_homepage(html)
    assert homepage == "https://itol.embl.de/"


class _StubOrcid:
    def fetch_person(self, orcid: str) -> dict:
        return {"orcid": orcid}

    def extract_contacts(self, person: dict) -> dict[str, list[str]]:
        return {"emails": [], "homepages": []}


class _StubOpenReview:
    def search_profiles(self, fullname: str) -> dict:
        return {"name": fullname}

    def extract_contacts(self, payload: dict) -> dict[str, str | None]:
        return {
            "openreview_id": "~Shan_Wang1",
            "homepage": "https://openreview-home.example.edu",
            "dblp_url": "https://dblp.org/pid/62/3650",
        }


class _StubDBLP:
    def search_author(self, name: str) -> dict:
        return {"name": name}

    def extract_contacts(self, payload: dict) -> dict[str, str | None]:
        return {
            "dblp_pid": "62/3650",
            "dblp_profile_url": "https://dblp.org/pid/62/3650",
            "homepage": "https://dblp-home.example.edu",
        }


def test_enrich_author_only_scrapes_real_homepages(monkeypatch):
    scraped_urls: list[str] = []

    def fake_extract_homepage_emails(url: str) -> list[str]:
        scraped_urls.append(url)
        return [f"contact@{url.split('//', 1)[1]}"]

    monkeypatch.setattr("scripts.p2_contact_poc.extract_homepage_emails", fake_extract_homepage_emails)

    author_record = {
        "source_record_id": "https://openalex.org/A5009615188",
        "raw": {
            "name": "Shan Wang",
            "orcid": "0000-0002-0698-4341",
            "institution": "University of Saskatchewan",
        },
    }

    enriched = enrich_author(
        author_record,
        orcid=_StubOrcid(),
        openreview=_StubOpenReview(),
        dblp=_StubDBLP(),
    )

    assert scraped_urls == [
        "https://openreview-home.example.edu",
        "https://dblp-home.example.edu",
    ]
    assert enriched["emails"] == [
        {"value": "contact@openreview-home.example.edu", "source": "homepage:https://openreview-home.example.edu"},
        {"value": "contact@dblp-home.example.edu", "source": "homepage:https://dblp-home.example.edu"},
    ]


def test_filter_candidate_emails_drops_telemetry_domains():
    emails = [
        "researcher@example.edu",
        "2062d0a4929b45348643784b5cb39c36@sentry.wixpress.com",
        "alerts@sentry.io",
    ]
    assert filter_candidate_emails(emails) == ["researcher@example.edu"]


def test_dblp_search_retries_transient_disconnect(monkeypatch):
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"result":{"hits":{"hit":[]}}}'

    attempts = {"count": 0}

    def fake_urlopen(request, timeout=60):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RemoteDisconnected("closed")
        return _Response()

    monkeypatch.setattr("sources.dblp.urlopen", fake_urlopen)
    monkeypatch.setattr("sources.dblp.sleep", lambda _: None)

    payload = DBLPAdapter(backoff_seconds=0, retry_limit=2).search_author("Retry Tester")
    assert payload == {"result": {"hits": {"hit": []}}}
    assert attempts["count"] == 2
