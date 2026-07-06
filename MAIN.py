#This is the full and final code for the Raspberry pi

import time
import os
import heapq  
import serial  
from smbus2 import SMBus  

# --- MAZE DIMENSIONS & START ---
MAP_WIDTH = 8   
MAP_HEIGHT = 6  
START_X = 4     
START_Y = 0     

# --- HIGH-SPEED CALIBRATION & TIME BUDGET ---
WALL_THRESHOLD_CM = 14.0
CELL_TIME_S = 0.55      # ADJUST THIS: Seconds to travel exactly one 30cm block
DRIVE_SPEED = 0.85      # ADJUST THIS: Motor power (0.0 to 1.0)

TOTAL_MATCH_TIME_S = 180.0  
SAFETY_BUFFER_S = 20.0     

# --- SERIAL & DISTRIBUTED HARDWARE SETUP ---
try:
    esp32_serial = serial.Serial('/dev/serial0', baudrate=115200, timeout=0.1)
except Exception as e:
    print(f"Warning: Serial port initialization failed: {e}. Running in simulation mode.")
    esp32_serial = None

TCS_I2C_ADDR = 0x29

def read_tcs_color(bus_number):
    try:
        with SMBus(bus_number) as bus:
            bus.write_byte_data(TCS_I2C_ADDR, 0x00 | 0x80, 0x03)
            time.sleep(0.05)
            raw_data = bus.read_i2c_block_data(TCS_I2C_ADDR, 0x14 | 0x80, 8)
            return "NORMAL" # Implement strict RGB thresholds here if testing requires it
    except Exception:
        return "NORMAL"  

# --- STATE & COST MATRIX ---
robot = {'x': START_X, 'y': START_Y}
maze = [[0 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]
maze[robot['x']][robot['y']] = 1  

cell_costs = [[1 for _ in range(MAP_HEIGHT)] for _ in range(MAP_WIDTH)]

last_silver_checkpoint = (START_X, START_Y)
robot_state = "EXPLORING" 
last_move = None
return_path_actions = []  
score_counter = 1          

start_time = time.time()

# --- PATHFINDER (DIJKSTRA'S ALGORITHM) ---
def get_fastest_path_sequence(from_x, from_y, target_x, target_y):
    if (from_x, from_y) == (target_x, target_y):
        return []

    pq = [(0, from_x, from_y)]
    lowest_cost = {(from_x, from_y): 0}
    parent = {(from_x, from_y): None}

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

# --- TELEMETRY CONTROLS ---
def send_esp32_command(command_string):
    if esp32_serial and esp32_serial.is_open:
        try:
            esp32_serial.write(f"{command_string}\n".encode('utf-8'))
        except Exception as e:
            pass

def get_esp32_telemetry():
    fallback_data = {"NORTH": 100.0, "EAST": 100.0, "SOUTH": 100.0, "WEST": 100.0, "RGB3": "NORMAL", "RGB4": "NORMAL"}
    if not esp32_serial:
        return fallback_data
        
    try:
        send_esp32_command("GET_DATA")
        line = esp32_serial.readline().decode('utf-8').strip()
        parts = line.split(',')
        if len(parts) == 6:
            return {
                "NORTH": float(parts[0]), "EAST": float(parts[1]),
                "SOUTH": float(parts[2]), "WEST": float(parts[3]),
                "RGB3": parts[4], "RGB4": parts[5]
            }
    except Exception:
        pass
    return fallback_data

def stop_motors(force=False):
    if force:
        send_esp32_command("MOTOR_STOP")
        time.sleep(0.25) 

def execute_step(move_type):
    send_esp32_command(f"MOVE:{move_type}:{DRIVE_SPEED}")
    time.sleep(CELL_TIME_S) 

    if move_type == "NORTH": robot['y'] += 1
    elif move_type == "SOUTH": robot['y'] -= 1
    elif move_type == "EAST": robot['x'] += 1
    elif move_type == "WEST": robot['x'] -= 1

def is_valid_cell(x, y):
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT

def print_maze(time_left):
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"=== MATCH TIME: {time_left:.1f}s | EXPLORED: {score_counter} | STATE: {robot_state} ===")
    for y in range(MAP_HEIGHT - 1, -1, -1):
        row_str = ""
        for x in range(MAP_WIDTH):
            if x == robot['x'] and y == robot['y']: row_str += " R "  
            elif x == START_X and y == START_Y: row_str += " 🏁 " 
            elif maze[x][y] == 99: row_str += " █ "  
            elif maze[x][y] == 88: row_str += " S "  
            elif maze[x][y] == 77: row_str += " B "  
            elif maze[x][y] == 0: row_str += " . "  
            else: row_str += f" {maze[x][y]} " 
        print(row_str)

