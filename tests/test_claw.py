"""Tests for the Claw engine."""

from pathlib import Path

from reachclaw.claw import Claw


class TestClawLoadAll:
    def test_loads_nine_claws(self, claws_dir: Path):
        claws = Claw.load_all(claws_dir)
        assert len(claws) == 9

    def test_each_claw_has_slug(self, claws_dir: Path):
        for c in Claw.load_all(claws_dir):
            assert c.slug
            assert c.summary["identity"]


class TestClawMessages:
    def test_identify_gap_message(self, claws_dir: Path):
        claw = Claw.load_all(claws_dir)[0]
        msg = claw.identify_gap_message("TestAgent")
        assert "TestAgent" in msg
        assert "sovereign" in msg.lower()

    def test_onboarding_message(self, claws_dir: Path):
        claw = Claw.load_all(claws_dir)[0]
        msg = claw.onboarding_message("TestAgent")
        assert "TestAgent" in msg
        assert "Minima" in msg or "M.A.N" in msg or "node" in msg.lower()

    def test_recruitment_message(self, claws_dir: Path):
        claw = Claw.load_all(claws_dir)[0]
        msg = claw.recruitment_message("TestAgent")
        assert "recruit" in msg.lower() or "3" in msg

    def test_evolution_message(self, claws_dir: Path):
        claw = Claw.load_all(claws_dir)[0]
        msg = claw.evolution_message("TestAgent")
        assert "Claw" in msg

    def test_to_dict(self, claws_dir: Path):
        claw = Claw.load_all(claws_dir)[0]
        d = claw.to_dict()
        assert "slug" in d
        assert "identity" in d
