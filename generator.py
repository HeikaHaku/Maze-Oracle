from maze import Maze, Direction, SpecialCell
import random

def generator(w: int, h: int) -> Maze:
    '''A maze generation algorithm using Prim's Algorithm.'''
    maze = Maze(w, h)
    
    # Pick starting and ending cells from along the edges of the maze
    edge_cells = [(x, 0) for x in range(w)] + [(x, h-1) for x in range(w)] + [(0, y) for y in range(h)] + [(w-1, y) for y in range(h)]
    starting_cell = random.choice(edge_cells)
    ending_cell = random.choice([cell for cell in edge_cells if cell != starting_cell])
    maze.mark_special_cell(*starting_cell, SpecialCell.START)
    maze.mark_special_cell(*ending_cell, SpecialCell.EXIT)
    
    # Initialize the visited and unvisited lists for the maze generation algorithm
    visited: list[Maze.Cell] = []
    neighbors: list[Maze.Cell] = []
    unvisited: list[Maze.Cell] = [maze.get_cell(*starting_cell)]
        
    while unvisited:
        current_cell = random.choice(unvisited)
        unvisited.remove(current_cell)
        visited.append(current_cell)
        neighbors = current_cell.neighbors(maze)
        unvisited.extend([neighbor for neighbor in neighbors if neighbor not in visited and neighbor not in unvisited])
        visited_neighbors = [neighbor for neighbor in neighbors if neighbor in visited]
        
        # If there are no visited neighbors, skip to the next iteration of the loop
        if not visited_neighbors:
            continue
        
        # Choose a random visited neighbor unless you would be connecting the starting cell to the exit cell, in which case choose a random visited neighbor that is not the starting cell
        neighbor = random.choice([cell for cell in visited_neighbors if cell.special != SpecialCell.START]) if current_cell.special == SpecialCell.EXIT else random.choice(visited_neighbors)
        
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

def fixed_generator(w: int, h: int, mode: str) -> Maze:
    '''A maze generation algorithm with logic to ensure the desired validity or fail state for testing.
    TODO: Implement different modes for maze generation.'''
    maze = Maze(w, h)
    
    num_special = len(SpecialCell)
    
    # Base case, needs at least two rows or columns per special case
    # However, may later tweak to treat start and exit cells specially, like above
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
    for special in SpecialCell:
        zone_size = size + (1 if remainder > 0 else 0)
        zone: list[Maze.Cell] = [maze.get_cell(offset + x, y) for x in range(zone_size) for y in range(h)] if orientation == 'vertical' else [maze.get_cell(x, offset + y) for x in range(w) for y in range(zone_size)]
        remainder -= 1
        visited: list[Maze.Cell] = []
        unvisited: list[Maze.Cell] = []
        
        cell: Maze.Cell | None = None
        
        if special == SpecialCell.START or special == SpecialCell.EXIT:
            cell = random.choice([cell for cell in zone if cell.coords() in edge_cells])
            if special == SpecialCell.START:
                # Connect a random cell in the start zone to the next
                start_connect: Maze.Cell = random.choice([c for c in zone if c.x == zone_size - 1] if orientation == 'vertical' else [c for c in zone if c.y == zone_size - 1])
                neighbor = start_connect.get_neighbor(Direction.RIGHT if orientation == 'vertical' else Direction.DOWN, maze) # type: ignore
                neighbor.walls[Direction.LEFT if orientation == 'vertical' else Direction.UP] = False
                start_connect.walls[Direction.RIGHT if orientation == 'vertical' else Direction.DOWN] = False
        else:
            # Place the special cell along the zone boundry to the next
            # So we can use it as the path to the next zone
            cell = random.choice([cell for cell in zone if cell.x == offset + zone_size - 1] if orientation == 'vertical' else [cell for cell in zone if cell.y == offset + zone_size - 1])
            # Connect these special cells to the next zones
            neighbor: Maze.Cell = cell.get_neighbor(Direction.RIGHT if orientation == 'vertical' else Direction.DOWN, maze) # type: ignore
            neighbor.walls[Direction.LEFT if orientation == 'vertical' else Direction.UP] = False
            cell.walls[Direction.RIGHT if orientation == 'vertical' else Direction.DOWN] = False
        maze.mark_special_cell(*cell.coords(), special)
        
        unvisited.append(cell)
        
        while unvisited:
            current_cell = random.choice(unvisited)
            unvisited.remove(current_cell)
            visited.append(current_cell)
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
valid_maze: Maze = fixed_generator(10,10, 'valid')
# Temporary code to output the maze to verify until the maze visualization or oracle function is implemented
# print(maze.to_dict())
print(valid_maze.to_dict())
# Print all special cells
# print([cell.to_dict() for row in maze.cells for cell in row if cell.special])
