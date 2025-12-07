from maestro.integrations import StateChangeEvent
from maestro.registry import maestro
from maestro.triggers import state_change_trigger

from .common import Nyx, Tess, get_vehicle_config

VehicleComplicationT = maestro.MaestroNyxComplication | maestro.MaestroTessComplication
VehicleT = type[Nyx] | type[Tess]


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

    vehicle.complication.update(
        trailing=get_trailing(vehicle),
        leading=get_leading(vehicle),
        outer=get_outer(vehicle),
        gauge=get_gauge(vehicle),
    )


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
