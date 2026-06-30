# synced_seed_sweep_main.py
# Sweep seed widths and benchmark classic_oracle and quantum_oracle on the
# exact same generated mazes.
#
# Invalid mazes are counted and timed only. Only valid seeds are stored.

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter_ns
from typing import Any, Iterable
import random

import classic_oracle
import quantum_oracle
from generator import reversible_generator


# Exhaustive sweeps are cleanest for scaling experiments. 16 bits means 65,536
# candidates, which is usually manageable. Add 18 or 20 once the smaller sweep
# is behaving the way you expect.
SEED_BIT_SWEEP = [8, 10, 12, 14, 16]

WIDTH = 16
HEIGHT = 16

# Keep this True for the real seed-width scaling experiment. If False, the
# generator uses FIXED_GENERATOR_BITS for every sweep row, which is useful only
# when you intentionally want to test external seed aliasing/truncation.
GENERATOR_BITS_MATCH_SEED_BITS = True
FIXED_GENERATOR_BITS = 16

DRAW_VALID_MAZES = False
DRAW_COUNT = 2
MISMATCH_PRINT_LIMIT = 10
VALID_SEED_SAMPLE_COUNT = 10
ALTERNATE_ORACLE_ORDER = True
SAMPLE_RANDOM_SEED = 12346


@dataclass
class OracleStats:
    name: str
    valid_count: int = 0
    invalid_count: int = 0
    valid_time_ns: int = 0
    invalid_time_ns: int = 0
    total_time_ns: int = 0
    first_valid_seed: int | None = None
    first_valid_index: int | None = None
    first_valid_cumulative_oracle_ns: int | None = None
    valid_seeds: list[int] = field(default_factory=list)

    def record(
        self,
        *,
        seed: int,
        index: int,
        result: Any,
        elapsed_ns: int,
    ) -> None:
        self.total_time_ns += elapsed_ns

        if result:
            self.valid_count += 1
            self.valid_time_ns += elapsed_ns
            self.valid_seeds.append(seed)

            if self.first_valid_seed is None:
                self.first_valid_seed = seed
                self.first_valid_index = index
                # Oracle-only cumulative time, not wall-clock time.
                self.first_valid_cumulative_oracle_ns = self.total_time_ns
        else:
            self.invalid_count += 1
            self.invalid_time_ns += elapsed_ns

    def avg_valid_ms(self) -> float:
        return self.valid_time_ns / max(self.valid_count, 1) / 1e6

    def avg_invalid_ms(self) -> float:
        return self.invalid_time_ns / max(self.invalid_count, 1) / 1e6

    def avg_all_ms(self, num_runs: int) -> float:
        return self.total_time_ns / max(num_runs, 1) / 1e6

    def total_seconds(self) -> float:
        return self.total_time_ns / 1e9

    def total_minutes(self) -> float:
        return self.total_time_ns / 1e9 / 60

    def first_valid_ms(self) -> float:
        if self.first_valid_cumulative_oracle_ns is None:
            return 0.0
        return self.first_valid_cumulative_oracle_ns / 1e6

    def first_valid_index_display(self) -> str:
        return "None" if self.first_valid_index is None else f"{self.first_valid_index:,}"

    def first_valid_seed_display(self) -> str:
        return "None" if self.first_valid_seed is None else f"{self.first_valid_seed}"


@dataclass
class SweepSummary:
    seed_bits: int
    generator_bits: int
    candidates: int
    unique_seeds: int
    classic_stats: OracleStats
    quantum_stats: OracleStats
    mismatch_count: int
    generation_time_ns: int
    wall_time_ns: int
    grover_iterations: int | None
    mismatches: list[tuple[int, Any, Any]] = field(default_factory=list)

    @property
    def valid_count(self) -> int:
        # With zero mismatches, both sides are identical. If there are mismatches,
        # report the classic count as the classical exhaustive baseline.
        return self.classic_stats.valid_count

    @property
    def valid_rate(self) -> float:
        return self.valid_count / max(self.candidates, 1)


def result_reason(result: Any) -> str:
    reason = getattr(result, "reason", None)
    return "" if reason is None else str(reason)


def timed_oracle_call(oracle_function: Any, maze: Any) -> tuple[Any, int]:
    start = perf_counter_ns()
    result = oracle_function(maze)
    end = perf_counter_ns()
    return result, end - start


def generator_bits_for(seed_bits: int) -> int:
    if GENERATOR_BITS_MATCH_SEED_BITS:
        return seed_bits
    return FIXED_GENERATOR_BITS


def estimate_grover_iterations(seed_bits: int, marked_count: int) -> int | None:
    if marked_count <= 0:
        return None
    return quantum_oracle.optimal_grover_iterations(
        num_seed_qubits=seed_bits,
        num_marked=marked_count,
    )


