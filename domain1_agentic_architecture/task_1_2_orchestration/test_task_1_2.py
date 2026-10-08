from common.mock import MockClient
from domain1_agentic_architecture.task_1_2_orchestration import anti_pattern as anti
from domain1_agentic_architecture.task_1_2_orchestration import good_example as good


def _run():
    client = MockClient(good.mock_model)
    return client, good.Coordinator(client).run()


# ---- build exercise --------------------------------------------------------------------------

def test_step2_decomposition_covers_full_breadth():
    _, r = _run()
    assert len(r.subtopics) >= 5
    assert set(r.subtopics) == good.REQUIRED_SUBTOPICS


def test_step3_every_subagent_prompt_has_explicit_context():
    _, r = _run()
    prompts = [e["prompt"] for e in r.routing_log if "prompt" in e]
    assert all(f"Research goal: {good.GOAL}" in p and "Your assigned subtopic:" in p for p in prompts)


def test_step3_document_agent_receives_web_results_via_coordinator():
    _, r = _run()
    solar_doc = next(e for e in r.routing_log if e.get("to") == "document_analysis" and e["subtopic"] == "solar")
    assert "https://example.org/solar/1" in solar_doc["prompt"]


def test_subagent_calls_are_isolated_single_message_requests():
    client, _ = _run()
    assert all(len(c["messages"]) == 1 for c in client.calls)


def test_step4_coverage_labels():
    labels = good.Coordinator.assess_coverage({
        "a": [{"source": "x"}] * 3, "b": [{"source": "x"}], "c": [], "d": [{"source": ""}] * 5})
    assert labels == {"a": "well-covered", "b": "partial", "c": "missing", "d": "missing"}


def test_step5_only_gaps_are_redelegated_until_threshold():
    _, r = _run()
    follow_ups = [e["subtopic"] for e in r.routing_log if e.get("follow_up")]
    assert set(follow_ups) == {"tidal", "nuclear fusion"}  # the missing + partial ones only
    assert r.iterations == 2  # tidal needs two rounds; exits on threshold, not the cap


def test_step6_all_six_energy_types_well_covered():
    _, r = _run()
    assert all(v == "well-covered" for v in r.coverage.values())
    assert good.trace_coverage_failure(r) == "no gap"


def test_max_iterations_is_a_safety_net():
    r = good.Coordinator(MockClient(good.mock_model), max_iterations=1).run()
    assert r.iterations == 1 and r.coverage["tidal"] == "partial"


def test_all_traffic_routes_through_the_hub():
    _, r = _run()
    assert all(("to" in e) != ("from" in e) for e in r.routing_log)  # every entry is hub->spoke or spoke->hub


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_tuning_queries_cannot_fix_narrow_decomposition():
    r = anti.trap1_blame_downstream(MockClient(good.mock_model))
    assert r.subtopics == ["solar", "wind"]
    assert "coordinator decomposition" in good.trace_coverage_failure(r)


def test_trap2_subagent_without_explicit_context_cannot_help():
    f = anti.trap2_assume_shared_memory(MockClient(good.mock_model))
    assert f[0]["source"] == "" and "no subtopic" in f[0]["claim"]


def test_trap3_direct_communication_bypasses_observability_and_error_handling():
    d = anti.trap3_direct_subagent_communication(MockClient(good.mock_model))
    assert d["coordinator_routing_log"] == [] and "unhandled" in d["outcome"]


def test_trap4_more_subagents_inherit_narrow_assignments():
    r = anti.trap4_add_more_subagents(MockClient(good.mock_model))
    assert len({e["to"] for e in r.routing_log if "to" in e}) == 4
    assert set(r.subtopics) == {"solar", "wind"}


def test_trap5_correct_trace_points_at_coordinator_not_subagents():
    r = anti.trap4_add_more_subagents(MockClient(good.mock_model))
    assert "subagent" in anti.trap5_wrong_failure_trace(r)
    assert good.trace_coverage_failure(r).startswith("coordinator decomposition")


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "trace: no gap" in capsys.readouterr().out
