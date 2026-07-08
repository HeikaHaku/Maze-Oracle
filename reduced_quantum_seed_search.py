"""
reduced_quantum_seed_search.py

An actual computed Grover seed-search demo for the Maze Oracle project.

This file is intentionally small. It does not call the classical maze oracle and
it does not phase-mark a precomputed list of valid seeds. Instead, the quantum
circuit computes a reduced procedural map predicate from the seed register.

Reduced PCG problem
-------------------
Seed width: 4 qubits.
Generator: the low 4-bit reduction of the repository LCG

    x -> (1103515245*x + 12345) mod 16

Since 1103515245 == 13 mod 16 and 12345 == 9 mod 16, the circuit computes

    x -> (13*x + 9) mod 16.

The reduced generator produces three LCG outputs from the seed:

    r1 = LCG(seed)
    r2 = LCG(r1)
    r3 = LCG(r2)

Each output contributes a two-bit feature position using its high two bits:

    start = r1 >> 2
    key   = r2 >> 2
    exit  = r3 >> 2

The reduced map is a 4-cell line dungeon. The valid-order predicate is:

    start < key < exit

The Grover oracle computes r1, r2, and r3 into work registers, applies a phase
flip when the generated feature positions satisfy the predicate, and uncomputes
all work registers back to |0>.

This is a real computed oracle for a reduced seed-search PCG problem:

    |seed>|0000>|0000>|0000> -> (-1)^valid(seed)|seed>|0000>|0000>|0000>

It is not the full 16x16 maze oracle. It is the smallest useful bridge from the
existing LCG/generator idea to actual quantum seed search.
"""

from __future__ import annotations

from math import pi, sqrt
from typing import Iterable

try:
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
except ImportError:  # Allow classical helper functions to work without Qiskit.
    ClassicalRegister = None  # type: ignore[assignment]
    QuantumCircuit = None  # type: ignore[assignment]
    QuantumRegister = None  # type: ignore[assignment]
    transpile = None  # type: ignore[assignment]


# The repository LCG constants reduced modulo 16.
LCG_A_MOD_16 = 1103515245 % 16  # 13
LCG_C_MOD_16 = 12345 % 16       # 9
SEED_BITS = 4
FEATURE_BITS = 2

# Algebraic normal form for y = (13*x + 9) mod 16, little-endian bits.
# Each output bit y_i is expressed as an XOR of monomials in x_0, x_1, x_2, x_3.
# () means constant 1. (0, 2) means x_0 AND x_2.
LCG13_9_ANF: tuple[tuple[tuple[int, ...], ...], ...] = (
    ((), (0,)),                                      # y0 = 1 xor x0
    ((0,), (1,)),                                    # y1 = x0 xor x1
    ((0,), (0, 1), (2,)),                            # y2 = x0 xor x0*x1 xor x2
    ((), (0,), (1,), (0, 1), (0, 2), (0, 1, 2), (3,)), # y3
)

# Valid generated feature-position triples for start < key < exit on a 4-cell line.
VALID_POSITION_TRIPLES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (0, 1, 3),
    (0, 2, 3),
    (1, 2, 3),
)


def _require_qiskit() -> None:
    """Raise a clear error when a circuit-building path needs Qiskit."""
    if any(obj is None for obj in (ClassicalRegister, QuantumCircuit, QuantumRegister, transpile)):
        raise ImportError(
            "Qiskit is required for quantum circuit construction. "
            "Install it with: pip install qiskit qiskit-aer"
        )


def bits_little_endian(value: int, width: int) -> list[int]:
    """Return the binary bits of value in little-endian order."""
    if value < 0 or value >= 2**width:
        raise ValueError(f"Value {value} does not fit in {width} bits.")
    return [(value >> i) & 1 for i in range(width)]


def qiskit_count_key_to_seed(bitstring: str) -> int:
    """
    Convert a Qiskit measurement key into a decimal seed.

    With measure(seed[i], c[i]), Qiskit displays classical bits as c[n-1]...c[0].
    Therefore int(bitstring, 2) is the seed value.
    """
    return int(bitstring, 2)


