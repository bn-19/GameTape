import time
import pandas as pd
from fastapi import HTTPException
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, teamgamelog
from requests.exceptions import Timeout, ConnectionError as ReqConnectionError

CURRENT_SEASON = "2024-25"
PREVIOUS_SEASON = "2023-24"


def _fetch_with_retry(endpoint_cls, **kwargs) -> pd.DataFrame:
    last_exc = None
    for attempt in range(3):
        try:
            result = endpoint_cls(**kwargs, timeout=15)
            return result.get_data_frames()[0]
        except (Timeout, ReqConnectionError) as e:
            last_exc = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error fetching stats: {str(e)}")
    raise HTTPException(status_code=503, detail="NBA stats API temporarily unavailable. Try again in a few seconds.")


def resolve_player(query: str) -> dict:
    """Return nba_api player dict or raise HTTPException."""
    matches = players.find_players_by_full_name(query)
    if not matches:
        matches = players.find_players_by_last_name(query)
    if not matches:
        return None
    if len(matches) > 1:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Multiple players match '{query}'. Did you mean one of these?",
                "suggestions": [m["full_name"] for m in matches[:5]],
            },
        )
    return matches[0]


def resolve_team(query: str) -> dict:
    """Return nba_api team dict or None."""
    for finder in [
        lambda q: teams.find_teams_by_nickname(q),
        lambda q: teams.find_teams_by_full_name(q),
        lambda q: teams.find_teams_by_city(q),
        lambda q: [teams.find_team_by_abbreviation(q.upper())] if teams.find_team_by_abbreviation(q.upper()) else [],
    ]:
        result = finder(query)
        if result:
            return result[0]
    return None


def get_player_game(player_id: int, player_name: str) -> tuple[pd.Series, str]:
    """Fetch the most recent game row for a player. Returns (row, season)."""
    for season in [CURRENT_SEASON, PREVIOUS_SEASON]:
        df = _fetch_with_retry(
            playergamelog.PlayerGameLog,
            player_id=player_id,
            season=season,
            season_type_all_star="Regular Season",
        )
        if not df.empty:
            row = df.iloc[0]
            min_val = str(row.get("MIN", "")).strip()
            if min_val in ("0:00", "0", "", "None"):
                raise HTTPException(
                    status_code=404,
                    detail=f"{player_name} did not play in their most recent game ({row.get('GAME_DATE', '')}).",
                )
            return row, season
    raise HTTPException(
        status_code=404,
        detail=f"{player_name} has no recorded games in {CURRENT_SEASON} or {PREVIOUS_SEASON}.",
    )


def get_team_game(team_id: int, team_name: str) -> tuple[pd.Series, str]:
    """Fetch the most recent game row for a team. Returns (row, season)."""
    for season in [CURRENT_SEASON, PREVIOUS_SEASON]:
        df = _fetch_with_retry(
            teamgamelog.TeamGameLog,
            team_id=team_id,
            season=season,
        )
        if not df.empty:
            return df.iloc[0], season
    raise HTTPException(
        status_code=404,
        detail=f"{team_name} has no recorded games in {CURRENT_SEASON} or {PREVIOUS_SEASON}.",
    )
