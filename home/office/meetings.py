from contextlib import suppress

from maestro.integrations import EntityId, StateChangeEvent, StateManager
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


@state_change_trigger(maestro.meeting_active)
def meeting_active(state_change: StateChangeEvent) -> None:
    if state_change.new.state == "on":
        switch.office_door_led.turn_on()
        if person.emily.state == "home":
            send_meeting_notification()
    else:
        switch.office_door_led.turn_off()


@event_fired_trigger("office_leds")
def toggle_office_leds() -> None:
    switch.office_door_led.toggle()


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
