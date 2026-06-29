from utils import ResultTable
import classic_oracle as classic
import quantum_orace as quantum
from generator import generator, fixed_generator, reversible_generator
from time import perf_counter_ns
import random

num = 100000
results = ResultTable()
seeds = [random.getrandbits(32) for _ in range(num)]
unique_seeds = set()
start = perf_counter_ns()
for seed in seeds:
    # TODO: Skip duplicate seeds?
    unique_seeds.add(seed)
    maze = reversible_generator(seed)
    result = quantum.oracle(maze)
    end = perf_counter_ns()
    results.add(maze, result, end - start)
    start = perf_counter_ns()

print(f"Valid mazes: {len(results.valid):,}")
print(f"Invalid mazes: {len(results.invalid):,}")
print(f"Average time for valid mazes: {results.time_ns['valid'] / max(len(results.valid), 1) / 1e6:,.6f} ms")
# Since we're limiting the number of invalid mazes stored, we need to calculate the average time based on the total number of mazes minus the valid ones.
print(f"Average time for invalid mazes: {results.time_ns['invalid'] / max(num - len(results.valid), 1) / 1e6:,.6f} ms")
print(f"Average time for all mazes: {results.time_ns['total'] / num / 1e6:,.6f} ms")
print(f"Total Time for {num:,} mazes: {results.time_ns['total'] / 1e9 / 60:,.6f} minutes ({results.time_ns['total'] / 1e9:,.6f} seconds)")
print(f"Time until first valid maze: {results.time_ns['first'] / 1e6:,.6f} ms")
print(f"Unique seeds used: {len(unique_seeds):,}")
print(f"Two randomly selected valid seeds: {random.sample([result.maze.seed for result in results.valid], min(2, len(results.valid)))}")
print(f"Two randomly selected invalid seeds: {random.sample([result.maze.seed for result in results.invalid], min(2, len(results.invalid)))}")
# print(f"Two randomly selected valid mazes: {[result.maze.to_dict() for result in random.sample(results.valid, 2)]}")
# print(f"Two randomly selected invalid mazes: {[result.maze.to_dict() for result in random.sample(results.invalid, 2)]}")

print("Drawing two random valid mazes...")
[maze.draw() for maze in random.sample([result.maze for result in results.valid], min(2, len(results.valid)))]
print("Drawing two random invalid mazes...")
[maze.draw(invalid=True) for maze in random.sample([result.maze for result in results.invalid], min(2, len(results.invalid)))]