import type { HighlightResponse } from '../types/highlight'
import GameSummary from './GameSummary'
import KeyHighlights from './KeyHighlights'
import StatLine from './StatLine'
import GenericStatLine from './GenericStatLine'
import ImpactAnalysis from './ImpactAnalysis'
import HighlightGrade from './HighlightGrade'

interface Props {
  data: HighlightResponse
}

const DEFAULT_COLORS = { primary: '#FF6B35', secondary: '#FFFFFF' }

export default function HighlightCard({ data }: Props) {
  const colors = data.team_colors ?? DEFAULT_COLORS

  return (
    <div
      className="highlight-card"
      style={{
        borderColor: colors.primary,
        boxShadow: `0 0 60px ${colors.primary}33, 0 0 120px ${colors.primary}11`,
      }}
    >
      <GameSummary
        summary={data.game_summary}
        colors={colors}
        headshot_url={data.headshot_url}
        result_type={data.result_type}
        team_abbrev={data.team_abbrev}
      />
      <KeyHighlights highlights={data.key_highlights} colors={colors} />
      {data.stat_items ? (
        <GenericStatLine stats={data.stat_items} colors={colors} />
      ) : (
        <StatLine stats={data.stat_line} colors={colors} />
      )}
      <ImpactAnalysis analysis={data.impact_analysis} colors={colors} />
      <HighlightGrade grade={data.highlight_grade} score={data.grade_score} colors={colors} />
    </div>
  )
}
