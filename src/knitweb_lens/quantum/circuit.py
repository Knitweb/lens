"""Canonical quantum circuit model — framework-agnostic."""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CircuitMeta:
    name: str
    qubits: int
    depth: int | None = None
    tags: list[str] = field(default_factory=list)
    domain: str = "fundamental"        # fundamental|algorithms|arithmetic|...
    source_lang: str = "qasm2"         # qasm2|qasm3|qiskit|cirq|pennylane|tket
    description: str = ""
    author: str = ""
    version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "name": self.name, "qubits": self.qubits, "depth": self.depth,
            "tags": self.tags, "domain": self.domain,
            "source_lang": self.source_lang, "description": self.description,
            "author": self.author, "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitMeta":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class QuantumCircuit:
    """Framework-agnostic quantum circuit container."""
    meta: CircuitMeta
    qasm: str                          # canonical QASM 2.0 source
    extra: dict[str, Any] = field(default_factory=dict)  # framework-native objects

    # ------------------------------------------------------------------ #
    @property
    def cid(self) -> str:
        from .cid import cid_of
        return cid_of(self.qasm)

    def to_dict(self) -> dict:
        return {"meta": self.meta.to_dict(), "qasm": self.qasm, "cid": self.cid}

    @classmethod
    def from_dict(cls, d: dict) -> "QuantumCircuit":
        return cls(meta=CircuitMeta.from_dict(d["meta"]), qasm=d["qasm"])

    @classmethod
    def from_qasm(cls, qasm: str, **meta_kwargs) -> "QuantumCircuit":
        n = _count_qubits(qasm)
        d = _estimate_depth(qasm)
        name = meta_kwargs.pop("name", "unnamed")
        return cls(meta=CircuitMeta(name=name, qubits=n, depth=d, **meta_kwargs), qasm=qasm)

    # ------------------------------------------------------------------ #
    def to_qasm(self) -> str:
        return self.qasm

    def __repr__(self) -> str:
        return f"<QuantumCircuit '{self.meta.name}' q={self.meta.qubits} cid={self.cid[:10]}…>"


# ------------------------------------------------------------------ helpers
def _count_qubits(qasm: str) -> int:
    total = 0
    for line in qasm.splitlines():
        l = line.strip()
        if l.startswith("qreg "):
            try:
                total += int(l.split("[")[1].split("]")[0])
            except Exception:
                pass
    return total or 1


def _estimate_depth(qasm: str) -> int:
    gates = [l for l in qasm.splitlines()
             if l.strip() and not l.strip().startswith(("//", "OPENQASM", "include", "qreg", "creg"))]
    return len(gates)
