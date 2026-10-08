import pytest

from domain2_tool_design_mcp.task_2_5_builtin_tools import anti_pattern as anti
from domain2_tool_design_mcp.task_2_5_builtin_tools import good_example as good


@pytest.fixture
def root(tmp_path):
    return good.workspace(tmp_path / "ws")


def test_step1_grep_finds_direct_callers_and_wrapper_callers(root):
    r = good.find_callers(good.Tools(root), "processLegacyOrder")
    assert r["direct"] == ["src/admin.ts", "src/checkout.ts", "src/orders/OrderProcessor.ts"]
    assert r["via_wrapper"] == {"submitLegacyOrder": ["src/api/orders.ts", "src/jobs/nightly.ts"]}


def test_step2_glob_finds_sibling_tests(root):
    t = good.Tools(root)
    assert good.find_tests(t, ["src/checkout.ts", "src/orders/OrderProcessor.ts"]) == [
        "tests/OrderProcessor.test.ts", "tests/checkout.test.ts"]


def test_steps3_4_migration_edits_callers(root):
    r = good.migrate(root)
    assert r["edits"] == {"src/admin.ts": "edit", "src/checkout.ts": "replace_all"}
    assert "processLegacyOrder(" not in (root / "src/checkout.ts").read_text()
    reads = [line for line in r["log"] if line.startswith("Read")]
    assert len(reads) == 5  # only files the searches justified


def test_edit_refuses_non_unique_match(root):
    with pytest.raises(good.EditError, match="not unique"):
        good.Tools(root).edit("src/checkout.ts", "processLegacyOrder(cart.order)", "x")


def test_step5_widen_to_change_one_occurrence(root):
    t = good.Tools(root)
    assert good.edit_with_recovery(t, "src/checkout.ts", "processLegacyOrder(", "processOrder(", False) == "widened"
    assert (root / "src/checkout.ts").read_text().count("processLegacyOrder(") == 1


def test_trap1_glob_cannot_find_callers(root):
    assert anti.trap1_glob_for_callers(root) == []


def test_trap2_grep_cannot_find_files_by_name(root):
    assert anti.trap2_grep_for_test_files(root) == []
    assert good.Tools(root).glob("tests/*.test.ts")


def test_trap3_reading_everything_costs_more_than_the_whole_incremental_job(tmp_path, root):
    assert anti.trap3_read_everything(root) > good.migrate(good.workspace(tmp_path / "ws2"))["context_chars"]


def test_trap4_read_write_costs_more_than_edit(tmp_path, root):
    t = good.Tools(good.workspace(tmp_path / "ws2"))
    t.edit("src/admin.ts", "processLegacyOrder(order)", "processOrder(order)")
    t.edit("src/checkout.ts", "processLegacyOrder(", "processOrder(", replace_all=True)
    assert anti.trap4_read_write_every_change(root) > 3 * t.context_chars


def test_trap5_exam_answer_is_read_write():
    assert anti.trap5_exam_answer_after_non_unique()["exam_guide_v1_answer"].startswith("Read + Write")


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "replace_all" in capsys.readouterr().out
