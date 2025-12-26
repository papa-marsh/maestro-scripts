from maestro.registry import climate, person
from maestro.triggers import cron_trigger
from maestro.utils import Notif
from scripts.custom_domains.climate import Thermostat


@cron_trigger(hour=8)
def check_thermostat_hold() -> None:
    if climate.thermostat.preset_mode == Thermostat.PresetMode.HOLD:
        Notif(
            title="Thermostat on Hold",
            message="The thermostat is still set to hold mode",
        ).send(person.marshall)
