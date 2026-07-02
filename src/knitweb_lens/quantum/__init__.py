"""knitweb_lens.quantum — quantum artifact storage, sharing and discovery.

Three content-addressed artifact kinds share one P2P store:
    lcid:  QuantumCircuit      (100 built-in circuits, QASM 2.0)
    lres:  QuantumResult       (measurement outcomes / execution results)
    lqpu:  BackendDescriptor   (quantum-system capability profiles)

Quick start:
    from knitweb_lens.quantum import library, search, Store, QuantumResult
    lib = library()          # 100 QuantumCircuit objects
    bell = lib['bell_phi_plus']
    print(bell.cid)          # lcid:...

    res = QuantumResult(circuit_cid=bell.cid, counts={"00": 500, "11": 524})
    print(res.cid)           # lres:...
"""
from .circuit import QuantumCircuit, CircuitMeta
from .result import QuantumResult
from .backend import BackendDescriptor
from .cid import cid_of, cid_of_obj, canonical_json
from .library import library, list_circuits, domains
from .store import Store
from .search import search

__all__ = [
    "QuantumCircuit", "CircuitMeta",
    "QuantumResult",
    "BackendDescriptor",
    "cid_of", "cid_of_obj", "canonical_json",
    "library", "list_circuits", "domains",
    "Store",
    "search",
]
