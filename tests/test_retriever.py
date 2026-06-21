from knitweb_lens import Chunk, ChunkRef, Retriever


def test_retriever_is_deterministic_and_integer_scored():
    chunks = [
        Chunk(
            ChunkRef("s", cid="b"),
            title="Other",
            text="unrelated",
            priority=10,
        ),
        Chunk(
            ChunkRef("s", cid="a", relation_path=("derived-from->root",)),
            title="Pulse fabric",
            text="Lens preserves Pulse fabric citations.",
            priority=10,
        ),
    ]

    ranked1 = Retriever().retrieve("Pulse citations", chunks, limit=2)
    ranked2 = Retriever().retrieve("Pulse citations", reversed(chunks), limit=2)

    assert [item.chunk.ref.cid for item in ranked1] == ["a", "b"]
    assert [item.chunk.ref.cid for item in ranked2] == ["a", "b"]
    assert all(isinstance(item.score, int) for item in ranked1)


def test_retriever_tie_breaks_by_source_identity():
    chunks = [
        Chunk(ChunkRef("b", cid="2"), title="same", text="same text", priority=1),
        Chunk(ChunkRef("a", cid="1"), title="same", text="same text", priority=1),
    ]

    ranked = Retriever().retrieve("same", chunks, limit=2)

    assert [item.chunk.ref.source_id for item in ranked] == ["a", "b"]


def test_retriever_source_trust_changes_ranking_with_integer_score():
    chunks = [
        Chunk(ChunkRef("low-trust", cid="low"), title="Pulse", text="Pulse evidence", priority=10),
        Chunk(ChunkRef("high-trust", cid="high"), title="Pulse", text="Pulse evidence", priority=10),
    ]

    ranked = Retriever(source_trust={"low-trust": 0, "high-trust": 100}).retrieve("Pulse", chunks, limit=2)

    assert [item.chunk.ref.source_id for item in ranked] == ["high-trust", "low-trust"]
    assert ranked[0].trust_score == 500
    assert ranked[1].trust_score == -500


def test_retriever_rejects_invalid_source_trust():
    chunks = [Chunk(ChunkRef("s", cid="a"), title="Pulse", text="Pulse evidence", priority=10)]

    try:
        Retriever(source_trust={"s": 101}).retrieve("Pulse", chunks)
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_rank_matches_per_chunk_score_after_query_hoist():
    # Regression: query tokenization/phrase are hoisted out of the per-chunk
    # hot path. The hoisted rank() path must produce results identical to
    # calling the public score() per chunk (which recomputes them).
    chunks = [
        Chunk(ChunkRef("s", cid="a"), title="Pulse fabric", text="Lens preserves Pulse citations.", priority=10),
        Chunk(ChunkRef("s", cid="b"), title="Other", text="unrelated alpha", priority=10),
        Chunk(ChunkRef("s", cid="c"), title="Pulse", text="Pulse Pulse Pulse", priority=5),
    ]
    retriever = Retriever()
    query = "Pulse citations"

    via_rank = retriever.rank(query, chunks)
    via_score = [retriever.score(query, chunk) for chunk in chunks]
    by_cid = {item.chunk.ref.cid: item for item in via_rank}

    for scored in via_score:
        hoisted = by_cid[scored.chunk.ref.cid]
        assert hoisted.score == scored.score
        assert hoisted.lexical_score == scored.lexical_score


def test_query_features_single_char_fallback_tokenizes_once():
    # Regression for the hoist: a query whose tokens are ALL single-character must fall back to the
    # raw token list (not empty) — and _query_features must tokenize the query only once.
    from knitweb_lens.retriever import Retriever
    import knitweb_lens.retriever as rmod

    calls = {"n": 0}
    real = rmod.tokenize

    def counting_tokenize(s):
        calls["n"] += 1
        return real(s)

    rmod.tokenize = counting_tokenize
    try:
        q_terms, phrase = Retriever()._query_features("a b c")  # all single-char tokens
    finally:
        rmod.tokenize = real
    assert q_terms == ("a", "b", "c"), "single-char-only query must fall back to the raw tokens"
    assert calls["n"] == 1, "query should be tokenized exactly once"
