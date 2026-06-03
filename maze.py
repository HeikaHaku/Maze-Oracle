from __future__ import annotations
import json
from typing import Self
from maze_utils import Direction, SpecialCell

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
            
        def neighbors(self: Self, maze: Maze, valid: bool = False) -> list[Maze.Cell]:
            '''Returns a list of neighboring cells, and if valid is set, only those that are accessible (i.e., no wall in the direction).'''
            neighbors: list[Maze.Cell] = []
            direction_map = { 
                            'x': { Direction.RIGHT: 1, Direction.LEFT: -1, Direction.UP: 0, Direction.DOWN: 0 },
                            'y': { Direction.RIGHT: 0, Direction.LEFT: 0, Direction.UP: -1, Direction.DOWN: 1 }
                            }
            for direction in Direction:
                if self.x + direction_map['x'][direction] < 0 or self.x + direction_map['x'][direction] >= maze.width:
                    continue
                if self.y + direction_map['y'][direction] < 0 or self.y + direction_map['y'][direction] >= maze.height:
                    continue
                neighbors.append(maze.cells[self.x + direction_map['x'][direction]][self.y + direction_map['y'][direction]])
            if valid:
                # Return only accessible neighbors (i.e., no wall in the direction)
                return [neighbor for neighbor in neighbors if not self.walls[Direction(self.get_direction_to(neighbor))]]
            return neighbors
        
        def get_neighbor(self: Self, direction: Direction, maze: Maze) -> Maze.Cell | None:
            '''Returns the neighboring cell in the specified direction, if it exists.'''
            direction_map = {
                'x': { Direction.RIGHT: 1, Direction.LEFT: -1, Direction.UP: 0, Direction.DOWN: 0 },
                'y': { Direction.RIGHT: 0, Direction.LEFT: 0, Direction.UP: -1, Direction.DOWN: 1 }
            }
            new_x = self.x + direction_map['x'][direction]
            new_y = self.y + direction_map['y'][direction]
            if 0 <= new_x < maze.width and 0 <= new_y < maze.height:
                return maze.cells[new_x][new_y]
            return None
        
        def get_direction_to(self: Self, other: Maze.Cell) -> Direction | None:
            '''Determines the direction from this cell to another cell, assuming they are adjacent.'''
            match (other.x - self.x, other.y - self.y):
                case (0, -1):
                    return Direction.UP
                case (1, 0):
                    return Direction.RIGHT
                case (0, 1):
                    return Direction.DOWN
                case (-1, 0):
                    return Direction.LEFT
            return None  # Not adjacent
        
        def coords(self: Self) -> tuple[int, int]:
            '''Returns the coordinates of the cell as a tuple.'''
            return (self.x, self.y)
            
        def __eq__(self: Self, other: Maze.Cell) -> bool:
            '''Checks if two cells are equal based on their coordinates.'''
            return self.x == other.x and self.y == other.y
        
        def __ne__(self: Self, other: Maze.Cell) -> bool:
            '''Checks if two cells are not equal based on their coordinates.'''
            return not self.__eq__(other)
        
        def __hash__(self: Self) -> int:
            '''Provides a hash based on the cell's coordinates for use in sets and dictionaries.'''
            return hash((self.x, self.y))
    
    def __init__(self: Self, width: int, height: int, seed: bytearray | bytes | float | int | str | None = None) -> Self:
        self.width = width
        self.height = height
        self.cells = [[self.Cell(x, y) for y in range(height)] for x in range(width)]
        self.special_cells: dict[SpecialCell, Maze.Cell] = {}
        self.seed = seed
        
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
    
    def get_cell(self: Self, x: int, y: int) -> Maze.Cell:
        '''Returns the cell object at the specified coordinates.'''
        return self.cells[x][y]
        
    def to_dict(self: Self) -> dict:
        '''Converts the maze's properties to a dictionary format for serialization.'''
        return {k: v for k, v in {
            'width': self.width,
            'height': self.height,
            'cells': [[cell.to_dict() for cell in row] for row in self.cells],
            'special_cells': {cell_type.name: {'x': cell.x, 'y': cell.y} for cell_type, cell in self.special_cells.items()},
            'seed': self.seed
        }.items() if v is not None and v != [] and v != {}}
    
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
                cell.special = SpecialCell[cell_data['special']] if cell_data['special'] else None
        for cell_type, cell_info in data['special_cells'].items():
            maze.special_cells[SpecialCell[cell_type]] = maze.cells[cell_info['x']][cell_info['y']]
        return maze
        
    # def __str__(self: Self) -> str:
    #     pass  # Implement a method to visualize the maze as a string if needed
    
    # def render_maze(self: Self) -> None:
    #     pass  # Implement a method to render the maze visually if needed