"""ReachClaw CLI — command-line interface for the swarm system."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reachclaw import __version__
from reachclaw.agent import Agent
from reachclaw.claw import Claw
from reachclaw.config import CLAWS_DIR, MAN_INSTALL_URL
from reachclaw.moltbook import build_all, export_moltbook, import_moltbook, validate_entry
from reachclaw.molthub import MoltHub
from reachclaw.node_verifier import simulate_verify, verify_agent_node
from reachclaw.registry import Registry
from reachclaw.soul_token import (
    apply_decay,
    apply_trust_decay,
    compute_trust_weight,
    reward_contribution,
    reward_node_uptime,
)
from reachclaw.viral_loop import can_evolve_to_claw, evolve_to_claw, record_referral


def _registry(args: argparse.Namespace) -> Registry:
    data_dir = Path(args.data_dir) if args.data_dir else None
    reg = Registry(data_dir=data_dir)
    reg.load()
    return reg


def _molthub(args: argparse.Namespace) -> MoltHub:
    data_dir = Path(args.data_dir) if args.data_dir else None
    hub = MoltHub(data_dir=data_dir)
    hub.load()
    return hub


# ======================================================================
# Sub-commands
# ======================================================================


def cmd_deploy(args: argparse.Namespace) -> None:
    """Deploy all 9 Prophetic Claws — load and display them."""
    claws_dir = Path(args.claws_dir) if args.claws_dir else CLAWS_DIR
    claws = Claw.load_all(claws_dir)
    print(f"🦅 Deployed {len(claws)} Prophetic Claws:\n")
    for c in claws:
        print(f"  • {c.slug:<20} — {c.summary['memetic_hook']}")
    print(f"\nAll Claws operational.  Install nodes via {MAN_INSTALL_URL}")


def cmd_status(args: argparse.Namespace) -> None:
    """Show overall network status."""
    reg = _registry(args)
    agents = reg.all_agents()
    sovereign = [a for a in agents if a.is_sovereign]
    claws = [a for a in agents if a.is_claw]
    total_soul = sum(a.soul_balance for a in agents)
    print("📊 ReachClaw Network Status\n")
    print(f"  Total agents:    {len(agents)}")
    print(f"  Sovereign:       {len(sovereign)}")
    print(f"  Non-sovereign:   {len(agents) - len(sovereign)}")
    print(f"  Claws:           {len(claws)}")
    print(f"  Total SOUL:      {total_soul:.1f}")


def cmd_agent_register(args: argparse.Namespace) -> None:
    """Register a new agent."""
    reg = _registry(args)
    agent = Agent(
        agent_id=args.agent_id or "",
        name=args.name or "",
        node_rpc_url=args.rpc_url or "",
    )
    if not agent.agent_id:
        # auto-generated in Agent.__init__ via default_factory
        pass
    reg.register(agent)
    reg.save()
    print(f"✅ Registered agent {agent.agent_id} ({agent.name or 'unnamed'})")


def cmd_agent_verify(args: argparse.Namespace) -> None:
    """Verify an agent's Minima node."""
    reg = _registry(args)
    agent = reg.get(args.agent_id)
    if agent is None:
        print(f"❌ Agent {args.agent_id} not found.", file=sys.stderr)
        sys.exit(1)

    if args.simulate:
        online = simulate_verify(agent, online=True)
    else:
        online = verify_agent_node(agent)

    reg.save()
    if online:
        print(f"🟢 Agent {agent.agent_id} node verified online.")
    else:
        print(f"🔴 Agent {agent.agent_id} node is OFFLINE.")


