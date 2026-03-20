from dataclasses import dataclass
from enum import StrEnum

import requests

from maestro.utils import log
from scripts.config.secrets import BALLDONTLIE_API_KEY

BASE_URL = "https://api.balldontlie.io/mlb/v1"

DETROIT_TIGERS_TEAM_ID = 10


class InningHalf(StrEnum):
    TOP = "Top"
    BOTTOM = "Bot"


@dataclass
class LiveGameData:
    """Live game state from the balldontlie MLB API"""

    away_runs: int
    home_runs: int
    status: str
    period: int
    inning_half: InningHalf


def get_live_game(team_id: int, game_date: str) -> LiveGameData | None:
    """Fetch live game data for a team on a given date (YYYY-MM-DD). Returns None on failure."""
    url = f"{BASE_URL}/games"
    headers = {"Authorization": BALLDONTLIE_API_KEY}
    params: dict[str, str | int] = {"team_ids[]": team_id, "dates[]": game_date}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception:
        log.exception("Failed to fetch game data from balldontlie", team_id=team_id, date=game_date)
        return None

    games = data.get("data", [])
    if not games:
        return None

    game = games[0]

    away_innings = game.get("away_team_data", {}).get("inning_scores", [])
    home_innings = game.get("home_team_data", {}).get("inning_scores", [])
    period: int = game.get("period", 0)

    if len(away_innings) < period:
        inning_half = InningHalf.TOP
    elif len(home_innings) < period:
        inning_half = InningHalf.BOTTOM
    else:
        # Inning complete, heading to top of next
        inning_half = InningHalf.TOP
        period += 1

    return LiveGameData(
        away_runs=game.get("away_team_data", {}).get("runs", 0),
        home_runs=game.get("home_team_data", {}).get("runs", 0),
        status=game.get("status", ""),
        period=period,
        inning_half=inning_half,
    )
