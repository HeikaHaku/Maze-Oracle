from utils import OracleResult, State
from maze_utils import SpecialCell, SpecialCellOrder
from maze import Maze
from generator import generator, fixed_generator
from collections import deque


def oracle(maze: Maze) -> OracleResult:
    '''Tests a given maze for validity.
    
    Conditions for validity:
    - Must have a starting cell
    - Must have an ending cell
    - Must visit every cell at least once, even if the solution does not
    - Must traverse the special cells in the following order: Start -> Key -> Boss -> Treasure -> Exit
    '''
    states: deque[State] = deque([State(maze.special_cells[SpecialCell.START], SpecialCellOrder.START)])
    visited: set[tuple[Maze.Cell, SpecialCellOrder]] = set()
    seen: set[Maze.Cell] = set()
    found_exit = False
    
    while states:
        # print(states.not_empty.acquire(), states.qsize())
        current_cell, current_state = states.popleft()
        neighbors = current_cell.neighbors(maze, True)
        for neighbor in neighbors:
            cell_state = current_state

            if neighbor.special:
                neighbor_flag = SpecialCellOrder[neighbor.special.name]
                if current_state & neighbor_flag:
                    # We have already visited this special cell, so we can skip it.
                    continue
                # If the neighbor is a special cell, we need to check if we have visited the previous special cells in the correct order
                if current_state != neighbor_flag - 1:
                    # We have achieved an invalid state, so this maze is invalid.
                    return OracleResult(False, f"Visited {neighbor.special.name} before visiting all previous special cells.")
                cell_state |= neighbor_flag
            if (neighbor, cell_state) not in visited:
                visited.add((neighbor, cell_state))
                states.append(State(neighbor, cell_state))
            if neighbor not in seen:
                seen.add(neighbor)
            if neighbor.special == SpecialCell.EXIT:
                found_exit = True
    
    if not found_exit:
        # We never found the exit, so this maze is invalid.
        return OracleResult(False, "Never found the exit.")
    
    if set([cell for row in maze.cells for cell in row]) != seen:
        # We did not visit every cell, so this maze is invalid.
        return OracleResult(False, "Did not visit every cell.")
    
    return OracleResult(True)

# maze = generator(10, 10)
# result = oracle(maze)
# print(result)
# if not result:
#     print(maze.to_dict())
