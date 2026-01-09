from maestro.domains import HOME, OFF, ON
from maestro.integrations import EntityId, StateChangeEvent, StateManager
from maestro.registry import maestro, person, switch
from maestro.triggers import HassEvent, event_fired_trigger, hass_trigger, state_change_trigger
from maestro.utils import Notif
from scripts.common.event_type import EventType


@hass_trigger(HassEvent.STARTUP)
def initialize_meeting_active_entity() -> None:
    """Create the entity only if it doesn't already exist"""
    StateManager().initialize_hass_entity(
        entity_id=EntityId("maestro.meeting_active"),
        state=OFF,
        attributes={},
        restore_cached=True,
    )


@event_fired_trigger(EventType.MEETING_ACTIVE)
def toggle_meeting_active() -> None:
    maestro.meeting_active.state = ON if maestro.meeting_active.state == OFF else OFF


@state_change_trigger(maestro.meeting_active, to_state=ON)
@state_change_trigger(person.emily, to_state=HOME)
def send_meeting_notif() -> None:
    if person.emily.state == HOME and maestro.meeting_active.state == ON:
        Notif(
            title="Dad's In a Meeting",
            message="Shhh",
            tag="meeting_active",
            priority=Notif.Priority.TIME_SENSITIVE,
        ).send(person.emily)


@state_change_trigger(maestro.meeting_active)
def toggle_door_leds(state_change: StateChangeEvent) -> None:
    if state_change.new.state == ON:
        switch.office_door_led.turn_on()
    else:
        switch.office_door_led.turn_off()
