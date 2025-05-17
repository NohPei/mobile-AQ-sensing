import time
import board
import adafruit_scd4x
from utils import config
import busio

i2c = busio.I2C(board.SCL, board.SDA, frequency=config.I2C_FREQ) 
scd4x = adafruit_scd4x.SCD4X(i2c)
scd4x.reinit()

print("Starting measurements...")
scd4x.start_periodic_measurement()
initial_time = time.time()
while True:
    if scd4x.data_ready:
        scd4x_readings = [scd4x.CO2, scd4x.temperature, scd4x.relative_humidity]
        print("Elapsed time since last measurement: ", time.time() - initial_time)
        print(f"CO2: {scd4x_readings[0]}ppm, Temperature: {scd4x_readings[1]}C, Humidity: {scd4x_readings[2]}%")
        initial_time = time.time()
        time.sleep(5)
