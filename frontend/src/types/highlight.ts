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
  result_type: 'player' | 'team'
  game_summary: GameSummary
  key_highlights: string[]
  stat_line: StatLine
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
