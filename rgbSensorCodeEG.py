import time
import board
import adafruit_tcs34725

# Initialize I2C and TCS34725 sensor
i2c = board.I2C()
sensor = adafruit_tcs34725.TCS34725(i2c)

# Set gain and integration time for the sensor
sensor.gain = adafruit_tcs34725.GAIN_4X
sensor.integration_time = 100  # In milliseconds

try:
    while True:
        # Read color values
        r, g, b, c = sensor.color_raw
        temperature = sensor.color_temperature  # Optional: Estimate color temperature
        lux = sensor.lux  # Optional: Calculate brightness in lux

        print(f"Raw RGB: R={r}, G={g}, B={b}, Clear={c}")
        if temperature is not None:
            print(f"Color Temperature: {temperature:.2f} K")
        print(f"Lux: {lux:.2f} lx")
        print("--------------------------")
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")