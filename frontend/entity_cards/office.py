from dataclasses import asdict

from maestro.domains import ON, UNAVAILABLE, UNKNOWN
from maestro.integrations import StateChangeEvent
from maestro.registry import maestro, sensor, switch
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from scripts.common.event_type import UIEvent, ui_event_trigger
from scripts.frontend.common.entity_card import EntityCardAttributes
from scripts.frontend.common.icons import Icon
from scripts.home.office.meetings import toggle_meeting_active

card = maestro.entity_card_4


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes = EntityCardAttributes(
        title="Office",
        icon=Icon.CLOUD,
    )
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state="Loading...",
        attributes=asdict(attributes),
        restore_cached=True,
    )
    card.update(title=attributes.title, row_2_icon=Icon.FINANCE, row_3_icon=Icon.CLOUD_OUTLINE)


@state_change_trigger(maestro.meeting_active)
def set_state(state_change: StateChangeEvent) -> None:
    if state_change.new.state == ON:
        active = True
        state = "Busy"
        icon = Icon.HEADSET
    else:
        active = False
        state = "Available"
        icon = Icon.CLOUD

    card.update(state=state, active=active, icon=icon)


@state_change_trigger(
    sensor.office_ambient_sensor_temperature,
    sensor.office_ambient_sensor_humidity,
    switch.space_heater,
)
def set_row_1() -> None:
    if sensor.office_ambient_sensor_temperature.state in [UNKNOWN, UNAVAILABLE]:
        card.update(row_1_value="Offline", row_1_icon=Icon.THERMOMETER_OFF)
        return

    temperature = float(sensor.office_ambient_sensor_temperature.state)
    humidity = float(sensor.office_ambient_sensor_humidity.state)

    value = f"{temperature:.0f}° · {humidity:.0f}%"
    icon = Icon.RADIATOR if switch.space_heater.is_on else Icon.THERMOMETER_WATER
    card.update(row_1_value=value, row_1_icon=icon)


def set_row_2() -> None: ...
def set_row_3() -> None: ...


@cron_trigger(hour=8, minute=30, day_of_week=[0, 1, 2, 3, 4])
def daily_review_reminder() -> None:
    card.blink = True


@ui_event_trigger(UIEvent.ENTITY_CARD_4_TAP)
def handle_tap() -> None:
    if card.blink:
        card.blink = False
        return

    toggle_meeting_active()


@ui_event_trigger(UIEvent.ENTITY_CARD_4_DOUBLE_TAP)
def handle_double_tap() -> None: ...  # Toggle finance view


@ui_event_trigger(UIEvent.ENTITY_CARD_4_HOLD)
def handle_hold() -> None:
    if switch.space_heater.is_on:
        switch.space_heater.turn_off()
    else:
        switch.space_heater.turn_on()
