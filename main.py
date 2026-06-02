from utils import ResultTable
import classic_oracle as classic
from generator import generator, fixed_generator
from time import perf_counter_ns

num = 100000
results = ResultTable()
start = perf_counter_ns()
for i in range(num):
    maze = generator(10, 10)
    result = classic.oracle(maze)
    end = perf_counter_ns()
    results.add(maze, result, end - start)
    start = perf_counter_ns()

time = { 'valid': sum(result.time_ns for result in results.valid), 'invalid': sum(result.time_ns for result in results.invalid) }
time['total'] = time['valid'] + time['invalid']

print(f"Valid mazes: {len(results.valid):,}")
print(f"Invalid mazes: {len(results.invalid):,}")
print(f"Average time for valid mazes: {time['valid'] / len(results.valid) / 1e6:,.6f} ms")
print(f"Average time for invalid mazes: {time['invalid'] / len(results.invalid) / 1e6:,.6f} ms")
print(f"Average time for all mazes: {time['total'] / num / 1e6:,.6f} ms")
print(f"Total Time for {num:,} mazes: {time['total'] / 1e9 / 60:,.6f} minutes ({time['total'] / 1e9:,.6f} seconds)")
# print(f"Two randomly selected valid mazes: {[result.maze.to_dict() for result in random.sample(results.valid, 2)]}")
# print(f"Two randomly selected invalid mazes: {[result.maze.to_dict() for result in random.sample(results.invalid, 2)]}")