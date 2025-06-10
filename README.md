**NOTE:** *this repository and README file are still actively under development* 
---

*last updated: 6/9/2025*

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
- **Adafruit SCD41** (True/NDIR CO₂, Temperature, Humidity)
- **Adafruit ENS160 MOX Gas Sensor** (TVOC, AQI, eCO₂)
- **DFRobot SEN0571** (Qualitative Odor Sensor)
- **GT-U7 GPS & GNSS Antenna Amplifier**

- [3D printed enclosure](https://github.com/NohPei/mobile-AQ-documentation/blob/main/v2-enclosure.stl)

**NOTE:** why both ENS160 and SCD41? We could use only SCD41 to measure *true* CO₂ (which isn't affected by VOCs like the ENS160), but we wanted something to measure TVOC/VOCs
- while ENS160 is currently included, we are actively searching to replace it with an alternative sensor for VOCs only

### TVOC vs. VOC
- VOCs (Volatile Organic Compounds) = individual or specific groups of volatile organic compounds.
- TVOC (Total Volatile Organic Compounds) = represents the total concentration of all volatile organic compounds in the air.


# How are the different sensors interfaced?
- I2C: RTC, MQs (x3), IMU, ENS160, SCD41, PM
- UART: GPS

# Sensors + Data Structure 
Overview and in-depth resources for the sensors, type of data they capture, and output format of the CSV.

Each row in the CSV file contains a timestamped sensor reading from the mobile air quality sensing unit. The columns are listed below:

| Column Name         | Description                                        | Units               |
|---------------------|----------------------------------------------------|---------------------|
| `Timestamp (ms)`    | System timestamp when data was logged              | milliseconds        |
| `GPS Timestamp(UTC)`| UTC timestamp from GPS module                      | ISO 8601 or seconds |
| `Latitude`          | Latitude position from GPS                         | degrees             |
| `Longitude`         | Longitude position from GPS                        | degrees             |
| `MQ-3 Voltage`      | Raw analog voltage from MQ-3 sensor                | volts               |
| `MQ-4 Voltage`      | Raw analog voltage from MQ-4 sensor                | volts               |
| `MQ-8 Voltage`      | Raw analog voltage from MQ-8 sensor                | volts               |
| `MQ-3 R_s`          | Sensor resistance for MQ-3                         | ohms (Ω)            |
| `MQ-4 R_s`          | Sensor resistance for MQ-4                         | ohms (Ω)            |
| `MQ-8 R_s`          | Sensor resistance for MQ-8                         | ohms (Ω)            |
| `SCD41 CO₂`         | CO₂ concentration                                  | ppm                 |
| `SCD41 Temperature` | Ambient temperature                                | °C                  |
| `SCD41 Humidity`    | Relative humidity                                  | %                   |
| `PM1.0`             | Particulate matter 1.0 µm concentration            | µg/m³               |
| `PM2.5`             | Particulate matter 2.5 µm concentration            | µg/m³               |
| `PM10`              | Particulate matter 10 µm concentration             | µg/m³               |
| `Accel X`           | X-axis acceleration                                | m/s²                |
| `Accel Y`           | Y-axis acceleration                                | m/s²                |
| `Accel Z`           | Z-axis acceleration                                | m/s²                |
| `Gyro X`            | X-axis angular velocity                            | °/s                 |
| `Gyro Y`            | Y-axis angular velocity                            | °/s                 |
| `Gyro Z`            | Z-axis angular velocity                            | °/s                 |
| `Mag X`             | X-axis magnetic field                              | µT                  |
| `Mag Y`             | Y-axis magnetic field                              | µT                  |
| `Mag Z`             | Z-axis magnetic field                              | µT                  |


### Real-Time Clock (ds3231) -> Timestamp (ms)
- ex) 2025-05-07 00:34:16.522

### GPS (GT-U7 + GNSS antenna amplifier) -> GPS Timestamp (UTC), Latitude,Longitude
- ex) 2025-05-07 04:34:16,42.29262116666666,-83.71489916666667

### Gas Sensors (MQ Series) -> Voltage
[resource 1](https://www.theengineeringprojects.com/2024/04/mq-gas-sensor-series.html)
[resource 2](https://robocraze.com/blogs/post/mq-series-gas-sensor)
[resource 3](https://iotbyhvm.ooo/mq-gas-sensors-gas-sensors/)

MQ-3 = H2, LPG, CH4, CO, Alcohol, Smoke or Propane
- [MQ-3 datasheet](https://cdn.sparkfun.com/assets/6/a/1/7/b/MQ-3.pdf)
MQ-4 = Methane, CNG
MQ-8 = Hydrogen Sulfide 
- outputs are voltages, representing raw output from sensor 
    - reflects concentration of gas it is sensing 

- ex) 0.3605,0.165,0.34450000000000003
**note**: tells us the concentration of a gas in part per million (ppm) according to the resistance ratio of the sensor (RS/R0). MQ senors have a built-in variable resistor that changes its value according to the concentration of gas. If the concentration is High, the resistance decreases,  if the concentration is low, the resistance increases


MQ-3 R_s,MQ-4 R_s,MQ-8 R_s
ex) 128696.25520110958,293030.303030303,135137.88098693758,

(ENS160 is optional...)
ENS160 TVOC,ENS160 eCO₂,ENS160 AQI
datasheet: https://cdn-learn.adafruit.com/assets/assets/000/115/331/original/SC_001224_DS_1_ENS160_Datasheet_Rev_0_95-2258311.pdf 
TVOC values: 0 - 65,000
eCO₂ values: 400 - 65,000 
AQI values: 1-5
- ex) 0,400,1

SCD41 CO₂,SCD41 Temperature,SCD41 Humidity,
ex) 590,24.380483710994127,29.660486762798506

DFROBOT SEN0571 Odor Sensor (*qualitative* sensor...)
[resource](https://docs.cirkitdesigner.com/component/8f45805b-c744-4d19-9426-4d6299082ad4/fermion-mems-odor-smell-gas-detection-sensor) <- although the wiring instructions are incorrect, that resource has good notes

PM1.0,PM2.5,PM10
ex) 1,1,3
