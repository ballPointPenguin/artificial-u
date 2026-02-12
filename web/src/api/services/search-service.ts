/**
 * Global search service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { SearchResponse } from '../types.js'

interface SearchParams {
  q: string
  limit?: number
}

export const searchService = {
  search: (params: SearchParams): Promise<SearchResponse> => {
    const queryParams = new URLSearchParams()
    queryParams.set('q', params.q)
    if (params.limit !== undefined) queryParams.set('limit', String(params.limit))
    return httpClient.get<SearchResponse>(`${ENDPOINTS.search}?${queryParams.toString()}`)
  },
}
