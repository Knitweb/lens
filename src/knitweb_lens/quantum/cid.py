"""Content addressing — deterministic CID from canonical QASM."""
import hashlib


_PREFIX = "lcid:"   # lens-CID namespace


def cid_of(content: str | bytes) -> str:
    """Return a stable 32-char hex content ID for any string or bytes."""
    if isinstance(content, str):
        content = content.encode()
    digest = hashlib.sha256(content).hexdigest()
    return _PREFIX + digest[:32]


def verify(content: str | bytes, cid: str) -> bool:
    return cid_of(content) == cid
