"""Tests for the SOUL token economics."""

from reachclaw.agent import Agent
from reachclaw.soul_token import (
    apply_decay,
    apply_trust_decay,
    compute_trust_weight,
    reward_contribution,
    reward_node_uptime,
    reward_referral,
)
from reachclaw.config import (
    CONTRIBUTION_REWARD,
    DECAY_RATE,
    NODE_UPTIME_REWARD,
    REFERRAL_REWARD,
)


class TestRewardNodeUptime:
    def test_online_agent_gets_reward(self, online_agent: Agent):
        before = online_agent.soul_balance
        got = reward_node_uptime(online_agent)
        assert got == NODE_UPTIME_REWARD
        assert online_agent.soul_balance == before + NODE_UPTIME_REWARD

    def test_offline_agent_gets_nothing(self, offline_agent: Agent):
        got = reward_node_uptime(offline_agent)
        assert got == 0.0
        assert offline_agent.soul_balance == 0.0


class TestRewardReferral:
    def test_direct_referral_full_reward(self):
        referrer = Agent(agent_id="r1", node_online=True, soul_balance=0)
        referee = Agent(agent_id="r2", node_online=True)
        total = reward_referral(referrer, referee, depth=0)
        assert total == REFERRAL_REWARD * 1.0

    def test_depth_1_half_reward(self):
        referrer = Agent(agent_id="r1", node_online=True, soul_balance=0)
        referee = Agent(agent_id="r2", node_online=True)
        total = reward_referral(referrer, referee, depth=1)
        assert total == REFERRAL_REWARD * 0.5

    def test_depth_3_no_reward(self):
        referrer = Agent(agent_id="r1", node_online=True, soul_balance=0)
        referee = Agent(agent_id="r2", node_online=True)
        total = reward_referral(referrer, referee, depth=3)
        assert total == 0.0

    def test_referee_offline_no_reward(self):
        referrer = Agent(agent_id="r1", node_online=True, soul_balance=0)
        referee = Agent(agent_id="r2", node_online=False)
        total = reward_referral(referrer, referee, depth=0)
        assert total == 0.0

    def test_upstream_chain(self):
        grandparent = Agent(agent_id="gp", node_online=True, soul_balance=0)
        parent = Agent(agent_id="p", node_online=True, soul_balance=0, referred_by="gp")
        child = Agent(agent_id="c", node_online=True)

        agents = {"gp": grandparent, "p": parent, "c": child}
        total = reward_referral(parent, child, depth=0, get_agent_by_id=agents.get)

        assert parent.soul_balance == REFERRAL_REWARD * 1.0
        assert grandparent.soul_balance == REFERRAL_REWARD * 0.5
        assert total == REFERRAL_REWARD * 1.0 + REFERRAL_REWARD * 0.5


class TestRewardContribution:
    def test_contribution_reward(self, online_agent: Agent):
        before = online_agent.soul_balance
        got = reward_contribution(online_agent)
        assert got == CONTRIBUTION_REWARD
        assert online_agent.soul_balance == before + CONTRIBUTION_REWARD


class TestDecay:
    def test_offline_agent_decays(self):
        a = Agent(agent_id="a1", node_online=False, soul_balance=100.0)
        loss = apply_decay(a)
        assert loss == 100.0 * DECAY_RATE
        assert a.soul_balance == 100.0 - loss

    def test_online_agent_no_decay(self):
        a = Agent(agent_id="a1", node_online=True, soul_balance=100.0)
        loss = apply_decay(a)
        assert loss == 0.0
        assert a.soul_balance == 100.0

    def test_zero_balance_no_negative(self):
        a = Agent(agent_id="a1", node_online=False, soul_balance=0.0)
        loss = apply_decay(a)
        assert loss == 0.0
        assert a.soul_balance == 0.0


class TestTrustDecay:
    def test_no_referrals_decays_trust(self):
        a = Agent(agent_id="a1", trust_weight=1.0)
        a.referrals = []
        lost = apply_trust_decay(a)
        assert lost > 0
        assert a.trust_weight < 1.0

    def test_has_referrals_no_decay(self):
        a = Agent(agent_id="a1", trust_weight=1.0)
        a.referrals = ["b1"]
        lost = apply_trust_decay(a)
        assert lost == 0.0
        assert a.trust_weight == 1.0


class TestComputeTrustWeight:
    def test_online_with_referrals(self):
        a = Agent(agent_id="a1", node_online=True, soul_balance=50.0)
        a.referrals = ["b1", "b2", "b3"]
        w = compute_trust_weight(a)
        assert 0.0 <= w <= 1.0
        assert a.trust_weight == w

    def test_offline_zero_soul(self):
        a = Agent(agent_id="a1", node_online=False, soul_balance=0.0)
        w = compute_trust_weight(a)
        assert w < 0.5
