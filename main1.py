from gpiozero import DistanceSensor, Motor, Buzzer, LED
from collections import deque
import time
import os

# --- MAZE DIMENSIONS & DESTINATIONS ---
MAP_WIDTH = 8   
MAP_HEIGHT = 6  
START_X = 4     
START_Y = 0     

# Define your target goal coordinates (e.g., top-right corner of the 8x6 grid)
GOAL_X = 7
GOAL_Y = 5

WALL_THRESHOLD_CM = 14.0
CELL_TIME_S = 0.90      
DRIVE_SPEED = 0.6       

# --- HARDWARE SETUP ---
buzzer = Buzzer(26)  
led = LED(19)       

# Ultrasonic Sensors
sensor_n = DistanceSensor(echo=17, trigger=4, max_distance=2.0)  
sensor_e = DistanceSensor(echo=23, trigger=24, max_distance=2.0) 
sensor_s = DistanceSensor(echo=21, trigger=20, max_distance=2.0) 
sensor_w = DistanceSensor(echo=27, trigger=22, max_distance=2.0) 

# Omni Motors
motor_fl = Motor(forward=5, backward=6, enable=13)   
motor_fr = Motor(forward=22, backward=27, enable=12) 
motor_rl = Motor(forward=16, backward=18, enable=25) 
motor_rr = Motor(forward=8, backward=7, enable=11)   

# --- STATE & MEMORY ---
robot = {'x': START_X, 'y': START_Y}
# 0 = Unvisited, 99 = Wall, 88 = Silver, 77 = Blue
maze = [[0 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]
maze[robot['x']][robot['y']] = 1 

last_silver_checkpoint = (START_X, START_Y)

# SYSTEM STATE: "EXPLORING", "RETURNING", or "FINISHED"
robot_state = "EXPLORING" 

# --- RGB COLOR SENSOR INTERFACE ---
def get_tile_color(direction):
    """ Reads the RGB sensor via I2C Multiplexer (Placeholder logic) """
    return "NORMAL" 

# --- PATHFINDING ENGINE (Breadth-First Search) ---
def get_shortest_path_move(target_x, target_y):
    """
    Analyzes the known memory matrix and calculates the immediate 
    next directional slide needed to reach the target coordinates.
    """
    start = (robot['x'], robot['y'])
    if start == (target_x, target_y):
        return None
        
    queue = deque([start])
    parent = {start: None}
    visited = {start}
    
    while queue:
        curr = queue.popleft()
        if curr == (target_x, target_y):
            break
            
        cx, cy = curr
        # Maps 4 directions of movement
        neighbors = [
            ((cx, cy + 1), "NORTH"),
            ((cx + 1, cy), "EAST"),
            ((cx, cy - 1), "SOUTH"),
            ((cx - 1, cy), "WEST")
        ]
        
        for (nx, ny), direction in neighbors:
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                # The pathfinder treats anything that isn't a confirmed wall (99) as open space
                if maze[nx][ny] != 99 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (curr, direction)
                    queue.append((nx, ny))
                    
    # Reconstruct the path backwards to find the very next step
    curr = (target_x, target_y)
    if curr not in parent:
        return None  # No available path found
        
    while parent[curr] is not None:
        prev, direction = parent[curr]
        if prev == start:
            return direction
        curr = prev
    return None

# --- MOVEMENT ACTIONS ---
def stop_motors():
    motor_fl.stop()
    motor_fr.stop()
    motor_rl.stop()
    motor_rr.stop()
    time.sleep(0.2)

def move_north():
    motor_fl.forward(speed=DRIVE_SPEED)
    motor_fr.forward(speed=DRIVE_SPEED)
    motor_rl.forward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    stop_motors()
    robot['y'] += 1

def move_south():
    motor_fl.backward(speed=DRIVE_SPEED)
    motor_fr.backward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.backward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    stop_motors()
    robot['y'] -= 1

def move_east():
    motor_fl.forward(speed=DRIVE_SPEED)
    motor_fr.backward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    stop_motors()
    robot['x'] += 1

def move_west():
    motor_fl.backward(speed=DRIVE_SPEED)
    motor_fr.forward(speed=DRIVE_SPEED)
    motor_rl.backward(speed=DRIVE_SPEED)
    motor_rr.forward(speed=DRIVE_SPEED)
    time.sleep(CELL_TIME_S)
    stop_motors()
    robot['x'] -= 1

def is_valid_cell(x, y):
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT

def print_maze():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"=== OMNI-ROBOT MAP | STATE: {robot_state} ===")
    for y in range(MAP_HEIGHT - 1, -1, -1):
        row_str = ""
        for x in range(MAP_WIDTH):
            if x == robot['x'] and y == robot['y']: row_str += " R "  
            elif x == GOAL_X and y == GOAL_Y: row_str += " G " # Visual Goal Marker
            elif maze[x][y] == 99: row_str += " █ "  
            elif maze[x][y] == 88: row_str += " S "  
            elif maze[x][y] == 77: row_str += " B "  
            elif maze[x][y] == 0: row_str += " . "  
            else: row_str += f" {maze[x][y]} " 
        print(row_str)
    print("==========================================")

