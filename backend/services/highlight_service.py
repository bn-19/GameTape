import pandas as pd
from models.schemas import GameSummary, StatLine, HighlightResponse, TeamColors
from services.team_colors import get_team_colors, extract_team_abbrev_from_matchup


def _parse_result(wl: str, matchup: str) -> str:
    """Build a result string like 'W 118-105'."""
    return f"{wl} (via {matchup})" if wl else matchup


def _build_key_highlights(s: dict) -> list[str]:
    h = []
    pts, reb, ast = s["PTS"], s["REB"], s["AST"]
    stl, blk, tov = s["STL"], s["BLK"], s["TOV"]
    fg_pct = s["FG_PCT"]
    fg3m, fg3_pct = s["FG3M"], s["FG3_PCT"]
    pm = s["PLUS_MINUS"]

    if pts >= 40:
        h.append(f"ERUPTED for {pts} POINTS in an all-time performance! 🔥")
    elif pts >= 30:
        h.append(f"Went OFF for {pts} buckets — absolutely cooking")
    elif pts >= 20:
        h.append(f"Dropped {pts} efficient points on the night")
    else:
        h.append(f"Chipped in {pts} points off the bench/rotation")

    if fg_pct >= 0.60:
        h.append(f"Surgical efficiency — {int(fg_pct * 100)}% from the field")
    elif fg3m >= 5:
        h.append(f"Rained down {fg3m} THREES from deep ({int(fg3_pct * 100)}% from three)")
    elif fg3m >= 3 and fg3_pct >= 0.40:
        h.append(f"Dialed in from beyond the arc — {fg3m}/{int(s['FG3A'])} from three")

    if ast >= 10:
        h.append(f"DIME MACHINE — {ast} assists, borderline triple-double territory")
    elif ast >= 7:
        h.append(f"Dished out {ast} dimes, controlling the offense all night")

    if reb >= 15:
        h.append(f"DOMINATED the glass with {reb} boards — a rebounding clinic")
    elif reb >= 10:
        h.append(f"Owned the paint with {reb} rebounds")

    if stl + blk >= 5:
        h.append(f"LOCKDOWN defender — {stl} steals + {blk} blocks = {stl + blk} stocks 🛡️")
    elif stl >= 3:
        h.append(f"Pickpocket artist: {stl} steals on the night")

    if pm >= 20:
        h.append(f"Team was +{pm} with them on the court — a DIFFERENCE MAKER")

    if tov >= 6:
        h.append(f"Coughed up {tov} turnovers — something to clean up")

    return h[:5]


def _build_impact_analysis(s: dict, name: str) -> str:
    pts, reb, ast = s["PTS"], s["REB"], s["AST"]
    stl, blk, tov = s["STL"], s["BLK"], s["TOV"]
    fg_pct = s["FG_PCT"]
    fg3m = s["FG3M"]
    matchup = s["MATCHUP"]
    wl = s.get("WL", "")
    pm = s["PLUS_MINUS"]

    opponent = matchup.replace("vs.", "vs").replace("@", "on the road vs")
    outcome = "dominant victory" if wl == "W" else "tough loss"

    lines = [
        f"{name} delivered {'a complete, all-around effort' if pts + reb + ast > 50 else 'a solid contribution'} "
        f"{opponent}, ending in a {outcome}."
    ]

    if pts >= 30:
        lines.append(
            f"The scoring was ELECTRIC — {pts} points on {int(fg_pct * 100)}% shooting kept the defense on their heels all night."
        )
    elif fg_pct >= 0.55:
        lines.append(f"Efficiency was the story: {int(fg_pct * 100)}% from the field made every possession count.")

    if fg3m >= 4:
        lines.append(f"The long ball was falling — {fg3m} threes stretched the defense and opened the paint.")

    if ast >= 8:
        lines.append(f"The playmaking was elite, with {ast} assists threading the needle for open teammates.")

    if reb >= 10:
        lines.append(f"Controlling the glass with {reb} boards gave the team extra possessions.")

    if stl + blk >= 4:
        lines.append(f"Defense was equally impressive — {stl + blk} combined stocks disrupted the opposing offense.")

    if tov >= 5:
        lines.append(f"The {tov} turnovers were a concern and gave the opponent easy transition opportunities.")

    if pm > 0:
        lines.append(f"The +{pm} plus/minus tells the real story — this team was better when {name.split()[0]} was on the floor.")

    return " ".join(lines)


def _compute_grade(s: dict) -> tuple[str, float]:
    pts = s.get("PTS", 0)
    reb = s.get("REB", 0)
    ast = s.get("AST", 0)
    stl = s.get("STL", 0)
    blk = s.get("BLK", 0)
    tov = s.get("TOV", 0)
    fg3m = s.get("FG3M", 0)
    fg_pct = s.get("FG_PCT", 0.0)
    fg3_pct = s.get("FG3_PCT", 0.0)
    pm = s.get("PLUS_MINUS", 0)

    score = 0.0
    score += min(pts * 1.2, 36)
    score += min(reb * 1.5, 15)
    score += min(ast * 1.5, 12)
    score += (stl + blk) * 2.0

    if fg_pct >= 0.60:
        score += 10
    elif fg_pct >= 0.50:
        score += 6
    elif fg_pct >= 0.40:
        score += 2

    if fg3_pct >= 0.50 and fg3m >= 3:
        score += 8
    elif fg3_pct >= 0.40 and fg3m >= 2:
        score += 4

    score -= tov * 2.0
    score += min(max(pm * 0.3, -5), 10)

    dd = sum([pts >= 10, reb >= 10, ast >= 10, stl >= 10, blk >= 10])
    if dd >= 3:
        score += 15
    elif dd >= 2:
        score += 7

    score = max(0.0, min(score, 100.0))

    grade_map = [
        (93, "A+"), (88, "A"), (82, "A-"),
        (76, "B+"), (70, "B"), (64, "B-"),
        (58, "C+"), (52, "C"), (46, "C-"),
        (40, "D+"), (34, "D"), (28, "D-"),
        (0, "F"),
    ]
    grade = next(g for threshold, g in grade_map if score >= threshold)
    return grade, round(score, 1)


