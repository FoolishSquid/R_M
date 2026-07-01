# config.py

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
BLUE_TILE_PENALTY_S = 5 

# --- HARDWARE PINS (BCM) ---
PIN_BUZZER = 26
PIN_LED = 19

# Ultrasonic Triggers/Echoes
PIN_TRIG_N, PIN_ECHO_N = 4, 17
PIN_TRIG_E, PIN_ECHO_E = 24, 23
PIN_TRIG_S, PIN_ECHO_S = 20, 21
PIN_TRIG_W, PIN_ECHO_W = 22, 27

# Motor Pins (Forward, Backward, Enable)
MOT_FL = (5, 6, 13)
MOT_FR = (22, 27, 12)
MOT_RL = (16, 18, 25)
MOT_RR = (8, 7, 11)