"""
quantum_oracle.py

First quantum layer for the Maze Oracle project.

This file implements a seed-level Grover search. 
"""

from __future__ import annotations

from math import pi, sqrt
from typing import Iterable, TYPE_CHECKING

try:
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
except ImportError:  # Keep oracle(maze) usable even without Qiskit installed.
    ClassicalRegister = None  # type: ignore[assignment]
    QuantumCircuit = None  # type: ignore[assignment]
    QuantumRegister = None  # type: ignore[assignment]
    transpile = None  # type: ignore[assignment]

from collections import Counter

if TYPE_CHECKING:
    from maze import Maze
    from utils import OracleResult


def _require_qiskit() -> None:
    """Raise a clear error when a circuit-building path needs Qiskit."""
    if any(obj is None for obj in (ClassicalRegister, QuantumCircuit, QuantumRegister, transpile)):
        raise ImportError(
            "Qiskit is required for quantum circuit construction. "
            "Install it with: pip install qiskit qiskit-aer"
        )


def bits_little_endian(value: int, width: int) -> list[int]:
    """
    Return bits in little-endian order.

    Qubit 0 stores the least significant bit.
    """
    return [(value >> i) & 1 for i in range(width)]


def qiskit_count_key_to_seed(bitstring: str) -> int:
    """
    Convert a Qiskit measurement key into an integer seed.

    If we measure q[i] -> c[i], Qiskit displays the classical string as
    c[n-1]...c[0], so int(bitstring, 2) gives the expected seed.
    """
    return int(bitstring, 2)


def oracle(maze: "Maze") -> "OracleResult":
    """
    Compatibility entry point matching classic_oracle.oracle(maze).

    main.py calls oracle_module.oracle(maze) after generating one maze from
    one seed. The seed-level Grover code in this module marks basis states
    using the same maze-validity predicate, but it does not directly consume
    a single Maze object as a quantum circuit.

    This wrapper therefore keeps quantum_oracle usable as a drop-in module
    wherever classic_oracle is currently used, while preserving one shared
    definition of maze validity.
    """
    from classic_oracle import oracle as classic_maze_oracle

    return classic_maze_oracle(maze)


def apply_phase_flip_on_basis_state(
    circuit: QuantumCircuit,
    qubits: QuantumRegister,
    marked_state: int,
) -> None:
    """
    Apply a -1 phase to exactly one computational basis state.

    Example:
        num qubits = 4
        marked_state = 1
        marks |0001> with a phase flip.

    Internally:
        1. X-flip the zero bits so the marked state becomes |111...1>.
        2. Apply a multi-controlled phase flip.
        3. Undo the X gates.
    """
    num_qubits = len(qubits)
    bits = bits_little_endian(marked_state, num_qubits)

    # Map the marked basis state to |111...1>.
    for i, bit in enumerate(bits):
        if bit == 0:
            circuit.x(qubits[i])

    # Apply phase flip to |111...1>.
    if num_qubits == 1:
        circuit.z(qubits[0])
    else:
        target = qubits[num_qubits - 1]
        controls = qubits[: num_qubits - 1]

        circuit.h(target)
        circuit.mcx(controls, target)
        circuit.h(target)

    # Undo the basis-state mapping.
    for i, bit in reversed(list(enumerate(bits))):
        if bit == 0:
            circuit.x(qubits[i])


def build_phase_oracle(
    num_seed_qubits: int,
    marked_seeds: Iterable[int],
    name: str = "SeedOracle",
) -> QuantumCircuit:
    """
    Build a phase oracle that marks one or more seed values.

    This is a truth-table-style oracle over seed values. It is useful for
    testing Grover amplification before implementing the full reversible
    maze predicate.

    Truth-table Oracle:
    1. Search over seed states |seed>.
    2. Phase-mark selected seeds.
    3. Apply Grover diffusion.
    4. Measure amplified candidate seeds.
    """
    _require_qiskit()

    marked = sorted(set(marked_seeds))
    max_seed = 2**num_seed_qubits

    if not marked:
        raise ValueError("The oracle needs at least one marked seed.")

    for seed in marked:
        if seed < 0 or seed >= max_seed:
            raise ValueError(
                f"Seed {seed} does not fit in {num_seed_qubits} qubits."
            )

    seed_register = QuantumRegister(num_seed_qubits, "seed")
    oracle = QuantumCircuit(seed_register, name=name)

    for seed in marked:
        apply_phase_flip_on_basis_state(oracle, seed_register, seed)

    return oracle


