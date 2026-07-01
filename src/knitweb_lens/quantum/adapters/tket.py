"""Pytket adapter — requires `pip install knitweb-lens[tket]`."""
from __future__ import annotations


def convert(circuit, *, name: str = "tket_circuit", domain: str = "algorithms",
            tags: list[str] | None = None, description: str = "",
            author: str = "") -> "QuantumCircuit":
    try:
        from pytket.qasm import circuit_to_qasm_str
    except ImportError as e:
        raise ImportError("Install pytket: pip install knitweb-lens[tket]") from e

    from ..circuit import QuantumCircuit, CircuitMeta

    qasm_str = circuit_to_qasm_str(circuit)
    n = circuit.n_qubits
    d = circuit.depth()
    meta = CircuitMeta(
        name=name, qubits=n, depth=d,
        tags=tags or ["tket"], domain=domain,
        source_lang="tket",
        description=description, author=author,
    )
    return QuantumCircuit(meta=meta, qasm=qasm_str)
