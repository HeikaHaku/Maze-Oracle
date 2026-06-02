from enum import IntFlag, IntEnum, Enum
from typing import Self

class Direction(Enum):
    '''Represents the four cardinal directions for maze generation and navigation.'''
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    
    def opposite(self: Self) -> Self:
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