import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

import requests
from fastapi import HTTPException

from models.schemas import (
    GameSummary,
    HighlightResponse,
    LabeledStat,
    RecentGame,
    RecentGameLeader,
    RecentGamesResponse,
    RecentGameTeam,
    SearchSuggestion,
    StatLine,
    TeamColors,
)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
ROSTER_CACHE_SECONDS = 60 * 60
_roster_cache: dict[str, Any] = {"loaded_at": 0.0, "players": []}


def _get_json(url: str, params: dict[str, Any] | None = None) -> dict:
    try:
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"NFL data temporarily unavailable: {str(e)}")


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _score(query: str, candidate: str) -> float:
    q = _normalize(query)
    c = _normalize(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if c.startswith(q):
        return 0.96
    if q in c:
        return 0.9
    return SequenceMatcher(None, q, c).ratio()


def _hex(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    clean = value.strip().lstrip("#")
    if len(clean) != 6:
        return fallback
    return f"#{clean.upper()}"


def _team_colors(team: dict) -> TeamColors:
    return TeamColors(
        primary=_hex(team.get("color"), "#FF6B35"),
        secondary=_hex(team.get("alternateColor"), "#FFFFFF"),
    )


def _team_logo(team: dict) -> str:
    logos = team.get("logos") or []
    if logos and isinstance(logos[0], dict):
        return logos[0].get("href", "")
    return team.get("logo", "")


def _teams() -> list[dict]:
    data = _get_json(f"{ESPN_BASE}/teams")
    return [item["team"] for item in data["sports"][0]["leagues"][0]["teams"]]


def _headshot_url(athlete: dict) -> str:
    headshot = athlete.get("headshot")
    if isinstance(headshot, dict):
        return headshot.get("href", "")
    if isinstance(headshot, str):
        return headshot
    player_id = athlete.get("id")
    if player_id:
        return f"https://a.espncdn.com/i/headshots/nfl/players/full/{player_id}.png"
    return ""


def _experience_label(athlete: dict) -> str:
    years = (athlete.get("experience") or {}).get("years")
    if years is None:
        return "-"
    if int(years or 0) == 0:
        return "Rookie"
    return f"{years} yrs"


def _roster_for_team(team: dict) -> list[dict]:
    team_id = team.get("id")
    if not team_id:
        return []
    try:
        data = _get_json(f"{ESPN_BASE}/teams/{team_id}/roster")
    except HTTPException:
        return []

    players: list[dict] = []
    for group in data.get("athletes", []) or []:
        for athlete in group.get("items", []) or []:
            name = athlete.get("displayName") or athlete.get("fullName")
            player_id = athlete.get("id")
            if not name or not player_id:
                continue
            position = athlete.get("position") or {}
            status = athlete.get("status") or {}
            college = athlete.get("college") or {}
            players.append({
                "id": int(player_id),
                "displayName": name,
                "fullName": athlete.get("fullName") or name,
                "team_name": team.get("displayName", ""),
                "team_abbrev": team.get("abbreviation", ""),
                "team_logo": _team_logo(team),
                "team_colors": _team_colors(team),
                "position": position.get("abbreviation") or position.get("displayName") or "NFL",
                "position_name": position.get("displayName") or position.get("abbreviation") or "NFL player",
                "jersey": athlete.get("jersey") or "-",
                "status": status.get("name") or status.get("type") or "Roster",
                "experience": _experience_label(athlete),
                "college": college.get("shortName") or college.get("name") or "-",
                "headshot_url": _headshot_url(athlete),
            })
    return players


def _roster_players() -> list[dict]:
    now = time.time()
    if now - float(_roster_cache["loaded_at"]) < ROSTER_CACHE_SECONDS:
        return list(_roster_cache["players"])

    teams = _teams()
    players: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_roster_for_team, team) for team in teams]
        for future in as_completed(futures):
            players.extend(future.result())

    players.sort(key=lambda player: (player["team_abbrev"], player["displayName"]))
    _roster_cache["loaded_at"] = now
    _roster_cache["players"] = players
    return list(players)


def _recent_events(limit: int = 4) -> list[dict]:
    # Prefer the latest postseason stages first, then regular-season Week 18.
    candidates = [
        {"seasontype": 3, "week": 5, "limit": 20},
        {"seasontype": 3, "week": 3, "limit": 20},
        {"seasontype": 3, "week": 2, "limit": 20},
        {"seasontype": 2, "week": 18, "limit": 20},
    ]
    events: list[dict] = []
    seen: set[str] = set()
    for params in candidates:
        data = _get_json(f"{ESPN_BASE}/scoreboard", params=params)
        for event in data.get("events", []):
            event_id = str(event.get("id", ""))
            if event_id and event_id not in seen:
                events.append(event)
                seen.add(event_id)
    events.sort(key=lambda event: event.get("date", ""), reverse=True)
    return events[:limit]


