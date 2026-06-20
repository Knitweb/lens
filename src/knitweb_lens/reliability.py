"""Deterministic reliability reports for Lens answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .types import InterpretSession


@dataclass(frozen=True)
class ReliabilityReport:
    confidence: int
    abstained: bool
    reason: str
    citation_count: int
    source_count: int
    lexical_support: int
    provenance_support: int
    trust_support: int

    def __post_init__(self) -> None:
        for name in (
            "confidence",
            "citation_count",
            "source_count",
            "lexical_support",
            "provenance_support",
            "trust_support",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be int")

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "abstained": self.abstained,
            "reason": self.reason,
            "citation_count": self.citation_count,
            "source_count": self.source_count,
            "lexical_support": self.lexical_support,
            "provenance_support": self.provenance_support,
            "trust_support": self.trust_support,
        }


def _trust_for(source_id: str, source_trust: dict[str, int] | None) -> int:
    value = 50 if source_trust is None else source_trust.get(source_id, 50)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("source trust values must be int")
    if value < 0 or value > 100:
        raise ValueError("source trust values must be between 0 and 100")
    return value


def evaluate_session(
    session: InterpretSession,
    *,
    min_confidence: int = 250,
    source_trust: dict[str, int] | None = None,
) -> ReliabilityReport:
    if min_confidence < 0 or min_confidence > 1000:
        raise ValueError("min_confidence must be between 0 and 1000")
    ranked = session.ranked_chunks
    citation_count = len(ranked)
    if citation_count == 0:
        return ReliabilityReport(
            confidence=0,
            abstained=True,
            reason="no cited chunks available",
            citation_count=0,
            source_count=0,
            lexical_support=0,
            provenance_support=0,
            trust_support=0,
        )

    source_count = len({item.chunk.ref.source_id for item in ranked})
    lexical_support = sum(min(item.lexical_score, 200) for item in ranked) // citation_count
    provenance_support = sum(min(item.provenance_score, 150) for item in ranked) // citation_count
    trust_support = sum(_trust_for(item.chunk.ref.source_id, source_trust) for item in ranked) // citation_count
    citation_bonus = min(30, citation_count * 10)
    source_bonus = min(20, source_count * 5)

    confidence_percent = max(
        0,
        min(
            100,
            (
                (lexical_support // 4)
                + (provenance_support // 10)
                + citation_bonus
                + source_bonus
                + ((trust_support - 50) // 5)
            ),
        ),
    )
    if lexical_support == 0:
        confidence_percent = min(confidence_percent, 20)
    confidence = confidence_percent * 10

    abstained = confidence < min_confidence
    reason = "sufficient grounded support"
    if abstained:
        reason = f"confidence {confidence} below threshold {min_confidence}"
    return ReliabilityReport(
        confidence=confidence,
        abstained=abstained,
        reason=reason,
        citation_count=citation_count,
        source_count=source_count,
        lexical_support=lexical_support,
        provenance_support=provenance_support,
        trust_support=trust_support,
    )


def abstention_text(report: ReliabilityReport) -> str:
    return (
        "Insufficient grounded support to answer from the supplied Lens context. "
        f"{report.reason}."
    )
