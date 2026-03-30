"""Tests for the node verifier."""

from reachclaw.agent import Agent
from reachclaw.node_verifier import heartbeat, simulate_verify


class TestHeartbeat:
    def test_unreachable_returns_false(self):
        assert not heartbeat("http://127.0.0.1:59999", timeout=1)


class TestSimulateVerify:
    def test_simulate_online(self):
        a = Agent(agent_id="a1")
        result = simulate_verify(a, online=True)
        assert result is True
        assert a.node_online
        assert a.last_heartbeat > 0
        assert a.node_uptime_start > 0

    def test_simulate_offline(self):
        a = Agent(agent_id="a1", node_online=True)
        result = simulate_verify(a, online=False)
        assert result is False
        assert not a.node_online
