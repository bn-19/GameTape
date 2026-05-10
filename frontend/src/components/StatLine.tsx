import type { StatLine as StatLineType, TeamColors } from '../types/highlight'

interface Props {
  stats: StatLineType
  colors: TeamColors
}

const pct = (n: number) => `${Math.round(n * 100)}%`

export default function StatLine({ stats, colors }: Props) {
  const cells = [
    { label: 'PTS', value: stats.points },
    { label: 'REB', value: stats.rebounds },
    { label: 'AST', value: stats.assists },
    { label: 'STL', value: stats.steals },
    { label: 'BLK', value: stats.blocks },
    { label: 'TOV', value: stats.turnovers },
    { label: 'FG', value: `${stats.fg_made}/${stats.fg_attempted}` },
    { label: 'FG%', value: pct(stats.fg_pct) },
    { label: '3PT', value: `${stats.fg3_made}/${stats.fg3_attempted}` },
    { label: '3P%', value: pct(stats.fg3_pct) },
    { label: 'FT', value: `${stats.ft_made}/${stats.ft_attempted}` },
    { label: '+/-', value: stats.plus_minus > 0 ? `+${stats.plus_minus}` : stats.plus_minus },
    { label: 'MIN', value: stats.minutes },
  ]

  return (
    <section className="card-section">
      <div className="section-header" style={{ color: colors.primary }}>
        📊 Full Stat Line
      </div>
      <div className="stat-grid">
        {cells.map(({ label, value }) => (
          <div key={label} className="stat-cell">
            <span className="stat-value" style={{ color: colors.primary }}>
              {value}
            </span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
