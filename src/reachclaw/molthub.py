"""MoltHub — deployment registry for managing deployed Claw instances.

MoltHub tracks which Claws have been deployed, their current status,
and provides lifecycle management (deploy, activate, deactivate, undeploy).
The hub state is persisted as a JSON file alongside the agent registry.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from reachclaw.config import DATA_DIR
from reachclaw.moltbook import validate_entry


# Valid deployment states.
STATUS_DEPLOYED = "deployed"
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"


class MoltHub:
    """Central deployment hub for Claw archetypes.

    Each deployed Claw is stored as a record containing the MoltBook
    manifest entry plus deployment metadata (status, timestamps).
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or DATA_DIR
        self._deployments: dict[str, dict[str, Any]] = {}
        self._file = self._dir / "molthub.json"

    # ------------------------------------------------------------------
    # Deployment lifecycle
    # ------------------------------------------------------------------

    def deploy(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Deploy a Claw from a validated MoltBook *entry*.

        Raises ``ValueError`` if the entry is invalid or the slug is
        already deployed.
        """
        errors = validate_entry(entry)
        if errors:
            raise ValueError(
                f"Invalid MoltBook entry: {'; '.join(errors)}"
            )

        slug = entry["slug"]
        if slug in self._deployments:
            raise ValueError(f"Claw '{slug}' is already deployed")

        now = time.time()
        record: dict[str, Any] = {
            "entry": entry,
            "status": STATUS_DEPLOYED,
            "deployed_at": now,
            "activated_at": 0.0,
            "deactivated_at": 0.0,
        }
        self._deployments[slug] = record
        return record

    def activate(self, slug: str) -> dict[str, Any]:
        """Set a deployed Claw to *active*."""
        record = self._require(slug)
        record["status"] = STATUS_ACTIVE
        record["activated_at"] = time.time()
        return record

    def deactivate(self, slug: str) -> dict[str, Any]:
        """Set a deployed Claw to *inactive*."""
        record = self._require(slug)
        record["status"] = STATUS_INACTIVE
        record["deactivated_at"] = time.time()
        return record

    def undeploy(self, slug: str) -> bool:
        """Remove a Claw deployment entirely.  Returns ``True`` on success."""
        return self._deployments.pop(slug, None) is not None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, slug: str) -> dict[str, Any] | None:
        """Return the deployment record for *slug*, or ``None``."""
        return self._deployments.get(slug)

    def list_deployments(self) -> list[dict[str, Any]]:
        """Return all deployment records."""
        return list(self._deployments.values())

    def list_active(self) -> list[dict[str, Any]]:
        """Return only deployments with status *active*."""
        return [r for r in self._deployments.values() if r["status"] == STATUS_ACTIVE]

    @property
    def size(self) -> int:
        return len(self._deployments)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> Path:
        """Persist hub state to disk."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(self._deployments, indent=2), encoding="utf-8"
        )
        return self._file

    def load(self) -> int:
        """Load hub state from disk. Returns the number of deployments loaded."""
        if not self._file.exists():
            return 0
        raw = json.loads(self._file.read_text(encoding="utf-8"))
        self._deployments = raw
        return len(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require(self, slug: str) -> dict[str, Any]:
        """Return the record for *slug* or raise ``KeyError``."""
        record = self._deployments.get(slug)
        if record is None:
            raise KeyError(f"Claw '{slug}' is not deployed")
        return record
