"""Task 5.6 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-6-information-provenance

Trap 1  selecting the most recent source when two credible sources conflict
Trap 2  assuming different numbers are always contradictions
Trap 3  letting synthesis paraphrase without preserving claim-source mappings
Trap 4  rendering every content type in one uniform format
"""

from __future__ import annotations

from domain5_context_reliability.task_5_6_provenance.good_example import Finding, SOURCES

FINDINGS = [Finding(**f) for agent in SOURCES.values() for f in agent]


def trap1_pick_most_recent() -> str:
    growth = [f for f in FINDINGS if f.metric == "market growth"]
    latest = max(growth, key=lambda f: f.publicationDate)
    return f"Market growth: {latest.value}."  # the 2023 figure, and the trend, are gone


def trap2_everything_is_a_conflict() -> str:
    a, b = [f for f in FINDINGS if f.metric == "market growth"]
    return f"CONFLICT: sources disagree ({a.value} vs {b.value})."  # ignores that they measure different years


def trap3_paraphrase() -> str:
    return "Heat-pump adoption is growing strongly, subsidies are expanding and efficiency is high."  # no sources at all


def trap4_uniform_prose() -> str:
    return " ".join(f.claim for f in FINDINGS)  # financial figures buried in sentences, no table, no list


def main():
    print(f"trap 1 most recent : {trap1_pick_most_recent()}")
    print(f"trap 2 all conflict: {trap2_everything_is_a_conflict()}")
    print(f"trap 3 paraphrase  : {trap3_paraphrase()}")
    print(f"trap 4 uniform     : {trap4_uniform_prose()}")


if __name__ == "__main__":
    main()
