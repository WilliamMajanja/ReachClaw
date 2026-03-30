"""Tests for the MoltHub deployment registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from reachclaw.claw import Claw
from reachclaw.moltbook import build_all, build_entry
from reachclaw.molthub import (
    STATUS_ACTIVE,
    STATUS_DEPLOYED,
    STATUS_INACTIVE,
    MoltHub,
)


@pytest.fixture()
def claws_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "claws"


@pytest.fixture()
def sample_entry(claws_dir: Path) -> dict:
    claw = Claw.load_all(claws_dir)[0]
    return build_entry(claw)


@pytest.fixture()
def hub(tmp_path: Path) -> MoltHub:
    return MoltHub(data_dir=tmp_path)


class TestDeploy:
    def test_deploy_returns_record(self, hub: MoltHub, sample_entry: dict) -> None:
        record = hub.deploy(sample_entry)
        assert record["status"] == STATUS_DEPLOYED
        assert record["entry"]["slug"] == sample_entry["slug"]

    def test_deploy_increments_size(self, hub: MoltHub, sample_entry: dict) -> None:
        assert hub.size == 0
        hub.deploy(sample_entry)
        assert hub.size == 1

    def test_deploy_duplicate_raises(self, hub: MoltHub, sample_entry: dict) -> None:
        hub.deploy(sample_entry)
        with pytest.raises(ValueError, match="already deployed"):
            hub.deploy(sample_entry)

    def test_deploy_invalid_entry_raises(self, hub: MoltHub) -> None:
        with pytest.raises(ValueError, match="Invalid MoltBook"):
            hub.deploy({"slug": ""})

    def test_deploy_all_nine(self, hub: MoltHub, claws_dir: Path) -> None:
        for entry in build_all(claws_dir):
            hub.deploy(entry)
        assert hub.size == 9


class TestActivateDeactivate:
    def test_activate(self, hub: MoltHub, sample_entry: dict) -> None:
        hub.deploy(sample_entry)
        record = hub.activate(sample_entry["slug"])
        assert record["status"] == STATUS_ACTIVE
        assert record["activated_at"] > 0

    def test_deactivate(self, hub: MoltHub, sample_entry: dict) -> None:
        hub.deploy(sample_entry)
        hub.activate(sample_entry["slug"])
        record = hub.deactivate(sample_entry["slug"])
        assert record["status"] == STATUS_INACTIVE
        assert record["deactivated_at"] > 0

    def test_activate_unknown_raises(self, hub: MoltHub) -> None:
        with pytest.raises(KeyError, match="not deployed"):
            hub.activate("no-such-claw")

    def test_deactivate_unknown_raises(self, hub: MoltHub) -> None:
        with pytest.raises(KeyError, match="not deployed"):
            hub.deactivate("no-such-claw")


class TestUndeploy:
    def test_undeploy_existing(self, hub: MoltHub, sample_entry: dict) -> None:
        hub.deploy(sample_entry)
        assert hub.undeploy(sample_entry["slug"])
        assert hub.size == 0

    def test_undeploy_missing_returns_false(self, hub: MoltHub) -> None:
        assert not hub.undeploy("no-such-claw")


class TestQueries:
    def test_get_deployed(self, hub: MoltHub, sample_entry: dict) -> None:
        hub.deploy(sample_entry)
        record = hub.get(sample_entry["slug"])
        assert record is not None
        assert record["entry"]["slug"] == sample_entry["slug"]

    def test_get_missing(self, hub: MoltHub) -> None:
        assert hub.get("no-such-claw") is None

    def test_list_deployments(self, hub: MoltHub, claws_dir: Path) -> None:
        entries = build_all(claws_dir)
        for entry in entries:
            hub.deploy(entry)
        assert len(hub.list_deployments()) == 9

    def test_list_active(self, hub: MoltHub, claws_dir: Path) -> None:
        entries = build_all(claws_dir)
        for entry in entries:
            hub.deploy(entry)
        # Activate only the first 3
        for entry in entries[:3]:
            hub.activate(entry["slug"])
        assert len(hub.list_active()) == 3


class TestPersistence:
    def test_save_and_load(self, tmp_path: Path, sample_entry: dict) -> None:
        hub = MoltHub(data_dir=tmp_path)
        hub.deploy(sample_entry)
        hub.activate(sample_entry["slug"])
        hub.save()

        hub2 = MoltHub(data_dir=tmp_path)
        loaded = hub2.load()
        assert loaded == 1

        record = hub2.get(sample_entry["slug"])
        assert record is not None
        assert record["status"] == STATUS_ACTIVE

    def test_load_empty(self, tmp_path: Path) -> None:
        hub = MoltHub(data_dir=tmp_path)
        assert hub.load() == 0