def _leader_from_espn(raw: dict, fallback_team: str = "", category: str = "") -> RecentGameLeader:
    athlete = raw.get("athlete", {})
    player_id = int(athlete.get("id", 0) or 0)
    return RecentGameLeader(
        name=athlete.get("displayName") or athlete.get("fullName") or "Team leader",
        player_id=player_id,
        team_abbrev=fallback_team,
        points=int(raw.get("value", 0) or 0),
        rebounds=0,
        assists=0,
        headshot_url=athlete.get("headshot") or "",
        category=category,
        display_value=raw.get("displayValue", ""),
    )


def _leaders(event: dict) -> list[RecentGameLeader]:
    leaders: list[RecentGameLeader] = []
    for group in event.get("competitions", [{}])[0].get("leaders", []) or []:
        metric = group.get("shortDisplayName") or group.get("displayName") or "Leader"
        raw_leaders = group.get("leaders", []) or []
        if raw_leaders:
            leader = _leader_from_espn(raw_leaders[0], category=metric)
            leaders.append(leader)
    return leaders[:3]


def _recent_player_candidates(query: str, limit: int = 6) -> list[tuple[float, RecentGameLeader, str]]:
    candidates: list[tuple[float, RecentGameLeader, str]] = []
    for event in _recent_events(limit=8):
        for group in event.get("competitions", [{}])[0].get("leaders", []) or []:
            metric = group.get("shortDisplayName") or group.get("displayName") or "Leader"
            for raw in group.get("leaders", [])[:2]:
                leader = _leader_from_espn(raw, category=metric)
                candidate_score = _score(query, leader.name)
                if candidate_score >= 0.55:
                    candidates.append((candidate_score, leader, metric))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[:limit]


def _roster_player_candidates(query: str, limit: int = 6) -> list[tuple[float, dict]]:
    candidates: list[tuple[float, dict]] = []
    for player in _roster_players():
        aliases = [
            player["displayName"],
            player["fullName"],
            f"{player['displayName']} {player['team_abbrev']}",
            f"{player['team_abbrev']} {player['displayName']}",
        ]
        candidate_score = max(_score(query, alias) for alias in aliases if alias)
        if candidate_score >= 0.55:
            candidates.append((candidate_score, player))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[:limit]


def suggest_search(query: str, limit: int = 6) -> list[SearchSuggestion]:
    suggestions: list[tuple[float, SearchSuggestion]] = []
    for candidate_score, player in _roster_player_candidates(query, limit):
        subtitle = f"{player['team_abbrev']} · {player['position_name']}"
        suggestions.append((
            candidate_score,
            SearchSuggestion(value=player["displayName"], type="player", subtitle=subtitle),
        ))
    for team in _teams():
        aliases = [team.get("displayName", ""), team.get("name", ""), team.get("location", ""), team.get("abbreviation", "")]
        candidate_score = max(_score(query, alias) for alias in aliases if alias)
        if candidate_score >= 0.55:
            suggestions.append((
                candidate_score,
                SearchSuggestion(
                    value=team["displayName"],
                    type="team",
                    subtitle=f"NFL team · {team['abbreviation']}",
                ),
            ))
    for candidate_score, leader, metric in _recent_player_candidates(query, limit):
        suggestions.append((
            candidate_score,
            SearchSuggestion(value=leader.name, type="player", subtitle=f"NFL {metric} leader"),
        ))
    unique: dict[str, tuple[float, SearchSuggestion]] = {}
    for candidate_score, suggestion in suggestions:
        current = unique.get(suggestion.value)
        if current is None or candidate_score > current[0]:
            unique[suggestion.value] = (candidate_score, suggestion)
    return [suggestion for _, suggestion in sorted(unique.values(), key=lambda item: item[0], reverse=True)[:limit]]


def _empty_stat_line() -> StatLine:
    return StatLine(
        points=0,
        rebounds=0,
        assists=0,
        steals=0,
        blocks=0,
        turnovers=0,
        minutes="0",
        fg_made=0,
        fg_attempted=0,
        fg_pct=0,
        fg3_made=0,
        fg3_attempted=0,
        fg3_pct=0,
        ft_made=0,
        ft_attempted=0,
        ft_pct=0,
        plus_minus=0,
    )


