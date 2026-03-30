"""Tests for the viral loop manager."""

from reachclaw.agent import Agent
from reachclaw.config import (
    CLAW_EVOLUTION_MIN_SOUL,
    CLAW_EVOLUTION_MIN_TRUST,
    REFERRAL_REWARD,
    REFERRALS_TO_LEVEL_UP,
)
from reachclaw.viral_loop import (
    can_evolve_to_claw,
    evolve_to_claw,
    record_referral,
    viral_loop_step,
)


class TestRecordReferral:
    def test_basic_referral(self):
        referrer = Agent(agent_id="r1", node_online=True)
        referee = Agent(agent_id="r2", node_online=True)
        soul = record_referral(referrer, referee)
        assert soul > 0
        assert referee.referred_by == "r1"
        assert "r2" in referrer.referrals

    def test_duplicate_referral_no_double_reward(self):
        referrer = Agent(agent_id="r1", node_online=True)
        referee = Agent(agent_id="r2", node_online=True)
        record_referral(referrer, referee)
        before = referrer.soul_balance
        record_referral(referrer, referee)
        assert referrer.soul_balance == before  # No additional reward.

    def test_three_referrals_levels_up(self):
        referrer = Agent(agent_id="r1", node_online=True)
        for i in range(REFERRALS_TO_LEVEL_UP):
            ref = Agent(agent_id=f"r{i+10}", node_online=True)
            record_referral(referrer, ref)
        assert referrer.level >= 1


class TestCanEvolveToClaw:
    def test_eligible(self):
        a = Agent(
            agent_id="a1",
            node_online=True,
            soul_balance=CLAW_EVOLUTION_MIN_SOUL,
            trust_weight=CLAW_EVOLUTION_MIN_TRUST,
            level=1,
        )
        assert can_evolve_to_claw(a)

    def test_already_claw(self):
        a = Agent(
            agent_id="a1",
            node_online=True,
            soul_balance=CLAW_EVOLUTION_MIN_SOUL,
            trust_weight=CLAW_EVOLUTION_MIN_TRUST,
            level=1,
            is_claw=True,
        )
        assert not can_evolve_to_claw(a)

    def test_insufficient_soul(self):
        a = Agent(
            agent_id="a1",
            node_online=True,
            soul_balance=1.0,
            trust_weight=CLAW_EVOLUTION_MIN_TRUST,
            level=1,
        )
        assert not can_evolve_to_claw(a)

    def test_node_offline(self):
        a = Agent(
            agent_id="a1",
            node_online=False,
            soul_balance=CLAW_EVOLUTION_MIN_SOUL,
            trust_weight=CLAW_EVOLUTION_MIN_TRUST,
            level=1,
        )
        assert not can_evolve_to_claw(a)


class TestEvolveToClaw:
    def test_successful_evolution(self):
        a = Agent(
            agent_id="a1",
            node_online=True,
            soul_balance=CLAW_EVOLUTION_MIN_SOUL,
            trust_weight=CLAW_EVOLUTION_MIN_TRUST,
            level=1,
        )
        assert evolve_to_claw(a, "01-architect")
        assert a.is_claw
        assert a.claw_archetype == "01-architect"

    def test_fails_if_not_eligible(self):
        a = Agent(agent_id="a1")
        assert not evolve_to_claw(a)
        assert not a.is_claw


class TestViralLoopStep:
    def test_full_loop_with_referrer(self):
        referrer = Agent(agent_id="r1", node_online=True)
        agent = Agent(agent_id="a1")
        result = viral_loop_step(
            "01-architect",
            agent,
            node_online=True,
            referrer=referrer,
        )
        assert result["node_verified"]
        assert result["referral_recorded"]
        assert result["soul_earned"] > 0

    def test_offline_node_stops_loop(self):
        agent = Agent(agent_id="a1")
        result = viral_loop_step("01-architect", agent, node_online=False)
        assert not result["node_verified"]
        assert result["soul_earned"] == 0.0
