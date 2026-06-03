from maze import Maze
from maze_utils import SpecialCell, Direction
import random
from typing import Literal

def generator(w: int, h: int, seed: bytearray | bytes | float | int | str | None = None) -> Maze:
    '''A maze generation algorithm using Prim's Algorithm.'''
    if seed is not None:
        random.seed(seed)
    maze = Maze(w, h)
    
    # Pick starting and ending cells from along the edges of the maze
    edge_cells = [(x, 0) for x in range(w)] + [(x, h-1) for x in range(w)] + [(0, y) for y in range(h)] + [(w-1, y) for y in range(h)]
    starting_cell = random.choice(edge_cells)
    ending_cell = random.choice([cell for cell in edge_cells if cell != starting_cell])
    maze.mark_special_cell(*starting_cell, SpecialCell.START)
    maze.mark_special_cell(*ending_cell, SpecialCell.EXIT)
    
    # Initialize the visited and unvisited lists for the maze generation algorithm
    visited: set[Maze.Cell] = set()
    neighbors: list[Maze.Cell] = []
    unvisited: list[Maze.Cell] = [maze.get_cell(*starting_cell)]
        
    while unvisited:
        current_cell = random.choice(unvisited)
        unvisited.remove(current_cell)
        visited.add(current_cell)
        neighbors = current_cell.neighbors(maze)
        unvisited.extend([neighbor for neighbor in neighbors if neighbor not in visited and neighbor not in unvisited])
        visited_neighbors = [neighbor for neighbor in neighbors if neighbor in visited]
        
        # If there are no visited neighbors, skip to the next iteration of the loop
        if not visited_neighbors:
            continue
        
        # Choose a random visited neighbor unless you would be connecting the starting cell to the exit cell, in which case choose a random visited neighbor that is not the starting cell
        neighbor: Maze.Cell
        if current_cell.special == SpecialCell.EXIT:
            filtered = [cell for cell in visited_neighbors if cell.special != SpecialCell.START]
            if not filtered:
                visited.remove(current_cell)
                unvisited.append(current_cell)
                continue
            neighbor = random.choice(filtered)
        else:
            neighbor = random.choice(visited_neighbors)
        
        # Find the direction from the current cell to the chosen neighboring cell and remove the wall between them
        direction: Direction | None = current_cell.get_direction_to(neighbor)
        if direction is None:
            continue  # This should not happen since neighbor is a visited neighbor of current_cell
        current_cell.walls[direction] = False
        neighbor.walls[direction.opposite()] = False
        
    # Assign remaining special cells
    for special in SpecialCell:
        # These are assigned manually, as they *must* exist
        if special == SpecialCell.START or special == SpecialCell.EXIT:
            continue
        # Choose a random cell in the maze that isn't already a special cell
        cell: Maze.Cell = random.choice([cell for row in maze.cells for cell in row if cell.special is None])
        maze.mark_special_cell(*cell.coords(), special)
    
    return maze

