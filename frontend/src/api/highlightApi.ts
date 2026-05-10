import axios from 'axios'
import { HighlightResponse, ApiError } from '../types/highlight'

export const searchHighlight = async (query: string): Promise<HighlightResponse> => {
  const { data } = await axios.get<HighlightResponse>('/api/search', {
    params: { q: query },
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
    if (err.code === 'ECONNABORTED') return { message: 'Request timed out. The NBA stats API can be slow — try again.' }
    if (!err.response) return { message: 'Cannot reach the server. Make sure the backend is running on port 8000.' }
  }
  return { message: 'An unexpected error occurred.' }
}
