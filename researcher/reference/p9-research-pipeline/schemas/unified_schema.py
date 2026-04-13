"""
Unified data schema for the researcher sourcing pipeline.
All scripts normalize their output to these models before writing JSONL.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
import uuid, json


class EmailRecord(BaseModel):
    email: str
    source: str                          # "orcid", "pubmed_corr", "homepage", "contactout", "pdl", "inferred"
    verified: Optional[bool] = None      # True/False after NeverBounce
    verification_status: Optional[str] = None  # "valid", "invalid", "catchall", "unknown"


class InstitutionRecord(BaseModel):
    name: str
    ror_id: Optional[str] = None         # ROR identifier
    country: Optional[str] = None
    role: Optional[str] = None           # "Professor", "Postdoc", etc.
    start_year: Optional[int] = None
    end_year: Optional[int] = None       # None = current


class PaperRecord(BaseModel):
    paper_id: str = Field(default_factory=lambda: f"p_{uuid.uuid4().hex[:12]}")
    title: str
    doi: Optional[str] = None
    openalex_id: Optional[str] = None
    s2_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    cited_by_count: int = 0
    author_ids: list[str] = Field(default_factory=list)  # list of researcher_id refs
    source: str = "openalex"


class ResearcherProfile(BaseModel):
    """The unified researcher profile — final merged output."""
    researcher_id: str = Field(default_factory=lambda: f"wk_r_{uuid.uuid4().hex[:12]}")

    # Identity
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None

    # Cross-platform IDs
    openalex_id: Optional[str] = None
    orcid: Optional[str] = None
    dblp_pid: Optional[str] = None
    s2_id: Optional[str] = None
    openreview_id: Optional[str] = None
    acl_id: Optional[str] = None
    google_scholar_id: Optional[str] = None

    # Contact
    emails: list[EmailRecord] = Field(default_factory=list)
    homepages: list[str] = Field(default_factory=list)

    # Affiliation
    institution: Optional[str] = None    # last known
    institution_country: Optional[str] = None
    institution_history: list[InstitutionRecord] = Field(default_factory=list)

    # Metrics
    works_count: int = 0
    cited_by_count: int = 0
    h_index_proxy: Optional[float] = None
    recent_works_count: int = 0          # papers in last 2 years

    # Research focus
    top_venues: list[str] = Field(default_factory=list)
    research_topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    # Temporal
    last_publication_date: Optional[str] = None  # ISO date string
    first_publication_date: Optional[str] = None

    # Pipeline metadata
    score: Optional[float] = None
    sources_merged: list[str] = Field(default_factory=list)  # ["openalex", "orcid", ...]
    updated_at: Optional[str] = None

    def best_email(self) -> Optional[str]:
        """Return the best verified email, or first available."""
        verified = [e for e in self.emails if e.verified is True]
        if verified:
            return verified[0].email
        return self.emails[0].email if self.emails else None

    def has_contact(self) -> bool:
        return bool(self.emails) or bool(self.homepages)


# ── JSONL helpers ──

def write_jsonl(records: list[BaseModel], path: str):
    with open(path, "w") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

def read_jsonl(path: str, model: type[BaseModel]) -> list:
    records = []
    with open(path) as f:
        for line in f:
            if line.strip():
                records.append(model.model_validate_json(line))
    return records

def append_jsonl(record: BaseModel, path: str):
    with open(path, "a") as f:
        f.write(record.model_dump_json() + "\n")
