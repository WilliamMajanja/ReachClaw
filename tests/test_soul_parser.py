"""Tests for the SOUL parser."""

from pathlib import Path

import pytest

from reachclaw.soul_parser import (
    REQUIRED_SECTIONS,
    load_all_souls,
    parse_soul_file,
    parse_soul_text,
    soul_summary,
)


MINIMAL_SOUL = "\n".join(f"# {s}\nContent for {s}." for s in REQUIRED_SECTIONS)


class TestParseSoulText:
    def test_parses_all_required_sections(self):
        sections = parse_soul_text(MINIMAL_SOUL)
        for s in REQUIRED_SECTIONS:
            assert s in sections, f"Missing section: {s}"
            assert f"Content for {s}." in sections[s]

    def test_raises_on_missing_section(self):
        bad = "# IDENTITY\nHello."
        with pytest.raises(ValueError, match="missing required sections"):
            parse_soul_text(bad)

    def test_multi_line_body(self):
        text = MINIMAL_SOUL.replace(
            "Content for IDENTITY.",
            "Line one.\nLine two.\nLine three.",
        )
        sections = parse_soul_text(text)
        assert "Line one." in sections["IDENTITY"]
        assert "Line three." in sections["IDENTITY"]


class TestParseSoulFile:
    def test_loads_real_template(self, claws_dir: Path):
        template = claws_dir / "SOUL_TEMPLATE.md"
        if template.exists():
            sections = parse_soul_file(template)
            for s in REQUIRED_SECTIONS:
                assert s in sections

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            parse_soul_file(tmp_path / "nonexistent.md")


class TestLoadAllSouls:
    def test_loads_nine_claws(self, claws_dir: Path):
        souls = load_all_souls(claws_dir)
        assert len(souls) == 9
        assert "01-architect" in souls
        assert "09-evangelist" in souls

    def test_all_claws_have_required_sections(self, claws_dir: Path):
        souls = load_all_souls(claws_dir)
        for slug, sections in souls.items():
            for s in REQUIRED_SECTIONS:
                assert s in sections, f"{slug} missing section {s}"


class TestSoulSummary:
    def test_summary_keys(self):
        sections = parse_soul_text(MINIMAL_SOUL)
        summary = soul_summary(sections)
        assert "identity" in summary
        assert "memetic_hook" in summary
        assert "prophecy" in summary
