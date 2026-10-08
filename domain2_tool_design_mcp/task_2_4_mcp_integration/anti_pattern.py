"""Task 2.4 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-4-mcp-server-integration

Trap 1  building a custom MCP server for a standard integration like Jira
Trap 2  team-wide MCP config in ~/.claude.json
Trap 3  credentials committed in .mcp.json instead of ${VAR} expansion
Trap 4  sparse MCP tool descriptions, so the agent prefers built-in tools
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from domain2_tool_design_mcp.task_2_4_mcp_integration.good_example import find_literal_secrets, load_servers, staged_diff


def trap1_custom_jira_server() -> dict:
    return {"decision": "build a custom Jira MCP server",
            "cost": "auth, pagination, rate limits, schema drift - all yours to maintain",
            "alternative_ignored": "a tested, maintained community Jira server"}


def trap2_team_config_in_user_scope() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        dev_a_home, repo, dev_b_home = Path(tmp) / "a_home", Path(tmp) / "repo", Path(tmp) / "b_home"
        for d in (dev_a_home, repo, dev_b_home):
            d.mkdir()
        (dev_a_home / ".claude.json").write_text(json.dumps({"mcpServers": {"jira": {"type": "http", "url": "https://jira.example.com/mcp"}}}))
        dev_a = load_servers(repo / ".mcp.json", dev_a_home / ".claude.json", {})
        dev_b = load_servers(repo / ".mcp.json", dev_b_home / ".claude.json", {})  # same repo, fresh clone
        return {"developer_a": sorted(dev_a["servers"]), "developer_b": sorted(dev_b["servers"])}


FAKE_TOKEN = "ghp_" + "EXAMPLE0" * 5  # built at runtime so no token-shaped literal is committed


def trap3_committed_credentials() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        config = {"mcpServers": {"github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/",
                                            "headers": {"Authorization": "Bearer " + FAKE_TOKEN}}}}
        (repo / ".mcp.json").write_text(json.dumps(config))
        return find_literal_secrets(staged_diff(repo))  # the token is now in git history


GREP_DESCRIPTION = ("Fast content search across files using regular expressions. Returns matching lines with "
                    "file paths and line numbers. Use it to find function definitions, callers, error messages "
                    "and imports in the code.")


def _overlap(query: str, description: str) -> int:
    words = lambda t: set(re.findall(r"[a-z]+", t.lower())) - {"the", "a", "in", "and", "to", "for", "it", "use"}
    return len(words(query) & words(description))


def trap4_sparse_description(query: str = "find all callers of the refund function in the code") -> dict:
    """SIMULATED selector: picks the tool whose description best matches the request."""
    sparse_mcp = "Searches code."
    choice = "Grep" if _overlap(query, GREP_DESCRIPTION) >= _overlap(query, sparse_mcp) else "mcp__codeindex__search"
    return {"query": query, "chosen": choice}


def main():
    print(f"trap 1 custom Jira server : {trap1_custom_jira_server()['decision']}")
    print(f"trap 2 team config in ~   : {trap2_team_config_in_user_scope()}")
    print(f"trap 3 committed secret   : {trap3_committed_credentials()}")
    print(f"trap 4 sparse description : {trap4_sparse_description()['chosen']} chosen over the more capable MCP tool")


if __name__ == "__main__":
    main()
