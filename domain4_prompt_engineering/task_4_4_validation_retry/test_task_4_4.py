import pytest

from common.mock import MockClient
from domain4_prompt_engineering.task_4_4_validation_retry import anti_pattern as anti
from domain4_prompt_engineering.task_4_4_validation_retry import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_schema_has_self_check_fields():
    assert {"calculated_total", "stated_total", "conflict_detected", "detected_pattern"} <= set(good.SCHEMA["required"])


def test_step2_validators_give_specific_messages():
    base = dict(vendor="V", department=None, invoice_date="2026-09-01", due_date="2026-10-01", line_items=[200, 250],
                stated_total=500, calculated_total=450, detected_pattern="x")
    assert good.validate(base)[1] == "line items sum to £450.00 but stated_total is £500.00"
    assert "before invoice_date" in good.validate({**base, "line_items": [500], "due_date": "2026-08-01"})[1]


def test_step3_retry_includes_document_failed_extraction_and_error():
    c = client()
    good.process(c, "A")
    retry_prompt = c.calls[1]["messages"][0]["content"]
    assert good.DOCS["A"] in retry_prompt and "Your previous extraction" in retry_prompt
    assert "Validation error: line items sum to £450.00" in retry_prompt


@pytest.mark.parametrize("doc,status,attempts", [("A", "ok", 2), ("B", "ok", 2), ("C", "human_review", 1),
                                                  ("D", "human_review", 1), ("E", "human_review", 1)])
def test_step4_only_fixable_documents_are_retried(doc, status, attempts):
    r = good.process(client(), doc)
    assert (r["status"], r["attempts"]) == (status, attempts)


def test_step5_dismissal_rates_by_pattern():
    reviews = [{"pattern": "a", "dismissed": True}, {"pattern": "a", "dismissed": False}, {"pattern": "b", "dismissed": False}]
    assert good.dismissal_rates(reviews) == {"a": 0.5, "b": 0.0}


def test_trap1_retrying_cannot_create_missing_information():
    assert anti.trap1_retry_absent_information(client())["department_found"] is False


def test_trap2_retry_without_error_repeats_the_mistake():
    assert anti.trap2_retry_without_error(client())["same_error_every_time"]


def test_trap3_schema_passes_semantic_error():
    r = anti.trap3_schema_only(client())
    assert r["schema_valid"] and r["semantic_error"]


def test_trap4_pydantic_catches_what_schema_cannot():
    r = anti.trap4_pydantic_redundant(client())
    assert r["passes_schema"] and "before invoice_date" in r["pydantic_says"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "human_review" in capsys.readouterr().out