def build_diffuser(num_seed_qubits: int, name: str = "Diffuser") -> QuantumCircuit:
    """
    Build the standard Grover diffusion operator over the seed register.
    """
    _require_qiskit()

    seed_register = QuantumRegister(num_seed_qubits, "seed")
    diffuser = QuantumCircuit(seed_register, name=name)

    diffuser.h(seed_register)
    diffuser.x(seed_register)

    # Phase flip |111...1>.
    if num_seed_qubits == 1:
        diffuser.z(seed_register[0])
    else:
        target = seed_register[num_seed_qubits - 1]
        controls = seed_register[: num_seed_qubits - 1]

        diffuser.h(target)
        diffuser.mcx(controls, target)
        diffuser.h(target)

    diffuser.x(seed_register)
    diffuser.h(seed_register)

    return diffuser


def optimal_grover_iterations(num_seed_qubits: int, num_marked: int) -> int:
    """
    Approximate number of Grover iterations.

    For N states and M marked states, the usual estimate is:

        round((pi / 4) * sqrt(N / M))

    We force at least one iteration for tiny demos.
    """
    if num_marked <= 0:
        raise ValueError("num_marked must be positive.")

    total_states = 2**num_seed_qubits
    return max(1, round((pi / 4) * sqrt(total_states / num_marked)))


def build_grover_circuit(
    num_seed_qubits: int,
    marked_seeds: Iterable[int],
    iterations: int | None = None,
    measure: bool = True,
) -> QuantumCircuit:
    """
    Build a complete Grover circuit over seed values.
    """
    _require_qiskit()

    marked = sorted(set(marked_seeds))

    if iterations is None:
        iterations = optimal_grover_iterations(num_seed_qubits, len(marked))

    seed_register = QuantumRegister(num_seed_qubits, "seed")
    classical_register = ClassicalRegister(num_seed_qubits, "c")

    if measure:
        circuit = QuantumCircuit(seed_register, classical_register)
    else:
        circuit = QuantumCircuit(seed_register)

    oracle = build_phase_oracle(num_seed_qubits, marked).to_gate()
    diffuser = build_diffuser(num_seed_qubits).to_gate()

    # Uniform superposition over all seed states.
    circuit.h(seed_register)

    for _ in range(iterations):
        circuit.append(oracle, seed_register)
        circuit.append(diffuser, seed_register)

    if measure:
        circuit.measure(seed_register, classical_register)

    return circuit


def toy_lcg_marked_seeds(
    num_seed_qubits: int = 4,
    target: int = 6,
) -> list[int]:
    """
    Toy predicate from the earlier Grover demo:

        (5 * seed + 1) mod 2^n == target

    For n = 4 and target = 6, this marks seed 1.
    """
    modulus = 2**num_seed_qubits
    return [
        seed
        for seed in range(modulus)
        if (5 * seed + 1) % modulus == target
    ]

def maze_valid_marked_seeds(
    num_seed_qubits: int,
    width: int = 16,
    height: int = 16,
    generator_bits: int = 16,
    max_marked: int | None = None,
) -> list[int]:
    """
    Search over 2^num_seed_qubits seed inputs, but let the procedural
    generator use its own LCG bit width.
    """
    from generator import reversible_generator
    from classic_oracle import oracle

    marked: list[int] = []

    for seed in range(2**num_seed_qubits):
        maze = reversible_generator(
            seed=seed,
            bits=generator_bits,
            width=width,
            height=height,
        )

        result = oracle(maze)

        if result:
            marked.append(seed)

            if max_marked is not None and len(marked) >= max_marked:
                break

    return marked

