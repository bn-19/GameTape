import { useState } from 'react'
import { HighlightResponse, ApiError } from './types/highlight'
import { searchHighlight, parseApiError } from './api/highlightApi'
import SearchBar from './components/SearchBar'
import HighlightCard from './components/HighlightCard'
import ErrorMessage from './components/ErrorMessage'
import './App.css'

export default function App() {
  const [highlight, setHighlight] = useState<HighlightResponse | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (query: string) => {
    setLoading(true)
    setError(null)
    setHighlight(null)
    try {
      const data = await searchHighlight(query)
      setHighlight(data)
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">
          <span className="title-ball">🏀</span> NBA Highlight Mode
        </h1>
        <p className="app-subtitle">Live game commentary · Real stats · Broadcast energy</p>
        <SearchBar onSearch={handleSearch} loading={loading} />
      </header>

      <main className="app-main">
        {loading && (
          <div className="loading-state">
            <div className="loading-ball">🏀</div>
            <p>Fetching highlights from the NBA…</p>
          </div>
        )}
        {error && !loading && (
          <ErrorMessage error={error} onSuggestionClick={handleSearch} />
        )}
        {highlight && !loading && <HighlightCard data={highlight} />}
        {!highlight && !error && !loading && (
          <div className="empty-state">
            <div className="empty-icon">🏀</div>
            <p>Search for a player or team to see their latest highlights</p>
            <div className="example-searches">
              {['Stephen Curry', 'LeBron James', 'Nikola Jokic', 'Lakers', 'Celtics'].map((ex) => (
                <button key={ex} className="example-chip" onClick={() => handleSearch(ex)}>
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
