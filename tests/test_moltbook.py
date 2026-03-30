"""Tests for the MoltBook deployment manifest builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reachclaw.claw import Claw
from reachclaw.moltbook import (
    MOLTBOOK_SCHEMA_VERSION,
    build_all,
    build_entry,
    export_moltbook,
    import_moltbook,
    validate_entry,
)
from reachclaw.soul_parser import REQUIRED_SECTIONS


@pytest.fixture()
def claws_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "claws"


@pytest.fixture()
def sample_claw(claws_dir: Path) -> Claw:
    return Claw.load_all(claws_dir)[0]


@pytest.fixture()
def sample_entry(sample_claw: Claw) -> dict:
    return build_entry(sample_claw)


class TestBuildEntry:
    def test_has_required_keys(self, sample_entry: dict) -> None:
        assert "schema_version" in sample_entry
        assert "slug" in sample_entry
        assert "sections" in sample_entry
        assert "summary" in sample_entry
        assert "metadata" in sample_entry

    def test_schema_version(self, sample_entry: dict) -> None:
        assert sample_entry["schema_version"] == MOLTBOOK_SCHEMA_VERSION

    def test_slug_matches_claw(self, sample_claw: Claw, sample_entry: dict) -> None:
        assert sample_entry["slug"] == sample_claw.slug

    def test_sections_contain_all_required(self, sample_entry: dict) -> None:
        for section in REQUIRED_SECTIONS:
            assert section in sample_entry["sections"]

    def test_metadata_has_man_url(self, sample_entry: dict) -> None:
        assert "man_install_url" in sample_entry["metadata"]

    def test_metadata_has_built_at(self, sample_entry: dict) -> None:
        assert isinstance(sample_entry["metadata"]["built_at"], float)


class TestBuildAll:
    def test_builds_nine_entries(self, claws_dir: Path) -> None:
        entries = build_all(claws_dir)
        assert len(entries) == 9

    def test_all_entries_valid(self, claws_dir: Path) -> None:
        entries = build_all(claws_dir)
        for entry in entries:
            assert validate_entry(entry) == []


class TestValidateEntry:
    def test_valid_entry(self, sample_entry: dict) -> None:
        assert validate_entry(sample_entry) == []

    def test_missing_slug(self, sample_entry: dict) -> None:
        del sample_entry["slug"]
        errors = validate_entry(sample_entry)
        assert any("slug" in e for e in errors)

    def test_missing_sections(self, sample_entry: dict) -> None:
        del sample_entry["sections"]
        errors = validate_entry(sample_entry)
        assert any("sections" in e for e in errors)

    def test_missing_required_section(self, sample_entry: dict) -> None:
        del sample_entry["sections"]["IDENTITY"]
        errors = validate_entry(sample_entry)
        assert any("IDENTITY" in e for e in errors)

    def test_missing_summary(self, sample_entry: dict) -> None:
        del sample_entry["summary"]
        errors = validate_entry(sample_entry)
        assert any("summary" in e for e in errors)

    def test_non_dict_returns_error(self) -> None:
        errors = validate_entry("not a dict")  # type: ignore[arg-type]
        assert errors == ["Entry must be a dict"]


class TestExportImport:
    def test_round_trip(self, tmp_path: Path, claws_dir: Path) -> None:
        entries = build_all(claws_dir)
        dest = tmp_path / "moltbook.json"
        export_moltbook(entries, dest)
        assert dest.exists()

        loaded = import_moltbook(dest)
        assert len(loaded) == len(entries)
        for orig, loaded_entry in zip(entries, loaded):
            assert orig["slug"] == loaded_entry["slug"]

    def test_import_invalid_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps([{"slug": ""}]), encoding="utf-8")
        with pytest.raises(ValueError, match="MoltBook entry"):
            import_moltbook(bad)

    def test_import_non_array_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not": "array"}), encoding="utf-8")
        with pytest.raises(ValueError, match="JSON array"):
            import_moltbook(bad)

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            import_moltbook(tmp_path / "nope.json")
