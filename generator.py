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
    
    return maze

maze = generator(10, 10)
# Temporary code to output the maze to verify until the maze visualization or oracle function is implemented
print(maze.to_dict())