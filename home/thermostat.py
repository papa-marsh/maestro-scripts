from maestro.registry import climate, person
from maestro.triggers import cron_trigger
from maestro.utils import Notif
from scripts.custom_domains.climate import Thermostat
from scripts.custom_domains.zone import ZoneExtended


@cron_trigger(hour=20)
def thermostat_hold_reminder() -> None:
    marshall_at_lakeshore = ZoneExtended.get_zone_metadata(person.marshall.state).lakeshore
    emily_at_lakeshore = ZoneExtended.get_zone_metadata(person.emily.state).lakeshore

    if (
        marshall_at_lakeshore
        and emily_at_lakeshore
        and climate.thermostat.preset_mode != Thermostat.PresetMode.HOLD
    ):
        Notif(
            title="Thermostat on Auto",
            message=(
                f"The thermostat is set to auto mode at {climate.thermostat.temperature}°. "
                "Consider setting a hold at a more conservative setpoint to save energy."
            ),
        ).send(person.marshall)


@cron_trigger(hour=8)
def check_thermostat_hold() -> None:
    if climate.thermostat.preset_mode == Thermostat.PresetMode.HOLD:
        Notif(
            title="Thermostat on Hold",
            message="The thermostat is still set to hold mode",
        ).send(person.marshall)
