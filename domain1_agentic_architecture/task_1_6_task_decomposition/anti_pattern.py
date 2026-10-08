"""Task 1.6 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-6-task-decomposition

Trap 1  choosing the pattern by what sounds sophisticated, not task characteristics
Trap 2  a more powerful model / larger context window as the fix for dilution
Trap 3  single pass with better prompts as "equivalent" to multi-pass
Trap 4  fixed pipelines for open-ended investigation
Trap 5  batching files without a cross-file integration pass
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from domain1_agentic_architecture.task_1_6_task_decomposition.good_example import (
    ISSUES_SCHEMA,
    import_graph,
    load_repo,
    mock_model,
    single_pass_review,
)


def trap1_pattern_by_sophistication(task: str) -> str:
    return "dynamic_decomposition"  # "it sounds more advanced" - even for a code review whose steps are known


def trap2_bigger_model(client, files) -> dict:
    """Same single pass, 'bigger model, bigger window'. The architecture is unchanged, so the
    attention is still spread across every file at once (the mock models the lesson's claim)."""
    return single_pass_review(client, files, "You have a 1M-token context window - review all files.")


def trap3_better_prompt(client, files) -> dict:
    return single_pass_review(client, files, "Be EQUALLY thorough on every file. Do not skim later files.")


FIXED_TEST_PLAN = ["09_invoice.js", "10_profile.js", "11_reports.js", "03_search.js"]  # decided before exploring


def trap4_fixed_pipeline_for_exploration(files) -> dict:
    graph, tested, built_on_untested = import_graph(files), set(), []
    for module in FIXED_TEST_PLAN:  # cannot react to what writing the tests reveals
        built_on_untested += [(module, d) for d in graph[module] if d not in tested]
        tested.add(module)
    return {"order": FIXED_TEST_PLAN, "tests_built_on_untested_dependencies": built_on_untested}


def trap5_batching_without_integration(client, files, batch_size: int = 5) -> dict:
    names, issues = list(files), []
    for i in range(0, len(names), batch_size):
        batch = "\n".join(f"--- {n} ---\n{files[n]}" for n in names[i:i + batch_size])
        issues += ask_json(client, f"[BATCH REVIEW]\n{batch}", ISSUES_SCHEMA)["issues"]
    return {"issues": issues, "cross_file": []}  # no pass ever sees 01_users.js next to 10_profile.js


def main():
    print(mode_banner())
    files = load_repo()
    print(f"trap 1 sophistication : code review -> {trap1_pattern_by_sophistication('multi-file code review')}")
    print(f"trap 2 bigger model   : {len(trap2_bigger_model(get_client(mock_model), files)['issues'])} issues (multi-pass finds 8)")
    print(f"trap 3 better prompt  : {len(trap3_better_prompt(get_client(mock_model), files)['issues'])} issues (multi-pass finds 8)")
    r = trap4_fixed_pipeline_for_exploration(files)
    print(f"trap 4 fixed plan     : tests built on untested deps {r['tests_built_on_untested_dependencies']}")
    r = trap5_batching_without_integration(get_client(mock_model), files)
    print(f"trap 5 batches of 5   : {len(r['issues'])} local issues, {len(r['cross_file'])} cross-file  <- contract bug missed")


if __name__ == "__main__":
    main()