def run_seed_width(seed_bits: int) -> SweepSummary:
    generator_bits = generator_bits_for(seed_bits)
    candidates = 2**seed_bits

    classic_stats = OracleStats("Classic oracle")
    quantum_stats = OracleStats("Quantum oracle")
    mismatches: list[tuple[int, Any, Any]] = []
    generation_time_ns = 0

    benchmark_start = perf_counter_ns()

    for index, seed in enumerate(range(candidates), start=1):
        generation_start = perf_counter_ns()
        maze = reversible_generator(
            seed=seed,
            bits=generator_bits,
            width=WIDTH,
            height=HEIGHT,
        )
        generation_end = perf_counter_ns()
        generation_time_ns += generation_end - generation_start

        # Alternate oracle order to reduce the bias from always running one
        # oracle on a cache-warmed maze object.
        classic_first = (not ALTERNATE_ORACLE_ORDER) or (index % 2 == 1)

        if classic_first:
            classic_result, classic_elapsed_ns = timed_oracle_call(
                classic_oracle.oracle,
                maze,
            )
            quantum_result, quantum_elapsed_ns = timed_oracle_call(
                quantum_oracle.oracle,
                maze,
            )
        else:
            quantum_result, quantum_elapsed_ns = timed_oracle_call(
                quantum_oracle.oracle,
                maze,
            )
            classic_result, classic_elapsed_ns = timed_oracle_call(
                classic_oracle.oracle,
                maze,
            )

        classic_stats.record(
            seed=seed,
            index=index,
            result=classic_result,
            elapsed_ns=classic_elapsed_ns,
        )
        quantum_stats.record(
            seed=seed,
            index=index,
            result=quantum_result,
            elapsed_ns=quantum_elapsed_ns,
        )

        if bool(classic_result) != bool(quantum_result):
            mismatches.append((seed, classic_result, quantum_result))

    benchmark_end = perf_counter_ns()
    wall_time_ns = benchmark_end - benchmark_start

    return SweepSummary(
        seed_bits=seed_bits,
        generator_bits=generator_bits,
        candidates=candidates,
        unique_seeds=candidates,
        classic_stats=classic_stats,
        quantum_stats=quantum_stats,
        mismatch_count=len(mismatches),
        generation_time_ns=generation_time_ns,
        wall_time_ns=wall_time_ns,
        grover_iterations=estimate_grover_iterations(seed_bits, classic_stats.valid_count),
        mismatches=mismatches,
    )


def format_duration(ns: int) -> str:
    return f"{ns / 1e9 / 60:,.6f} minutes ({ns / 1e9:,.6f} seconds)"


def print_side_by_side_stats(summary: SweepSummary) -> None:
    classic_stats = summary.classic_stats
    quantum_stats = summary.quantum_stats
    num_runs = summary.candidates

    print()
    print("=" * 92)
    print(
        f"Seed bits: {summary.seed_bits} | "
        f"Generator bits: {summary.generator_bits} | "
        f"Candidates: {summary.candidates:,}"
    )
    print("=" * 92)
    print(f"Seeds tested: {num_runs:,}")
    print(f"Unique seeds used: {summary.unique_seeds:,}")
    print(f"Mismatches: {summary.mismatch_count:,}")
    print(f"Valid rate: {summary.valid_rate:.8%}")
    print(
        "Estimated Grover iterations: "
        f"{summary.grover_iterations if summary.grover_iterations is not None else 'N/A'}"
    )
    print(f"Alternating oracle order: {ALTERNATE_ORACLE_ORDER}")
    print(f"Total maze generation time: {format_duration(summary.generation_time_ns)}")
    print(f"Total benchmark wall time: {format_duration(summary.wall_time_ns)}")
    print()

    rows = [
        (
            "Valid mazes",
            f"{classic_stats.valid_count:,}",
            f"{quantum_stats.valid_count:,}",
        ),
        (
            "Invalid mazes",
            f"{classic_stats.invalid_count:,}",
            f"{quantum_stats.invalid_count:,}",
        ),
        (
            "Average time for valid mazes",
            f"{classic_stats.avg_valid_ms():,.6f} ms",
            f"{quantum_stats.avg_valid_ms():,.6f} ms",
        ),
        (
            "Average time for invalid mazes",
            f"{classic_stats.avg_invalid_ms():,.6f} ms",
            f"{quantum_stats.avg_invalid_ms():,.6f} ms",
        ),
        (
            "Average time for all mazes",
            f"{classic_stats.avg_all_ms(num_runs):,.6f} ms",
            f"{quantum_stats.avg_all_ms(num_runs):,.6f} ms",
        ),
        (
            f"Total oracle time for {num_runs:,} mazes",
            (
                f"{classic_stats.total_minutes():,.6f} minutes "
                f"({classic_stats.total_seconds():,.6f} seconds)"
            ),
            (
                f"{quantum_stats.total_minutes():,.6f} minutes "
                f"({quantum_stats.total_seconds():,.6f} seconds)"
            ),
        ),
        (
            "First valid seed index",
            classic_stats.first_valid_index_display(),
            quantum_stats.first_valid_index_display(),
        ),
        (
            "First valid seed",
            classic_stats.first_valid_seed_display(),
            quantum_stats.first_valid_seed_display(),
        ),
        (
            "Oracle time until first valid maze",
            f"{classic_stats.first_valid_ms():,.6f} ms",
            f"{quantum_stats.first_valid_ms():,.6f} ms",
        ),
    ]

    label_width = max(len(row[0]) for row in rows)
    classic_width = max(len("Classic oracle"), *(len(row[1]) for row in rows))
    quantum_width = max(len("Quantum oracle"), *(len(row[2]) for row in rows))

    print(
        f"{'Statistic':<{label_width}}  "
        f"{'Classic oracle':>{classic_width}}  "
        f"{'Quantum oracle':>{quantum_width}}"
    )
    print(
        f"{'-' * label_width}  "
        f"{'-' * classic_width}  "
        f"{'-' * quantum_width}"
    )

    for label, classic_value, quantum_value in rows:
        print(
            f"{label:<{label_width}}  "
            f"{classic_value:>{classic_width}}  "
            f"{quantum_value:>{quantum_width}}"
        )

    if classic_stats.valid_seeds:
        shown = classic_stats.valid_seeds[:VALID_SEED_SAMPLE_COUNT]
        suffix = "" if len(classic_stats.valid_seeds) <= VALID_SEED_SAMPLE_COUNT else " ..."
        print()
        print(f"First valid seeds: {shown}{suffix}")

    if summary.mismatches:
        print()
        print(f"First {min(MISMATCH_PRINT_LIMIT, len(summary.mismatches))} mismatches:")
        for seed, classic_result, quantum_result in summary.mismatches[:MISMATCH_PRINT_LIMIT]:
            print()
            print(f"Seed: {seed}")
            print(
                f"Classic: valid={bool(classic_result)} "
                f"reason={result_reason(classic_result)!r}"
            )
            print(
                f"Quantum: valid={bool(quantum_result)} "
                f"reason={result_reason(quantum_result)!r}"
            )