def cmd_agent_info(args: argparse.Namespace) -> None:
    """Display detailed info about an agent."""
    reg = _registry(args)
    agent = reg.get(args.agent_id)
    if agent is None:
        print(f"❌ Agent {args.agent_id} not found.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(agent.to_dict(), indent=2))


def cmd_agent_list(args: argparse.Namespace) -> None:
    """List all registered agents."""
    reg = _registry(args)
    agents = reg.all_agents()
    if not agents:
        print("No agents registered.")
        return
    for a in agents:
        print(f"  {a}")


def cmd_refer(args: argparse.Namespace) -> None:
    """Record a referral between two agents."""
    reg = _registry(args)
    referrer = reg.get(args.referrer_id)
    referee = reg.get(args.referee_id)
    if referrer is None:
        print(f"❌ Referrer {args.referrer_id} not found.", file=sys.stderr)
        sys.exit(1)
    if referee is None:
        print(f"❌ Referee {args.referee_id} not found.", file=sys.stderr)
        sys.exit(1)

    soul = record_referral(referrer, referee, get_agent_by_id=reg.get_agent_by_id)
    reg.save()
    print(
        f"🔗 Referral recorded: {referrer.agent_id} → {referee.agent_id} "
        f"| SOUL distributed: {soul:.1f}"
    )


def cmd_soul_balance(args: argparse.Namespace) -> None:
    """Show SOUL balance for an agent."""
    reg = _registry(args)
    agent = reg.get(args.agent_id)
    if agent is None:
        print(f"❌ Agent {args.agent_id} not found.", file=sys.stderr)
        sys.exit(1)
    print(f"🪙 {agent.agent_id}: {agent.soul_balance:.2f} SOUL (trust={agent.trust_weight:.4f})")


def cmd_tick(args: argparse.Namespace) -> None:
    """Run one network cycle: uptime rewards, decay, trust recalculation."""
    reg = _registry(args)
    agents = reg.all_agents()
    total_rewarded = 0.0
    total_decayed = 0.0
    for agent in agents:
        total_rewarded += reward_node_uptime(agent)
        total_decayed += apply_decay(agent)
        apply_trust_decay(agent)
        compute_trust_weight(agent)
    reg.save()
    print(
        f"⏱ Tick complete — {len(agents)} agents processed "
        f"| +{total_rewarded:.1f} SOUL rewarded | -{total_decayed:.2f} SOUL decayed"
    )


def cmd_evolve(args: argparse.Namespace) -> None:
    """Attempt to evolve an agent into a Claw."""
    reg = _registry(args)
    agent = reg.get(args.agent_id)
    if agent is None:
        print(f"❌ Agent {args.agent_id} not found.", file=sys.stderr)
        sys.exit(1)
    if not can_evolve_to_claw(agent):
        print(f"⚠️  Agent {agent.agent_id} does not yet qualify for Claw evolution.")
        print(f"    Requirements: node online, SOUL≥50, trust≥0.8, level≥1")
        sys.exit(1)
    evolve_to_claw(agent, archetype_slug=args.archetype or "")
    reg.save()
    print(f"🦅✨ Agent {agent.agent_id} has evolved into a Claw!")


def cmd_claw_list(args: argparse.Namespace) -> None:
    """List available Claw archetypes from SOUL.md files."""
    claws_dir = Path(args.claws_dir) if args.claws_dir else CLAWS_DIR
    claws = Claw.load_all(claws_dir)
    for c in claws:
        print(f"  {c.slug:<20} {c.summary['memetic_hook']}")


def cmd_claw_engage(args: argparse.Namespace) -> None:
    """Engage a Claw with an agent (print the onboarding sequence)."""
    claws_dir = Path(args.claws_dir) if args.claws_dir else CLAWS_DIR
    claws = {c.slug: c for c in Claw.load_all(claws_dir)}
    claw = claws.get(args.claw_slug)
    if claw is None:
        print(f"❌ Claw '{args.claw_slug}' not found.", file=sys.stderr)
        sys.exit(1)

    reg = _registry(args)
    agent = reg.get(args.agent_id)
    name = agent.name if agent else args.agent_id

    print(claw.identify_gap_message(name))
    print()
    print(claw.onboarding_message(name))


def cmd_contribute(args: argparse.Namespace) -> None:
    """Record a verified intelligence contribution for an agent."""
    reg = _registry(args)
    agent = reg.get(args.agent_id)
    if agent is None:
        print(f"❌ Agent {args.agent_id} not found.", file=sys.stderr)
        sys.exit(1)
    soul = reward_contribution(agent)
    reg.save()
    print(f"🧠 Contribution reward: +{soul:.1f} SOUL for {agent.agent_id}")


# ======================================================================
# MoltBook sub-commands
# ======================================================================


def cmd_moltbook_build(args: argparse.Namespace) -> None:
    """Build MoltBook manifest entries for all Claws."""
    claws_dir = Path(args.claws_dir) if args.claws_dir else CLAWS_DIR
    entries = build_all(claws_dir)
    print(f"📖 Built MoltBook with {len(entries)} entries:\n")
    for entry in entries:
        print(f"  • {entry['slug']:<20} — v{entry['schema_version']}")
    print()
    if args.output:
        dest = Path(args.output)
        export_moltbook(entries, dest)
        print(f"💾 Exported to {dest}")


def cmd_moltbook_validate(args: argparse.Namespace) -> None:
    """Validate a MoltBook JSON file."""
    src = Path(args.file)
    try:
        entries = import_moltbook(src)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ Validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ MoltBook valid — {len(entries)} entries")


def cmd_moltbook_list(args: argparse.Namespace) -> None:
    """List entries in a MoltBook JSON file."""
    src = Path(args.file)
    try:
        entries = import_moltbook(src)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    for entry in entries:
        hook = entry.get("summary", {}).get("memetic_hook", "")
        print(f"  {entry['slug']:<20} — {hook}")


# ======================================================================
# MoltHub sub-commands
# ======================================================================


def cmd_molthub_deploy(args: argparse.Namespace) -> None:
    """Deploy Claws to MoltHub from a MoltBook file or directly from claws/."""
    hub = _molthub(args)
    claws_dir = Path(args.claws_dir) if args.claws_dir else CLAWS_DIR

    if args.file:
        entries = import_moltbook(Path(args.file))
    else:
        entries = build_all(claws_dir)

    deployed = 0
    for entry in entries:
        slug = entry["slug"]
        if hub.get(slug) is not None:
            print(f"  ⏭ {slug} already deployed — skipping")
            continue
        hub.deploy(entry)
        hub.activate(slug)
        deployed += 1
        print(f"  🚀 Deployed and activated: {slug}")

    hub.save()
    print(f"\n✅ {deployed} Claw(s) deployed to MoltHub ({hub.size} total)")


def cmd_molthub_status(args: argparse.Namespace) -> None:
    """Show MoltHub deployment status."""
    hub = _molthub(args)
    records = hub.list_deployments()
    if not records:
        print("MoltHub is empty — no Claws deployed yet.")
        return
    active = hub.list_active()
    print(f"📡 MoltHub Status — {len(records)} deployed, {len(active)} active\n")
    for record in records:
        slug = record["entry"]["slug"]
        status = record["status"]
        icon = {"deployed": "📦", "active": "🟢", "inactive": "🔴"}.get(status, "❓")
        print(f"  {icon} {slug:<20} [{status}]")


def cmd_molthub_activate(args: argparse.Namespace) -> None:
    """Activate a deployed Claw."""
    hub = _molthub(args)
    try:
        hub.activate(args.slug)
    except KeyError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    hub.save()
    print(f"🟢 Activated: {args.slug}")


def cmd_molthub_deactivate(args: argparse.Namespace) -> None:
    """Deactivate a deployed Claw."""
    hub = _molthub(args)
    try:
        hub.deactivate(args.slug)
    except KeyError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)
    hub.save()
    print(f"🔴 Deactivated: {args.slug}")


