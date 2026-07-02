/**
 * Tag service
 */
import { httpClient } from '../client.js'
import { ENDPOINTS } from '../config.js'
import type { TagsListResponse } from '../types.js'

interface ListTagsParams {
  language?: string
  q?: string
  limit?: number
}

export const tagService = {
  listTags: (params: ListTagsParams = {}): Promise<TagsListResponse> => {
    const queryParams = new URLSearchParams()
    if (params.language) queryParams.set('language', params.language)
    if (params.q) queryParams.set('q', params.q)
    if (params.limit) queryParams.set('limit', params.limit.toString())
    const query = queryParams.toString()
    return httpClient.get<TagsListResponse>(
      query ? `${ENDPOINTS.tags.list}?${query}` : ENDPOINTS.tags.list
    )
  },

  enqueueBackfill: (options?: {
    force?: boolean
    includeHidden?: boolean
  }): Promise<{ enqueued: number; job_ids: number[] }> => {
    const queryParams = new URLSearchParams()
    if (options?.force) queryParams.set('force', 'true')
    if (options?.includeHidden) queryParams.set('include_hidden', 'true')
    const query = queryParams.toString()
    return httpClient.post(
      query ? `${ENDPOINTS.tags.backfill}?${query}` : ENDPOINTS.tags.backfill,
      {}
    )
  },
}
