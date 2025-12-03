from maestro.domains import AWAY, HOME, OFF
from maestro.integrations import Domain
from maestro.registry import fan, person
from maestro.testing import MaestroTest

from .. import air_purifier


def test_air_purifier_on_while_away(maestro_test: MaestroTest) -> None:
    maestro_test.set_state(person.marshall, HOME)
    maestro_test.set_state(person.emily, HOME)
    maestro_test.set_state(fan.office_purifier, OFF)

    maestro_test.trigger_state_change(person.marshall, HOME, AWAY)
    maestro_test.assert_action_not_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    maestro_test.trigger_state_change(person.emily, HOME, AWAY)
    maestro_test.assert_action_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    maestro_test.trigger_state_change(person.marshall, AWAY, HOME)
    maestro_test.assert_action_called(Domain.FAN, "turn_off", fan.office_purifier.id)
