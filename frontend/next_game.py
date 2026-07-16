from maestro.integrations import StateManager
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
from scripts.common.balldontlie import (
    DETROIT_TIGERS_TEAM_ID,
    InningHalf,
    LiveGameData,
    get_live_game,
)
from scripts.frontend.common.icons import Icon

card = maestro.next_game_card

STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
STATUS_FINAL = "STATUS_FINAL"

NBSP = "\u00a0"
ARROW_PAD = NBSP * 2
TRAIL_PAD = NBSP * 4


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
    StateManager().initialize_hass_entity(
        entity_id=card.id,
        state=local_now().isoformat(),
        attributes=attributes,
        restore_cached=True,
    )
    card.update(icon=attributes["icon"])


@cron_trigger("*/2 * * * *")
@state_change_trigger(calendar.detroit_tigers)
def update_card() -> None:
    next_game = calendar.detroit_tigers.next_event
    away_team, home_team = parse_teams(next_game.title)
    game_active = next_game.start <= local_now()

    middle_row = readable_relative_date(next_game.start).capitalize()
    bottom_row = next_game.start.strftime("%-I:%M %p")

    if game_active:
        game = get_live_game(DETROIT_TIGERS_TEAM_ID, next_game.start.strftime("%Y-%m-%d"))
        if game is not None:
            middle_row, bottom_row = format_live_game(game)

    card.update(
        top_row=next_game.title,
        middle_row=middle_row,
        bottom_row=bottom_row,
        left_icon_path=f"/local/mlb_logos/{away_team}.png",
        right_icon_path=f"/local/mlb_logos/{home_team}.png",
        active=game_active,
    )


def format_live_game(game: LiveGameData) -> tuple[str, str]:
    """Format live game data into (middle_row, bottom_row) for the card"""
    score = f"{game.away_runs} - {game.home_runs}"

    if game.status == STATUS_FINAL:
        return "Final", score

    if game.status == STATUS_IN_PROGRESS:
        if game.inning_half == InningHalf.TOP:
            return f"◀{ARROW_PAD}{game.inning_half} {game.period}{TRAIL_PAD}", score
        return f"{TRAIL_PAD}{game.inning_half} {game.period}{ARROW_PAD}▶", score

    return "Live", score


def parse_teams(message: str) -> tuple[str, str]:
    away_team, home_team = message.split(" @ ")
    away_team = away_team.split(" (")[0].strip()
    home_team = home_team.split(" (")[0].strip()
    return away_team, home_team
