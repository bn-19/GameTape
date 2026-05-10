from fastapi import APIRouter, HTTPException, Query
from models.schemas import HighlightResponse, RecentGamesResponse, SuggestionResponse
from services import nba_service, highlight_service, nfl_service

router = APIRouter()


@router.get("/suggest", response_model=SuggestionResponse)
def suggest(
    q: str = Query(..., min_length=1, description="Partial player or team name"),
    sport: str = Query("nba", pattern="^(nba|nfl)$"),
):
    service = nfl_service if sport == "nfl" else nba_service
    return SuggestionResponse(suggestions=service.suggest_search(q))


@router.get("/recent-games", response_model=RecentGamesResponse)
def recent_games(sport: str = Query("nba", pattern="^(nba|nfl)$")):
    service = nfl_service if sport == "nfl" else nba_service
    return service.get_recent_games()


@router.get("/search", response_model=HighlightResponse)
def search(
    q: str = Query(..., min_length=1, description="Player name or team name"),
    sport: str = Query("nba", pattern="^(nba|nfl)$"),
):
    if sport == "nfl":
        return nfl_service.search(q)

    # Team names should not be blocked by fuzzy player matches like
    # "San Antonio Spurs" -> "Antonio Reeves".
    team = nba_service.resolve_team(q)
    if team:
        row, season = nba_service.get_team_game(team["id"], team["full_name"])
        return highlight_service.build_team_highlight(
            row=row,
            season=season,
            team_name=team["full_name"],
            team_abbrev=team["abbreviation"],
        )

    # Try player after team lookup.
    try:
        player = nba_service.resolve_player(q)
    except HTTPException as e:
        if e.status_code == 422:
            raise  # ambiguous — surface the suggestions
        player = None

    if player:
        row, season = nba_service.get_player_game(player["id"], player["full_name"])
        # Derive team abbreviation from the matchup string (first token is the player's team)
        matchup = str(row.get("MATCHUP", ""))
        team_abbrev = matchup.split()[0].upper() if matchup else ""
        return highlight_service.build_player_highlight(
            row=row,
            season=season,
            player_name=player["full_name"],
            player_id=player["id"],
            team_abbrev=team_abbrev,
        )

    raise HTTPException(
        status_code=404,
        detail=f"No player or team found matching '{q}'. Try a full name like 'Stephen Curry' or 'Lakers'.",
    )
