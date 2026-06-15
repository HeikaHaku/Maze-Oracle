"""
computed_lcg_oracle.py

A standalone Grover demo with a computed reversible oracle.

Search problem:
    Find a 4-bit seed such that:

        (5 * seed + 1) mod 16 == target

For target = 6, the correct seed is 1.

The oraclegit statuscomputes the predicate inside the quantum circuit:

    |seed>|0000> -> |seed>|(5*seed + 1) mod 16>

then phase-flips states where the computed value equals the target, and then
uncomputes the work register back to |0000>.
"""

from __future__ import annotations

from typing import Iterable

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def bits_little_endian(value: int, width: int) -> list[int]:
    """
    Return the binary bits of value in little-endian order.

    Example:
        value = 6 = binary 0110
        bits_little_endian(6, 4) -> [0, 1, 1, 0]

    Qubit convention in this file:
        qubit 0 stores the least significant bit.
    """
    if value < 0 or value >= 2**width:
        raise ValueError(f"Value {value} does not fit in {width} bits.")

    return [(value >> i) & 1 for i in range(width)]


def qiskit_count_key_to_seed(bitstring: str) -> int:
    """
    Convert a Qiskit measurement key into a decimal seed value.

    If we measure seed[i] -> c[i], Qiskit displays the classical result as
    c[n-1]...c[0], so int(bitstring, 2) gives the expected seed value.
    """
    return int(bitstring, 2)


# -----------------------------------------------------------------------------
# Generic Grover components
# -----------------------------------------------------------------------------


def apply_phase_flip_if_register_equals(
    circuit: QuantumCircuit,
    register: QuantumRegister,
    value: int,
) -> None:
    """
    Apply a phase flip if the given quantum register equals value.

    This implements:
        |value> -> -|value>

    and leaves the other computational basis states unchanged.

    The register is interpreted internally as little-endian:
        register[0] = least significant bit
    """
    num_qubits = len(register)
    bits = bits_little_endian(value, num_qubits)

    # Map the target value to |111...1>.
    for i, bit in enumerate(bits):
        if bit == 0:
            circuit.x(register[i])

    # Apply a phase flip to |111...1>.
    if num_qubits == 1:
        circuit.z(register[0])
    else:
        target = register[num_qubits - 1]
        controls = list(register[: num_qubits - 1])

        circuit.h(target)
        circuit.mcx(controls, target)
        circuit.h(target)

    # Undo the mapping.
    for i, bit in reversed(list(enumerate(bits))):
        if bit == 0:
            circuit.x(register[i])


def build_diffuser(num_qubits: int, name: str = "Diffuser") -> QuantumCircuit:
    """
    Build the standard Grover diffusion operator over num_qubits.

    This performs inversion about the mean on the seed register.
    """
    register = QuantumRegister(num_qubits, "seed")
    diffuser = QuantumCircuit(register, name=name)

    diffuser.h(register)
    diffuser.x(register)

    # Phase flip |111...1>.
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


# -----------------------------------------------------------------------------
# Computed reversible LCG predicate
# -----------------------------------------------------------------------------


def compute_lcg4_output(
    circuit: QuantumCircuit,
    seed: QuantumRegister,
    work: QuantumRegister,
    tmp,
) -> None:
    """
    Reversibly compute:

        work ^= (5 * seed + 1) mod 16

    This is an XOR-style reversible computation. Running this function twice
    restores the work register to its original value.

    seed bits are little-endian:
        seed[0] = least significant bit
        seed[3] = most significant bit

    work bits are also little-endian.

    For a 4-bit seed x, the output y = (5*x + 1) mod 16 has bits:

        y0 = 1 xor x0
        y1 = x0 xor x1
        y2 = x0 xor (x0 & x1) xor x2
        y3 = x1 xor (x0 & x1) xor (x0 & x2)
             xor (x0 & x1 & x2) xor x3
    """
    if len(seed) != 4 or len(work) != 4:
        raise ValueError("This toy LCG oracle requires 4 seed qubits and 4 work qubits.")

    x0, x1, x2, x3 = seed[0], seed[1], seed[2], seed[3]
    y0, y1, y2, y3 = work[0], work[1], work[2], work[3]

    # y0 = 1 xor x0
    circuit.x(y0)
    circuit.cx(x0, y0)

    # y1 = x0 xor x1
    circuit.cx(x0, y1)
    circuit.cx(x1, y1)

    # y2 = x0 xor (x0 & x1) xor x2
    circuit.cx(x0, y2)
    circuit.ccx(x0, x1, y2)
    circuit.cx(x2, y2)

    # y3 = x1 xor (x0 & x1) xor (x0 & x2)
    #      xor (x0 & x1 & x2) xor x3
    circuit.cx(x1, y3)
    circuit.cx(x3, y3)
    circuit.ccx(x0, x1, y3)
    circuit.ccx(x0, x2, y3)

    # tmp = x0 & x1
    circuit.ccx(x0, x1, tmp)

    # y3 ^= tmp & x2 = x0 & x1 & x2
    circuit.ccx(tmp, x2, y3)

    # Uncompute tmp.
    circuit.ccx(x0, x1, tmp)


