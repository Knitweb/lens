"""Cirq adapter — requires `pip install knitweb-lens[cirq]`."""
from __future__ import annotations


def convert(circuit, *, name: str = "cirq_circuit", domain: str = "algorithms",
            tags: list[str] | None = None, description: str = "",
            author: str = "") -> "QuantumCircuit":
    try:
        import cirq
        from cirq.contrib.qasm import circuit_to_qasm
    except ImportError:
        try:
            import cirq
            from cirq.qasm import QasmOutput
            qasm_str = cirq.qasm(circuit)
        except Exception as e:
            raise ImportError("Install Cirq: pip install knitweb-lens[cirq]") from e
    else:
        qasm_str = circuit_to_qasm(circuit)

    from ..circuit import QuantumCircuit, CircuitMeta, _count_qubits, _estimate_depth

    meta = CircuitMeta(
        name=name, qubits=_count_qubits(qasm_str),
        depth=_estimate_depth(qasm_str),
        tags=tags or ["cirq"], domain=domain,
        source_lang="cirq",
        description=description, author=author,
    )
    return QuantumCircuit(meta=meta, qasm=qasm_str)
