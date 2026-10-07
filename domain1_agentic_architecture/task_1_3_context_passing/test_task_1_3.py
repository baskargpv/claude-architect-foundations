import pytest
from pydantic import ValidationError

from common.mock import MockClient
from domain1_agentic_architecture.task_1_3_context_passing import anti_pattern as anti
from domain1_agentic_architecture.task_1_3_context_passing import good_example as good

URLS = [s["url"] for s in good.WEB_SOURCES]
DOC = good.DOCUMENTS[0]["name"]


def test_spawn_requires_explicit_agent_grant():
    assert good.can_spawn_subagents(good.COORDINATOR_OPTIONS)
    assert good.can_spawn_subagents({"allowed_tools": ["Task"]})  # exam-guide name
    assert not good.can_spawn_subagents(anti.BROKEN_OPTIONS)  # agents defined, not granted


def test_coordinator_refuses_to_run_without_grant():
    with pytest.raises(PermissionError):
        good.run(MockClient(good.mock_model), options=anti.BROKEN_OPTIONS)


def test_subagent_tools_are_scoped():
    assert good.tool_scope_violations(good.SUBAGENTS) == []
    assert len(good.tool_scope_violations(anti.BROKEN_OPTIONS["agents"])) == 2


def test_finding_metadata_must_match_retriever():
    with pytest.raises(ValidationError):
        good.Finding(claim="x", retrieved_by="web_search_agent", confidence="high")
    with pytest.raises(ValidationError):
        good.Finding(claim="x", retrieved_by="document_analysis_agent", confidence="high", document_name=DOC)


def test_subagents_run_in_parallel_as_separate_requests():
    client = MockClient(good.mock_model)
    findings = good.gather_findings(client, good.GOAL)
    assert {f.retrieved_by for f in findings} == {"web_search_agent", "document_analysis_agent"}
    assert len(client.calls) == 2


def test_good_synthesis_prompt_carries_full_metadata():
    prompt, report = good.run(MockClient(good.mock_model))
    for url in URLS:
        assert url in prompt and url in report
    assert '"page_number": 9' in prompt
    assert f"{DOC} p.4" in report


def test_anti_synthesis_prompt_has_claims_but_no_metadata():
    prompt, report = anti.run(MockClient(good.mock_model))
    assert "41% of illustrators" in prompt
    assert not any(url in prompt for url in URLS)
    assert DOC not in prompt and "page_number" not in prompt
    assert not any(url in report for url in URLS)  # unsourced output, traced to the handoff


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "every claim unsourced" in capsys.readouterr().out
