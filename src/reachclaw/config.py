"""Global configuration constants for ReachClaw."""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Root of the ReachClaw repository (two levels up from this file).
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

CLAWS_DIR: Path = REPO_ROOT / "claws"

# Where persistent JSON data is stored at runtime.
DATA_DIR: Path = Path(os.environ.get("REACHCLAW_DATA_DIR", REPO_ROOT / ".reachclaw"))

# ---------------------------------------------------------------------------
# SOUL token economics
# ---------------------------------------------------------------------------

# Base SOUL reward per heartbeat cycle when a node is online.
NODE_UPTIME_REWARD: float = 1.0

# Reward given to the *referrer* when a direct referee proves node operation.
REFERRAL_REWARD: float = 5.0

# Diminishing referral‑depth multipliers (index 0 = direct referral).
REFERRAL_DEPTH_MULTIPLIERS: list[float] = [1.0, 0.5, 0.25]

# Reward for a verified intelligence contribution.
CONTRIBUTION_REWARD: float = 3.0

# ---------------------------------------------------------------------------
# Decay
# ---------------------------------------------------------------------------

# Fraction of SOUL that decays per cycle when a node is offline.
DECAY_RATE: float = 0.05

# Fraction of trust‑weight reduction per cycle without new referrals.
TRUST_DECAY_RATE: float = 0.02

# ---------------------------------------------------------------------------
# Viral‑loop
# ---------------------------------------------------------------------------

# Number of verified referrals required to level up.
REFERRALS_TO_LEVEL_UP: int = 3

# Maximum referral depth that earns rewards.
MAX_REFERRAL_DEPTH: int = len(REFERRAL_DEPTH_MULTIPLIERS)

# Minimum SOUL balance to be eligible for Claw evolution.
CLAW_EVOLUTION_MIN_SOUL: float = 50.0

# Minimum trust‑weight to be eligible for Claw evolution.
CLAW_EVOLUTION_MIN_TRUST: float = 0.8

# ---------------------------------------------------------------------------
# Node verification
# ---------------------------------------------------------------------------

# Default Minima node RPC endpoint (local).
DEFAULT_NODE_RPC_URL: str = "http://127.0.0.1:9005"

# Heartbeat timeout in seconds.
HEARTBEAT_TIMEOUT: int = 5

# M.A.N install URL.
MAN_INSTALL_URL: str = "https://github.com/Gheek-Labs/M.A.N"
