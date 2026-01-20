import socket
from contextlib import suppress
from dataclasses import asdict

from maestro.domains import ON
from maestro.registry import binary_sensor, maestro, sensor, update
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon

card = maestro.entity_card_6


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Hass",
        icon=Icon.RASPBERRY_PI,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.update(title=attributes.title)


@cron_trigger("* * * * *")
def set_state() -> None:
    update_available = (
        update.home_assistant_core_update.state == ON
        or update.home_assistant_supervisor_update.state == ON
    )
    if not check_internet_connection():
        state = "Disconnected"
        icon = Icon.WEB_OFF
        blink = True
    else:
        state = update.home_assistant_core_update.installed_version[2:]
        icon = Icon.UPDATE if update_available else Icon.HOME_ASSISTANT
        blink = False

    card.update(state=state, icon=icon, active=update_available, blink=blink)


@state_change_trigger(binary_sensor.z_wave_js_running)
def set_row_2() -> None:
    value = "Running" if binary_sensor.z_wave_js_running.is_on else "Not Running"
    color = RowColor.RED if binary_sensor.z_wave_js_running.is_on else RowColor.DEFAULT
    card.update(row_2_value=value, row_2_color=color)


@state_change_trigger(sensor.cpu_temperature)
def set_row_3() -> None:
    cpu_temp = float(sensor.cpu_temperature.state)
    value = f"{cpu_temp} °F"
    color = RowColor.RED if cpu_temp >= 110 else RowColor.DEFAULT
    card.update(row_3_value=value, row_3_color=color)


def check_internet_connection() -> bool:
    """Check internet connection by attempting TCP connections"""
    for host in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        with suppress(OSError), socket.create_connection(host, timeout=3):
            return True
    return False