def apply_computed_lcg4_phase_oracle(
    circuit: QuantumCircuit,
    seed: QuantumRegister,
    work: QuantumRegister,
    tmp,
    target: int = 6,
) -> None:
    """
    Computed phase oracle for:

        (5 * seed + 1) mod 16 == target

    It does:
        1. Compute y = f(seed) into the work register.
        2. Phase flip if y == target.
        3. Uncompute y, returning the work register to |0000>.
    """
    compute_lcg4_output(circuit, seed, work, tmp)

    apply_phase_flip_if_register_equals(
        circuit=circuit,
        register=work,
        value=target,
    )

    # Uncompute work back to |0000>.
    compute_lcg4_output(circuit, seed, work, tmp)


# -----------------------------------------------------------------------------
# Full Grover circuit builder
# -----------------------------------------------------------------------------


def build_computed_lcg4_grover_circuit(
    target: int = 6,
    iterations: int = 3,
    measure: bool = True,
) -> QuantumCircuit:
    """
    Build Grover search using the computed reversible LCG oracle.

    Search problem:
        Find seed such that (5 * seed + 1) mod 16 == target.

    For target = 6, the answer is seed = 1.
    """
    seed = QuantumRegister(4, "seed")
    work = QuantumRegister(4, "work")
    tmp = QuantumRegister(1, "tmp")

    if measure:
        c = ClassicalRegister(4, "c")
        circuit = QuantumCircuit(seed, work, tmp, c)
    else:
        circuit = QuantumCircuit(seed, work, tmp)

    diffuser = build_diffuser(4).to_gate()

    # Uniform superposition over all seed values.
    circuit.h(seed)

    for _ in range(iterations):
        apply_computed_lcg4_phase_oracle(
            circuit=circuit,
            seed=seed,
            work=work,
            tmp=tmp[0],
            target=target,
        )

        circuit.append(diffuser, seed)

    if measure:
        circuit.measure(seed, c)

    return circuit


# -----------------------------------------------------------------------------
# Classical checks and local simulation
# -----------------------------------------------------------------------------


def classical_lcg4(seed: int) -> int:
    """
    Classical version of the toy LCG predicate.
    """
    if seed < 0 or seed >= 16:
        raise ValueError("seed must be a 4-bit integer from 0 to 15.")

    return (5 * seed + 1) % 16


def valid_seeds_for_target(target: int = 6) -> list[int]:
    """
    Classical reference check, used only for printing/debugging.
    The quantum oracle does not use this list internally.
    """
    return [seed for seed in range(16) if classical_lcg4(seed) == target]


def run_local_simulation(
    circuit: QuantumCircuit,
    shots: int = 4096,
) -> dict[str, int]:
    """
    Run the circuit locally using qiskit-aer.
    """
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
            f"LCG(seed)={classical_lcg4(seed):>2} | "
            f"count={count:>5} | "
            f"p={probability:.4f}"
        )


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------


def main() -> None:
    target = 6
    iterations = 3
    shots = 4096

    print("Computed reversible LCG Grover demo")
    print(f"Predicate: (5 * seed + 1) mod 16 == {target}")
    print(f"Classical reference valid seeds: {valid_seeds_for_target(target)}")
    print(f"Grover iterations: {iterations}")
    print()

    circuit = build_computed_lcg4_grover_circuit(
        target=target,
        iterations=iterations,
    )

    print(f"Circuit qubits: {circuit.num_qubits}")
    print(f"Circuit depth: {circuit.depth()}")
    print(f"Circuit size: {circuit.size()}")
    print()

    counts = run_local_simulation(circuit, shots=shots)
    print_top_counts(counts)


if __name__ == "__main__":
    main()
