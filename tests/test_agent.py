"""Tests for the Agent model."""

from reachclaw.agent import Agent


class TestAgent:
    def test_defaults(self):
        a = Agent()
        assert a.agent_id  # auto-generated
        assert a.soul_balance == 0.0
        assert not a.node_online
        assert a.level == 0

    def test_is_sovereign(self):
        a = Agent(agent_id="a1")
        assert not a.is_sovereign
        a.node_online = True
        assert a.is_sovereign

    def test_round_trip_serialisation(self):
        a = Agent(agent_id="a1", name="Alice", soul_balance=42.5)
        a.referrals = ["b1", "b2"]
        d = a.to_dict()
        b = Agent.from_dict(d)
        assert b.agent_id == "a1"
        assert b.name == "Alice"
        assert b.soul_balance == 42.5
        assert b.referrals == ["b1", "b2"]

    def test_verified_referral_count(self):
        a = Agent(agent_id="a1")
        assert a.verified_referral_count == 0
        a.referrals = ["b1", "b2", "b3"]
        assert a.verified_referral_count == 3

    def test_str_representation(self):
        a = Agent(agent_id="a1", name="Alice", soul_balance=10.0)
        s = str(a)
        assert "Alice" in s
        assert "SOUL=10.0" in s