def _competitors(event: dict) -> tuple[dict, dict]:
    competitors = event["competitions"][0]["competitors"]
    home = next(item for item in competitors if item.get("homeAway") == "home")
    away = next(item for item in competitors if item.get("homeAway") == "away")
    return home, away


def _team_from_competitor(item: dict) -> RecentGameTeam:
    team = item["team"]
    return RecentGameTeam(
        name=team["displayName"],
        abbreviation=team["abbreviation"],
        score=int(item.get("score", 0) or 0),
        record=(item.get("records") or [{}])[0].get("summary", ""),
        colors=_team_colors(team),
    )


def _record_wins(record: str) -> int | None:
    match = re.match(r"^(\d+)-", record or "")
    return int(match.group(1)) if match else None


def _nfl_underdog_note(home: RecentGameTeam, away: RecentGameTeam) -> str | None:
    if home.score == away.score:
        return None
    leader = home if home.score > away.score else away
    opponent = away if leader == home else home
    leader_wins = _record_wins(leader.record)
    opponent_wins = _record_wins(opponent.record)
    if leader_wins is not None and opponent_wins is not None and leader_wins < opponent_wins:
        return f"{leader.abbreviation} is the worse-record side ({leader.record}) leading {opponent.abbreviation} ({opponent.record})."
    return None


def _team_profile_response(team: dict) -> HighlightResponse:
    colors = _team_colors(team)
    abbreviation = team.get("abbreviation", "")
    name = team.get("displayName", "NFL team")
    return HighlightResponse(
        sport="nfl",
        result_type="team",
        game_summary=GameSummary(
            player_or_team=name,
            opponent="NFL",
            game_date="Current roster",
            result=f"{team.get('location', '')} {team.get('name', '')}".strip(),
            season="NFL 2025",
        ),
        key_highlights=[
            f"{name} is available in the football search index.",
            "Open a latest-game card for recent score context, leaders, and underdog watch.",
            "Search any current roster player to jump straight to their team profile.",
        ],
        stat_line=_empty_stat_line(),
        stat_items=[
            LabeledStat(label="TEAM", value=abbreviation or "-"),
            LabeledStat(label="CITY", value=team.get("location", "-")),
            LabeledStat(label="NAME", value=team.get("name", "-")),
            LabeledStat(label="TYPE", value="NFL team"),
        ],
        impact_analysis=f"{name} can be searched directly from the American Football tab, even when it is not one of the latest games shown on the home screen.",
        highlight_grade="Roster",
        grade_score=72,
        team_abbrev=abbreviation,
        team_colors=colors,
        headshot_url=_team_logo(team),
    )


def _player_profile_response(player: dict) -> HighlightResponse:
    team_name = player["team_name"]
    jersey = f"#{player['jersey']}" if player["jersey"] != "-" else "No jersey listed"
    role = f"{player['position_name']} · {player['team_abbrev']}"
    return HighlightResponse(
        sport="nfl",
        result_type="player",
        game_summary=GameSummary(
            player_or_team=player["displayName"],
            opponent=player["team_abbrev"],
            game_date="Current roster",
            result=f"{team_name} · {jersey} · {player['position']}",
            season="NFL 2025",
        ),
        key_highlights=[
            f"{player['displayName']} is listed on the {team_name} roster.",
            f"Position: {player['position_name']} ({player['position']}).",
            f"Status: {player['status']} · Experience: {player['experience']}.",
        ],
        stat_line=_empty_stat_line(),
        stat_items=[
            LabeledStat(label="TEAM", value=player["team_abbrev"]),
            LabeledStat(label="POS", value=player["position"]),
            LabeledStat(label="NO", value=str(player["jersey"])),
            LabeledStat(label="EXP", value=player["experience"]),
            LabeledStat(label="COL", value=player["college"]),
            LabeledStat(label="ROLE", value=role),
        ],
        impact_analysis=f"{player['displayName']} is searchable from the full NFL roster index. Latest-game leader cards still appear when ESPN has fresh game-leader data for that player.",
        highlight_grade="Roster",
        grade_score=70,
        team_abbrev=player["team_abbrev"],
        team_colors=player["team_colors"],
        player_id=player["id"],
        headshot_url=player["headshot_url"],
    )


