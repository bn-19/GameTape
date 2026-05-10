from pydantic import BaseModel
from typing import List, Optional


class TeamColors(BaseModel):
    primary: str
    secondary: str


class GameSummary(BaseModel):
    player_or_team: str
    opponent: str
    game_date: str
    result: str
    season: str


class StatLine(BaseModel):
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    minutes: str
    fg_made: int
    fg_attempted: int
    fg_pct: float
    fg3_made: int
    fg3_attempted: int
    fg3_pct: float
    ft_made: int
    ft_attempted: int
    ft_pct: float
    plus_minus: int


class LabeledStat(BaseModel):
    label: str
    value: str


class HighlightResponse(BaseModel):
    sport: str = "nba"
    result_type: str  # "player" | "team"
    game_summary: GameSummary
    key_highlights: List[str]
    stat_line: StatLine
    stat_items: Optional[List[LabeledStat]] = None
    impact_analysis: str
    highlight_grade: str
    grade_score: float
    team_abbrev: Optional[str] = None
    team_colors: Optional[TeamColors] = None
    player_id: Optional[int] = None
    headshot_url: Optional[str] = None


class ErrorDetail(BaseModel):
    message: str
    suggestions: Optional[List[str]] = None


class SearchSuggestion(BaseModel):
    value: str
    type: str
    subtitle: str


class SuggestionResponse(BaseModel):
    suggestions: List[SearchSuggestion]


class RecentGameTeam(BaseModel):
    name: str
    abbreviation: str
    score: int
    record: str
    colors: TeamColors
    seed: Optional[int] = None


class RecentGameLeader(BaseModel):
    name: str
    player_id: int
    team_abbrev: str
    points: int
    rebounds: int
    assists: int
    headshot_url: str
    category: Optional[str] = None
    display_value: Optional[str] = None


class RecentGame(BaseModel):
    game_id: str
    game_date: str
    status: str
    label: str
    series_text: str
    matchup: str
    home_team: RecentGameTeam
    away_team: RecentGameTeam
    leaders: List[RecentGameLeader]
    highlights: List[str]
    underdog_note: Optional[str] = None


class RecentGamesResponse(BaseModel):
    as_of_date: str
    games: List[RecentGame]
