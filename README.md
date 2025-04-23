**NOTE:** *this repository and README file are still actively under development*
---

# Mobile AQ Sensing Unit Overview

- **Raspberry Pi 4B** (Raspberry Pi OS Bookworm)
- **DS3231 RTC** (real-time clock module)
- **MQ Gas Sensors**:
  - MQ-3 (Alcohol)
  - MQ-4 (Methane)
  - MQ-8 (Hydrogen)
  - All read via **ADS1115 16-bit ADC**
- **Adafruit Breakout board Plantower PMSA003I** (Particulate Matter Sensor, PM1.0 / PM2.5 / PM10)
- **GY-BNO08X** (9 DoF IMU — accelerometer, gyro, magnetometer)
- **Adafruit ENS160** (MOX gas sensor — eCO₂, TVOC, AQI)
- **Adafruit SCD41** (True/NDIR CO₂, Temperature, Humidity)
- **GT-U7 GPS & GNSS Antenna Amplifier**


**NOTE:** why both ENS160 and SCD41? We could use only SCD41 to measure *true* CO₂ (which isn't affected by VOCs like the ENS160), but we want something to measure TVOC/VOCs
- while ENS160 is currently included, we are actively searching to replace it with an alternative sensor for VOCs only

### TVOC vs. VOC
**VOCs (Volatile Organic Compounds)** = individual or specific groups of volatile organic compounds.
**TVOC (Total Volatile Organic Compounds)** = represents the total concentration of all volatile organic compounds in the air. 
---
# How are the different sensors interfaced?
- I2C: RTC, MQs (x3), IMU, ENS160, SCD41, PM
- UART: GPS
---
# Sensors + Data Structure 
Overview and in-depth resources for the sensors, type of data they capture, and output format of the CSV.

### Real-Time Clock (ds3231) -> Timestamp (ms)
- ex) 2025-03-20 13:45:45.611

### GPS (GT-U7 + GNSS antenna amplifier) -> Latitude,Longitude
- ex) 42.248456166666664,-83.76558416666667

### Gas Sensors (MQ Series) -> Voltage
resource: https://www.theengineeringprojects.com/2024/04/mq-gas-sensor-series.html  
resource: https://robocraze.com/blogs/post/mq-series-gas-sensor
resource: https://iotbyhvm.ooo/mq-gas-sensors-gas-sensors/
MQ-3 = H2, LPG, CH4, CO, Alcohol, Smoke or Propane
MQ-3 datasheet: https://cdn.sparkfun.com/assets/6/a/1/7/b/MQ-3.pdf
MQ-4 = Methane, CNG
MQ-8 = Hydrogen Sulfide 
- outputs are voltages, representing raw output from sensor 
    - reflects concentration of gas it is sensing 

- ex) 0.3605,0.165,0.34450000000000003
**note**: tells us the concentration of a gas in part per million (ppm) according to the resistance ratio of the sensor (RS/R0). MQ senors have a built-in variable resistor that changes its value according to the concentration of gas. If the concentration is High, the resistance decreases,  if the concentration is low, the resistance increases


MQ-3 R_s,MQ-4 R_s,MQ-8 R_s
128696.25520110958,293030.303030303,135137.88098693758,


ENS160 TVOC,ENS160 eCO₂,ENS160 AQI
datasheet: https://cdn-learn.adafruit.com/assets/assets/000/115/331/original/SC_001224_DS_1_ENS160_Datasheet_Rev_0_95-2258311.pdf 
TVOC values: 0 - 65,000
eCO₂ values: 400 - 65,000 
AQI values: 1-5
- ex) 0,400,1

SCD41 CO₂,SCD41 Temperature,SCD41 Humidity,
590,24.380483710994127,29.660486762798506

PM1.0,PM2.5,PM10
0,0,0
