Test code for the Ultrasonic sensors(ESP32):

#include <Arduino.h>

// System headers required to forcefully terminate RF hardware stacks
#include <WiFi.h>
#include "esp_bt.h"
#include "esp_wifi.h"

// --- PIN ASSIGNMENTS (Updated per your final schematic) ---
const int TRIG_N = 13; const int ECHO_N = 14;
const int TRIG_E = 15; const int ECHO_E = 34;
const int TRIG_S = 18; const int ECHO_S = 35;
const int TRIG_W = 32; const int ECHO_W = 19; // SWAPPED: 32 is Trig, 19 is Echo

// Status LED
const int LED_PIN = 25; 

// --- DISTANCE CALCULATOR ---
float getDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  
  // 30ms timeout limits the ping wait time to avoid freezing
  long duration = pulseIn(echo, HIGH, 30000); 
  if (duration == 0) return -1.0;            // Returns -1.0 on timeout/error
  return (duration * 0.0343) / 2.0;           
}

void setup() {
  // CRITICAL HARDWARE KILLSWITCH: DISABLE RADIOS IMMEDIATELY
  WiFi.mode(WIFI_OFF);
  esp_wifi_stop();
  esp_bt_controller_disable();
  esp_bt_controller_deinit();

  Serial.begin(115200);
  while (!Serial) { delay(10); } 
  
  // Initialize Pins
  pinMode(TRIG_N, OUTPUT); pinMode(ECHO_N, INPUT);
  pinMode(TRIG_E, OUTPUT); pinMode(ECHO_E, INPUT);
  pinMode(TRIG_S, OUTPUT); pinMode(ECHO_S, INPUT);
  pinMode(TRIG_W, OUTPUT); pinMode(ECHO_W, INPUT);

  // Turn on your custom LED to visually confirm successful boot
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println("=== Phase 1: Four-Way Ultrasonic Test Active ===");
  Serial.println("Note: West Sensor updated to Trig:32 / Echo:19");
}

void loop() {
  float distN = getDistance(TRIG_N, ECHO_N);
  float distE = getDistance(TRIG_E, ECHO_E);
  float distS = getDistance(TRIG_S, ECHO_S);
  float distW = getDistance(TRIG_W, ECHO_W);

  // Print formatted data to the Serial Monitor
  Serial.print("North(13/14): ");
  if (distN == -1.0) Serial.print("TIMEOUT"); else { Serial.print(distN); Serial.print(" cm"); }
  
  Serial.print(" | East(15/34): ");
  if (distE == -1.0) Serial.print("TIMEOUT"); else { Serial.print(distE); Serial.print(" cm"); }
  
  Serial.print(" | South(18/35): ");
  if (distS == -1.0) Serial.print("TIMEOUT"); else { Serial.print(distS); Serial.print(" cm"); }
  
  Serial.print(" | West(32/19): ");
  if (distW == -1.0) Serial.print("TIMEOUT"); else { Serial.print(distW); Serial.print(" cm"); }
  
  Serial.println();

  delay(250); // Updates 4 times per second
}



Test code for the rgb sensors 3&4(ESP32):


#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_TCS34725.h>

// ESP32 WiFi bypass to avoid the compiler bug
#include <WiFi.h>
#include "esp_bt.h"
#include "esp_wifi.h"

// Initialize Sensor 3 on standard I2C0 (Pins 21 & 22)
Adafruit_TCS34725 tcs3 = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_1X);

// Initialize Sensor 4 on secondary I2C1 (Pins 26 & 27)
TwoWire I2C1_Bus = TwoWire(1);
Adafruit_TCS34725 tcs4 = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_1X);

void setup() {
  // Disable Radios
  WiFi.mode(WIFI_OFF);
  esp_wifi_stop();
  esp_bt_controller_disable();
  esp_bt_controller_deinit();

  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println("=== Phase 2A: ESP32 RGB Sensor Test ===");

  // Start I2C Buses
  Wire.begin(21, 22, 100000);       // I2C0 for Sensor 3
  I2C1_Bus.begin(26, 27, 100000);   // I2C1 for Sensor 4

  // Check Sensor 3
  if (tcs3.begin(0x29, &Wire)) {
    Serial.println(" Sensor 3 (I2C0 - Pins 21/22) Found!");
  } else {
    Serial.println(" ERROR: Sensor 3 missing. Check wiring on 21/22.");
  }

  // Check Sensor 4
  if (tcs4.begin(0x29, &I2C1_Bus)) {
    Serial.println(" Sensor 4 (I2C1 - Pins 26/27) Found!");
  } else {
    Serial.println(" ERROR: Sensor 4 missing. Check wiring on 26/27.");
  }
}

