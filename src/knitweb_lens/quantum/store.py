"""P2P circuit store — local-first with optional Knitweb fabric sync."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Iterator

_DEFAULT_DIR = Path.home() / ".knitweb_lens" / "store"


class Store:
    """Content-addressed circuit store.

    Local storage at ~/.knitweb_lens/store/<cid>.json
    Remote sync via Knitweb relay when `relay` is configured.
    """

    def __init__(self, root: str | Path | None = None, relay: str | None = None):
        self.root = Path(root) if root else _DEFAULT_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self.relay = relay or os.environ.get("KNITWEB_RELAY")

    # ------------------------------------------------------------------ put
    def put(self, circuit: "QuantumCircuit") -> str:
        """Store a circuit; returns its CID."""
        from .circuit import QuantumCircuit
        data = circuit.to_dict()
        cid = data["cid"]
        path = self._path(cid)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if self.relay:
            self._push_to_relay(cid, data)
        return cid

    # ------------------------------------------------------------------ get
    def get(self, cid: str) -> "QuantumCircuit":
        """Retrieve a circuit by CID (local, then relay)."""
        path = self._path(cid)
        if not path.exists():
            if self.relay:
                self._pull_from_relay(cid, path)
            else:
                raise KeyError(f"Circuit not found: {cid}")
        from .circuit import QuantumCircuit
        return QuantumCircuit.from_dict(json.loads(path.read_text()))

    # ------------------------------------------------------------------ list
    def list(self) -> Iterator[dict]:
        for p in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(p.read_text())
                yield {"cid": data.get("cid"), "meta": data.get("meta", {})}
            except Exception:
                continue

    # ------------------------------------------------------------------ search
    def find(self, query: str = "", domain: str = "", tags: list[str] | None = None) -> list[dict]:
        results = []
        q = query.lower()
        for item in self.list():
            meta = item.get("meta", {})
            name = meta.get("name", "").lower()
            desc = meta.get("description", "").lower()
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
            import urllib.request, urllib.error
            body = json.dumps(data).encode()
            req = urllib.request.Request(
                f"{self.relay}/circuits/{cid}",
                data=body, method="PUT",
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            import warnings
            warnings.warn(f"Relay push failed: {e}")

    def _pull_from_relay(self, cid: str, dest: Path) -> None:
        import urllib.request
        url = f"{self.relay}/circuits/{cid}"
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
        return f"<Store root={self.root} circuits={len(self)} relay={self.relay}>"
