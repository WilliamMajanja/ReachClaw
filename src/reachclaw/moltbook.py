"""MoltBook — deployment manifest builder for Claw archetypes.

A MoltBook entry packages a Claw's SOUL.md, configuration, and metadata
into a portable JSON manifest that can be validated, exported, and used
by MoltHub for deployment.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from reachclaw.claw import Claw
from reachclaw.config import CLAWS_DIR, MAN_INSTALL_URL
from reachclaw.soul_parser import REQUIRED_SECTIONS


# Current manifest schema version.
MOLTBOOK_SCHEMA_VERSION: str = "1.0"


def build_entry(claw: Claw) -> dict[str, Any]:
    """Build a MoltBook manifest entry from a loaded *claw*.

    The entry contains everything needed to deploy the Claw on MoltHub:
    identity, sections, summary, and deployment metadata.
    """
    return {
        "schema_version": MOLTBOOK_SCHEMA_VERSION,
        "slug": claw.slug,
        "sections": dict(claw.sections),
        "summary": claw.summary,
        "metadata": {
            "man_install_url": MAN_INSTALL_URL,
            "built_at": time.time(),
        },
    }


def build_all(claws_dir: Path | None = None) -> list[dict[str, Any]]:
    """Build MoltBook entries for every Claw archetype under *claws_dir*."""
    claws_dir = claws_dir or CLAWS_DIR
    claws = Claw.load_all(claws_dir)
    return [build_entry(c) for c in claws]


def validate_entry(entry: dict[str, Any]) -> list[str]:
    """Validate a MoltBook manifest entry.

    Returns a list of error strings.  An empty list means valid.
    """
    errors: list[str] = []

    if not isinstance(entry, dict):
        return ["Entry must be a dict"]

    if "slug" not in entry or not entry["slug"]:
        errors.append("Missing or empty 'slug'")

    if "schema_version" not in entry:
        errors.append("Missing 'schema_version'")

    sections = entry.get("sections")
    if not isinstance(sections, dict):
        errors.append("Missing or invalid 'sections'")
    else:
        for req in REQUIRED_SECTIONS:
            if req not in sections:
                errors.append(f"Missing required section: {req}")

    if "summary" not in entry or not isinstance(entry.get("summary"), dict):
        errors.append("Missing or invalid 'summary'")

    return errors


def export_moltbook(entries: list[dict[str, Any]], dest: Path) -> Path:
    """Write a list of MoltBook entries to *dest* as JSON."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return dest


def import_moltbook(src: Path) -> list[dict[str, Any]]:
    """Load MoltBook entries from a JSON file at *src*.

    Raises ``FileNotFoundError`` if *src* does not exist and
    ``ValueError`` if any entry fails validation.
    """
    raw = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("MoltBook file must contain a JSON array")

    entries: list[dict[str, Any]] = []
    for idx, entry in enumerate(raw):
        errors = validate_entry(entry)
        if errors:
            raise ValueError(
                f"MoltBook entry {idx} ({entry.get('slug', '?')}): "
                + "; ".join(errors)
            )
        entries.append(entry)
    return entries
