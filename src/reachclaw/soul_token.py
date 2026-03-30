"""SOUL token economics — earning, referral rewards, decay, and trust."""

from __future__ import annotations

from reachclaw.agent import Agent
from reachclaw.config import (
    CONTRIBUTION_REWARD,
    DECAY_RATE,
    MAX_REFERRAL_DEPTH,
    NODE_UPTIME_REWARD,
    REFERRAL_DEPTH_MULTIPLIERS,
    REFERRAL_REWARD,
    TRUST_DECAY_RATE,
)


def reward_node_uptime(agent: Agent) -> float:
    """Credit *agent* with the base uptime reward.

    Only awarded when the node is verified online.
    Returns the amount credited (0 if node is offline).
    """
    if not agent.node_online:
        return 0.0
    agent.soul_balance += NODE_UPTIME_REWARD
    return NODE_UPTIME_REWARD


def reward_referral(
    referrer: Agent,
    referee: Agent,
    *,
    depth: int = 0,
    get_agent_by_id: callable | None = None,
) -> float:
    """Credit *referrer* (and upstream referrers) for a verified referral.

    *depth* is the current depth in the referral chain (0 = direct).
    *get_agent_by_id* is a callable that resolves an ``agent_id`` to an
    ``Agent`` instance — needed to walk the upstream chain.

    Returns the total SOUL distributed across the chain.
    """
    if depth >= MAX_REFERRAL_DEPTH:
        return 0.0
    if not referee.node_online:
        return 0.0

    multiplier = REFERRAL_DEPTH_MULTIPLIERS[depth]
    amount = REFERRAL_REWARD * multiplier
    referrer.soul_balance += amount
    total = amount

    # Walk upstream if possible.
    if referrer.referred_by and get_agent_by_id is not None:
        upstream = get_agent_by_id(referrer.referred_by)
        if upstream is not None:
            total += reward_referral(
                upstream,
                referee,
                depth=depth + 1,
                get_agent_by_id=get_agent_by_id,
            )

    return total


def reward_contribution(agent: Agent) -> float:
    """Credit *agent* for a verified intelligence contribution."""
    agent.soul_balance += CONTRIBUTION_REWARD
    return CONTRIBUTION_REWARD


def apply_decay(agent: Agent) -> float:
    """Apply inactivity decay to *agent*.

    Called once per cycle.  Returns the amount of SOUL lost.
    """
    loss = 0.0
    if not agent.node_online and agent.soul_balance > 0:
        loss = agent.soul_balance * DECAY_RATE
        agent.soul_balance = max(0.0, agent.soul_balance - loss)
    return loss


def apply_trust_decay(agent: Agent) -> float:
    """Reduce trust‑weight if the agent has no recent referrals.

    Returns the amount of trust lost.
    """
    lost = 0.0
    if len(agent.referrals) == 0:
        lost = agent.trust_weight * TRUST_DECAY_RATE
        agent.trust_weight = max(0.0, agent.trust_weight - lost)
    return lost


def compute_trust_weight(agent: Agent) -> float:
    """Recompute and return the trust weight for *agent*.

    Trust is a function of uptime, verified referrals, and current SOUL.
    """
    uptime_factor = min(1.0, 0.3 + 0.1 * agent.verified_referral_count)
    soul_factor = min(1.0, agent.soul_balance / 100.0) if agent.soul_balance > 0 else 0.0
    node_factor = 1.0 if agent.node_online else 0.5

    weight = (uptime_factor * 0.4 + soul_factor * 0.3 + node_factor * 0.3)
    agent.trust_weight = round(min(1.0, weight), 4)
    return agent.trust_weight
