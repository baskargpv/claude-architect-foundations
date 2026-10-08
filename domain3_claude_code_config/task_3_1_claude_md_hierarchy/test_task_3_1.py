from pathlib import Path

import pytest

from domain3_claude_code_config.task_3_1_claude_md_hierarchy import anti_pattern as anti
from domain3_claude_code_config.task_3_1_claude_md_hierarchy import good_example as good


@pytest.fixture
def tree(tmp_path):
    return good.build_project(tmp_path / "repo"), tmp_path / "home"


def names(loaded, root):
    return [str(Path(p).relative_to(root)) for p, _ in loaded]


def test_steps1_4_files_written(tree):
    project, _ = tree
    assert all((project / rel).exists() for rel in good.PROJECT_FILES)


def test_step5_root_loads_project_and_always_on_rule_only(tree):
    project, home = tree
    assert names(good.loaded_memory(project, home), project) == [".claude/CLAUDE.md", ".claude/rules/security.md"]


def test_step5_api_directory_adds_package_file_and_matching_rule(tree):
    project, home = tree
    loaded = good.loaded_memory(project, home, project / "packages/api", ["packages/api/users.test.ts"])
    assert names(loaded, project) == [".claude/CLAUDE.md", "packages/api/CLAUDE.md",
                                      ".claude/rules/security.md", ".claude/rules/testing.md"]


def test_subdirectory_file_loads_on_demand_when_a_file_there_is_read(tree):
    project, home = tree
    loaded = good.loaded_memory(project, home, touched=["packages/api/routes.ts"])
    assert "packages/api/CLAUDE.md" in names(loaded, project)


def test_step4_import_inlined_relative_to_containing_file(tree):
    project, home = tree
    assert "REST resources are plural nouns" in good.context_text(good.loaded_memory(project, home))


def test_import_path_is_relative_to_the_containing_file_not_the_cwd(tmp_path):
    project = good.build_project(tmp_path / "r", {".claude/CLAUDE.md": "@./standards/naming.md\n",
                                                  "standards/naming.md": "plural nouns"})
    assert "plural nouns" not in good.expand_imports(project / ".claude/CLAUDE.md")  # looks in .claude/standards/


def test_local_file_loads_after_and_conflicts_are_concatenated(tree):
    project, home = tree
    (project / "CLAUDE.md").write_text("Use tabs.")
    (project / "CLAUDE.local.md").write_text("Use spaces.")
    loaded = good.loaded_memory(project, home)
    assert names(loaded, project)[:2] == ["CLAUDE.md", ".claude/CLAUDE.md"] and "CLAUDE.local.md" in names(loaded, project)
    text = good.context_text(loaded)
    assert "Use tabs." in text and "Use spaces." in text  # no precedence: both reach Claude


def test_step6_user_file_is_outside_the_repo(tree):
    project, home = tree
    assert not good.in_repo(project, home / ".claude" / "CLAUDE.md")
    assert good.in_repo(project, project / ".claude" / "CLAUDE.md")


def test_trap1_new_teammate_misses_user_level_rules():
    assert anti.trap1_conventions_in_user_config() == {"dev_a_has_rule": True, "dev_b_has_rule": False}


def test_trap2_memory_command_is_diagnostic_only():
    assert anti.trap2_memory_loads_nothing() == {"changed_what_loaded": False}


def test_trap3_directory_copies_drift():
    r = anti.trap3_directory_level_for_cross_cutting()
    assert r["copies"] == 50 and r["distinct_versions"] == 2


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "packages/api/CLAUDE.md" in capsys.readouterr().out
