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
                print(f" {name} (I2C Bus {bus_num}) Initialized successfully!")
                return True
    except Exception as e:
        print(f" ERROR: {name} (I2C Bus {bus_num}) failed: {e}")
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
