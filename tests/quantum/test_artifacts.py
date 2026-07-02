"""Phase A tests — QuantumResult, BackendDescriptor, cross-kind store/search."""
import pytest
from knitweb_lens.quantum import (
    QuantumCircuit, QuantumResult, BackendDescriptor,
    Store, search, cid_of_obj, canonical_json,
)
from knitweb_lens.quantum.adapters.qasm import from_qasm


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


# ── QuantumResult ───────────────────────────────────────────────────────
def test_result_cid_prefix_and_determinism():
    r1 = QuantumResult(circuit_cid="lcid:abc", counts={"00": 500, "11": 524})
    r2 = QuantumResult(circuit_cid="lcid:abc", counts={"11": 524, "00": 500})  # reordered
    assert r1.cid.startswith("lres:")
    assert r1.cid == r2.cid, "CID must be order-independent (canonical JSON)"


def test_result_shots_default_and_probs():
    r = QuantumResult(circuit_cid="lcid:x", counts={"0": 25, "1": 75})
    assert r.shots == 100
    probs = r.probabilities()
    assert abs(probs["1"] - 0.75) < 1e-9
    assert r.most_frequent == "1"


def test_result_roundtrip():
    r = QuantumResult(circuit_cid="lcid:x", counts={"00": 10}, backend_cid="lqpu:y",
                      author="edwin", created="2026-07-02T00:00:00Z")
    r2 = QuantumResult.from_dict(r.to_dict())
    assert r2.cid == r.cid
    assert r2.backend_cid == "lqpu:y"


def test_result_validation():
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="", counts={"0": 1})
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="lcid:x", counts={})
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="lcid:x", counts={"0": -1})
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="lcid:x", counts={"0": 0})
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="lcid:x", counts={"0": 5}, shots=-1)
    with pytest.raises(ValueError):
        QuantumResult(circuit_cid="lcid:x", counts={"0": 5, "1": 5}, shots=9)


# ── BackendDescriptor ─────────────────────────────────────────────────────
def test_backend_cid_prefix_and_coupling_order():
    b1 = BackendDescriptor(name="q", n_qubits=3, coupling_map=[[0, 1], [1, 2]])
    b2 = BackendDescriptor(name="q", n_qubits=3, coupling_map=[[1, 2], [0, 1]])  # reordered
    assert b1.cid.startswith("lqpu:")
    assert b1.cid == b2.cid, "coupling map order must not affect CID"


def test_backend_roundtrip_and_can_run():
    b = BackendDescriptor(name="aer", provider="local", n_qubits=32,
                          native_gates=["cx", "h", "rz"], simulator=True)
    b2 = BackendDescriptor.from_dict(b.to_dict())
    assert b2.cid == b.cid
    assert b2.can_run(4) and not b2.can_run(64)


def test_backend_validation():
    with pytest.raises(ValueError):
        BackendDescriptor(name="")
    with pytest.raises(ValueError):
        BackendDescriptor(name="q", coupling_map=[[0, 1, 2]])


# ── canonical json / cid helper ──────────────────────────────────────────
def test_canonical_json_stable():
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert cid_of_obj({"a": 1}, "lres:").startswith("lres:")


# ── cross-kind store + search ─────────────────────────────────────────────
def test_store_all_three_kinds(tmp_path):
    store = Store(root=tmp_path)
    circ = from_qasm(BELL_QASM, name="bell", domain="fundamental", tags=["bell"])
    res = QuantumResult(circuit_cid=circ.cid, counts={"00": 500, "11": 524})
    bk = BackendDescriptor(name="aer_sim", provider="local", n_qubits=32)

    ccid = store.put(circ)
    rcid = store.put(res)
    bcid = store.put(bk)
    assert ccid.startswith("lcid:")
    assert rcid.startswith("lres:")
    assert bcid.startswith("lqpu:")

    # get returns the correct type per CID namespace
    assert isinstance(store.get(ccid), QuantumCircuit)
    assert isinstance(store.get(rcid), QuantumResult)
    assert isinstance(store.get(bcid), BackendDescriptor)

    # list by kind
    assert len(list(store.list(kind="circuit"))) == 1
    assert len(list(store.list(kind="result"))) == 1
    assert len(list(store.list(kind="backend"))) == 1
    assert len(list(store.list())) == 3


def test_store_find_by_kind(tmp_path):
    store = Store(root=tmp_path)
    circ = from_qasm(BELL_QASM, name="bell")
    bk = BackendDescriptor(name="ibm_kyiv", provider="IBM", n_qubits=127, simulator=False)
    store.put(circ)
    store.put(bk)

    backends = store.find(kind="backend")
    assert len(backends) == 1
    assert backends[0]["meta"]["name"] == "ibm_kyiv"

    hits = store.find(query="ibm", kind="backend")
    assert len(hits) == 1


def test_search_kind_filter_excludes_library_results():
    # library circuits are kind=circuit; searching kind=backend must skip them
    results = search(kind="backend", source="library")
    assert results == []


# ── QASM3 / STIM / QIR tagging ────────────────────────────────────────────
def test_qasm3_passthrough_keeps_source_lang():
    q3 = 'OPENQASM 3;\nqubit[2] q;\nh q[0];\ncx q[0], q[1];'
    c = from_qasm(q3, name="q3", lang="qasm3")
    assert c.meta.source_lang == "qasm3"
    assert "OPENQASM 3" in c.qasm  # verbatim, not down-converted


def test_qasm3_autodetect_downconverts():
    q3 = 'OPENQASM 3;\ninclude "stdgates.inc";\nqubit[1] q;\nh q[0];'
    c = from_qasm(q3, name="q3auto")  # no lang -> down-convert (legacy behavior)
    assert c.meta.source_lang == "qasm2"
    assert "OPENQASM 2.0" in c.qasm


def test_stim_and_qir_tagging():
    stim_body = "H 0\nCNOT 0 1\nM 0 1"
    c = from_qasm(stim_body, name="stim_bell", lang="stim")
    assert c.meta.source_lang == "stim"
    assert "stim" in c.meta.tags
    assert c.qasm == stim_body  # verbatim
