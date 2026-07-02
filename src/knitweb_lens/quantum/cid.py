"""Content addressing — deterministic CIDs for circuits, results and backends.

Every artifact kind gets its own CID namespace prefix so a CID is
self-describing:

    lcid:  quantum circuit  (SHA-256 of canonical QASM)
    lres:  execution result (SHA-256 of canonical JSON)
    lqpu:  backend / quantum-system descriptor (SHA-256 of canonical JSON)
"""
import hashlib
import json
from typing import Any

_PREFIX = "lcid:"   # default namespace: quantum circuits


def cid_of(content: str | bytes, prefix: str = _PREFIX) -> str:
    """Return a stable 32-char hex content ID for any string or bytes.

    The ``prefix`` selects the artifact namespace (``lcid:``/``lres:``/``lqpu:``).
    """
    if isinstance(content, str):
        content = content.encode()
    digest = hashlib.sha256(content).hexdigest()
    return prefix + digest[:32]


def canonical_json(obj: Any) -> str:
    """Deterministic JSON encoding: sorted keys, no insignificant whitespace.

    Two dicts with the same key/value content always encode to identical bytes,
    so their CID is stable regardless of construction order.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def cid_of_obj(obj: Any, prefix: str) -> str:
    """CID of an arbitrary JSON-serialisable object under ``prefix``."""
    return cid_of(canonical_json(obj), prefix=prefix)


def verify(content: str | bytes, cid: str) -> bool:
    """True iff ``content`` hashes to ``cid`` under the cid's own prefix."""
    prefix = cid.split(":", 1)[0] + ":" if ":" in cid else _PREFIX
    return cid_of(content, prefix=prefix) == cid
