"""Portable Lens context bundles and citation rendering."""

from __future__ import annotations

from typing import Any, Sequence

from .reliability import abstention_text, evaluate_session
from .rlm import LLMAdapter, OfflineLLMAdapter
from .types import Chunk, ChunkRef, InterpretAnswer, InterpretSession, RankedChunk

CONTEXT_FORMAT = "knitweb-lens-context"
CONTEXT_VERSION = 1


def context_bundle(session: InterpretSession) -> dict[str, Any]:
    """Return a stable JSON-serializable context bundle for a session."""
    return {
        "format": CONTEXT_FORMAT,
        "version": CONTEXT_VERSION,
        "session": session.to_dict(),
    }


def session_from_context(bundle: dict[str, Any]) -> InterpretSession:
    """Rebuild an InterpretSession from a Lens context bundle."""
    if bundle.get("format") != CONTEXT_FORMAT:
        raise ValueError("not a Knitweb Lens context bundle")
    if bundle.get("version") != CONTEXT_VERSION:
        raise ValueError(f"unsupported Lens context version: {bundle.get('version')!r}")
    return session_from_dict(bundle["session"])


def answer_from_context(
    bundle: dict[str, Any],
    *,
    llm: LLMAdapter | None = None,
    source_trust: dict[str, int] | None = None,
) -> InterpretAnswer:
    session = session_from_context(bundle)
    model = llm or OfflineLLMAdapter()
    report = evaluate_session(session, source_trust=source_trust)
    if report.abstained:
        text = abstention_text(report)
    else:
        text = model.complete(session.query, session.ranked_chunks)
    return InterpretAnswer(
        query=session.query,
        text=text,
        session=session,
        reliability=report.to_dict(),
    )


def session_from_dict(value: dict[str, Any]) -> InterpretSession:
    return InterpretSession(
        query=value["query"],
        session_id=value["session_id"],
        ranked_chunks=tuple(ranked_chunk_from_dict(item) for item in value.get("ranked_chunks", ())),
        budget_chars=int(value["budget_chars"]),
        max_chunks=int(value["max_chunks"]),
    )


def ranked_chunk_from_dict(value: dict[str, Any]) -> RankedChunk:
    return RankedChunk(
        chunk=chunk_from_dict(value["chunk"]),
        score=int(value["score"]),
        lexical_score=int(value["lexical_score"]),
        provenance_score=int(value["provenance_score"]),
        priority_score=int(value["priority_score"]),
        weight_score=int(value["weight_score"]),
    )


def chunk_from_dict(value: dict[str, Any]) -> Chunk:
    metadata = value.get("metadata") or {}
    return Chunk(
        ref=chunk_ref_from_dict(value["ref"]),
        text=value["text"],
        title=value.get("title", ""),
        record=value.get("record"),
        priority=int(value.get("priority", 50)),
        weight=int(value.get("weight", 1)),
        distance=int(value.get("distance", 0)),
        metadata=metadata,
    )


def chunk_ref_from_dict(value: dict[str, Any]) -> ChunkRef:
    return ChunkRef(
        source_id=value["source_id"],
        source_uri=value.get("source_uri", ""),
        cid=value.get("cid"),
        node_id=value.get("node_id"),
        relation_path=tuple(value.get("relation_path") or ()),
    )


def citation_lines(refs: Sequence[ChunkRef]) -> tuple[str, ...]:
    lines: list[str] = []
    for index, ref in enumerate(refs, start=1):
        identity = ref.cid or ref.node_id or ""
        parts = [f"[{index}]", ref.source_id]
        if ref.source_uri:
            parts.append(ref.source_uri)
        if identity:
            parts.append(identity)
        if ref.relation_path:
            parts.append("path=" + " | ".join(ref.relation_path))
        lines.append(" ".join(parts))
    return tuple(lines)


def citations_markdown(refs: Sequence[ChunkRef]) -> str:
    if not refs:
        return "No citations."
    return "\n".join(f"- {line}" for line in citation_lines(refs))


def session_markdown(session: InterpretSession) -> str:
    lines = [
        f"# Lens Context: {session.session_id}",
        "",
        f"Query: `{session.query}`",
        "",
        f"Budget: {session.used_chars}/{session.budget_chars} chars, {len(session.ranked_chunks)}/{session.max_chunks} chunks",
        "",
        "## Citations",
        "",
        citations_markdown(session.citations),
        "",
        "## Ranked Chunks",
        "",
    ]
    for index, item in enumerate(session.ranked_chunks, start=1):
        chunk = item.chunk
        lines.extend(
            [
                f"### {index}. {chunk.title or chunk.ref.cid or chunk.ref.node_id or chunk.ref.source_id}",
                "",
                f"Score: {item.score} (lexical {item.lexical_score}, priority {item.priority_score}, provenance {item.provenance_score}, weight {item.weight_score})",
                "",
                "```text",
                chunk.text,
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def answer_markdown(answer: InterpretAnswer) -> str:
    reliability = answer.reliability or {}
    return "\n".join(
        [
            f"# Lens Answer: {answer.session.session_id}",
            "",
            f"Query: `{answer.query}`",
            "",
            "## Reliability",
            "",
            f"Confidence: {reliability.get('confidence', 'n/a')}",
            "",
            f"Abstained: {reliability.get('abstained', 'n/a')}",
            "",
            f"Reason: {reliability.get('reason', 'n/a')}",
            "",
            "## Answer",
            "",
            answer.text,
            "",
            "## Citations",
            "",
            citations_markdown(answer.citations),
            "",
        ]
    )
