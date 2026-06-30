import classic_oracle
import quantum_oracle
from generator import reversible_generator
import random

num = 100000
random.seed(12345)
seeds = [random.getrandbits(32) for _ in range(num)]

mismatches = []

for seed in seeds:
    maze = reversible_generator(seed)

    classic_result = classic_oracle.oracle(maze)
    quantum_result = quantum_oracle.oracle(maze)

    if bool(classic_result) != bool(quantum_result):
        mismatches.append((seed, classic_result, quantum_result))

print(f"Seeds tested: {num:,}")
print(f"Mismatches: {len(mismatches):,}")

if mismatches:
    for seed, classic_result, quantum_result in mismatches[:10]:
        print()
        print(f"Seed: {seed}")
        print(f"Classic: {classic_result}")
        print(f"Quantum: {quantum_result}")