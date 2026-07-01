"""Framework adapters — convert native circuits → QuantumCircuit."""
from .qasm import from_qasm, to_qasm

__all__ = ["from_qasm", "to_qasm"]


def from_qiskit(qc, **meta) -> "QuantumCircuit":
    """Convert a Qiskit QuantumCircuit to a lens QuantumCircuit."""
    from .qiskit import convert
    return convert(qc, **meta)


def from_cirq(circuit, **meta) -> "QuantumCircuit":
    from .cirq import convert
    return convert(circuit, **meta)


def from_pennylane(tape, **meta) -> "QuantumCircuit":
    from .pennylane import convert
    return convert(tape, **meta)


def from_tket(circuit, **meta) -> "QuantumCircuit":
    from .tket import convert
    return convert(circuit, **meta)
