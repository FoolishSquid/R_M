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
