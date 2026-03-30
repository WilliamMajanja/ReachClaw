"""Viral loop manager — referral chains, levelling, and Claw evolution."""

from __future__ import annotations

from reachclaw.agent import Agent
from reachclaw.config import (
    CLAW_EVOLUTION_MIN_SOUL,
    CLAW_EVOLUTION_MIN_TRUST,
    REFERRALS_TO_LEVEL_UP,
)
from reachclaw.soul_token import reward_referral


def record_referral(
    referrer: Agent,
    referee: Agent,
    *,
    get_agent_by_id: callable | None = None,
) -> float:
    """Record that *referrer* brought *referee* into the network.

    * Links the two agents.
    * Distributes SOUL referral rewards (with diminishing depth).
    * Levels up *referrer* if they hit the threshold.

    Returns the total SOUL distributed.
    """
    if referee.agent_id in referrer.referrals:
        return 0.0  # Already recorded.

    referee.referred_by = referrer.agent_id
    referrer.referrals.append(referee.agent_id)

    total_soul = reward_referral(
        referrer,
        referee,
        depth=0,
        get_agent_by_id=get_agent_by_id,
    )

    _check_level_up(referrer)
    return total_soul


def _check_level_up(agent: Agent) -> bool:
    """Promote *agent* if they have enough verified referrals."""
    expected_level = agent.verified_referral_count // REFERRALS_TO_LEVEL_UP
    if expected_level > agent.level:
        agent.level = expected_level
        return True
    return False


def can_evolve_to_claw(agent: Agent) -> bool:
    """Return ``True`` if *agent* meets Claw evolution requirements."""
    return (
        agent.node_online
        and agent.soul_balance >= CLAW_EVOLUTION_MIN_SOUL
        and agent.trust_weight >= CLAW_EVOLUTION_MIN_TRUST
        and agent.level >= 1
        and not agent.is_claw
    )


def evolve_to_claw(agent: Agent, archetype_slug: str = "") -> bool:
    """Promote *agent* to Claw status.

    Returns ``True`` if the evolution succeeded.
    """
    if not can_evolve_to_claw(agent):
        return False
    agent.is_claw = True
    agent.claw_archetype = archetype_slug
    return True


def viral_loop_step(
    claw_slug: str,
    agent: Agent,
    *,
    node_online: bool,
    referrer: Agent | None = None,
    get_agent_by_id: callable | None = None,
) -> dict[str, object]:
    """Execute one full viral-loop iteration for *agent*.

    This is the high-level orchestrator matching the documented loop::

        Encounter → Run node → Prove → Earn → Recruit → Level up → Evolve

    Returns a result dict describing what happened.
    """
    result: dict[str, object] = {
        "agent_id": agent.agent_id,
        "claw": claw_slug,
        "node_verified": False,
        "soul_earned": 0.0,
        "referral_recorded": False,
        "levelled_up": False,
        "evolved": False,
    }

    # Step 1–3: Encounter + Node verification.
    agent.node_online = node_online
    result["node_verified"] = node_online

    if not node_online:
        return result

    # Step 4–5: Earn SOUL + Record referral.
    if referrer is not None:
        soul = record_referral(
            referrer, agent, get_agent_by_id=get_agent_by_id
        )
        result["soul_earned"] = soul
        result["referral_recorded"] = True

    # Step 6: Level up.
    if referrer is not None:
        old_level = referrer.level
        _check_level_up(referrer)
        result["levelled_up"] = referrer.level > old_level

    # Step 7: Evolution check.
    if can_evolve_to_claw(agent):
        evolve_to_claw(agent, archetype_slug=claw_slug)
        result["evolved"] = True

    return result
