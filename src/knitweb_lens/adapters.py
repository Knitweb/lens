"""Source adapters that normalize external stores into Lens chunks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol

from .types import Chunk, ChunkRef
from .util import chunk_text, read_json, record_to_text, record_title, stable_id


class SourceAdapter(Protocol):
    """Protocol for dependency-free source adapters."""

    @property
    def source_id(self) -> str:
        ...

    def iter_chunks(self) -> Iterable[Chunk]:
        ...


def _edge_path(edges: Iterable[Any]) -> tuple[str, ...]:
    path: list[str] = []
    for edge in edges:
        if isinstance(edge, dict):
            rel = str(edge.get("rel") or edge.get("type") or edge.get("label") or "")
            dst = str(edge.get("dst") or edge.get("target") or edge.get("to") or "")
        else:
            rel = str(getattr(edge, "rel", ""))
            dst = str(getattr(edge, "dst", ""))
        if rel or dst:
            path.append(f"{rel}->{dst}" if dst else rel)
    return tuple(path)


def _metadata(**values: str | int | None) -> tuple[tuple[str, str | int | None], ...]:
    return tuple(sorted(values.items()))


class JsonLdAdapter:
    """Adapter for Pulse/Knitweb JSON-LD Web exports."""

    def __init__(
        self,
        doc: dict[str, Any],
        *,
        source_id: str = "jsonld",
        source_uri: str = "",
        priority: int = 70,
    ) -> None:
        self._doc = doc
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        graph = self._doc.get("@graph", [])
        if not isinstance(graph, list):
            raise ValueError("JSON-LD document @graph must be a list")
        for node in graph:
            if not isinstance(node, dict):
                raise ValueError("JSON-LD @graph entries must be objects")
        for index, node in enumerate(sorted(graph, key=lambda item: str(item.get("id", "")))):
            record = node.get("record", node)
            node_id = str(node.get("id") or stable_id("jsonld-node", node))
            text = record_to_text(record)
            if not text.strip():
                continue
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=self._source_uri,
                cid=node_id,
                node_id=node_id,
                relation_path=_edge_path(node.get("edges", [])),
            )
            yield Chunk(
                ref=ref,
                title=record_title(record, fallback=node_id),
                text=text,
                record=record if isinstance(record, dict) else {"value": record},
                priority=self._priority,
                weight=1,
                distance=0,
                metadata=_metadata(index=index, adapter="jsonld"),
            )


class RdfJsonLdAdapter(JsonLdAdapter):
    """Adapter for generic JSON-LD graphs that may not use Pulse's record key."""

    def __init__(
        self,
        doc: dict[str, Any],
        *,
        source_id: str = "rdf-jsonld",
        source_uri: str = "",
        priority: int = 55,
    ) -> None:
        super().__init__(doc, source_id=source_id, source_uri=source_uri, priority=priority)


class FabricWebAdapter:
    """Adapter for a Knitweb `Web`-like object without importing knitweb."""

    def __init__(self, web: Any, *, source_id: str = "fabric-web", source_uri: str = "") -> None:
        self._web = web
        self._source_id = source_id
        self._source_uri = source_uri

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        nodes: dict[str, Any] = getattr(self._web, "nodes", {})
        out_edges: dict[str, Any] = getattr(self._web, "_out", {})
        for cid in sorted(nodes.keys()):
            record = nodes[cid]
            text = record_to_text(record)
            if not text.strip():
                continue
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=self._source_uri,
                cid=cid,
                node_id=cid,
                relation_path=_edge_path(out_edges.get(cid, [])),
            )
            yield Chunk(
                ref=ref,
                title=record_title(record, fallback=cid),
                text=text,
                record=record if isinstance(record, dict) else {"value": record},
                priority=75,
                weight=1,
                distance=0,
                metadata=_metadata(adapter="fabric-web"),
            )


def _event_text(event: dict[str, Any]) -> str:
    for key in ("text", "message", "content", "body", "summary", "observation"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return record_to_text(event)


def _event_relation_path(event: dict[str, Any]) -> tuple[str, ...]:
    path: list[str] = []
    for key, rel in (
        ("in_reply_to", "reply-to"),
        ("parent_id", "reply-to"),
        ("target", "targets"),
        ("target_cid", "targets"),
        ("cid", "mentions"),
        ("tool_call_id", "tool-call"),
    ):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            path.append(f"{rel}->{value.strip()}")
    path.extend(_edge_path(event.get("edges") or event.get("relationships") or ()))
    return tuple(path)


class InteractionLogAdapter:
    """Adapter for read-only human/agent interaction logs.

    This consumes exported interaction records. It does not become a chat store,
    identity layer, agent runtime, or event bus.
    """

    def __init__(
        self,
        events: Iterable[dict[str, Any]],
        *,
        source_id: str = "interaction-log",
        source_uri: str = "",
        priority: int = 65,
    ) -> None:
        self._events = tuple(events)
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for index, event in enumerate(self._events):
            if not isinstance(event, dict):
                raise ValueError("interaction log events must be objects")
            text = _event_text(event)
            if not text.strip():
                continue
            event_id = str(event.get("id") or stable_id("interaction-event", event))
            actor = str(event.get("actor") or event.get("author") or event.get("speaker") or "")
            actor_type = str(event.get("actor_type") or event.get("role") or "unknown")
            title = event.get("title")
            if not isinstance(title, str) or not title.strip():
                title = " ".join(part for part in (actor_type, actor) if part).strip() or event_id
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=str(event.get("source_uri") or self._source_uri),
                cid=str(event["cid"]) if event.get("cid") else None,
                node_id=event_id,
                relation_path=_event_relation_path(event),
            )
            yield Chunk(
                ref=ref,
                title=title,
                text=text,
                record=event,
                priority=self._priority,
                weight=int(event.get("weight", 1)),
                distance=int(event.get("distance", 0)),
                metadata=_metadata(
                    index=index,
                    adapter="interaction-log",
                    actor=actor or None,
                    actor_type=actor_type,
                    timestamp=str(event.get("timestamp")) if event.get("timestamp") is not None else None,
                ),
            )


