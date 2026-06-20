"""Prompt rendering helpers for optional live model adapters."""

from __future__ import annotations

from collections.abc import Sequence

from .types import RankedChunk


def render_model_prompt(query: str, context: Sequence[RankedChunk]) -> str:
    """Render a deterministic grounded prompt for an external model adapter.

    Lens does not ship live model clients in the base package. Optional adapters
    can use this function to preserve the same citation contract when sending
    context to OpenAI, a local model, or another completion service.
    """
    lines = [
        "Answer the query using only the cited Lens context.",
        "Preserve citation numbers in the answer.",
        "If the context is insufficient, say so.",
        "",
        f"Query: {query}",
        "",
        "Context:",
    ]
    if not context:
        lines.append("[no context]")
    for index, ranked in enumerate(context, start=1):
        chunk = ranked.chunk
        ref = chunk.ref
        identity = ref.cid or ref.node_id or ""
        lines.extend(
            [
                f"[{index}] title: {chunk.title or identity or ref.source_id}",
                f"[{index}] source_id: {ref.source_id}",
                f"[{index}] source_uri: {ref.source_uri}",
                f"[{index}] cid_or_node: {identity}",
                f"[{index}] relation_path: {' | '.join(ref.relation_path)}",
                f"[{index}] text: {chunk.text}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
