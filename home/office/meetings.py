from contextlib import suppress

from maestro.integrations import EntityId, StateManager
from maestro.registry import maestro, person, switch
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    event_fired_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import Notif


@hass_trigger(HassEvent.STARTUP_NOT_WORKING_YET)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_meeting_active_entity() -> None:
    with suppress(FileExistsError):
        StateManager().upsert_hass_entity(
            entity_id=EntityId("maestro.meeting_active"),
            state="off",
            attributes={},
            create_only=True,
        )


@event_fired_trigger("meeting_active")
def toggle_meeting_active() -> None:
    if maestro.meeting_active.state == "off":
        maestro.meeting_active.state = "on"
        switch.office_door_led.turn_on()
        if person.emily.state == "home":
            send_meeting_notification()
    else:
        maestro.meeting_active.state = "off"
        switch.office_door_led.turn_off()


@state_change_trigger(person.emily, to_state="home")
def meeting_active_on_arrival() -> None:
    if maestro.meeting_active.state == "on":
        send_meeting_notification()


def send_meeting_notification() -> None:
    Notif(
        title="Dad's In a Meeting",
        message="Shhh",
        tag="meeting_active",
        priority=Notif.Priority.TIME_SENSITIVE,
    ).send(person.emily)
