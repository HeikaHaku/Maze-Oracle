import classic_oracle as classic
from time import perf_counter_ns
from generator import binary_generator, random_binary_generator
from utils import ResultTable
from maze import Maze

num = 1000000
results = ResultTable()
start = perf_counter_ns()
end = start
maze: Maze
for _ in range(num):
    maze = binary_generator(10, 10)
    result = classic.oracle(maze)
    if result:
        end = perf_counter_ns()
        print(f'Valid maze found in {(end - start) / 1e9} seconds')
        maze.draw(filename='binary_test_maze.png')
        break
    
if end == start:
    print('No valid maze found')
# Print number of valid results and the time taken in seconds

