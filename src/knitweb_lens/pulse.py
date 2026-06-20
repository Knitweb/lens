"""Read-only Pulse/Knitweb export shape inspection."""

from __future__ import annotations

from typing import Any


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def pulse_export_issues(doc: Any) -> tuple[str, ...]:
    """Return structural compatibility issues for a Pulse JSON-LD export.

    This is not an authoritative verifier. Pulse still owns canonical CID
    recomputation, attestation checks, import/export round-trips, and mutation.
    Lens only checks whether the export can be consumed as read-only evidence.
    """
    issues: list[str] = []
    if not isinstance(doc, dict):
        return ("document must be an object",)
    graph = doc.get("@graph")
    if not isinstance(graph, list):
        return ("document @graph must be a list",)
    for node_index, node in enumerate(graph):
        path = f"@graph[{node_index}]"
        if not isinstance(node, dict):
            issues.append(f"{path} must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            issues.append(f"{path}.id must be a non-empty string")
        record = node.get("record")
        if not isinstance(record, dict):
            issues.append(f"{path}.record must be an object")
        ual = node.get("ual")
        if ual is not None and not isinstance(ual, str):
            issues.append(f"{path}.ual must be a string when present")
        edges = node.get("edges", [])
        if not isinstance(edges, list):
            issues.append(f"{path}.edges must be a list")
            continue
        for edge_index, edge in enumerate(edges):
            edge_path = f"{path}.edges[{edge_index}]"
            if not isinstance(edge, dict):
                issues.append(f"{edge_path} must be an object")
                continue
            rel = edge.get("rel")
            dst = edge.get("dst")
            if not isinstance(rel, str) or not rel.strip():
                issues.append(f"{edge_path}.rel must be a non-empty string")
            if not isinstance(dst, str) or not dst.strip():
                issues.append(f"{edge_path}.dst must be a non-empty string")
            weight = edge.get("weight", 1)
            if not _is_int(weight):
                issues.append(f"{edge_path}.weight must be an integer")
    return tuple(issues)


def validate_pulse_export_shape(doc: Any) -> None:
    """Raise ``ValueError`` if *doc* is not a Lens-compatible Pulse export."""
    issues = pulse_export_issues(doc)
    if issues:
        raise ValueError("; ".join(issues))


def inspect_pulse_export(doc: Any) -> dict[str, Any]:
    """Return a deterministic summary of a Pulse JSON-LD export shape."""
    issues = pulse_export_issues(doc)
    graph = doc.get("@graph", []) if isinstance(doc, dict) else []
    nodes = [node for node in graph if isinstance(node, dict)] if isinstance(graph, list) else []
    edge_count = 0
    relation_counts: dict[str, int] = {}
    ual_count = 0
    for node in nodes:
        if isinstance(node.get("ual"), str) and node["ual"]:
            ual_count += 1
        edges = node.get("edges", [])
        if not isinstance(edges, list):
            continue
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            edge_count += 1
            rel = edge.get("rel")
            if isinstance(rel, str) and rel:
                relation_counts[rel] = relation_counts.get(rel, 0) + 1
    return {
        "format": "pulse-jsonld-export-shape",
        "ok": not issues,
        "issues": list(issues),
        "node_count": len(nodes),
        "edge_count": edge_count,
        "ual_count": ual_count,
        "relation_counts": dict(sorted(relation_counts.items())),
        "authoritative_verification": False,
        "mutates_source_graphs": False,
    }
