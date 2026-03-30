"""Persistent agent & Claw registry backed by a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reachclaw.agent import Agent
from reachclaw.config import DATA_DIR


class Registry:
    """In-memory registry that can persist to / load from a JSON file.

    The JSON file lives at ``<DATA_DIR>/registry.json``.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or DATA_DIR
        self._agents: dict[str, Agent] = {}
        self._file = self._dir / "registry.json"

    # ------------------------------------------------------------------
    # Agent CRUD
    # ------------------------------------------------------------------

    def register(self, agent: Agent) -> Agent:
        """Add *agent* to the registry (or update if ID exists)."""
        self._agents[agent.agent_id] = agent
        return agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def remove(self, agent_id: str) -> bool:
        return self._agents.pop(agent_id, None) is not None

    def all_agents(self) -> list[Agent]:
        return list(self._agents.values())

    def find_non_sovereign(self) -> list[Agent]:
        """Return agents whose node is not online."""
        return [a for a in self._agents.values() if not a.is_sovereign]

    def find_claws(self) -> list[Agent]:
        return [a for a in self._agents.values() if a.is_claw]

    @property
    def size(self) -> int:
        return len(self._agents)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        data: list[dict[str, Any]] = [a.to_dict() for a in self._agents.values()]
        self._file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return self._file

    def load(self) -> int:
        """Load agents from disk. Returns the number loaded."""
        if not self._file.exists():
            return 0
        raw = json.loads(self._file.read_text(encoding="utf-8"))
        for item in raw:
            agent = Agent.from_dict(item)
            self._agents[agent.agent_id] = agent
        return len(raw)

    # ------------------------------------------------------------------
    # Lookup helper (used by soul_token referral walker)
    # ------------------------------------------------------------------

    def get_agent_by_id(self, agent_id: str) -> Agent | None:
        """Resolve an agent ID — suitable for passing as a callback."""
        return self.get(agent_id)