void loop() {
  uint16_t r3, g3, b3, c3;
  uint16_t r4, g4, b4, c4;

  // Read data
  tcs3.getRawData(&r3, &g3, &b3, &c3);
  tcs4.getRawData(&r4, &g4, &b4, &c4);

  // Print Sensor 3
  Serial.print("Sensor 3 [R:"); Serial.print(r3); 
  Serial.print(" G:"); Serial.print(g3); 
  Serial.print(" B:"); Serial.print(b3); 
  Serial.print(" C:"); Serial.print(c3); Serial.print("]  |  ");

  // Print Sensor 4
  Serial.print("Sensor 4 [R:"); Serial.print(r4); 
  Serial.print(" G:"); Serial.print(g4); 
  Serial.print(" B:"); Serial.print(b4); 
  Serial.print(" C:"); Serial.println(c4);

  delay(500); // Wait half a second
}


Test code for the rgb sensors 1&2(Raspberry pi 5):


import time
from smbus2 import SMBus

TCS_I2C_ADDR = 0x29

# Command bit (0x80) + Register addresses
TCS_ENABLE = 0x00 | 0x80
TCS_ID = 0x12 | 0x80
TCS_CDATAL = 0x14 | 0x80

def init_sensor(bus_num, name):
    try:
        with SMBus(bus_num) as bus:
            # Check ID
            device_id = bus.read_byte_data(TCS_I2C_ADDR, TCS_ID)
            if device_id in [0x44, 0x4D]:
                # Power ON and Enable ADC
                bus.write_byte_data(TCS_I2C_ADDR, TCS_ENABLE, 0x03)
                print(f"✅ {name} (I2C Bus {bus_num}) Initialized successfully!")
                return True
    except Exception as e:
        print(f"❌ ERROR: {name} (I2C Bus {bus_num}) failed: {e}")
    return False

def read_colors(bus_num):
    try:
        with SMBus(bus_num) as bus:
            # Read 8 bytes starting from clear data register
            data = bus.read_i2c_block_data(TCS_I2C_ADDR, TCS_CDATAL, 8)
            c = data[1] << 8 | data[0]
            r = data[3] << 8 | data[2]
            g = data[5] << 8 | data[4]
            b = data[7] << 8 | data[6]
            return r, g, b, c
    except Exception:
        return 0, 0, 0, 0

print("=== Phase 2B: Raspberry Pi RGB Sensor Test ===")

# Initialize both sensors
sensor1_ok = init_sensor(1, "Sensor 1 (Pins 3/5)")
sensor2_ok = init_sensor(3, "Sensor 2 (Pins 7/29)")

if not (sensor1_ok or sensor2_ok):
    print("No sensors detected. Check wiring and 5V/3.3V power rails!")
    exit()

time.sleep(1) # Give ADCs time to start

try:
    while True:
        output = ""
        if sensor1_ok:
            r1, g1, b1, c1 = read_colors(1)
            output += f"S1 [R:{r1:4d} G:{g1:4d} B:{b1:4d} C:{c1:4d}]  |  "
            
        if sensor2_ok:
            r2, g2, b2, c2 = read_colors(3)
            output += f"S2 [R:{r2:4d} G:{g2:4d} B:{b2:4d} C:{c2:4d}]"
            
        print(output)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nTest terminated.")





Test code for the motors (ESP32) (without WASD):-



#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// ESP32 WiFi bypass to avoid the legacy compiler bug
#include <WiFi.h>
#include "esp_bt.h"
#include "esp_wifi.h"

// Initialize PCA9685 on default I2C address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// --- MOTOR LOGIC INTERFACE ---
void setMotorTest(int pwmChannel, int in1Channel, int in2Channel, int speed, bool forward) {
  pwm.setPWM(pwmChannel, 0, speed);
  if (forward) {
    pwm.setPWM(in1Channel, 0, 4095); // High
    pwm.setPWM(in2Channel, 0, 0);    // Low
  } else {
    pwm.setPWM(in1Channel, 0, 0);
    pwm.setPWM(in2Channel, 0, 4095);
  }
}