# -----------------------------------------------------------------------------
# Classical reference for the reduced PCG problem
# -----------------------------------------------------------------------------


def lcg4_next(value: int) -> int:
    """Classical 4-bit version of the repository LCG."""
    return (LCG_A_MOD_16 * value + LCG_C_MOD_16) % 16


def reduced_map_positions(seed: int) -> tuple[int, int, int]:
    """
    Generate the reduced line-dungeon feature positions from a 4-bit seed.

    Returns:
        (start, key, exit), each in {0, 1, 2, 3}.
    """
    if seed < 0 or seed >= 2**SEED_BITS:
        raise ValueError(f"Seed {seed} does not fit in {SEED_BITS} bits.")

    r1 = lcg4_next(seed)
    r2 = lcg4_next(r1)
    r3 = lcg4_next(r2)

    return (r1 >> 2, r2 >> 2, r3 >> 2)


def reduced_map_is_valid(seed: int) -> bool:
    """Return True exactly when the reduced generated map satisfies start < key < exit."""
    start, key, exit_ = reduced_map_positions(seed)
    return start < key < exit_


def reduced_map_marked_seeds() -> list[int]:
    """Return all marked seeds for the reduced 4-bit problem."""
    return [seed for seed in range(2**SEED_BITS) if reduced_map_is_valid(seed)]


# -----------------------------------------------------------------------------
# Reversible circuit building blocks
# -----------------------------------------------------------------------------


def xor_monomial_into_target(
    circuit: QuantumCircuit,
    controls: list,
    target,
) -> None:
    """
    Toggle target by the AND of controls.

    controls = []      -> target ^= 1
    controls = [a]     -> target ^= a
    controls = [a, b]  -> target ^= a & b
    controls = [a,b,c] -> target ^= a & b & c
    """
    if len(controls) == 0:
        circuit.x(target)
    elif len(controls) == 1:
        circuit.cx(controls[0], target)
    elif len(controls) == 2:
        circuit.ccx(controls[0], controls[1], target)
    else:
        circuit.mcx(controls, target)


def compute_lcg13_9_mod16_xor(
    circuit: QuantumCircuit,
    source: QuantumRegister,
    target: QuantumRegister,
) -> None:
    """
    Reversibly compute target ^= (13*source + 9) mod 16.

    This is an XOR-style reversible computation. Applying this function twice
    with the same source and target restores target to its original value.
    """
    if len(source) != SEED_BITS or len(target) != SEED_BITS:
        raise ValueError("This reduced oracle requires 4-bit source and target registers.")

    for output_bit, terms in enumerate(LCG13_9_ANF):
        for term in terms:
            controls = [source[index] for index in term]
            xor_monomial_into_target(circuit, controls, target[output_bit])


def apply_phase_flip_if_qubits_match(
    circuit: QuantumCircuit,
    qubits: list,
    bit_pattern: Iterable[int],
) -> None:
    """
    Apply a -1 phase exactly when qubits match bit_pattern.

    bit_pattern is given in the same order as qubits.
    """
    bits = list(bit_pattern)
    if len(qubits) != len(bits):
        raise ValueError("qubits and bit_pattern must have the same length.")
    if not qubits:
        raise ValueError("At least one qubit is required for a phase check.")

    # Map desired pattern to |111...1>.
    for qubit, bit in zip(qubits, bits):
        if bit == 0:
            circuit.x(qubit)
        elif bit != 1:
            raise ValueError("bit_pattern entries must be 0 or 1.")

    # Phase-flip |111...1>.
    if len(qubits) == 1:
        circuit.z(qubits[0])
    else:
        target = qubits[-1]
        controls = qubits[:-1]
        circuit.h(target)
        circuit.mcx(controls, target)
        circuit.h(target)

    # Undo the mapping.
    for qubit, bit in reversed(list(zip(qubits, bits))):
        if bit == 0:
            circuit.x(qubit)


