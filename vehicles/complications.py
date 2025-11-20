from contextlib import suppress

from maestro.integrations import EntityId, StateChangeEvent, StateManager
from maestro.registry import maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import local_now
from scripts.custom_domains import AppleWatchComplication

from .common import Nyx, Tess, get_vehicle_config

VehicleComplicationT = maestro.MaestroNyxComplication | maestro.MaestroTessComplication
VehicleT = type[Nyx] | type[Tess]


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_complication_entities() -> None:
    gauge_text = AppleWatchComplication.GaugeText(
        leading="",
        outer="",
        trailing="",
        gauge=1.0,
    )

    for vehicle in (Nyx, Tess):
        with suppress(FileExistsError):
            StateManager().upsert_hass_entity(
                entity_id=vehicle.complication.id,
                state=local_now().isoformat(),
                attributes=dict(gauge_text),
                create_only=True,
            )


def get_complication_and_vehicle(entity_id: EntityId) -> tuple[VehicleComplicationT, VehicleT]:
    if ".nyx_" in entity_id:
        return maestro.nyx_complication, Nyx
    else:
        return maestro.tess_complication, Tess


@state_change_trigger(
    Nyx.battery,
    Nyx.lock,
    Nyx.climate,
    Nyx.charger,
    Tess.battery,
    Tess.lock,
    Tess.climate,
    Tess.charger,
)
def update_complication(state_change: StateChangeEvent) -> None:
    vehicle = get_vehicle_config(state_change.entity_id)

    attributes = AppleWatchComplication.GaugeText(
        leading=get_leading(vehicle),
        outer=get_outer(vehicle),
        trailing=get_trailing(vehicle),
        gauge=get_gauge(vehicle),
    )

    vehicle.complication.update(attributes)


def get_leading(vehicle: VehicleT) -> str:
    return "🔒" if vehicle.lock.state == "locked" else ""


def get_trailing(vehicle: VehicleT) -> str:
    if vehicle.climate.state != vehicle.climate.HVACMode.HEAT_COOL:
        return ""

    setpoint = vehicle.climate.temperature
    inside_temp = vehicle.climate.current_temperature
    if setpoint == inside_temp:
        outside_temp = float(vehicle.temperature_outside.state)
        return "❄️" if setpoint <= outside_temp else "♨️"
    else:
        return "❄️" if setpoint <= inside_temp else "♨️"


def get_outer(vehicle: VehicleT) -> str:
    outer = vehicle.battery.state
    outer += "⚡️" if vehicle.charger.is_on else "%"
    return outer


def get_gauge(vehicle: VehicleT) -> float:
    return float(vehicle.battery.state) / float(vehicle.charge_limit.state)
