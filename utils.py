from maze import Maze
from typing import Self, Iterator
from enum import IntFlag, IntEnum, Enum

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

class Direction(Enum):
    '''Represents the four cardinal directions for maze generation and navigation.'''
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    
    def opposite(self: Self) -> Direction:
        '''Returns the opposite direction.'''
        match self:
            case Direction.UP:
                return Direction.DOWN
            case Direction.RIGHT:
                return Direction.LEFT
            case Direction.DOWN:
                return Direction.UP
            case Direction.LEFT:
                return Direction.RIGHT
    
class SpecialCell(IntEnum):
    '''Represents special types of cells within the maze.'''
    START = 0
    KEY = 1
    BOSS = 2
    TREASURE = 3
    EXIT = 4
      
class SpecialCellOrder(IntFlag):
    START = 1
    KEY = 2
    BOSS = 4
    TREASURE = 8
    EXIT = 16
    
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