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

5. Create backup systemd serivce (load module, manually register if missing, set system clock)
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
   
-> will work on every boot with/without connectivity and set the system time to correctly use the hardware clock. 
