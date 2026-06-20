"""Source adapters that normalize external stores into Lens chunks."""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import Any, Iterable, Protocol

from .types import Chunk, ChunkRef
from .util import chunk_text, read_json, record_to_text, record_title, stable_id

_HTML_TAG_RE = re.compile(r"<[^>]+>")

_ACTIVITYSTREAMS_TYPES = {
    "Accept",
    "Activity",
    "Add",
    "Announce",
    "Application",
    "Article",
    "Audio",
    "Block",
    "Collection",
    "CollectionPage",
    "Create",
    "Delete",
    "Dislike",
    "Document",
    "Event",
    "Flag",
    "Follow",
    "Group",
    "Ignore",
    "Image",
    "IntransitiveActivity",
    "Invite",
    "Join",
    "Leave",
    "Like",
    "Listen",
    "Mention",
    "Move",
    "Note",
    "Object",
    "Offer",
    "OrderedCollection",
    "OrderedCollectionPage",
    "Organization",
    "Page",
    "Person",
    "Place",
    "Profile",
    "Question",
    "Read",
    "Reject",
    "Relationship",
    "Remove",
    "Service",
    "TentativeAccept",
    "TentativeReject",
    "Tombstone",
    "Travel",
    "Undo",
    "Update",
    "Video",
    "View",
}


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


