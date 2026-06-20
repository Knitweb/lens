import json

from knitweb_lens import EvalCase, load_eval_cases, run_eval
from knitweb_lens.cli import main


def test_run_eval_reports_abstention_and_citation_results(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("Lens preserves provenance citations for grounded answers.", encoding="utf-8")
    cases = [
        EvalCase(
            name="grounded",
            query="What preserves provenance citations?",
            paths=("source.md",),
            should_abstain=False,
            must_cite=("source.md",),
        ),
        EvalCase(
            name="unsupported",
            query="quantum weather banana",
            paths=("source.md",),
            should_abstain=True,
        ),
    ]

    result = run_eval(cases, base_dir=tmp_path)

    assert result["total"] == 2
    assert result["passed"] == 2
    assert result["true_abstentions"] == 1
    assert isinstance(result["average_confidence"], int)


def test_load_eval_cases_accepts_object_with_cases(tmp_path):
    fixture = tmp_path / "eval.json"
    fixture.write_text(
        json.dumps({"cases": [{"name": "x", "query": "q", "paths": ["a.md"]}]}),
        encoding="utf-8",
    )

    cases = load_eval_cases(fixture)

    assert cases[0].name == "x"
    assert cases[0].paths == ("a.md",)


def test_cli_eval_outputs_json(tmp_path, capsys):
    source = tmp_path / "source.md"
    source.write_text("Lens preserves provenance citations.", encoding="utf-8")
    fixture = tmp_path / "eval.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "name": "grounded",
                    "query": "What preserves provenance?",
                    "paths": ["source.md"],
                    "must_cite": ["source.md"],
                }
            ]
        ),
        encoding="utf-8",
    )

    code = main(["eval", str(fixture), "--base-dir", str(tmp_path)])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] == 1


def test_eval_case_source_trust_controls_abstention(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("Lens preserves provenance citations.", encoding="utf-8")
    cases = [
        EvalCase(
            name="untrusted",
            query="What preserves provenance?",
            paths=("source.md",),
            should_abstain=True,
            source_trust={"local-files": 0},
        )
    ]

    result = run_eval(cases, base_dir=tmp_path)

    assert result["passed"] == 1
    assert result["cases"][0]["trust_support"] == 0
