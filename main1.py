from gpiozero import DistanceSensor, Motor, Buzzer, LED
import time
import os
import heapq  # Used for fast Dijkstra priority queue

# --- MAZE DIMENSIONS & TARGETS ---
MAP_WIDTH = 8   
MAP_HEIGHT = 6  
START_X = 4     
START_Y = 0     
GOAL_X = 7
GOAL_Y = 5

# --- HIGH-SPEED CALIBRATION ---
WALL_THRESHOLD_CM = 14.0
CELL_TIME_S = 0.55      # Dropped from 0.90 (Faster physical tile clearing)
DRIVE_SPEED = 0.85      # Bumped from 0.60 for maximum momentum

# --- HARDWARE SETUP ---
buzzer = Buzzer(26)  
led = LED(19)       

sensor_n = DistanceSensor(echo=17, trigger=4, max_distance=2.0)  
sensor_e = DistanceSensor(echo=23, trigger=24, max_distance=2.0) 
sensor_s = DistanceSensor(echo=21, trigger=20, max_distance=2.0) 

# FIX: Moved from pins 27 and 22 to pins 9 and 10
sensor_w = DistanceSensor(echo=9, trigger=10, max_distance=2.0) 

motor_fl = Motor(forward=5, backward=6, enable=13)   
motor_fr = Motor(forward=22, backward=27, enable=12) # Now uniquely owns 22 and 27
motor_rl = Motor(forward=16, backward=18, enable=25)  
motor_rr = Motor(forward=8, backward=7, enable=11)   

