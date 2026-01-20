from enum import StrEnum


class Icon(StrEnum):
    BABY = "mdi:baby"
    BABY_BUGGY = "mdi:baby-buggy"
    BATTERY_UNKNOWN = "mdi:battery-unknown"
    CALENDAR_TODAY = "mdi:calendar-today"
    CAR_ELECTRIC = "mdi:car-electric"
    CAR_ELECTRIC_OUTLINE = "mdi:car-electric-outline"
    CLOUD = "mdi:cloud"
    CLOUD_OUTLINE = "mdi:cloud-outline"
    DOG = "mdi:dog"
    DOOR_OPEN = "mdi:door-open"
    FAN = "mdi:fan"
    FINANCE = "mdi:finance"
    FIRE = "mdi:fire"
    HEADSET = "mdi:headset"
    HELP = "mdi:help"
    HOME = "mdi:home"
    HVAC = "mdi:hvac"
    HVAC_OFF = "mdi:hvac-off"
    LOCK = "mdi:lock"
    LOCK_OPEN_VARIANT = "mdi:lock-open-variant"
    LOCK_QUESTION = "mdi:lock-question"
    MAP_CLOCK = "mdi:map-clock"
    NAVIGATION = "mdi:navigation"
    PROGRESS_QUESTION = "mdi:progress-question"
    RADIATOR = "mdi:radiator"
    RASPBERRY_PI = "mdi:raspberry-pi"
    ROAD_VARIANT = "mdi:road-variant"
    SLEEP = "mdi:sleep"
    SNOWFLAKE = "mdi:snowflake"
    TIMER_OUTLINE = "mdi:timer-outline"
    THERMOMETER = "mdi:thermometer"
    THERMOMETER_OFF = "mdi:thermometer-off"
    THERMOMETER_WATER = "mdi:thermometer-water"
    UPDATE = "mdi:update"


def battery_icon(battery: float, charging: bool = False, full_threshold: int = 100) -> str:
    """
    Returns a battery icon name corresponding to how full the battery is and whether it's charging.
    Output string includes "mdi:" prefix. Use full_threshold if "full" is less than 100%.
    """
    if 0 < battery < 1:
        battery *= 100
    battery = min(battery * (100 / full_threshold), 100)

    icon = "mdi:battery-charging-" if charging else "mdi:battery-"
    icon += str(round(battery / 10) * 10)

    return "mdi:battery" if icon == "mdi:battery-100" else icon
