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

from .common import Nyx, Tess


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP_NOT_WORKING_YET)
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
                entity_id=EntityId(vehicle.watch_complication_id),
                state=local_now().isoformat(),
                attributes=dict(gauge_text),
                create_only=True,
            )


def get_complication_and_vehicle(
    entity_id: EntityId,
) -> tuple[
    maestro.MaestroNyxComplication | maestro.MaestroTessComplication,
    type[Nyx] | type[Tess],
]:
    if ".nyx_" in entity_id:
        return maestro.nyx_complication, Nyx
    else:
        return maestro.tess_complication, Tess


@state_change_trigger(Nyx.battery, Tess.battery)
def update_complication_leading(state_change: StateChangeEvent) -> None:
    complication, _ = get_complication_and_vehicle(state_change.entity_id)
    complication.leading = "🔒" if state_change.new.state == "locked" else ""


@state_change_trigger(Nyx.charger, Tess.charger)
def update_complication_trailing(state_change: StateChangeEvent) -> None:
    complication, _ = get_complication_and_vehicle(state_change.entity_id)
    complication.trailing = "⚡️" if state_change.new.state == "on" else ""


@state_change_trigger(Nyx.battery, Nyx.climate, Tess.battery, Tess.climate)
def update_complication_outer(state_change: StateChangeEvent) -> None:
    complication, vehicle = get_complication_and_vehicle(state_change.entity_id)
    text = vehicle.battery.state
    if vehicle.climate.state == vehicle.climate.HVACMode.HEAT_COOL:
        setpoint = vehicle.climate.temperature
        inside_temp = vehicle.climate.current_temperature
        if setpoint == inside_temp:
            text += "❄️" if setpoint <= int(vehicle.temperature_outside.state) else "♨️"
        else:
            text += "❄️" if setpoint <= inside_temp else "♨️"
    else:
        text += "%"
    complication.outer = text


@state_change_trigger(Nyx.charger, Tess.charger)
def update_complication_gauge(state_change: StateChangeEvent) -> None:
    complication, vehicle = get_complication_and_vehicle(state_change.entity_id)
    complication.gauge = float(vehicle.battery.state) / float(vehicle.charge_limit.state)
