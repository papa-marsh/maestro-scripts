from dataclasses import asdict
from datetime import timedelta

from maestro.domains import HOME, UNAVAILABLE, UNKNOWN
from maestro.registry import maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import JobScheduler, local_now, resolve_timestamp
from scripts.custom_domains.zone import ZoneExtended
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon, battery_icon
from scripts.vehicles.common import Nyx

card = maestro.entity_card_2

ARRIVAL_TIME_RECHECK_JOB_ID = "nyx_arrival_time_recheck"


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Nyx",
        icon=Icon.CAR_ELECTRIC_OUTLINE,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.title = attributes.title


@state_change_trigger(Nyx.climate, Nyx.parked, Nyx.software_update)
def set_state() -> None:
    if not Nyx.parked.is_on:
        card.state = "Driving"
        card.icon = Icon.ROAD_VARIANT
        card.active = True
        return

    if Nyx.climate.state == Nyx.climate.HVACMode.HEAT_COOL:
        card.state = "Air On"
        card.icon = Icon.FAN
        card.active = True
        return

    card.state = "Air Off"
    card.icon = Icon.UPDATE if Nyx.software_update.is_on else Icon.CAR_ELECTRIC_OUTLINE
    card.active = False


@state_change_trigger(Nyx.battery)
def set_row_1() -> None:
    battery = Nyx.battery.state
    if battery in [UNKNOWN, UNAVAILABLE]:
        card.row_1_icon = Icon.BATTERY_UNKNOWN
        return

    card.row_1_value = battery + "%"
    card.row_1_icon = battery_icon(
        battery=float(battery),
        charging=Nyx.charger.is_on,
        full_threshold=int(Nyx.charge_limit.state),
    )


@state_change_trigger(Nyx.location, Nyx.destination, Nyx.lock, Nyx.parked)
def set_row_2() -> None:
    if Nyx.location.state == HOME:
        card.row_2_value = "Home"
        card.row_2_icon = Icon.HOME
        card.row_2_color = RowColor.DEFAULT
        return

    if Nyx.destination.state != UNKNOWN and not Nyx.parked.is_on:
        destination_metadata = ZoneExtended.get_zone_metadata(Nyx.destination.state)
        card.row_2_value = str(destination_metadata.short_name)
        card.row_2_icon = Icon.NAVIGATION
        card.row_2_color = RowColor.DEFAULT
        return

    if Nyx.lock.state in [UNKNOWN, UNAVAILABLE]:
        card.row_2_value = "Unknown"
        card.row_2_icon = Icon.LOCK_QUESTION
        return

    card.row_2_value = Nyx.lock.state
    card.row_2_icon = Icon.LOCK if Nyx.lock.state == "locked" else Icon.LOCK_OPEN_VARIANT
    card.row_2_color = RowColor.DEFAULT if Nyx.lock.state == "locked" else RowColor.RED


@state_change_trigger(Nyx.parked, Nyx.arrival_time, Nyx.temperature_inside, Nyx.climate)
def set_row_3() -> None:
    if Nyx.climate.state in [UNKNOWN, UNAVAILABLE]:
        card.row_3_icon = Icon.THERMOMETER_OFF
        return

    now = local_now()
    seconds_remaining = (resolve_timestamp(Nyx.arrival_time.state) - now).total_seconds()

    if not Nyx.parked.is_on and seconds_remaining >= 0:
        card.row_3_value = f"{seconds_remaining // 60} minutes"
        card.row_3_icon = Icon.MAP_CLOCK

        JobScheduler().schedule_job(
            run_time=now + timedelta(seconds=30),
            func=set_row_3,
            job_id=ARRIVAL_TIME_RECHECK_JOB_ID,
        )
        return

    current_temp = int(float(Nyx.temperature_inside.state))
    card.row_3_value = f"{current_temp}° F"
    card.row_3_icon = Icon.THERMOMETER
    card.row_3_color = RowColor.RED if current_temp >= 100 else RowColor.DEFAULT
