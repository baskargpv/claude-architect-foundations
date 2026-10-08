import json

from common.mcp_util import read_resource, resources, tool_defs
from domain2_tool_design_mcp.task_2_4_mcp_integration import anti_pattern as anti
from domain2_tool_design_mcp.task_2_4_mcp_integration import good_example as good


def test_step1_project_config_shapes(tmp_path):
    project_cfg, _ = good.write_configs(tmp_path / "repo", tmp_path / "home")
    servers = json.loads(project_cfg.read_text())["mcpServers"]
    assert servers["github"]["type"] == "http" and servers["github"]["url"].startswith("https://")
    assert "command" in servers["warehouse"]
    assert all(good.validate_entry(n, e) is None for n, e in servers.items())


def test_url_without_type_is_flagged():
    assert "skipped" in good.validate_entry("x", {"url": "https://example.com/mcp"})


def test_step2_git_diff_has_variable_reference_not_secret(tmp_path):
    good.write_configs(tmp_path / "repo", tmp_path / "home")
    diff = good.staged_diff(tmp_path / "repo")
    assert "${GITHUB_TOKEN}" in diff and good.find_literal_secrets(diff) == []


def test_env_expansion_default_and_unset_var_warning():
    warnings = []
    assert good.expand_env("${A}-${B:-fallback}-${C}", {"A": "1"}, warnings) == "1-fallback-"
    assert warnings == ["C is not set"]


def test_step3_both_scopes_load_together(tmp_path):
    project_cfg, user_cfg = good.write_configs(tmp_path / "repo", tmp_path / "home")
    loaded = good.load_servers(project_cfg, user_cfg, {"GITHUB_TOKEN": "t"})
    assert sorted(loaded["servers"]) == ["github", "my-scratchpad", "warehouse"]
    assert loaded["servers"]["github"]["headers"]["Authorization"] == "Bearer t"
    assert loaded["servers"]["warehouse"]["env"]["DATABASE_URL"] == "postgresql://localhost/dev"


def test_step4_resource_has_name_description_mimetype_uri():
    srv = good.build_warehouse_server()
    r = resources(srv)[0]
    assert (r.name, str(r.uri), r.mime_type) == ("warehouse_schema", "schema://warehouse/tables", "application/json")
    assert r.description and "orders" in json.loads(read_resource(srv, str(r.uri)))


def test_step5_tool_description_is_3_to_5_sentences_and_compares_to_builtins():
    q = good.description_quality(tool_defs(good.build_warehouse_server())[0]["description"])
    assert q["ok"] and q["compares_to_builtins"]


def test_trap1_community_first_for_standard_integrations():
    assert good.choose_integration("jira") == "evaluate the community MCP server first"
    assert anti.trap1_custom_jira_server()["decision"].startswith("build")


def test_trap2_user_scope_is_invisible_to_teammates():
    r = anti.trap2_team_config_in_user_scope()
    assert r == {"developer_a": ["jira"], "developer_b": []}


def test_trap3_literal_token_lands_in_git():
    assert anti.trap3_committed_credentials() != []


def test_trap4_sparse_mcp_description_loses_to_builtin():
    assert anti.trap4_sparse_description()["chosen"] == "Grep"


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "warehouse_schema" in capsys.readouterr().out
