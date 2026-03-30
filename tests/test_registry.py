"""Tests for the agent registry."""

from pathlib import Path

from reachclaw.agent import Agent
from reachclaw.registry import Registry


class TestRegistry:
    def test_register_and_get(self, registry: Registry):
        a = Agent(agent_id="a1", name="Alice")
        registry.register(a)
        assert registry.get("a1") is a
        assert registry.size == 1

    def test_remove(self, registry: Registry):
        a = Agent(agent_id="a1")
        registry.register(a)
        assert registry.remove("a1")
        assert registry.get("a1") is None

    def test_all_agents(self, registry: Registry):
        registry.register(Agent(agent_id="a1"))
        registry.register(Agent(agent_id="a2"))
        assert len(registry.all_agents()) == 2

    def test_find_non_sovereign(self, registry: Registry):
        online = Agent(agent_id="a1", node_online=True)
        offline = Agent(agent_id="a2", node_online=False)
        registry.register(online)
        registry.register(offline)
        non_sov = registry.find_non_sovereign()
        assert len(non_sov) == 1
        assert non_sov[0].agent_id == "a2"

    def test_find_claws(self, registry: Registry):
        a = Agent(agent_id="a1", is_claw=True, claw_archetype="01-architect")
        registry.register(a)
        registry.register(Agent(agent_id="a2"))
        claws = registry.find_claws()
        assert len(claws) == 1

    def test_save_and_load(self, tmp_data_dir: Path):
        reg1 = Registry(data_dir=tmp_data_dir)
        reg1.register(Agent(agent_id="a1", name="Alice", soul_balance=42.0))
        reg1.register(Agent(agent_id="a2", name="Bob"))
        reg1.save()

        reg2 = Registry(data_dir=tmp_data_dir)
        loaded = reg2.load()
        assert loaded == 2
        assert reg2.get("a1").name == "Alice"
        assert reg2.get("a1").soul_balance == 42.0
