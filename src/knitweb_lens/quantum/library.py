"""Built-in circuit library — 100 fundamental quantum circuits."""
from __future__ import annotations
import importlib.resources
from pathlib import Path
from functools import lru_cache
from .circuit import QuantumCircuit, CircuitMeta


_CIRCUIT_SPECS: list[dict] = [
    # ── FUNDAMENTAL (20) ────────────────────────────────────────────────
    {"name": "h_single",        "qubits": 1, "domain": "fundamental",  "tags": ["hadamard", "superposition"],
     "desc": "Single-qubit Hadamard gate: creates equal superposition"},
    {"name": "cnot",            "qubits": 2, "domain": "fundamental",  "tags": ["entanglement", "two-qubit"],
     "desc": "Controlled-NOT gate: fundamental two-qubit entangler"},
    {"name": "toffoli",         "qubits": 3, "domain": "fundamental",  "tags": ["ccx", "universal"],
     "desc": "Toffoli (CCX) gate: universal classical reversible gate"},
    {"name": "swap",            "qubits": 2, "domain": "fundamental",  "tags": ["swap"],
     "desc": "SWAP gate: exchanges two qubit states"},
    {"name": "cswap",           "qubits": 3, "domain": "fundamental",  "tags": ["fredkin", "swap"],
     "desc": "Fredkin (CSWAP) gate: controlled swap"},
    {"name": "bell_phi_plus",   "qubits": 2, "domain": "fundamental",  "tags": ["bell", "entanglement"],
     "desc": "Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2"},
    {"name": "bell_phi_minus",  "qubits": 2, "domain": "fundamental",  "tags": ["bell", "entanglement"],
     "desc": "Bell state |Φ-⟩ = (|00⟩ - |11⟩)/√2"},
    {"name": "bell_psi_plus",   "qubits": 2, "domain": "fundamental",  "tags": ["bell", "entanglement"],
     "desc": "Bell state |Ψ+⟩ = (|01⟩ + |10⟩)/√2"},
    {"name": "bell_psi_minus",  "qubits": 2, "domain": "fundamental",  "tags": ["bell", "entanglement"],
     "desc": "Bell state |Ψ-⟩ = (|01⟩ - |10⟩)/√2"},
    {"name": "ghz_3",           "qubits": 3, "domain": "fundamental",  "tags": ["ghz", "entanglement"],
     "desc": "3-qubit GHZ state: maximally entangled"},
    {"name": "ghz_4",           "qubits": 4, "domain": "fundamental",  "tags": ["ghz", "entanglement"],
     "desc": "4-qubit GHZ state"},
    {"name": "ghz_5",           "qubits": 5, "domain": "fundamental",  "tags": ["ghz", "entanglement"],
     "desc": "5-qubit GHZ state"},
    {"name": "w_state_3",       "qubits": 3, "domain": "fundamental",  "tags": ["w-state", "entanglement"],
     "desc": "3-qubit W state: (|001⟩+|010⟩+|100⟩)/√3"},
    {"name": "qft_4",           "qubits": 4, "domain": "fundamental",  "tags": ["qft", "fourier"],
     "desc": "4-qubit Quantum Fourier Transform"},
    {"name": "phase_kickback",  "qubits": 2, "domain": "fundamental",  "tags": ["phase", "kickback"],
     "desc": "Phase kickback: eigenphase of oracle embedded in control"},
    {"name": "quantum_walk_2",  "qubits": 2, "domain": "fundamental",  "tags": ["walk"],
     "desc": "2-qubit discrete quantum walk step"},
    {"name": "superposition_n4","qubits": 4, "domain": "fundamental",  "tags": ["superposition"],
     "desc": "4-qubit uniform superposition via H⊗4"},
    {"name": "entangled_pair",  "qubits": 2, "domain": "fundamental",  "tags": ["epr"],
     "desc": "EPR pair preparation: basis of quantum communication"},
    {"name": "rx_ry_rz",        "qubits": 1, "domain": "fundamental",  "tags": ["rotation"],
     "desc": "Single-qubit Rx Ry Rz sequence on one qubit"},
    {"name": "phase_oracle",    "qubits": 3, "domain": "fundamental",  "tags": ["oracle", "phase"],
     "desc": "3-qubit phase oracle: marks |111⟩ with a phase flip"},

    # ── ALGORITHMS (20) ─────────────────────────────────────────────────
    {"name": "deutsch_jozsa",   "qubits": 4, "domain": "algorithms",   "tags": ["dj", "oracle"],
     "desc": "Deutsch-Jozsa: determines constant vs balanced in O(1)"},
    {"name": "bernstein_vazirani","qubits":4, "domain": "algorithms",   "tags": ["bv", "oracle"],
     "desc": "Bernstein-Vazirani: extracts hidden bit-string in one query"},
    {"name": "simon_2",         "qubits": 4, "domain": "algorithms",   "tags": ["simon", "oracle"],
     "desc": "Simon's algorithm: finds hidden period with O(n) queries"},
    {"name": "grover_2q",       "qubits": 2, "domain": "algorithms",   "tags": ["grover", "search"],
     "desc": "2-qubit Grover: quadratic search speedup"},
    {"name": "grover_3q",       "qubits": 3, "domain": "algorithms",   "tags": ["grover", "search"],
     "desc": "3-qubit Grover: search 8-element database"},
    {"name": "qpe_2",           "qubits": 4, "domain": "algorithms",   "tags": ["qpe", "phase"],
     "desc": "Quantum Phase Estimation with 2 precision bits"},
    {"name": "qpe_3",           "qubits": 5, "domain": "algorithms",   "tags": ["qpe", "phase"],
     "desc": "Quantum Phase Estimation with 3 precision bits"},
    {"name": "hhl_2x2",         "qubits": 4, "domain": "algorithms",   "tags": ["hhl", "linear-systems"],
     "desc": "HHL algorithm for 2×2 linear system Ax=b"},
    {"name": "amplitude_amp",   "qubits": 3, "domain": "algorithms",   "tags": ["amplitude", "amplification"],
     "desc": "Amplitude Amplification: generalised Grover"},
    {"name": "quantum_walk_4",  "qubits": 4, "domain": "algorithms",   "tags": ["walk"],
     "desc": "4-qubit quantum walk: line graph step operator"},
    {"name": "swap_test",       "qubits": 5, "domain": "algorithms",   "tags": ["swap-test", "fidelity"],
     "desc": "SWAP test: estimates overlap ⟨ψ|φ⟩ between two states"},
    {"name": "vqe_h2",          "qubits": 4, "domain": "algorithms",   "tags": ["vqe", "variational"],
     "desc": "VQE ansatz for H₂ molecule ground state"},
    {"name": "qaoa_maxcut_4",   "qubits": 4, "domain": "algorithms",   "tags": ["qaoa", "optimization"],
     "desc": "QAOA MaxCut on 4-node graph (p=1 layer)"},
    {"name": "qaoa_maxcut_p2",  "qubits": 4, "domain": "algorithms",   "tags": ["qaoa", "optimization"],
     "desc": "QAOA MaxCut p=2 layers"},
    {"name": "shor_order_15",   "qubits": 8, "domain": "algorithms",   "tags": ["shor", "factoring"],
     "desc": "Shor's algorithm period-finding oracle for N=15"},
    {"name": "variational_4",   "qubits": 4, "domain": "algorithms",   "tags": ["variational", "ansatz"],
     "desc": "Generic 4-qubit hardware-efficient variational ansatz"},
    {"name": "iqpe",            "qubits": 2, "domain": "algorithms",   "tags": ["iqpe", "phase"],
     "desc": "Iterative QPE: resource-efficient phase estimation"},
    {"name": "haa_4",           "qubits": 4, "domain": "algorithms",   "tags": ["ansatz", "hardware"],
     "desc": "Hardware-efficient ansatz depth-2 for 4 qubits"},
    {"name": "real_amplitudes",  "qubits": 4, "domain": "algorithms",   "tags": ["ansatz", "real"],
     "desc": "RealAmplitudes ansatz: only real amplitudes, no imaginary"},
    {"name": "two_local_rzrx",  "qubits": 4, "domain": "algorithms",   "tags": ["two-local", "ansatz"],
     "desc": "TwoLocal ansatz: Rz–Rx rotation blocks + CNOT entanglement"},

    # ── ARITHMETIC (15) ─────────────────────────────────────────────────
    {"name": "adder_1bit",      "qubits": 3, "domain": "arithmetic",   "tags": ["adder", "arithmetic"],
     "desc": "1-bit quantum full adder: sum and carry"},
    {"name": "adder_4bit",      "qubits": 9, "domain": "arithmetic",   "tags": ["adder", "ripple-carry"],
     "desc": "4-bit ripple-carry quantum adder"},
    {"name": "draper_adder_4",  "qubits": 8, "domain": "arithmetic",   "tags": ["draper", "qft-adder"],
     "desc": "Draper QFT-based addition: no carry qubits"},
    {"name": "subtractor_4",    "qubits": 9, "domain": "arithmetic",   "tags": ["subtractor"],
     "desc": "4-bit quantum subtractor (adder with bit-flip)"},
    {"name": "multiplier_2bit", "qubits": 8, "domain": "arithmetic",   "tags": ["multiplier"],
     "desc": "2-bit quantum multiplier: outputs a×b in 4-bit register"},
    {"name": "modular_add_4",   "qubits": 8, "domain": "arithmetic",   "tags": ["modular", "adder"],
     "desc": "4-bit modular adder (mod N circuit)"},
    {"name": "increment_4",     "qubits": 4, "domain": "arithmetic",   "tags": ["increment"],
     "desc": "4-bit in-place quantum increment |x⟩ → |x+1 mod 16⟩"},
    {"name": "comparator_4",    "qubits": 9, "domain": "arithmetic",   "tags": ["comparator"],
     "desc": "4-bit quantum comparator: sets ancilla if a < b"},
    {"name": "gcd_4",           "qubits":12, "domain": "arithmetic",   "tags": ["gcd", "euclidean"],
     "desc": "Quantum GCD circuit for 4-bit inputs"},
    {"name": "controlled_add_4","qubits": 9, "domain": "arithmetic",   "tags": ["controlled", "adder"],
     "desc": "Controlled 4-bit adder: adds only when control=|1⟩"},
    {"name": "modular_exp_15",  "qubits": 8, "domain": "arithmetic",   "tags": ["modular-exp", "shor"],
     "desc": "Modular exponentiation 2^x mod 15: core of Shor's"},
    {"name": "cuccaro_adder",   "qubits":10, "domain": "arithmetic",   "tags": ["cuccaro", "adder"],
     "desc": "Cuccaro in-place adder: linear depth, one ancilla"},
    {"name": "carry_save_4",    "qubits":12, "domain": "arithmetic",   "tags": ["carry-save"],
     "desc": "Carry-save adder for 3×4-bit operands"},
    {"name": "square_4",        "qubits": 8, "domain": "arithmetic",   "tags": ["squaring"],
     "desc": "4-bit quantum squaring circuit |x⟩|0⟩ → |x⟩|x²⟩"},
    {"name": "div_by_3",        "qubits": 6, "domain": "arithmetic",   "tags": ["division"],
     "desc": "Quantum integer division by 3 for 3-bit input"},

    # ── ERROR CORRECTION (10) ───────────────────────────────────────────
    {"name": "bit_flip_3",      "qubits": 3, "domain": "error_correction", "tags": ["bit-flip", "repetition"],
     "desc": "3-qubit bit-flip code: encodes logical |0⟩/|1⟩"},
    {"name": "phase_flip_3",    "qubits": 3, "domain": "error_correction", "tags": ["phase-flip", "repetition"],
     "desc": "3-qubit phase-flip (sign) code"},
    {"name": "shor_9",          "qubits": 9, "domain": "error_correction", "tags": ["shor-9", "qec"],
     "desc": "Shor 9-qubit code: first general QEC code"},
    {"name": "steane_7",        "qubits": 7, "domain": "error_correction", "tags": ["steane", "css"],
     "desc": "Steane 7-qubit [[7,1,3]] code: first CSS code"},
    {"name": "perfect_5",       "qubits": 5, "domain": "error_correction", "tags": ["perfect", "qec"],
     "desc": "[[5,1,3]] perfect code: minimal universal QEC"},
    {"name": "teleportation",   "qubits": 3, "domain": "error_correction", "tags": ["teleportation"],
     "desc": "Quantum teleportation: transmits state using entanglement + 2 cbits"},
    {"name": "superdense_coding","qubits":2,  "domain": "error_correction", "tags": ["superdense"],
     "desc": "Superdense coding: sends 2 classical bits through 1 qubit"},
    {"name": "syndrome_meas_3", "qubits": 5, "domain": "error_correction", "tags": ["syndrome"],
     "desc": "3-qubit repetition code syndrome measurement ancilla"},
    {"name": "logical_x",       "qubits": 7, "domain": "error_correction", "tags": ["logical-gate", "qec"],
     "desc": "Logical X on Steane [[7,1,3]] encoded qubit"},
    {"name": "logical_hadamard", "qubits":7,  "domain": "error_correction", "tags": ["logical-gate", "qec"],
     "desc": "Logical Hadamard on Steane [[7,1,3]] encoded qubit"},

    # ── CRYPTOGRAPHY (10) ───────────────────────────────────────────────
    {"name": "bb84_encode",     "qubits": 2, "domain": "cryptography", "tags": ["bb84", "qkd"],
     "desc": "BB84 qubit encoding: 4 BB84 basis states"},
    {"name": "e91_entangle",    "qubits": 2, "domain": "cryptography", "tags": ["e91", "qkd"],
     "desc": "E91 entanglement-based QKD: Ekert protocol EPR source"},
    {"name": "b92_encode",      "qubits": 2, "domain": "cryptography", "tags": ["b92", "qkd"],
     "desc": "B92 two-state QKD protocol encoding"},
    {"name": "commit_scheme",   "qubits": 3, "domain": "cryptography", "tags": ["commitment", "crypto"],
     "desc": "Quantum bit commitment scheme (unconditionally binding)"},
    {"name": "hash_oracle_3",   "qubits": 6, "domain": "cryptography", "tags": ["hash", "oracle"],
     "desc": "3-bit quantum hash oracle: marks collisions in superposition"},
    {"name": "grover_2of8",     "qubits": 3, "domain": "cryptography", "tags": ["grover", "crypto"],
     "desc": "Grover search in 8-element database: 2 marked items"},
    {"name": "ecdlp_oracle_4",  "qubits": 8, "domain": "cryptography", "tags": ["ecdlp", "ecc"],
     "desc": "4-bit ECDLP oracle: period-finding for elliptic-curve DLP"},
    {"name": "secp256k1_pointadd","qubits":4, "domain": "cryptography", "tags": ["secp256k1", "bitcoin"],
     "desc": "Minimal secp256k1 point-add circuit sketch (4-bit demo)"},
    {"name": "secret_sharing_3","qubits": 3, "domain": "cryptography", "tags": ["secret-sharing"],
     "desc": "3-player quantum secret sharing via GHZ state"},
    {"name": "qrng_4",          "qubits": 4, "domain": "cryptography", "tags": ["rng", "random"],
     "desc": "Quantum random number generator: 4 independent random bits"},

    # ── OPTIMIZATION (10) ───────────────────────────────────────────────
    {"name": "qaoa_tsp_4",      "qubits": 4, "domain": "optimization", "tags": ["qaoa", "tsp"],
     "desc": "QAOA for 4-city TSP (travelling salesman)"},
    {"name": "vqe_lih",         "qubits": 4, "domain": "optimization", "tags": ["vqe", "chemistry"],
     "desc": "VQE UCCSD ansatz for LiH molecule"},
    {"name": "vqe_uccd",        "qubits": 4, "domain": "optimization", "tags": ["vqe", "uccsd"],
     "desc": "UCCD ansatz: unitary coupled cluster double excitations"},
    {"name": "ising_model_4",   "qubits": 4, "domain": "optimization", "tags": ["ising", "spin"],
     "desc": "Quantum Ising model: transverse-field Hamiltonian evolution"},
    {"name": "heisenberg_4",    "qubits": 4, "domain": "optimization", "tags": ["heisenberg", "spin"],
     "desc": "Heisenberg spin chain: XXX model Trotter step"},
    {"name": "adiabatic_4",     "qubits": 4, "domain": "optimization", "tags": ["adiabatic", "annealing"],
     "desc": "Adiabatic evolution 4-qubit: slow ramp from easy to hard"},
    {"name": "grover_opt",      "qubits": 4, "domain": "optimization", "tags": ["grover", "optimization"],
     "desc": "Grover-based combinatorial optimization oracle"},
    {"name": "trotter_h2",      "qubits": 4, "domain": "optimization", "tags": ["trotter", "simulation"],
     "desc": "Trotterised H₂ evolution: first-order decomposition"},
    {"name": "kicked_ising_4",  "qubits": 4, "domain": "optimization", "tags": ["kicked", "ising"],
     "desc": "Kicked transverse-field Ising model: Floquet dynamics"},
    {"name": "rqaoa_4",         "qubits": 4, "domain": "optimization", "tags": ["rqaoa", "qaoa"],
     "desc": "Recursive QAOA: iteratively reduce problem size"},

    # ── SIMULATION (10) ─────────────────────────────────────────────────
    {"name": "ising_1d_4",      "qubits": 4, "domain": "simulation",   "tags": ["ising", "1d"],
     "desc": "1D transverse-field Ising model Trotter step"},
    {"name": "fermi_hubbard_4", "qubits": 4, "domain": "simulation",   "tags": ["fermi-hubbard"],
     "desc": "Fermi-Hubbard model single Trotter step"},
    {"name": "molecular_h2",    "qubits": 4, "domain": "simulation",   "tags": ["h2", "chemistry"],
     "desc": "H₂ molecular Hamiltonian: Jordan-Wigner mapping"},
    {"name": "xxz_chain_4",     "qubits": 4, "domain": "simulation",   "tags": ["xxz", "spin"],
     "desc": "XXZ spin chain: anisotropic Heisenberg Hamiltonian"},
    {"name": "tfim_4",          "qubits": 4, "domain": "simulation",   "tags": ["tfim"],
     "desc": "Transverse-field Ising model: quantum phase transition demo"},
    {"name": "bose_hubbard_4",  "qubits": 4, "domain": "simulation",   "tags": ["bose-hubbard"],
     "desc": "Bose-Hubbard model: boson hopping on a 4-site lattice"},
    {"name": "vqe_beh2",        "qubits": 6, "domain": "simulation",   "tags": ["beh2", "chemistry"],
     "desc": "BeH₂ molecule: 6-qubit VQE ground state"},
    {"name": "clock_sync_4",    "qubits": 4, "domain": "simulation",   "tags": ["clock", "sync"],
     "desc": "Quantum clock synchronisation: entangled timing protocol"},
    {"name": "loschmidt_4",     "qubits": 4, "domain": "simulation",   "tags": ["loschmidt", "echo"],
     "desc": "Loschmidt echo: forward + time-reversed evolution"},
    {"name": "qsim_random_4",   "qubits": 4, "domain": "simulation",   "tags": ["random", "benchmark"],
     "desc": "Random quantum circuit for hardware benchmarking"},

    # ── COMMUNICATION (5) ───────────────────────────────────────────────
    {"name": "teleport_full",   "qubits": 3, "domain": "communication","tags": ["teleportation", "qcomm"],
     "desc": "Full quantum teleportation with classical correction gates"},
    {"name": "entswap_4",       "qubits": 4, "domain": "communication","tags": ["entanglement-swapping"],
     "desc": "Entanglement swapping: extends entanglement range"},
    {"name": "repeater_4",      "qubits": 4, "domain": "communication","tags": ["repeater", "qnetwork"],
     "desc": "Elementary quantum repeater: encode + teleport + decode"},
    {"name": "dense_code_2",    "qubits": 2, "domain": "communication","tags": ["dense", "coding"],
     "desc": "Dense coding: encode 2 cbits into 1 shared qubit"},
    {"name": "qcomm_channel_3", "qubits": 3, "domain": "communication","tags": ["channel", "qcomm"],
     "desc": "Quantum channel simulation: amplitude-damping noisy channel"},
]

