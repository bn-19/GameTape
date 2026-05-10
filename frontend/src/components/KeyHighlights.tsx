import { TeamColors } from '../types/highlight'

interface Props {
  highlights: string[]
  colors: TeamColors
}

export default function KeyHighlights({ highlights, colors }: Props) {
  return (
    <section className="card-section">
      <div className="section-header" style={{ color: colors.primary }}>
        🔥 Key Highlights
      </div>
      <ul className="highlights-list">
        {highlights.map((h, i) => (
          <li key={i} className="highlight-item" style={{ borderLeftColor: colors.primary }}>
            {h}
          </li>
        ))}
      </ul>
    </section>
  )
}
