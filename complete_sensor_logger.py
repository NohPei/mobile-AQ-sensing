import time
import board
import busio
import serial
import csv
import threading
import glob
from datetime import datetime
import pynmea2
import adafruit_scd4x
import adafruit_ens160
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_bno08x
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_ens160 import NORMAL_OP, START_UP, WARM_UP, INVALID_OUT, MODE_STANDARD
from adafruit_pm25.i2c import PM25_I2C

# using ACT led to verify we have started logging data
led_path="/sys/class/leds/ACT/brightness"

def set_led(state):
  with open(led_path, "w") as led:
    led.write("1" if state else "0")
set_led(0)

# Initialize I2C - added frequency for PM sensor...
reset_pin = None
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Initialize ADS1115 (MQ Gas Sensors)
ads = ADS.ADS1115(i2c)
mq_sensors = {
    "MQ-3 (Alcohol)": AnalogIn(ads, ADS.P0),
    "MQ-4 (Methane)": AnalogIn(ads, ADS.P1),
    "MQ-8 (Hydrogen)": AnalogIn(ads, ADS.P3)
}

# Initialize IMU (GY-BNO08X)
imu = BNO08X_I2C(i2c, address=0x4B)
imu.enable_feature(adafruit_bno08x.BNO_REPORT_ACCELEROMETER)
imu.enable_feature(adafruit_bno08x.BNO_REPORT_GYROSCOPE)
imu.enable_feature(adafruit_bno08x.BNO_REPORT_MAGNETOMETER)

# Initialize Serial Interfaces
gps_uart = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=0.1)

# Initialize Sensors
ens160 = adafruit_ens160.ENS160(i2c)
ens160.mode = MODE_STANDARD
scd41 = adafruit_scd4x.SCD4X(i2c)
scd41.start_periodic_measurement()
pm25 = PM25_I2C(i2c, reset_pin)

print("ENS160 firmware:", ens160.firmware_version)
print("ENS160 mode:", ens160.mode)

# Store latest GPS coordinates and time
gps_lock = threading.Lock()
latest_lat, latest_lon, latest_gps_time = None, None, None
last_gps_fix_timestamp = None

# **Threaded GPS Reading**
def read_gps_continuous():
    global latest_lat, latest_lon, latest_gps_time, last_gps_fix_timestamp
    while True:
        try:
            line = gps_uart.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("$GPRMC"):
                msg = pynmea2.parse(line)
                if msg.status == 'A':
                    gps_datetime = datetime.combine(msg.datestamp, msg.timestamp)
                    with gps_lock:
                        latest_gps_time = gps_datetime
                        last_gps_fix_timestamp = time.time()
            elif line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                if hasattr(msg, 'gps_qual') and msg.gps_qual > 0:
                    with gps_lock:
                        latest_lat, latest_lon = msg.latitude, msg.longitude
                        last_gps_fix_timestamp = time.time()
        except Exception as e:
            print(f"GPS Error: {e}")
        time.sleep(0.05)

# Start GPS Thread
gps_thread = threading.Thread(target=read_gps_continuous, daemon=True)
gps_thread.start()

# **Warm-Up Period (1 Minute)**
warmup_time = 1 * 60
print(f"Starting warm-up period ({warmup_time // 60} minutes)...")
start_time = time.time()
while time.time() - start_time < warmup_time:
    remaining_time = warmup_time - (time.time() - start_time)
    print(f"Warm-up time remaining: {int(remaining_time // 60)}m {int(remaining_time % 60)}s", end="\r")
    set_led(1)
    time.sleep(1)
    set_led(0)
    time.sleep(1)
print("\nWarm-up complete. Starting data collection...")

set_led(1)

# **Create and Open CSV File for Logging**
first_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = f"sensor_log_{first_timestamp}.csv"

