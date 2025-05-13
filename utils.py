import time
from datetime import datetime,timezone
import pytz

class config:
    I2C_ADDRESS = 0x48
    I2C_FREQ = 100000
    SENSOR_HEADERS = [
        "Timestamp (ms)", "MQ-3 Voltage", "MQ-4 Voltage", "MQ-8 Voltage"
    ]
  
led_path="/sys/class/leds/ACT/brightness"

def set_led(state):
  with open(led_path, "w") as led:
    led.write("0" if state else "1")
  
def warm_up(duration_seconds: int) -> None:
  """
    Performs a warm-up period, blinking the LED every 1 second.

    Args:
        duration_seconds (int): Warm-up duration in seconds.
    
    Returns:
        None
  """
  print(f"Starting warm-up period ({duration_seconds // 60} minutes {duration_seconds % 60} seconds)...")
  start_time = time.time()
  while time.time() - start_time < duration_seconds:
      remaining_time = duration_seconds - (time.time() - start_time)
      print(f"Warm-up time remaining: {int(remaining_time // 60)}m {int(remaining_time % 60)}s", end="\r")
      set_led(1)
      time.sleep(1)
      set_led(0)
      time.sleep(1)
  print("\nWarm-up complete. Starting data collection...")

def get_utc_ms(dt_str: str) -> int:
    """
    Convert a datetime string to UTC milliseconds.

    Args:
        dt_str (str): The datetime string in the format "%Y-%m-%d %H:%M:%S.%f".

    Returns:
        int: The UTC milliseconds.
    """
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
    local_tz = pytz.timezone("America/Detroit")  # Replace with your local timezone
    dt_local = local_tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    utc_ms = int(dt_utc.timestamp() * 1000)
    return utc_ms