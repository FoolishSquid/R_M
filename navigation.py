# navigation.py
import config as cfg
import heapq
import os

class Navigator:
    def __init__(self):
        self.x = cfg.START_X
        self.y = cfg.START_Y
        self.maze = [[0 for _ in range(cfg.MAP_HEIGHT)] for _ in range(cfg.MAP_WIDTH)]
        self.cell_costs = [[1 for _ in range(cfg.MAP_HEIGHT)] for _ in range(cfg.MAP_WIDTH)]
        self.maze[self.x][self.y] = 1 
        self.last_silver = (cfg.START_X, cfg.START_Y)
        self.state = "EXPLORING"

    def is_valid_cell(self, x, y):
        return 0 <= x < cfg.MAP_WIDTH and 0 <= y < cfg.MAP_HEIGHT

    def update_position(self, direction):
        if direction == "NORTH": self.y += 1
        elif direction == "SOUTH": self.y -= 1
        elif direction == "EAST": self.x += 1
        elif direction == "WEST": self.x -= 1

    def mark_wall(self, x, y):
        if self.is_valid_cell(x, y):
            self.maze[x][y] = 99

    def record_tile_visit(self, color_type):
        """ Updates internal memory based on the tile the robot just landed on """
        if self.maze[self.x][self.y] not in [88, 77, 99]:
            self.maze[self.x][self.y] += 1

        if color_type == "SILVER":
            self.last_silver = (self.x, self.y)
            self.maze[self.x][self.y] = 88 
        elif color_type == "BLUE":
            self.maze[self.x][self.y] = 77 
            self.cell_costs[self.x][self.y] = 6 

    def get_fastest_path_move(self, target_x, target_y):
        """ Dijkstra's Algorithm: Returns next direction string based on time weights """
        start = (self.x, self.y)
        if start == (target_x, target_y): return None

        pq = [(0, start[0], start[1])]
        lowest_cost = {start: 0}
        parent = {start: None}

        while pq:
            curr_cost, cx, cy = heapq.heappop(pq)
            if (cx, cy) == (target_x, target_y): break
            if curr_cost > lowest_cost.get((cx, cy), float('inf')): continue

            for (nx, ny), d in [((cx, cy+1), "NORTH"), ((cx+1, cy), "EAST"), 
                                ((cx, cy-1), "SOUTH"), ((cx-1, cy), "WEST")]:
                if self.is_valid_cell(nx, ny) and self.maze[nx][ny] != 99:
                    total_cost = curr_cost + self.cell_costs[nx][ny]
                    if total_cost < lowest_cost.get((nx, ny), float('inf')):
                        lowest_cost[(nx, ny)] = total_cost
                        parent[(nx, ny)] = ((cx, cy), d)
                        heapq.heappush(pq, (total_cost, nx, ny))

        curr = (target_x, target_y)
        if curr not in parent: return None
        while parent[curr] is not None:
            prev, direction = parent[curr]
            if prev == start: return direction
            curr = prev
        return None

    def find_nearest_unvisited(self):
        """ Used when boxed in: finds nearest 0-visit tile using Dijkstra """
        start = (self.x, self.y)
        pq = [(0, start[0], start[1])]
        visited = {start}
        
        while pq:
            cost, cx, cy = heapq.heappop(pq)
            if self.maze[cx][cy] == 0: return cx, cy
                
            for nx, ny in [(cx, cy+1), (cx+1, cy), (cx, cy-1), (cx-1, cy)]:
                if self.is_valid_cell(nx, ny) and self.maze[nx][ny] != 99 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    heapq.heappush(pq, (cost + self.cell_costs[nx][ny], nx, ny))
        return None

    def draw_map(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"=== OMNI-ROBOT | STATE: {self.state} ===")
        for y in range(cfg.MAP_HEIGHT - 1, -1, -1):
            row = ""
            for x in range(cfg.MAP_WIDTH):
                if x == self.x and y == self.y: row += " R "  
                elif x == cfg.GOAL_X and y == cfg.GOAL_Y: row += " G " 
                elif self.maze[x][y] == 99: row += " █ "  
                elif self.maze[x][y] == 88: row += " S "  
                elif self.maze[x][y] == 77: row += " B "  
                elif self.maze[x][y] == 0: row += " . "  
                else: row += f" {self.maze[x][y]} " 
            print(row)
        print("===================================")