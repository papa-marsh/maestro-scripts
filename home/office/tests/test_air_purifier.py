from maestro.domains import AWAY, HOME, OFF
from maestro.integrations import Domain
from maestro.registry import fan, person
from maestro.testing import MaestroTest

from .. import air_purifier


def test_air_purifier_on_while_away(mt: MaestroTest) -> None:
    mt.set_state(person.marshall, HOME)
    mt.set_state(person.emily, HOME)
    mt.set_state(fan.office_purifier, OFF)

    mt.trigger_state_change(person.marshall, HOME, AWAY)
    mt.assert_action_not_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    mt.trigger_state_change(person.emily, HOME, AWAY)
    mt.assert_action_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    mt.trigger_state_change(person.marshall, AWAY, HOME)
    mt.assert_action_called(Domain.FAN, "turn_off", fan.office_purifier.id)