#debugging code highlighting why seeds are invalid
def debug_maze_seed_space(        
    num_seed_qubits: int,
    width: int = 16,
    height: int = 16,
    generator_bits: int = 16,
) -> list[int]:
    from generator import reversible_generator
    from classic_oracle import oracle

    reasons = Counter()
    valid_seeds = []

    for seed in range(2**num_seed_qubits):
        maze = reversible_generator(
            seed=seed,
            bits=generator_bits,
            width=width,
            height=height,
        )

        result = oracle(maze)

        if result:
            valid_seeds.append(seed)
        else:
            reasons[result.reason] += 1

    print(f"Scanned seeds: {2**num_seed_qubits}")
    print(f"Valid seeds: {len(valid_seeds)}")
    print(f"First valid seeds: {valid_seeds[:20]}")
    print()
    print("Invalid reasons:")
    for reason, count in reasons.most_common():
        print(f"{count:>5} | {reason}")

    return valid_seeds

def run_local_simulation(
    circuit: QuantumCircuit,
    shots: int = 4096,
) -> dict[str, int]:
    """
    Run the circuit locally using qiskit-aer.
    """
    _require_qiskit()

    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise ImportError(
            "qiskit-aer is required for local simulation. "
            "Install it with: pip install qiskit-aer"
        ) from exc

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    job = simulator.run(compiled, shots=shots)
    result = job.result()
    return result.get_counts()


def print_top_counts(counts: dict[str, int], limit: int = 10) -> None:
    """
    Print measured seeds sorted by count.
    """
    total = sum(counts.values())

    print("Top measured seeds:")
    for bitstring, count in sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]:
        seed = qiskit_count_key_to_seed(bitstring)
        probability = count / total
        print(
            f"bitstring={bitstring} | "
            f"seed={seed:>4} | "
            f"count={count:>5} | "
            f"p={probability:.4f}"
        )

if __name__ == "__main__":
    num_seed_qubits = 16

    marked = debug_maze_seed_space(
        num_seed_qubits=num_seed_qubits,
        width=16,
        height=16,
        generator_bits=16,
    )

    if not marked:
        raise RuntimeError("No valid seeds found in this seed space.")

    iterations = optimal_grover_iterations(
        num_seed_qubits=num_seed_qubits,
        num_marked=len(marked),
    )

    print()
    print(f"Number of marked seeds: {len(marked)}")
    print(f"Grover iterations: {iterations}")
    print(f"Marked seeds: {marked}")

    circuit = build_grover_circuit(
        num_seed_qubits=num_seed_qubits,
        marked_seeds=marked,
        iterations=iterations,
    )

    print()
    print(f"Circuit qubits: {circuit.num_qubits}")
    print(f"Circuit depth: {circuit.depth()}")
    print(f"Circuit size: {circuit.size()}")

    counts = run_local_simulation(circuit, shots=4096)
    print_top_counts(counts, limit=25)

""""
if __name__ == "__main__":
    DEBUG_ONLY = False

    if DEBUG_ONLY:
        debug_maze_seed_space(
            num_seed_qubits=16,
            width=16,
            height=16,
            generator_bits=16,
        )

    else:
        num_seed_qubits = 16

        marked = maze_valid_marked_seeds(
            num_seed_qubits=num_seed_qubits,
            width=16,
            height=16,
            generator_bits=16,
        )

        print(f"Number of marked seeds: {len(marked)}")
        print(f"Marked seeds: {marked[:20]}")

        if not marked:
            raise RuntimeError("No valid seeds found in this seed space.")

        circuit = build_grover_circuit(
            num_seed_qubits=num_seed_qubits,
            marked_seeds=marked,
        )

        print(circuit.draw(fold=-1))

        counts = run_local_simulation(circuit, shots=4096)
        print_top_counts(counts)


Toy model code
if __name__ == "__main__":
    num_seed_qubits = 4

    marked = toy_lcg_marked_seeds(
        num_seed_qubits=num_seed_qubits,
        target=6,
    )

    print(f"Marked seeds: {marked}")

    circuit = build_grover_circuit(
        num_seed_qubits=num_seed_qubits,
        marked_seeds=marked,
    )

    print(circuit.draw(fold=-1))

    counts = run_local_simulation(circuit, shots=4096)
    print_top_counts(counts)
"""