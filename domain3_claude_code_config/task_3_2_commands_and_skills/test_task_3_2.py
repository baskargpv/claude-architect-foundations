import pytest

from common.mock import MockClient
from domain3_claude_code_config.task_3_2_commands_and_skills import anti_pattern as anti
from domain3_claude_code_config.task_3_2_commands_and_skills import good_example as good


@pytest.fixture
def dirs(tmp_path):
    repo, me = tmp_path / "repo", tmp_path / "me"
    good.write_files(repo, me)
    return repo, me, tmp_path / "teammate"


def test_steps1_4_frontmatter(dirs):
    repo, me, _ = dirs
    skill = good.discover_commands(repo, me)["brainstorm"]["meta"]
    assert skill["context"] == "fork" and skill["allowed-tools"] == ["Read", "Grep", "Glob"] and skill["argument-hint"]


def test_step5_review_everywhere_brainstorm_only_for_me(dirs):
    repo, me, teammate = dirs
    assert sorted(good.discover_commands(repo, me)) == ["brainstorm", "review"]
    assert sorted(good.discover_commands(repo, teammate)) == ["review"]


def test_skill_wins_name_clash_and_description_falls_back(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".claude/commands").mkdir(parents=True)
    (repo / ".claude/commands/deploy.md").write_text("Old command.")
    (repo / ".claude/skills/deploy").mkdir(parents=True)
    (repo / ".claude/skills/deploy/SKILL.md").write_text("Deploy the app safely.\n\nStep details...")
    found = good.discover_commands(repo, tmp_path / "home")
    assert found["deploy"]["shape"] == "skill" and found["deploy"]["description"] == "Deploy the app safely."


def test_allowed_tools_exam_vs_current(dirs):
    repo, me, _ = dirs
    p = good.tool_permissions(good.discover_commands(repo, me)["brainstorm"]["meta"])
    assert p["exam_answer_restricted_to"] == ["Read", "Grep", "Glob"]
    assert "Bash" in p["current_still_callable"]  # pre-approval isn't a restriction


def test_step6_fork_returns_only_the_summary(dirs):
    repo, me, _ = dirs
    history = good.run_skill(MockClient(good.mock_model), good.discover_commands(repo, me)["brainstorm"], "x", [])
    assert history == [{"role": "assistant", "content": "SUMMARY: best three are approaches 2, 5 and 9."}]


def test_trap1_loose_file_in_skills_creates_nothing():
    assert anti.trap1_flat_file_in_skills() == []


def test_trap2_user_path_is_not_shared():
    assert anti.trap2_team_command_in_user_path() == {"me": ["review"], "teammate": []}


def test_trap3_skill_body_is_not_session_context():
    assert anti.trap3_skill_as_always_on() == {"rule_in_every_session": False}


def test_trap4_without_fork_verbose_output_floods_main_conversation():
    assert anti.trap4_no_fork()["chars_added_to_main_conversation"] > 500


def test_trap5_workflow_in_claude_md_costs_every_session():
    r = anti.trap5_workflow_in_claude_md()
    assert r["chars_loaded_over_sessions"] == 10 * r["as_a_skill_used_twice"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "SUMMARY" in capsys.readouterr().out
