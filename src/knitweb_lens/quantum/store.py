"""P2P artifact store — local-first, with optional Knitweb fabric sync.

Stores three content-addressed artifact kinds side by side, disambiguated by
their CID prefix:

    lcid:  circuit   -> relay path /circuits/{cid}
    lres:  result    -> relay path /results/{cid}
    lqpu:  backend    -> relay path /backends/{cid}
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Iterator

_DEFAULT_DIR = Path.home() / ".knitweb_lens" / "store"

# CID prefix -> (artifact kind, relay collection path)
_PREFIX_KIND = {
    "lcid:": ("circuit", "circuits"),
    "lres:": ("result", "results"),
    "lqpu:": ("backend", "backends"),
}


def _kind_and_path(cid: str) -> tuple[str, str]:
    prefix = cid.split(":", 1)[0] + ":" if ":" in cid else "lcid:"
    return _PREFIX_KIND.get(prefix, ("circuit", "circuits"))


def _load_artifact(data: dict):
    """Reconstruct the right artifact type from a stored dict."""
    kind, _ = _kind_and_path(data.get("cid", ""))
    if kind == "result":
        from .result import QuantumResult
        return QuantumResult.from_dict(data)
    if kind == "backend":
        from .backend import BackendDescriptor
        return BackendDescriptor.from_dict(data)
    from .circuit import QuantumCircuit
    return QuantumCircuit.from_dict(data)


def _searchable(data: dict) -> dict:
    """Uniform {name, description, tags, domain, kind} view over any artifact."""
    kind, _ = _kind_and_path(data.get("cid", ""))
    if kind == "result":
        return {
            "name": data.get("circuit_cid", ""),
            "description": f"result · {data.get('shots', 0)} shots",
            "tags": ["result"],
            "domain": "result",
            "kind": "result",
        }
    if kind == "backend":
        return {
            "name": data.get("name", ""),
            "description": data.get("provider", ""),
            "tags": list(data.get("native_gates", [])) + ["backend"],
            "domain": "backend",
            "kind": "backend",
        }
    meta = dict(data.get("meta", {}))
    meta["kind"] = "circuit"
    return meta


class Store:
    """Content-addressed store for circuits, results and backends.

    Local storage at ``~/.knitweb_lens/store/<cid>.json``; remote sync via a
    Knitweb relay when ``relay`` (or ``$KNITWEB_RELAY``) is configured.
    """

    def __init__(self, root: str | Path | None = None, relay: str | None = None):
        self.root = Path(root) if root else _DEFAULT_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self.relay = relay or os.environ.get("KNITWEB_RELAY")

    # ------------------------------------------------------------------ put
    def put(self, artifact) -> str:
        """Store any artifact exposing ``.to_dict()``/``.cid``; returns its CID."""
        data = artifact.to_dict()
        cid = data["cid"]
        self._path(cid).write_text(json.dumps(data, indent=2), encoding="utf-8")
        if self.relay:
            self._push_to_relay(cid, data)
        return cid

    # ------------------------------------------------------------------ get
    def get(self, cid: str):
        """Retrieve an artifact by CID (local first, then relay).

        Returns a QuantumCircuit / QuantumResult / BackendDescriptor depending
        on the CID namespace.
        """
        path = self._path(cid)
        if not path.exists():
            if self.relay:
                self._pull_from_relay(cid, path)
            else:
                raise KeyError(f"Artifact not found: {cid}")
        return _load_artifact(json.loads(path.read_text()))

    # ------------------------------------------------------------------ list
    def list(self, kind: str = "") -> Iterator[dict]:
        """Yield ``{cid, kind, meta}`` for stored artifacts, optionally by kind."""
        for p in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(p.read_text())
            except Exception:
                continue
            cid = data.get("cid")
            if not cid:
                continue
            k, _ = _kind_and_path(cid)
            if kind and k != kind:
                continue
            yield {"cid": cid, "kind": k, "meta": _searchable(data)}

    # ------------------------------------------------------------------ search
    def find(self, query: str = "", domain: str = "", tags: list[str] | None = None,
             kind: str = "") -> list[dict]:
        results = []
        q = query.lower()
        for item in self.list(kind=kind):
            meta = item.get("meta", {})
            name = str(meta.get("name", "")).lower()
            desc = str(meta.get("description", "")).lower()
            item_tags = meta.get("tags", [])
            item_domain = meta.get("domain", "")
            if q and q not in name and q not in desc and q not in " ".join(item_tags):
                continue
            if domain and item_domain != domain:
                continue
            if tags and not any(t in item_tags for t in tags):
                continue
            results.append(item)
        return results

    # ------------------------------------------------------------------ relay
    def _push_to_relay(self, cid: str, data: dict) -> None:
        try:
            import urllib.request
            _, coll = _kind_and_path(cid)
            body = json.dumps(data).encode()
            req = urllib.request.Request(
                f"{self.relay}/{coll}/{cid}",
                data=body, method="PUT",
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            import warnings
            warnings.warn(f"Relay push failed: {e}")

    def _pull_from_relay(self, cid: str, dest: Path) -> None:
        import urllib.request
        _, coll = _kind_and_path(cid)
        url = f"{self.relay}/{coll}/{cid}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read()
        dest.write_bytes(body)

    # ------------------------------------------------------------------ helpers
    def _path(self, cid: str) -> Path:
        safe = cid.replace(":", "_")
        return self.root / f"{safe}.json"

    def __len__(self) -> int:
        return sum(1 for _ in self.root.glob("*.json"))

    def __repr__(self) -> str:
        return f"<Store root={self.root} artifacts={len(self)} relay={self.relay}>"
