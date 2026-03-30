"""Node verifier — check if a Minima node is running via its RPC endpoint."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

from reachclaw.agent import Agent
from reachclaw.config import DEFAULT_NODE_RPC_URL, HEARTBEAT_TIMEOUT


def heartbeat(rpc_url: str | None = None, *, timeout: int = HEARTBEAT_TIMEOUT) -> bool:
    """Return ``True`` if the Minima node at *rpc_url* responds to a health check.

    Uses a simple HTTP GET against the node's RPC endpoint.
    """
    url = rpc_url or DEFAULT_NODE_RPC_URL
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def verify_agent_node(agent: Agent) -> bool:
    """Perform a heartbeat check for *agent*'s node and update its status.

    Returns ``True`` if the node is confirmed online.
    """
    url = agent.node_rpc_url or DEFAULT_NODE_RPC_URL
    online = heartbeat(url)
    now = time.time()

    if online:
        if not agent.node_online:
            agent.node_uptime_start = now
        agent.node_online = True
        agent.last_heartbeat = now
    else:
        agent.node_online = False

    return online


def simulate_verify(agent: Agent, *, online: bool = True) -> bool:
    """Set node status directly — useful for testing / offline development.

    Returns the status that was set.
    """
    now = time.time()
    agent.node_online = online
    if online:
        if agent.node_uptime_start == 0.0:
            agent.node_uptime_start = now
        agent.last_heartbeat = now
    return online