def position_pattern_bits(start: int, key: int, exit_: int) -> list[int]:
    """
    Convert three two-bit positions into the qubit pattern used by the oracle.

    The qubit order is:
        r1[2], r1[3], r2[2], r2[3], r3[2], r3[3]

    where r1 gives start, r2 gives key, and r3 gives exit.
    """
    return (
        bits_little_endian(start, FEATURE_BITS)
        + bits_little_endian(key, FEATURE_BITS)
        + bits_little_endian(exit_, FEATURE_BITS)
    )


def apply_reduced_map_phase_oracle(
    circuit: QuantumCircuit,
    seed: QuantumRegister,
    r1: QuantumRegister,
    r2: QuantumRegister,
    r3: QuantumRegister,
    use_barriers: bool = True,
) -> None:
    """
    Apply the computed phase oracle for the reduced PCG seed-search problem.

    Steps:
        1. Compute r1 = LCG(seed).
        2. Compute r2 = LCG(r1).
        3. Compute r3 = LCG(r2).
        4. Phase-flip generated feature triples satisfying start < key < exit.
        5. Uncompute r3, r2, and r1.
    """
    # Compute the generated map features.
    compute_lcg13_9_mod16_xor(circuit, seed, r1)
    compute_lcg13_9_mod16_xor(circuit, r1, r2)
    compute_lcg13_9_mod16_xor(circuit, r2, r3)

    if use_barriers:
        circuit.barrier()

    # The feature positions are the high two bits of the LCG outputs.
    feature_qubits = [r1[2], r1[3], r2[2], r2[3], r3[2], r3[3]]
    for start, key, exit_ in VALID_POSITION_TRIPLES:
        apply_phase_flip_if_qubits_match(
            circuit,
            feature_qubits,
            position_pattern_bits(start, key, exit_),
        )

    if use_barriers:
        circuit.barrier()

    # Uncompute the generated map features.
    compute_lcg13_9_mod16_xor(circuit, r2, r3)
    compute_lcg13_9_mod16_xor(circuit, r1, r2)
    compute_lcg13_9_mod16_xor(circuit, seed, r1)


# -----------------------------------------------------------------------------
# Grover circuit
# -----------------------------------------------------------------------------


def build_diffuser(num_qubits: int, name: str = "Diffuser") -> QuantumCircuit:
    """Build the standard Grover diffusion operator over num_qubits."""
    _require_qiskit()

    register = QuantumRegister(num_qubits, "seed")
    diffuser = QuantumCircuit(register, name=name)

    diffuser.h(register)
    diffuser.x(register)

    if num_qubits == 1:
        diffuser.z(register[0])
    else:
        target = register[num_qubits - 1]
        controls = list(register[: num_qubits - 1])
        diffuser.h(target)
        diffuser.mcx(controls, target)
        diffuser.h(target)

    diffuser.x(register)
    diffuser.h(register)

    return diffuser


def optimal_grover_iterations(num_seed_qubits: int, num_marked: int) -> int:
    """Return the standard approximate Grover iteration count."""
    if num_marked <= 0:
        raise ValueError("num_marked must be positive.")
    total_states = 2**num_seed_qubits
    return max(1, round((pi / 4) * sqrt(total_states / num_marked)))


def build_reduced_map_oracle_gate(use_barriers: bool = False):
    """Build the reduced-map computed phase oracle as a reusable gate."""
    _require_qiskit()

    seed = QuantumRegister(SEED_BITS, "seed")
    r1 = QuantumRegister(SEED_BITS, "r1")
    r2 = QuantumRegister(SEED_BITS, "r2")
    r3 = QuantumRegister(SEED_BITS, "r3")

    oracle = QuantumCircuit(seed, r1, r2, r3, name="ReducedMapOracle")
    apply_reduced_map_phase_oracle(oracle, seed, r1, r2, r3, use_barriers=use_barriers)

    return oracle.to_gate()


