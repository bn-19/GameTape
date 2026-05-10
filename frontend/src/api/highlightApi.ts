import axios from 'axios'
import type { HighlightResponse, ApiError, RecentGamesResponse, SearchSuggestion } from '../types/highlight'

export type Sport = 'nba' | 'nfl'

export const searchHighlight = async (query: string, sport: Sport): Promise<HighlightResponse> => {
  const { data } = await axios.get<HighlightResponse>('/api/search', {
    params: { q: query, sport },
    timeout: 25000,
  })
  return data
}

export const fetchSearchSuggestions = async (query: string, sport: Sport): Promise<SearchSuggestion[]> => {
  const trimmed = query.trim()
  if (!trimmed) return []
  const { data } = await axios.get<{ suggestions: SearchSuggestion[] }>('/api/suggest', {
    params: { q: trimmed, sport },
    timeout: 8000,
  })
  return data.suggestions
}

export const fetchRecentGames = async (sport: Sport): Promise<RecentGamesResponse> => {
  const { data } = await axios.get<RecentGamesResponse>('/api/recent-games', {
    params: { sport },
    timeout: 25000,
  })
  return data
}

export const parseApiError = (err: unknown): ApiError => {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'object' && detail !== null) {
      return { message: detail.message, suggestions: detail.suggestions }
    }
    if (typeof detail === 'string') return { message: detail }
    if (err.code === 'ECONNABORTED') return { message: 'Request timed out. The stats API can be slow — try again.' }
    if (!err.response) return { message: 'Cannot reach the server. Make sure the backend is running on port 8000.' }
  }
  return { message: 'An unexpected error occurred.' }
}