def get_recent_games(limit: int = 4) -> RecentGamesResponse:
    games: list[RecentGame] = []
    for event in _recent_events(limit=limit):
        home_raw, away_raw = _competitors(event)
        home = _team_from_competitor(home_raw)
        away = _team_from_competitor(away_raw)
        status = event.get("status", {}).get("type", {}).get("shortDetail") or event.get("status", {}).get("type", {}).get("description", "")
        leaders = _leaders(event)
        top_leader = leaders[0] if leaders else None
        winner = home if home.score >= away.score else away
        underdog_note = _nfl_underdog_note(home, away)
        highlights = [
            f"{status}: {away.abbreviation} {away.score}, {home.abbreviation} {home.score}",
            f"{winner.name} finished with {winner.score} points.",
        ]
        if top_leader:
            highlights.append(f"{top_leader.name} headlined the box score.")
        if underdog_note:
            highlights.append(underdog_note)

        game_date = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).strftime("%b %d, %Y")
        games.append(
            RecentGame(
                game_id=str(event["id"]),
                game_date=game_date,
                status=status,
                label=event.get("season", {}).get("slug", "NFL"),
                series_text=event.get("name", ""),
                matchup=f"{away.abbreviation} @ {home.abbreviation}",
                home_team=home,
                away_team=away,
                leaders=leaders,
                highlights=highlights,
                underdog_note=underdog_note,
            )
        )
    as_of = games[0].game_date if games else datetime.now().strftime("%b %d, %Y")
    return RecentGamesResponse(as_of_date=as_of, games=games)


def search(query: str) -> HighlightResponse:
    suggestions = suggest_search(query, limit=1)
    if not suggestions:
        raise HTTPException(
            status_code=404,
            detail=f"No NFL team or recent leader found matching '{query}'. Try a team like 'Seahawks' or a recent leader.",
        )
    best = suggestions[0]
    recent = get_recent_games(limit=8).games

    if best.type == "team":
        team_lookup = next(
            (
                team for team in _teams()
                if _normalize(team.get("displayName", "")) == _normalize(best.value)
            ),
            None,
        )
        for game in recent:
            if best.value in (game.home_team.name, game.away_team.name):
                team = game.home_team if best.value == game.home_team.name else game.away_team
                opponent = game.away_team if team == game.home_team else game.home_team
                return HighlightResponse(
                    sport="nfl",
                    result_type="team",
                    game_summary=GameSummary(
                        player_or_team=team.name,
                        opponent=opponent.abbreviation,
                        game_date=game.game_date,
                        result=f"{game.status} - {game.matchup}",
                        season="NFL 2025",
                    ),
                    key_highlights=game.highlights,
                    stat_line=_empty_stat_line(),
                    stat_items=[
                        LabeledStat(label="PTS", value=str(team.score)),
                        LabeledStat(label="OPP", value=str(opponent.score)),
                        LabeledStat(label="REC", value=team.record or "-"),
                        LabeledStat(label="GAME", value=game.status),
                    ],
                    impact_analysis=f"{team.name} was last seen against {opponent.name}. {game.highlights[0]}",
                    highlight_grade="Recap",
                    grade_score=75,
                    team_abbrev=team.abbreviation,
                    team_colors=team.colors,
                )
        if team_lookup:
            return _team_profile_response(team_lookup)

    for game in recent:
        for leader in game.leaders:
            if _normalize(leader.name) == _normalize(best.value):
                return HighlightResponse(
                    sport="nfl",
                    result_type="player",
                    game_summary=GameSummary(
                        player_or_team=leader.name,
                        opponent=game.matchup,
                        game_date=game.game_date,
                        result=game.status,
                        season="NFL 2025",
                    ),
                    key_highlights=game.highlights,
                    stat_line=_empty_stat_line(),
                    stat_items=[
                        LabeledStat(label="ROLE", value=best.subtitle.replace("NFL ", "").replace(" leader", "")),
                        LabeledStat(label="GAME", value=game.status),
                        LabeledStat(label="MATCH", value=game.matchup),
                    ],
                    impact_analysis=f"{leader.name} appeared among the latest NFL game leaders for {game.matchup}.",
                    highlight_grade="Spotlight",
                    grade_score=75,
                    team_abbrev=leader.team_abbrev,
                    player_id=leader.player_id,
                    headshot_url=leader.headshot_url,
                )

    player = next(
        (
            player for player in _roster_players()
            if _normalize(player["displayName"]) == _normalize(best.value)
        ),
        None,
    )
    if player:
        return _player_profile_response(player)

    raise HTTPException(status_code=404, detail=f"No recent NFL result found for '{query}'.")
