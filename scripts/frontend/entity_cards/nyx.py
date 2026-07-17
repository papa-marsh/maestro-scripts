from dataclasses import asdict
from datetime import timedelta

from maestro.domains import UNAVAILABLE, UNKNOWN, Entity
from maestro.integrations import StateManager
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import JobScheduler, local_now, resolve_timestamp

from custom_domains.zone_extended import ZoneExtended
from registry import maestro
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
    StateManager().initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.title = attributes.title


@state_change_trigger(
    Nyx.climate,
    Nyx.parked,
    Nyx.software_update,
    Nyx.battery,
    Nyx.location,
    Nyx.destination,
    Nyx.lock,
    Nyx.arrival_time,
    Nyx.temperature_inside,
)
def update_card() -> None:
    """Recompute all card attributes from current entity state in a single atomic update"""
    state, attributes = _compute_state()
    attributes.update(_compute_row_1())
    attributes.update(_compute_row_2())
    attributes.update(_compute_row_3())
    card.update(state=state, **attributes)


def _compute_state() -> tuple[str, dict[str, str | bool]]:
    if not Nyx.parked.is_on:
        return "Driving", {"icon": Icon.ROAD_VARIANT, "active": True}
    if Nyx.climate.state == Nyx.climate.HVACMode.HEAT_COOL:
        return "Air On", {"icon": Icon.FAN, "active": True}

    icon = Icon.UPDATE if Nyx.software_update.is_on else Icon.CAR_ELECTRIC_OUTLINE
    return "Air Off", {"icon": icon, "active": False}


def _compute_row_1() -> dict[str, str]:
    battery = Nyx.battery.state
    if battery in [UNKNOWN, UNAVAILABLE]:
        return {"row_1_icon": Icon.BATTERY_UNKNOWN}

    icon = battery_icon(
        battery=float(battery),
        charging=Nyx.charger.is_on,
        full_threshold=int(Nyx.charge_limit.state),
    )
    return {"row_1_value": battery + "%", "row_1_icon": icon}


def _compute_row_2() -> dict[str, str]:
    if Nyx.location.is_home:
        return {"row_2_value": "Home", "row_2_icon": Icon.HOME, "row_2_color": RowColor.DEFAULT}
    if Nyx.destination.state != UNKNOWN and not Nyx.parked.is_on:
        destination_metadata = ZoneExtended.get_zone_metadata(Nyx.destination.state)
        return {
            "row_2_value": str(destination_metadata.short_name),
            "row_2_icon": Icon.NAVIGATION,
            "row_2_color": RowColor.DEFAULT,
        }
    if Nyx.lock.state in [UNKNOWN, UNAVAILABLE]:
        return {
            "row_2_value": "Unknown",
            "row_2_icon": Icon.LOCK_QUESTION,
            "row_2_color": RowColor(card.row_2_color),
        }

    locked = Nyx.lock.state == "locked"
    return {
        "row_2_value": Nyx.lock.state,
        "row_2_icon": Icon.LOCK if locked else Icon.LOCK_OPEN_VARIANT,
        "row_2_color": RowColor.DEFAULT if locked else RowColor.RED,
    }


def _compute_row_3() -> dict[str, str]:
    entities: list[Entity] = [Nyx.temperature_inside, Nyx.parked, Nyx.arrival_time, Nyx.climate]
    if any(entity.state in [UNKNOWN, UNAVAILABLE] for entity in entities):
        return {
            "row_3_value": "Unavailable",
            "row_3_icon": Icon.THERMOMETER_OFF,
            "row_3_color": RowColor.DEFAULT,
        }

    if not Nyx.parked.is_on:
        now = local_now()
        seconds_remaining = (resolve_timestamp(Nyx.arrival_time.state) - now).total_seconds()
        minutes_remaining = int(seconds_remaining // 60)

        if minutes_remaining >= 0:
            JobScheduler().schedule_job(
                run_time=now + timedelta(seconds=30),
                func=update_card,
                job_id=ARRIVAL_TIME_RECHECK_JOB_ID,
            )
            return {"row_3_value": f"{minutes_remaining} minutes", "row_3_icon": Icon.MAP_CLOCK}

    current_temp = int(float(Nyx.temperature_inside.state))
    color = RowColor.RED if current_temp >= 100 else RowColor.DEFAULT
    return {
        "row_3_value": f"{current_temp}° F",
        "row_3_icon": Icon.THERMOMETER,
        "row_3_color": color,
    }
