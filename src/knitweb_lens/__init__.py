"""Lens: pure-Python interpret sessions over Knitweb fabric data."""

from .adapters import (
    FabricWebAdapter,
    InteractionLogAdapter,
    JsonLdAdapter,
    LocalFilesAdapter,
    MappingRowsAdapter,
    RdfJsonLdAdapter,
    SourceAdapter,
    VectorResultsAdapter,
)
from .capabilities import compatibility_report
from .context import (
    CONTEXT_FORMAT,
    CONTEXT_VERSION,
    answer_from_context,
    answer_markdown,
    citation_lines,
    citations_markdown,
    context_bundle,
    session_from_context,
    session_markdown,
)
from .eval import EvalCase, load_eval_cases, run_eval
from .retriever import Retriever
from .reliability import ReliabilityReport, abstention_text, evaluate_session
from .rlm import LLMAdapter, OfflineLLMAdapter, RLMHarness
from .types import Chunk, ChunkRef, InterpretAnswer, InterpretSession, RankedChunk

__all__ = [
    "Chunk",
    "ChunkRef",
    "CONTEXT_FORMAT",
    "CONTEXT_VERSION",
    "FabricWebAdapter",
    "InterpretAnswer",
    "InterpretSession",
    "InteractionLogAdapter",
    "EvalCase",
    "JsonLdAdapter",
    "LLMAdapter",
    "LocalFilesAdapter",
    "MappingRowsAdapter",
    "OfflineLLMAdapter",
    "RdfJsonLdAdapter",
    "Retriever",
    "RLMHarness",
    "ReliabilityReport",
    "RankedChunk",
    "SourceAdapter",
    "VectorResultsAdapter",
    "compatibility_report",
    "answer_from_context",
    "answer_markdown",
    "abstention_text",
    "citation_lines",
    "citations_markdown",
    "context_bundle",
    "evaluate_session",
    "load_eval_cases",
    "run_eval",
    "session_from_context",
    "session_markdown",
]

__version__ = "0.1.0"
