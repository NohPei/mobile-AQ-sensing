### DS3231 RTC Setup on Raspberry Pi OS (Bookworm)

To get the DS3231 RTC working reliably on Raspberry Pi OS (Bookworm), follow these steps:

1. enable i2c using `sudo raspi-config`, and verify the RTC is detected at address `0x68` using `i2cdetect -y 1`.
2. In `/boot/firmware/config.txt`, add the following line all the way at the bottomt to enable the overlay:

```ini
dtoverlay=i2c-rtc,ds3231
```
3. Add the RTC driver to /etc/modules: (underscore!)
```ini
rtc_ds1307
```
4. Add the driver to /etc/initramfs-tools/modules: (hyphen!)
```ini
rtc-ds1307
```
- then update initramfs tools:
```bash
sudo update-initramfs -u
```

5. Create fallback script at /usr/local/bin/fallback_rtc_init.sh:
```bash
#!/bin/bash

LOG_TAG="FALLBACK_RTC"
I2C_BUS=1
RTC_ADDRESS=0x68

logger -t "$LOG_TAG" "Starting RTC fallback init..."

modprobe rtc_ds1307
logger -t "$LOG_TAG" "Loaded rtc_ds1307 driver."

if [ ! -e /dev/rtc0 ]; then
    logger -t "$LOG_TAG" "/dev/rtc0 not found. Attempting manual registration..."
    echo "ds3231 $RTC_ADDRESS" > /sys/class/i2c-adapter/i2c-${I2C_BUS}/new_device 2>/dev/null
    sleep 1
fi

if [ -e /dev/rtc0 ]; then
    logger -t "$LOG_TAG" "RTC registered successfully at /dev/rtc0."
    sleep 1
    if hwclock -s; then
        logger -t "$LOG_TAG" "System time set from RTC: $(hwclock -r)"
    else
        logger -t "$LOG_TAG" "ERROR: hwclock failed to read from RTC after registration."
    fi
else
    logger -t "$LOG_TAG" "ERROR: /dev/rtc0 still not available. RTC registration failed or device not present."
fi
```
- make it executable: sudo chmod +x /usr/local/bin/fallback_rtc_init.sh


6. Make the systemd serivce (load module, manually register if missing, set system clock)
```ini
[Unit]
Description=Manual Fallback RTC Init
After=multi-user.target
ConditionPathExists=/dev/i2c-1

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fallback_rtc_init.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```
- reload & enable that:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fallback-rtc.service
```

7. (optional/overkill but good for system longevity and consistency) sync RTC if NTP sync happens (pi connects to network) at /usr/local/bin/rtc_writeback.sh:
```bash
#!/bin/bash

LOG_TAG="RTC_WRITEBACK"

logger -t "$LOG_TAG" "Waiting for NTP synchronization..."

MAX_TRIES=60
for i in $(seq 1 $MAX_TRIES); do
    SYNCED=$(timedatectl show -p NTPSynchronized --value)
    if [ "$SYNCED" = "yes" ]; then
        logger -t "$LOG_TAG" "System clock synchronized, writing to RTC..."
        hwclock -w && logger -t "$LOG_TAG" "RTC updated from system time."
        exit 0
    fi
    sleep 2
done

logger -t "$LOG_TAG" "ERROR: NTP sync not achieved within timeout."
exit 1
```
- make it executable: sudo chmod +x /usr/local/bin/rtc_writeback.sh

8. Create the systemd service for it:
```ini
[Unit]
Description=Write system time to RTC after NTP sync
After=network-online.target systemd-timesyncd.service
Requires=systemd-timesyncd.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/rtc_writeback.sh
TimeoutStartSec=90

[Install]
WantedBy=multi-user.target
```
- reload & enable that:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fallback-rtc.service
```

### Summary:   
1. this will make RTC work on every boot with/without connectivity and set the system time to correctly use the hardware clock. 
2. bonus: will resync with NTP when Wi-Fi connectivity happens so RTC is updated from system time.

