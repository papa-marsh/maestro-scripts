from dataclasses import asdict
from datetime import timedelta

from maestro.domains import ON, UNAVAILABLE, UNKNOWN
from maestro.registry import binary_sensor, climate, maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import local_now
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon
from scripts.home.door_left_open import EXTERIOR_DOORS

card = maestro.entity_card_3


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Home",
        icon=Icon.HOME,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.title = attributes.title
    card.row_3_icon = Icon.DOG


@state_change_trigger(*EXTERIOR_DOORS)
def set_state() -> None:
    open_doors = [door for door in EXTERIOR_DOORS if door.state == "on"]
    open_count = len(open_doors)
    if open_count == 1:
        card.state = open_doors[0].friendly_name.split(" ")[0]
        card.active = True
    elif open_count > 1:
        card.state = f"{open_count} Doors"
        card.icon = Icon.DOOR_OPEN
        card.active = True
    else:
        card.state = "All Shut"
        card.icon = Icon.HOME
        card.active = False


@state_change_trigger(climate.thermostat)
@cron_trigger("*/10 * * * *")
def set_row_1() -> None:
    if climate.thermostat in [UNKNOWN, UNAVAILABLE]:
        card.row_1_value = "Offline"
        card.row_1_icon = Icon.THERMOMETER_OFF
        return

    temp = climate.thermostat.current_temperature
    humidity = climate.thermostat.current_humidity
    card.row_1_value = f"{temp:.0f}° · {humidity:.0f}%"


@state_change_trigger(climate.thermostat)
@cron_trigger("*/10 * * * *")
def set_row_2() -> None:
    if climate.thermostat in [UNKNOWN, UNAVAILABLE]:
        card.row_2_value = "Offline"
        card.row_2_icon = Icon.HVAC
        return

    value = climate.thermostat.hvac_action
    current_temp = climate.thermostat.current_temperature
    setpoint = climate.thermostat.temperature
    if current_temp != setpoint:
        value += f" ({setpoint})"

    icon_map = {"cool": "mdi:snowflake", "heat": "mdi:fire", "off": "mdi:hvac-off"}

    card.row_2_value = value
    card.row_2_icon = icon_map[climate.thermostat.state]


@state_change_trigger(binary_sensor.chelsea_cabinet_sensor, to_state=ON)
def set_row_3() -> None:
    card.row_3_value = local_now().strftime("%-I:%M %p")
    card.row_3_color = RowColor.DEFAULT


@cron_trigger(hour=7)
@cron_trigger(hour=19)
def set_row_3_color() -> None:
    last_changed = binary_sensor.chelsea_cabinet_sensor.last_changed
    if local_now() - last_changed > timedelta(hours=1):
        card.row_3_color = RowColor.RED
