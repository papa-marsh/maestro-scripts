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
from scripts.custom_domains.zone_extended import ZoneExtended
from scripts.frontend.common.entity_card import EntityCardAttributes, RowColor
from scripts.frontend.common.icons import Icon, battery_icon
from scripts.vehicles.common import Tess

card = maestro.entity_card_5

ARRIVAL_TIME_RECHECK_JOB_ID = "tess_arrival_time_recheck"


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Tess",
        icon=Icon.CAR_ELECTRIC,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.title = attributes.title


@state_change_trigger(Tess.climate, Tess.parked, Tess.software_update)
def set_state() -> None:
    if not Tess.parked.is_on:
        card.state = "Driving"
        card.icon = Icon.ROAD_VARIANT
        card.active = True
        return

    if Tess.climate.state == Tess.climate.HVACMode.HEAT_COOL:
        card.state = "Air On"
        card.icon = Icon.FAN
        card.active = True
        return

    card.state = "Air Off"
    card.icon = Icon.UPDATE if Tess.software_update.is_on else Icon.CAR_ELECTRIC
    card.active = False


@state_change_trigger(Tess.battery)
def set_row_1() -> None:
    battery = Tess.battery.state
    if battery in [UNKNOWN, UNAVAILABLE]:
        card.row_1_icon = Icon.BATTERY_UNKNOWN
        return

    card.row_1_value = battery + "%"
    card.row_1_icon = battery_icon(
        battery=float(battery),
        charging=Tess.charger.is_on,
        full_threshold=int(Tess.charge_limit.state),
    )


@state_change_trigger(Tess.location, Tess.destination, Tess.lock, Tess.parked)
def set_row_2() -> None:
    if Tess.location.state == HOME:
        card.row_2_value = "Home"
        card.row_2_icon = Icon.HOME
        card.row_2_color = RowColor.DEFAULT
        return

    if Tess.destination.state != UNKNOWN and not Tess.parked.is_on:
        destination_metadata = ZoneExtended.get_zone_metadata(Tess.destination.state)
        card.row_2_value = str(destination_metadata.short_name)
        card.row_2_icon = Icon.NAVIGATION
        card.row_2_color = RowColor.DEFAULT
        return

    if Tess.lock.state in [UNKNOWN, UNAVAILABLE]:
        card.row_2_value = "Unknown"
        card.row_2_icon = Icon.LOCK_QUESTION
        return

    card.row_2_value = Tess.lock.state
    card.row_2_icon = Icon.LOCK if Tess.lock.state == "locked" else Icon.LOCK_OPEN_VARIANT
    card.row_2_color = RowColor.DEFAULT if Tess.lock.state == "locked" else RowColor.RED


@state_change_trigger(Tess.parked, Tess.arrival_time, Tess.temperature_inside, Tess.climate)
def set_row_3() -> None:
    if Tess.climate.state in [UNKNOWN, UNAVAILABLE]:
        card.row_3_icon = Icon.THERMOMETER_OFF
        return

    now = local_now()
    seconds_remaining = (resolve_timestamp(Tess.arrival_time.state) - now).total_seconds()

    if not Tess.parked.is_on and seconds_remaining >= 0:
        card.row_3_value = f"{seconds_remaining // 60} minutes"
        card.row_3_icon = Icon.MAP_CLOCK

        JobScheduler().schedule_job(
            run_time=now + timedelta(seconds=30),
            func=set_row_3,
            job_id=ARRIVAL_TIME_RECHECK_JOB_ID,
        )
        return

    current_temp = int(float(Tess.temperature_inside.state))
    card.row_3_value = f"{current_temp}° F"
    card.row_3_icon = Icon.THERMOMETER
    card.row_3_color = RowColor.RED if current_temp >= 100 else RowColor.DEFAULT