def _row_type(row: dict[str, Any]) -> str | None:
    for key in ("atom_type", "type", "kind"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _metadata(**values: str | int | None) -> tuple[tuple[str, str | int | None], ...]:
    return tuple(sorted(values.items()))


def _iter_values(value: Any) -> Iterable[Any]:
    if isinstance(value, (list, tuple)):
        yield from value
    elif value is not None:
        yield value


def _type_name(value: Any) -> str:
    first = next(_iter_values(value), None)
    return str(first).strip() if first is not None else ""


def _plain_text(value: str) -> str:
    without_tags = _HTML_TAG_RE.sub(" ", value)
    return " ".join(unescape(without_tags).split())


def _value_id(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("id", "@id", "href", "url", "name"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return None


def _append_relation(path: list[str], rel: str, value: Any) -> None:
    for item in _iter_values(value):
        identifier = _value_id(item)
        if identifier:
            path.append(f"{rel}->{identifier}")


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


def _origintrail_ual(asset: dict[str, Any]) -> str:
    for key in ("ual", "UAL", "assetUAL", "asset_ual"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    value = asset.get("@id")
    if isinstance(value, str) and value.strip().casefold().startswith("did:dkg:"):
        return value.strip()
    return ""


def _origintrail_assets(data: dict[str, Any] | Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    if isinstance(data, dict):
        raw_assets: Any = data.get("assets")
        if raw_assets is None:
            raw_assets = data.get("knowledgeAssets")
        if raw_assets is None:
            raw_assets = [data]
    else:
        raw_assets = data
    if not isinstance(raw_assets, Iterable):
        raise ValueError("OriginTrail assets must be objects")
    assets: list[dict[str, Any]] = []
    for asset in raw_assets:
        if not isinstance(asset, dict):
            raise ValueError("OriginTrail assets must be objects")
        assets.append(asset)
    return tuple(assets)


def _looks_like_origintrail_asset(data: dict[str, Any]) -> bool:
    has_ual = bool(_origintrail_ual(data))
    return has_ual and any(
        key in data
        for key in (
            "@graph",
            "assertion",
            "assertionId",
            "assertion_id",
            "graph",
            "knowledgeAsset",
            "public",
            "publicAssertion",
            "public_assertion",
        )
    )


def _origintrail_records(asset: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    for key in (
        "publicAssertion",
        "public_assertion",
        "assertion",
        "graph",
        "knowledgeAsset",
        "public",
    ):
        value = asset.get(key)
        if isinstance(value, dict) and isinstance(value.get("@graph"), list):
            return tuple(item for item in value["@graph"] if isinstance(item, dict))
        if isinstance(value, list):
            return tuple(item for item in value if isinstance(item, dict))
        if isinstance(value, dict):
            return (value,)
    graph = asset.get("@graph")
    if isinstance(graph, list):
        return tuple(item for item in graph if isinstance(item, dict))
    return (asset,)


def _origintrail_relation_path(record: dict[str, Any]) -> tuple[str, ...]:
    path = list(_edge_path(record.get("edges") or record.get("relationships") or ()))
    for rel, key in (
        ("same-as", "sameAs"),
        ("subject", "subject"),
        ("predicate", "predicate"),
        ("object", "object"),
    ):
        _append_relation(path, rel, record.get(key))
    return tuple(dict.fromkeys(path))


class OriginTrailUALAdapter:
    """Adapter for already-resolved OriginTrail Knowledge Asset snapshots.

    This preserves UALs as citations. It does not resolve UALs, publish assets,
    anchor assertions, run SPARQL, or connect to a DKG node.
    """

    def __init__(
        self,
        assets: dict[str, Any] | Iterable[dict[str, Any]],
        *,
        source_id: str = "origintrail-ual",
        source_uri: str = "",
        priority: int = 64,
    ) -> None:
        self._assets = _origintrail_assets(assets)
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for asset_index, asset in enumerate(self._assets):
            ual = _origintrail_ual(asset)
            asset_id = str(asset.get("asset_id") or asset.get("assetId") or asset.get("id") or ual)
            assertion_id = asset.get("assertion_id") or asset.get("assertionId")
            for record_index, record in enumerate(_origintrail_records(asset)):
                text = record_to_text(record)
                if not text.strip():
                    continue
                node_id = str(
                    record.get("id")
                    or record.get("@id")
                    or record.get("cid")
                    or stable_id("origintrail-record", {"ual": ual, "record": record})
                )
                ref = ChunkRef(
                    source_id=self._source_id,
                    source_uri=ual or self._source_uri,
                    cid=str(record["cid"]) if record.get("cid") else None,
                    node_id=node_id,
                    relation_path=_origintrail_relation_path(record),
                )
                yield Chunk(
                    ref=ref,
                    title=record_title(record, fallback=node_id),
                    text=text,
                    record=record,
                    priority=self._priority,
                    weight=int(asset.get("weight", 1)),
                    distance=int(asset.get("distance", 0)),
                    metadata=_metadata(
                        adapter="origintrail-ual",
                        asset_id=asset_id or None,
                        asset_index=asset_index,
                        assertion_id=str(assertion_id) if assertion_id is not None else None,
                        record_index=record_index,
                        ual=ual or None,
                    ),
                )


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


def _activitystreams_context(value: Any) -> bool:
    for item in _iter_values(value):
        if isinstance(item, str) and "activitystreams" in item.casefold():
            return True
        if isinstance(item, dict):
            if any(isinstance(part, str) and "activitystreams" in part.casefold() for part in item.values()):
                return True
    return False


def _looks_like_activitystreams(data: dict[str, Any]) -> bool:
    if _activitystreams_context(data.get("@context")):
        return True
    activity_type = _type_name(data.get("type") or data.get("@type"))
    if activity_type in {"Collection", "OrderedCollection", "CollectionPage", "OrderedCollectionPage"}:
        return "items" in data or "orderedItems" in data
    return activity_type in _ACTIVITYSTREAMS_TYPES and any(
        key in data for key in ("actor", "object", "published", "inReplyTo", "target", "to", "cc")
    )


def _activitystreams_items(doc: dict[str, Any] | list[Any]) -> tuple[dict[str, Any], ...]:
    if isinstance(doc, list):
        raw_items = doc
    elif isinstance(doc, dict):
        raw_items = doc.get("orderedItems") or doc.get("items")
        if raw_items is None:
            raw_items = [doc]
    else:
        raise ValueError("ActivityStreams document must be an object or list")
    if not isinstance(raw_items, list):
        raise ValueError("ActivityStreams items must be a list")
    items: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("ActivityStreams items must be objects")
        items.append(item)
    return tuple(items)


def _activitystreams_text(item: dict[str, Any]) -> str:
    containers: list[dict[str, Any]] = [item]
    obj = item.get("object")
    if isinstance(obj, dict):
        containers.append(obj)
    parts: list[str] = []
    for container in containers:
        for key in ("content", "summary", "name"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                text = _plain_text(value)
                if text and text not in parts:
                    parts.append(text)
        source = container.get("source")
        if isinstance(source, dict):
            value = source.get("content")
            if isinstance(value, str) and value.strip():
                text = _plain_text(value)
                if text and text not in parts:
                    parts.append(text)
    if parts:
        return "\n\n".join(parts)
    return record_to_text(item)


def _activitystreams_relation_path(item: dict[str, Any]) -> tuple[str, ...]:
    path: list[str] = []
    containers: list[dict[str, Any]] = [item]
    obj = item.get("object")
    if isinstance(obj, dict):
        containers.append(obj)
    _append_relation(path, "actor", item.get("actor"))
    _append_relation(path, "object", item.get("object"))
    for rel, key in (
        ("attributed-to", "attributedTo"),
        ("targets", "target"),
        ("context", "context"),
        ("reply-to", "inReplyTo"),
        ("audience-to", "to"),
        ("audience-cc", "cc"),
        ("tag", "tag"),
    ):
        for container in containers:
            _append_relation(path, rel, container.get(key))
    return tuple(dict.fromkeys(path))


def _activitystreams_actor(item: dict[str, Any]) -> str | None:
    actor = _value_id(item.get("actor")) or _value_id(item.get("attributedTo"))
    obj = item.get("object")
    if actor is None and isinstance(obj, dict):
        actor = _value_id(obj.get("attributedTo"))
    return actor


class ActivityStreamsAdapter:
    """Adapter for read-only ActivityStreams objects and collections.

    This reads ActivityStreams JSON as evidence. It does not implement
    ActivityPub delivery, inbox/outbox side effects, federation, or moderation.
    """

    def __init__(
        self,
        doc: dict[str, Any] | list[Any],
        *,
        source_id: str = "activitystreams",
        source_uri: str = "",
        priority: int = 62,
    ) -> None:
        self._doc = doc
        self._source_id = source_id
        self._source_uri = source_uri
        self._priority = priority

    @property
    def source_id(self) -> str:
        return self._source_id

    def iter_chunks(self) -> Iterable[Chunk]:
        for index, item in enumerate(_activitystreams_items(self._doc)):
            text = _activitystreams_text(item)
            if not text.strip():
                continue
            obj = item.get("object")
            activity_type = _type_name(item.get("type") or item.get("@type")) or "Activity"
            object_type = _type_name(obj.get("type") or obj.get("@type")) if isinstance(obj, dict) else ""
            node_id = _value_id(item) or stable_id("activitystreams-item", item)
            actor = _activitystreams_actor(item)
            published = item.get("published") or item.get("updated")
            title = item.get("name")
            if not isinstance(title, str) or not title.strip():
                title = " ".join(part for part in (activity_type, object_type) if part).strip() or node_id
            ref = ChunkRef(
                source_id=self._source_id,
                source_uri=str(item.get("source_uri") or self._source_uri),
                cid=str(item["cid"]) if item.get("cid") else None,
                node_id=node_id,
                relation_path=_activitystreams_relation_path(item),
            )
            yield Chunk(
                ref=ref,
                title=title,
                text=text,
                record=item,
                priority=self._priority,
                weight=int(item.get("weight", 1)),
                distance=int(item.get("distance", 0)),
                metadata=_metadata(
                    index=index,
                    adapter="activitystreams",
                    activity_type=activity_type,
                    actor=actor,
                    published=str(published) if published is not None else None,
                ),
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
                if isinstance(data, dict) and _looks_like_origintrail_asset(data):
                    adapter = OriginTrailUALAdapter(
                        data,
                        source_id=f"{self._source_id}:{path.name}",
                        source_uri=str(path),
                        priority=self._priority,
                    )
                    yield from adapter.iter_chunks()
                    continue
                if isinstance(data, dict) and "@graph" in data:
                    adapter = JsonLdAdapter(
                        data,
                        source_id=f"{self._source_id}:{path.name}",
                        source_uri=str(path),
                        priority=self._priority,
                    )
                    yield from adapter.iter_chunks()
                    continue
                if isinstance(data, dict) and _looks_like_activitystreams(data):
                    adapter = ActivityStreamsAdapter(
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
                if isinstance(data, dict) and "rows" in data:
                    rows = data.get("rows")
                    if not isinstance(rows, list):
                        raise ValueError("mapping rows JSON rows must be a list")
                    adapter = MappingRowsAdapter(
                        rows,
                        source_id=f"{self._source_id}:{path.name}",
                        source_uri=str(path),
                        priority=self._priority,
                    )
                    yield from adapter.iter_chunks()
                    continue
                if isinstance(data, dict) and "vector_results" in data:
                    results = data.get("vector_results")
                    if not isinstance(results, list):
                        raise ValueError("vector results JSON vector_results must be a list")
                    adapter = VectorResultsAdapter(
                        results,
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
                metadata=_metadata(index=index, adapter="mapping-rows", row_type=_row_type(row)),
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
