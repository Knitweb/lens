"""Offline-testable RLM harness over Lens retrieval chunks."""

from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from .adapters import SourceAdapter
from .reliability import abstention_text, evaluate_session
from .retriever import Retriever
from .types import Chunk, InterpretAnswer, InterpretSession, RankedChunk
from .util import stable_id, tokenize


class LLMAdapter(Protocol):
    """Small completion protocol. Live LLMs can implement this later."""

    def complete(self, query: str, context: Sequence[RankedChunk]) -> str:
        ...


class OfflineLLMAdapter:
    """Deterministic answer synthesizer used by default and in tests."""

    def complete(self, query: str, context: Sequence[RankedChunk]) -> str:
        if not context:
            return "No grounded answer: Lens found no matching source chunks."
        terms = set(tokenize(query))
        lines: list[str] = []
        for index, ranked in enumerate(context, start=1):
            sentence = _best_sentence(ranked.chunk.text, terms)
            title = ranked.chunk.title or ranked.chunk.ref.node_id or ranked.chunk.ref.cid or ranked.chunk.ref.source_id
            lines.append(f"[{index}] {title}: {sentence}")
        return "\n".join(lines)


def _best_sentence(text: str, terms: set[str]) -> str:
    candidates = [part.strip() for part in text.replace("\n", " ").split(".") if part.strip()]
    if not candidates:
        return text.strip()[:240]
    best = max(
        candidates,
        key=lambda sentence: (
            len(set(tokenize(sentence)) & terms),
            -len(sentence),
            sentence,
        ),
    )
    if len(best) > 280:
        return best[:277].rstrip() + "..."
    return best


class RLMHarness:
    """Iterative interpret harness.

    The harness intentionally looks like a tool loop, but its default model is
    deterministic. A live adapter can be supplied without changing retrieval,
    citation, or tests.
    """

    def __init__(
        self,
        *,
        retriever: Retriever | None = None,
        llm: LLMAdapter | None = None,
        min_confidence: int = 25,
        source_trust: dict[str, int] | None = None,
    ) -> None:
        self.retriever = retriever or Retriever()
        self.llm = llm or OfflineLLMAdapter()
        self.min_confidence = min_confidence
        self.source_trust = source_trust

    def collect(self, adapters: Iterable[SourceAdapter]) -> tuple[Chunk, ...]:
        chunks: list[Chunk] = []
        for adapter in adapters:
            chunks.extend(adapter.iter_chunks())
        chunks.sort(key=lambda chunk: chunk.stable_key())
        return tuple(chunks)

    def session(
        self,
        query: str,
        *,
        adapters: Iterable[SourceAdapter],
        max_chunks: int = 8,
        budget_chars: int = 4000,
    ) -> InterpretSession:
        if max_chunks < 0:
            raise ValueError("max_chunks must be non-negative")
        if budget_chars < 0:
            raise ValueError("budget_chars must be non-negative")
        candidates = self.collect(adapters)
        ranked = self.retriever.retrieve(query, candidates, limit=max_chunks * 4 if max_chunks else 0)
        selected: list[RankedChunk] = []
        used = 0
        for item in ranked:
            if len(selected) >= max_chunks:
                break
            next_used = used + len(item.chunk.text)
            if selected and next_used > budget_chars:
                continue
            if not selected and item.chunk.text and budget_chars > 0 and next_used > budget_chars:
                selected.append(_trim_ranked(item, budget_chars))
                break
            selected.append(item)
            used = next_used
        session_id = stable_id(
            "lens-session",
            {
                "query": query,
                "chunks": [item.chunk.ref.stable_key() for item in selected],
                "budget_chars": budget_chars,
                "max_chunks": max_chunks,
            },
        )
        return InterpretSession(
            query=query,
            session_id=session_id,
            ranked_chunks=tuple(selected),
            budget_chars=budget_chars,
            max_chunks=max_chunks,
        )

    def query(
        self,
        query: str,
        *,
        adapters: Iterable[SourceAdapter],
        max_chunks: int = 8,
        budget_chars: int = 4000,
    ) -> InterpretAnswer:
        session = self.session(
            query,
            adapters=adapters,
            max_chunks=max_chunks,
            budget_chars=budget_chars,
        )
        report = evaluate_session(
            session,
            min_confidence=self.min_confidence,
            source_trust=self.source_trust,
        )
        if report.abstained:
            text = abstention_text(report)
        else:
            text = self.llm.complete(query, session.ranked_chunks)
        return InterpretAnswer(
            query=query,
            text=text,
            session=session,
            reliability=report.to_dict(),
        )

    def export_context(
        self,
        query: str,
        *,
        adapters: Iterable[SourceAdapter],
        max_chunks: int = 8,
        budget_chars: int = 4000,
    ) -> dict:
        from .context import context_bundle

        session = self.session(
            query,
            adapters=adapters,
            max_chunks=max_chunks,
            budget_chars=budget_chars,
        )
        return context_bundle(session)


def _trim_ranked(item: RankedChunk, budget_chars: int) -> RankedChunk:
    from dataclasses import replace

    trimmed_text = item.chunk.text[:budget_chars].rstrip()
    return replace(item, chunk=replace(item.chunk, text=trimmed_text))
