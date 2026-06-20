"""Lens: pure-Python interpret sessions over Knitweb fabric data."""

from .adapters import (
    ActivityStreamsAdapter,
    FabricWebAdapter,
    InteractionLogAdapter,
    JsonLdAdapter,
    LocalFilesAdapter,
    MappingRowsAdapter,
    OriginTrailUALAdapter,
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
from .pulse import inspect_pulse_export, pulse_export_issues, validate_pulse_export_shape
from .prompts import render_model_prompt
from .retriever import Retriever
from .reliability import ReliabilityReport, abstention_text, evaluate_session
from .rlm import LLMAdapter, OfflineLLMAdapter, RLMHarness
from .types import Chunk, ChunkRef, InterpretAnswer, InterpretSession, RankedChunk

__all__ = [
    "ActivityStreamsAdapter",
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
    "OriginTrailUALAdapter",
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
    "inspect_pulse_export",
    "load_eval_cases",
    "pulse_export_issues",
    "run_eval",
    "render_model_prompt",
    "session_from_context",
    "session_markdown",
    "validate_pulse_export_shape",
]

__version__ = "0.1.0"
