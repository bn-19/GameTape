import type { TeamColors } from '../types/highlight'

interface Props {
  stats: { label: string; value: string }[]
  colors: TeamColors
}

export default function GenericStatLine({ stats, colors }: Props) {
  return (
    <section className="card-section">
      <div className="section-header" style={{ color: colors.primary }}>
        📊 Game Snapshot
      </div>
      <div className="stat-grid">
        {stats.map(({ label, value }) => (
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
