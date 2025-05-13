import board # board pinout abstract
import busio # board bus abstract
import adafruit_ads1x15.ads1115 as ADS # Four channel ADC
from adafruit_ads1x15.analog_in import AnalogIn # Analog read function

import os
import time
from datetime import datetime,timezone
import pytz
import csv

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading
import queue

import utils
from utils import config


def main():
    # Set up the LED permission if running in venv
    utils.set_led(0)

    try:
        # Check if board has SDA and SCL attributes
        if hasattr(board, "SDA") and hasattr(board, "SCL"):
            print("Board has SDA and SCL ports.")
        else:
            print("Board is missing SDA and/or SCL ports.")
    except Exception as e:
        print(f"Error checking board ports: {e}")

    # bus and adc initialization
    i2c = busio.I2C(board.SCL,board.SDA,frequency=config.I2C_FREQ) 
    ads = ADS.ADS1115(i2c,address=config.I2C_ADDRESS)
    mq_sensors = {
        "MQ-3 (Alcohol)": AnalogIn(ads, ADS.P0),
        "MQ-4 (Methane)": AnalogIn(ads, ADS.P1),
        "MQ-8 (Hydrogen)": AnalogIn(ads, ADS.P3)
    }

    utils.set_led(1)


    csv_filename = f"sensor_log.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(config.SENSOR_HEADERS)
        print("Logging data to {}. Ctrl+C to stop.".format(csv_filename))
        
        while True:
            try:
                timestamp = datetime.now()
                mq_readings = [mq_sensor.voltage for mq_sensor in mq_sensors.values()]
                
                # Write to CSV (formatted string for CSV)
                writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], *mq_readings])
                file.flush()
                
                time.sleep(0.1)  # Adjust sampling rate as needed
                
            except KeyboardInterrupt:
                print(f"\nStopping sensor logging. Data saved to {csv_filename}.")
                break
        file.close()

if __name__ == "__main__":
    main()