def print_scaling_table(summaries: Iterable[SweepSummary]) -> None:
    rows = []

    for summary in summaries:
        grover_display = (
            "N/A" if summary.grover_iterations is None else f"{summary.grover_iterations:,}"
        )
        rows.append(
            (
                f"{summary.seed_bits}",
                f"{summary.generator_bits}",
                f"{summary.candidates:,}",
                f"{summary.valid_count:,}",
                f"{summary.valid_rate:.8%}",
                grover_display,
                f"{summary.mismatch_count:,}",
                f"{summary.classic_stats.avg_all_ms(summary.candidates):,.6f} ms",
                f"{summary.quantum_stats.avg_all_ms(summary.candidates):,.6f} ms",
                f"{summary.classic_stats.total_seconds():,.6f} s",
                f"{summary.quantum_stats.total_seconds():,.6f} s",
                f"{summary.generation_time_ns / 1e9:,.6f} s",
                f"{summary.wall_time_ns / 1e9:,.6f} s",
            )
        )

    headers = (
        "seed bits",
        "gen bits",
        "candidates",
        "valid",
        "valid rate",
        "Grover iters",
        "mismatches",
        "classic avg",
        "quantum avg",
        "classic total",
        "quantum total",
        "gen total",
        "wall total",
    )

    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    print()
    print("=" * 92)
    print("Scaling summary")
    print("=" * 92)
    print("  ".join(f"{header:>{width}}" for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))

    for row in rows:
        print("  ".join(f"{value:>{width}}" for value, width in zip(row, widths)))


def draw_valid_samples(summaries: list[SweepSummary]) -> None:
    if not DRAW_VALID_MAZES:
        return

    sample_rng = random.Random(SAMPLE_RANDOM_SEED)

    for summary in summaries:
        valid_seeds = summary.classic_stats.valid_seeds
        selected_seeds = sample_rng.sample(valid_seeds, min(DRAW_COUNT, len(valid_seeds)))

        if not selected_seeds:
            continue

        print()
        print(f"Drawing {len(selected_seeds)} valid maze(s) for seed_bits={summary.seed_bits}...")
        for seed in selected_seeds:
            print(f"Seed: {seed}")
            maze = reversible_generator(
                seed=seed,
                bits=summary.generator_bits,
                width=WIDTH,
                height=HEIGHT,
            )
            maze.draw()


def main() -> None:
    print("Synced seed-width sweep")
    print(f"Seed-bit sweep: {SEED_BIT_SWEEP}")
    print(f"Maze size: {WIDTH} x {HEIGHT}")
    print(f"Generator bits match seed bits: {GENERATOR_BITS_MATCH_SEED_BITS}")
    if not GENERATOR_BITS_MATCH_SEED_BITS:
        print(f"Fixed generator bits: {FIXED_GENERATOR_BITS}")
    print()

    all_start = perf_counter_ns()
    summaries: list[SweepSummary] = []

    for seed_bits in SEED_BIT_SWEEP:
        summary = run_seed_width(seed_bits)
        summaries.append(summary)
        print_side_by_side_stats(summary)

    all_end = perf_counter_ns()

    print_scaling_table(summaries)

    print()
    print(f"Total sweep wall time: {format_duration(all_end - all_start)}")

    draw_valid_samples(summaries)


if __name__ == "__main__":
    main()