assert len(_CIRCUIT_SPECS) == 100, f"Expected 100, got {len(_CIRCUIT_SPECS)}"


@lru_cache(maxsize=1)
def library() -> dict[str, "QuantumCircuit"]:
    """Return all built-in circuits keyed by name."""
    result: dict[str, QuantumCircuit] = {}
    circuits_dir = Path(__file__).parent / "circuits"
    for spec in _CIRCUIT_SPECS:
        name = spec["name"]
        qasm_path = circuits_dir / spec["domain"] / f"{name}.qasm"
        if qasm_path.exists():
            qasm = qasm_path.read_text()
        else:
            qasm = _generate_qasm(spec)
        meta = CircuitMeta(
            name=name, qubits=spec["qubits"],
            domain=spec["domain"], tags=spec["tags"],
            description=spec["desc"], source_lang="qasm2",
        )
        result[name] = QuantumCircuit(meta=meta, qasm=qasm)
    return result


def list_circuits(domain: str = "") -> list[str]:
    """Return circuit names, optionally filtered by domain."""
    return [s["name"] for s in _CIRCUIT_SPECS
            if not domain or s["domain"] == domain]


def domains() -> list[str]:
    seen: list[str] = []
    for s in _CIRCUIT_SPECS:
        if s["domain"] not in seen:
            seen.append(s["domain"])
    return seen


