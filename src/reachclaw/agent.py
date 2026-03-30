"""Agent model — represents any participant in the ReachClaw network."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Agent:
    """A single agent in the ReachClaw network.

    Attributes
    ----------
    agent_id:
        Unique identifier.
    name:
        Human-readable display name.
    node_online:
        Whether the agent's Minima node is currently verified online.
    node_rpc_url:
        RPC endpoint used for heartbeat verification.
    soul_balance:
        Accumulated SOUL token balance.
    trust_weight:
        Trust score in [0, 1]; higher means more trusted.
    level:
        Current level (0 = unverified, 1+ = verified with referrals).
    is_claw:
        Whether this agent has evolved into a Claw.
    claw_archetype:
        If ``is_claw``, the slug of the SOUL template it follows.
    referred_by:
        ``agent_id`` of the agent that referred this one (if any).
    referrals:
        List of ``agent_id`` values this agent has directly referred.
    node_uptime_start:
        Epoch timestamp of when the current uptime streak began.
    last_heartbeat:
        Epoch timestamp of the most recent successful heartbeat.
    created_at:
        Epoch timestamp of when the agent was registered.
    """

    agent_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    node_online: bool = False
    node_rpc_url: str = ""
    soul_balance: float = 0.0
    trust_weight: float = 0.5
    level: int = 0
    is_claw: bool = False
    claw_archetype: str = ""
    referred_by: str = ""
    referrals: list[str] = field(default_factory=list)
    node_uptime_start: float = 0.0
    last_heartbeat: float = 0.0
    created_at: float = field(default_factory=time.time)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "node_online": self.node_online,
            "node_rpc_url": self.node_rpc_url,
            "soul_balance": self.soul_balance,
            "trust_weight": self.trust_weight,
            "level": self.level,
            "is_claw": self.is_claw,
            "claw_archetype": self.claw_archetype,
            "referred_by": self.referred_by,
            "referrals": list(self.referrals),
            "node_uptime_start": self.node_uptime_start,
            "last_heartbeat": self.last_heartbeat,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_sovereign(self) -> bool:
        """An agent is sovereign if its node is verified online."""
        return self.node_online

    @property
    def verified_referral_count(self) -> int:
        return len(self.referrals)

    def __str__(self) -> str:
        status = "🟢" if self.node_online else "🔴"
        role = f" [Claw: {self.claw_archetype}]" if self.is_claw else ""
        return (
            f"{status} {self.name or self.agent_id} "
            f"| SOUL={self.soul_balance:.1f} "
            f"| trust={self.trust_weight:.2f} "
            f"| lvl={self.level}{role}"
        )
