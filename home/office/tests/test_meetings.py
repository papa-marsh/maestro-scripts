from maestro.domains import AWAY, HOME, OFF, ON
from maestro.integrations import Domain
from maestro.registry import maestro, person, switch
from maestro.testing import MaestroTest
from maestro.triggers import HassEvent, MaestroEvent

from .. import meetings


def test_initialize_meeting_active_entity(maestro_test: MaestroTest) -> None:
    # Test entity is created on HASS startup
    maestro_test.assert_entity_does_not_exist(maestro.meeting_active)
    maestro_test.trigger_hass_event(HassEvent.STARTUP)
    maestro_test.assert_entity_exists(maestro.meeting_active)

    maestro_test.reset()

    # Test entity is created on Maestro startup
    maestro_test.assert_entity_does_not_exist(maestro.meeting_active)
    maestro_test.trigger_maestro_event(MaestroEvent.STARTUP)
    maestro_test.assert_entity_exists(maestro.meeting_active)


def test_toggle_meeting_active(maestro_test: MaestroTest) -> None:
    # Setup: Initialize meeting_active entity and set person.emily away
    maestro_test.set_state(maestro.meeting_active, OFF)
    maestro_test.set_state(person.emily, AWAY)
    maestro_test.set_state(switch.office_door_led, OFF)

    # Test turning meeting on when Emily is not home (no notification)
    maestro_test.trigger_event("meeting_active")
    maestro_test.assert_state(maestro.meeting_active, ON)
    maestro_test.assert_action_called(Domain.SWITCH, "turn_on", entity_id="switch.office_door_led")
    maestro_test.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    maestro_test.clear_action_calls()

    # Test turning meeting off
    maestro_test.trigger_event("meeting_active")
    maestro_test.assert_state(maestro.meeting_active, OFF)
    maestro_test.assert_action_called(Domain.SWITCH, "turn_off", entity_id="switch.office_door_led")

    maestro_test.clear_action_calls()

    # Test turning meeting on when Emily is home (should send notification)
    maestro_test.set_state(person.emily, HOME)
    maestro_test.trigger_event("meeting_active")
    maestro_test.assert_state(maestro.meeting_active, ON)
    maestro_test.assert_action_called(Domain.SWITCH, "turn_on", entity_id="switch.office_door_led")
    maestro_test.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)


def test_meeting_active_on_arrival(maestro_test: MaestroTest) -> None:
    # Setup: Meeting is not active
    maestro_test.set_state(maestro.meeting_active, OFF)
    maestro_test.set_state(person.emily, AWAY)

    # Test: Emily arrives home when meeting is not active (no notification)
    maestro_test.trigger_state_change(person.emily, old=AWAY, new=HOME)
    maestro_test.assert_action_not_called(Domain.NOTIFY, person.emily.notify_action_name)

    maestro_test.clear_action_calls()

    # Setup: Emily leaves, Meeting is now active
    maestro_test.set_state(person.emily, AWAY)
    maestro_test.set_state(maestro.meeting_active, ON)

    # Test: Emily arrives home when meeting is active (should send notification)
    maestro_test.trigger_state_change(person.emily, old=AWAY, new=HOME)
    maestro_test.assert_action_called(Domain.NOTIFY, person.emily.notify_action_name)
