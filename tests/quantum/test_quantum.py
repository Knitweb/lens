"""Core tests for knitweb-lens."""
import pytest
from knitweb_lens.quantum import QuantumCircuit, CircuitMeta, cid_of, library, search
from knitweb_lens.quantum.adapters.qasm import from_qasm
from knitweb_lens.quantum.store import Store


BELL_QASM = """\
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""


def test_cid_stable():
    c1 = cid_of("hello")
    c2 = cid_of("hello")
    assert c1 == c2
    assert c1.startswith("lcid:")


def test_from_qasm():
    circ = from_qasm(BELL_QASM, name="bell", domain="fundamental", tags=["bell"])
    assert circ.meta.name == "bell"
    assert circ.meta.qubits == 2
    assert circ.cid.startswith("lcid:")


def test_circuit_to_dict_roundtrip():
    circ = from_qasm(BELL_QASM, name="bell")
    d = circ.to_dict()
    circ2 = QuantumCircuit.from_dict(d)
    assert circ2.meta.name == circ.meta.name
    assert circ2.qasm == circ.qasm


def test_library_has_100():
    lib = library()
    assert len(lib) == 100


def test_library_domains():
    lib = library()
    domains = {c.meta.domain for c in lib.values()}
    assert "fundamental" in domains
    assert "algorithms" in domains


def test_search_by_name():
    results = search("bell")
    assert any("bell" in r.get("meta", {}).get("name", "") for r in results)


def test_search_by_domain():
    results = search(domain="cryptography")
    for r in results:
        assert r.get("meta", {}).get("domain") == "cryptography"


def test_store_put_get(tmp_path):
    store = Store(root=tmp_path)
    circ = from_qasm(BELL_QASM, name="bell_test")
    cid = store.put(circ)
    assert cid.startswith("lcid:")
    circ2 = store.get(cid)
    assert circ2.meta.name == "bell_test"


def test_store_list(tmp_path):
    store = Store(root=tmp_path)
    circ = from_qasm(BELL_QASM, name="bell_list")
    store.put(circ)
    items = list(store.list())
    assert len(items) == 1


def test_store_find(tmp_path):
    store = Store(root=tmp_path)
    circ = from_qasm(BELL_QASM, name="findme", domain="fundamental", tags=["test"])
    store.put(circ)
    hits = store.find(query="findme")
    assert len(hits) == 1


# ── regression: library QASM generation bugs ────────────────────────────
def test_every_circuit_has_matching_qreg_size():
    """Every generated circuit must declare qreg q[n] matching its meta.qubits.

    Regression for the steane_7 typo `h[4];` (invalid, missing q[...]) and the
    dead duplicate steane_7 branch — guards all 100 circuits at once.
    """
    lib = library()
    for name, circ in lib.items():
        qasm = circ.qasm
        assert f"qreg q[{circ.meta.qubits}];" in qasm, f"{name}: qreg size mismatch"
        for line in qasm.splitlines():
            s = line.strip()
            if not s or s.startswith(("//", "OPENQASM", "include", "qreg", "creg", "measure", "if")):
                continue
            assert "q[" in s, f"{name}: malformed gate line {s!r}"


def test_no_out_of_range_qubit_index():
    """No gate may address a qubit index >= declared register size.

    Skips the `qreg q[N];` declaration line, where N is the size (not an index).
    """
    import re
    lib = library()
    for name, circ in lib.items():
        n = circ.meta.qubits
        for line in circ.qasm.splitlines():
            s = line.strip()
            if s.startswith(("qreg", "creg")):
                continue
            for idx in re.findall(r"q\[(\d+)\]", s):
                assert int(idx) < n, f"{name}: q[{idx}] out of range (size {n})"


def test_superdense_coding_is_valid():
    """superdense_coding must apply a Pauli in the encode step (was H;CX;CX;H no-op)."""
    lib = library()
    body = lib["superdense_coding"].qasm
    assert "x q[0];" in body
