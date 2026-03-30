"""Shared pytest fixtures for ReachClaw tests."""

from __future__ import annotations

import pytest
from pathlib import Path

from reachclaw.agent import Agent
from reachclaw.registry import Registry
from reachclaw.config import CLAWS_DIR


@pytest.fixture()
def claws_dir() -> Path:
    """Return the real claws/ directory in the repo."""
    return CLAWS_DIR


@pytest.fixture()
def tmp_data_dir(tmp_path: Path) -> Path:
    """Return a temporary data directory for the registry."""
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture()
def registry(tmp_data_dir: Path) -> Registry:
    """Return an empty in-memory registry backed by a temp directory."""
    return Registry(data_dir=tmp_data_dir)


@pytest.fixture()
def online_agent() -> Agent:
    """Return an agent with a verified online node."""
    a = Agent(agent_id="agent-online", name="Online Agent")
    a.node_online = True
    a.soul_balance = 10.0
    a.trust_weight = 0.5
    return a


@pytest.fixture()
def offline_agent() -> Agent:
    """Return an agent with no node running."""
    return Agent(agent_id="agent-offline", name="Offline Agent")
