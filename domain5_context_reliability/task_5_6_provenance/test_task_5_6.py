import pytest
from pydantic import ValidationError

from common.mock import MockClient
from domain5_context_reliability.task_5_6_provenance import anti_pattern as anti
from domain5_context_reliability.task_5_6_provenance import good_example as good


def findings():
    c = MockClient(good.mock_model)
    return good.research(c, "WEB", "heat pumps") + good.research(c, "DOCS", "heat pumps")


def test_step1_mapping_requires_all_five_fields():
    with pytest.raises(ValidationError):
        good.Finding(claim="x", sourceUrl="u", documentName="d", relevantExcerpt="e")  # no publicationDate


def test_step2_two_subagents_return_full_mappings():
    fs = findings()
    assert len(fs) == 4 and all(f.sourceUrl and f.publicationDate and f.relevantExcerpt for f in fs)


def test_step3_synthesis_keeps_every_citation():
    report = good.synthesise(findings())
    assert all(f.sourceUrl in report for f in findings())


def test_step4_conflict_keeps_both_values_with_explanation():
    c = good.find_conflicts(findings())
    assert c[0]["metric"] == "market growth" and {v for v, _, _ in c[0]["values"]} == {"12%", "8%"}
    assert c[0]["explanation"].startswith("trend over time")


def test_conflict_types():
    base = dict(claim="c", sourceUrl="u", documentName="d", relevantExcerpt="e", metric="m")
    same = good.Finding(**base, publicationDate="2024-01-01", value="1", methodology="calendar")
    assert good.classify_conflict(same, good.Finding(**base, publicationDate="2024-01-01", value="2", methodology="fiscal")).startswith("methodology")
    assert good.classify_conflict(same, good.Finding(**base, publicationDate="2024-01-01", value="2", methodology="calendar")).startswith("unexplained")


def test_step5_rendering_by_content_type():
    report = good.synthesise(findings())
    assert "| Metric | Value | Source |" in report  # financial -> table
    assert "\n- Inverter heat pumps" in report  # technical -> list
    assert "subsidies for home batteries [Energy Daily" in report  # news -> prose


def test_trap1_most_recent_drops_a_value():
    assert "12%" not in anti.trap1_pick_most_recent()


def test_trap2_trend_mislabelled_as_conflict():
    assert anti.trap2_everything_is_a_conflict().startswith("CONFLICT")


def test_trap3_paraphrase_loses_attribution():
    assert "http" not in anti.trap3_paraphrase()


def test_trap4_uniform_format_has_no_table():
    assert "|" not in anti.trap4_uniform_prose()


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "trend over time" in capsys.readouterr().out
