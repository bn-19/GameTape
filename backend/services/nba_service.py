import re
import time
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import HTTPException
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, teamgamelog, scoreboardv3
from requests.exceptions import Timeout, ConnectionError as ReqConnectionError

from models.schemas import (
    RecentGame,
    RecentGameLeader,
    RecentGamesResponse,
    RecentGameTeam,
    SearchSuggestion,
    TeamColors,
)
from services.team_colors import get_team_colors

CURRENT_SEASON = "2025-26"
PREVIOUS_SEASON = "2024-25"
SEASON_TYPES = ("Playoffs", "Regular Season")


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


def _endpoint_with_retry(endpoint_cls, **kwargs):
    last_exc = None
    for attempt in range(3):
        try:
            return endpoint_cls(**kwargs, timeout=15)
        except (Timeout, ReqConnectionError) as e:
            last_exc = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error fetching stats: {str(e)}")
    raise HTTPException(status_code=503, detail="NBA stats API temporarily unavailable. Try again in a few seconds.")


def _normalize_query(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _score_candidate(query: str, candidate: str) -> float:
    q = _normalize_query(query)
    c = _normalize_query(candidate)
    if not q or not c:
        return 0.0
    if c == q:
        return 1.0
    if c.startswith(q):
        return 0.96
    if q in c:
        return 0.9
    return SequenceMatcher(None, q, c).ratio()


def _player_candidates(query: str, limit: int = 6) -> list[tuple[float, dict]]:
    ranked = [
        (_score_candidate(query, player["full_name"]), player)
        for player in players.get_active_players()
    ]
    return sorted((item for item in ranked if item[0] >= 0.55), key=lambda item: item[0], reverse=True)[:limit]


def _team_candidates(query: str, limit: int = 6) -> list[tuple[float, dict]]:
    ranked = []
    for team in teams.get_teams():
        aliases = [
            team["full_name"],
            team["nickname"],
            team["city"],
            team["abbreviation"],
        ]
        score = max(_score_candidate(query, alias) for alias in aliases if alias)
        if score >= 0.55:
            ranked.append((score, team))
    return sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]


def _exact_team_match(query: str) -> dict | None:
    normalized_query = _normalize_query(query)
    for team in teams.get_teams():
        aliases = [
            team["full_name"],
            team["nickname"],
            team["city"],
            team["abbreviation"],
        ]
        if normalized_query in {_normalize_query(alias) for alias in aliases if alias}:
            return team
    return None


def suggest_search(query: str, limit: int = 6) -> list[SearchSuggestion]:
    suggestions: list[tuple[float, SearchSuggestion]] = []
    for score, player in _player_candidates(query, limit):
        suggestions.append((
            score,
            SearchSuggestion(
                value=player["full_name"],
                type="player",
                subtitle="Player",
            ),
        ))
    for score, team in _team_candidates(query, limit):
        suggestions.append((
            score,
            SearchSuggestion(
                value=team["full_name"],
                type="team",
                subtitle=f"{team['city']} {team['nickname']} · {team['abbreviation']}",
            ),
        ))
    unique: dict[str, tuple[float, SearchSuggestion]] = {}
    for score, suggestion in suggestions:
        current = unique.get(suggestion.value)
        if current is None or score > current[0]:
            unique[suggestion.value] = (score, suggestion)
    return [suggestion for _, suggestion in sorted(unique.values(), key=lambda item: item[0], reverse=True)[:limit]]


