from maestro.registry import climate, person
from maestro.triggers import cron_trigger
from maestro.utils import Notif
from scripts.custom_domains.climate import Thermostat
from scripts.custom_domains.zone import ZoneExtended


@cron_trigger(hour=12)
@cron_trigger(hour=20)
def thermostat_hold_reminder() -> None:
    marshall_zone = ZoneExtended.get_zone_metadata(person.marshall.state)
    emily_zone = ZoneExtended.get_zone_metadata(person.emily.state)

    if not marshall_zone.lakeshore or not emily_zone.lakeshore:
        return
    if climate.thermostat.preset_mode == Thermostat.PresetMode.HOLD:
        return

    Notif(
        title="Thermostat on Auto",
        message=(
            f"The thermostat is set to auto mode at {climate.thermostat.temperature}°. "
            "Consider setting a hold at a more conservative setpoint to save energy."
        ),
    ).send(person.marshall)


@cron_trigger(hour=8)
@cron_trigger(hour=20)
def check_thermostat_hold() -> None:
    if climate.thermostat.preset_mode == Thermostat.PresetMode.HOLD:
        Notif(
            title="Thermostat Set To Hold",
            message=f"The thermostat is still set to hold at {climate.thermostat.temperature}",
        ).send(person.marshall)
