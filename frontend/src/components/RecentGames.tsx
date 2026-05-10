import { useEffect, useState } from 'react'
import { fetchRecentGames } from '../api/highlightApi'
import type { RecentGame, RecentGamesResponse } from '../types/highlight'
import type { Sport } from '../api/highlightApi'

interface Props {
  onSearch: (query: string) => void
  sport: Sport
  title: string
  underdogTitle: string
}

const teamStyle = (color: string) => ({ color, textShadow: `0 0 22px ${color}66` })

function LeaderImage({ leader }: { leader: RecentGame['leaders'][number] }) {
  return (
    <img
      className="recent-leader-img"
      src={leader.headshot_url}
      alt={leader.name}
      onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
    />
  )
}

function RecentGameCard({ game, onSearch }: { game: RecentGame; onSearch: (query: string) => void }) {
  const [open, setOpen] = useState(false)
  const topLeader = game.leaders[0]
  const leaderLine = topLeader?.display_value || `${topLeader?.points} PTS · ${topLeader?.rebounds} REB · ${topLeader?.assists} AST`

  return (
    <article
      className="recent-game-card"
      style={{ borderColor: game.home_team.colors.primary }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <div className="recent-game-topline">
        <span>{game.status}</span>
        <span>{game.game_date}</span>
      </div>
      <div className="recent-scoreline">
        <div>
          <span className="recent-team" style={teamStyle(game.away_team.colors.primary)}>
            {game.away_team.abbreviation}
          </span>
          <strong>{game.away_team.score}</strong>
        </div>
        <div>
          <span className="recent-team" style={teamStyle(game.home_team.colors.primary)}>
            {game.home_team.abbreviation}
          </span>
          <strong>{game.home_team.score}</strong>
        </div>
      </div>
      <p className="recent-series">{game.label || game.series_text || game.matchup}</p>
      {game.underdog_note && <div className="underdog-badge">Underdog</div>}
      {topLeader && (
        <div className="recent-leader">
          <LeaderImage leader={topLeader} />
          <div>
            <span>{topLeader.name}</span>
            <small>{topLeader.category ? `${topLeader.category}: ` : ''}{leaderLine}</small>
          </div>
        </div>
      )}
      <div className="recent-actions">
        <button
          className="recent-inspect-btn"
          type="button"
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onClick={() => setOpen(true)}
        >
          Inspect
        </button>
        <button className="recent-load-btn" type="button" onClick={() => onSearch(game.home_team.name)}>
          Team recap
        </button>
      </div>
      {open && (
        <div className="recent-popover">
          <div className="recent-popover-title">Highlights</div>
          <ul>
            {game.highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
          {game.underdog_note && <p className="underdog-popover-note">{game.underdog_note}</p>}
          {game.leaders.length > 1 && (
            <div className="recent-popover-leaders">
              {game.leaders.slice(0, 2).map((leader) => (
                <button key={leader.player_id} type="button" onClick={() => onSearch(leader.name)}>
                  <LeaderImage leader={leader} />
                  <span>{leader.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  )
}

function UnderdogWatch({ games, title, onSearch }: { games: RecentGame[]; title: string; onSearch: (query: string) => void }) {
  const underdogs = games.filter((game) => game.underdog_note)
  if (underdogs.length === 0) return null

  return (
    <section className="underdog-watch">
      <div>
        <span>Underdog Watch</span>
        <h3>{title}</h3>
      </div>
      <div className="underdog-list">
        {underdogs.slice(0, 2).map((game) => {
          const leader = game.home_team.score > game.away_team.score ? game.home_team : game.away_team
          return (
            <button key={game.game_id} type="button" onClick={() => onSearch(leader.name)}>
              <strong>{leader.abbreviation}</strong>
              <small>{game.underdog_note}</small>
            </button>
          )
        })}
      </div>
    </section>
  )
}

export default function RecentGames({ onSearch, sport, title, underdogTitle }: Props) {
  const [data, setData] = useState<RecentGamesResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mounted = true
    fetchRecentGames(sport)
      .then((recent) => {
        if (mounted) setData(recent)
      })
      .catch(() => {
        if (mounted) setError(true)
      })
    return () => {
      mounted = false
    }
  }, [sport])

  if (error) return null

  return (
    <section className="recent-games-section">
      <div className="recent-header">
        <div>
          <h2>{title}</h2>
          <p>{data ? `As of ${data.as_of_date}` : 'Loading current scoreboard...'}</p>
        </div>
      </div>
      {data && <UnderdogWatch games={data.games} title={underdogTitle} onSearch={onSearch} />}
      <div className="recent-games-grid">
        {data
          ? data.games.map((game) => (
              <RecentGameCard key={game.game_id} game={game} onSearch={onSearch} />
            ))
          : Array.from({ length: 2 }).map((_, index) => (
              <div key={index} className="recent-game-card recent-skeleton" />
            ))}
      </div>
    </section>
  )
}
