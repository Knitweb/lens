"""QASM 2.0 / 3.0 adapter."""
from __future__ import annotations
from ..circuit import QuantumCircuit, CircuitMeta, _count_qubits, _estimate_depth


def from_qasm(qasm: str, *, name: str = "unnamed", domain: str = "fundamental",
              tags: list[str] | None = None, description: str = "",
              author: str = "", lang: str = "") -> QuantumCircuit:
    """Parse a circuit source string into a QuantumCircuit.

    Auto-detects OpenQASM 2.0 vs 3.0. Pass ``lang="qasm3"`` to keep a QASM 3
    body verbatim (pass-through, no down-conversion), or ``lang="stim"`` /
    ``lang="qir"`` to record a non-QASM interchange format — in those cases the
    body is stored as-is and the format is recorded in ``source_lang`` and tags.
    """
    qasm = qasm.strip()
    if not qasm:
        raise ValueError("Empty QASM string")

    tags = list(tags or [])

    # Explicit non-QASM interchange formats: store verbatim, tag the format.
    if lang in ("stim", "qir"):
        if lang not in tags:
            tags.append(lang)
        meta = CircuitMeta(
            name=name, qubits=_count_qubits(qasm), depth=_estimate_depth(qasm),
            tags=tags, domain=domain, source_lang=lang,
            description=description, author=author,
        )
        return QuantumCircuit(meta=meta, qasm=qasm)

    # Detect / honor QASM version.
    if lang == "qasm3" or "OPENQASM 3" in qasm:
        source_lang = "qasm3"
        # Pass-through: keep QASM 3 verbatim unless explicitly down-converted.
        if lang == "":
            qasm = _qasm3_to_qasm2(qasm)
            source_lang = "qasm2"
    else:
        source_lang = "qasm2"

    n = _count_qubits(qasm)
    d = _estimate_depth(qasm)

    meta = CircuitMeta(
        name=name, qubits=n, depth=d,
        tags=tags, domain=domain,
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
