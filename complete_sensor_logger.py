import time
import board
import busio
import serial
import csv
import threading
from datetime import datetime
import pynmea2
import adafruit_scd4x
import adafruit_ens160
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_pm25.uart import PM25_UART

i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)
mq_sensors = {
    "MQ-3 (Alcohol)": AnalogIn(ads, ADS.P0),
    "MQ-4 (Methane)": AnalogIn(ads, ADS.P1),
    "MQ-8 (Hydrogen)": AnalogIn(ads, ADS.P3)
}

pm_uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=3)
pm_sensor = PM25_UART(pm_uart)
gps_uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

ens160 = adafruit_ens160.ENS160(i2c)
scd41 = adafruit_scd4x.SCD4X(i2c)
scd41.start_periodic_measurement()

gps_lock = threading.Lock()
latest_lat, latest_lon = None, None

def read_gps_continuous():
    global latest_lat, latest_lon
    while True:
        try:
            line = gps_uart.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                if hasattr(msg, 'gps_qual') and msg.gps_qual > 0:
                    with gps_lock:
                        latest_lat, latest_lon = msg.latitude, msg.longitude
        except Exception as e:
            print(f"GPS Error: {e}")
        time.sleep(0.5) 

gps_thread = threading.Thread(target=read_gps_continuous, daemon=True)
gps_thread.start()

warmup_time = 5 * 60  
print(f"Starting warm-up period ({warmup_time // 60} minutes)...")

start_time = time.time()

while time.time() - start_time < warmup_time:
    remaining_time = warmup_time - (time.time() - start_time)
    print(f"Warm-up time remaining: {int(remaining_time // 60)}m {int(remaining_time % 60)}s", end="\r")
    time.sleep(5)

print("\nWarm-up complete. Starting data collection...")


first_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = f"sensor_log_{first_timestamp}.csv"

with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Timestamp (ms)", "Latitude", "Longitude",
        "MQ-3 Voltage", "MQ-4 Voltage", "MQ-8 Voltage",
        "MQ-3 R_s", "MQ-4 R_s", "MQ-8 R_s",
        "ENS160 TVOC", "ENS160 eCO₂", "ENS160 AQI",
        "SCD41 CO₂", "SCD41 Temperature", "SCD41 Humidity",
        "PM1.0", "PM2.5", "PM10"
    ])

    def calculate_resistance(v_out, v_circuit=5.0, r_load=10000):
        if v_out == 0:
            return None
        return ((v_circuit - v_out) / v_out) * r_load

    def read_pm_sensor():
        try:
            data = pm_sensor.read()
            return data["pm10 standard"], data["pm25 standard"], data["pm100 standard"]
        except RuntimeError:
            print("Failed to read PM sensor, retrying...")
        return None, None, None

    try:
        print(f"Logging sensor data to {csv_filename}... Press CTRL+C to stop.")

        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            with gps_lock:
                lat, lon = latest_lat, latest_lon

            pm1_0, pm2_5, pm10 = read_pm_sensor()

            mq_values = [channel.voltage for channel in mq_sensors.values()]
            mq_resistances = [calculate_resistance(v) for v in mq_values]

            ens160_tvoc = ens160.TVOC if hasattr(ens160, "TVOC") else None
            ens160_eco2 = ens160.eCO2 if hasattr(ens160, "eCO2") else None
            ens160_aqi = ens160.AQI if hasattr(ens160, "AQI") else None

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

            sensor_values = [
                timestamp, lat, lon,
                *mq_values, *mq_resistances,
                ens160_tvoc, ens160_eco2, ens160_aqi,
                scd41_co2, scd41_temp, scd41_hum,
                pm1_0, pm2_5, pm10
            ]

            writer.writerow(sensor_values)
            file.flush()
            print(sensor_values)
            time.sleep(3)

    except KeyboardInterrupt:
        print(f"\nStopping sensor logging. Data saved to {csv_filename}.")
