# Mobile Gas Sensing Module Setup Tutorial

## Table of Contents

1. [Introduction](#introduction)
2. [Hardware Requirements](#hardware-requirements)
3. [Assembly Instructions](#assembly-instructions)
4. [Software Setup](#software-setup)
   - [Operating System Installation](#operating-system-installation)
   - [Required Libraries](#required-libraries)
   - [Sensor Configuration](#sensor-configuration)
5. [RTC Configuration](#rtc-configuration)
   - [DS3231 Setup](#ds3231-setup)
   - [Time Synchronization](#time-synchronization)
6. [Data Collection](#data-collection)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)
9. [References](#references)

## Introduction

This guide provides step-by-step instructions for building and configuring a mobile gas sensing module from scratch. Follow each section in order for a complete setup.

## Software Requirement

#### Operating System Installation

Download it through https://www.raspberrypi.com/software/

In this repo, Raspberry Pi 5, 64 bit enhanced version is installed

#### Required Libraries (in python venv)
To make sure you can access the sysled as indication. You can run following command to create new rule and change the permission of sysled:

```
sudo nano /etc/udev/rules.d/99-led-permissions.rules
```

Type following command in the new rules:
```
SUBSYSTEM=="leds", KERNEL=="ACT", MODE="0666"
```

Reload rules:
```
sudo udevadm control --reload-rules
sudo udevadm trigger
```

If none of the above things work, manually modify the permission with 
```
sudo chmod 666 /sys/class/leds/ACT/brightness
```

1. ADS1115 => pip install adafruit-circuitpython-ads1x15
2. lgpio (not defaulty installed for pi5, higher performance) => pip install lgpio
3. 
