"""QASM 2.0 / 3.0 adapter."""
from __future__ import annotations
from ..circuit import QuantumCircuit, CircuitMeta, _count_qubits, _estimate_depth


def from_qasm(qasm: str, *, name: str = "unnamed", domain: str = "fundamental",
              tags: list[str] | None = None, description: str = "",
              author: str = "") -> QuantumCircuit:
    """Parse QASM 2.0 or 3.0 string into a QuantumCircuit."""
    qasm = qasm.strip()
    if not qasm:
        raise ValueError("Empty QASM string")

    # Detect version
    source_lang = "qasm3" if "OPENQASM 3" in qasm else "qasm2"

    # Normalise to QASM 2.0 if 3.0 (best-effort)
    if source_lang == "qasm3":
        qasm = _qasm3_to_qasm2(qasm)

    n = _count_qubits(qasm)
    d = _estimate_depth(qasm)

    meta = CircuitMeta(
        name=name, qubits=n, depth=d,
        tags=tags or [], domain=domain,
        source_lang=source_lang,
        description=description, author=author,
    )
    return QuantumCircuit(meta=meta, qasm=qasm)


def to_qasm(circuit: QuantumCircuit) -> str:
    return circuit.qasm


def _qasm3_to_qasm2(src: str) -> str:
    """Best-effort QASM 3 → QASM 2 for common gates."""
    lines = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("OPENQASM 3"):
            lines.append("OPENQASM 2.0;")
        elif stripped.startswith("include"):
            lines.append('include "qelib1.inc";')
        elif stripped.startswith("bit[") or stripped.startswith("bit "):
            # creg conversion: bit[n] name; → creg name[n];
            import re
            m = re.match(r"bit\[(\d+)\]\s+(\w+)\s*;", stripped)
            if m:
                lines.append(f"creg {m.group(2)}[{m.group(1)}];")
            else:
                lines.append(line)
        elif stripped.startswith("qubit[") or stripped.startswith("qubit "):
            import re
            m = re.match(r"qubit\[(\d+)\]\s+(\w+)\s*;", stripped)
            if m:
                lines.append(f"qreg {m.group(2)}[{m.group(1)}];")
            else:
                lines.append(line)
        else:
            lines.append(line)
    return "\n".join(lines)
