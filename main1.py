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
CELL_TIME_S = 0.55      
DRIVE_SPEED = 0.85      

# --- HARDWARE SETUP ---
buzzer = Buzzer(26)  
led = LED(19)       

sensor_n = DistanceSensor(echo=17, trigger=4, max_distance=2.0)  
sensor_e = DistanceSensor(echo=23, trigger=24, max_distance=2.0) 
sensor_s = DistanceSensor(echo=21, trigger=20, max_distance=2.0) 
sensor_w = DistanceSensor(echo=9, trigger=10, max_distance=2.0) 

motor_fl = Motor(forward=5, backward=6, enable=13)   
motor_fr = Motor(forward=22, backward=27, enable=12) 
motor_rl = Motor(forward=16, backward=18, enable=25)  
motor_rr = Motor(forward=8, backward=7, enable=11)   

# --- STATE & COST MATRIX ---
robot = {'x': START_X, 'y': START_Y}
maze = [[0 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]
maze[robot['x']][robot['y']] = 1 

cell_costs = [[1 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]

last_silver_checkpoint = (START_X, START_Y)
robot_state = "EXPLORING" 
last_move = None
return_path_actions = []  # Queue to store cached return actions

def get_tile_color(direction):
    """ Reads RGB sensor via I2C Multiplexer (Placeholder) """
    return "NORMAL" 

# --- OPTIMIZED PATHFINDER (DIJKSTRA'S ALGORITHM) ---
def get_fastest_path_sequence(target_x, target_y):
    """ Calculates and returns the full list of directional moves to a target """
    start = (robot['x'], robot['y'])
    if start == (target_x, target_y):
        return []

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
            ((cx, cy + 1), "NORTH"), ((cx + 1, cy), "EAST"),
            ((cx, cy - 1), "SOUTH"), ((cx - 1, cy), "WEST")
        ]

        for (nx, ny), direction in neighbors:
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                if maze[nx][ny] != 99:
                    total_cost = curr_cost + cell_costs[nx][ny]
                    if total_cost < lowest_cost.get((nx, ny), float('inf')):
                        lowest_cost[(nx, ny)] = total_cost
                        parent[(nx, ny)] = ((cx, cy), direction)
                        heapq.heappush(pq, (total_cost, nx, ny))

    # Trace backwards to assemble full path
    path = []
    curr = (target_x, target_y)
    if curr not in parent:
        return []
        
    while parent[curr] is not None:
        prev, direction = parent[curr]
        path.append(direction)
        curr = prev
    
    path.reverse()
    return path

def find_nearest_unvisited():
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
    if force:
        motor_fl.stop()
        motor_fr.stop()
        motor_rl.stop()
        motor_rr.stop()
        time.sleep(0.1)

def execute_step(move_type):
    """ Non-blocking step controller: execution split into windows for sensor safety checks """
    intervals = 5
    sleep_slice = CELL_TIME_S / intervals
    
    for _ in range(intervals):
        if move_type == "NORTH":
            motor_fl.forward(speed=DRIVE_SPEED); motor_fr.forward(speed=DRIVE_SPEED)
            motor_rl.forward(speed=DRIVE_SPEED); motor_rr.forward(speed=DRIVE_SPEED)
        elif move_type == "SOUTH":
            motor_fl.backward(speed=DRIVE_SPEED); motor_fr.backward(speed=DRIVE_SPEED)
            motor_rl.backward(speed=DRIVE_SPEED); motor_rr.backward(speed=DRIVE_SPEED)
        elif move_type == "EAST":
            motor_fl.forward(speed=DRIVE_SPEED); motor_fr.backward(speed=DRIVE_SPEED)
            motor_rl.backward(speed=DRIVE_SPEED); motor_rr.forward(speed=DRIVE_SPEED)
        elif move_type == "WEST":
            motor_fl.backward(speed=DRIVE_SPEED); motor_fr.forward(speed=DRIVE_SPEED)
            motor_rl.backward(speed=DRIVE_SPEED); motor_rr.backward(speed=DRIVE_SPEED)
        
        time.sleep(sleep_slice)
        # Dynamic Emergency Stop could be injected here if sensors read < 4cm

    if move_type == "NORTH": robot['y'] += 1
    elif move_type == "SOUTH": robot['y'] -= 1
    elif move_type == "EAST": robot['x'] += 1
    elif move_type == "WEST": robot['x'] -= 1

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
    
    # Mapping configuration array to run Phase 1 clean and DRY
    sensor_map = {
        "NORTH": (0, 1, sensor_n),
        "EAST":  (1, 0, sensor_e),
        "SOUTH": (0, -1, sensor_s),
        "WEST":  (-1, 0, sensor_w)
    }

    while robot_state != "FINISHED":
        if robot_state == "EXPLORING" and robot['x'] == GOAL_X and robot['y'] == GOAL_Y:
            robot_state = "RETURNING"
            stop_motors(force=True)
            buzzer.blink(on_time=0.1, off_time=0.1, n=5, background=False)
            time.sleep(0.5)
            # CACHING: Calculate absolute fastest reverse path back to start once
            return_path_actions = get_fastest_path_sequence(START_X, START_Y)

        elif robot_state == "RETURNING" and robot['x'] == START_X and robot['y'] == START_Y:
            robot_state = "FINISHED"
            stop_motors(force=True)
            buzzer.on(); time.sleep(1.0); buzzer.off()
            break

        # --- PHASE 1: HARDWARE READ & WALL MEMORY MAPPING (REFRACTORED/DRY) ---
        sensor_data = {}
        for direction, (dx, dy, sensor_obj) in sensor_map.items():
            dist = sensor_obj.distance * 100
            tx, ty = robot['x'] + dx, robot['y'] + dy
            
            # Default fallbacks if cell is a wall/invalid
            sensor_data[direction] = {"visits": 999, "color": "NORMAL"}
            
            if is_valid_cell(tx, ty):
                if dist > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
                    tile_color = get_tile_color(direction)
                    sensor_data[direction]["color"] = tile_color
                    if tile_color == "BLACK":
                        maze[tx][ty] = 99
                    else:
                        sensor_data[direction]["visits"] = maze[tx][ty]
                elif dist <= WALL_THRESHOLD_CM:
                    maze[tx][ty] = 99

        # --- PHASE 2: TIME OPTIMIZED SEARCH ---
        move_decision = None
        target_color = "NORMAL"

        if robot_state == "EXPLORING":
            options = [sensor_data[d]["visits"] for d in ["NORTH", "EAST", "SOUTH", "WEST"]]
            min_visits = min(options)

            if min_visits == 999:
                next_target = find_nearest_unvisited()
                if next_target:
                    path = get_fastest_path_sequence(next_target[0], next_target[1])
                    if path: move_decision = path[0]
                else:
                    path = get_fastest_path_sequence(GOAL_X, GOAL_Y)
                    if path: move_decision = path[0]
            else:
                for d in ["NORTH", "EAST", "SOUTH", "WEST"]:
                    if sensor_data[d]["visits"] == min_visits:
                        move_decision = d
                        break
            
            if move_decision:
                target_color = sensor_data[move_decision]["color"]

        elif robot_state == "RETURNING":
            # Streamlined tracking: pop pre-calculated moves instead of running Dijkstra endlessly
            if return_path_actions:
                move_decision = return_path_actions.pop(0)
                target_color = sensor_data[move_decision]["color"]

        # --- PHASE 3: MOMENTUM CONSERVATION MOVEMENT ---
        if move_decision != last_move:
            stop_motors(force=True)  

        if move_decision in ["NORTH", "EAST", "SOUTH", "WEST"]:
            execute_step(move_decision)
        else:
            # FIXED: Actively calculate path to escape back to checkpoint instead of coordinate teleportation
            escape_path = get_fastest_path_sequence(last_silver_checkpoint[0], last_silver_checkpoint[1])
            if escape_path:
                execute_step(escape_path[0])
            else:
                print("Critical: Completely Trapped!")
                break

        last_move = move_decision

        # --- PHASE 4: UPDATE MEMORY LOGS & PENALTIES ---
        if maze[robot['x']][robot['y']] not in [88, 77, 99]:
            maze[robot['x']][robot['y']] += 1

        if target_color == "SILVER":
            last_silver_checkpoint = (robot['x'], robot['y'])
            maze[robot['x']][robot['y']] = 88 

        elif target_color == "BLUE":
            maze[robot['x']][robot['y']] = 77 
            cell_costs[robot['x']][robot['y']] = 6  
            stop_motors(force=True)
            print_maze()
            for _ in range(5):
                led.on(); time.sleep(0.5); led.off(); time.sleep(0.5)
            last_move = None 
            if robot_state == "RETURNING": # Recalculate return path if a blue penalty alters optimal path weights
                return_path_actions = get_fastest_path_sequence(START_X, START_Y)

        print_maze()

except KeyboardInterrupt:
    print("\nRun Terminated Early.")
    motor_fl.stop(); motor_fr.stop(); motor_rl.stop(); motor_rr.stop()