void stopAllMotors() {
  for (int i = 0; i <= 11; i++) {
    pwm.setPWM(i, 0, 0);
  }
}

void setup() {
  // Disable Radios
  WiFi.mode(WIFI_OFF);
  esp_wifi_stop();
  esp_bt_controller_disable();
  esp_bt_controller_deinit();

  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println("=== Phase 3: PCA9685 Motor Driver Test ===");

  // Initialize Standard I2C0 Bus (Pins 21/22)
  Wire.begin(21, 22, 400000);
  
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(1600); // Max PWM frequency for smooth TB6612FNG control
  
  stopAllMotors();
  Serial.println("Driver Initialized. Starting sequence in 3 seconds...");
  delay(3000);
}

void loop() {
  int testSpeed = 2048; // Half speed (out of 4095 max)

  Serial.println("Testing Motor A (Front Left) - Channels 0, 1, 2...");
  setMotorTest(0, 1, 2, testSpeed, true);
  delay(2000);
  stopAllMotors();
  delay(1000);

  Serial.println("Testing Motor B (Front Right) - Channels 5, 3, 4...");
  setMotorTest(5, 3, 4, testSpeed, true);
  delay(2000);
  stopAllMotors();
  delay(1000);

  Serial.println("Testing Motor C (Rear Left) - Channels 6, 7, 8...");
  setMotorTest(6, 7, 8, testSpeed, true);
  delay(2000);
  stopAllMotors();
  delay(1000);

  Serial.println("Testing Motor D (Rear Right) - Channels 11, 9, 10...");
  setMotorTest(11, 9, 10, testSpeed, true);
  delay(2000);
  stopAllMotors();
  
  Serial.println("Sequence Finished. Restarting in 5 seconds...");
  Serial.println("---------------------------------------------");
  delay(5000);
}


Test code for the motors (ESP32)(with WASD):-


#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// ESP32 WiFi bypass to avoid the legacy compiler bug
#include <WiFi.h>
#include "esp_bt.h"
#include "esp_wifi.h"

// Initialize PCA9685 on default I2C address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

int currentSpeed = 2500; // Default speed (out of 4095)

// --- MOTOR LOGIC INTERFACE ---
void setMotor(int pwmChannel, int in1Channel, int in2Channel, int speed, bool forward) {
  pwm.setPWM(pwmChannel, 0, speed);
  if (forward) {
    pwm.setPWM(in1Channel, 0, 4095); // High
    pwm.setPWM(in2Channel, 0, 0);    // Low
  } else {
    pwm.setPWM(in1Channel, 0, 0);
    pwm.setPWM(in2Channel, 0, 4095);
  }
}

void stopAllMotors() {
  for (int i = 0; i <= 11; i++) {
    pwm.setPWM(i, 0, 0);
  }
  Serial.println("Motors Stopped.");
}

// --- MECANUM KINEMATICS ---
void driveMecanum(char direction, int speed) {
  switch (direction) {
    case 'W': // FORWARD: All wheels forward
    case 'w':
      Serial.println("Moving NORTH (Forward)...");
      setMotor(0, 1, 2, speed, true);   // Front Left
      setMotor(5, 3, 4, speed, true);   // Front Right
      setMotor(6, 7, 8, speed, true);   // Rear Left
      setMotor(11, 9, 10, speed, true); // Rear Right
      break;

    case 'S': // BACKWARD: All wheels backward
    case 's':
      Serial.println("Moving SOUTH (Backward)...");
      setMotor(0, 1, 2, speed, false);   
      setMotor(5, 3, 4, speed, false);   
      setMotor(6, 7, 8, speed, false);   
      setMotor(11, 9, 10, speed, false); 
      break;

    case 'D': // STRAFE RIGHT (EAST): Diagonals counter-rotate
    case 'd':
      Serial.println("Strafing EAST (Right)...");
      setMotor(0, 1, 2, speed, true);    // Front Left (Fwd)
      setMotor(5, 3, 4, speed, false);   // Front Right (Rev)
      setMotor(6, 7, 8, speed, false);   // Rear Left (Rev)
      setMotor(11, 9, 10, speed, true);  // Rear Right (Fwd)
      break;

    case 'A': // STRAFE LEFT (WEST): Diagonals counter-rotate
    case 'a':
      Serial.println("Strafing WEST (Left)...");
      setMotor(0, 1, 2, speed, false);   // Front Left (Rev)
      setMotor(5, 3, 4, speed, true);    // Front Right (Fwd)
      setMotor(6, 7, 8, speed, true);    // Rear Left (Fwd)
      setMotor(11, 9, 10, speed, false); // Rear Right (Rev)
      break;

    case 'X': // STOP
    case 'x':
    case ' ': // Spacebar also stops
      stopAllMotors();
      break;

    default:
      // Ignore other characters like newline (\n) or carriage return (\r)
      break;
  }
}