class LocalFilesAdapter:
    """Adapter for local Markdown, text, JSON, and JSON-LD files."""

    def __init__(
        self,
        paths: Iterable[str | Path],
        *,
        source_id: str = "local-files",
        priority: int = 45,
    ) -> None:
        self._paths = tuple(Path(path) for path in paths)
        self._source_id = source_id
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for path in sorted(self._paths, key=lambda item: str(item)):
            if not path.exists():
                raise FileNotFoundError(f"source path not found: {path}")
            if path.is_dir():
                raise IsADirectoryError(f"source path is a directory: {path}")
            if path.suffix.lower() == ".json":
                data = read_json(path)
                if isinstance(data, dict) and "@graph" in data:
                    adapter = JsonLdAdapter(
                        data,
                        source_id=f"{self._source_id}:{path.name}",
                        source_uri=str(path),
                        priority=self._priority,
                    )
                    yield from adapter.iter_chunks()
                    continue
                if isinstance(data, dict) and ("interactions" in data or "events" in data):
                    events = data.get("interactions") if "interactions" in data else data.get("events")
                    if not isinstance(events, list):
                        raise ValueError("interaction JSON events must be a list")
                    adapter = InteractionLogAdapter(
                        events,
                        source_id=f"{self._source_id}:{path.name}",
                        source_uri=str(path),
                        priority=self._priority,
                    )
                    yield from adapter.iter_chunks()
                    continue
                text = record_to_text(data)
                title = record_title(data, fallback=path.name)
                chunks = chunk_text(text)
            else:
                text = path.read_text(encoding="utf-8")
                title = path.name
                chunks = chunk_text(text)
            for index, part in enumerate(chunks):
                cid = stable_id("local-chunk", {"path": str(path), "index": index, "text": part})
                ref = ChunkRef(
                    source_id=self._source_id,
                    source_uri=str(path),
                    cid=cid,
                    node_id=f"{path.name}:{index}",
                )
                yield Chunk(
                    ref=ref,
                    title=title,
                    text=part,
                    record={"path": str(path), "chunk": index},
                    priority=self._priority,
                    weight=1,
                    distance=0,
                    metadata=_metadata(index=index, adapter="local-files"),
                )


class MappingRowsAdapter:
    """Adapter for Neo4j, LightRAG, or graph-query row dictionaries."""

    def __init__(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        source_id: str = "mapping-rows",
        source_uri: str = "",
        priority: int = 60,
    ) -> None:
        self._rows = tuple(rows)
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for index, row in enumerate(self._rows):
            text = (
                row.get("text")
                or row.get("body")
                or row.get("content")
                or row.get("description")
                or record_to_text(row)
            )
            if not isinstance(text, str) or not text.strip():
                continue
            node_id = str(row.get("cid") or row.get("id") or stable_id("row", row))
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=str(row.get("source_uri") or self._source_uri),
                cid=str(row.get("cid")) if row.get("cid") is not None else None,
                node_id=node_id,
                relation_path=_edge_path(row.get("path") or row.get("relationships") or ()),
            )
            weight = row.get("weight", 1)
            distance = row.get("distance", 0)
            yield Chunk(
                ref=ref,
                title=record_title(row, fallback=node_id),
                text=text,
                record=row,
                priority=self._priority,
                weight=int(weight),
                distance=int(distance),
                metadata=_metadata(index=index, adapter="mapping-rows"),
            )


class VectorResultsAdapter:
    """Adapter for vector-store result objects or dictionaries.

    Any floating similarity score from an external store is quantized into an
    integer `weight`. Lens never emits float ranking metadata.
    """

    def __init__(
        self,
        results: Iterable[Any],
        *,
        source_id: str = "vector-results",
        source_uri: str = "",
        priority: int = 50,
    ) -> None:
        self._results = tuple(results)
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for index, result in enumerate(self._results):
            row = result if isinstance(result, dict) else getattr(result, "__dict__", {})
            payload = row.get("payload", row)
            text = row.get("text") or payload.get("text") or payload.get("content") or record_to_text(payload)
            if not isinstance(text, str) or not text.strip():
                continue
            raw_score = row.get("score", row.get("similarity", 0))
            if isinstance(raw_score, float):
                weight = int(raw_score * 1000)
            elif isinstance(raw_score, int) and not isinstance(raw_score, bool):
                weight = raw_score
            else:
                weight = 0
            node_id = str(row.get("id") or payload.get("id") or stable_id("vector-result", row))
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=str(row.get("source_uri") or self._source_uri),
                cid=str(payload.get("cid")) if isinstance(payload, dict) and payload.get("cid") else None,
                node_id=node_id,
            )
            yield Chunk(
                ref=ref,
                title=record_title(payload, fallback=node_id),
                text=text,
                record=payload if isinstance(payload, dict) else {"value": payload},
                priority=self._priority,
                weight=weight,
                distance=0,
                metadata=_metadata(index=index, adapter="vector-results"),
            )
