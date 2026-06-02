from maze import Maze
from typing import Self, Iterator
from maze_utils import SpecialCellOrder

class State:
    def __init__(self: Self, cell: Maze.Cell, special_order: SpecialCellOrder):
        self.cell = cell
        self.special_order = special_order
        
    def __iter__(self: Self) -> Iterator[Maze.Cell | SpecialCellOrder]:
        yield self.cell
        yield self.special_order
        
class OracleResult:
    def __init__(self: Self, valid: bool, reason: str | None = None):
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
        def __init__(self: Self, maze: Maze, result: OracleResult, time_ns: int):
            self.maze = maze
            self.result = result
            self.time_ns = time_ns
    def __init__(self: Self):
        self.valid: list[ResultTable.Result] = []
        self.invalid: list[ResultTable.Result] = []
    def add(self: Self, maze: Maze, result: OracleResult, time_ns: int):
        if result:
            self.valid.append(ResultTable.Result(maze, result, time_ns))
        else:
            self.invalid.append(ResultTable.Result(maze, result, time_ns))