def resolve_player(query: str) -> dict:
    """Return nba_api player dict or raise HTTPException."""
    matches = players.find_players_by_full_name(query)
    if not matches:
        matches = players.find_players_by_last_name(query)
    if not matches:
        fuzzy_matches = _player_candidates(query)
        if not fuzzy_matches:
            return None
        top_score, top_player = fuzzy_matches[0]
        second_score = fuzzy_matches[1][0] if len(fuzzy_matches) > 1 else 0.0
        if top_score >= 0.72 and top_score - second_score >= 0.04:
            return top_player
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"No exact player match for '{query}'. Did you mean one of these?",
                "suggestions": [player["full_name"] for _, player in fuzzy_matches[:5]],
            },
        )
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
    exact = _exact_team_match(query)
    if exact:
        return exact

    for finder in [
        lambda q: teams.find_teams_by_nickname(q),
        lambda q: teams.find_teams_by_full_name(q),
        lambda q: teams.find_teams_by_city(q),
        lambda q: [teams.find_team_by_abbreviation(q.upper())] if teams.find_team_by_abbreviation(q.upper()) else [],
    ]:
        result = finder(query)
        if result:
            return result[0]
    fuzzy_matches = _team_candidates(query)
    if fuzzy_matches:
        top_score, top_team = fuzzy_matches[0]
        second_score = fuzzy_matches[1][0] if len(fuzzy_matches) > 1 else 0.0
        if top_score >= 0.72 and top_score - second_score >= 0.04:
            return top_team
    return None


def get_player_game(player_id: int, player_name: str) -> tuple[pd.Series, str]:
    """Fetch the most recent game row for a player. Returns (row, season)."""
    for season in [CURRENT_SEASON, PREVIOUS_SEASON]:
        for season_type in SEASON_TYPES:
            df = _fetch_with_retry(
                playergamelog.PlayerGameLog,
                player_id=player_id,
                season=season,
                season_type_all_star=season_type,
            )
            if not df.empty:
                row = df.iloc[0]
                min_val = str(row.get("MIN", "")).strip()
                if min_val in ("0:00", "0", "", "None"):
                    raise HTTPException(
                        status_code=404,
                        detail=f"{player_name} did not play in their most recent game ({row.get('GAME_DATE', '')}).",
                    )
                return row, f"{season} {season_type}"
    raise HTTPException(
        status_code=404,
        detail=f"{player_name} has no recorded games in {CURRENT_SEASON} or {PREVIOUS_SEASON}.",
    )


def get_team_game(team_id: int, team_name: str) -> tuple[pd.Series, str]:
    """Fetch the most recent game row for a team. Returns (row, season)."""
    for season in [CURRENT_SEASON, PREVIOUS_SEASON]:
        for season_type in SEASON_TYPES:
            df = _fetch_with_retry(
                teamgamelog.TeamGameLog,
                team_id=team_id,
                season=season,
                season_type_all_star=season_type,
            )
            if not df.empty:
                return df.iloc[0], f"{season} {season_type}"
    raise HTTPException(
        status_code=404,
        detail=f"{team_name} has no recorded games in {CURRENT_SEASON} or {PREVIOUS_SEASON}.",
    )


def _team_colors(abbrev: str) -> TeamColors:
    primary, secondary = get_team_colors(abbrev)
    return TeamColors(primary=primary, secondary=secondary)


def _line_team(row: pd.Series) -> RecentGameTeam:
    abbrev = str(row.get("teamTricode", "")).upper()
    raw_seed = row.get("seed", None)
    seed = int(raw_seed) if raw_seed not in (None, "", "None") else None
    return RecentGameTeam(
        name=f"{row.get('teamCity', '')} {row.get('teamName', '')}".strip(),
        abbreviation=abbrev,
        score=int(row.get("score", 0) or 0),
        record=f"{int(row.get('wins', 0) or 0)}-{int(row.get('losses', 0) or 0)}",
        colors=_team_colors(abbrev),
        seed=seed,
    )


def _leader(row: pd.Series) -> RecentGameLeader:
    player_id = int(row.get("personId", 0) or 0)
    return RecentGameLeader(
        name=str(row.get("name", "")),
        player_id=player_id,
        team_abbrev=str(row.get("teamTricode", "")).upper(),
        points=int(row.get("points", 0) or 0),
        rebounds=int(row.get("rebounds", 0) or 0),
        assists=int(row.get("assists", 0) or 0),
        headshot_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
    )