def _row_to_dict(row: pd.Series) -> dict:
    return {
        "PTS": int(row.get("PTS", 0)),
        "REB": int(row.get("REB", 0)),
        "AST": int(row.get("AST", 0)),
        "STL": int(row.get("STL", 0)),
        "BLK": int(row.get("BLK", 0)),
        "TOV": int(row.get("TOV", 0)),
        "MIN": str(row.get("MIN", "0")),
        "FGM": int(row.get("FGM", 0)),
        "FGA": int(row.get("FGA", 0)),
        "FG_PCT": float(row.get("FG_PCT", 0.0)),
        "FG3M": int(row.get("FG3M", 0)),
        "FG3A": int(row.get("FG3A", 0)),
        "FG3_PCT": float(row.get("FG3_PCT", 0.0)),
        "FTM": int(row.get("FTM", 0)),
        "FTA": int(row.get("FTA", 0)),
        "FT_PCT": float(row.get("FT_PCT", 0.0)),
        "PLUS_MINUS": int(row.get("PLUS_MINUS", 0)),
        "MATCHUP": str(row.get("MATCHUP", "")),
        "GAME_DATE": str(row.get("GAME_DATE", "")),
        "WL": str(row.get("WL", "")),
    }


def build_player_highlight(
    row: pd.Series,
    season: str,
    player_name: str,
    player_id: int,
    team_abbrev: str,
) -> HighlightResponse:
    s = _row_to_dict(row)
    grade, score = _compute_grade(s)
    primary, secondary = get_team_colors(team_abbrev)

    matchup = s["MATCHUP"]
    parts = matchup.split()
    opponent = parts[-1] if len(parts) >= 3 else matchup

    return HighlightResponse(
        result_type="player",
        game_summary=GameSummary(
            player_or_team=player_name,
            opponent=opponent,
            game_date=s["GAME_DATE"],
            result=f"{s['WL']} — {s['MATCHUP']}",
            season=season,
        ),
        key_highlights=_build_key_highlights(s),
        stat_line=StatLine(
            points=s["PTS"],
            rebounds=s["REB"],
            assists=s["AST"],
            steals=s["STL"],
            blocks=s["BLK"],
            turnovers=s["TOV"],
            minutes=s["MIN"],
            fg_made=s["FGM"],
            fg_attempted=s["FGA"],
            fg_pct=s["FG_PCT"],
            fg3_made=s["FG3M"],
            fg3_attempted=s["FG3A"],
            fg3_pct=s["FG3_PCT"],
            ft_made=s["FTM"],
            ft_attempted=s["FTA"],
            ft_pct=s["FT_PCT"],
            plus_minus=s["PLUS_MINUS"],
        ),
        impact_analysis=_build_impact_analysis(s, player_name),
        highlight_grade=grade,
        grade_score=score,
        team_abbrev=team_abbrev,
        team_colors=TeamColors(primary=primary, secondary=secondary),
        player_id=player_id,
        headshot_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
    )


def build_team_highlight(
    row: pd.Series,
    season: str,
    team_name: str,
    team_abbrev: str,
) -> HighlightResponse:
    s = _row_to_dict(row)
    grade, score = _compute_grade(s)
    primary, secondary = get_team_colors(team_abbrev)

    matchup = s["MATCHUP"]
    parts = matchup.split()
    opponent = parts[-1] if len(parts) >= 3 else matchup

    return HighlightResponse(
        result_type="team",
        game_summary=GameSummary(
            player_or_team=team_name,
            opponent=opponent,
            game_date=s["GAME_DATE"],
            result=f"{s['WL']} — {s['MATCHUP']}",
            season=season,
        ),
        key_highlights=_build_key_highlights(s),
        stat_line=StatLine(
            points=s["PTS"],
            rebounds=s["REB"],
            assists=s["AST"],
            steals=s["STL"],
            blocks=s["BLK"],
            turnovers=s["TOV"],
            minutes=s["MIN"],
            fg_made=s["FGM"],
            fg_attempted=s["FGA"],
            fg_pct=s["FG_PCT"],
            fg3_made=s["FG3M"],
            fg3_attempted=s["FG3A"],
            fg3_pct=s["FG3_PCT"],
            ft_made=s["FTM"],
            ft_attempted=s["FTA"],
            ft_pct=s["FT_PCT"],
            plus_minus=s["PLUS_MINUS"],
        ),
        impact_analysis=_build_impact_analysis(s, team_name),
        highlight_grade=grade,
        grade_score=score,
        team_abbrev=team_abbrev,
        team_colors=TeamColors(primary=primary, secondary=secondary),
    )
