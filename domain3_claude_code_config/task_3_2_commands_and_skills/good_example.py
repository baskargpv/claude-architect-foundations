"""Task 3.2 — Custom Slash Commands and Skills (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-2-slash-commands-skills

CLAUDE.md loads every session; a skill's body enters context only when it runs. Two file shapes
create /name: .claude/commands/<name>.md (flat) or .claude/skills/<name>/SKILL.md (folder).
Repo paths are team-shared; ~/.claude/ paths are personal.
"""

from __future__ import annotations

from pathlib import Path

from common import config
from common.claude_config import parse_frontmatter
from common.client import get_client, mode_banner, response_text
from common.mock import message, text

# ---- Steps 1-4: a team command and a personal skill --------------------------------------------

REVIEW_COMMAND = """---
description: Run the team code review checklist on the current diff
---
Review the diff against our checklist:
1. Tests cover the change. 2. No secrets or debug prints. 3. Errors are handled, not swallowed.
"""

BRAINSTORM_SKILL = """---
description: Brainstorm many alternative designs for a problem and return the best three
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
argument-hint: "<problem to brainstorm>"
---
Generate at least ten distinct approaches to the problem, reason about each in detail,
then finish with a line starting 'SUMMARY:' naming the best three.
"""


def write_files(project: Path, home: Path):
    (project / ".claude/commands").mkdir(parents=True, exist_ok=True)
    (project / ".claude/commands/review.md").write_text(REVIEW_COMMAND)  # Step 1: team, shared via git
    (home / ".claude/skills/brainstorm").mkdir(parents=True, exist_ok=True)
    (home / ".claude/skills/brainstorm/SKILL.md").write_text(BRAINSTORM_SKILL)  # Steps 2-4: personal


# ---- Step 5: which /commands exist for a given checkout + home directory -------------------------

def discover_commands(project: Path, home: Path) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for scope, base in (("user", home / ".claude"), ("project", project / ".claude")):
        for f in sorted((base / "commands").glob("*.md")):
            found.setdefault(f.stem, {"scope": scope, "shape": "command", "path": f})
        for f in sorted((base / "skills").glob("*/SKILL.md")):  # only folder + SKILL.md counts
            found[f.parent.name] = {"scope": scope, "shape": "skill", "path": f}  # skills win a name clash
    for entry in found.values():
        meta, body = parse_frontmatter(entry["path"].read_text())
        entry["meta"] = meta
        entry["description"] = meta.get("description") or body.strip().split("\n\n")[0]  # fallback: first paragraph
    return found


def tool_permissions(meta: dict, all_tools=("Read", "Grep", "Glob", "Edit", "Write", "Bash")) -> dict:
    """Exam answer: allowed-tools RESTRICTS the skill. Current docs: it PRE-APPROVES those tools
    (no permission prompt); everything else stays callable unless listed in disallowed-tools."""
    allowed = meta.get("allowed-tools", [])
    callable_now = [t for t in all_tools if t not in meta.get("disallowed-tools", [])]
    return {"exam_answer_restricted_to": allowed, "current_pre_approved": allowed, "current_still_callable": callable_now}


# ---- Step 6: invoking a context: fork skill keeps its verbose output out of the main conversation ----

def run_skill(client, skill: dict, arguments: str, main_history: list) -> list:
    _, body = parse_frontmatter(skill["path"].read_text())
    messages = [{"role": "user", "content": f"{body}\n\nProblem: {arguments}"}]
    output = response_text(client.messages.create(model=config.model(), max_tokens=4096, messages=messages))
    if skill["meta"].get("context") == "fork":  # isolated sub-agent: only a condensed result comes back
        summary = next((line for line in output.splitlines() if line.startswith("SUMMARY:")), output[:200])
        return main_history + [{"role": "assistant", "content": summary}]
    return main_history + [{"role": "assistant", "content": output}]


PRACTICE = {
    "question": "Where should a team-shared /review command and a personal, verbose /brainstorm skill go, and what does the skill need?",
    "options": {"A": "Both in ~/.claude/commands/", "B": "Both in .claude/commands/ with context: fork",
                "C": "/review in .claude/commands/; /brainstorm at ~/.claude/skills/brainstorm/SKILL.md with context: fork",
                "D": "/review in CLAUDE.md; /brainstorm in .claude/skills/ with only allowed-tools"},
    "answer": "C",
    "why": "Team commands go in the repo, personal ones under ~/.claude/, and context: fork keeps verbose output out of the main thread.",
}


def mock_model(kwargs: dict):
    ideas = "\n".join(f"Approach {i}: detailed reasoning about option {i} ... (long)" for i in range(1, 11))
    return message(text(f"{ideas}\nSUMMARY: best three are approaches 2, 5 and 9."))


def main():
    import tempfile

    print(mode_banner())
    with tempfile.TemporaryDirectory() as tmp:
        repo, me, teammate = Path(tmp) / "repo", Path(tmp) / "me", Path(tmp) / "teammate"
        write_files(repo, me)
        mine, theirs = discover_commands(repo, me), discover_commands(repo, teammate)
        print(f"step 5 my commands      : {sorted(mine)}")
        print(f"       teammate commands: {sorted(theirs)}")
        print(f"allowed-tools: {tool_permissions(mine['brainstorm']['meta'])}")
        history = run_skill(get_client(mock_model), mine["brainstorm"], "cache invalidation strategy", [])
        print(f"step 6 main conversation received: {history[-1]['content']!r}")


if __name__ == "__main__":
    main()
