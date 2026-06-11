"""Tests for the admin event notification flow"""

from maestro.integrations import Domain
from maestro.registry import person
from maestro.testing import MaestroTest
from scripts.common.event_type import EventType

from .. import admin


def test_admin_event_sends_actionable_notif(mt: MaestroTest) -> None:
    """Test that admin_event sends Marshall a notification listing fireable events"""
    mt.trigger_event(EventType.ADMIN_EVENT)

    calls = mt.get_action_calls(Domain.NOTIFY, person.marshall.notify_action_name)
    assert len(calls) == 1

    payload = calls[0].kwargs
    assert payload["message"] == "Long-press to fire event"

    action_names = {action["action"] for action in payload["data"]["actions"]}
    expected_names = {
        f"{admin.FIRE_ACTION_PREFIX}{event_type}"
        for event_type in EventType
        if event_type not in admin.EXCLUDED_EVENT_TYPES
    }
    assert action_names == expected_names

    # Excluded events must not be offered as actions
    assert f"{admin.FIRE_ACTION_PREFIX}{EventType.ADMIN_EVENT}" not in action_names
    assert f"{admin.FIRE_ACTION_PREFIX}{EventType.MAESTRO_UI_EVENT}" not in action_names


def test_fire_admin_event_fires_selected_event(mt: MaestroTest) -> None:
    """Test that responding to the admin notification fires the selected event"""
    mt.trigger_notif_action(f"{admin.FIRE_ACTION_PREFIX}{EventType.BATHROOM_FLOOR}")

    mt.assert_event_fired(EventType.BATHROOM_FLOOR)


def test_fire_admin_event_fires_only_selected_event(mt: MaestroTest) -> None:
    """Test that only the selected event is fired, not the others"""
    mt.trigger_notif_action(f"{admin.FIRE_ACTION_PREFIX}{EventType.MEETING_ACTIVE}")

    mt.assert_event_fired(EventType.MEETING_ACTIVE)
    mt.assert_event_not_fired(EventType.BATHROOM_FLOOR)
    mt.assert_event_not_fired(EventType.ADMIN_EVENT)


def test_unrelated_notif_action_does_not_fire_event(mt: MaestroTest) -> None:
    """Test that an unrelated notif action doesn't fire any event"""
    mt.trigger_notif_action("some_other_action")

    assert len(mt.get_fired_events()) == 0