def _nba_underdog_note(home: RecentGameTeam, away: RecentGameTeam, status_id: int) -> str | None:
    if home.seed is None or away.seed is None or home.seed == away.seed:
        return None
    if home.score == away.score:
        return None
    leader = home if home.score > away.score else away
    opponent = away if leader == home else home
    if leader.seed > opponent.seed:
        action = "upset watch" if status_id != 3 else "upset hit"
        return f"{leader.abbreviation} is the lower seed ({leader.seed}) over {opponent.abbreviation} ({opponent.seed}) - {action}."
    return None


def get_recent_games(limit: int = 4, lookback_days: int = 10) -> RecentGamesResponse:
    """Return recent live/final games, walking back from the local NBA date."""
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    games: list[RecentGame] = []

    for offset in range(lookback_days):
        game_date = today - timedelta(days=offset)
        board = _endpoint_with_retry(scoreboardv3.ScoreboardV3, game_date=game_date.isoformat())
        headers = board.game_header.get_data_frame()
        lines = board.line_score.get_data_frame()
        leaders = board.game_leaders.get_data_frame()

        if headers.empty:
            continue

        for _, game in headers.iterrows():
            status_id = int(game.get("gameStatus", 0) or 0)
            if status_id == 1:
                continue

            game_id = str(game.get("gameId", ""))
            code = str(game.get("gameCode", ""))
            code_match = re.search(r"/([A-Z]{3})([A-Z]{3})$", code)
            away_abbrev = code_match.group(1) if code_match else ""
            home_abbrev = code_match.group(2) if code_match else ""

            game_lines = lines[lines["gameId"].astype(str) == game_id]
            if game_lines.empty:
                continue

            home_rows = game_lines[game_lines["teamTricode"].astype(str).str.upper() == home_abbrev]
            away_rows = game_lines[game_lines["teamTricode"].astype(str).str.upper() == away_abbrev]
            if home_rows.empty or away_rows.empty:
                home_row = game_lines.iloc[0]
                away_row = game_lines.iloc[1] if len(game_lines) > 1 else game_lines.iloc[0]
            else:
                home_row = home_rows.iloc[0]
                away_row = away_rows.iloc[0]

            home_team = _line_team(home_row)
            away_team = _line_team(away_row)
            game_leaders = sorted(
                [_leader(row) for _, row in leaders[leaders["gameId"].astype(str) == game_id].iterrows()],
                key=lambda leader: leader.points,
                reverse=True,
            )

            status_text = str(game.get("gameStatusText", "")).strip()
            label = str(game.get("gameLabel", "")) or str(game.get("seriesGameNumber", ""))
            series_text = str(game.get("seriesText", ""))
            winner = home_team if home_team.score >= away_team.score else away_team
            top_leader = max(game_leaders, key=lambda leader: leader.points, default=None)
            leader_phrase = "posted" if status_id == 3 else "is showing"
            highlights = [
                f"{status_text}: {away_team.abbreviation} {away_team.score}, {home_team.abbreviation} {home_team.score}",
                f"{winner.name} {leader_phrase} {winner.score} team points.",
            ]
            if top_leader:
                highlights.append(
                    f"{top_leader.name} paced the stars with {top_leader.points} pts, "
                    f"{top_leader.rebounds} reb, {top_leader.assists} ast."
                )
            if series_text:
                highlights.append(series_text)
            underdog_note = _nba_underdog_note(home_team, away_team, status_id)
            if underdog_note:
                highlights.append(underdog_note)

            games.append(
                RecentGame(
                    game_id=game_id,
                    game_date=game_date.strftime("%b %d, %Y"),
                    status=status_text,
                    label=label,
                    series_text=series_text,
                    matchup=f"{away_team.abbreviation} @ {home_team.abbreviation}",
                    home_team=home_team,
                    away_team=away_team,
                    leaders=game_leaders,
                    highlights=highlights,
                    underdog_note=underdog_note,
                )
            )

            if len(games) >= limit:
                return RecentGamesResponse(as_of_date=today.strftime("%b %d, %Y"), games=games)

    return RecentGamesResponse(as_of_date=today.strftime("%b %d, %Y"), games=games)
