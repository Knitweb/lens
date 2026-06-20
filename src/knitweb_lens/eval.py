"""Offline evaluation helpers for Lens reliability behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .adapters import LocalFilesAdapter, SourceAdapter
from .rlm import RLMHarness


@dataclass(frozen=True)
class EvalCase:
    name: str
    query: str
    paths: tuple[str, ...] = field(default_factory=tuple)
    should_abstain: bool = False
    must_cite: tuple[str, ...] = field(default_factory=tuple)
    source_trust: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EvalCase":
        return cls(
            name=value.get("name") or value["query"],
            query=value["query"],
            paths=tuple(value.get("paths") or ()),
            should_abstain=bool(value.get("should_abstain", False)),
            must_cite=tuple(value.get("must_cite") or ()),
            source_trust={str(k): int(v) for k, v in (value.get("source_trust") or {}).items()},
        )

    def adapters(self, *, base_dir: str | Path = ".") -> list[SourceAdapter]:
        root = Path(base_dir)
        paths = [root / path for path in self.paths]
        return [LocalFilesAdapter(paths)] if paths else []


def run_eval(
    cases: Iterable[EvalCase],
    *,
    base_dir: str | Path = ".",
    harness: RLMHarness | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    totals = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "expected_abstentions": 0,
        "true_abstentions": 0,
        "false_abstentions": 0,
        "missed_abstentions": 0,
        "citation_failures": 0,
        "confidence_sum": 0,
    }
    for case in cases:
        runner = harness or RLMHarness(source_trust=case.source_trust or None)
        answer = runner.query(case.query, adapters=case.adapters(base_dir=base_dir))
        reliability = answer.reliability or {}
        abstained = bool(reliability.get("abstained", False))
        confidence = int(reliability.get("confidence", 0))
        cited_text = "\n".join(
            " ".join(
                part
                for part in (ref.source_id, ref.source_uri, ref.cid or "", ref.node_id or "")
                if part
            )
            for ref in answer.citations
        )
        missing_citations = tuple(fragment for fragment in case.must_cite if fragment not in cited_text)
        passed = (abstained == case.should_abstain) and not missing_citations

        totals["total"] += 1
        totals["confidence_sum"] += confidence
        if passed:
            totals["passed"] += 1
        else:
            totals["failed"] += 1
        if case.should_abstain:
            totals["expected_abstentions"] += 1
            if abstained:
                totals["true_abstentions"] += 1
            else:
                totals["missed_abstentions"] += 1
        elif abstained:
            totals["false_abstentions"] += 1
        if missing_citations:
            totals["citation_failures"] += 1

        rows.append(
            {
                "name": case.name,
                "query": case.query,
                "passed": passed,
                "should_abstain": case.should_abstain,
                "abstained": abstained,
                "confidence": confidence,
                "missing_citations": list(missing_citations),
                "citation_count": len(answer.citations),
                "trust_support": int(reliability.get("trust_support", 0)),
            }
        )
    total = totals["total"]
    avg_confidence = totals["confidence_sum"] // total if total else 0
    return {
        "total": total,
        "passed": totals["passed"],
        "failed": totals["failed"],
        "expected_abstentions": totals["expected_abstentions"],
        "true_abstentions": totals["true_abstentions"],
        "false_abstentions": totals["false_abstentions"],
        "missed_abstentions": totals["missed_abstentions"],
        "citation_failures": totals["citation_failures"],
        "average_confidence": avg_confidence,
        "cases": rows,
    }


def load_eval_cases(path: str | Path) -> tuple[EvalCase, ...]:
    import json

    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        values = data.get("cases", [])
    else:
        values = data
    if not isinstance(values, list):
        raise ValueError("eval fixture must be a list or an object with a cases list")
    return tuple(EvalCase.from_dict(item) for item in values)
