import socket
from contextlib import suppress
from dataclasses import asdict
from datetime import timedelta

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
from maestro.utils import JobScheduler
from maestro.utils.dates import local_now
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon

card = maestro.entity_card_6

ZWAVE_CHECK_JOB_ID = "post_startup_zwave_check"


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
    card.update(
        title=attributes.title,
        row_1_icon=Icon.Z_WAVE,
        row_2_icon=Icon.THERMOMETER,
        row_3_icon=Icon.MEMORY,
    )


@cron_trigger("* * * * *")
def set_state() -> None:
    update_available = (
        update.home_assistant_core_update.state == ON
        or update.home_assistant_supervisor_update.state == ON
    )
    if not check_internet_connection():
        state = "Offline"
        icon = Icon.WEB_OFF
        blink = True
    else:
        state = update.home_assistant_core_update.installed_version[2:]
        icon = Icon.UPDATE if update_available else Icon.HOME_ASSISTANT
        blink = False

    card.update(state=state, icon=icon, active=update_available, blink=blink)


@hass_trigger(HassEvent.STARTUP)
def post_startup_zwave_check() -> None:
    in_five_minutes = local_now() + timedelta(minutes=5)
    JobScheduler().schedule_job(run_time=in_five_minutes, func=set_row_1, job_id=ZWAVE_CHECK_JOB_ID)


@state_change_trigger(binary_sensor.z_wave_js_running)
def set_row_1() -> None:
    value = "Running" if binary_sensor.z_wave_js_running.is_on else "Not Running"
    color = RowColor.DEFAULT if binary_sensor.z_wave_js_running.is_on else RowColor.RED
    card.update(row_1_value=value, row_1_color=color)


@state_change_trigger(sensor.cpu_temperature)
def set_row_2() -> None:
    cpu_temp = float(sensor.cpu_temperature.state)
    value = f"{cpu_temp:.0f} °F"
    color = RowColor.RED if cpu_temp >= 110 else RowColor.DEFAULT
    card.update(row_2_value=value, row_2_color=color)


@state_change_trigger(sensor.memory_use_percent)
def set_row_3() -> None:
    memory_use = float(sensor.memory_use_percent.state)
    value = f"{memory_use:.1f}%"
    color = RowColor.RED if memory_use >= 85 else RowColor.DEFAULT
    card.update(row_3_value=value, row_3_color=color)


def check_internet_connection() -> bool:
    """Check internet connection by attempting TCP connections"""
    for host in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        with suppress(OSError), socket.create_connection(host, timeout=3):
            return True
    return False
