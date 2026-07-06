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
