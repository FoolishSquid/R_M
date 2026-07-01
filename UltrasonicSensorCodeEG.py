import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)  # Trigger pin
GPIO.setup(15, GPIO.IN)   # Echo pin

def measure_distance():
    #Trigger the ultrasonic sensor
    GPIO.output(14, GPIO.HIGH)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(14, GPIO.LOW)

    # Measure the time it takes for the echo to return
    while GPIO.input(15) == 0:
        start_time = time.time()
    while GPIO.input(15) == 1:
        end_time = time.time()

    # Calculate the distance
    distance = (end_time - start_time) * 34300 / 2  # Speed of sound in cm/s
    return distance

try:
    while True:
        dist = measure_distance()
        print(f"Distance: {dist:.2f} cm")
        time.sleep(1)  # Wait for 1 second before the next measurement
except KeyboardInterrupt:
    print("Measurement stopped by user")
    GPIO.cleanup()  # Clean up GPIO settings