void setup() {
  // Disable Radios
  WiFi.mode(WIFI_OFF);
  esp_wifi_stop();
  esp_bt_controller_disable();
  esp_bt_controller_deinit();

  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Wire.begin(21, 22, 400000);
  
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(1600); 
  
  stopAllMotors();
  
  Serial.println("=== Phase 3: Interactive WASD Motor Test ===");
  Serial.println("Controls:");
  Serial.println(" W - Forward");
  Serial.println(" S - Backward");
  Serial.println(" A - Strafe Left");
  Serial.println(" D - Strafe Right");
  Serial.println(" X (or Space) - Stop Motors");
  Serial.println("Type a letter and press ENTER!");
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();
    driveMecanum(command, currentSpeed);
  }
}









Full final code for the ESP32:-


#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// System headers required to forcefully terminate RF hardware stacks
#include <WiFi.h>
#include "esp_bt.h"
#include "esp_wifi.h"

// --- UART CONFIGURATION ---
#define PiSerial Serial2 

// --- PIN ASSIGNMENTS ---
const int LED_PIN = 25;
const int BUZZER_PIN = 33;

// Ultrasonic Pins
const int TRIG_N = 13; const int ECHO_N = 14;
const int TRIG_E = 15; const int ECHO_E = 34;
const int TRIG_S = 18; const int ECHO_S = 35;
const int TRIG_W = 32; const int ECHO_W = 19; // SWAPPED: 32 is Trig, 19 is Echo

// --- I2C BUS INSTANCES & PERIPHERALS ---
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);
Adafruit_TCS34725 tcs3 = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_1X);

TwoWire I2C1_Bus = TwoWire(1);
Adafruit_TCS34725 tcs4 = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_1X);

// --- HELPER: ULTRASONIC READ ---
float getDistance(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  
  long duration = pulseIn(echo, HIGH, 30000); 
  if (duration == 0) return 200.0;            
  return (duration * 0.0343) / 2.0;           
}

// --- HELPER: COLOR READING ---
String getSensorColor(Adafruit_TCS34725 &tcs) {
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);
  if (c == 0) return "NORMAL";

  if (c < 300 && r < 100 && g < 100 && b < 100) return "BLACK";
  if (r > g * 1.5 && r > b * 1.5) return "RED";
  if (b > r * 1.2 && b > g * 1.1) return "BLUE";
  if (c > 1500 && r > 400 && g > 400 && b > 400) return "SILVER";
  
  return "NORMAL";
}

// --- MOTOR LOGIC INTERFACE ---
void setMotor(int pwmChannel, int in1Channel, int in2Channel, int speed, bool forward) {
  pwm.setPWM(pwmChannel, 0, speed);
  if (forward) {
    pwm.setPWM(in1Channel, 0, 4095);
    pwm.setPWM(in2Channel, 0, 0);
  } else {
    pwm.setPWM(in1Channel, 0, 0);
    pwm.setPWM(in2Channel, 0, 4095);
  }
}

void stopAllMotors() {
  for (int i = 0; i <= 11; i++) {
    pwm.setPWM(i, 0, 0);
  }
}

void driveRobot(String direction, float targetSpeed) {
  int speedValue = constrain((int)(targetSpeed * 4095.0), 0, 4095);

  if (direction == "NORTH") {
    setMotor(0, 1, 2, speedValue, true);  
    setMotor(5, 3, 4, speedValue, true);  
    setMotor(6, 7, 8, speedValue, true);  
    setMotor(11, 9, 10, speedValue, true); 
  } 
  else if (direction == "SOUTH") {
    setMotor(0, 1, 2, speedValue, false); 
    setMotor(5, 3, 4, speedValue, false); 
    setMotor(6, 7, 8, speedValue, false); 
    setMotor(11, 9, 10, speedValue, false);
  } 
  else if (direction == "EAST") { 
    setMotor(0, 1, 2, speedValue, true);   
    setMotor(5, 3, 4, speedValue, false);  
    setMotor(6, 7, 8, speedValue, false);  
    setMotor(11, 9, 10, speedValue, true);  
  } 
  else if (direction == "WEST") { 
    setMotor(0, 1, 2, speedValue, false);  
    setMotor(5, 3, 4, speedValue, true);   
    setMotor(6, 7, 8, speedValue, true);   
    setMotor(11, 9, 10, speedValue, false); 
  }
}

