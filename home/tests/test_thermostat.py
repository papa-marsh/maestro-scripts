from maestro.integrations import Domain
from maestro.registry import climate, person
from maestro.testing import MaestroTest
from scripts.custom_domains.climate import Thermostat

from .. import thermostat


def test_check_thermostat_hold(mt: MaestroTest) -> None:
    mt.set_state(
        entity=climate.thermostat,
        state=Thermostat.HVACMode.HEAT,
        attributes={"preset_mode": Thermostat.PresetMode.NONE},
    )
    # Notif not sent when thermostat is not on hold
    thermostat.check_thermostat_hold()
    mt.assert_action_not_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Notif sent when thermostat is on hold
    mt.set_state(
        entity=climate.thermostat,
        state=Thermostat.HVACMode.HEAT,
        attributes={"preset_mode": Thermostat.PresetMode.HOLD},
    )
    thermostat.check_thermostat_hold()
    mt.assert_action_called(Domain.NOTIFY, person.marshall.notify_action_name)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)
