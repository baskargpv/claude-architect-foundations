"""Task 3.1 — CLAUDE.md Hierarchy, Scoping, and Modular Organisation (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-1-claude-md-hierarchy

Builds a real project tree and models how Claude Code assembles memory from it:
user -> project -> directory files are CONCATENATED (no precedence), CLAUDE.local.md loads
after CLAUDE.md, @imports inline eagerly, path-scoped rules load only for matching files.
"""

from __future__ import annotations

import re
from pathlib import Path

from common.claude_config import matches, parse_frontmatter

# ---- Steps 1-4: write the configuration -------------------------------------------------------

PROJECT_FILES = {
    ".claude/CLAUDE.md": "# Team standards\n\n## Naming\nUse camelCase for functions.\n@../standards/naming.md\n\n"
                         "## Error handling\nNever swallow exceptions; wrap with context.\n\n"
                         "## Code review\nEvery PR needs a test.\n",
    "standards/naming.md": "## Naming details\nREST resources are plural nouns: /users, /orders.\n",
    "packages/api/CLAUDE.md": "# API package\nEndpoints return {data, error}. Validate request bodies with Zod.\n",
    ".claude/rules/testing.md": "---\npaths: [\"**/*.test.ts\"]\n---\n# Testing\nName tests 'does X when Y'. One assertion focus per test.\n",
    ".claude/rules/security.md": "# Security\nNever log tokens.\n",  # no paths: loads every session
}


def build_project(root: Path, files: dict[str, str] = PROJECT_FILES) -> Path:
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content)
    return root


# ---- Step 5: what loads (the model behind /context) ----------------------------------------------

def expand_imports(path: Path, seen: set | None = None) -> str:
    """@path lines are inlined when the file is read; paths resolve relative to THIS file."""
    seen = seen or set()
    out = []
    for line in path.read_text().splitlines():
        m = re.fullmatch(r"@(\S+)", line.strip())
        target = (path.parent / m.group(1)).resolve() if m else None
        if target and target.exists() and target not in seen:
            seen.add(target)
            out.append(expand_imports(target, seen))
        else:
            out.append(line)
    return "\n".join(out)


def loaded_memory(project: Path, home: Path, cwd: Path | None = None, touched: list[str] = ()) -> list[tuple[str, str]]:
    """Ordered (file, reason) list - broadest to most specific. Order is NOT precedence."""
    cwd = cwd or project
    loaded = []

    def add(p: Path, reason: str):
        if p.exists():
            loaded.append((str(p), reason))

    add(home / ".claude" / "CLAUDE.md", "user")
    add(project / "CLAUDE.md", "project")
    add(project / ".claude" / "CLAUDE.md", "project")
    add(project / "CLAUDE.local.md", "project (local, loads after CLAUDE.md)")
    rel = cwd.relative_to(project)
    for i in range(1, len(rel.parts) + 1):  # walk down from the root to the launch directory
        d = project.joinpath(*rel.parts[:i])
        add(d / "CLAUDE.md", "directory (launch path)")
        add(d / "CLAUDE.local.md", "directory local")
    for f in touched:  # subdirectory files load on demand when Claude reads a file there
        d = (project / f).parent
        if d != project and not any(str(d / "CLAUDE.md") == x for x, _ in loaded):
            add(d / "CLAUDE.md", f"directory (on demand: read {f})")
    for rule in sorted((project / ".claude" / "rules").glob("*.md")):
        meta, _ = parse_frontmatter(rule.read_text())
        if "paths" not in meta:
            add(rule, "rule (no paths: every session)")
        elif any(matches(f, meta["paths"]) for f in touched):
            add(rule, "rule (paths matched)")
    return loaded


def context_text(loaded: list[tuple[str, str]]) -> str:
    """Everything is concatenated into one context - a later file does not override an earlier one."""
    return "\n\n".join(expand_imports(Path(p)) for p, _ in loaded)


def memory_command(project: Path, home: Path) -> list[str]:
    """/memory lists memory locations. It's diagnostic: nothing gets loaded by running it."""
    return [str(home / ".claude" / "CLAUDE.md"), str(project / ".claude" / "CLAUDE.md"), str(project / "CLAUDE.local.md")]


def in_repo(project: Path, path: Path) -> bool:
    return project in path.resolve().parents


PRACTICE = {
    "question": "Developer A's Claude Code follows the team's API naming; new Developer B on the same repo and branch "
                "gets inconsistent naming. Most likely root cause?",
    "options": {"A": "B lacks an MCP server supplying the rules", "B": "The rules are in a .claude/rules/ file B's setup ignores",
                "C": "The conventions are in A's user-level ~/.claude/CLAUDE.md, not project config",
                "D": "B hasn't run /memory to load the config"},
    "answer": "C",
    "why": "User-level files never reach git, so a fresh clone can't have them; /memory loads nothing.",
}


def main():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        project, home = build_project(Path(tmp) / "repo"), Path(tmp) / "home"
        for label, cwd, touched in [("root", project, []), ("packages/api", project / "packages/api", ["packages/api/users.test.ts"])]:
            print(f"step 5 loaded at {label}:")
            for p, reason in loaded_memory(project, home, cwd, touched):
                print(f"    {Path(p).relative_to(tmp)}  [{reason}]")
        print(f"@import inlined eagerly: {'plural nouns' in context_text(loaded_memory(project, home))}")
        user_md = home / ".claude" / "CLAUDE.md"  # step 6
        user_md.parent.mkdir(parents=True)
        user_md.write_text("Prefer early returns.\n")
        print(f"step 6 ~/.claude/CLAUDE.md inside the repo (shared via git)? {in_repo(project, user_md)}")


if __name__ == "__main__":
    main()
