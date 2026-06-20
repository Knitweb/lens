"""Command-line interface for Lens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .adapters import LocalFilesAdapter, SourceAdapter
from .capabilities import compatibility_report
from .context import answer_from_context, answer_markdown, session_from_context, session_markdown
from .eval import load_eval_cases, run_eval
from .pulse import inspect_pulse_export
from .rlm import RLMHarness
from .server import serve
from .util import stable_json


def _adapters(paths: Iterable[str]) -> list[SourceAdapter]:
    path_list = [Path(path) for path in paths]
    if not path_list:
        return []
    return [LocalFilesAdapter(path_list)]


def _print_json(value: dict) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _reject_conflicting_outputs(args: argparse.Namespace) -> None:
    if getattr(args, "json", False) and getattr(args, "markdown", False):
        raise ValueError("--json and --markdown cannot be used together")


def _write_text_or_print(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def cmd_index(args: argparse.Namespace) -> int:
    for adapter in _adapters(args.paths):
        for chunk in adapter.iter_chunks():
            print(stable_json(chunk.to_dict()))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    _reject_conflicting_outputs(args)
    harness = RLMHarness()
    answer = harness.query(
        args.query,
        adapters=_adapters(args.paths),
        max_chunks=args.max_chunks,
        budget_chars=args.budget_chars,
    )
    if args.json:
        _print_json(answer.to_dict())
    elif args.markdown:
        print(answer_markdown(answer), end="")
    else:
        print(answer.text)
        if answer.citations:
            print("\nCitations:")
            for index, ref in enumerate(answer.citations, start=1):
                print(f"[{index}] {ref.source_id} {ref.source_uri} {ref.cid or ref.node_id or ''}".rstrip())
    return 0


def cmd_session(args: argparse.Namespace) -> int:
    harness = RLMHarness()
    session = harness.session(
        args.query,
        adapters=_adapters(args.paths),
        max_chunks=args.max_chunks,
        budget_chars=args.budget_chars,
    )
    _print_json(session.to_dict())
    return 0


def cmd_export_context(args: argparse.Namespace) -> int:
    harness = RLMHarness()
    bundle = harness.export_context(
        args.query,
        adapters=_adapters(args.paths),
        max_chunks=args.max_chunks,
        budget_chars=args.budget_chars,
    )
    text = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    _write_text_or_print(text, args.out)
    return 0


def cmd_render_context(args: argparse.Namespace) -> int:
    bundle = json.loads(Path(args.context_file).read_text(encoding="utf-8"))
    if args.answer:
        text = answer_markdown(answer_from_context(bundle))
    else:
        text = session_markdown(session_from_context(bundle))
    _write_text_or_print(text, args.out)
    return 0


def cmd_answer_context(args: argparse.Namespace) -> int:
    _reject_conflicting_outputs(args)
    bundle = json.loads(Path(args.context_file).read_text(encoding="utf-8"))
    answer = answer_from_context(bundle)
    if args.json:
        _print_json(answer.to_dict())
    elif args.markdown:
        print(answer_markdown(answer), end="")
    else:
        print(answer.text)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    serve(args.paths, host=args.host, port=args.port)
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    cases = load_eval_cases(args.fixture)
    result = run_eval(cases, base_dir=args.base_dir)
    _print_json(result)
    return 0


def cmd_capabilities(args: argparse.Namespace) -> int:
    _print_json(compatibility_report())
    return 0


def cmd_inspect_pulse(args: argparse.Namespace) -> int:
    doc = json.loads(Path(args.export_file).read_text(encoding="utf-8"))
    _print_json(inspect_pulse_export(doc))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lens", description="Knitweb Lens interpret CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index", help="Normalize input files into JSONL chunks")
    index.add_argument("paths", nargs="+")
    index.set_defaults(func=cmd_index)

    query = sub.add_parser("query", help="Run an offline interpret query")
    query.add_argument("query")
    query.add_argument("paths", nargs="+")
    query.add_argument("--max-chunks", type=int, default=8)
    query.add_argument("--budget-chars", type=int, default=4000)
    query.add_argument("--json", action="store_true")
    query.add_argument("--markdown", action="store_true")
    query.set_defaults(func=cmd_query)

    session = sub.add_parser("session", help="Return the retrieved interpret session as JSON")
    session.add_argument("query")
    session.add_argument("paths", nargs="+")
    session.add_argument("--max-chunks", type=int, default=8)
    session.add_argument("--budget-chars", type=int, default=4000)
    session.set_defaults(func=cmd_session)

    context = sub.add_parser("export-context", help="Export retrieved context as JSON")
    context.add_argument("query")
    context.add_argument("paths", nargs="+")
    context.add_argument("--max-chunks", type=int, default=8)
    context.add_argument("--budget-chars", type=int, default=4000)
    context.add_argument("--out")
    context.set_defaults(func=cmd_export_context)

    render = sub.add_parser("render-context", help="Render a saved Lens context bundle")
    render.add_argument("context_file")
    render.add_argument("--answer", action="store_true", help="Render the offline answer instead of raw context")
    render.add_argument("--out")
    render.set_defaults(func=cmd_render_context)

    answer_context = sub.add_parser("answer-context", help="Answer from a saved Lens context bundle")
    answer_context.add_argument("context_file")
    answer_context.add_argument("--json", action="store_true")
    answer_context.add_argument("--markdown", action="store_true")
    answer_context.set_defaults(func=cmd_answer_context)

    server = sub.add_parser("serve", help="Serve POST /interpret over stdlib HTTP")
    server.add_argument("paths", nargs="*")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8765)
    server.set_defaults(func=cmd_serve)

    eval_parser = sub.add_parser("eval", help="Run an offline Lens eval fixture")
    eval_parser.add_argument("fixture")
    eval_parser.add_argument("--base-dir", default=".")
    eval_parser.set_defaults(func=cmd_eval)

    capabilities = sub.add_parser("capabilities", help="Print the Lens compatibility boundary")
    capabilities.set_defaults(func=cmd_capabilities)

    inspect_pulse = sub.add_parser("inspect-pulse", help="Inspect a Pulse JSON-LD export shape")
    inspect_pulse.add_argument("export_file")
    inspect_pulse.set_defaults(func=cmd_inspect_pulse)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except BrokenPipeError:
        return 1
    except Exception as exc:
        print(f"lens: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
