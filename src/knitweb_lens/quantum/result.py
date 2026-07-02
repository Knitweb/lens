"""QuantumResult — a shareable, content-addressed execution outcome.

A result records what happened when a circuit was run: the measurement
histogram (counts), how many shots, on which backend, and by whom. It is
content-addressed under the ``lres:`` namespace so a result can be cited,
shared and verified independently of the circuit that produced it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cid import cid_of_obj


@dataclass
class QuantumResult:
    """Measurement outcome of running a circuit on a backend.

    Parameters
    ----------
    circuit_cid : CID (``lcid:``) of the circuit that was executed.
    counts      : bitstring -> shot count histogram, e.g. ``{"00": 512, "11": 512}``.
    shots       : total shots (defaults to sum of counts when omitted).
    backend_cid : CID (``lqpu:``) of the backend/system it ran on, if known.
    created     : ISO-8601 timestamp string (caller supplies; kept out of CID? no —
                  it IS part of provenance, so it is included in the CID).
    author      : public key / handle of the submitter.
    meta        : free-form extra metadata (does not affect equality semantics
                  beyond being part of the canonical CID).
    """

    circuit_cid: str
    counts: dict[str, int]
    shots: int = 0
    backend_cid: str = ""
    created: str = ""
    author: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kind: str = "result"

    def __post_init__(self) -> None:
        if not self.circuit_cid:
            raise ValueError("QuantumResult requires a circuit_cid")
        if not isinstance(self.counts, dict) or not self.counts:
            raise ValueError("QuantumResult requires a non-empty counts histogram")
        for k, v in self.counts.items():
            if not isinstance(k, str) or not isinstance(v, int) or v < 0:
                raise ValueError(f"invalid counts entry: {k!r} -> {v!r}")
        if not self.shots:
            self.shots = sum(self.counts.values())
        if self.shots <= 0:
            raise ValueError("QuantumResult requires a positive shot count")
        if self.shots < sum(self.counts.values()):
            raise ValueError("shots cannot be smaller than total counts")

    # ------------------------------------------------------------------ CID
    def _cid_payload(self) -> dict:
        """The canonical, CID-defining view (excludes derived/display fields)."""
        return {
            "kind": "result",
            "circuit_cid": self.circuit_cid,
            "counts": self.counts,
            "shots": self.shots,
            "backend_cid": self.backend_cid,
            "created": self.created,
            "author": self.author,
            "meta": self.meta,
        }

    @property
    def cid(self) -> str:
        return cid_of_obj(self._cid_payload(), prefix="lres:")

    # ------------------------------------------------------------------ IO
    def to_dict(self) -> dict:
        d = self._cid_payload()
        d["cid"] = self.cid
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "QuantumResult":
        return cls(
            circuit_cid=d["circuit_cid"],
            counts={str(k): int(v) for k, v in d["counts"].items()},
            shots=int(d.get("shots", 0)),
            backend_cid=d.get("backend_cid", ""),
            created=d.get("created", ""),
            author=d.get("author", ""),
            meta=d.get("meta", {}),
        )

    # ------------------------------------------------------------------ derived
    @property
    def most_frequent(self) -> str:
        """The bitstring with the highest count (ties broken lexicographically)."""
        return max(sorted(self.counts), key=lambda k: self.counts[k])

    def probabilities(self) -> dict[str, float]:
        total = self.shots or sum(self.counts.values()) or 1
        return {k: v / total for k, v in self.counts.items()}

    def __repr__(self) -> str:
        return (f"<QuantumResult circuit={self.circuit_cid[:14]}… "
                f"shots={self.shots} outcomes={len(self.counts)} cid={self.cid[:14]}…>")