# --- STATE & COST MATRIX ---
robot = {'x': START_X, 'y': START_Y}
maze = [[0 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]
maze[robot['x']][robot['y']] = 1 

# Time cost weights for pathfinding calculation
# Normal step = 1 second | Blue step = 6 seconds (1s drive + 5s delay)
cell_costs = [[1 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]

last_silver_checkpoint = (START_X, START_Y)
robot_state = "EXPLORING" 
last_move = None

def get_tile_color(direction):
    """ Reads RGB sensor via I2C Multiplexer (Placeholder) """
    return "NORMAL" 

# --- OPTIMIZED PATHFINDER (DIJKSTRA'S ALGORITHM) ---
def get_fastest_path_move(target_x, target_y):
    """
    Calculates the fastest route to target coordinates based on actual
    time penalties (weights) rather than just the number of tiles.
    """
    start = (robot['x'], robot['y'])
    if start == (target_x, target_y):
        return None

    # Priority queue stores: (cumulative_time_cost, x, y)
    pq = [(0, start[0], start[1])]
    lowest_cost = {start: 0}
    parent = {start: None}

    while pq:
        curr_cost, cx, cy = heapq.heappop(pq)

        if (cx, cy) == (target_x, target_y):
            break

        if curr_cost > lowest_cost.get((cx, cy), float('inf')):
            continue

        neighbors = [
            ((cx, cy + 1), "NORTH"),
            ((cx + 1, cy), "EAST"),
            ((cx, cy - 1), "SOUTH"),
            ((cx - 1, cy), "WEST")
        ]

        for (nx, ny), direction in neighbors:
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if maze[nx][ny] != 99:  # Avoid confirmed walls/black tiles
                    # Calculate weight based on tile profile
                    step_cost = cell_costs[nx][ny]
                    total_cost = curr_cost + step_cost

                    if total_cost < lowest_cost.get((nx, ny), float('inf')):
                        lowest_cost[(nx, ny)] = total_cost
                        parent[(nx, ny)] = ((cx, cy), direction)
                        heapq.heappush(pq, (total_cost, nx, ny))

    # Trace backwards to find immediate next action step
    curr = (target_x, target_y)
    if curr not in parent:
        return None  # No safe path available
        
    while parent[curr] is not None:
        prev, direction = parent[curr]
        if prev == start:
            return direction
        curr = prev
    return None

def find_nearest_unvisited():
    """ Finds the closest coordinate with a visit value of 0 using Dijkstra """
    start = (robot['x'], robot['y'])
    pq = [(0, start[0], start[1])]
    visited = {start}
    
    while pq:
        cost, cx, cy = heapq.heappop(pq)
        
        if maze[cx][cy] == 0:
            return cx, cy
            
        for nx, ny in [(cx, cy+1), (cx+1, cy), (cx, cy-1), (cx-1, cy)]:
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if maze[nx][ny] != 99 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    heapq.heappush(pq, (cost + cell_costs[nx][ny], nx, ny))
    return None

# --- MOVEMENT CONTROLS ---
def stop_motors(force=False):
    """ Smart stop: maintains rolling momentum unless forced to change direction """
    if force:
        motor_fl.stop()
        motor_fr.stop()
        motor_rl.stop()
        motor_rr.stop()
        time.sleep(0.1)

def move_north():
    motor_fl.forward(speed=DRIVE_SPEED)
    motor_fr.forward(speed=DRIVE_SPEED)
    motor_rl.forward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    robot['y'] += 1

def move_south():
    motor_fl.backward(speed=DRIVE_SPEED)
    motor_fr.backward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.backward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    robot['y'] -= 1

def move_east():
    motor_fl.forward(speed=DRIVE_SPEED)
    motor_fr.backward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    robot['x'] += 1

def move_west():
    motor_fl.backward(speed=DRIVE_SPEED)
    motor_fr.forward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    robot['x'] -= 1

def is_valid_cell(x, y):
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT

def print_maze():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"=== OMNI-ROBOT FAST RUN | STATE: {robot_state} ===")
    for y in range(MAP_HEIGHT - 1, -1, -1):
        row_str = ""
        for x in range(MAP_WIDTH):
            if x == robot['x'] and y == robot['y']: row_str += " R "  
            elif x == GOAL_X and y == GOAL_Y: row_str += " G " 
            elif maze[x][y] == 99: row_str += " █ "  
            elif maze[x][y] == 88: row_str += " S "  
            elif maze[x][y] == 77: row_str += " B "  
            elif maze[x][y] == 0: row_str += " . "  
            else: row_str += f" {maze[x][y]} " 
        print(row_str)
    print("==========================================")

# --- MAIN EXECUTOR ---
try:
    print("Booting High-Speed Performance Profile...")
    time.sleep(2)
    
    while robot_state != "FINISHED":
        # Check targets
        if robot_state == "EXPLORING" and robot['x'] == GOAL_X and robot['y'] == GOAL_Y:
            robot_state = "RETURNING"
            stop_motors(force=True)
            buzzer.blink(on_time=0.1, off_time=0.1, n=5, background=False)
            time.sleep(0.5)

        elif robot_state == "RETURNING" and robot['x'] == START_X and robot['y'] == START_Y:
            robot_state = "FINISHED"
            stop_motors(force=True)
            buzzer.on()
            time.sleep(1.0)
            buzzer.off()
            break

        # Sensor sweeps
        dist_n = sensor_n.distance * 100
        dist_e = sensor_e.distance * 100
        dist_s = sensor_s.distance * 100
        dist_w = sensor_w.distance * 100 

        visits_n, visits_e, visits_s, visits_w = 999, 999, 999, 999
        color_n, color_e, color_s, color_w = "NORMAL", "NORMAL", "NORMAL", "NORMAL"
        
        # --- PHASE 1: HARDWARE READ & WALL MEMORY MAPPING ---
        # North
        tx, ty = robot['x'], robot['y'] + 1
        if is_valid_cell(tx, ty) and dist_n > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_n = get_tile_color("NORTH")
            if color_n == "BLACK": maze[tx][ty] = 99
            else: visits_n = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_n <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # East
        tx, ty = robot['x'] + 1, robot['y']
        if is_valid_cell(tx, ty) and dist_e > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_e = get_tile_color("EAST")
            if color_e == "BLACK": maze[tx][ty] = 99
            else: visits_e = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_e <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # South
        tx, ty = robot['x'], robot['y'] - 1
        if is_valid_cell(tx, ty) and dist_s > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_s = get_tile_color("SOUTH")
            if color_s == "BLACK": maze[tx][ty] = 99
            else: visits_s = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_s <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # West
        tx, ty = robot['x'] - 1, robot['y']
        if is_valid_cell(tx, ty) and dist_w > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_w = get_tile_color("WEST")
            if color_w == "BLACK": maze[tx][ty] = 99
            else: visits_w = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_w <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # --- PHASE 2: EXTREME TIME OPTIMIZED SEARCH ---
        move_decision = None
        target_color = "NORMAL"

        if robot_state == "EXPLORING":
            options = [visits_n, visits_e, visits_s, visits_w]
            min_visits = min(options)

            if min_visits == 999:
                # If local cells are dead ends, pathfind to the nearest unvisited tile instantly
                next_target = find_nearest_unvisited()
                if next_target:
                    move_decision = get_fastest_path_move(next_target[0], next_target[1])
                else:
                    # If whole maze is explored, go to goal directly
                    move_decision = get_fastest_path_move(GOAL_X, GOAL_Y)
            else:
                if visits_n == min_visits: move_decision = "NORTH"
                elif visits_e == min_visits: move_decision = "EAST"
                elif visits_s == min_visits: move_decision = "SOUTH"
                elif visits_w == min_visits: move_decision = "WEST"
            
            # Extract target color attribute based on choice
            if move_decision == "NORTH": target_color = color_n
            elif move_decision == "EAST": target_color = color_e
            elif move_decision == "SOUTH": target_color = color_s
            elif move_decision == "WEST": target_color = color_w

        elif robot_state == "RETURNING":
            # Dijkstra Time-Optimized Calculation back to start
            move_decision = get_fastest_path_move(START_X, START_Y)
            if move_decision == "NORTH": target_color = color_n
            elif move_decision == "EAST": target_color = color_e
            elif move_decision == "SOUTH": target_color = color_s
            elif move_decision == "WEST": target_color = color_w

        # --- PHASE 3: MOMENTUM CONSERVATION MOVEMENT ---
        if move_decision != last_move:
            stop_motors(force=True)  # Only kill power if changing vectors

        if move_decision == "NORTH": move_north()
        elif move_decision == "EAST": move_east()
        elif move_decision == "SOUTH": move_south()
        elif move_decision == "WEST": move_west()
        else:
            # Trapped fallback
            robot['x'], robot['y'] = last_silver_checkpoint
            last_move = None
            continue

        last_move = move_decision

        # --- PHASE 4: UPDATE MEMORY LOGS & PENALTIES ---
        if maze[robot['x']][robot['y']] not in [88, 77, 99]:
            maze[robot['x']][robot['y']] += 1

        if target_color == "SILVER":
            last_silver_checkpoint = (robot['x'], robot['y'])
            maze[robot['x']][robot['y']] = 88 

        elif target_color == "BLUE":
            maze[robot['x']][robot['y']] = 77 
            cell_costs[robot['x']][robot['y']] = 6  # Log high cost weight to avoid this tile later
            stop_motors(force=True)
            print_maze()
            for _ in range(5):
                led.on()
                time.sleep(0.5)
                led.off()
                time.sleep(0.5)
            last_move = None # Reset momentum after stalling

        print_maze()

except KeyboardInterrupt:
    print("\nRun Terminated Early.")
    motor_fl.stop()
    motor_fr.stop()
    motor_rl.stop()
    motor_rr.stop()
