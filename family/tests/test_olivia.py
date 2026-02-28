from maestro.domains import AWAY, HOME
from maestro.integrations import Domain
from maestro.registry import person, switch
from maestro.testing import MaestroTest
from scripts.common.event_type import EventType

from .. import olivia


def test_toggle_sound_machine(mt: MaestroTest) -> None:
    # Sound machine doesn't turn on when Emily is not home
    mt.set_state(person.emily, AWAY)
    mt.trigger_event(EventType.OLIVIA_ASLEEP)
    mt.assert_action_not_called(
        domain=Domain.SWITCH,
        action="turn_on",
    )

    # Sound machine turns on when Emily is home
    mt.set_state(person.emily, HOME)
    mt.trigger_event(EventType.OLIVIA_ASLEEP)
    mt.assert_action_called(
        domain=Domain.SWITCH,
        action="turn_on",
        entity_id=switch.olivias_sound_machine.id,
    )

    # Sound machine turns off for 'olivia_awake' event
    mt.trigger_event(EventType.OLIVIA_AWAKE)
    mt.assert_action_called(
        domain=Domain.SWITCH,
        action="turn_off",
        entity_id=switch.olivias_sound_machine.id,
    )
