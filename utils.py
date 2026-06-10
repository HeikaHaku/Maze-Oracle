from maze import Maze
from typing import Self, Iterator, Callable
from maze_utils import SpecialCellOrder

class State:
    def __init__(self: Self, cell: Maze.Cell, special_order: SpecialCellOrder) -> Self:
        self.cell = cell
        self.special_order = special_order
        
    def __iter__(self: Self) -> Iterator[Maze.Cell | SpecialCellOrder]:
        yield self.cell
        yield self.special_order
        
class OracleResult:
    def __init__(self: Self, valid: bool, reason: str | None = None) -> Self:
        self._valid = valid
        self.reason = reason
    
    def __str__(self: Self) -> str:
        if self:
            return "The maze is valid."
        else:
            return f"The maze is invalid. Reason: {self.reason}"
        
    def __bool__(self: Self) -> bool:
        return self._valid
    
class ResultTable:
    class Result:
        def __init__(self: Self, maze: Maze, result: OracleResult, time_ns: int) -> Self:
            self.maze = maze
            self.result = result
            self.time_ns = time_ns
    def __init__(self: Self, limit: int = 100) -> Self:
        self.valid: list[ResultTable.Result] = []
        self.invalid: list[ResultTable.Result] = []
        self.time_ns = { 'valid': 0, 'invalid': 0, 'total': 0, 'first': 0 }
        self.limit = limit
    def add(self: Self, maze: Maze, result: OracleResult, time_ns: int):
        if result:
            self.valid.append(ResultTable.Result(maze, result, time_ns))
            self.time_ns['valid'] += time_ns
            if self.time_ns['first'] == 0:
                self.time_ns['first'] = self.time_ns['total'] + time_ns
        else:
            if self.limit:
                if len(self.invalid) >= self.limit:
                    self.invalid.pop(0)
            self.invalid.append(ResultTable.Result(maze, result, time_ns))
            self.time_ns['invalid'] += time_ns
        self.time_ns['total'] += time_ns
            
def lcg(state: int, bits: int = 31, mod: int | None = None) -> int:
    '''Linear Congruential Generator'''
    a = 1103515245
    c = 12345
    mod = mod if mod is not None else (2 ** bits)
    
    return (a * state + c) % mod

# A class based version which tracks its own state.
class LCG:
    '''Linear Congruential Generator initialized with a seed and number of bits.'''
    _a: int = 1103515245
    _c: int = 12345
    
    def __init__(self: Self, seed: int, bits: int = 31, mod: int | None = None) -> Self:
        self._state: int = seed
        self._seed: int = seed
        self._bits: int = bits
        self._mod: int = mod if mod is not None else (2 ** bits)
        
    @property
    def a(self: Self) -> int:
        return self._a
    
    @property
    def c(self: Self) -> int:
        return self._c
    
    @property
    def bits(self: Self) -> int:
        return self._bits
    
    @property
    def mod(self: Self) -> int:
        return self._mod

    @property
    def state(self: Self) -> int:
        return self._state
    
    @property
    def seed(self: Self) -> int:
        return self._seed
    
    @seed.setter
    def seed(self: Self, value: int) -> None:
        self._seed = value
        self._state = value
        
    def next(self: Self) -> int:
        self._state = (self._a * self._state + self._c) % self._mod
        return self._state
    
    def __call__(self: Self) -> int:
        return self.next()
    
def lcg_wrapper(seed: int, bits: int = 31, mod: int | None = None) -> Callable[[], int]:
    '''A wrapper for the Linear Congruential Generator that maintains its own state.'''
    a: int = 1103515245
    c: int = 12345
    mod = (2 ** bits) if mod is None else mod
    
    def lcg() -> int:
        nonlocal seed
        seed = (a * seed + c) % mod
        return seed
    
    return lcg