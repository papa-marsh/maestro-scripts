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

    period: int = game.get("period", 0)
    scoring_summary: list[dict] = game.get("scoring_summary", [])

    # Scoring summary is the most reliable source for inning half and score
    if scoring_summary:
        last_play = scoring_summary[-1]
        away_runs: int = last_play.get("away_score", 0)
        home_runs: int = last_play.get("home_score", 0)
        inning_half = InningHalf.BOTTOM if last_play.get("inning") == "bottom" else InningHalf.TOP
    else:
        away_runs = game.get("away_team_data", {}).get("runs", 0)
        home_runs = game.get("home_team_data", {}).get("runs", 0)
        away_innings = game.get("away_team_data", {}).get("inning_scores", [])
        home_innings = game.get("home_team_data", {}).get("inning_scores", [])
        inning_half = InningHalf.BOTTOM if len(away_innings) > len(home_innings) else InningHalf.TOP

    return LiveGameData(
        away_runs=away_runs,
        home_runs=home_runs,
        status=game.get("status", ""),
        period=period,
        inning_half=inning_half,
    )
