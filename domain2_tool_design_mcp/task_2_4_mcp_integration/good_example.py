"""Task 2.4 — MCP Server Integration (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-4-mcp-server-integration

Project scope: .mcp.json at the repo root (shared via git). User scope: ~/.claude.json (personal).
Secrets stay out of git through ${VAR} expansion. Resources show what data exists; tools act on it.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from common.mcp_util import read_resource, resources, tool_defs

# ---- Step 1-2: project-scoped .mcp.json with ${VAR} expansion ---------------------------------

PROJECT_CONFIG = {"mcpServers": {
    "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/",
               "headers": {"Authorization": "Bearer ${GITHUB_TOKEN}"}},
    "warehouse": {"command": "npx", "args": ["-y", "@example/warehouse-mcp"],
                  "env": {"DATABASE_URL": "${DATABASE_URL:-postgresql://localhost/dev}"}},
}}

# ---- Step 3: a personal / experimental server in the user-scoped file ---------------------------

USER_CONFIG = {"mcpServers": {"my-scratchpad": {"command": "python", "args": ["~/tools/scratch_mcp.py"]}}}


def write_configs(project: Path, home: Path) -> tuple[Path, Path]:
    project.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    (project / ".mcp.json").write_text(json.dumps(PROJECT_CONFIG, indent=2))
    (home / ".claude.json").write_text(json.dumps(USER_CONFIG, indent=2))
    return project / ".mcp.json", home / ".claude.json"


def expand_env(value: str, env: dict, warnings: list) -> str:
    """${VAR} and ${VAR:-default}. An unset var with no default warns; loading carries on."""
    def sub(m):
        name, default = m.group(1), m.group(2)
        if name in env:
            return env[name]
        if default is not None:
            return default
        warnings.append(f"{name} is not set")
        return ""
    return re.sub(r"\$\{(\w+)(?::-([^}]*))?\}", sub, value)


def validate_entry(name: str, entry: dict) -> str | None:
    if "url" in entry and entry.get("type") != "http":
        return f"{name}: has a url but no \"type\": \"http\" - it would be read as stdio and skipped"
    if "url" not in entry and "command" not in entry:
        return f"{name}: needs either type+url (remote) or command+args (stdio)"
    return None


SECRET_PATTERNS = [r"gh[pousr]_[A-Za-z0-9]{20,}", r"sk-ant-[\w-]{10,}", r"Bearer (?!\$\{)[A-Za-z0-9._-]{20,}"]


def find_literal_secrets(text_: str) -> list[str]:
    return [m.group(0) for p in SECRET_PATTERNS for m in re.finditer(p, text_)]


def load_servers(project_config: Path, user_config: Path, env: dict) -> dict:
    """Every server from both scopes is discovered at connection time and available at once."""
    servers, warnings, errors = {}, [], []
    for path in (project_config, user_config):
        if path.exists():
            for name, entry in json.loads(path.read_text())["mcpServers"].items():
                if err := validate_entry(name, entry):
                    errors.append(err)
                    continue
                servers[name] = json.loads(expand_env(json.dumps(entry), env, warnings))
    return {"servers": servers, "warnings": warnings, "errors": errors}


def staged_diff(project: Path) -> str:
    """Step 2: what would actually be committed."""
    run = lambda *a: subprocess.run(["git", *a], cwd=project, capture_output=True, text=True, check=True).stdout
    run("init", "-q")
    run("add", ".mcp.json")
    return run("diff", "--cached")


# ---- Step 4: a catalogue exposed as an MCP resource ----------------------------------------------

def build_warehouse_server() -> MCPServer:
    srv = MCPServer("warehouse")

    @srv.resource("schema://warehouse/tables", name="warehouse_schema", mime_type="application/json",
                  description="Every table in the warehouse with its columns - read this before querying.")
    def schema() -> str:
        return json.dumps({"orders": ["id", "customer_id", "total_cents", "placed_at"],
                           "customers": ["id", "email", "region"]})

    # ---- Step 5: a 3-5 sentence description that holds its own against built-ins ----
    @srv.tool(description=(
        "Runs a read-only SQL query against the analytics warehouse and returns rows as JSON. "
        "Use it for questions about orders, customers and revenue that need aggregation or joins. "
        "Read the schema://warehouse/tables resource first so you know the table and column names. "
        "Prefer this over Grep or Read on exported CSV files: it queries live data and handles joins."))
    def query_warehouse(sql: str) -> dict:
        return {"rows": [], "sql": sql}

    return srv


def description_quality(description: str) -> dict:
    sentences = [s for s in re.split(r"(?<=\.)\s+", description.strip()) if s]
    return {"sentences": len(sentences), "ok": 3 <= len(sentences) <= 5,
            "compares_to_builtins": bool(re.search(r"\b(Grep|Read|Glob|built-in)\b", description))}


def choose_integration(system: str, team_specific_needs: bool = False) -> str:
    community = {"jira", "github", "slack", "linear", "notion"}
    if system.lower() in community and not team_specific_needs:
        return "evaluate the community MCP server first"
    return "build a custom MCP server"


PRACTICE = {
    "question": "A team wants Jira in its Claude Code workflow; a developer proposes building a custom MCP server. "
                "Correct first step?",
    "options": {"A": "Evaluate the community Jira MCP server first", "B": "Add Jira to ~/.claude.json",
                "C": "Call the Jira REST API from Bash", "D": "Build a custom server for the exact endpoints"},
    "answer": "A",
    "why": "Standard integrations have tested, maintained community servers; build custom only for team-specific needs.",
}


def main():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        project_cfg, user_cfg = write_configs(Path(tmp) / "repo", Path(tmp) / "home")
        diff = staged_diff(Path(tmp) / "repo")
        print(f"step 1-2 .mcp.json staged; literal secrets in diff: {find_literal_secrets(diff) or 'none'}; "
              f"references ${{GITHUB_TOKEN}}: {'${GITHUB_TOKEN}' in diff}")
        loaded = load_servers(project_cfg, user_cfg, env={"GITHUB_TOKEN": "ghp_local_only"})
        print(f"step 3 servers available at once: {sorted(loaded['servers'])}; warnings: {loaded['warnings']}")
    srv = build_warehouse_server()
    r = resources(srv)[0]
    print(f"step 4 resource: {r.name} {r.uri} {r.mime_type} -> {read_resource(srv, str(r.uri))}")
    print(f"step 5 description: {description_quality(tool_defs(srv)[0]['description'])}")
    print(f"Jira: {choose_integration('jira')}; in-house billing system: {choose_integration('ledgerline', True)}")


if __name__ == "__main__":
    main()
