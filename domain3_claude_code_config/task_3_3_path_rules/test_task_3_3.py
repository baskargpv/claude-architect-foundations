import pytest

from common.claude_config import matches, parse_frontmatter
from domain3_claude_code_config.task_3_3_path_rules import anti_pattern as anti
from domain3_claude_code_config.task_3_3_path_rules import good_example as good


@pytest.fixture
def project(tmp_path):
    good.write_rules(tmp_path)
    return tmp_path


def test_steps1_3_rules_have_paths_frontmatter(project):
    for name in good.RULES:
        meta, body = parse_frontmatter((project / ".claude/rules" / name).read_text())
        assert isinstance(meta["paths"], list) and body.startswith("#")


@pytest.mark.parametrize("path,expected", [
    ("a.test.ts", True), ("src/deep/x/y.test.tsx", True), ("src/x.ts", False), ("src/x.spec.ts", True)])
def test_double_star_matches_any_depth(path, expected):
    assert matches(path, ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"]) is expected


@pytest.mark.parametrize("edited,expected", [
    ("src/billing/invoice.test.ts", ["testing.md"]),  # step 4
    ("src/api/users/handler.ts", ["api-conventions.md"]),  # step 5
    ("terraform/prod/main.tf", ["terraform.md"]),
    ("README.md", []),
])
def test_steps4_5_only_matching_rules_load(project, edited, expected):
    assert good.rules_for(project, edited) == expected


def test_step6_split_rules_are_smaller_than_root_claude_md(project):
    f = good.footprint(project, "src/api/users/handler.ts")
    assert f["path_rules_chars"] < f["root_claude_md_chars"] / 2


def test_placement_guide():
    assert good.placement("file type across many directories") == ".claude/rules/ with paths: globs"


def test_trap1_copies_drift():
    assert anti.trap1_directory_copies() == {"files_to_maintain": 50, "versions_in_circulation": 2}


def test_trap2_root_wastes_tokens_on_unrelated_conventions():
    r = anti.trap2_everything_in_root()
    assert r["wasted_chars"] > r["relevant_chars"]


def test_trap3_skill_does_not_apply_automatically():
    assert anti.trap3_skill_instead_of_rule() == {"conventions_applied_while_editing": False}


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "testing.md" in capsys.readouterr().out
