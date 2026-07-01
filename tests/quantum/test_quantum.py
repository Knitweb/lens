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
