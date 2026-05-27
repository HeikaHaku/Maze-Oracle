from __future__ import annotations
import random
import json
from enum import Enum
from typing import Self

class Direction(Enum):
    '''Represents the four cardinal directions for maze generation and navigation.'''
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    
class SpecialCell(Enum):
    '''Represents special types of cells within the maze.'''
    START = 0
    KEY = 1
    BOSS = 2
    TREASURE = 3
    EXIT = 4

class Maze:
    '''Represents a maze structure with cells, walls, and special cell types.'''
    class Cell:
        '''Represents a single cell within the maze, including its position, walls, and whether it is a special cell or not.'''
        def __init__(self: Self, x: int, y: int) -> Self:
            self.x = x
            self.y = y
            self.walls = {Direction.UP: True, Direction.RIGHT: True, Direction.DOWN: True, Direction.LEFT: True}
            self.special: SpecialCell | None = None
            
        def to_dict(self: Self) -> dict:
            '''Converts the cell's properties to a dictionary format for serialization.'''
            return {
                'x': self.x,
                'y': self.y,
                'walls': {direction.name: has_wall for direction, has_wall in self.walls.items()},
                'special': self.special.name if self.special else None
            }
    
    def __init__(self: Self, width: int, height: int) -> Self:
        self.width = width
        self.height = height
        self.cells = [[self.Cell(x, y) for y in range(height)] for x in range(width)]
        self.special_cells: dict[SpecialCell, Maze.Cell] = {}
        
    def mark_special_cell(self: Self, x: int, y: int, cell_type: SpecialCell) -> None:
        '''Marks a specific cell in the maze as a special cell of the given type. There should only be one.
        TODO: Add error handling to ensure only one of each special cell type is marked.'''
        self.special_cells[cell_type] = self.cells[x][y]
        self.cells[x][y].special = cell_type
        
    def cell_valid(self: Self, x: int, y: int, direction: Direction) -> bool:
        '''Checks if moving in the given direction from the specified cell coordinates is valid (i.e., within maze bounds).'''
        match direction:
            case Direction.UP:
                return y > 0
            case Direction.RIGHT:
                return x < self.width - 1
            case Direction.DOWN:
                return y < self.height - 1
            case Direction.LEFT:
                return x > 0
        return False
        
    def to_dict(self: Self) -> dict:
        '''Converts the maze's properties to a dictionary format for serialization.'''
        return {
            'width': self.width,
            'height': self.height,
            'cells': [[cell.to_dict() for cell in row] for row in self.cells],
            'special_cells': self.special_cells
        }
    
    def to_json(self: Self) -> str:
        '''Serializes the maze to a JSON string.'''
        json.dumps(self.to_dict())
        
    def from_json(self: Self, json_str: str) -> Self:
        ''''Deserializes a JSON string to create a Maze instance.'''
        data = json.loads(json_str)
        maze = Maze(data['width'], data['height'])
        for x in range(maze.width):
            for y in range(maze.height):
                cell_data = data['cells'][x][y]
                cell = maze.cells[x][y]
                cell.walls = {Direction[direction]: has_wall for direction, has_wall in cell_data['walls'].items()}
                if cell_data['special'] and cell_data['special'] != 'None':
                    cell.special = SpecialCell[cell_data['special']]
                    maze.special_cells[cell.special] = cell
        return maze
        
    # def __str__(self: Self) -> str:
    #     pass  # Implement a method to visualize the maze as a string if needed
    
    # def render_maze(self: Self) -> None:
    #     pass  # Implement a method to render the maze visually if needed