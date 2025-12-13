from maestro.domains import AWAY, HOME, OFF, ON
from maestro.integrations import Domain
from maestro.registry import maestro, person, switch
from maestro.testing import MaestroTest
from maestro.triggers import HassEvent, MaestroEvent

from .. import meetings


def test_initialize_meeting_active_entity(mt: MaestroTest) -> None:
    # Test entity is created on HASS startup
    mt.assert_entity_does_not_exist(maestro.meeting_active)
    mt.trigger_hass_event(HassEvent.STARTUP)
    mt.assert_entity_exists(maestro.meeting_active)

    mt.reset()

    # Test entity is created on Maestro startup
    mt.assert_entity_does_not_exist(maestro.meeting_active)
    mt.trigger_maestro_event(MaestroEvent.STARTUP)
    mt.assert_entity_exists(maestro.meeting_active)


def test_toggle_meeting_active(mt: MaestroTest) -> None:
    # Setup: Initialize meeting_active entity and set person.emily away
    mt.set_state(maestro.meeting_active, OFF)
    mt.set_state(person.emily, AWAY)
    mt.set_state(switch.office_door_led, OFF)

    # Test turning meeting on when Emily is not home (no notification)
    mt.trigger_event("meeting_active")
    mt.assert_state(maestro.meeting_active, ON)
    mt.assert_action_called(Domain.SWITCH, "turn_on", entity_id="switch.office_door_led")
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    mt.clear_action_calls()

    # Test turning meeting off
    mt.trigger_event("meeting_active")
    mt.assert_state(maestro.meeting_active, OFF)
    mt.assert_action_called(Domain.SWITCH, "turn_off", entity_id="switch.office_door_led")

    mt.clear_action_calls()

    # Test turning meeting on when Emily is home (should send notification)
    mt.set_state(person.emily, HOME)
    mt.trigger_event("meeting_active")
    mt.assert_state(maestro.meeting_active, ON)
    mt.assert_action_called(Domain.SWITCH, "turn_on", entity_id="switch.office_door_led")
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)


def test_meeting_active_on_arrival(mt: MaestroTest) -> None:
    # Setup: Meeting is not active
    mt.set_state(maestro.meeting_active, OFF)
    mt.set_state(person.emily, AWAY)

    # Test: Emily arrives home when meeting is not active (no notification)
    mt.trigger_state_change(person.emily, old=AWAY, new=HOME)
    mt.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    mt.clear_action_calls()

    # Setup: Emily leaves, Meeting is now active
    mt.set_state(person.emily, AWAY)
    mt.set_state(maestro.meeting_active, ON)

    # Test: Emily arrives home when meeting is active (should send notification)
    mt.trigger_state_change(person.emily, old=AWAY, new=HOME)
    mt.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
