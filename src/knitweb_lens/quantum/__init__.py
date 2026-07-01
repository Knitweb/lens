"""knitweb_lens.quantum — quantum circuit storage, sharing and discovery.

100 built-in circuits (QASM 2.0), adapters for Qiskit/Cirq/PennyLane/pytket,
content-addressed local/P2P store, and CLI.

Quick start:
    from knitweb_lens.quantum import library, search, Store
    lib = library()          # 100 QuantumCircuit objects
    bell = lib['bell_phi_plus']
    print(bell.qasm)
    print(bell.cid)          # lcid:...
"""
from .circuit import QuantumCircuit, CircuitMeta
from .cid import cid_of
from .library import library, list_circuits, domains
from .store import Store
from .search import search

__all__ = [
    "QuantumCircuit", "CircuitMeta",
    "cid_of",
    "library", "list_circuits", "domains",
    "Store",
    "search",
]
