import json

from knitweb_lens.cli import main


def test_cli_query_json(tmp_path, capsys):
    path = tmp_path / "note.md"
    path.write_text("Lens cites source chunks.", encoding="utf-8")

    code = main(["query", "What cites source chunks?", str(path), "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["citations"]
    assert payload["session"]["ranked_chunks"]


def test_cli_context_export_render_and_answer(tmp_path, capsys):
    source = tmp_path / "note.md"
    context = tmp_path / "context.json"
    source.write_text("CLI context export can be rendered and replayed.", encoding="utf-8")

    assert main(["export-context", "What can be replayed?", str(source), "--out", str(context)]) == 0
    assert context.exists()

    assert main(["render-context", str(context), "--answer"]) == 0
    rendered = capsys.readouterr().out
    assert "## Answer" in rendered
    assert "CLI context export" in rendered

    assert main(["answer-context", str(context), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["citations"]


def test_cli_rejects_conflicting_output_flags(tmp_path, capsys):
    path = tmp_path / "note.md"
    path.write_text("Output flags are mutually exclusive.", encoding="utf-8")

    code = main(["query", "flags", str(path), "--json", "--markdown"])

    assert code == 2
    assert "cannot be used together" in capsys.readouterr().err


def test_cli_capabilities_command_is_registered(capsys):
    code = main(["capabilities"])

    assert code == 0
    assert "read-only-interpret-layer" in capsys.readouterr().out
