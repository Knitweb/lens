"""BackendDescriptor — a shareable, content-addressed quantum-system profile.

Describes the capabilities of a quantum backend (real QPU or simulator) so
peers can decide what a node can run before sending a circuit to it. Mirrors
the capability profiles used by platforms like QCI Connect and the layered
backend interface of RFC 9340-style quantum networks. Content-addressed under
the ``lqpu:`` namespace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cid import cid_of_obj


@dataclass
class BackendDescriptor:
    """Capability profile of a quantum backend.

    Parameters
    ----------
    name         : human name, e.g. ``"ibm_kyiv"`` or ``"aer_simulator"``.
    provider     : owner/vendor, e.g. ``"IBM"``, ``"local"``.
    n_qubits     : number of qubits.
    coupling_map : list of ``[control, target]`` connected qubit pairs
                   (empty = all-to-all / not specified).
    native_gates : basis gate set the hardware executes natively.
    basis        : optional named basis-gate profile string.
    error_rates  : optional per-gate/per-qubit error rates (name -> float).
    simulator    : True for a classical simulator, False for real hardware.
    meta         : free-form extra metadata.
    """

    name: str
    provider: str = ""
    n_qubits: int = 0
    coupling_map: list[list[int]] = field(default_factory=list)
    native_gates: list[str] = field(default_factory=list)
    basis: str = ""
    error_rates: dict[str, float] = field(default_factory=dict)
    simulator: bool = True
    meta: dict[str, Any] = field(default_factory=dict)
    kind: str = "backend"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("BackendDescriptor requires a name")
        if self.n_qubits < 0:
            raise ValueError("n_qubits must be >= 0")
        # normalise coupling map to sorted list of 2-int lists for a stable CID
        norm = []
        for pair in self.coupling_map:
            if len(pair) != 2:
                raise ValueError(f"coupling_map entry must be a pair: {pair!r}")
            norm.append([int(pair[0]), int(pair[1])])
        self.coupling_map = sorted(norm)

    # ------------------------------------------------------------------ CID
    def _cid_payload(self) -> dict:
        return {
            "kind": "backend",
            "name": self.name,
            "provider": self.provider,
            "n_qubits": self.n_qubits,
            "coupling_map": self.coupling_map,
            "native_gates": sorted(self.native_gates),
            "basis": self.basis,
            "error_rates": self.error_rates,
            "simulator": self.simulator,
            "meta": self.meta,
        }

    @property
    def cid(self) -> str:
        return cid_of_obj(self._cid_payload(), prefix="lqpu:")

    # ------------------------------------------------------------------ IO
    def to_dict(self) -> dict:
        d = self._cid_payload()
        d["cid"] = self.cid
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "BackendDescriptor":
        return cls(
            name=d["name"],
            provider=d.get("provider", ""),
            n_qubits=int(d.get("n_qubits", 0)),
            coupling_map=[list(p) for p in d.get("coupling_map", [])],
            native_gates=list(d.get("native_gates", [])),
            basis=d.get("basis", ""),
            error_rates=dict(d.get("error_rates", {})),
            simulator=bool(d.get("simulator", True)),
            meta=d.get("meta", {}),
        )

    # ------------------------------------------------------------------ helpers
    def can_run(self, qubits: int) -> bool:
        """True iff this backend has at least ``qubits`` qubits."""
        return self.n_qubits >= qubits

    def __repr__(self) -> str:
        kind = "sim" if self.simulator else "qpu"
        return (f"<BackendDescriptor {self.name} [{kind}] "
                f"q={self.n_qubits} cid={self.cid[:14]}…>")
