from maestro.domains import AWAY, HOME
from maestro.integrations import Domain
from maestro.registry import fan, person
from maestro.testing import MaestroTest

from .. import air_purifier


def test_air_purifier_on_while_away(mt: MaestroTest) -> None:
    # Fan stays off while someone's home
    mt.set_state(person.marshall, HOME)
    mt.set_state(person.emily, HOME)
    mt.trigger_state_change(person.marshall, new=AWAY)
    mt.assert_action_not_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    # Fan turns on when second person leaves
    mt.trigger_state_change(person.emily, new=AWAY)
    mt.assert_action_called(Domain.FAN, "turn_on", fan.office_purifier.id)

    # Fan turns off when someone arrives at home
    mt.trigger_state_change(person.emily, new=HOME)
    mt.assert_action_called(Domain.FAN, "turn_off", fan.office_purifier.id)
