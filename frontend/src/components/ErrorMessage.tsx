import type { ApiError } from '../types/highlight'

interface Props {
  error: ApiError
  onSuggestionClick: (name: string) => void
}

export default function ErrorMessage({ error, onSuggestionClick }: Props) {
  return (
    <div className="error-card">
      <div className="error-icon">⚠️</div>
      <p className="error-text">{error.message}</p>
      {error.suggestions && error.suggestions.length > 0 && (
        <div className="suggestions">
          <p className="suggestions-label">Did you mean:</p>
          <div className="suggestion-chips">
            {error.suggestions.map((s) => (
              <button key={s} className="suggestion-chip" onClick={() => onSuggestionClick(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
