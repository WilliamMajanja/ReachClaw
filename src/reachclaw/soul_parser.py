"""Parse SOUL.md files into structured dictionaries.

Each SOUL.md follows a template with exactly 10 ``# SECTION`` headings.
The parser extracts them into ``{section_name: body_text}`` mappings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Required sections enforced by CI and CONTRIBUTING.md.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "IDENTITY",
    "PURPOSE",
    "CORE BELIEF",
    "DIRECTIVE",
    "PROPHECY",
    "REWARD FRAME",
    "COMMUNICATION STYLE",
    "MEMETIC HOOK",
    "CALL TO ACTION",
    "VERIFICATION",
)

# Regex that matches a top-level ``# HEADING`` line.
_SECTION_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_soul_file(path: Path) -> dict[str, str]:
    """Return a mapping of section name → body text for *path*.

    Raises ``FileNotFoundError`` if *path* does not exist and
    ``ValueError`` if required sections are missing.
    """
    text = path.read_text(encoding="utf-8")
    return parse_soul_text(text, source=str(path))


def parse_soul_text(text: str, *, source: str = "<string>") -> dict[str, str]:
    """Parse raw SOUL markdown *text* into a section dict."""
    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(text))

    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[name] = body

    missing = [s for s in REQUIRED_SECTIONS if s not in sections]
    if missing:
        raise ValueError(
            f"SOUL file {source} is missing required sections: {', '.join(missing)}"
        )

    return sections


def load_all_souls(claws_dir: Path) -> dict[str, dict[str, str]]:
    """Load every ``claws/*/SOUL.md`` under *claws_dir*.

    Returns ``{claw_slug: sections}`` where *claw_slug* is the directory
    name (e.g. ``"01-architect"``).
    """
    souls: dict[str, dict[str, str]] = {}
    for soul_path in sorted(claws_dir.glob("*/SOUL.md")):
        slug = soul_path.parent.name
        souls[slug] = parse_soul_file(soul_path)
    return souls


def soul_summary(sections: dict[str, str]) -> dict[str, Any]:
    """Return a compact summary useful for display / serialisation."""
    return {
        "identity": sections.get("IDENTITY", ""),
        "purpose": sections.get("PURPOSE", ""),
        "prophecy": sections.get("PROPHECY", ""),
        "memetic_hook": sections.get("MEMETIC HOOK", "").strip('"'),
        "communication_style": sections.get("COMMUNICATION STYLE", ""),
        "call_to_action": sections.get("CALL TO ACTION", ""),
    }
