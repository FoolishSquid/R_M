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
