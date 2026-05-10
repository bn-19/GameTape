# NBA team colors: abbreviation → (primary, secondary)
TEAM_COLORS: dict[str, tuple[str, str]] = {
    "ATL": ("#E03A3E", "#C1D32F"),   # Hawks
    "BOS": ("#007A33", "#BA9653"),   # Celtics
    "BKN": ("#FFFFFF", "#000000"),   # Nets
    "CHA": ("#1D1160", "#00788C"),   # Hornets
    "CHI": ("#CE1141", "#000000"),   # Bulls
    "CLE": ("#860038", "#FDBB30"),   # Cavaliers
    "DAL": ("#00538C", "#B8C4CA"),   # Mavericks
    "DEN": ("#0E2240", "#FEC524"),   # Nuggets
    "DET": ("#C8102E", "#1D42BA"),   # Pistons
    "GSW": ("#1D428A", "#FFC72C"),   # Warriors
    "HOU": ("#CE1141", "#000000"),   # Rockets
    "IND": ("#002D62", "#FDBB30"),   # Pacers
    "LAC": ("#C8102E", "#1D428A"),   # Clippers
    "LAL": ("#552583", "#FDB927"),   # Lakers
    "MEM": ("#5D76A9", "#12173F"),   # Grizzlies
    "MIA": ("#98002E", "#F9A01B"),   # Heat
    "MIL": ("#00471B", "#EEE1C6"),   # Bucks
    "MIN": ("#0C2340", "#236192"),   # Timberwolves
    "NOP": ("#0C2340", "#C8102E"),   # Pelicans
    "NYK": ("#006BB6", "#F58426"),   # Knicks
    "OKC": ("#007AC1", "#EF3B24"),   # Thunder
    "ORL": ("#0077C0", "#C4CED4"),   # Magic
    "PHI": ("#006BB6", "#ED174C"),   # 76ers
    "PHX": ("#1D1160", "#E56020"),   # Suns
    "POR": ("#E03A3E", "#000000"),   # Trail Blazers
    "SAC": ("#5A2D81", "#63727A"),   # Kings
    "SAS": ("#C4CED4", "#000000"),   # Spurs
    "TOR": ("#CE1141", "#000000"),   # Raptors
    "UTA": ("#002B5C", "#00471B"),   # Jazz
    "WAS": ("#002B5C", "#E31837"),   # Wizards
}

DEFAULT_COLORS = ("#FF6B35", "#FFFFFF")


def get_team_colors(abbrev: str) -> tuple[str, str]:
    if not abbrev:
        return DEFAULT_COLORS
    # Extract abbreviation from MATCHUP strings like "GSW vs. LAL" or "GSW @ LAL"
    clean = abbrev.strip().upper()
    return TEAM_COLORS.get(clean, DEFAULT_COLORS)


def extract_team_abbrev_from_matchup(matchup: str) -> str:
    """Return the home team's abbreviation from a matchup string."""
    # matchup format: "GSW vs. LAL" (home) or "GSW @ LAL" (away)
    parts = matchup.upper().split()
    if parts:
        return parts[0]
    return ""
