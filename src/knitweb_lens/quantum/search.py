"""Search the built-in circuit library and any local/remote stores."""
from __future__ import annotations
from .library import library


def search(query: str = "", domain: str = "", tags: list[str] | None = None,
           source: str = "library") -> list[dict]:
    """Search circuits.

    Parameters
    ----------
    query   : substring match against name / description / tags
    domain  : filter by domain (fundamental, algorithms, arithmetic, ...)
    tags    : filter by tag list (any match)
    source  : "library" (built-in) | "store" (local) | "all"
    """
    results: list[dict] = []

    if source in ("library", "all"):
        for circuit in library().values():
            if _matches(circuit, query, domain, tags):
                results.append(circuit.to_dict())

    if source in ("store", "all"):
        from .store import Store
        store = Store()
        for item in store.list():
            meta = item.get("meta", {})
            if _matches_meta(meta, query, domain, tags):
                results.append(item)

    return results


def _matches(circuit, query: str, domain: str, tags: list[str] | None) -> bool:
    return _matches_meta(circuit.meta.to_dict(), query, domain, tags)


def _matches_meta(meta: dict, query: str, domain: str, tags: list[str] | None) -> bool:
    q = query.lower()
    name = meta.get("name", "").lower()
    desc = meta.get("description", "").lower()
    m_tags = meta.get("tags", [])
    m_domain = meta.get("domain", "")
    if q and q not in name and q not in desc and q not in " ".join(m_tags):
        return False
    if domain and m_domain != domain:
        return False
    if tags and not any(t in m_tags for t in tags):
        return False
    return True