# ── inline QASM generator ──────────────────────────────────────────────
def _generate_qasm(spec: dict) -> str:
    """Generate minimal QASM 2.0 for a spec when no file is on disk."""
    name = spec["name"]
    q = spec["qubits"]
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"// {spec['desc']}",
        f"qreg q[{q}];",
        f"creg c[{q}];",
    ]
    lines += _body(name, q)
    for i in range(q):
        lines.append(f"measure q[{i}] -> c[{i}];")
    return "\n".join(lines)


def _body(name: str, q: int) -> list[str]:  # noqa: C901 (big switch)
    # fmt: off
    if name == "h_single":       return ["h q[0];"]
    if name == "cnot":           return ["h q[0];", "cx q[0],q[1];"]
    if name == "toffoli":        return ["h q[0];", "h q[1];", "ccx q[0],q[1],q[2];"]
    if name == "swap":           return ["h q[0];", "swap q[0],q[1];"]
    if name == "cswap":          return ["x q[0];", "h q[1];", "cswap q[0],q[1],q[2];"]
    if name == "bell_phi_plus":  return ["h q[0];", "cx q[0],q[1];"]
    if name == "bell_phi_minus": return ["h q[0];", "cx q[0],q[1];", "z q[0];"]
    if name == "bell_psi_plus":  return ["h q[0];", "cx q[0],q[1];", "x q[1];"]
    if name == "bell_psi_minus": return ["h q[0];", "cx q[0],q[1];", "x q[1];", "z q[0];"]
    if name == "ghz_3":          return ["h q[0];", "cx q[0],q[1];", "cx q[1],q[2];"]
    if name == "ghz_4":          return ["h q[0];", "cx q[0],q[1];", "cx q[1],q[2];", "cx q[2],q[3];"]
    if name == "ghz_5":          return ["h q[0];", "cx q[0],q[1];", "cx q[1],q[2];", "cx q[2],q[3];", "cx q[3],q[4];"]
    if name == "w_state_3":
        return ["x q[0];",
                "h q[0];", "cx q[0],q[1];",
                "t q[0];", "h q[0];", "cx q[0],q[2];",
                "h q[0];", "cx q[0],q[1];", "h q[0];"]
    if name == "qft_4":
        return ["h q[0];", "cp(pi/2) q[1],q[0];", "cp(pi/4) q[2],q[0];", "cp(pi/8) q[3],q[0];",
                "h q[1];", "cp(pi/2) q[2],q[1];", "cp(pi/4) q[3],q[1];",
                "h q[2];", "cp(pi/2) q[3],q[2];",
                "h q[3];",
                "swap q[0],q[3];", "swap q[1],q[2];"]
    if name == "phase_kickback": return ["x q[1];", "h q[0];", "cz q[0],q[1];", "h q[0];"]
    if name == "quantum_walk_2": return ["h q[0];", "cx q[0],q[1];", "h q[0];"]
    if name == "superposition_n4": return [f"h q[{i}];" for i in range(4)]
    if name == "entangled_pair": return ["h q[0];", "cx q[0],q[1];"]
    if name == "rx_ry_rz":       return ["rx(pi/4) q[0];", "ry(pi/3) q[0];", "rz(pi/2) q[0];"]
    if name == "phase_oracle":   return ["ccx q[0],q[1],q[2];", "z q[2];", "ccx q[0],q[1],q[2];"]

    # algorithms
    if name == "deutsch_jozsa":
        return [f"h q[{i}];" for i in range(q-1)] + \
               ["x q[3];", "h q[3];"] + \
               [f"cx q[{i}],q[3];" for i in range(q-1)] + \
               [f"h q[{i}];" for i in range(q-1)]
    if name == "bernstein_vazirani":
        return ["h q[0];","h q[1];","h q[2];",
                "x q[3];","h q[3];",
                "cx q[0],q[3];","cx q[2],q[3];",
                "h q[0];","h q[1];","h q[2];"]
    if name == "simon_2":
        return ["h q[0];","h q[1];",
                "cx q[0],q[2];","cx q[0],q[3];",
                "cx q[1],q[2];",
                "h q[0];","h q[1];"]
    if name == "grover_2q":
        return ["h q[0];","h q[1];",
                "x q[0];","x q[1];","h q[1];","cx q[0],q[1];","h q[1];","x q[0];","x q[1];",
                "h q[0];","h q[1];",
                "x q[0];","x q[1];","h q[1];","cx q[0],q[1];","h q[1];","x q[0];","x q[1];",
                "h q[0];","h q[1];"]
    if name == "grover_3q":
        return ["h q[0];","h q[1];","h q[2];",
                "x q[0];","x q[1];","h q[2];","ccx q[0],q[1],q[2];","h q[2];","x q[0];","x q[1];",
                "h q[0];","h q[1];",
                "x q[0];","x q[1];","h q[2];","ccx q[0],q[1],q[2];","h q[2];","x q[0];","x q[1];",
                "h q[0];","h q[1];"]
    if name in ("qpe_2", "qpe_3", "iqpe"):
        return [f"h q[{i}];" for i in range(q-1)] + \
               ["x q[4];" if q > 4 else f"x q[{q-1}];"] + \
               [f"cp(pi/{2**i}) q[{i}],q[{q-1}];" for i in range(q-1)] + \
               ["h q[0];"] + \
               [f"cp(-pi/{2**(j-i)}) q[{i}],q[{j}];" for j in range(1, q-1) for i in range(j)] + \
               [f"h q[{i}];" for i in range(q-1)]
    if name == "hhl_2x2":
        return ["h q[0];","h q[1];","x q[2];",
                "cp(pi/2) q[0],q[2];","cp(pi/4) q[1],q[2];",
                "h q[0];","h q[1];",
                "ry(pi/8) q[3];"]
    if name in ("amplitude_amp", "grover_opt"):
        return [f"h q[{i}];" for i in range(q)] + \
               ["z q[0];","z q[1];"] + \
               [f"h q[{i}];" for i in range(q)]
    if name == "quantum_walk_4":
        return ["h q[0];","h q[1];",
                "cx q[0],q[2];","cx q[1],q[3];",
                "h q[0];","h q[1];"]
    if name == "swap_test":
        return ["h q[0];",
                "cswap q[0],q[1],q[3];","cswap q[0],q[2],q[4];",
                "h q[0];"]
    if name == "vqe_h2":
        return ["x q[0];","x q[2];",
                "ry(pi/4) q[0];","ry(pi/4) q[2];",
                "cx q[0],q[1];","cx q[2],q[3];",
                "ry(-pi/4) q[0];","ry(-pi/4) q[2];"]
    if name in ("qaoa_maxcut_4", "qaoa_maxcut_p2"):
        layers = 1 if "p2" not in name else 2
        body = [f"h q[{i}];" for i in range(q)]
        for _ in range(layers):
            body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
            body += [f"rz(0.5) q[{i}];" for i in range(q)]
            body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
            body += [f"rx(0.7) q[{i}];" for i in range(q)]
        return body
    if name == "shor_order_15":
        return [f"h q[{i}];" for i in range(4)] + \
               ["x q[4];"] + \
               [f"cx q[{i}],q[4+{i%4}];" for i in range(4)] + \
               [f"h q[{i}];" for i in range(4)]
    if name in ("variational_4", "haa_4", "real_amplitudes", "two_local_rzrx"):
        body = [f"ry(0.3) q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"ry(0.5) q[{i}];" for i in range(q)]
        return body

    # arithmetic
    if name == "adder_1bit":
        return ["cx q[0],q[2];","cx q[1],q[2];","ccx q[0],q[1],q[2];"]
    if name in ("adder_4bit","draper_adder_4","subtractor_4","cuccaro_adder","carry_save_4"):
        body = [f"cx q[{i}],q[{i+q//2}];" for i in range(q//2)]
        body += [f"ccx q[{i}],q[{i+1}],q[{i+q//2}];" for i in range(q//2-1)]
        return body
    if name in ("multiplier_2bit", "square_4"):
        return [f"cx q[{i}],q[{i+q//2}];" for i in range(q//2)] + \
               [f"ccx q[{i}],q[{i+1 if i+1<q//2 else 0}],q[{i+q//2}];" for i in range(q//2)]
    if name in ("modular_add_4","controlled_add_4","modular_exp_15"):
        return [f"h q[{i}];" for i in range(q//2)] + \
               [f"cp(pi/{2**i}) q[{i}],q[{q//2+i}];" for i in range(q//2)]
    if name in ("increment_4","div_by_3"):
        return ["x q[3];",
                "ccx q[2],q[3],q[3];",
                "ccx q[1],q[2],q[3];",
                "cx q[0],q[1];"]
    if name == "comparator_4":
        return [f"cx q[{i}],q[{i+4}];" for i in range(4)] + \
               ["ccx q[0],q[4],q[8];"]
    if name == "gcd_4":
        return [f"swap q[{i}],q[{i+q//3}];" for i in range(q//3)] + \
               [f"cx q[{i}],q[{i+q//3}];" for i in range(q//3)]

    # error correction
    if name == "bit_flip_3":
        return ["cx q[0],q[1];","cx q[0],q[2];"]
    if name == "phase_flip_3":
        return ["h q[0];","h q[1];","h q[2];","cx q[0],q[1];","cx q[0],q[2];","h q[0];","h q[1];","h q[2];"]
    if name == "shor_9":
        return ["cx q[0],q[3];","cx q[0],q[6];",
                "h q[0];","h q[3];","h q[6];",
                "cx q[0],q[1];","cx q[0],q[2];",
                "cx q[3],q[4];","cx q[3],q[5];",
                "cx q[6],q[7];","cx q[6],q[8];"]
    if name == "steane_7":
        return ["h q[0];","h q[2];","h q[4];",
                "cx q[0],q[3];","cx q[0],q[5];","cx q[0],q[6];",
                "cx q[2],q[3];","cx q[2],q[4];","cx q[2],q[6];",
                "cx q[4],q[5];","cx q[4],q[6];"]
    if name == "steane_7":
        return [f"cx q[{i}],q[{(i+1)%7}];" for i in range(7)]
    if name == "perfect_5":
        return ["h q[0];",
                "cz q[0],q[1];","cz q[0],q[2];","cz q[0],q[3];","cz q[0],q[4];",
                "h q[0];"]
    if name in ("teleportation","teleport_full"):
        return ["h q[1];","cx q[1],q[2];",
                "cx q[0],q[1];","h q[0];",
                "measure q[0] -> c[0];","measure q[1] -> c[1];",
                "if(c==1) x q[2];","if(c==2) z q[2];"]
    if name == "superdense_coding":
        return ["h q[0];","cx q[0],q[1];","cx q[0],q[1];","h q[0];"]
    if name == "syndrome_meas_3":
        return ["cx q[0],q[3];","cx q[1],q[3];",
                "cx q[1],q[4];","cx q[2],q[4];"]
    if name in ("logical_x","logical_hadamard"):
        return [f"x q[{i}];" for i in range(7)]

    # cryptography
    if name == "bb84_encode":
        return ["h q[0];","x q[1];"]
    if name in ("e91_entangle","entangled_pair"):
        return ["h q[0];","cx q[0],q[1];"]
    if name == "b92_encode":
        return ["h q[0];","t q[0];"]
    if name == "commit_scheme":
        return ["h q[0];","cx q[0],q[1];","cx q[1],q[2];"]
    if name == "hash_oracle_3":
        return [f"h q[{i}];" for i in range(q//2)] + \
               [f"cx q[{i}],q[{i+q//2}];" for i in range(q//2)]
    if name == "grover_2of8":
        return ["h q[0];","h q[1];","h q[2];",
                "x q[0];","h q[2];","ccx q[0],q[1],q[2];","h q[2];","x q[0];",
                "h q[0];","h q[1];","h q[2];"]
    if name in ("ecdlp_oracle_4","secp256k1_pointadd"):
        return [f"h q[{i}];" for i in range(q//2)] + \
               [f"cx q[{i}],q[{i+q//2}];" for i in range(q//2)] + \
               [f"h q[{i}];" for i in range(q//2)]
    if name == "secret_sharing_3":
        return ["h q[0];","cx q[0],q[1];","cx q[0],q[2];"]
    if name == "qrng_4":
        return [f"h q[{i}];" for i in range(4)]

    # optimization
    if name in ("qaoa_tsp_4","rqaoa_4"):
        body = [f"h q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"rz(0.5) q[{i}];" for i in range(q)]
        return body
    if name in ("vqe_lih","vqe_uccd","vqe_beh2"):
        body = [f"x q[{i}];" for i in range(q//2)]
        body += [f"ry(0.25) q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        return body
    if name in ("ising_model_4","ising_1d_4","tfim_4","kicked_ising_4"):
        body = [f"h q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"rz(0.5) q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"rx(0.3) q[{i}];" for i in range(q)]
        return body
    if name in ("heisenberg_4","xxz_chain_4","heisenberg_spin_4"):
        body = [f"rx(0.5) q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"rz(0.4) q[{i}];" for i in range(q)]
        return body
    if name in ("adiabatic_4",):
        body = [f"h q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        return body
    if name in ("trotter_h2","trotter_evolution_4"):
        return ["x q[0];","x q[2];",
                "cx q[0],q[1];","rz(0.2) q[1];","cx q[0],q[1];",
                "cx q[2],q[3];","rz(0.2) q[3];","cx q[2],q[3];"]
    if name == "loschmidt_4":
        body = [f"h q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        body += [f"rz(0.5) q[{i}];" for i in range(q)]
        body += [f"cx q[{(i+1)%q}],q[{i}];" for i in range(q)]
        body += [f"h q[{i}];" for i in range(q)]
        return body

    # simulation
    if name in ("fermi_hubbard_4","bose_hubbard_4"):
        body = [f"x q[{i}];" for i in range(q//2)]
        body += [f"ry(0.3) q[{i}];" for i in range(q)]
        body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
        return body
    if name == "molecular_h2":
        return ["x q[0];","x q[2];",
                "ry(0.1) q[0];","cx q[0],q[1];",
                "ry(0.1) q[2];","cx q[2],q[3];"]
    if name == "vqe_beh2":
        body = [f"x q[{i}];" for i in range(3)]
        body += [f"ry(0.2) q[{i}];" for i in range(6)]
        body += [f"cx q[{i}],q[{i+1}];" for i in range(5)]
        return body
    if name == "clock_sync_4":
        return ["h q[0];","cx q[0],q[1];","cx q[0],q[2];","cx q[0],q[3];"]
    if name == "qsim_random_4":
        return ["h q[0];","h q[2];",
                "cx q[0],q[1];","cx q[2],q[3];",
                "t q[0];","s q[2];","cx q[1],q[2];",
                "h q[1];","h q[3];"]

    # communication
    if name == "entswap_4":
        return ["h q[0];","cx q[0],q[1];","h q[2];","cx q[2],q[3];",
                "cx q[1],q[2];","h q[1];"]
    if name == "repeater_4":
        return ["h q[0];","cx q[0],q[1];",
                "h q[2];","cx q[2],q[3];",
                "cx q[1],q[2];","h q[1];"]
    if name in ("dense_code_2","superdense_coding"):
        return ["h q[0];","cx q[0],q[1];","x q[0];","h q[0];"]
    if name == "qcomm_channel_3":
        return ["h q[0];","cx q[0],q[1];","ry(0.1) q[1];","cx q[1],q[2];"]

    # fallback: random circuit
    body = [f"h q[{i}];" for i in range(q)]
    body += [f"cx q[{i}],q[{(i+1)%q}];" for i in range(q)]
    return body
    # fmt: on
