from knitweb_lens import LocalFilesAdapter, RLMHarness, evaluate_session


def test_query_attaches_integer_reliability_report(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Lens preserves provenance citations for grounded answers.", encoding="utf-8")

    answer = RLMHarness().query("What preserves provenance citations?", adapters=[LocalFilesAdapter([path])])

    assert answer.reliability is not None
    assert answer.reliability["status"] == "answered"
    assert isinstance(answer.reliability["confidence"], int)
    assert answer.reliability["abstained"] is False
    assert answer.reliability["citation_count"] == 1


def test_unrelated_query_abstains_with_low_confidence(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Lens preserves provenance citations.", encoding="utf-8")

    answer = RLMHarness().query("quantum weather banana", adapters=[LocalFilesAdapter([path])])

    assert answer.reliability["abstained"] is True
    assert answer.reliability["status"] == "abstained"
    assert answer.reliability["confidence"] < 250
    assert "Insufficient grounded support" in answer.text


def test_empty_session_abstains():
    session = RLMHarness().session("anything", adapters=[])
    report = evaluate_session(session)

    assert report.abstained is True
    assert report.confidence == 0
    assert report.reason == "no cited chunks available"


def test_min_confidence_range_is_validated():
    session = RLMHarness().session("anything", adapters=[])

    try:
        evaluate_session(session, min_confidence=1001)
    except ValueError as exc:
        assert "between 0 and 1000" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_low_source_trust_can_force_abstention(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Lens preserves provenance citations.", encoding="utf-8")

    trusted = RLMHarness(source_trust={"local-files": 100}).query(
        "What preserves provenance?",
        adapters=[LocalFilesAdapter([path])],
    )
    untrusted = RLMHarness(source_trust={"local-files": 0}).query(
        "What preserves provenance?",
        adapters=[LocalFilesAdapter([path])],
    )

    assert trusted.reliability["trust_support"] == 100
    assert untrusted.reliability["trust_support"] == 0
    assert trusted.reliability["confidence"] > untrusted.reliability["confidence"]
    assert untrusted.reliability["abstained"] is True


def test_source_trust_range_is_validated(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("Lens preserves provenance citations.", encoding="utf-8")

    try:
        RLMHarness(source_trust={"local-files": 101}).query(
            "What preserves provenance?",
            adapters=[LocalFilesAdapter([path])],
        )
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("expected ValueError")
