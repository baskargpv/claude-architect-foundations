from domain5_context_reliability.task_5_5_human_review_calibration import anti_pattern as anti
from domain5_context_reliability.task_5_5_human_review_calibration import good_example as good

RECORDS = good.generate()


def test_step1_records_have_values_confidence_and_four_types():
    assert {r["doc_type"] for r in RECORDS} == set(good.VOLUME) and all(0 < r["confidence"] < 1 for r in RECORDS)


def test_step2_aggregate_hides_bad_segments():
    acc = good.accuracy_by_segment(RECORDS)
    assert acc["aggregate"] > 0.94
    assert acc["by_segment"][("international", "date")] < 0.6


def test_step3_thresholds_differ_by_segment():
    th = good.thresholds(good.calibration(RECORDS))
    assert th[("standard_invoice", "date")] is not None
    assert th[("international", "amount")] is None  # never safe to automate


def test_step4_stratified_sample_includes_high_confidence_from_every_type():
    sample = good.stratified_sample(RECORDS)
    high = {r["doc_type"] for r in sample if r["confidence"] >= 0.95}
    assert high == set(good.VOLUME)


def test_step5_queue_pops_lowest_confidence_first_and_reorders_dynamically():
    q = good.ReviewQueue()
    q.push({"id": "a", "field": "date", "confidence": 0.9})
    q.push({"id": "b", "field": "date", "confidence": 0.6})
    first = q.pop()
    q.push({"id": "c", "field": "date", "confidence": 0.5})  # arrives later, jumps the queue
    assert first["id"] == "b" and q.pop()["id"] == "c"


def test_trap1_aggregate_automation_ships_errors():
    r = anti.trap1_automate_on_aggregate(RECORDS)
    assert r["wrong_but_automated"] > 50 and r["of_which_international_amounts"] > 50


def test_trap2_low_confidence_sampling_misses_novel_errors():
    assert anti.trap2_sample_low_confidence_only(RECORDS)["novel_high_confidence_errors_seen"] == 0


def test_trap3_same_raw_band_different_accuracy():
    acc = anti.trap3_raw_confidence(RECORDS)["actual_accuracy"]
    assert max(acc.values()) - min(acc.values()) > 0.01


def test_trap4_prioritising_beats_even_split():
    r = anti.trap4_even_split(RECORDS)
    assert r["errors_caught_lowest_confidence_first"] > 5 * r["errors_caught_even_split"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "aggregate accuracy" in capsys.readouterr().out
