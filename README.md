# Maze-Oracle

**Research prototype and historical archive for procedural maze generation, classical validation, and quantum seed-search experiments.**

**Contributors:** Elias Sopkin and Evan Reeves  
**Repository:** https://github.com/HeikaHaku/Maze-Oracle  
**Status:** Historical research prototype; not a production software package.

## Overview

Maze-Oracle explores seed-controlled procedural generation of grid mazes and the use of an *oracle*—a Boolean validity test—to identify seeds producing mazes with specified properties. The repository preserves early investigations of whole-map generation and validity testing, together with smaller quantum-circuit demonstrations developed while studying how such predicates might be evaluated within Grover search.

A representative pipeline is:

1. Choose an integer seed.
2. Generate a grid maze and place special cells using pseudorandom outputs.
3. Evaluate the maze against reachability and ordered-objective constraints.
4. Compare classical and experimental oracle implementations, or construct a quantum search over a reduced seed space.

This is a **research model of maze generation**, not a reproduction of Minecraft's actual world-generation code. It is retained as background to later research on quantum search for procedural-generation seeds.

## What is implemented?

The archive contains **several distinct approaches**, which should not be conflated:

- **Classical maze models and validation.** `maze.py`, `maze_utils.py`, `generator.py`, and `classic_oracle.py` define a grid with walls, special locations, deterministic seeded generation, and a graph-search validity predicate. The classical predicate checks objectives including the order *start → key → boss → treasure → exit* and reachability of the grid.
- **Classical benchmarks and agreement checks.** `main.py`, `synced_seed_main.py`, `synced_seed_sweep_main.py`, and `oracle_sync_validator.py` experiment with seed sampling, runtime measurements, and consistency of oracle interfaces.
- **Grover search with precomputed marks.** `quantum_oracle.py` classically enumerates which seeds satisfy the maze predicate and then constructs a Qiskit phase oracle marking those seed values. **It does not reversibly compute the entire maze and its validity predicate in superposition.** Its `oracle(maze)` compatibility function delegates to the classical validator.
- **Computed quantum toy examples.** `computed_lcg_oracle.py` implements a small reversible linear-congruential-generator (LCG) predicate, while `reduced_quantum_seed_search.py` constructs a reduced feature-generation/search example with compute–mark–uncompute structure. These are simplified demonstrations, not a full 16 × 16 reversible maze oracle.
- **Additional prototype.** `reversible_map_gen.py` is a partial, stand-alone design sketch, not an independently runnable program in its present form.

The term *reversible* in some function names describes the intended direction of the design; it does not imply that all Python map-generation or validity routines have already been synthesized as reversible quantum circuits.

## Requirements

- **Python 3.13** is specified by the included `Pipfile`.
- **Pillow** is declared in the `Pipfile` for image rendering.
- **Qiskit** and **qiskit-aer** are needed for circuit construction and local quantum simulation, but are not currently declared in the `Pipfile`.
- **Pipenv** is convenient for reproducing the environment specified by the existing lockfile.

For a local working environment:

```bash
git clone https://github.com/HeikaHaku/Maze-Oracle.git
cd Maze-Oracle
pipenv install
pipenv run python oracle_sync_validator.py
```

For the quantum demonstration scripts, install the additional packages in the Pipenv environment:

```bash
pipenv run pip install qiskit qiskit-aer
pipenv run python computed_lcg_oracle.py
pipenv run python reduced_quantum_seed_search.py
```

**Reproducibility note:** The preceding commands describe the intended entry points from source inspection. They have not been verified here as an end-to-end successful run; software and dependency versions may require additional adjustments. Some scripts use large seed spaces or computationally expensive circuit simulations. Inspect configuration variables before running them.

## Suggested entry points

| File | Purpose |
| --- | --- |
| `generator.py` | Classical seeded maze-generation variants, including `reversible_generator` |
| `maze.py` | Grid representation, serialization, and PNG rendering |
| `classic_oracle.py` | Classical graph-search maze-validity predicate |
| `oracle_sync_validator.py` | Compare classical and compatibility-oracle outcomes over a fixed seed sample |
| `synced_seed_main.py` | Side-by-side seed-matched timing/validity comparison |
| `quantum_oracle.py` | Grover circuits using classically precomputed marked maze seeds |
| `computed_lcg_oracle.py` | Reversible circuit for a four-bit toy LCG predicate |
| `reduced_quantum_seed_search.py` | Reduced computed feature oracle with uncomputation |
| `reversible_map_gen.py` | Incomplete map-generator design sketch |
| `sample mazes/` | Example maze artifacts |

Example PNGs are also included in the repository root. Output figures produced by scripts may be written into the working directory.

## Interpretation and limitations

This repository represents **exploratory development**, with several independent or evolving models. In particular:

- The map predicates and circuits do **not** establish a complete coherent quantum implementation of whole-map generation plus pathfinding.
- A phase oracle assembled from classically enumerated valid seeds is useful for investigating Grover amplification, but does not include the reversible computational cost of recognizing an arbitrary valid maze.
- The classical `quantum_oracle.oracle(maze)` wrapper uses the same classical validation function as `classic_oracle.oracle(maze)`; agreement between these interfaces is therefore **not** independent quantum-versus-classical validation.
- The sampled-seed benchmarks are exploratory and should not be interpreted as hardware performance measurements or quantum-speedup demonstrations.
- The full-map model, reduced computed oracle, and toy LCG circuit answer different questions and should not be treated as interchangeable implementations.

The code is preserved to document the design history, early experiments, and motivation for subsequent, more resource-conscious oracle constructions.

## Citation and archival record

If you use or discuss this code, please cite the repository (preferably a fixed release or archived DOI once one is available):

```bibtex
@misc{sopkin2026mazeoracle,
  author       = {Sopkin, Elias and Reeves, Evan},
  title        = {{Maze-Oracle}: Source Code Repository},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/HeikaHaku/Maze-Oracle}
}
```

After depositing a tagged release in Zenodo, replace the mutable repository URL in formal citations with the **version-specific DOI** and add the archived version number. The repository's Git history and release tag provide further provenance.

## License

This project is distributed under the BSD 3-Clause License.
See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Elias Sopkin and Evan Reeves.

## Project context

The archive predates and is separate from later optimized oracles developed for research on Grover-inspired procedural-generation seed search. It should be cited as an **earlier experimental implementation**, not as the source code for later hardware results unless a paper explicitly establishes that correspondence.

##Acknowledgement
This work was supported in part by the U.S. Department of Energy, Office of Science, Advanced Scientific Computing Research, through the ReACT-QISE Consortium under Award No. DE-SC0024096.

## Disclosure

Evan Reeves made use of ChatGPT in writing his sections of code. Elias Sopkin did not make use of AI in his coding sections.
