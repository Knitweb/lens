"""Deterministic integer-scored retrieval."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .types import Chunk, RankedChunk
from .util import tokenize, unique_tokens


def _trust_score(source_id: str, source_trust: dict[str, int] | None) -> int:
    value = 50 if source_trust is None else source_trust.get(source_id, 50)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("source trust values must be int")
    if value < 0 or value > 100:
        raise ValueError("source trust values must be between 0 and 100")
    return (value - 50) * 10


class Retriever:
    """Rank chunks by lexical match, source priority, provenance, and weight."""

    def __init__(self, *, phrase_bonus: int = 40, source_trust: dict[str, int] | None = None) -> None:
        self.phrase_bonus = phrase_bonus
        self.source_trust = dict(source_trust or {})

    def _query_features(self, query: str) -> tuple[tuple[str, ...], str]:
        """Query-only derivations used by every chunk score. Hoisted out of the
        per-chunk hot path so ``rank`` computes them once, not once per chunk."""
        all_terms = tokenize(query)                      # tokenize once
        q_terms = tuple(t for t in all_terms if len(t) > 1) or tuple(all_terms)
        phrase = query.casefold().strip()
        return q_terms, phrase

    def score(self, query: str, chunk: Chunk) -> RankedChunk:
        return self._score(self._query_features(query), chunk)

    def _score(self, query_features: tuple[tuple[str, ...], str], chunk: Chunk) -> RankedChunk:
        q_terms, phrase = query_features
        text = f"{chunk.title}\n{chunk.text}"
        doc_terms = Counter(tokenize(text))
        title_terms = unique_tokens(chunk.title)

        lexical = 0
        for term in q_terms:
            lexical += doc_terms.get(term, 0) * 10
            if term in title_terms:
                lexical += 20
        if phrase and phrase in text.casefold():
            lexical += self.phrase_bonus

        priority_score = chunk.priority * 100
        weight_score = max(chunk.weight, 0) * 10
        trust_score = _trust_score(chunk.ref.source_id, self.source_trust)
        provenance_score = max(0, 100 - max(chunk.distance, 0) * 20)
        provenance_score += len(chunk.ref.relation_path) * 5
        score = lexical + priority_score + weight_score + provenance_score + trust_score
        return RankedChunk(
            chunk=chunk,
            score=score,
            lexical_score=lexical,
            provenance_score=provenance_score,
            priority_score=priority_score,
            weight_score=weight_score,
            trust_score=trust_score,
        )

    def rank(self, query: str, chunks: Iterable[Chunk]) -> tuple[RankedChunk, ...]:
        features = self._query_features(query)
        ranked = [self._score(features, chunk) for chunk in chunks]
        ranked.sort(
            key=lambda item: (
                -item.score,
                item.chunk.ref.source_id,
                item.chunk.ref.source_uri,
                item.chunk.ref.cid or "",
                item.chunk.ref.node_id or "",
                item.chunk.title,
                item.chunk.text,
            )
        )
        return tuple(ranked)

    def retrieve(self, query: str, chunks: Iterable[Chunk], *, limit: int = 8) -> tuple[RankedChunk, ...]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        return self.rank(query, chunks)[:limit]
