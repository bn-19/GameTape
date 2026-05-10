import type { TeamColors } from '../types/highlight'

interface Props {
  grade: string
  score: number
  colors: TeamColors
}

export default function HighlightGrade({ grade, score, colors }: Props) {
  return (
    <section className="card-section grade-section">
      <div className="section-header" style={{ color: colors.primary }}>
        🏆 Highlight Grade
      </div>
      <div className="grade-display">
        <span
          className="grade-letter"
          style={{
            color: colors.primary,
            textShadow: `0 0 40px ${colors.primary}, 0 0 80px ${colors.primary}66`,
          }}
        >
          {grade}
        </span>
        <div className="grade-bar-track">
          <div
            className="grade-bar-fill"
            style={{
              width: `${score}%`,
              background: `linear-gradient(90deg, ${colors.secondary}, ${colors.primary})`,
            }}
          />
        </div>
        <span className="grade-score">{score}/100</span>
      </div>
    </section>
  )
}