def build_reduced_map_grover_circuit(
    iterations: int | None = None,
    measure: bool = True,
    use_barriers: bool = False,
) -> QuantumCircuit:
    """
    Build a complete Grover circuit for the reduced computed PCG oracle.

    Registers:
        seed: searched seed register
        r1, r2, r3: generated LCG/map-feature work registers, uncomputed each iteration
        c: classical measurement register for seed
    """
    _require_qiskit()

    marked = reduced_map_marked_seeds()
    if iterations is None:
        iterations = optimal_grover_iterations(SEED_BITS, len(marked))

    seed = QuantumRegister(SEED_BITS, "seed")
    r1 = QuantumRegister(SEED_BITS, "r1")
    r2 = QuantumRegister(SEED_BITS, "r2")
    r3 = QuantumRegister(SEED_BITS, "r3")
    classical = ClassicalRegister(SEED_BITS, "c")

    if measure:
        circuit = QuantumCircuit(seed, r1, r2, r3, classical)
    else:
        circuit = QuantumCircuit(seed, r1, r2, r3)

    oracle_gate = build_reduced_map_oracle_gate(use_barriers=use_barriers)
    diffuser_gate = build_diffuser(SEED_BITS).to_gate()

    circuit.h(seed)

    for _ in range(iterations):
        circuit.append(oracle_gate, list(seed) + list(r1) + list(r2) + list(r3))
        circuit.append(diffuser_gate, seed)

    if measure:
        circuit.measure(seed, classical)

    return circuit


def run_local_simulation(shots: int = 4096, iterations: int | None = None) -> dict[str, int]:
    """Run the reduced Grover circuit locally with qiskit-aer."""
    _require_qiskit()

    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise ImportError(
            "qiskit-aer is required for local simulation. "
            "Install it with: pip install qiskit-aer"
        ) from exc

    circuit = build_reduced_map_grover_circuit(iterations=iterations)
    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    job = simulator.run(compiled, shots=shots)
    result = job.result()
    return result.get_counts()


def print_problem_summary() -> None:
    """Print the reduced problem definition and its classically verified marked seeds."""
    marked = reduced_map_marked_seeds()
    iterations = optimal_grover_iterations(SEED_BITS, len(marked))

    print("Reduced computed quantum seed-search problem")
    print(f"LCG: x -> ({LCG_A_MOD_16}*x + {LCG_C_MOD_16}) mod 16")
    print("Feature positions: high two bits of r1, r2, r3")
    print("Validity condition: start < key < exit on a 4-cell line dungeon")
    print(f"Marked seeds: {marked}")
    for seed in marked:
        print(f"  seed {seed:>2}: positions={reduced_map_positions(seed)}")
    print(f"Recommended Grover iterations: {iterations}")


def print_top_counts(counts: dict[str, int], limit: int = 10) -> None:
    """Print measured seeds sorted by count."""
    total = sum(counts.values())
    print("Top measured seeds:")
    for bitstring, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]:
        seed = qiskit_count_key_to_seed(bitstring)
        probability = count / total
        print(
            f"bitstring={bitstring} | "
            f"seed={seed:>2} | "
            f"count={count:>5} | "
            f"p={probability:.4f} | "
            f"positions={reduced_map_positions(seed)} | "
            f"valid={reduced_map_is_valid(seed)}"
        )


if __name__ == "__main__":
    print_problem_summary()

    if QuantumCircuit is None:
        print("\nQiskit is not installed, so only the classical reduced-problem summary was printed.")
    else:
        circuit = build_reduced_map_grover_circuit()
        print("\nCircuit summary:")
        print(f"  qubits: {circuit.num_qubits}")
        print(f"  depth:  {circuit.depth()}")
        print(f"  ops:    {circuit.count_ops()}")

        try:
            counts = run_local_simulation(shots=4096)
            print()
            print_top_counts(counts)
        except ImportError as exc:
            print(f"\nSkipping local simulation: {exc}")
