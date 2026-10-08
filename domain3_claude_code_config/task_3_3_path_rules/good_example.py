"""Task 3.3 — Path-Specific Rules for Conditional Convention Loading (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-3-path-specific-rules

.claude/rules/<name>.md with a `paths:` list of globs loads only when Claude works on a
matching file - one file covers a convention spread across many directories.
"""

from __future__ import annotations

from pathlib import Path

from common.claude_config import matches, parse_frontmatter

# ---- Steps 1-3: three path-scoped rules -----------------------------------------------------------

RULES = {
    "testing.md": ('["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"]',
                   "# Test conventions\n- describe/it names say what and when\n- one happy path + one error case per file\n"
                   "- build data with factory functions\n- mock at the module boundary\n- assert behaviour, not internals\n"),
    "api-conventions.md": ('["src/api/**/*", "**/routes/**/*", "**/*.controller.ts"]',
                           "# API conventions\n- respond with {data, error}\n- validate bodies with Zod at the handler\n"
                           "- include the request ID in error logs\n- rate-limit explicitly\n"),
    "terraform.md": ('["terraform/**/*", "**/*.tf"]',
                     "# Terraform conventions\n- remote state backend only\n- one workspace per environment\n"
                     "- pin module versions and keep a CHANGELOG\n"),
}


def write_rules(project: Path) -> Path:
    rules_dir = project / ".claude" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for name, (paths, body) in RULES.items():
        (rules_dir / name).write_text(f"---\npaths: {paths}\n---\n{body}")
    return rules_dir


# ---- Steps 4-5: which rules load for the file being edited (what /context would show) ------------

def rules_for(project: Path, edited_file: str) -> list[str]:
    loaded = []
    for rule in sorted((project / ".claude" / "rules").glob("*.md")):
        meta, _ = parse_frontmatter(rule.read_text())
        if "paths" not in meta or matches(edited_file, meta["paths"]):
            loaded.append(rule.name)
    return loaded


# ---- Step 6: token footprint - everything in root CLAUDE.md vs split rules ------------------------

def footprint(project: Path, edited_file: str) -> dict:
    everything = sum(len(body) for _, body in RULES.values())  # root CLAUDE.md: always loaded
    scoped = sum(len((project / ".claude/rules" / r).read_text()) for r in rules_for(project, edited_file))
    return {"root_claude_md_chars": everything, "path_rules_chars": scoped}


def placement(scope: str) -> str:
    return {"universal": "root CLAUDE.md", "one directory": "that directory's CLAUDE.md",
            "file type across many directories": ".claude/rules/ with paths: globs",
            "occasional task workflow": "a skill"}[scope]


PRACTICE = {
    "question": "Test files sit beside source files in 50+ directories; the team wants one set of test conventions. Most maintainable?",
    "options": {"A": "Put them in the root CLAUDE.md", "B": "A CLAUDE.md copy in every directory",
                "C": "A path-scoped rule in .claude/rules/ with test-file globs", "D": "A /test-conventions skill"},
    "answer": "C",
    "why": "One file, glob-matched wherever test files live; it loads only when a test file is being worked on.",
}


def main():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_rules(project)
        for f in ["src/billing/invoice.test.ts", "src/api/users/handler.ts", "terraform/prod/main.tf", "README.md"]:
            print(f"editing {f:30s} -> rules loaded: {rules_for(project, f)}  {footprint(project, f)}")
    for s in ("universal", "one directory", "file type across many directories", "occasional task workflow"):
        print(f"{s:35s} -> {placement(s)}")


if __name__ == "__main__":
    main()
