from maze import Maze
from maze_utils import SpecialCell, Direction
from utils import LCG
import random
from typing import Literal

def generator(w: int, h: int, seed: bytearray | bytes | float | int | str | None = None) -> Maze:
    '''A maze generation algorithm using Prim's Algorithm.'''
    if seed is not None:
        random.seed(seed)
    maze = Maze(w, h, seed)
    
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
    maze = Maze(w, h, seed)
    
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

def random_binary_generator(w: int, h: int) -> Maze:
    '''A maze generation algorithm that generates a random binary string and decodes it into a maze.'''
    # Each cell should be represented by 5 bits for walls (up, right, down, left, special) and 3 bits for the special cell type (if any)
    # So each cell is represented by 8 bits (1 byte)
    num_cells = w * h
    num_bytes = num_cells + 8  # Since each cell is 1 byte and header is 8 bytes
    random_bytes = random.randbytes(num_bytes)
    
    return Maze.from_binary(random_bytes)

def binary_generator(w: int, h: int) -> Maze:
    '''A maze generation algorithm that produces a valid maze by generating a binary string with the correct format and decoding it into a maze.'''
    num_cells = w * h
    binary = bytearray()
    binary.extend(w.to_bytes(2, 'big'))
    binary.extend(h.to_bytes(2, 'big'))
    binary.extend((0).to_bytes(4, 'big'))  # Seed is not used in this generator, so set to 0
    special_cells = [SpecialCell.START, SpecialCell.KEY, SpecialCell.BOSS, SpecialCell.TREASURE, SpecialCell.EXIT]
    for _ in range(num_cells):
        byte = 0
        # Randomly decide which walls to include
        byte |= random.choice([0, 1]) << 7  # Up
        byte |= random.choice([0, 1]) << 6  # Right
        byte |= random.choice([0, 1]) << 5  # Down
        byte |= random.choice([0, 1]) << 4  # Left
        # Randomly decide if this cell is a special cell and which type
        if len(special_cells) and random.choice([False, True]):
                cell_type = random.choice(special_cells)
                byte |= 1 << 3  # Special cell bit
                byte |= cell_type.value  # Special cell type bits
                special_cells.remove(cell_type)  # Ensure each special cell is only used once
        binary.append(byte)
    return Maze.from_binary(binary)

def reversible_generator(seed: int, bits: int = 16, width: int = 16, height: int = 16) -> Maze:
    '''
    Fixed-output procedural maze generation. Uses an LCG to produce predictable results used to generate the maze.
    '''
    
    maze = Maze(width, height, seed)
    rng = LCG(seed, bits)
    
    specials = {k: rng() for k in SpecialCell}
    
    # Get cell coordinates along the perimeter
    edge_cells = [(x, y) for x in range(width) for y in range(height) if x == 0 or y == 0 or x == width - 1 or y == height - 1]
    # Get all possible cell coordinates
    cells = [(x, y) for x in range(width) for y in range(height)]
    
    for special in specials:
        if special == SpecialCell.START or special == SpecialCell.EXIT:
            coords = edge_cells[specials[special] % len(edge_cells)]
        else:
            coords = cells[specials[special] % len(cells)]
        maze.mark_special_cell(*coords, special)
        if coords in edge_cells:
            edge_cells.remove(coords)
        cells.remove(coords)

    # Set walls
    # for x in range(width):
    #     for y in range(height):
    #         if y != height - 1 and rng() >= rng.mod // 2:
    #             maze.get_cell(x, y).remove_wall(Direction.DOWN, maze)
    #         if x != width - 1 and rng() >= rng.mod // 2:
    #             maze.get_cell(x, y).remove_wall(Direction.RIGHT, maze)
    
    # Set walls
    for x in range(width):
        for y in range(height):
            can_right = x < width - 1
            can_down = y < height - 1
            
            if can_right and can_down:
                if rng() >= rng.mod // 2:
                    maze.get_cell(x, y).remove_wall(Direction.RIGHT, maze)
                else:
                    maze.get_cell(x, y).remove_wall(Direction.DOWN, maze)
            elif can_right:
                # cell = maze.get_cell(x, y)
                # if len([wall for wall in cell.walls.values() if wall]) == 4:
                #     if rng() >= rng.mod // 2:
                #         cell.remove_wall(Direction.RIGHT, maze)
                #     else:
                #         cell.remove_wall(Direction.UP, maze)
                cell = maze.get_cell(x, y)
                cell.remove_wall(Direction.RIGHT, maze)
            elif can_down:
                # cell = maze.get_cell(x, y)
                # if len([wall for wall in cell.walls.values() if wall]) == 4:
                #     if rng() >= rng.mod // 2:
                #         cell.remove_wall(Direction.DOWN, maze)
                #     else:
                #         cell.remove_wall(Direction.LEFT, maze)
                cell = maze.get_cell(x, y)
                cell.remove_wall(Direction.DOWN, maze)
    
    # Set Walls
    # current = maze.special_cells[SpecialCell.START]
    # current.visited = True
    
    # for _ in range(width * height):
    #     # Kill
    #     neighbors = current.get_unvisited_neighbors(maze)
    #     while neighbors:
    #         next = neighbors[rng() % len(neighbors)]
    #         current.remove_wall(current.get_direction_to(next), maze)
    #         next.visited = True
    #         current = next
            
    #     # Hunt
    #     for cell in maze.get_unvisited():
    #         visited = [cell for cell in cell.neighbors(maze) if cell.visited]
    #         if visited:
                
                
            

    return maze
            

# maze: Maze = generator(10, 10)
# valid_maze: Maze = fixed_generator(10,10, 'valid')
# Temporary code to output the maze to verify until the maze visualization or oracle function is implemented
# print(maze.to_dict())
# print(valid_maze.to_dict())
# Print all special cells
# print([cell.to_dict() for row in maze.cells for cell in row if cell.special])

# maze: Maze = generator(10, 10, 1269070205)
# print(maze.to_binary())
# b = maze.to_binary()
# maze2: Maze = Maze.from_binary(b['bytes'])
# print(maze.to_dict() == maze2.to_dict())
# maze.draw(filename='test.png')
# maze2.draw(filename='test2.png')

# maze: Maze = binary_generator(10, 10)
# maze.draw(filename='binary_test.png')

# for _ in range(4):
#     maze = reversible_generator(random.randint(0, 2**31 - 1))
#     maze.draw()