def fixed_generator(w: int, h: int, mode: Literal['valid', 'ordering', 'paths', 'all'] = 'valid', seed: bytearray | bytes | float | int | str | None = None) -> Maze:
    '''A maze generation algorithm with logic to ensure the desired validity or fail state for testing.
    
    Modes:
    - Valid: All placements of special cells are correct, and the maze is valid.
    - Ordering: Rearrange the ordering of the special cells to make it invalid.
    - Paths: Allow multiple paths, allowing special cells to be bypassed, rendering it invalid.
    - All: All of the above invalid options, plus any that get added later.
    
    TODO: Implement different modes for maze generation.'''
    if seed is not None:
        random.seed(seed)
    maze = Maze(w, h)
    
    # TODO: Also exclude exit cell if I can figure out how to guarantee it's placement is correct
    special_cells = [special for special in SpecialCell if special != SpecialCell.START]
    
    if mode == 'ordering' or mode == 'all':
        random.shuffle(special_cells)
    
    num_special = len(special_cells)
    
    # Base case, needs at least two rows or columns per special case, not including start or exit
    if num_special * 2 > w and num_special * 2 > h:
        raise Exception('Not enough space for guaranteed special cell placement generation.')
    
    # Force an orientation if only one side is long enough, else randomly
    orientation = 'horizontal' if num_special * 2 < h else 'vertical' if num_special * 2 < w else random.choice(['horizontal', 'vertical'])
    zones: list[list[Maze.Cell]] = []
    size = w // num_special if orientation == 'vertical' else h // num_special
    remainder = w % num_special if orientation == 'vertical' else h % num_special
    
    # Pick starting and ending cells from along the edges of the maze
    edge_cells = [(x, 0) for x in range(w)] + [(x, h-1) for x in range(w)] + [(0, y) for y in range(h)] + [(w-1, y) for y in range(h)]
    
    offset = 0
    for special in special_cells:
        zone_size = size + (1 if remainder > 0 else 0)
        zone: list[Maze.Cell] = [maze.get_cell(offset + x, y) for x in range(zone_size) for y in range(h)] if orientation == 'vertical' else [maze.get_cell(x, offset + y) for x in range(w) for y in range(zone_size)]
        remainder -= 1
        visited: set[Maze.Cell] = set()
        unvisited: list[Maze.Cell] = []
        
        cell: Maze.Cell | None = None
        
        if special == SpecialCell.EXIT:
            cell = random.choice([cell for cell in zone if cell.coords() in edge_cells])
            # if special == SpecialCell.START:
            #     # Connect a random cell in the start zone to the next
            #     start_connect: Maze.Cell = random.choice([c for c in zone if c.x == zone_size - 1] if orientation == 'vertical' else [c for c in zone if c.y == zone_size - 1])
            #     neighbor = start_connect.get_neighbor(Direction.RIGHT if orientation == 'vertical' else Direction.DOWN, maze) # type: ignore
            #     neighbor.walls[Direction.LEFT if orientation == 'vertical' else Direction.UP] = False
            #     start_connect.walls[Direction.RIGHT if orientation == 'vertical' else Direction.DOWN] = False
        else:
            # Place the special cell along the zone boundry to the next
            # So we can use it as the path to the next zone
            cell = random.choice([cell for cell in zone if cell.x == offset + zone_size - 1] if orientation == 'vertical' else [cell for cell in zone if cell.y == offset + zone_size - 1])
            # Connect these special cells to the next zones
            neighbor: Maze.Cell = cell.get_neighbor(Direction.RIGHT if orientation == 'vertical' else Direction.DOWN, maze) # type: ignore
            neighbor.walls[Direction.LEFT if orientation == 'vertical' else Direction.UP] = False
            cell.walls[Direction.RIGHT if orientation == 'vertical' else Direction.DOWN] = False
            if len(zones) == 0:
                start = random.choice([c for c in zone if c.coords() in edge_cells and c != cell])
                maze.mark_special_cell(*start.coords(), SpecialCell.START)
            # elif len(zones) == num_special - 1:
            #     end = random.choice([c for c in zone if c.coords() in edge_cells and c != cell])
            #     maze.mark_special_cell(*end.coords(), SpecialCell.EXIT)
        maze.mark_special_cell(*cell.coords(), special)
        
        unvisited.append(cell)
        
        while unvisited:
            current_cell = random.choice(unvisited)
            unvisited.remove(current_cell)
            visited.add(current_cell)
            neighbors = [cell for cell in current_cell.neighbors(maze) if cell in zone]
            unvisited.extend([neighbor for neighbor in neighbors if neighbor not in visited and neighbor not in unvisited])
            visited_neighbors = [neighbor for neighbor in neighbors if neighbor in visited]
            
            if not visited_neighbors:
                continue
            
            neighbor = random.choice(visited_neighbors)
            
            direction: Direction | None = current_cell.get_direction_to(neighbor)
            if direction is None:
                continue
            current_cell.walls[direction] = False
            neighbor.walls[direction.opposite()] = False
        
        zones.append(zone)
        offset += zone_size
    
    return maze

# maze: Maze = generator(10, 10)
# valid_maze: Maze = fixed_generator(10,10, 'valid')
# Temporary code to output the maze to verify until the maze visualization or oracle function is implemented
# print(maze.to_dict())
# print(valid_maze.to_dict())
# Print all special cells
# print([cell.to_dict() for row in maze.cells for cell in row if cell.special])