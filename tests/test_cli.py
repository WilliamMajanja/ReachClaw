"""Tests for the CLI."""

import json
from pathlib import Path

from reachclaw.cli import main


class TestCLIDeploy:
    def test_deploy(self, capsys, claws_dir: Path):
        main(["--claws-dir", str(claws_dir), "deploy"])
        out = capsys.readouterr().out
        assert "Deployed" in out
        assert "9" in out


class TestCLIAgentWorkflow:
    def test_register_verify_info_list(self, capsys, tmp_path: Path, claws_dir: Path):
        data = str(tmp_path / "data")

        # Register
        main(["--data-dir", data, "agent", "register", "--agent-id", "test1", "--name", "Tester"])
        out = capsys.readouterr().out
        assert "test1" in out

        # Verify (simulate)
        main(["--data-dir", data, "agent", "verify", "test1", "--simulate"])
        out = capsys.readouterr().out
        assert "online" in out.lower()

        # Info
        main(["--data-dir", data, "agent", "info", "test1"])
        info = json.loads(capsys.readouterr().out)
        assert info["agent_id"] == "test1"
        assert info["node_online"] is True

        # List
        main(["--data-dir", data, "agent", "list"])
        out = capsys.readouterr().out
        assert "Tester" in out


class TestCLIReferAndTick:
    def test_refer_and_tick(self, capsys, tmp_path: Path):
        data = str(tmp_path / "data")

        # Register two agents
        main(["--data-dir", data, "agent", "register", "--agent-id", "r1", "--name", "Referrer"])
        main(["--data-dir", data, "agent", "register", "--agent-id", "r2", "--name", "Referee"])
        capsys.readouterr()

        # Verify both
        main(["--data-dir", data, "agent", "verify", "r1", "--simulate"])
        main(["--data-dir", data, "agent", "verify", "r2", "--simulate"])
        capsys.readouterr()

        # Refer
        main(["--data-dir", data, "refer", "r1", "r2"])
        out = capsys.readouterr().out
        assert "Referral recorded" in out

        # Tick
        main(["--data-dir", data, "tick"])
        out = capsys.readouterr().out
        assert "Tick complete" in out

        # Check balance
        main(["--data-dir", data, "soul", "balance", "r1"])
        out = capsys.readouterr().out
        assert "SOUL" in out


class TestCLIClawList:
    def test_claw_list(self, capsys, claws_dir: Path):
        main(["--claws-dir", str(claws_dir), "claw", "list"])
        out = capsys.readouterr().out
        assert "01-architect" in out


class TestCLIStatus:
    def test_status(self, capsys, tmp_path: Path):
        data = str(tmp_path / "data")
        main(["--data-dir", data, "status"])
        out = capsys.readouterr().out
        assert "Network Status" in out


class TestCLIContribute:
    def test_contribute(self, capsys, tmp_path: Path):
        data = str(tmp_path / "data")
        main(["--data-dir", data, "agent", "register", "--agent-id", "c1"])
        capsys.readouterr()
        main(["--data-dir", data, "contribute", "c1"])
        out = capsys.readouterr().out
        assert "Contribution" in out
