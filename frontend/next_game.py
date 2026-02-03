from maestro.registry import calendar, maestro
from maestro.triggers import (
    HassEvent,
    MaestroEvent,
    cron_trigger,
    hass_trigger,
    maestro_trigger,
    state_change_trigger,
)
from maestro.utils import local_now, readable_relative_date
from scripts.custom_domains.google_calendar import GoogleCalendar
from scripts.frontend.common.icons import Icon

card = maestro.next_game_card


@hass_trigger(HassEvent.STARTUP)
@maestro_trigger(MaestroEvent.STARTUP)
def initialize_card() -> None:
    attributes: dict = {
        "icon": Icon.BASEBALL,
        "top_row": "Loading...",
        "middle_row": "Loading...",
        "bottom_row": "Loading...",
        "left_icon_path": "",
        "right_icon_path": "",
        "active": False,
    }
    card.state_manager.initialize_hass_entity(
        entity_id=card.id,
        state=local_now().isoformat(),
        attributes=attributes,
        restore_cached=True,
    )
    card.update(icon=attributes["icon"])


@cron_trigger(minute=5)  # TODO: make this more useful
@state_change_trigger(calendar.detroit_lions, calendar.detroit_tigers)
def update_card() -> None:
    next_game = get_next_game()
    away_team, home_team = parse_teams(next_game.title)

    card.update(
        top_row=next_game.title,
        middle_row=readable_relative_date(next_game.start),
        bottom_row=next_game.start.strftime("%-I:%M %p"),
        left_icon_path=f"/local/mlb_logos/{away_team}.svg",
        right_icon_path=f"/local/mlb_logos/{home_team}.svg",
    )


def get_next_game() -> GoogleCalendar.Event:
    tigers = calendar.detroit_tigers.next_event
    lions = calendar.detroit_lions.next_event
    next_game: GoogleCalendar.Event = lions if lions.start <= tigers.start else tigers
    return next_game


def parse_teams(message: str) -> tuple[str, str]:
    away_team, home_team = message.split(" @ ")
    return away_team, home_team
