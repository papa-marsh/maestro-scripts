from maestro.domains import AWAY, HOME, OFF, ON
from maestro.integrations import Domain
from maestro.registry import maestro, person
from maestro.testing import MaestroTest
from maestro.triggers import HassEvent

from .. import meetings


def test_initialize_meeting_active_entity(mt: MaestroTest) -> None:
    # Entity created by hass startup
    mt.assert_entity_does_not_exist(maestro.meeting_active)
    mt.trigger_hass_event(HassEvent.STARTUP)
    mt.assert_entity_exists(maestro.meeting_active)

    # No-op if entity already exists
    mt.set_state(maestro.meeting_active, ON)
    mt.trigger_hass_event(HassEvent.STARTUP)
    mt.assert_state(maestro.meeting_active, ON)


def test_toggle_meeting_active(mt: MaestroTest) -> None:
    # Action toggles entity off
    mt.set_state(maestro.meeting_active, ON)
    mt.trigger_event("meeting_active")
    mt.assert_state(maestro.meeting_active, OFF)

    # Notif doesn't send when Emily's away
    mt.set_state(person.emily, AWAY)
    mt.trigger_event("meeting_active")
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Notif sends when Emily arrives home if meeting is active
    mt.trigger_state_change(person.emily, new=HOME)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)

    # Notif sends immediately if Emily is home
    mt.clear_action_calls()
    mt.set_state(maestro.meeting_active, OFF)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)
    mt.trigger_event("meeting_active")
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
