"""Task 2.5 — Built-in Tools (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-5-built-in-tools

Grep searches file CONTENTS. Glob matches file PATHS. Edit replaces one unique old_string.
Explore incrementally: Grep for entry points, Read only what that justifies, Grep again
for renamed wrappers. Small Python versions of the tools run against sample_codebase/.
"""

from __future__ import annotations

import fnmatch
import re
import shutil
from pathlib import Path

SAMPLE = Path(__file__).parent / "sample_codebase"


class EditError(Exception):
    pass


class Tools:
    """Grep / Glob / Read / Edit / Write over a workspace, counting characters pulled into context."""

    def __init__(self, root: Path):
        self.root, self.context_chars, self.log = root, 0, []

    def _files(self):
        return sorted(p for p in self.root.rglob("*") if p.is_file())

    def grep(self, pattern: str) -> list[tuple[str, int, str]]:
        self.log.append(f"Grep {pattern}")
        hits = [(str(p.relative_to(self.root)), i, line.strip()) for p in self._files()
                for i, line in enumerate(p.read_text().splitlines(), 1) if re.search(pattern, line)]
        self.context_chars += sum(len(h[2]) for h in hits)
        return hits

    def glob(self, pattern: str) -> list[str]:
        self.log.append(f"Glob {pattern}")
        return [str(p.relative_to(self.root)) for p in self._files() if fnmatch.fnmatch(str(p.relative_to(self.root)), pattern)]

    def read(self, path: str) -> str:
        self.log.append(f"Read {path}")
        content = (self.root / path).read_text()
        self.context_chars += len(content)
        return content

    def edit(self, path: str, old: str, new: str, replace_all: bool = False):
        content = (self.root / path).read_text()
        count = content.count(old)
        if count == 0:
            raise EditError(f"old_string not found in {path}")
        if count > 1 and not replace_all:
            raise EditError(f"old_string matches {count} places in {path} - not unique")
        (self.root / path).write_text(content.replace(old, new) if replace_all else content.replace(old, new, 1))
        self.context_chars += len(old) + len(new)
        self.log.append(f"Edit {path}{' (replace_all)' if replace_all else ''}")

    def write(self, path: str, content: str):
        (self.root / path).write_text(content)
        self.context_chars += len(content)
        self.log.append(f"Write {path}")


def workspace(target: Path, unrelated_modules: int = 40) -> Path:
    """Copy the sample, plus unrelated modules - a real repo is mostly code the task never touches."""
    shutil.copytree(SAMPLE, target)
    for n in range(unrelated_modules):
        (target / "src" / f"feature_{n:02d}.ts").write_text(
            f"export function feature{n}(input: string): string {{\n  // unrelated module {n}\n"
            f"  return input.trim().toUpperCase() + '-{n}';\n}}\n" * 3)
    return target


# ---- Steps 1-2: Grep for callers (then Grep again for wrapper names), Glob for their tests ------

def find_callers(t: Tools, name: str) -> dict:
    hits = t.grep(rf"\b{name}\(")
    direct = sorted({f for f, _, _ in hits if not f.startswith("tests/")})
    wrappers = {}
    for f, _, line in t.grep(rf"export \{{ {name} as (\w+) \}}"):  # a barrel file re-exporting under a new name
        alias = re.search(rf"{name} as (\w+)", line).group(1)
        wrappers[alias] = sorted({g for g, _, _ in t.grep(rf"\b{alias}\(")})
    return {"direct": direct, "via_wrapper": wrappers}


def find_tests(t: Tools, caller_files: list[str]) -> list[str]:
    stems = sorted({Path(f).stem for f in caller_files})
    return sorted({p for s in stems for p in t.glob(f"tests/{s}.test.*")})


# ---- Step 4-5: Edit each caller; recover from a non-unique match ---------------------------------

def edit_with_recovery(t: Tools, path: str, old: str, new: str, change_every_occurrence: bool) -> str:
    try:
        t.edit(path, old, new)
        return "edit"
    except EditError as e:
        if "not unique" not in str(e):
            raise
    if change_every_occurrence:  # every occurrence should change the same way
        t.edit(path, old, new, replace_all=True)
        return "replace_all"
    content = (t.root / path).read_text()  # change ONE: widen old_string with surrounding lines until unique
    lines = content.splitlines(keepends=True)
    i = next(n for n, line in enumerate(lines) if old in line)
    for extra in range(1, len(lines)):
        anchor = "".join(lines[max(0, i - extra): i + 1])
        if content.count(anchor) == 1:
            t.edit(path, anchor, anchor.replace(old, new))
            return "widened"
    t.write(path, content.replace(old, new, 1))  # Read + Write: last resort
    return "read+write"


def migrate(root: Path, old_name: str = "processLegacyOrder", new_name: str = "processOrder") -> dict:
    t = Tools(root)
    callers = find_callers(t, old_name)  # Step 1
    all_callers = callers["direct"] + [f for fs in callers["via_wrapper"].values() for f in fs]
    tests = find_tests(t, all_callers)  # Step 2
    for f in all_callers:  # Step 3: read only the files the searches justified
        t.read(f)
    how = {}
    for f in callers["direct"]:  # Step 4: replace the deprecated call
        if f.endswith("OrderProcessor.ts"):
            continue  # the definition itself is handled separately
        how[f] = edit_with_recovery(t, f, f"{old_name}(", f"{new_name}(", change_every_occurrence=True)
    return {**callers, "tests": tests, "edits": how, "context_chars": t.context_chars, "log": t.log}


PRACTICE = {
    "question": "Which sequence finds all callers of deprecated processLegacyOrder() and their test files?",
    "options": {"A": "Bash find | xargs grep", "B": "Glob, then Grep",
                "C": "Grep for callers, then Glob for sibling tests", "D": "Read every file manually"},
    "answer": "C",
    "why": "Callers are a content search (Grep); sibling tests are a path pattern (Glob). Never Glob first, never read everything.",
}


def main():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        r = migrate(workspace(Path(tmp) / "ws"))
        print(f"step 1 direct callers : {r['direct']}")
        print(f"       via wrapper    : {r['via_wrapper']}")
        print(f"step 2 tests (Glob)   : {r['tests']}")
        print(f"step 4-5 edits        : {r['edits']}")
        print(f"context used          : {r['context_chars']} chars")
        t = Tools(Path(tmp) / "ws")
        print(f"one-occurrence change : {edit_with_recovery(t, 'src/checkout.ts', 'processOrder(', 'processOrderV2(', False)}")


if __name__ == "__main__":
    main()