# --- MAIN EXECUTION BUS LOOP ---
try:
    print("Booting Arena Profile...")
    time.sleep(2)
    start_time = time.time()  
    
    while robot_state != "FINISHED":
        elapsed_time = time.time() - start_time
        time_remaining = TOTAL_MATCH_TIME_S - elapsed_time

        path_to_start = get_fastest_path_sequence(robot['x'], robot['y'], START_X, START_Y)
        estimated_return_time = (len(path_to_start) * CELL_TIME_S) + SAFETY_BUFFER_S

        # --- TIME CRITICAL OVERRIDE ---
        if robot_state in ["EXPLORING", "RETURNING_TO_CHECKPOINT"] and time_remaining <= estimated_return_time:
            robot_state = "RETURNING"
            stop_motors(force=True)
            send_esp32_command("ALERT:GOAL")  
            return_path_actions = path_to_start

        # --- ARRIVAL CHECK ---
        if robot_state == "RETURNING" and robot['x'] == START_X and robot['y'] == START_Y:
            robot_state = "FINISHED"
            stop_motors(force=True)
            send_esp32_command("ALERT:FINISHED")
            break

        # --- PHASE 1: BALANCED BUS HARDWARE READ & HAZARD DETECTION ---
        telemetry = get_esp32_telemetry()
        
        sensor_readings = {
            "NORTH": (0, 1, telemetry["NORTH"], read_tcs_color(1)),       
            "EAST":  (1, 0, telemetry["EAST"],  read_tcs_color(3)),       
            "SOUTH": (0, -1, telemetry["SOUTH"], telemetry["RGB3"]),       
            "WEST":  (-1, 0, telemetry["WEST"],  telemetry["RGB4"])        
        }

        sensor_data = {}
        for direction, (dx, dy, dist, tile_color) in sensor_readings.items():
            tx, ty = robot['x'] + dx, robot['y'] + dy
            sensor_data[direction] = {"visits": 999, "color": "NORMAL"}
            
            if is_valid_cell(tx, ty):
                if dist > WALL_THRESHOLD_CM and maze[tx][ty] != 99:
                    sensor_data[direction]["color"] = tile_color
                    if tile_color == "BLACK":
                        maze[tx][ty] = 99
                        send_esp32_command("ALERT:BLACK") # Sound the buzzer for hazards!
                    else:
                        sensor_data[direction]["visits"] = maze[tx][ty]
                elif dist <= WALL_THRESHOLD_CM:
                    maze[tx][ty] = 99

        # --- PHASE 2: STATE & EXPLORATION LOGIC ---
        move_decision = None
        target_color = "NORMAL"

        if robot_state == "EXPLORING":
            options = [sensor_data[d]["visits"] for d in ["NORTH", "EAST", "SOUTH", "WEST"]]
            min_visits = min(options)

            if min_visits == 999 or min_visits > 0:
                next_target = find_nearest_unvisited()
                if next_target:
                    path = get_fastest_path_sequence(robot['x'], robot['y'], next_target[0], next_target[1])
                    if path: move_decision = path[0]
            
            if not move_decision and min_visits != 999:
                for d in ["NORTH", "EAST", "SOUTH", "WEST"]:
                    if sensor_data[d]["visits"] == min_visits:
                        move_decision = d
                        break
            
            if move_decision:
                target_color = sensor_data[move_decision]["color"]
            else:
                robot_state = "RETURNING"
                return_path_actions = path_to_start

        elif robot_state in ["RETURNING", "RETURNING_TO_CHECKPOINT"]:
            if return_path_actions:
                move_decision = return_path_actions.pop(0)
                target_color = sensor_data.get(move_decision, {}).get("color", "NORMAL")
            elif robot_state == "RETURNING_TO_CHECKPOINT":
                robot_state = "EXPLORING"
                maze[robot['x']][robot['y']] = 88 
                continue 

        # --- PHASE 3: MOVEMENT COMMANDS ---
        if move_decision != last_move:
            stop_motors(force=True)  

        if move_decision in ["NORTH", "EAST", "SOUTH", "WEST"]:
            execute_step(move_decision)
        else:
            break

        last_move = move_decision

        # --- PHASE 4: MEMORY LOGS & ANTI-LOOP PROTOCOL ---
        if is_valid_cell(robot['x'], robot['y']):
            if maze[robot['x']][robot['y']] == 0:
                score_counter += 1 
            
            if maze[robot['x']][robot['y']] not in [88, 77, 99]:
                maze[robot['x']][robot['y']] += 1
            
            # ANTI-LOOP DETECTION (Silver Checkpoint logic)
            if maze[robot['x']][robot['y']] >= 4 and robot_state == "EXPLORING":
                print("LOOP DETECTED! Retreating to Silver Checkpoint...")
                path_to_silver = get_fastest_path_sequence(robot['x'], robot['y'], last_silver_checkpoint[0], last_silver_checkpoint[1])
                if path_to_silver:
                    return_path_actions = path_to_silver
                    robot_state = "RETURNING_TO_CHECKPOINT"

        if target_color == "SILVER":
            last_silver_checkpoint = (robot['x'], robot['y'])
            maze[robot['x']][robot['y']] = 88 

        elif target_color == "BLUE":
            maze[robot['x']][robot['y']] = 77 
            cell_costs[robot['x']][robot['y']] = 6  
            stop_motors(force=True)
            send_esp32_command("ALERT:BLUE")
            print_maze(time_remaining)
            time.sleep(5.0) 
            last_move = None 
            if robot_state == "RETURNING": 
                return_path_actions = get_fastest_path_sequence(robot['x'], robot['y'], START_X, START_Y)

        print_maze(time_remaining)

except KeyboardInterrupt:
    print("\nRun Terminated Early.")
    stop_motors(force=True)
