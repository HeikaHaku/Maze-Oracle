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
    def __init__(self: Self) -> Self:
        self.valid: list[ResultTable.Result] = []
        self.invalid: list[ResultTable.Result] = []
    def add(self: Self, maze: Maze, result: OracleResult, time_ns: int):
        if result:
            self.valid.append(ResultTable.Result(maze, result, time_ns))
        else:
            self.invalid.append(ResultTable.Result(maze, result, time_ns))
            
def lcg(state: int, bits: int = 16) -> int:
    '''Linear Congruential Generator'''
    a = 1103515245
    c = 12345
    mod = (2 ** bits) - 1
    
    return (a * state + c) % mod

# A class based version which tracks its own state.
class LCG:
    '''Linear Congruential Generator initialized with a seed and number of bits.'''
    a: int = 1103515245
    c: int = 12345
    
    def __init__(self: Self, seed: int, bits: int = 16) -> Self:
        self._state: int = seed
        self._seed: int = seed
        self.bits: int = bits
        self.mod: int = (2 ** bits) - 1
        
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
        self._state = (self.a * self._state + self.c) % self.mod
        return self._state
    
    def __call__(self: Self) -> int:
        return self.next()
    
def lcg_wrapper(seed: int, bits: int = 16) -> Callable[[], int]:
    '''A wrapper for the Linear Congruential Generator that maintains its own state.'''
    a: int = 1103515245
    c: int = 12345
    mod = (2 ** bits) - 1
    
    def lcg() -> int:
        nonlocal seed
        seed = (a * seed + c) % mod
        return seed
    
    return lcg