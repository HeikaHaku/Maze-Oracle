# synced_seed_main.py
# Benchmark classic_oracle and quantum_oracle on the exact same seed list.
# Invalid mazes are counted and timed only. Only valid seeds/mazes are stored.

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter_ns
from typing import Any
import random

import classic_oracle
import quantum_oracle
from generator import reversible_generator


NUM_RUNS = 100_000
RANDOM_SEED = 12345
DRAW_VALID_MAZES = True
DRAW_COUNT = 2
MISMATCH_PRINT_LIMIT = 10


@dataclass
class OracleStats:
    name: str
    valid_count: int = 0
    invalid_count: int = 0
    valid_time_ns: int = 0
    invalid_time_ns: int = 0
    total_time_ns: int = 0
    first_valid_wall_ns: int | None = None
    valid_seeds: list[int] = field(default_factory=list)

    def record(
        self,
        *,
        seed: int,
        result: Any,
        elapsed_ns: int,
        wall_ns_at_result: int,
    ) -> None:
        self.total_time_ns += elapsed_ns

        if result:
            self.valid_count += 1
            self.valid_time_ns += elapsed_ns
            self.valid_seeds.append(seed)

            if self.first_valid_wall_ns is None:
                self.first_valid_wall_ns = wall_ns_at_result
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
        if self.first_valid_wall_ns is None:
            return 0.0
        return self.first_valid_wall_ns / 1e6


def result_reason(result: Any) -> str:
    reason = getattr(result, "reason", None)
    return "" if reason is None else str(reason)


def print_side_by_side_stats(
    *,
    classic_stats: OracleStats,
    quantum_stats: OracleStats,
    num_runs: int,
    unique_seed_count: int,
    generation_time_ns: int,
    total_wall_time_ns: int,
    mismatch_count: int,
) -> None:
    print(f"Seeds tested: {num_runs:,}")
    print(f"Unique seeds used: {unique_seed_count:,}")
    print(f"Mismatches: {mismatch_count:,}")
    print(
        f"Total maze generation time: "
        f"{generation_time_ns / 1e9 / 60:,.6f} minutes "
        f"({generation_time_ns / 1e9:,.6f} seconds)"
    )
    print(
        f"Total benchmark wall time: "
        f"{total_wall_time_ns / 1e9 / 60:,.6f} minutes "
        f"({total_wall_time_ns / 1e9:,.6f} seconds)"
    )
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
            "Time until first valid maze",
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


def main() -> None:
    seed_rng = random.Random(RANDOM_SEED)
    sample_rng = random.Random(RANDOM_SEED + 1)

    seeds = [seed_rng.getrandbits(32) for _ in range(NUM_RUNS)]
    unique_seeds = set(seeds)

    classic_stats = OracleStats("Classic oracle")
    quantum_stats = OracleStats("Quantum oracle")

    valid_mazes_by_seed = {}
    mismatches = []
    generation_time_ns = 0

    benchmark_start = perf_counter_ns()

    for seed in seeds:
        generation_start = perf_counter_ns()
        maze = reversible_generator(seed)
        generation_end = perf_counter_ns()
        generation_time_ns += generation_end - generation_start

        classic_start = perf_counter_ns()
        classic_result = classic_oracle.oracle(maze)
        classic_end = perf_counter_ns()
        classic_stats.record(
            seed=seed,
            result=classic_result,
            elapsed_ns=classic_end - classic_start,
            wall_ns_at_result=classic_end - benchmark_start,
        )

        quantum_start = perf_counter_ns()
        quantum_result = quantum_oracle.oracle(maze)
        quantum_end = perf_counter_ns()
        quantum_stats.record(
            seed=seed,
            result=quantum_result,
            elapsed_ns=quantum_end - quantum_start,
            wall_ns_at_result=quantum_end - benchmark_start,
        )

        classic_valid = bool(classic_result)
        quantum_valid = bool(quantum_result)

        if classic_valid or quantum_valid:
            valid_mazes_by_seed[seed] = maze

        if classic_valid != quantum_valid:
            mismatches.append((seed, classic_result, quantum_result))

    benchmark_end = perf_counter_ns()
    total_wall_time_ns = benchmark_end - benchmark_start

    print_side_by_side_stats(
        classic_stats=classic_stats,
        quantum_stats=quantum_stats,
        num_runs=NUM_RUNS,
        unique_seed_count=len(unique_seeds),
        generation_time_ns=generation_time_ns,
        total_wall_time_ns=total_wall_time_ns,
        mismatch_count=len(mismatches),
    )

    print()
    print(
        "Two randomly selected classic-valid seeds: "
        f"{sample_rng.sample(classic_stats.valid_seeds, min(2, len(classic_stats.valid_seeds)))}"
    )
    print(
        "Two randomly selected quantum-valid seeds: "
        f"{sample_rng.sample(quantum_stats.valid_seeds, min(2, len(quantum_stats.valid_seeds)))}"
    )

    if mismatches:
        print()
        print(f"First {min(MISMATCH_PRINT_LIMIT, len(mismatches))} mismatches:")
        for seed, classic_result, quantum_result in mismatches[:MISMATCH_PRINT_LIMIT]:
            print()
            print(f"Seed: {seed}")
            print(
                f"Classic: valid={bool(classic_result)}"
                f" reason={result_reason(classic_result)!r}"
            )
            print(
                f"Quantum: valid={bool(quantum_result)}"
                f" reason={result_reason(quantum_result)!r}"
            )

    if DRAW_VALID_MAZES:
        drawable_seeds = list(valid_mazes_by_seed)
        selected_seeds = sample_rng.sample(drawable_seeds, min(DRAW_COUNT, len(drawable_seeds)))

        print()
        print(f"Drawing {len(selected_seeds)} random valid maze(s)...")
        for seed in selected_seeds:
            print(f"Seed: {seed}")
            valid_mazes_by_seed[seed].draw()


if __name__ == "__main__":
    main()
