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


class HighlightResponse(BaseModel):
    result_type: str  # "player" | "team"
    game_summary: GameSummary
    key_highlights: List[str]
    stat_line: StatLine
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
