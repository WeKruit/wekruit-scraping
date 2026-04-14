from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.venue_tiers import (
    CSV_COLUMNS,
    ALLOWED_NORMALIZED_TIERS,
    DEFAULT_VENUE_TIER_ASSET,
    VenueTierRow,
    hash_venue_tier_asset,
    load_venue_tiers,
    matched_ai_cs_venue_tier,
    missing_primary_source,
    source_not_in_ai_cs_table,
    venue_explicitly_excluded,
    venue_row_unresolved,
)


def test_asset_header_and_loaded_rows_are_strict():
    with DEFAULT_VENUE_TIER_ASSET.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        assert next(reader) == list(CSV_COLUMNS)

    rows = load_venue_tiers()

    assert rows["https://openalex.org/S4306420609"] == VenueTierRow(
        canonical_venue_slug="neurips",
        canonical_venue_name="NeurIPS",
        venue_kind="conference",
        openalex_source_id="https://openalex.org/S4306420609",
        openalex_source_display_name="Neural Information Processing Systems",
        ccf_grade="A",
        core_grade="A*",
        normalized_tier="T1",
        include_in_ai_cs_corpus=True,
        evidence_ccf_url="https://www.ccf.org.cn/Academic_Evaluation/AI/",
        evidence_core_url="https://portal.core.edu.au/conf-ranks/98/",
        last_reviewed_at="2026-04-14T00:00:00Z",
        review_notes="CCF AI A and CORE ICORE2026 A*.",
    )
    assert rows["https://openalex.org/S4306419637"].normalized_tier == "T1"
    assert rows["https://openalex.org/S13144211"].normalized_tier == "T3"
    assert rows["https://openalex.org/S4210212817"].normalized_tier == "UNRESOLVED"
    assert rows["https://openalex.org/S4306400194"].normalized_tier == "EXCLUDE"
    assert "https://openalex.org/S134668137" not in rows
    assert all(row.normalized_tier in ALLOWED_NORMALIZED_TIERS for row in rows.values())
    assert any(row.include_in_ai_cs_corpus for row in rows.values())
    assert any(not row.include_in_ai_cs_corpus for row in rows.values())


def test_reason_codes_and_fingerprint_are_stable(tmp_path):
    assert matched_ai_cs_venue_tier == "matched_ai_cs_venue_tier"
    assert missing_primary_source == "missing_primary_source"
    assert source_not_in_ai_cs_table == "source_not_in_ai_cs_table"
    assert venue_row_unresolved == "venue_row_unresolved"
    assert venue_explicitly_excluded == "venue_explicitly_excluded"

    copied = tmp_path / "ai_cs_venue_tiers.csv"
    copied.write_text(DEFAULT_VENUE_TIER_ASSET.read_text(encoding="utf-8"), encoding="utf-8")
    original = hash_venue_tier_asset(DEFAULT_VENUE_TIER_ASSET)
    assert hash_venue_tier_asset(copied) == original

    changed = copied.read_text(encoding="utf-8").replace("NeurIPS", "NeurIPS X", 1)
    copied.write_text(changed, encoding="utf-8")
    assert hash_venue_tier_asset(copied) != original


@pytest.mark.parametrize(
    "csv_text, expected",
    [
        (
            "\n".join(
                    [
                        ",".join(CSV_COLUMNS),
                        "dup,One,conference,https://openalex.org/S1,One,A,A*,T1,true,https://example.com/a,https://example.com/b,2026-04-14T00:00:00Z,ok",
                        "dup,Two,conference,https://openalex.org/S1,Two,A,A*,T1,true,https://example.com/a,https://example.com/b,2026-04-14T00:00:00Z,ok",
                    ]
                )
                + "\n",
                "Duplicate openalex_source_id",
            ),
        (
            "\n".join(
                [
                    ",".join(CSV_COLUMNS),
                    ",One,conference,https://openalex.org/S1,One,A,A*,T1,true,https://example.com/a,https://example.com/b,2026-04-14T00:00:00Z,ok",
                ]
            )
            + "\n",
            "Blank required field",
        ),
        (
            "\n".join(
                [
                    ",".join(CSV_COLUMNS),
                    "bad,One,conference,https://openalex.org/S1,One,A,A*,T9,true,https://example.com/a,https://example.com/b,2026-04-14T00:00:00Z,ok",
                ]
            )
            + "\n",
            "Invalid normalized_tier",
        ),
        (
            "\n".join(
                [
                    ",".join(CSV_COLUMNS),
                    "bad,One,conference,https://openalex.org/S1,One,A,A*,EXCLUDE,true,https://example.com/a,https://example.com/b,2026-04-14T00:00:00Z,ok",
                ]
            )
            + "\n",
            "must be excluded",
        ),
    ],
)
def test_loader_rejects_invalid_assets(tmp_path, csv_text, expected):
    path = tmp_path / "bad.csv"
    path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(ValueError, match=expected):
        load_venue_tiers(path)
