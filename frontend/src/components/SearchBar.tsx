import { useState, useRef } from 'react'
import { fetchSearchSuggestions } from '../api/highlightApi'
import type { SearchSuggestion } from '../types/highlight'
import type { Sport } from '../api/highlightApi'

interface Props {
  onSearch: (query: string) => void
  loading: boolean
  sport: Sport
  icon: string
  placeholder: string
}

export default function SearchBar({ onSearch, loading, sport, icon, placeholder }: Props) {
  const [value, setValue] = useState('')
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [suggesting, setSuggesting] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const requestRef = useRef(0)
  const selectingRef = useRef(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) return
    const bestGuess = suggestions[0]?.value
    onSearch(bestGuess ?? trimmed)
    if (bestGuess) setValue(bestGuess)
    setSuggestions([])
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const nextValue = e.target.value
    setValue(nextValue)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    requestRef.current += 1
    if (nextValue.trim().length < 2) {
      setSuggestions([])
      setSuggesting(false)
      return
    }
    const requestId = requestRef.current
    debounceRef.current = setTimeout(async () => {
      setSuggesting(true)
      try {
        const nextSuggestions = await fetchSearchSuggestions(nextValue, sport)
        if (requestRef.current === requestId) {
          setSuggestions(nextSuggestions)
        }
      } catch {
        if (requestRef.current === requestId) {
          setSuggestions([])
        }
      } finally {
        if (requestRef.current === requestId) {
          setSuggesting(false)
        }
      }
    }, 180)
  }

  const chooseSuggestion = (suggestion: SearchSuggestion) => {
    setValue(suggestion.value)
    setSuggestions([])
    onSearch(suggestion.value)
  }

  const handleSuggestionPointer = (
    event: React.PointerEvent<HTMLButtonElement> | React.MouseEvent<HTMLButtonElement>,
    suggestion: SearchSuggestion,
  ) => {
    event.preventDefault()
    event.stopPropagation()
    if (selectingRef.current) return
    selectingRef.current = true
    chooseSuggestion(suggestion)
    window.setTimeout(() => {
      selectingRef.current = false
    }, 250)
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="search-shell">
        <div className="search-wrapper">
          <span className="search-icon">{icon}</span>
          <input
            className="search-input"
            type="text"
            value={value}
            onChange={handleChange}
            placeholder={placeholder}
            disabled={loading}
            autoFocus
          />
          <button className="search-btn" type="submit" disabled={loading || !value.trim()}>
            {loading ? <span className="spinner" /> : 'GO'}
          </button>
        </div>
        {(suggestions.length > 0 || suggesting) && (
          <div className="search-suggestions">
            <div className="suggestion-kicker">
              {suggesting ? 'Reading the floor...' : 'Best guesses'}
            </div>
            {suggestions.map((suggestion) => (
              <button
                key={`${suggestion.type}-${suggestion.value}`}
                className="search-suggestion"
                type="button"
                onPointerDownCapture={(event) => handleSuggestionPointer(event, suggestion)}
                onMouseDownCapture={(event) => handleSuggestionPointer(event, suggestion)}
                onClick={() => chooseSuggestion(suggestion)}
              >
                <span>{suggestion.value}</span>
                <small>{suggestion.subtitle}</small>
              </button>
            ))}
          </div>
        )}
      </div>
    </form>
  )
}
