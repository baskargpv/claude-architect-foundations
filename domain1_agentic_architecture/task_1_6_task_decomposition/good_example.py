"""Task 1.6 — Build a Multi-Pass Code Review Pipeline (lesson Build Exercise, steps 1-6),
plus the lesson's dynamic-decomposition example (legacy codebase test planning).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-6-task-decomposition

Code review's plan is knowable before any file is opened -> FIXED pipeline:
per-file local passes (full attention each) + ONE cross-file integration pass.
Legacy exploration's scope is unknown -> DYNAMIC decomposition that re-plans on discoveries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

SAMPLE_REPO = Path(__file__).parent / "sample_repo"

# ---- Step 1: read a directory of >= 10 source files -----------------------------------------

def load_repo(directory: Path = SAMPLE_REPO) -> dict[str, str]:
    files = {p.name: p.read_text() for p in sorted(directory.glob("*.js"))}
    if len(files) < 10:
        raise ValueError("the exercise needs at least 10 files - that's where dilution shows")
    return files


ISSUE = {"type": "object", "additionalProperties": False, "required": ["file", "line", "severity", "kind", "description"],
         "properties": {"file": {"type": "string"}, "line": {"type": "integer"},
                        "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
                        "kind": {"type": "string"}, "description": {"type": "string"}}}
FILE_REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["file", "bug_count", "issues", "exports", "uses", "query_style"],
    "properties": {
        "file": {"type": "string"}, "bug_count": {"type": "integer"}, "issues": {"type": "array", "items": ISSUE},
        "exports": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["function", "returns"],
                                               "properties": {"function": {"type": "string"}, "returns": {"type": "array", "items": {"type": "string"}}}}},
        "uses": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["function", "from_file", "properties"],
                                            "properties": {"function": {"type": "string"}, "from_file": {"type": "string"},
                                                           "properties": {"type": "array", "items": {"type": "string"}}}}},
        "query_style": {"anyOf": [{"type": "string", "enum": ["parameterized", "concatenated"]}, {"type": "null"}]},
    },
}
ISSUES_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["issues"],
                 "properties": {"issues": {"type": "array", "items": ISSUE}}}
CROSS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["cross_file_issues"],
                "properties": {"cross_file_issues": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False, "required": ["files", "kind", "description"],
                    "properties": {"files": {"type": "array", "items": {"type": "string"}}, "kind": {"type": "string"},
                                   "description": {"type": "string"}}}}}}

# ---- Step 3: per-file analysis passes -------------------------------------------------------

def local_review(client, name: str, source: str) -> dict:
    prompt = (f"[LOCAL REVIEW]\nReview this ONE file for bugs, security issues and inefficiencies. Report each issue "
              f"with line and severity, plus the file's exported functions (and returned keys), what it uses from "
              f"other files (and which properties it reads), and its SQL query style.\n--- {name} ---\n{source}")
    return ask_json(client, prompt, FILE_REVIEW_SCHEMA)


# ---- Step 4: one cross-file integration pass over the per-file summaries --------------------

def integration_review(client, summaries: list[dict]) -> list[dict]:
    prompt = ("[INTEGRATION REVIEW]\nPer-file issues are already reported - don't repeat them. Using these per-file "
              "summaries, look ONLY for cross-file problems: API contracts between producer and consumer, data flow "
              "between modules, and patterns applied differently across files.\n"
              f"{json.dumps([{k: s[k] for k in ('file', 'exports', 'uses', 'query_style')} for s in summaries])}")
    return ask_json(client, prompt, CROSS_SCHEMA)["cross_file_issues"]


def multi_pass_review(client, files: dict[str, str]) -> dict:
    summaries = [local_review(client, n, s) for n, s in files.items()]  # the plan is fixed up front
    return {"per_file": summaries, "issues": [i for s in summaries for i in s["issues"]],
            "cross_file": integration_review(client, summaries)}


# ---- Step 2: single-pass baseline -------------------------------------------------------------

def single_pass_review(client, files: dict[str, str], instructions: str = "Review all of these files.") -> dict:
    sources = "\n".join(f"--- {n} ---\n{s}" for n, s in files.items())
    issues = ask_json(client, f"[SINGLE PASS]\n{instructions}\n{sources}", ISSUES_SCHEMA)["issues"]
    return {"issues": issues, "cross_file": []}


# ---- Steps 5-6: compare, and record dilution artefacts --------------------------------------

def compare(single: dict, multi: dict, files: dict[str, str]) -> dict:
    def per_file(issues):
        return {n: sum(1 for i in issues if i["file"] == n) for n in files}
    s, m = per_file(single["issues"]), per_file(multi["issues"])
    buggy = [n for n, c in m.items() if c]
    return {"single_total": len(single["issues"]), "multi_total": len(multi["issues"]),
            "single_missed_files": [n for n in buggy if not s[n]],
            "multi_missed_files": [n for n in buggy if not m[n]],
            "cross_file_found_by": "integration pass" if multi["cross_file"] and not single["cross_file"] else "both/none"}


def dilution_artefacts(review: dict, files: dict[str, str]) -> list[dict]:
    """Identical code flagged in one file but approved in another."""
    flagged = {(i["file"], i["kind"]) for i in review["issues"]}
    artefacts = []
    for kind, pattern in RULES.items():
        holders = [n for n, src in files.items() if re.search(pattern[0], src)]
        hit = [n for n in holders if (n, kind) in flagged]
        miss = [n for n in holders if (n, kind) not in flagged]
        if hit and miss:
            artefacts.append({"kind": kind, "flagged_in": hit, "approved_in": miss})
    return artefacts


# ---- choosing the pattern by task characteristics ------------------------------------------

def choose_pattern(steps_known_upfront: bool) -> str:
    return "fixed_pipeline" if steps_known_upfront else "dynamic_decomposition"


# ---- the lesson's dynamic example: legacy test planning that re-plans on discovery ------------

def import_graph(files: dict[str, str]) -> dict[str, list[str]]:
    return {n: re.findall(r"from '\./([\w.]+)'", src) for n, src in files.items()}


def adaptive_test_plan(files: dict[str, str], has_tests: set[str] = frozenset()) -> dict:
    graph = import_graph(files)
    importers = {n: sum(n in deps for deps in graph.values()) for n in files}
    plan = sorted((n for n in files if graph[n]), key=lambda n: -len(graph[n]))  # Steps 1-3: map, prioritise, plan
    tested, log = set(has_tests), []
    while plan:
        target = plan.pop(0)
        if target in tested:
            continue
        untested_deps = [d for d in graph[target] if d not in tested]
        if untested_deps:  # Step 4-5: discovery -> reprioritise the dependency first
            log.append(f"discovered {target} depends on untested {untested_deps}; testing those first")
            plan = untested_deps + [target] + [p for p in plan if p not in untested_deps]
            continue
        tested.add(target)
        log.append(f"wrote tests for {target}")
    return {"order": [entry.split()[-1] for entry in log if entry.startswith("wrote")], "log": log, "importers": importers}


PRACTICE = {
    "question": "A 14-file review is detailed for files 1-5, misses obvious bugs in 10-14, and flags a forEach in one "
                "file while approving identical code in another. Root cause and fix?",
    "options": {"A": "Batches of 5 files, processed sequentially", "B": "Context window too small: use a larger model",
                "C": "A stronger prompt demanding equal thoroughness",
                "D": "Per-file local passes plus a separate cross-file integration pass"},
    "answer": "D",
    "why": "Attention dilution is architectural; only dedicated per-file passes plus an integration pass fix it. "
           "A misses cross-batch issues; B and C don't change attention allocation.",
}


# ---- mock model: a deterministic static analyser stands in for Claude -------------------------

RULES = {  # kind -> (regex, severity, description)
    "sql_injection": (r"\"SELECT[^\"]*'\s*\+|\"SELECT[^\"]*\"\s*\+", "critical", "SQL built by string concatenation"),
    "inefficient_foreach": (r"\.forEach\(\w+ => \{ \w+\.push\(", "minor", "forEach+push where map() would do"),
    "null_dereference": (r"\.find\([^)]*\);\n\s*return \w+\.\w+", "major", "find() result used without a null check"),
    "hardcoded_secret": (r"sk_live_", "critical", "hard-coded API secret"),
    "missing_await": (r"= fetch\(", "major", "fetch() result used without await"),
}


def analyse(name: str, src: str) -> list[dict]:
    issues = []
    for kind, (pattern, severity, desc) in RULES.items():
        for m in re.finditer(pattern, src):
            issues.append({"file": name, "line": src[:m.start()].count("\n") + 1, "severity": severity,
                           "kind": kind, "description": desc})
    return issues


def interface(name: str, src: str) -> dict:
    exports = [{"function": fn, "returns": re.findall(r"(\w+):", ret)}
               for fn, ret in re.findall(r"export (?:async )?function (\w+)[\s\S]*?return \{ ([^}]*) \}", src)]
    uses = []
    for fn, from_file in re.findall(r"import \{ (\w+) \} from '\./([\w.]+)'", src):
        var = re.search(rf"const (\w+) = {fn}\(", src)
        props = sorted(set(re.findall(rf"\b{var.group(1)}\.(\w+)", src))) if var else []
        uses.append({"function": fn, "from_file": from_file, "properties": props})
    style = "concatenated" if re.search(RULES["sql_injection"][0], src) else "parameterized" if "?'" in src or "= ?" in src else None
    return {"exports": exports, "uses": uses, "query_style": style}


def _files_in(prompt: str) -> dict[str, str]:
    parts = re.split(r"^--- ([\w.]+) ---\n", prompt, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    if prompt.startswith("[LOCAL REVIEW]"):
        (name, src), = _files_in(prompt).items()
        issues = analyse(name, src)
        return json_message({"file": name, "bug_count": len(issues), "issues": issues, **interface(name, src)})
    if prompt.startswith("[INTEGRATION REVIEW]"):
        summaries = json.loads(prompt.rsplit("\n", 1)[1])  # the summaries JSON is the last line
        by_file = {s["file"]: s for s in summaries}
        cross = []
        for s in summaries:
            for use in s["uses"]:
                producer = by_file.get(use["from_file"], {"exports": []})
                returned = next((e["returns"] for e in producer["exports"] if e["function"] == use["function"]), None)
                missing = [p for p in use["properties"] if returned is not None and p not in returned]
                if missing:
                    cross.append({"files": [use["from_file"], s["file"]], "kind": "api_contract",
                                  "description": f"{s['file']} reads {missing} from {use['function']}() but it returns {returned}"})
        styles = {s["file"]: s["query_style"] for s in summaries if s["query_style"]}
        if len(set(styles.values())) > 1:
            cross.append({"files": sorted(f for f, st in styles.items() if st == "concatenated"), "kind": "inconsistent_pattern",
                          "description": f"queries parameterized in {sorted(f for f, st in styles.items() if st == 'parameterized')} "
                                         "but concatenated elsewhere"})
        return json_message({"cross_file_issues": cross})
    if prompt.startswith("[SINGLE PASS]"):
        # SIMULATED attention dilution (the lesson's symptom): files 1-5 full depth, 6-9 critical only, 10+ skimmed.
        issues = []
        for pos, (name, src) in enumerate(_files_in(prompt).items(), start=1):
            found = analyse(name, src)
            issues += found if pos <= 5 else [i for i in found if i["severity"] == "critical"] if pos <= 9 else []
        return json_message({"issues": issues})
    if prompt.startswith("[BATCH REVIEW]"):
        files = _files_in(prompt)
        issues = [i for n, s in files.items() for i in analyse(n, s)]  # small batch: full attention within it
        return json_message({"issues": issues})
    raise ValueError(f"unexpected prompt: {prompt[:40]}")


def main():
    print(mode_banner())
    files = load_repo()
    single = single_pass_review(get_client(mock_model), files)
    multi = multi_pass_review(get_client(mock_model), files)
    print(f"step 5 comparison: {compare(single, multi, files)}")
    for c in multi["cross_file"]:
        print(f"  cross-file [{c['kind']}] {c['description']}")
    print(f"step 6 single-pass artefacts: {dilution_artefacts(single, files)}")
    print(f"       multi-pass artefacts : {dilution_artefacts(multi, files) or 'none'}")
    print(f"pattern for code review: {choose_pattern(True)}; for legacy exploration: {choose_pattern(False)}")
    plan = adaptive_test_plan(files)
    print("adaptive test plan:\n  " + "\n  ".join(plan["log"]))


if __name__ == "__main__":
    main()
