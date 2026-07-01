# hardware.py
from gpiozero import DistanceSensor, Motor, Buzzer, LED
import time
import config as cfg

# --- PERIPHERALS ---
buzzer = Buzzer(cfg.PIN_BUZZER)
led = LED(cfg.PIN_LED)

# --- SENSORS ---
sensor_n = DistanceSensor(echo=cfg.PIN_ECHO_N, trigger=cfg.PIN_TRIG_N, max_distance=2.0)  
sensor_e = DistanceSensor(echo=cfg.PIN_ECHO_E, trigger=cfg.PIN_TRIG_E, max_distance=2.0) 
sensor_s = DistanceSensor(echo=cfg.PIN_ECHO_S, trigger=cfg.PIN_TRIG_S, max_distance=2.0) 
sensor_w = DistanceSensor(echo=cfg.PIN_ECHO_W, trigger=cfg.PIN_TRIG_W, max_distance=2.0) 

# --- MOTORS ---
motor_fl = Motor(forward=cfg.MOT_FL[0], backward=cfg.MOT_FL[1], enable=cfg.MOT_FL[2])
motor_fr = Motor(forward=cfg.MOT_FR[0], backward=cfg.MOT_FR[1], enable=cfg.MOT_FR[2])
motor_rl = Motor(forward=cfg.MOT_RL[0], backward=cfg.MOT_RL[1], enable=cfg.MOT_RL[2])
motor_rr = Motor(forward=cfg.MOT_RR[0], backward=cfg.MOT_RR[1], enable=cfg.MOT_RR[2])

def get_ultrasonic_distances():
    """ Returns a dictionary of distances in cm """
    return {
        "NORTH": sensor_n.distance * 100,
        "EAST": sensor_e.distance * 100,
        "SOUTH": sensor_s.distance * 100,
        "WEST": sensor_w.distance * 100
    }

def get_tile_color(direction):
    """ Reads RGB sensor via I2C Multiplexer (Placeholder) """
    return "NORMAL"

def trigger_blue_penalty():
    """ Freezes hardware for the 5-second blue tile penalty """
    stop_motors(force=True)
    for _ in range(5):
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

def stop_motors(force=False):
    """ Kills power only if a full stop is requested """
    if force:
        motor_fl.stop()
        motor_fr.stop()
        motor_rl.stop()
        motor_rr.stop()
        time.sleep(0.1)

# --- OMNI KINEMATICS ---
def slide(direction):
    """ Executes a single timed physical slide """
    spd = cfg.DRIVE_SPEED
    if direction == "NORTH":
        motor_fl.forward(speed=spd); motor_fr.forward(speed=spd)
        motor_rl.forward(speed=spd); motor_rr.forward(speed=spd)
    elif direction == "SOUTH":
        motor_fl.backward(speed=spd); motor_fr.backward(speed=spd)
        motor_rl.backward(speed=spd); motor_rr.backward(speed=spd)
    elif direction == "EAST":
        motor_fl.forward(speed=spd); motor_fr.backward(speed=spd)
        motor_rl.backward(speed=spd); motor_rr.forward(speed=spd)
    elif direction == "WEST":
        motor_fl.backward(speed=spd); motor_fr.forward(speed=spd)
        motor_rl.forward(speed=spd); motor_rr.backward(speed=spd)
    
    time.sleep(cfg.CELL_TIME_S) 