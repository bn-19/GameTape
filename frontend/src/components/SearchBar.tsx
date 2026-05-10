import { useState, useRef } from 'react'

interface Props {
  onSearch: (query: string) => void
  loading: boolean
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (trimmed) onSearch(trimmed)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="search-wrapper">
        <span className="search-icon">🏀</span>
        <input
          className="search-input"
          type="text"
          value={value}
          onChange={handleChange}
          placeholder="Search player or team… e.g. Stephen Curry, Lakers"
          disabled={loading}
          autoFocus
        />
        <button className="search-btn" type="submit" disabled={loading || !value.trim()}>
          {loading ? <span className="spinner" /> : 'GO'}
        </button>
      </div>
    </form>
  )
}
