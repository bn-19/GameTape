export interface TeamColors {
  primary: string
  secondary: string
}

export interface GameSummary {
  player_or_team: string
  opponent: string
  game_date: string
  result: string
  season: string
}

export interface StatLine {
  points: number
  rebounds: number
  assists: number
  steals: number
  blocks: number
  turnovers: number
  minutes: string
  fg_made: number
  fg_attempted: number
  fg_pct: number
  fg3_made: number
  fg3_attempted: number
  fg3_pct: number
  ft_made: number
  ft_attempted: number
  ft_pct: number
  plus_minus: number
}

export interface HighlightResponse {
  sport: 'nba' | 'nfl'
  result_type: 'player' | 'team'
  game_summary: GameSummary
  key_highlights: string[]
  stat_line: StatLine
  stat_items?: { label: string; value: string }[]
  impact_analysis: string
  highlight_grade: string
  grade_score: number
  team_abbrev?: string
  team_colors?: TeamColors
  player_id?: number
  headshot_url?: string
}

export interface ApiError {
  message: string
  suggestions?: string[]
}

export interface SearchSuggestion {
  value: string
  type: 'player' | 'team'
  subtitle: string
}

export interface RecentGameTeam {
  name: string
  abbreviation: string
  score: number
  record: string
  colors: TeamColors
  seed?: number
}

export interface RecentGameLeader {
  name: string
  player_id: number
  team_abbrev: string
  points: number
  rebounds: number
  assists: number
  headshot_url: string
  category?: string
  display_value?: string
}

export interface RecentGame {
  game_id: string
  game_date: string
  status: string
  label: string
  series_text: string
  matchup: string
  home_team: RecentGameTeam
  away_team: RecentGameTeam
  leaders: RecentGameLeader[]
  highlights: string[]
  underdog_note?: string
}

export interface RecentGamesResponse {
  as_of_date: string
  games: RecentGame[]
}