# --- MAIN CONTROLLER LOOP ---
try:
    print("Booting Navigation Core...")
    time.sleep(2)
    
    while robot_state != "FINISHED":
        # Check targets before scanning
        if robot_state == "EXPLORING" and robot['x'] == GOAL_X and robot['y'] == GOAL_Y:
            robot_state = "RETURNING"
            buzzer.blink(on_time=0.3, off_time=0.2, n=3, background=False)
            print_maze()
            print("Goal Reached! Commencing Return Home via Shortest Path...")
            time.sleep(2)

        elif robot_state == "RETURNING" and robot['x'] == START_X and robot['y'] == START_Y:
            robot_state = "FINISHED"
            print_maze()
            print("Success! Back at starting position.")
            buzzer.on()
            time.sleep(1.5)
            buzzer.off()
            break

        # Read environment data
        dist_n = sensor_n.distance * 100
        dist_e = sensor_e.distance * 100
        dist_s = sensor_s.distance * 100
        dist_w = sensor_w.distance * 100 

        visits_n, visits_e, visits_s, visits_w = 999, 999, 999, 999
        color_n, color_e, color_s, color_w = "NORMAL", "NORMAL", "NORMAL", "NORMAL"
        
        # --- PHASE 1: SENSOR ACQUISITION & MAP CONTEXT ---
        # North
        tx, ty = robot['x'], robot['y'] + 1
        if is_valid_cell(tx, ty) and dist_n > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_n = get_tile_color("NORTH")
            if color_n == "BLACK":
                maze[tx][ty] = 99
                buzzer.blink(on_time=0.1, off_time=0.1, n=1, background=True)
            else: visits_n = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_n <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # East
        tx, ty = robot['x'] + 1, robot['y']
        if is_valid_cell(tx, ty) and dist_e > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_e = get_tile_color("EAST")
            if color_e == "BLACK":
                maze[tx][ty] = 99
                buzzer.blink(on_time=0.1, off_time=0.1, n=1, background=True)
            else: visits_e = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_e <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # South
        tx, ty = robot['x'], robot['y'] - 1
        if is_valid_cell(tx, ty) and dist_s > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_s = get_tile_color("SOUTH")
            if color_s == "BLACK":
                maze[tx][ty] = 99
                buzzer.blink(on_time=0.1, off_time=0.1, n=1, background=True)
            else: visits_s = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_s <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # West
        tx, ty = robot['x'] - 1, robot['y']
        if is_valid_cell(tx, ty) and dist_w > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
            color_w = get_tile_color("WEST")
            if color_w == "BLACK":
                maze[tx][ty] = 99
                buzzer.blink(on_time=0.1, off_time=0.1, n=1, background=True)
            else: visits_w = maze[tx][ty]
        elif is_valid_cell(tx, ty) and dist_w <= WALL_THRESHOLD_CM: maze[tx][ty] = 99

        # --- PHASE 2: ALGORITHMIC DECISION MAKING ---
        move_decision = None
        target_color = "NORMAL"

        if robot_state == "EXPLORING":
            # Traditional Explore Heuristic: Target the least-visited open track
            options = [visits_n, visits_e, visits_s, visits_w]
            min_visits = min(options)

            if min_visits == 999:
                print("Trapped! Triggering Checkpoint Safe Rollback...")
                robot['x'], robot['y'] = last_silver_checkpoint
                continue
            else:
                if visits_n == min_visits: move_decision, target_color = "NORTH", color_n
                elif visits_e == min_visits: move_decision, target_color = "EAST", color_e
                elif visits_s == min_visits: move_decision, target_color = "SOUTH", color_s
                elif visits_w == min_visits: move_decision, target_color = "WEST", color_w

        elif robot_state == "RETURNING":
            # Shortest Path Heuristic: Compute instantaneous path vector back to Start (START_X, START_Y)
            move_decision = get_shortest_path_move(START_X, START_Y)
            
            # Map tracking colors dynamically during flight
            if move_decision == "NORTH": target_color = color_n
            elif move_decision == "EAST": target_color = color_e
            elif move_decision == "SOUTH": target_color = color_s
            elif move_decision == "WEST": target_color = color_w

        # --- PHASE 3: EXECUTE FLIGHT PATTERN ---
        if move_decision == "NORTH": move_north()
        elif move_decision == "EAST": move_east()
        elif move_decision == "SOUTH": move_south()
        elif move_decision == "WEST": move_west()
        else:
            print("Error: No viable pathway found!")
            break

        # --- PHASE 4: UPDATE MEMORY LOGS & STEP DATA ---
        if maze[robot['x']][robot['y']] not in [88, 77, 99]:
            maze[robot['x']][robot['y']] += 1

        if target_color == "SILVER":
            last_silver_checkpoint = (robot['x'], robot['y'])
            maze[robot['x']][robot['y']] = 88 

        elif target_color == "BLUE":
            maze[robot['x']][robot['y']] = 77 
            print_maze()
            for _ in range(5):
                led.on()
                time.sleep(0.5)
                led.off()
                time.sleep(0.5)

        print_maze()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nMission Aborted Manually.")
    stop_motors()