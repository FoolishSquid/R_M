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
