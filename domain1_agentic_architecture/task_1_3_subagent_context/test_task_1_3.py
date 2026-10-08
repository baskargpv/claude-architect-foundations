import threading

import pytest
from pydantic import ValidationError

from common.mock import MockClient
from domain1_agentic_architecture.task_1_3_subagent_context import anti_pattern as anti
from domain1_agentic_architecture.task_1_3_subagent_context import good_example as good

RESEARCH_SYSTEMS = {d.prompt for d in good.SUBAGENTS.values()}


def barrier_mock(parties=2):
    """Each research subagent's FIRST call waits for the other: passes only if they run concurrently."""
    barrier = threading.Barrier(parties, timeout=3)

    def responder(kwargs):
        if kwargs.get("system") in RESEARCH_SYSTEMS and len(kwargs["messages"]) == 1:
            barrier.wait()
        return good.mock_model(kwargs)
    return responder


# ---- build exercise --------------------------------------------------------------------------

def test_step1_agent_in_allowed_tools_with_agents_defined():
    assert "Agent" in good.COORDINATOR_OPTIONS.allowed_tools
    assert set(good.COORDINATOR_OPTIONS.agents) == {"web_search_agent", "document_analysis_agent"}
    assert good.spawn_decision(good.AgentOptions(["Task"], good.SUBAGENTS)) == "allow"  # exam-guide name


def test_spawn_without_grant_exam_and_current_docs():
    no_grant = good.AgentOptions(["web_search"], good.SUBAGENTS, unattended=True)
    assert good.spawn_decision(no_grant) == "deny"  # exam answer; current docs: denied in unattended runs
    assert good.spawn_decision(good.AgentOptions(["web_search"], good.SUBAGENTS, unattended=False)) == "ask"
    out = good.run(MockClient(good.mock_model), options=no_grant)
    assert out["spawner"].findings == [] and out["spawner"].spawn_log == []


def test_step2_tools_are_scoped_per_role():
    assert good.scope_violations(good.SUBAGENTS) == []
    assert good.SUBAGENTS["web_search_agent"].tools == ["web_search"]
    assert good.SUBAGENTS["document_analysis_agent"].tools == ["read_document"]


def test_step3_finding_schema_enforces_metadata():
    with pytest.raises(ValidationError):
        good.Finding(claim="x", confidence="high", retrieved_by="web_search_agent")
    with pytest.raises(ValidationError):
        good.Finding(claim="x", confidence="high", retrieved_by="document_analysis_agent", document_name="d")


def test_step4_full_findings_reach_synthesis():
    out = good.run(MockClient(good.mock_model))
    p = out["synthesis_prompt"]
    assert "https://example.org/solar-efficiency-2025" in p and '"page_number": 27' in p
    assert good.trace_attribution_gap(p, out["spawner"].findings) == "metadata reached synthesis"


def test_step5_every_claim_attributed():
    out = good.run(MockClient(good.mock_model))
    assert len(out["spawner"].findings) == 4 and out["unattributed"] == []


def test_step6_research_subagents_run_in_parallel():
    out = good.run(MockClient(barrier_mock()))  # would raise BrokenBarrierError if sequential
    assert {s["subagent"] for s in out["spawner"].spawn_log} == {"web_search_agent", "document_analysis_agent"}


def test_coordinator_emits_both_spawns_in_one_response_and_waits():
    client = MockClient(good.mock_model)
    good.run_research(client)
    coordinator_calls = [c for c in client.calls if c.get("system") == good.COORDINATOR_SYSTEM]
    assert len(coordinator_calls) == 2  # spawn turn, then one turn after BOTH results came back
    results = coordinator_calls[1]["messages"][-1]["content"]
    assert len(results) == 2


def test_subagents_only_see_their_own_prompt():
    client = MockClient(good.mock_model)
    good.run_research(client)
    first_sub_calls = [c for c in client.calls if c.get("system") in RESEARCH_SYSTEMS and len(c["messages"]) == 1]
    assert all(good.COORDINATOR_SYSTEM not in str(c["messages"]) for c in first_sub_calls)


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_no_context_no_findings():
    assert anti.trap1_assume_inherited_context(MockClient(good.mock_model)) == []


def test_trap2_prompt_fix_cannot_restore_stripped_metadata():
    r = anti.trap2_blame_synthesis(MockClient(good.mock_model))
    assert len(r["unattributed_before"]) == 4 and len(r["unattributed_after_prompt_fix"]) == 4
    findings = good.run_research(MockClient(good.mock_model)).findings
    assert good.trace_attribution_gap(anti.strip_metadata_prompt(findings), findings) == "coordinator handoff dropped metadata"


def test_trap3_sequential_spawning_has_no_overlap():
    assert anti.trap3_sequential_invocation() == 1


def test_trap4_resume_mixes_alternatives_fork_keeps_them_apart():
    r = anti.trap4_confuse_fork_with_resume([{"role": "user", "content": "baseline"}])
    assert r["approach_b_sees_approach_a"] and r["forks_independent"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "B"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "unattributed claims: none" in capsys.readouterr().out
