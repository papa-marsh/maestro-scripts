from maestro.integrations import StateChangeEvent
from maestro.registry import person
from maestro.triggers import cron_trigger, state_change_trigger
from maestro.utils import Notif

from .common import Nyx, Tess

DEFAULT_CHARGE_LIMIT = 80


@state_change_trigger(Nyx.charger, Tess.charger, to_state="on")
def high_charge_limit(state_change: StateChangeEvent) -> None:
    vehicle = Nyx if state_change.entity_id == Nyx.charger.id else Tess

    if int(vehicle.charge_limit.state) > DEFAULT_CHARGE_LIMIT:
        name = vehicle.__name__
        Notif(
            title="High Charge Limit",
            message=f"{name} is plugged in with a charge limit of {vehicle.charge_limit.state}%.",
            tag="high_charge_limit",
        ).send(person.marshall)


@cron_trigger(hour=19)
def charge_reminder() -> None:
    for vehicle in (Nyx, Tess):
        name = vehicle.__name__

        is_home = vehicle.location_tracker.state == "home"
        unplugged = vehicle.charger == "off"
        low_battery = int(vehicle.battery.state) < int(vehicle.charge_limit.state) - 20

        if is_home and unplugged and low_battery:
            Notif(
                title="",
                message=f"{name} is unplugged with only {vehicle.battery.state}% battery",
                tag=f"{name.lower()}_charge_reminder",
                priority=Notif.Priority.TIME_SENSITIVE,
            ).send(person.marshall, person.emily)
