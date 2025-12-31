from datetime import date

from maestro.integrations import EntityId, StateManager
from maestro.registry import calendar, maestro, sun
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import local_now, log
from scripts.custom_domains.google_calendar import GoogleCalendar

calendar_ids: list[GoogleCalendar] = [
    calendar.family.id,
    calendar.marshall.id,
    calendar.emily.id,
    calendar.ellie.id,
    calendar.olivia.id,
]


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_sidebar_text_entity() -> None:
    sidebar_text = build_sidebar_text()

    _entity_data, created = StateManager().initialize_hass_entity(
        entity_id=EntityId("maestro.cast_sidebar_text"),
        state=sidebar_text,
        attributes={},
    )
    if created:
        log.info("Initialized entity for `maestro.cast_sidebar_text`")
    else:
        log.info("Entity `maestro.cast_sidebar_text` already exists. Skipping initialization")


@cron_trigger(minute=10)
@state_change_trigger(*calendar_ids)
def set_sidebar_text() -> None:
    maestro.cast_sidebar_text = build_sidebar_text()


def build_sidebar_text() -> str:
    day_of_week = date.today().strftime("%A")

    if sun.sun.is_above_horizon:
        sun_action = "sets"
        sun_time = sun.sun.next_setting
    else:
        sun_action = "rises"
        sun_time = sun.sun.next_rising

    upcoming_events = calendar.family.get_gcal_events(days=7, calendar_ids=calendar_ids)
    for calendar_event in upcoming_events:
        if calendar_event.start < local_now():
            continue
        next_event = calendar_event
        break

    next_up = f"Next up is {next_event.title}, {next_event.start.strftime('%A')}"
    if not next_event.all_day:
        next_up += f" at {next_event.start.strftime('%-I:%M %p')}"

    return f"""
        <li>Happy {day_of_week}!</li>
        <li>The sun {sun_action} at {sun_time}.</li>
        <li>‎</li>
        <li>{next_up}.</li>
    """