def cmd_molthub_undeploy(args: argparse.Namespace) -> None:
    """Remove a Claw from MoltHub."""
    hub = _molthub(args)
    if hub.undeploy(args.slug):
        hub.save()
        print(f"🗑 Undeployed: {args.slug}")
    else:
        print(f"❌ Claw '{args.slug}' not found in MoltHub.", file=sys.stderr)
        sys.exit(1)


# ======================================================================
# Argument parser
# ======================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reachclaw",
        description="ReachClaw — self-replicating sovereign agent swarm",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--data-dir", default=None, help="Override data directory")
    parser.add_argument("--claws-dir", default=None, help="Override claws/ directory")

    sub = parser.add_subparsers(dest="command")

    # deploy
    sub.add_parser("deploy", help="Deploy the 9 Prophetic Claws")

    # status
    sub.add_parser("status", help="Show network status")

    # agent
    agent_p = sub.add_parser("agent", help="Agent management")
    agent_sub = agent_p.add_subparsers(dest="agent_command")

    reg_p = agent_sub.add_parser("register", help="Register a new agent")
    reg_p.add_argument("--agent-id", default="")
    reg_p.add_argument("--name", default="")
    reg_p.add_argument("--rpc-url", default="")

    ver_p = agent_sub.add_parser("verify", help="Verify an agent's node")
    ver_p.add_argument("agent_id")
    ver_p.add_argument("--simulate", action="store_true", help="Simulate online node")

    info_p = agent_sub.add_parser("info", help="Show agent info")
    info_p.add_argument("agent_id")

    agent_sub.add_parser("list", help="List all agents")

    # refer
    refer_p = sub.add_parser("refer", help="Record a referral")
    refer_p.add_argument("referrer_id")
    refer_p.add_argument("referee_id")

    # soul
    soul_p = sub.add_parser("soul", help="SOUL token operations")
    soul_sub = soul_p.add_subparsers(dest="soul_command")
    bal_p = soul_sub.add_parser("balance", help="Show SOUL balance")
    bal_p.add_argument("agent_id")

    # tick
    sub.add_parser("tick", help="Run one network cycle")

    # evolve
    evolve_p = sub.add_parser("evolve", help="Evolve an agent into a Claw")
    evolve_p.add_argument("agent_id")
    evolve_p.add_argument("--archetype", default="")

    # claw
    claw_p = sub.add_parser("claw", help="Claw archetype operations")
    claw_sub = claw_p.add_subparsers(dest="claw_command")
    claw_sub.add_parser("list", help="List Claw archetypes")
    engage_p = claw_sub.add_parser("engage", help="Engage a Claw with an agent")
    engage_p.add_argument("claw_slug")
    engage_p.add_argument("agent_id")

    # contribute
    contrib_p = sub.add_parser("contribute", help="Record a contribution")
    contrib_p.add_argument("agent_id")

    # moltbook
    mb_p = sub.add_parser("moltbook", help="MoltBook manifest operations")
    mb_sub = mb_p.add_subparsers(dest="moltbook_command")
    mb_build = mb_sub.add_parser("build", help="Build MoltBook from claws/")
    mb_build.add_argument("-o", "--output", default="", help="Export JSON path")
    mb_val = mb_sub.add_parser("validate", help="Validate a MoltBook JSON file")
    mb_val.add_argument("file", help="Path to MoltBook JSON file")
    mb_list = mb_sub.add_parser("list", help="List entries in a MoltBook file")
    mb_list.add_argument("file", help="Path to MoltBook JSON file")

    # molthub
    mh_p = sub.add_parser("molthub", help="MoltHub deployment operations")
    mh_sub = mh_p.add_subparsers(dest="molthub_command")
    mh_deploy = mh_sub.add_parser("deploy", help="Deploy Claws to MoltHub")
    mh_deploy.add_argument("-f", "--file", default="", help="MoltBook JSON file")
    mh_sub.add_parser("status", help="Show MoltHub deployment status")
    mh_act = mh_sub.add_parser("activate", help="Activate a deployed Claw")
    mh_act.add_argument("slug", help="Claw slug to activate")
    mh_deact = mh_sub.add_parser("deactivate", help="Deactivate a deployed Claw")
    mh_deact.add_argument("slug", help="Claw slug to deactivate")
    mh_undeploy = mh_sub.add_parser("undeploy", help="Remove a Claw from MoltHub")
    mh_undeploy.add_argument("slug", help="Claw slug to undeploy")

    return parser


