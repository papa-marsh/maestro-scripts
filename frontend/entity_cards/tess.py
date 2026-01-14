from dataclasses import asdict
from datetime import timedelta

from maestro.domains import UNAVAILABLE, UNKNOWN, Entity
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

card = maestro.entity_card_1

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
        state = "Driving"
        icon = Icon.ROAD_VARIANT
        active = True
    elif Tess.climate.state == Tess.climate.HVACMode.HEAT_COOL:
        state = "Air On"
        icon = Icon.FAN
        active = True
    else:
        state = "Air Off"
        icon = Icon.UPDATE if Tess.software_update.is_on else Icon.CAR_ELECTRIC
        active = False

    card.update(state=state, icon=icon, active=active)


@state_change_trigger(Tess.battery)
def set_row_1() -> None:
    battery = Tess.battery.state
    if battery in [UNKNOWN, UNAVAILABLE]:
        card.row_1_icon = Icon.BATTERY_UNKNOWN
        return

    value = battery + "%"
    icon = battery_icon(
        battery=float(battery),
        charging=Tess.charger.is_on,
        full_threshold=int(Tess.charge_limit.state),
    )
    card.update(row_1_value=value, row_1_icon=icon)


@state_change_trigger(Tess.location, Tess.destination, Tess.lock, Tess.parked)
def set_row_2() -> None:
    if Tess.location.is_home:
        value = "Home"
        icon = Icon.HOME
        color = RowColor.DEFAULT
    elif Tess.destination.state != UNKNOWN and not Tess.parked.is_on:
        destination_metadata = ZoneExtended.get_zone_metadata(Tess.destination.state)
        value = str(destination_metadata.short_name)
        icon = Icon.NAVIGATION
        color = RowColor.DEFAULT
    elif Tess.lock.state in [UNKNOWN, UNAVAILABLE]:
        value = "Unknown"
        icon = Icon.LOCK_QUESTION
        color = RowColor(card.row_2_color)
    else:
        value = Tess.lock.state
        icon = Icon.LOCK if Tess.lock.state == "locked" else Icon.LOCK_OPEN_VARIANT
        color = RowColor.DEFAULT if Tess.lock.state == "locked" else RowColor.RED

    card.update(row_2_value=value, row_2_icon=icon, row_2_color=color)


@state_change_trigger(Tess.parked, Tess.arrival_time, Tess.climate, Tess.temperature_inside)
def set_row_3() -> None:
    entities: list[Entity] = [Tess.temperature_inside, Tess.parked, Tess.arrival_time, Tess.climate]
    if any(entity.state in [UNKNOWN, UNAVAILABLE] for entity in entities):
        card.update(
            row_3_value="Unavailable",
            row_3_icon=Icon.THERMOMETER_OFF,
            row_3_color=RowColor.DEFAULT,
        )
        return

    if not Tess.parked.is_on:
        now = local_now()
        seconds_remaining = (resolve_timestamp(Tess.arrival_time.state) - now).total_seconds()
        minutes_remaining = int(seconds_remaining // 60)

        if minutes_remaining >= 0:
            value = f"{minutes_remaining} minutes"
            card.update(row_3_value=value, row_3_icon=Icon.MAP_CLOCK)

            JobScheduler().schedule_job(
                run_time=now + timedelta(seconds=30),
                func=set_row_3,
                job_id=ARRIVAL_TIME_RECHECK_JOB_ID,
            )
            return

    current_temp = int(float(Tess.temperature_inside.state))
    value = f"{current_temp}° F"
    color = RowColor.RED if current_temp >= 100 else RowColor.DEFAULT

    card.update(row_3_value=value, row_3_icon=Icon.THERMOMETER, row_3_color=color)
