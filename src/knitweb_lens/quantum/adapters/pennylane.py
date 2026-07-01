"""PennyLane adapter — requires `pip install knitweb-lens[pennylane]`."""
from __future__ import annotations


def convert(tape_or_qfunc, *, name: str = "pennylane_circuit",
            domain: str = "algorithms", tags: list[str] | None = None,
            description: str = "", author: str = "") -> "QuantumCircuit":
    try:
        import pennylane as qml
    except ImportError as e:
        raise ImportError("Install PennyLane: pip install knitweb-lens[pennylane]") from e

    from ..circuit import QuantumCircuit, CircuitMeta

    # Accept a QuantumTape or a QNode
    if hasattr(tape_or_qfunc, "operations"):
        tape = tape_or_qfunc
    elif callable(tape_or_qfunc):
        dev = qml.device("default.qubit", wires=4)
        qnode = qml.QNode(tape_or_qfunc, dev)
        qml.draw(qnode)()
        tape = qnode.tape
    else:
        raise TypeError("Pass a QuantumTape or a callable quantum function")

    n_qubits = len(tape.wires)
    depth = len(tape.operations)

    # Convert to QASM via pennylane's built-in exporter (if available)
    try:
        from pennylane.io import to_qasm
        qasm_str = to_qasm(tape)
    except Exception:
        qasm_str = _tape_to_qasm_fallback(tape)

    meta = CircuitMeta(
        name=name, qubits=n_qubits, depth=depth,
        tags=tags or ["pennylane"], domain=domain,
        source_lang="pennylane",
        description=description, author=author,
    )
    return QuantumCircuit(meta=meta, qasm=qasm_str)


def _tape_to_qasm_fallback(tape) -> str:
    """Minimal QASM 2.0 from a PennyLane tape."""
    n = len(tape.wires)
    lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{n}];', f'creg c[{n}];']
    for op in tape.operations:
        name = op.name.lower()
        wires = [str(w) for w in op.wires]
        if name in ("hadamard", "h"):
            lines.append(f"h q[{wires[0]}];")
        elif name in ("paulix", "x"):
            lines.append(f"x q[{wires[0]}];")
        elif name in ("pauliy", "y"):
            lines.append(f"y q[{wires[0]}];")
        elif name in ("pauliz", "z"):
            lines.append(f"z q[{wires[0]}];")
        elif name in ("cnot", "cx"):
            lines.append(f"cx q[{wires[0]}],q[{wires[1]}];")
        elif name in ("cz",):
            lines.append(f"cz q[{wires[0]}],q[{wires[1]}];")
        elif name in ("s",):
            lines.append(f"s q[{wires[0]}];")
        elif name in ("t",):
            lines.append(f"t q[{wires[0]}];")
        elif name in ("rx",):
            lines.append(f"rx({op.parameters[0]}) q[{wires[0]}];")
        elif name in ("ry",):
            lines.append(f"ry({op.parameters[0]}) q[{wires[0]}];")
        elif name in ("rz",):
            lines.append(f"rz({op.parameters[0]}) q[{wires[0]}];")
        elif name in ("toffoli", "ccx"):
            lines.append(f"ccx q[{wires[0]}],q[{wires[1]}],q[{wires[2]}];")
        elif name in ("swap",):
            lines.append(f"swap q[{wires[0]}],q[{wires[1]}];")
        else:
            lines.append(f"// unsupported: {name}")
    for i in range(n):
        lines.append(f"measure q[{i}] -> c[{i}];")
    return "\n".join(lines)
