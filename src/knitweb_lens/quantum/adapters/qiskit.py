"""Qiskit adapter — requires `pip install knitweb-lens[qiskit]`."""
from __future__ import annotations


def convert(qc, *, name: str | None = None, domain: str = "algorithms",
            tags: list[str] | None = None, description: str = "",
            author: str = "") -> "QuantumCircuit":
    try:
        from qiskit import qasm2
    except ImportError as e:
        raise ImportError("Install Qiskit: pip install knitweb-lens[qiskit]") from e

    from ..circuit import QuantumCircuit, CircuitMeta

    qasm_str = qasm2.dumps(qc)
    n = qc.num_qubits
    d = qc.depth()
    meta = CircuitMeta(
        name=name or qc.name or "qiskit_circuit",
        qubits=n, depth=d,
        tags=tags or ["qiskit"],
        domain=domain,
        source_lang="qiskit",
        description=description, author=author,
    )
    return QuantumCircuit(meta=meta, qasm=qasm_str)
