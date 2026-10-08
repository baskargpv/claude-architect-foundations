"""Task 3.3 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-3-path-specific-rules

Trap 1  directory-level CLAUDE.md instead of path rules for a cross-directory convention
Trap 2  file-type conventions in the root CLAUDE.md
Trap 3  using a skill where a path rule is needed for automatic convention loading
"""

from __future__ import annotations

from domain3_claude_code_config.task_3_3_path_rules.good_example import RULES


def trap1_directory_copies(test_dirs: int = 50) -> dict:
    body = RULES["testing.md"][1]
    copies = {f"src/module_{i:02d}/CLAUDE.md": body for i in range(test_dirs)}
    copies["src/module_13/CLAUDE.md"] = body.replace("factory functions", "inline literals")  # one copy edited
    return {"files_to_maintain": len(copies), "versions_in_circulation": len(set(copies.values()))}


def trap2_everything_in_root(edited_file: str = "terraform/prod/main.tf") -> dict:
    root = "".join(body for _, body in RULES.values())  # loads every session, whatever you edit
    relevant = RULES["terraform.md"][1]
    return {"loaded_chars": len(root), "relevant_chars": len(relevant), "wasted_chars": len(root) - len(relevant)}


def trap3_skill_instead_of_rule(edited_file: str = "src/billing/invoice.test.ts", invoked: bool = False) -> dict:
    """A /test-conventions skill only applies if someone remembers to invoke it."""
    return {"conventions_applied_while_editing": invoked}


def main():
    print(f"trap 1 directory copies : {trap1_directory_copies()}")
    print(f"trap 2 root CLAUDE.md   : {trap2_everything_in_root()}")
    print(f"trap 3 skill not a rule : {trap3_skill_instead_of_rule()}")


if __name__ == "__main__":
    main()
