import { TeamColors } from '../types/highlight'

interface Props {
  analysis: string
  colors: TeamColors
}

export default function ImpactAnalysis({ analysis, colors }: Props) {
  return (
    <section className="card-section">
      <div className="section-header" style={{ color: colors.primary }}>
        💥 Impact Analysis
      </div>
      <p className="impact-text">{analysis}</p>
    </section>
  )
}