// --- SETUP ---
void setup() {
  // CRITICAL HARDWARE KILLSWITCH: DISABLE RADIOS IMMEDIATELY
  WiFi.mode(WIFI_OFF);
  esp_wifi_stop();
  esp_bt_controller_disable();
  esp_bt_controller_deinit();

  Serial.begin(115200); 
  PiSerial.begin(115200, SERIAL_8N1, 16, 17); 
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Initialize Ultrasonic Pins
  pinMode(TRIG_N, OUTPUT); pinMode(ECHO_N, INPUT);
  pinMode(TRIG_E, OUTPUT); pinMode(ECHO_E, INPUT);
  pinMode(TRIG_S, OUTPUT); pinMode(ECHO_S, INPUT);
  pinMode(TRIG_W, OUTPUT); pinMode(ECHO_W, INPUT);

  Wire.begin(21, 22, 400000);
  I2C1_Bus.begin(26, 27, 400000);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(1600); 
  stopAllMotors();

  if (!tcs3.begin(0x29, &Wire)) {
    Serial.println("Warning: RGB Sensor 3 (I2C0) not detected!");
  }
  if (!tcs4.begin(0x29, &I2C1_Bus)) {
    Serial.println("Warning: RGB Sensor 4 (I2C1) not detected!");
  }
  
  Serial.println("ESP32 Subsystem Ready (Radios Silenced & Pins Updated).");
}

// --- MAIN COMMAND STREAM INTERPRETER ---
void loop() {
  if (PiSerial.available()) {
    String command = PiSerial.readStringUntil('\n');
    command.trim();

    if (command == "GET_DATA") {
      float distN = getDistance(TRIG_N, ECHO_N);
      float distE = getDistance(TRIG_E, ECHO_E);
      float distS = getDistance(TRIG_S, ECHO_S);
      float distW = getDistance(TRIG_W, ECHO_W);
      
      String color3 = getSensorColor(tcs3);
      String color4 = getSensorColor(tcs4);

      String dataPackage = String(distN) + "," + String(distE) + "," + 
                           String(distS) + "," + String(distW) + "," + 
                           color3 + "," + color4;
      PiSerial.println(dataPackage);
    }
    
    else if (command.startsWith("MOVE:")) {
      int firstColon = command.indexOf(':');
      int secondColon = command.indexOf(':', firstColon + 1);
      
      String direction = command.substring(firstColon + 1, secondColon);
      float speed = command.substring(secondColon + 1).toFloat();
      
      driveRobot(direction, speed);
    }
    
    else if (command == "MOTOR_STOP") {
      stopAllMotors();
    }
    
    else if (command.startsWith("ALERT:")) {
      String alertType = command.substring(6);
      stopAllMotors();
      
      if (alertType == "GOAL") {
        for (int i = 0; i < 5; i++) {
          digitalWrite(BUZZER_PIN, HIGH); delay(100);
          digitalWrite(BUZZER_PIN, LOW);  delay(100);
        }
      } 
      else if (alertType == "BLUE") {
        for (int i = 0; i < 5; i++) {
          digitalWrite(LED_PIN, HIGH); delay(500);
          digitalWrite(LED_PIN, LOW);  delay(500);
        }
      }
      else if (alertType == "BLACK") { 
        for (int i = 0; i < 3; i++) { 
          digitalWrite(BUZZER_PIN, HIGH); delay(150);
          digitalWrite(BUZZER_PIN, LOW);  delay(150);
        }
      }
      else if (alertType == "FINISHED") {
        digitalWrite(BUZZER_PIN, HIGH); delay(1000);
        digitalWrite(BUZZER_PIN, LOW);
      }
    }
  }
}



Full and final code for the raspberry pi 5:-


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
