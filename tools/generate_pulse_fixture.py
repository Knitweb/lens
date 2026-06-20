#!/usr/bin/env python3
"""Generate a Lens test fixture from Pulse/Knitweb ``export_web``.

The generated JSON is checked into Lens, but Pulse remains an optional external
producer. Lens tests consume the fixture as data and do not import Knitweb.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _default_pulse_src() -> Path | None:
    candidate = Path(__file__).resolve().parents[2] / "pulse" / "src"
    return candidate if candidate.exists() else None


def _load_pulse(pulse_src: str | None) -> tuple[Any, Any]:
    source = Path(pulse_src).resolve() if pulse_src else _default_pulse_src()
    if source is not None:
        sys.path.insert(0, str(source))
    from knitweb.fabric.jsonld import export_web
    from knitweb.fabric.web import Web

    return Web, export_web


def build_fixture(pulse_src: str | None = None) -> dict[str, Any]:
    Web, export_web = _load_pulse(pulse_src)
    web = Web()
    fabric = web.weave(
        {
            "kind": "knowledge",
            "title": "Pulse export fixture root",
            "body": "Pulse export_web produced this content-addressed source record for Lens tests.",
            "tags": ["pulse", "fixture"],
        }
    )
    lens = web.weave(
        {
            "kind": "knowledge",
            "title": "Lens compatibility evidence",
            "body": "Lens reads Pulse JSON-LD exports as read-only evidence and preserves citations.",
            "tags": ["lens", "interpret"],
        }
    )
    interaction = web.weave(
        {
            "kind": "knowledge",
            "title": "Human agent interpretation note",
            "body": "Human and agent interaction context can be cited without becoming a fabric store.",
            "tags": ["human-agent", "citation"],
        }
    )
    web.link(lens, fabric, "derived-from", weight=2, metadata={"reputation": 9})
    web.link(interaction, lens, "supports", weight=3, metadata={"deploy-location": "lens-fixture"})
    return export_web(web)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Pulse export fixture for Lens")
    parser.add_argument("--pulse-src", help="Path to a Pulse/Knitweb src directory")
    parser.add_argument("--out", default="tests/fixtures/pulse_real_web_export.json")
    args = parser.parse_args(argv)
    doc = build_fixture(args.pulse_src)
    Path(args.out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
