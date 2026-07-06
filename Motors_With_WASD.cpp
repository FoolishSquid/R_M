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
