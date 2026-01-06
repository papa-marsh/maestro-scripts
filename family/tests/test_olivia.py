from maestro.integrations import Domain
from maestro.registry import switch
from maestro.testing import MaestroTest
from scripts.common.event_type import EventType

from .. import olivia


def test_toggle_sound_machine(mt: MaestroTest) -> None:
    # Sound machine turns on for 'olivia_asleep' event
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
