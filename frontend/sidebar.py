from datetime import date

from maestro.integrations import EntityId, StateManager
from maestro.registry import calendar, maestro
from maestro.triggers import HassEvent, MaestroEvent, cron_trigger, hass_trigger, maestro_trigger
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
    StateManager().initialize_hass_entity(
        entity_id=EntityId("maestro.cast_sidebar_text"),
        state=build_sidebar_text(),
        attributes={},
    )


@cron_trigger(hour=0)
def set_sidebar_text() -> None:
    maestro.cast_sidebar_text.state = build_sidebar_text()


def build_sidebar_text() -> str:
    today = date.today().strftime("%A")

    return f"""
        <li>Happy {today}!</li>
        <li>‎</li>
    """
