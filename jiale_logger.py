import board # board pinout abstract
import busio # board bus abstract
import adafruit_ads1x15.ads1115 as ADS # Four channel ADC
from adafruit_ads1x15.analog_in import AnalogIn # Analog read function
import adafruit_scd4x # CO2 sensor

import os
import time
from datetime import datetime,timezone
import pytz
import csv
import argparse

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading
import queue

import utils
from utils import config
print("utils imported")
class DataCollector(threading.Thread):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.running = True
        self.daemon = True  # Thread will exit when main program exits

    def run(self):
        # Initialize sensors
        i2c = busio.I2C(board.SCL, board.SDA, frequency=config.I2C_FREQ) 
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDRESS)
        scd41 = adafruit_scd4x.SCD4X(i2c)
        mq_sensors = {
            "MQ-3 (Alcohol)": AnalogIn(ads, ADS.P0),
            "MQ-4 (Methane)": AnalogIn(ads, ADS.P1),
            "MQ-8 (Hydrogen)": AnalogIn(ads, ADS.P3)
        }
        scd41.start_periodic_measurement()
        # Add the warm-up function call here
        print("Starting sensor warm-up...")
        utils.warm_up(5)  # Pass the number of seconds to warm up
        print("Warm-up complete, beginning data collection")
        csv_filename = f"sensor_log.csv"
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(config.SENSOR_HEADERS)
            print("Logging data to {}. Ctrl+C to stop.".format(csv_filename))
            
            while self.running:
                timestamp = datetime.now()
                mq_readings = [mq_sensor.voltage for mq_sensor in mq_sensors.values()]
                
                # Write to CSV
                writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], *mq_readings])
                file.flush()
                
                # Send data to plotting thread
                if self.data_queue is not None:
                    self.data_queue.put((timestamp, *mq_readings))
                
                #time.sleep(0.1)  # Adjust sampling rate as needed

    def stop(self):
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Gas sensor data logger with optional plotting')
    parser.add_argument('--plot', action='store_true', help='Enable plotting')
    args = parser.parse_args()
    plot_enabled = args.plot
    # Set up the LED
    utils.set_led(0)

    if plot_enabled:
        # Create figure and axes
        fig, ax = plt.subplots(3, 1, figsize=(10, 8))
        max_points = 100
        
        # Create deques for data
        times = deque(maxlen=max_points)
        mq3_data = deque(maxlen=max_points)
        mq4_data = deque(maxlen=max_points)
        mq8_data = deque(maxlen=max_points)

        # Initialize plots
        lines = []
        labels = ['MQ-3 (Alcohol)', 'MQ-4 (Methane)', 'MQ-8 (Hydrogen)']
        for i, axis in enumerate(ax):
            line, = axis.plot([], [], 'r-', label=labels[i])
            lines.append(line)
            axis.set_ylabel('Voltage (V)')
            axis.set_xlabel('Time (s)')
            axis.grid(True)
            axis.legend()


        start_time = None
        data_queue = queue.Queue()
    else:
        data_queue = None
        print("Plotting disabled")
    
    # Create and start data collector thread
    collector = DataCollector(data_queue)
    collector.start()

    if plot_enabled:
        def update_plot(frame):
            nonlocal start_time
            
            # Get all available data from queue
            while not data_queue.empty():
                timestamp, mq3, mq4, mq8 = data_queue.get()

                if start_time is None:
                    start_time = timestamp

                elapsed = (timestamp - start_time).total_seconds()

                times.append(elapsed)
                mq3_data.append(mq3)
                mq4_data.append(mq4)
                mq8_data.append(mq8)

            # Update each line
            data_sets = [mq3_data, mq4_data, mq8_data]
            for line, data in zip(lines, data_sets):
                line.set_data(list(times), list(data))
                axis = line.axes
                axis.relim()
                axis.autoscale_view()

            return lines

        # Start animation in main thread
        ani = FuncAnimation(fig, update_plot, interval=10, blit=True, save_count=max_points)

        try:
            plt.show()
        except KeyboardInterrupt:
            pass
    else:
        try:
            print("Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    collector.stop()
    collector.join()
    if plot_enabled:
        plt.close()
    print("Logger stopped")

if __name__ == "__main__":
    main()