with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
       "Timestamp (ms)", "GPS Timestamp (UTC)", "Latitude", "Longitude",
    	"MQ-3 Voltage", "MQ-4 Voltage", "MQ-8 Voltage",
        "MQ-3 R_s", "MQ-4 R_s", "MQ-8 R_s",
        "ENS160 TVOC", "ENS160 eCO₂", "ENS160 AQI",
        "SCD41 CO₂", "SCD41 Temperature", "SCD41 Humidity",
        "PM1.0", "PM2.5", "PM10",
        "Accel X", "Accel Y", "Accel Z",
        "Gyro X", "Gyro Y", "Gyro Z",
        "Mag X", "Mag Y", "Mag Z"
    ])

    def calculate_resistance(v_out, v_circuit=5.0, r_load=10000):
        if v_out == 0:
            return None
        return ((v_circuit - v_out) / v_out) * r_load

    try:
        print(f"Logging sensor data to {csv_filename}... Press CTRL+C to stop.")

        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with gps_lock:
                lat, lon = latest_lat, latest_lon
                gps_time = latest_gps_time.strftime("%Y-%m-%d %H:%M:%S") if latest_gps_time else None
                gps_age = time.time() - last_gps_fix_timestamp if last_gps_fix_timestamp else None

            if gps_age and gps_age > 2:
                print(f"GPS fix is stale ({gps_age:.1f} seconds old)")

            mq_values = [channel.voltage for channel in mq_sensors.values()]
            mq_resistances = [calculate_resistance(v) for v in mq_values]

            scd41_co2, scd41_temp, scd41_hum = None, None, None
            try:
                scd41_co2 = scd41.CO2
                scd41_temp = scd41.temperature
                scd41_hum = scd41.relative_humidity
            except OSError:
                print("SCD41 error detected. Restarting sensor...")
                scd41.stop_periodic_measurement()
                time.sleep(2)
                scd41.start_periodic_measurement()

            try:
                if scd41_temp is not None and scd41_hum is not None:
                    ens160.temperature_compensation = scd41_temp
                    ens160.humidity_compensation = scd41_hum
            except Exception as e:
                print(f"ENS160 compensation error: {e}")

            if ens160.new_data_available:
                validity = ens160.data_validity
                if validity == NORMAL_OP:
                    try:
                        data = ens160.read_all_sensors()
                        ens160_tvoc = data["TVOC"]
                        ens160_eco2 = data["eCO2"]
                        ens160_aqi = data["AQI"]
                    except Exception as e:
                        print(f"ENS160 read error: {e}")
                        ens160_tvoc, ens160_eco2, ens160_aqi = None, None, None
                else:
                    print(f"ENS160 not ready → status: {validity}")
                    ens160_tvoc, ens160_eco2, ens160_aqi = None, None, None
            else:
                ens160_tvoc, ens160_eco2, ens160_aqi = None, None, None

            try:
                aqdata = pm25.read()
                pm1_0 = aqdata["pm10 env"]
                pm2_5 = aqdata["pm25 env"]
                pm10 = aqdata["pm100 env"]


            except RuntimeError:
                print("Unable to read from sensor, retrying...")
                continue

            accel_x, accel_y, accel_z = None, None, None
            gyro_x, gyro_y, gyro_z = None, None, None
            mag_x, mag_y, mag_z = None, None, None
            try:
                accel_x, accel_y, accel_z = imu.acceleration
                gyro_x, gyro_y, gyro_z = imu.gyro
                mag_x, mag_y, mag_z = imu.magnetic
            except Exception as e:
                if "UNKNOWN Report Type" in str(e) or "0x7b" in str(e) or "Unprocessable Batch bytes" in str(e):
                    pass
                else:
                    print(f"IMU read error: {e}")

            sensor_values = [
                timestamp, gps_time, lat, lon,
                *mq_values, *mq_resistances,
                ens160_tvoc, ens160_eco2, ens160_aqi,
                scd41_co2, scd41_temp, scd41_hum,
                pm1_0, pm2_5, pm10,
                accel_x, accel_y, accel_z,
                gyro_x, gyro_y, gyro_z,
                mag_x, mag_y, mag_z
            ]

            writer.writerow(sensor_values)
            file.flush()
            print(sensor_values)
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\nStopping sensor logging. Data saved to {csv_filename}.")
