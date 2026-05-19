"""
Claude Agents Registry — loader

Lightweight loader for `claude-agents.json`. Mirrors the API of the original
Python registry (`get_agent`, `list_agents`, `print_agent_summary`) and adds
search, validation, and a small CLI.

Usage as a library
------------------
    >>> from loader import get_agent, list_agents
    >>> agent = get_agent("deep_research")
    >>> print(agent["systemPrompt"])

Usage as a CLI
--------------
    $ python loader.py list
    $ python loader.py show deep_research
    $ python loader.py prompt deep_research          # prints only the system prompt
    $ python loader.py search "brazilian"
    $ python loader.py validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

REGISTRY_FILENAME = "claude-agents.json"
REGISTRY_PATH = Path(__file__).resolve().parent / REGISTRY_FILENAME

REQUIRED_FIELDS = {
    "name",
    "emoji",
    "description",
    "claudeTools",
    "capabilities",
    "examples",
    "systemPrompt",
}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_registry(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load the agent registry from disk.

    Parameters
    ----------
    path
        Optional path to a JSON file. Defaults to `claude-agents.json` next
        to this module.

    Returns
    -------
    dict
        Mapping of agent_id to agent metadata.

    Raises
    ------
    FileNotFoundError
        If the registry file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    target = Path(path) if path else REGISTRY_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"Registry not found at {target}. "
            f"Export `{REGISTRY_FILENAME}` from the Claude Agent Hub and "
            f"place it next to this loader."
        )
    with target.open(encoding="utf-8") as f:
        return json.load(f)


# Lazy module-level cache so repeated calls are cheap.
_REGISTRY: dict[str, dict[str, Any]] | None = None


def _registry() -> dict[str, dict[str, Any]]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = load_registry()
    return _REGISTRY


def reload() -> dict[str, dict[str, Any]]:
    """Force a re-read of the registry from disk and return it."""
    global _REGISTRY
    _REGISTRY = load_registry()
    return _REGISTRY


# --------------------------------------------------------------------------- #
# Public API (mirrors the original registry)
# --------------------------------------------------------------------------- #

def get_agent(agent_key: str) -> dict[str, Any]:
    """Return the full metadata dict for a single agent.

    Raises ``KeyError`` (with a helpful message) if the key is unknown.
    """
    agents = _registry()
    if agent_key not in agents:
        raise KeyError(
            f"Agent '{agent_key}' not found. "
            f"Available: {sorted(agents.keys())}"
        )
    return agents[agent_key]


def list_agents() -> list[str]:
    """Return all available agent keys in registration order."""
    return list(_registry().keys())


def get_prompt(agent_key: str) -> str:
    """Convenience accessor — return just the system prompt for an agent."""
    return get_agent(agent_key)["systemPrompt"]


def search(query: str) -> list[tuple[str, dict[str, Any]]]:
    """Case-insensitive substring search across name, description,
    capabilities, tools, and example prompts.

    Returns
    -------
    list of (agent_key, agent_dict) tuples for matching agents.
    """
    q = query.lower().strip()
    if not q:
        return list(_registry().items())

    results: list[tuple[str, dict[str, Any]]] = []
    for key, agent in _registry().items():
        haystack_parts: Iterable[str] = (
            agent.get("name", ""),
            agent.get("description", ""),
            *agent.get("capabilities", []),
            *agent.get("claudeTools", []),
            *agent.get("examples", []),
        )
        haystack = " ".join(haystack_parts).lower()
        if q in haystack:
            results.append((key, agent))
    return results


def print_agent_summary(agent_key: str) -> None:
    """Pretty-print a single agent's metadata to stdout."""
    a = get_agent(agent_key)
    print()
    print(f"{a['emoji']} {a['name']}  [{agent_key}]")
    print("-" * 60)
    print(f"Description : {a['description']}")
    print(f"Capabilities: {', '.join(a['capabilities'])}")
    print(f"Tools       : {', '.join(a['claudeTools'])}")
    print()
    print("Examples:")
    for example in a["examples"]:
        print(f"  - {example}")
    print()


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate(agents: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Validate the registry against the expected schema.

    Returns a list of human-readable error strings. An empty list means the
    registry is well-formed.
    """
    agents = agents if agents is not None else _registry()
    errors: list[str] = []

    if not isinstance(agents, dict):
        return ["Registry root must be a JSON object keyed by agent ID."]

    for key, agent in agents.items():
        prefix = f"[{key}]"

        if not isinstance(agent, dict):
            errors.append(f"{prefix} entry is not an object.")
            continue

        missing = REQUIRED_FIELDS - agent.keys()
        if missing:
            errors.append(f"{prefix} missing fields: {sorted(missing)}")

        for list_field in ("claudeTools", "capabilities", "examples"):
            value = agent.get(list_field)
            if value is not None and not (
                isinstance(value, list) and all(isinstance(v, str) for v in value)
            ):
                errors.append(f"{prefix} field '{list_field}' must be a list of strings.")

        for str_field in ("name", "emoji", "description", "systemPrompt"):
            value = agent.get(str_field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{prefix} field '{str_field}' must be a string.")

        prompt = agent.get("systemPrompt", "")
        if isinstance(prompt, str) and len(prompt.strip()) < 50:
            errors.append(
                f"{prefix} systemPrompt looks suspiciously short "
                f"({len(prompt)} chars) — double-check it was exported correctly."
            )

    return errors


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _cli() -> int:
    parser = argparse.ArgumentParser(
        prog="loader.py",
        description="Inspect and validate the Claude agents registry.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all agent keys.")

    show = sub.add_parser("show", help="Show full metadata for one agent.")
    show.add_argument("agent_key")

    prompt = sub.add_parser(
        "prompt",
        help="Print just the system prompt (useful for piping into pbcopy / xclip).",
    )
    prompt.add_argument("agent_key")

    search_cmd = sub.add_parser("search", help="Search across all agent metadata.")
    search_cmd.add_argument("query")

    sub.add_parser("validate", help="Validate the registry against the schema.")

    args = parser.parse_args()

    try:
        if args.command == "list":
            for key in list_agents():
                a = get_agent(key)
                print(f"{a['emoji']}  {key:<28} {a['name']}")
            return 0

        if args.command == "show":
            print_agent_summary(args.agent_key)
            return 0

        if args.command == "prompt":
            print(get_prompt(args.agent_key))
            return 0

        if args.command == "search":
            matches = search(args.query)
            if not matches:
                print(f"No agents match {args.query!r}.")
                return 1
            for key, a in matches:
                print(f"{a['emoji']}  {key:<28} {a['name']}")
            return 0

        if args.command == "validate":
            errors = validate()
            if errors:
                print(f"Registry has {len(errors)} issue(s):")
                for e in errors:
                    print(f"  - {e}")
                return 1
            print(f"Registry OK — {len(list_agents())} agents validated.")
            return 0

    except (KeyError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
