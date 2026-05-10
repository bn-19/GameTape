import { useState } from 'react'
import type { HighlightResponse, ApiError } from './types/highlight'
import { searchHighlight, parseApiError } from './api/highlightApi'
import type { Sport } from './api/highlightApi'
import SearchBar from './components/SearchBar'
import HighlightCard from './components/HighlightCard'
import ErrorMessage from './components/ErrorMessage'
import RecentGames from './components/RecentGames'
import './App.css'

const SPORT_CONFIG = {
  nba: {
    tab: 'Basketball',
    icon: '🏀',
    title: 'NBA Highlight Mode',
    subtitle: 'Live game commentary · Real stats · Broadcast energy',
    placeholder: 'Search NBA player or team… e.g. LeBron James, Lakers',
    loading: 'Fetching highlights from the NBA…',
    empty: 'Search for a player or team to see their latest basketball highlights',
    recentTitle: 'Latest NBA Games',
    underdogTitle: 'Lower seeds making noise',
    examples: ['LeBron James', 'Stephen Curry', 'Nikola Jokic', 'Lakers', 'Celtics'],
    features: ['Smart search', 'Playoff-first recaps', 'Underdog watch'],
  },
  nfl: {
    tab: 'American Football',
    icon: '🏈',
    title: 'NFL Highlight Mode',
    subtitle: 'Latest NFL scores · Real leaders · Game-day energy',
    placeholder: 'Search NFL player or team… e.g. Seahawks, Drake Maye',
    loading: 'Fetching highlights from the NFL…',
    empty: 'Search for a player or team to see their latest football highlights',
    recentTitle: 'Latest NFL Games',
    underdogTitle: 'Worse-record teams on alert',
    examples: ['Seattle Seahawks', 'New England Patriots', 'Drake Maye', 'Kenneth Walker III', 'Philadelphia Eagles'],
    features: ['Team recaps', 'Latest leaders', 'Underdog watch'],
  },
} satisfies Record<Sport, {
  tab: string
  icon: string
  title: string
  subtitle: string
  placeholder: string
  loading: string
  empty: string
  recentTitle: string
  underdogTitle: string
  examples: string[]
  features: string[]
}>

const NBA_LOGOS = [
  1610612737, 1610612738, 1610612751, 1610612766, 1610612741, 1610612739, 1610612742, 1610612743,
  1610612765, 1610612744, 1610612745, 1610612754, 1610612746, 1610612747, 1610612763, 1610612748,
  1610612749, 1610612750, 1610612740, 1610612752, 1610612760, 1610612753, 1610612755, 1610612756,
  1610612757, 1610612758, 1610612759, 1610612761, 1610612762, 1610612764,
].map((id) => `https://cdn.nba.com/logos/nba/${id}/primary/L/logo.svg`)

const NFL_LOGOS = [
  'ari', 'atl', 'bal', 'buf', 'car', 'chi', 'cin', 'cle',
  'dal', 'den', 'det', 'gb', 'hou', 'ind', 'jax', 'kc',
  'lv', 'lac', 'lar', 'mia', 'min', 'ne', 'no', 'nyg',
  'nyj', 'phi', 'pit', 'sf', 'sea', 'tb', 'ten', 'wsh',
].map((abbr) => `https://a.espncdn.com/i/teamlogos/nfl/500/${abbr}.png`)

function LogoBackdrop({ sport }: { sport: Sport }) {
  const logos = sport === 'nba' ? NBA_LOGOS : NFL_LOGOS
  return (
    <div className="logo-backdrop" aria-hidden="true">
      {logos.map((src) => (
        <img key={src} src={src} alt="" />
      ))}
    </div>
  )
}

export default function App() {
  const [sport, setSport] = useState<Sport>('nba')
  const [highlight, setHighlight] = useState<HighlightResponse | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(false)
  const config = SPORT_CONFIG[sport]

  const switchSport = (nextSport: Sport) => {
    setSport(nextSport)
    setHighlight(null)
    setError(null)
  }

  const handleSearch = async (query: string) => {
    setLoading(true)
    setError(null)
    setHighlight(null)
    try {
      const data = await searchHighlight(query, sport)
      setHighlight(data)
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`app app-${sport}`}>
      <LogoBackdrop sport={sport} />
      <header className="app-header">
        <nav className="sport-tabs" aria-label="Choose sport">
          {(['nba', 'nfl'] as Sport[]).map((tabSport) => (
            <button
              key={tabSport}
              type="button"
              className={tabSport === sport ? 'sport-tab active' : 'sport-tab'}
              onClick={() => switchSport(tabSport)}
            >
              {SPORT_CONFIG[tabSport].icon} {SPORT_CONFIG[tabSport].tab}
            </button>
          ))}
        </nav>
        <h1 className="app-title">
          <span className="title-ball">{config.icon}</span> {config.title}
        </h1>
        <p className="app-subtitle">{config.subtitle}</p>
        <SearchBar
          key={sport}
          onSearch={handleSearch}
          loading={loading}
          sport={sport}
          icon={config.icon}
          placeholder={config.placeholder}
        />
      </header>

      <main className="app-main">
        {loading && (
          <div className="loading-state">
            <div className="loading-ball">{config.icon}</div>
            <p>{config.loading}</p>
          </div>
        )}
        {error && !loading && (
          <ErrorMessage error={error} onSuggestionClick={handleSearch} />
        )}
        {highlight && !loading && <HighlightCard data={highlight} />}
        {!highlight && !error && !loading && (
          <div className="empty-state">
            <div className="empty-icon">{config.icon}</div>
            <p>{config.empty}</p>
            <div className="example-searches">
              {config.examples.map((ex) => (
                <button key={ex} className="example-chip" onClick={() => handleSearch(ex)}>
                  {ex}
                </button>
              ))}
            </div>
            <div className="app-feature-strip" aria-label="App features">
              {config.features.map((feature) => (
                <span key={feature}>{feature}</span>
              ))}
            </div>
            <RecentGames
              key={sport}
              onSearch={handleSearch}
              sport={sport}
              title={config.recentTitle}
              underdogTitle={config.underdogTitle}
            />
          </div>
        )}
      </main>
    </div>
  )
}
