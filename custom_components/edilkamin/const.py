"""Constants for the Edilkamin integration."""

DOMAIN = "edilkamin"

# Configuration
MAC_ADDRESS = "mac_address"
USERNAME = "username"
PASSWORD = "password"  # noqa: S105

# API Constants
UPDATE_INTERVAL_SECONDS = 60  # Increased from 15s for better efficiency
API_TIMEOUT_SECONDS = 10

# Adaptive Interval Constants
ADAPTIVE_INTERVAL_MIN_SECONDS = 30  # Minimum (after change detected)
ADAPTIVE_INTERVAL_MAX_SECONDS = 120  # Maximum (stable, no changes)
ADAPTIVE_INTERVAL_NORMAL_SECONDS = 60  # Normal interval
TIME_TO_LONG_INTERVAL_SECONDS = 300  # 5 minutes without changes
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY_SECONDS = 1

# Temperature limits (in Celsius)
TEMP_MIN = 10.0
TEMP_MAX = 30.0

# Fan speed limits (in %)
FAN_SPEED_MIN = 0
FAN_SPEED_MAX = 100

# Power levels (for manual mode)
POWER_LEVEL_MIN = 1
POWER_LEVEL_MAX = 5

# Valid MQTT Commands
MQTT_COMMANDS = {
    "power",
    "enviroment_1_temperature",
    "enviroment_2_temperature",
    "chrono_mode",
    "airkare_function",
    "relax_mode",
    "fan_1_speed",
    "fan_2_speed",
    "fan_3_speed",
    "standby_mode",
    "auto_mode",
    "power_level",
}

# Device states
STATE_STANDBY = "standby"
STATE_IGNITION = "ignition"
STATE_HEATING = "heating"
STATE_COOLING = "cooling"
STATE_OFF = "off"

