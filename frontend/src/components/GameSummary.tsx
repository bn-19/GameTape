import type { GameSummary as GameSummaryType, TeamColors } from '../types/highlight'

interface Props {
  summary: GameSummaryType
  colors: TeamColors
  headshot_url?: string
  result_type: 'player' | 'team'
  team_abbrev?: string
}

export default function GameSummary({ summary, colors, headshot_url, result_type, team_abbrev }: Props) {
  const isWin = summary.result.startsWith('W')

  return (
    <section className="card-section game-summary-section">
      <div className="section-header" style={{ color: colors.primary }}>
        🏀 Game Summary
      </div>
      <div className="game-summary-body">
        {headshot_url && result_type === 'player' && (
          <img
            className="player-headshot"
            src={headshot_url}
            alt={summary.player_or_team}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        )}
        <div className="game-summary-info">
          <h2 className="player-name" style={{ color: colors.primary, textShadow: `0 0 30px ${colors.primary}88` }}>
            {summary.player_or_team}
          </h2>
          {team_abbrev && (
            <span className="team-badge" style={{ background: colors.primary, color: '#000' }}>
              {team_abbrev}
            </span>
          )}
          <div className="game-meta">
            <span className={`result-badge ${isWin ? 'result-win' : 'result-loss'}`}>
              {isWin ? '✅ WIN' : '❌ LOSS'}
            </span>
            <span className="matchup-text">{summary.result.replace(/^[WL] — /, '')}</span>
          </div>
          <div className="game-date">
            {summary.game_date} · {summary.season}
          </div>
        </div>
      </div>
    </section>
  )
}