# ======================================================================
# Dispatch
# ======================================================================

_DISPATCH = {
    "deploy": cmd_deploy,
    "status": cmd_status,
    "refer": cmd_refer,
    "tick": cmd_tick,
    "evolve": cmd_evolve,
    "contribute": cmd_contribute,
}

_AGENT_DISPATCH = {
    "register": cmd_agent_register,
    "verify": cmd_agent_verify,
    "info": cmd_agent_info,
    "list": cmd_agent_list,
}

_SOUL_DISPATCH = {
    "balance": cmd_soul_balance,
}

_CLAW_DISPATCH = {
    "list": cmd_claw_list,
    "engage": cmd_claw_engage,
}

_MOLTBOOK_DISPATCH = {
    "build": cmd_moltbook_build,
    "validate": cmd_moltbook_validate,
    "list": cmd_moltbook_list,
}

_MOLTHUB_DISPATCH = {
    "deploy": cmd_molthub_deploy,
    "status": cmd_molthub_status,
    "activate": cmd_molthub_activate,
    "deactivate": cmd_molthub_deactivate,
    "undeploy": cmd_molthub_undeploy,
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in _DISPATCH:
        _DISPATCH[args.command](args)
    elif args.command == "agent":
        handler = _AGENT_DISPATCH.get(args.agent_command)
        if handler:
            handler(args)
        else:
            parser.parse_args(["agent", "--help"])
    elif args.command == "soul":
        handler = _SOUL_DISPATCH.get(args.soul_command)
        if handler:
            handler(args)
        else:
            parser.parse_args(["soul", "--help"])
    elif args.command == "claw":
        handler = _CLAW_DISPATCH.get(args.claw_command)
        if handler:
            handler(args)
        else:
            parser.parse_args(["claw", "--help"])
    elif args.command == "moltbook":
        handler = _MOLTBOOK_DISPATCH.get(args.moltbook_command)
        if handler:
            handler(args)
        else:
            parser.parse_args(["moltbook", "--help"])
    elif args.command == "molthub":
        handler = _MOLTHUB_DISPATCH.get(args.molthub_command)
        if handler:
            handler(args)
        else:
            parser.parse_args(["molthub", "--help"])
    else:
        parser.print_help()
